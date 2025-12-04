"""
Sakina Gas Company - User Model
Built from scratch with comprehensive user management and security
Version 3.0 - Enterprise grade with advanced features
"""

from database import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import secrets
import re

class User(UserMixin, db.Model):
    """
    Comprehensive User model with advanced security and management features
    """
    __tablename__ = 'users'
    
    # Primary identification
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    
    # Password and security
    password_hash = Column(String(512), nullable=False) # FIX: Increased size for secure hashing
    salt = Column(String(32), nullable=False)
    password_reset_token = Column(String(100), nullable=True)
    password_reset_expires = Column(DateTime, nullable=True)
    last_password_change = Column(DateTime, nullable=False, default=func.current_timestamp())
    password_history = Column(JSON, nullable=True)  # Store hashes of last 5 passwords
    
    # Personal information
    first_name = Column(String(50), nullable=False)
    middle_name = Column(String(50), nullable=True)
    last_name = Column(String(50), nullable=False)
    
    # Employment details
    employee_id = Column(String(20), nullable=True, index=True)  # Links to Employee table
    role = Column(String(30), nullable=False, default='employee', index=True)
    department = Column(String(50), nullable=True)
    location = Column(String(50), nullable=False)
    
    # Account status and security
    is_active = Column(Boolean, nullable=False, default=True)
    is_verified = Column(Boolean, nullable=False, default=False)
    email_verified = Column(Boolean, nullable=False, default=False)
    failed_login_attempts = Column(Integer, nullable=False, default=0)
    account_locked_until = Column(DateTime, nullable=True)
    
    # Activity tracking
    created_date = Column(DateTime, nullable=False, default=func.current_timestamp())
    created_by = Column(Integer, nullable=True)  # User ID who created this account
    last_login = Column(DateTime, nullable=True)
    last_seen = Column(DateTime, nullable=True)
    last_activity = Column(DateTime, nullable=True)
    login_count = Column(Integer, nullable=False, default=0)
    
    # Session management
    current_session_id = Column(String(100), nullable=True)
    session_expires = Column(DateTime, nullable=True)
    remember_token = Column(String(100), nullable=True)
    
    # Security settings
    two_factor_enabled = Column(Boolean, nullable=False, default=False)
    two_factor_secret = Column(String(50), nullable=True)
    backup_codes = Column(JSON, nullable=True)  # Array of backup codes
    
    # User preferences and settings
    preferences = Column(JSON, nullable=True)  # Store user preferences as JSON
    notification_settings = Column(JSON, nullable=True)  # Email, SMS preferences
    dashboard_theme = Column(String(20), nullable=False, default='light')
    language = Column(String(5), nullable=False, default='en')
    timezone = Column(String(50), nullable=False, default='Africa/Nairobi')
    
    # Profile completion and metadata
    profile_picture = Column(String(255), nullable=True)
    signature = Column(Text, nullable=True)
    bio = Column(Text, nullable=True)
    phone = Column(String(20), nullable=True)
    
    # System metadata
    user_metadata = Column(JSON, nullable=True)  # Additional metadata storage  <-- FIX: Renamed from 'metadata'
    last_updated = Column(DateTime, nullable=False, default=func.current_timestamp(), onupdate=func.current_timestamp())
    
    # Relationships
    # created_audit_logs is handled in AuditLog model
    # FIX: Use string literal for relationship to break circular dependency
    employee = relationship('Employee', backref='user_account', uselist=False, 
                          primaryjoin="User.employee_id == Employee.employee_id")
    
    def __init__(self, **kwargs):
        """Initialize user with secure defaults"""
        super(User, self).__init__()
        
        # Generate salt for password hashing
        self.salt = secrets.token_hex(16)
        
        # Initialize preferences
        self.preferences = {
            'items_per_page': 25,
            'dashboard_widgets': [],
            'email_notifications': True,
            'auto_logout_minutes': 480  # 8 hours
        }
        
        # Initialize notification settings
        self.notification_settings = {
            'email_login_alerts': True,
            'email_password_changes': True,
            'email_account_changes': True,
            'email_system_notifications': True
        }
        
        # Set creation timestamp
        self.created_date = datetime.utcnow()
        
        # Apply any provided kwargs
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def set_password(self, password):
        """Set password with enhanced security and history tracking"""
        from flask import current_app # Local import for config access
        
        # FIX: Added try/except for security, the logic is sound but needs local context
        try:
            # Validate password strength
            if not self.is_password_strong(password):
                raise ValueError("Password does not meet security requirements")
            
            # Check against password history
            if self.is_password_in_history(password):
                raise ValueError("Cannot reuse recent passwords")
            
            # Generate new hash
            password_hash = generate_password_hash(password + self.salt, method='pbkdf2:sha256', salt_length=16)
            
            # Update password history
            if self.password_history is None:
                self.password_history = []
            
            # Add current password hash to history
            if self.password_hash:
                self.password_history.append(self.password_hash)
            
            # Keep only last N passwords in history
            policy = current_app.config.get('VALIDATION_RULES', {}).get('password_policy', {})
            history_size = policy.get('history_check', 5)
            self.password_history = self.password_history[-history_size:]
            
            # Set new password
            self.password_hash = password_hash
            self.last_password_change = datetime.utcnow()
            
            # Clear any password reset tokens
            self.password_reset_token = None
            self.password_reset_expires = None
            
            # Reset failed login attempts
            self.failed_login_attempts = 0
            self.account_locked_until = None
        except Exception as e:
            raise ValueError(f"Password setting failed: {e}")
    
    def check_password(self, password):
        """Check password with enhanced security logging"""
        from flask import current_app # Local import
        
        if not self.password_hash:
            return False
        
        # Check if account is locked
        if self.is_account_locked():
            return False
        
        # Verify password
        is_valid = check_password_hash(self.password_hash, password + self.salt)
        
        if is_valid:
            # Reset failed attempts on successful login
            self.failed_login_attempts = 0
            self.account_locked_until = None
            self.last_login = datetime.utcnow()
            self.login_count += 1
        else:
            # Increment failed attempts
            self.failed_login_attempts += 1
            
            # Lock account after max attempts
            max_attempts = current_app.config.get('MAX_LOGIN_ATTEMPTS', 5)
            if self.failed_login_attempts >= max_attempts:
                lockout_duration = current_app.config.get('ACCOUNT_LOCKOUT_DURATION', timedelta(minutes=30))
                self.account_locked_until = datetime.utcnow() + lockout_duration
        
        return is_valid
    
    def is_account_locked(self):
        """Check if account is currently locked"""
        if self.account_locked_until is None:
            return False
        
        if datetime.utcnow() < self.account_locked_until:
            return True
        
        # Unlock account if lockout period has expired
        self.account_locked_until = None
        self.failed_login_attempts = 0
        return False
    
    def is_password_strong(self, password):
        """Validate password strength according to policy"""
        from flask import current_app # Local import
        
        policy = current_app.config.get('VALIDATION_RULES', {}).get('password_policy', {})
        
        if len(password) < policy.get('min_length', 8):
            return False
        
        # Check for uppercase, lowercase, digits, special characters
        if policy.get('require_uppercase', True) and not re.search(r'[A-Z]', password):
            return False
        if policy.get('require_lowercase', True) and not re.search(r'[a-z]', password):
            return False
        if policy.get('require_numbers', True) and not re.search(r'\d', password):
            return False
        if policy.get('require_special_chars', True) and not re.search(r'[!@#$%^&*()_+\-=\[\]{};:"\\|,.<>\?]', password):
            return False
        
        # Check against forbidden patterns (simplified check)
        if any(pattern in password.lower() for pattern in policy.get('forbidden_patterns', [])):
            return False

        return True
    
    def is_password_in_history(self, password):
        """Check if password was used recently"""
        if not self.password_history:
            return False
        
        # Check against stored password hashes
        for old_hash in self.password_history:
            # Check password against hash with current salt
            if check_password_hash(old_hash, password + self.salt):
                return True
        
        return False
    
    def is_password_expired(self):
        """Check if password has expired"""
        if not self.last_password_change:
            return True
        
        from flask import current_app # Local import
        expiry_days = current_app.config.get('PASSWORD_EXPIRY_DAYS', 90)
        expiry_date = self.last_password_change + timedelta(days=expiry_days)
        
        return datetime.utcnow() > expiry_date
    
    def generate_password_reset_token(self):
        """Generate secure password reset token"""
        self.password_reset_token = secrets.token_urlsafe(32)
        self.password_reset_expires = datetime.utcnow() + timedelta(hours=1)  # 1 hour expiry
        return self.password_reset_token
    
    def verify_password_reset_token(self, token):
        """Verify password reset token"""
        if not self.password_reset_token or not self.password_reset_expires:
            return False
        
        if datetime.utcnow() > self.password_reset_expires:
            return False
        
        return self.password_reset_token == token
    
    def get_full_name(self):
        """Get user's full name"""
        if self.middle_name:
            return f"{self.first_name} {self.middle_name} {self.last_name}"
        return f"{self.first_name} {self.last_name}"
    
    def get_display_name(self):
        """Get display name for UI"""
        return self.get_full_name()
    
    def get_initials(self):
        """Get user's initials"""
        initials = self.first_name[0].upper() if self.first_name else ''
        if self.middle_name:
            initials += self.middle_name[0].upper()
        if self.last_name:
            initials += self.last_name[0].upper()
        return initials
    
    def get_role_display(self):
        """Get human-readable role name"""
        from flask import current_app # Local import
        roles_config = current_app.config.get('USER_ROLES', {})
        return roles_config.get(self.role, {}).get('display_name', self.role.replace('_', ' ').title())

    def get_permissions(self):
        """Get user permissions based on role"""
        from flask import current_app
        roles_config = current_app.config.get('USER_ROLES', {})
        role_config = roles_config.get(self.role, {})
        return role_config.get('permissions', [])
    
    def has_permission(self, permission):
        """Check if user has specific permission"""
        if self.role == 'admin':
            return True  # Admin has all permissions
        
        permissions = self.get_permissions()
        return permission in permissions or 'all_permissions' in permissions
    
    def can_access_location(self, location):
        """Check if user can access specific location"""
        from flask import current_app
        roles_config = current_app.config.get('USER_ROLES', {})
        role_config = roles_config.get(self.role, {})
        locations_access = role_config.get('locations_access', 'assigned_only')
        
        if locations_access == 'all' or self.role == 'admin':
            return True
        elif locations_access == 'assigned_only':
            return location == self.location
        
        return False
    
    def get_accessible_locations(self):
        """Get list of locations user can access"""
        from flask import current_app
        
        if self.can_access_location('all'):
            locations_config = current_app.config.get('COMPANY_LOCATIONS', {})
            return list(locations_config.keys())
        else:
            return [self.location] if self.location else []
    
    def update_last_activity(self):
        """Update last activity timestamp"""
        self.last_activity = datetime.utcnow()
        self.last_seen = datetime.utcnow()
    
    def is_online(self, threshold_minutes=15):
        """Check if user is considered online"""
        if not self.last_activity:
            return False
        
        threshold = datetime.utcnow() - timedelta(minutes=threshold_minutes)
        return self.last_activity > threshold
    
    def get_dashboard_widgets(self):
        """Get user's dashboard widget configuration"""
        if not self.preferences:
            return []
        
        widgets = self.preferences.get('dashboard_widgets', [])
        
        # If no custom widgets, return default based on role
        if not widgets:
            from flask import current_app
            roles_config = current_app.config.get('USER_ROLES', {})
            role_config = roles_config.get(self.role, {})
            return role_config.get('dashboard_widgets', [])
        
        return widgets
    
    def update_preferences(self, new_preferences):
        """Update user preferences"""
        if self.preferences is None:
            self.preferences = {}
        
        self.preferences.update(new_preferences)
        self.last_updated = datetime.utcnow()
    
    def get_profile_completeness(self):
        """Calculate profile completion percentage"""
        required_fields = [
            'first_name', 'last_name', 'email', 'phone',
            'department', 'location', 'role'
        ]
        
        completed_fields = 0
        for field in required_fields:
            value = getattr(self, field, None)
            if value and str(value).strip():
                completed_fields += 1
        
        # Additional checks for preferences and settings
        if self.preferences and len(self.preferences) > 2:
            completed_fields += 1
        
        if self.profile_picture:
            completed_fields += 1
        
        total_fields = len(required_fields) + 2
        return round((completed_fields / total_fields) * 100, 1)
    
    def generate_session_token(self):
        """Generate secure session token"""
        self.current_session_id = secrets.token_urlsafe(32)
        self.session_expires = datetime.utcnow() + timedelta(hours=8)
        return self.current_session_id
    
    def is_session_valid(self, session_id):
        """Validate session token"""
        if not self.current_session_id or not self.session_expires:
            return False
        
        if datetime.utcnow() > self.session_expires:
            return False
        
        return self.current_session_id == session_id
    
    def extend_session(self):
        """Extend current session"""
        if self.current_session_id:
            self.session_expires = datetime.utcnow() + timedelta(hours=8)
    
    def invalidate_session(self):
        """Invalidate current session"""
        self.current_session_id = None
        self.session_expires = None
        self.remember_token = None
    
    def get_security_events(self, limit=10):
        """Get recent security events for this user"""
        from models.audit import AuditLog
        
        security_events = AuditLog.query.filter(
            AuditLog.user_id == self.id,
            AuditLog.event_category == 'security'
        ).order_by(AuditLog.timestamp.desc()).limit(limit).all()
        
        return security_events
    
    def to_dict(self, include_sensitive=False):
        """Convert user to dictionary"""
        data = {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'first_name': self.first_name,
            'middle_name': self.middle_name,
            'last_name': self.last_name,
            'full_name': self.get_full_name(),
            'role': self.role,
            'role_display': self.get_role_display(),
            'department': self.department,
            'location': self.location,
            'is_active': self.is_active,
            'created_date': self.created_date.isoformat() if self.created_date else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None,
            'is_online': self.is_online(),
            'profile_completeness': self.get_profile_completeness()
        }
        
        if include_sensitive:
            data.update({
                'failed_login_attempts': self.failed_login_attempts,
                'is_account_locked': self.is_account_locked(),
                'password_expired': self.is_password_expired(),
                'two_factor_enabled': self.two_factor_enabled,
                'preferences': self.preferences,
                'notification_settings': self.notification_settings
            })
        
        return data
    
    @classmethod
    def create_user(cls, username, email, password, first_name, last_name, 
                   role='employee', location='head_office', **kwargs):
        """Class method to create new user with validation"""
        # Validate required fields
        if not all([username, email, password, first_name, last_name]):
            raise ValueError("Missing required fields")
        
        # Check if username or email already exists
        if cls.query.filter_by(username=username).first():
            raise ValueError("Username already exists")
        
        if cls.query.filter_by(email=email).first():
            raise ValueError("Email already exists")
        
        # Create new user
        user = cls(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            role=role,
            location=location,
            **kwargs
        )
        
        # Set password
        user.set_password(password)
        
        return user
    
    @classmethod
    def authenticate(cls, username_or_email, password):
        """Authenticate user by username/email and password"""
        # Find user by username or email
        user = cls.query.filter(
            db.or_(
                cls.username == username_or_email,
                cls.email == username_or_email
            )
        ).first()
        
        if not user or not user.is_active:
            return None
        
        # Check password
        if user.check_password(password):
            # Update activity
            user.update_last_activity()
            return user
        
        return None
    
    @classmethod
    def get_by_role(cls, role):
        """Get all users by role"""
        return cls.query.filter_by(role=role, is_active=True).all()
    
    @classmethod
    def get_by_location(cls, location):
        """Get all users by location"""
        return cls.query.filter_by(location=location, is_active=True).all()
    
    @classmethod
    def search_users(cls, query, role=None, location=None, is_active=True):
        """Search users with filters"""
        search = cls.query
        
        if query:
            search_term = f"%{query}%"
            search = search.filter(
                db.or_(
                    cls.username.like(search_term),
                    cls.email.like(search_term),
                    cls.first_name.like(search_term),
                    cls.last_name.like(search_term)
                )
            )
        
        if role:
            search = search.filter_by(role=role)
        
        if location:
            search = search.filter_by(location=location)
        
        if is_active is not None:
            search = search.filter_by(is_active=is_active)
        
        return search.order_by(cls.first_name, cls.last_name).all()
    
    def __repr__(self):
        return f'<User {self.username} ({self.get_full_name()})>'