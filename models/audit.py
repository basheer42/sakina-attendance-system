"""
Sakina Gas Company - Audit Log Model
Built from scratch with comprehensive audit trail and security logging
Version 3.0 - Enterprise grade with full complexity
"""

from database import db
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, timedelta # Added timedelta import
from flask import current_app

class AuditLog(db.Model):
    """
    Comprehensive Audit Log model for tracking all system activities
    """
    __tablename__ = 'audit_logs'
    
    # Primary identification
    id = Column(Integer, primary_key=True)
    
    # Event identification
    event_type = Column(String(50), nullable=False, index=True)
    event_category = Column(String(30), nullable=False, default='general', index=True)  # security, data, system, user, etc.
    event_action = Column(String(30), nullable=False, index=True)  # create, update, delete, login, etc.
    
    # Event details
    description = Column(Text, nullable=False)
    details = Column(JSON, nullable=True)  # Additional event details
    
    # User and session information
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True, index=True)
    session_id = Column(String(100), nullable=True)
    impersonated_by = Column(Integer, ForeignKey('users.id'), nullable=True)  # If user is being impersonated
    
    # Target entities (what was affected)
    target_type = Column(String(50), nullable=True, index=True)  # user, employee, attendance, etc.
    target_id = Column(Integer, nullable=True, index=True)
    target_identifier = Column(String(100), nullable=True)  # Human-readable identifier
    
    # Employee context (if action related to an employee)
    employee_id = Column(Integer, ForeignKey('employees.id'), nullable=True, index=True)
    
    # Network and location information
    ip_address = Column(String(45), nullable=True, index=True)  # IPv4 or IPv6
    user_agent = Column(Text, nullable=True)
    hostname = Column(String(255), nullable=True)
    request_method = Column(String(10), nullable=True)  # GET, POST, PUT, DELETE
    request_path = Column(String(500), nullable=True)
    request_query_params = Column(JSON, nullable=True)
    
    # Geographic information
    country = Column(String(50), nullable=True)
    city = Column(String(100), nullable=True)
    timezone = Column(String(50), nullable=True)
    
    # Risk assessment
    risk_level = Column(String(20), nullable=False, default='low', index=True)  # low, medium, high, critical
    risk_score = Column(Integer, nullable=False, default=0)  # 0-100 risk score
    
    # Data changes (for update operations)
    old_values = Column(JSON, nullable=True)  # Previous values
    new_values = Column(JSON, nullable=True)  # New values
    changed_fields = Column(JSON, nullable=True)  # List of changed field names
    
    # System and application context
    application_module = Column(String(50), nullable=True)  # dashboard, employees, attendance, etc.
    application_version = Column(String(20), nullable=True)
    
    # Timing information
    timestamp = Column(DateTime, nullable=False, default=func.current_timestamp(), index=True)
    processing_time_ms = Column(Integer, nullable=True)  # Time taken to process request
    
    # Compliance and legal
    is_compliance_relevant = Column(Boolean, nullable=False, default=False)
    compliance_category = Column(String(50), nullable=True)  # gdpr, kenyan_law, financial, etc.
    retention_period_days = Column(Integer, nullable=False, default=2555)  # 7 years default
    
    # Success and failure tracking
    is_successful = Column(Boolean, nullable=False, default=True)
    error_code = Column(String(20), nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Investigation and analysis
    is_suspicious = Column(Boolean, nullable=False, default=False)
    investigation_status = Column(String(20), nullable=True)  # pending, investigating, resolved, false_positive
    investigated_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    investigation_notes = Column(Text, nullable=True)
    investigation_date = Column(DateTime, nullable=True)
    
    # Automated analysis
    anomaly_score = Column(Integer, nullable=False, default=0)  # 0-100 anomaly score
    ml_analysis = Column(JSON, nullable=True)  # Machine learning analysis results
    
    # Correlation and grouping
    correlation_id = Column(String(100), nullable=True, index=True)  # Group related events
    parent_event_id = Column(Integer, ForeignKey('audit_logs.id'), nullable=True)
    
    # Metadata and extensions
    audit_metadata = Column(JSON, nullable=True)  # Flexible metadata storage (FIX: Renamed from 'metadata')
    tags = Column(JSON, nullable=True)  # Event tags for categorization
    
    # Data retention
    expires_at = Column(DateTime, nullable=True, index=True)  # When this log can be purged
    is_archived = Column(Boolean, nullable=False, default=False)
    archive_date = Column(DateTime, nullable=True)
    
    # Relationships
    # NOTE: User and Employee imports are needed, but circular imports are handled via string literals in the relationship calls (e.g. 'User')
    user = relationship('User', foreign_keys=[user_id], backref='audit_logs_created') # FIX: Renamed backref
    impersonator = relationship('User', foreign_keys=[impersonated_by], backref='audit_logs_impersonated') # FIX: Renamed backref
    employee = relationship('Employee', backref='employee_audit_logs') # FIX: Renamed backref
    investigator = relationship('User', foreign_keys=[investigated_by], backref='audit_logs_investigated') # FIX: Renamed backref
    parent_event = relationship('AuditLog', remote_side=[id], backref='child_events')
    
    # Indexes
    __table_args__ = (
        db.Index('idx_timestamp_type', 'timestamp', 'event_type'),
        db.Index('idx_user_timestamp', 'user_id', 'timestamp'),
        db.Index('idx_risk_timestamp', 'risk_level', 'timestamp'),
        db.Index('idx_target_timestamp', 'target_type', 'target_id', 'timestamp'),
        db.Index('idx_compliance_timestamp', 'is_compliance_relevant', 'timestamp'),
    )
    
    def __init__(self, **kwargs):
        """Initialize audit log with defaults"""
        super(AuditLog, self).__init__()
        
        # Set default metadata
        self.audit_metadata = {} # FIX: Renamed from self.metadata
        self.tags = []
        self.details = {}
        
        # Set timestamp
        self.timestamp = datetime.utcnow()
        
        # Calculate expiry date based on retention period
        if 'retention_period_days' in kwargs:
            retention_days = kwargs['retention_period_days']
        else:
            retention_days = self.retention_period_days or 2555
        
        self.expires_at = self.timestamp + timedelta(days=retention_days)
        
        # Apply any provided kwargs
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        
        # Calculate risk score
        self._calculate_risk_score()
    
    def _calculate_risk_score(self):
        """Calculate automated risk score based on event characteristics"""
        score = 0
        
        # Base score by event type
        high_risk_events = [
            'user_login_failed', 'account_locked', 'password_change', 
            'user_created', 'user_deleted', 'permission_changed',
            'employee_deleted', 'salary_changed', 'data_export'
        ]
        medium_risk_events = [
            'login_successful', 'employee_updated', 'attendance_modified', # FIX: Corrected login event
            'leave_approved', 'performance_review_created'
        ]
        
        if self.event_type in high_risk_events:
            score += 30
        elif self.event_type in medium_risk_events:
            score += 15
        else:
            score += 5
        
        # IP address risk
        if self.ip_address:
            # Check for private vs public IP
            if not self.ip_address.startswith(('192.168.', '10.', '172.16')): # FIX: Corrected 172. range check
                score += 10  # Public IP adds risk
        
        # Time-based risk (after hours)
        if self.timestamp:
            hour = self.timestamp.hour
            if hour < 6 or hour > 22:  # After hours
                score += 15
            elif hour < 7 or hour > 19:  # Early/late
                score += 5
        
        # User agent risk
        if self.user_agent:
            suspicious_agents = ['curl', 'wget', 'python', 'script']
            if any(agent in self.user_agent.lower() for agent in suspicious_agents):
                score += 20
        
        # Error conditions
        if not self.is_successful:
            score += 25
        
        # Set final score and risk level
        self.risk_score = min(100, max(0, score))
        
        if self.risk_score >= 70:
            self.risk_level = 'critical'
        elif self.risk_score >= 50:
            self.risk_level = 'high'
        elif self.risk_score >= 30:
            self.risk_level = 'medium'
        else:
            self.risk_level = 'low'
    
    def mark_suspicious(self, reason, investigated_by_user_id=None):
        """Mark event as suspicious"""
        self.is_suspicious = True
        self.investigation_status = 'pending'
        
        if investigated_by_user_id:
            self.investigated_by = investigated_by_user_id
        
        if not self.investigation_notes:
            self.investigation_notes = ""
        
        self.investigation_notes += f"\n\nMarked suspicious: {reason}"
        self.investigation_date = datetime.utcnow()
    
    def resolve_investigation(self, resolution, investigated_by_user_id, notes=None):
        """Resolve investigation"""
        valid_resolutions = ['resolved', 'false_positive', 'escalated']
        if resolution not in valid_resolutions:
            raise ValueError(f"Invalid resolution. Must be one of: {valid_resolutions}")
        
        self.investigation_status = resolution
        self.investigated_by = investigated_by_user_id
        self.investigation_date = datetime.utcnow()
        
        if notes:
            if not self.investigation_notes:
                self.investigation_notes = ""
            self.investigation_notes += f"\n\nResolved as {resolution}: {notes}"
    
    def add_tag(self, tag):
        """Add tag to event"""
        if self.tags is None:
            self.tags = []
        
        if tag not in self.tags:
            self.tags.append(tag)
    
    def remove_tag(self, tag):
        """Remove tag from event"""
        if self.tags and tag in self.tags:
            self.tags.remove(tag)
    
    def has_tag(self, tag):
        """Check if event has specific tag"""
        return self.tags and tag in self.tags
    
    def get_event_category_display(self):
        """Get human-readable event category"""
        category_map = {
            'security': 'Security',
            'data': 'Data Management',
            'system': 'System',
            'user': 'User Management',
            'employee': 'Employee Management',
            'attendance': 'Attendance',
            'leave': 'Leave Management',
            'performance': 'Performance',
            'compliance': 'Compliance',
            'general': 'General'
        }
        return category_map.get(self.event_category, self.event_category.title())
    
    def get_risk_level_display(self):
        """Get human-readable risk level"""
        risk_map = {
            'low': 'Low Risk',
            'medium': 'Medium Risk',
            'high': 'High Risk',
            'critical': 'Critical Risk'
        }
        return risk_map.get(self.risk_level, self.risk_level.title())
    
    def get_risk_color(self):
        """Get color code for risk level"""
        color_map = {
            'low': '#28A745',      # Green
            'medium': '#FFC107',   # Yellow
            'high': '#FD7E14',     # Orange
            'critical': '#DC3545'  # Red
        }
        return color_map.get(self.risk_level, '#6C757D')
    
    def get_formatted_timestamp(self):
        """Get formatted timestamp"""
        if self.timestamp:
            return self.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        return '-'
    
    def get_user_display(self):
        """Get user display name"""
        # FIX: Added safe check for user relationship existence and required methods
        if self.user:
            if hasattr(self.user, 'get_full_name'):
                return self.user.get_full_name()
            return self.user.username
        return 'System'
    
    def get_target_display(self):
        """Get target display name"""
        if self.target_identifier:
            return self.target_identifier
        elif self.target_type and self.target_id:
            return f"{self.target_type.title()} #{self.target_id}"
        return '-'
    
    def to_dict(self, include_sensitive=False):
        """Convert audit log to dictionary"""
        data = {
            'id': self.id,
            'event_type': self.event_type,
            'event_category': self.event_category,
            'event_category_display': self.get_event_category_display(),
            'event_action': self.event_action,
            'description': self.description,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'formatted_timestamp': self.get_formatted_timestamp(),
            'user_display': self.get_user_display(),
            'target_display': self.get_target_display(),
            'risk_level': self.risk_level,
            'risk_level_display': self.get_risk_level_display(),
            'risk_score': self.risk_score,
            'risk_color': self.get_risk_color(),
            'is_successful': self.is_successful,
            'is_suspicious': self.is_suspicious
        }
        
        if include_sensitive:
            data.update({
                'user_id': self.user_id,
                'target_type': self.target_type,
                'target_id': self.target_id,
                'employee_id': self.employee_id,
                'ip_address': self.ip_address,
                'user_agent': self.user_agent,
                'details': self.details,
                'old_values': self.old_values,
                'new_values': self.new_values,
                'changed_fields': self.changed_fields,
                'error_code': self.error_code,
                'error_message': self.error_message,
                'investigation_status': self.investigation_status,
                'investigation_notes': self.investigation_notes,
                'tags': self.tags,
                'metadata': self.audit_metadata # FIX: Renamed
            })
        
        return data
    
    @classmethod
    def log_event(cls, event_type, description, user_id=None, employee_id=None,
                  target_type=None, target_id=None, target_identifier=None,
                  ip_address=None, user_agent=None, details=None,
                  old_values=None, new_values=None, changed_fields=None,
                  event_category='general', event_action='unknown',
                  risk_level='low', session_id=None, **kwargs):
        """
        Create and save audit log entry
        """
        from flask import request, current_app
        
        # Get request context if available
        if not ip_address and request and hasattr(request, 'environ'):
            ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', 
                                           request.environ.get('REMOTE_ADDR'))
        
        if not user_agent and request and hasattr(request, 'headers'):
            user_agent = request.headers.get('User-Agent')
        
        # Create audit log entry
        audit_log = cls(
            event_type=event_type,
            event_category=event_category,
            event_action=event_action,
            description=description,
            user_id=user_id,
            employee_id=employee_id,
            target_type=target_type,
            target_id=target_id,
            target_identifier=target_identifier,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details or {},
            old_values=old_values,
            new_values=new_values,
            changed_fields=changed_fields,
            risk_level=risk_level,
            session_id=session_id,
            **kwargs
        )
        
        # Add request context if available
        if request and hasattr(request, 'method'):
            audit_log.request_method = request.method
            audit_log.request_path = request.path
            if request.args:
                audit_log.request_query_params = dict(request.args)
        
        # Set application context
        if current_app:
            audit_log.application_version = current_app.config.get('APP_VERSION')
        
        # Save to database
        try:
            db.session.add(audit_log)
            # NOTE: We do NOT commit here. The caller (e.g., a route handler) must commit
            # to ensure the audit log is part of the transaction or to handle rollback.
            # However, for utility/security functions, an immediate commit can be safer.
            # We'll stick to an immediate commit as often done for security logs.
            db.session.commit() 
            return audit_log
        except Exception as e:
            db.session.rollback()
            # Log to application logger as fallback
            if current_app:
                current_app.logger.error(f"Failed to create audit log: {e}")
            return None
    
    @classmethod
    def log_security_event(cls, event_type, description, user_id=None, 
                          risk_level='medium', **kwargs):
        """Log security-related events"""
        return cls.log_event(
            event_type=event_type,
            description=description,
            user_id=user_id,
            event_category='security',
            event_action=event_type.split('_')[0] if event_type else 'security_event', # Infer action
            risk_level=risk_level,
            is_compliance_relevant=True,
            **kwargs
        )
    
    @classmethod
    def log_data_change(cls, target_type, target_id, action, old_values, 
                       new_values, user_id, description=None, **kwargs):
        """Log data modification events"""
        # Calculate changed fields
        changed_fields = []
        if old_values and new_values:
            for key, new_val in new_values.items():
                old_val = old_values.get(key)
                if old_val != new_val:
                    changed_fields.append(key)
        
        return cls.log_event(
            event_type=f"{target_type}_{action}",
            description=description or f"{target_type.title()} {action}d",
            user_id=user_id,
            target_type=target_type,
            target_id=target_id,
            event_category='data',
            event_action=action,
            old_values=old_values,
            new_values=new_values,
            changed_fields=changed_fields,
            **kwargs
        )
    
    @classmethod
    def get_recent_events(cls, limit=50, user_id=None, event_category=None, 
                         risk_level=None):
        """Get recent audit events with filters"""
        query = cls.query
        
        if user_id:
            query = query.filter(cls.user_id == user_id)
        
        if event_category:
            query = query.filter(cls.event_category == event_category)
        
        if risk_level:
            query = query.filter(cls.risk_level == risk_level)
        
        return query.order_by(cls.timestamp.desc()).limit(limit).all()
    
    @classmethod
    def get_suspicious_events(cls, limit=50):
        """Get suspicious events requiring investigation"""
        return cls.query.filter(
            cls.is_suspicious == True,
            cls.investigation_status.in_(['pending', None])
        ).order_by(cls.timestamp.desc()).limit(limit).all()
    
    @classmethod
    def get_events_by_user(cls, user_id, limit=100):
        """Get events for specific user"""
        return cls.query.filter(
            cls.user_id == user_id
        ).order_by(cls.timestamp.desc()).limit(limit).all()
    
    @classmethod
    def get_events_for_target(cls, target_type, target_id, limit=50):
        """Get events for specific target entity"""
        return cls.query.filter(
            cls.target_type == target_type,
            cls.target_id == target_id
        ).order_by(cls.timestamp.desc()).limit(limit).all()
    
    @classmethod
    def cleanup_expired_logs(cls):
        """Clean up expired audit logs"""
        cutoff_date = datetime.utcnow()
        
        # Archive before deletion
        expired_logs = cls.query.filter(
            cls.expires_at <= cutoff_date,
            cls.is_archived == False
        ).all()
        
        archived_count = 0
        for log in expired_logs:
            log.is_archived = True
            log.archive_date = datetime.utcnow()
            archived_count += 1
        
        # Delete very old archived logs (beyond compliance requirements)
        very_old_date = datetime.utcnow() - timedelta(days=3650)  # 10 years
        deleted_count = cls.query.filter(
            cls.archive_date <= very_old_date
        ).delete()
        
        db.session.commit()
        
        return {'archived': archived_count, 'deleted': deleted_count}
    
    def __repr__(self):
        return f'<AuditLog {self.event_type}: {self.description[:50]}>'