"""
Enhanced Database Models for Sakina Gas Attendance System
Built upon your existing comprehensive model structure with additional professional features
"""
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date, timedelta
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import func, and_, or_
import json

# Import SQLAlchemy but don't create instance here
from flask_sqlalchemy import SQLAlchemy

# Create a placeholder that will be set by the app
db = None

def init_models(database):
    """Initialize models with the database instance from app"""
    global db
    db = database

class User(UserMixin, db.Model):
    """Enhanced User model with comprehensive role management and audit features"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    
    # Enhanced profile information
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    middle_name = db.Column(db.String(50), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    
    # Role and location with enhanced permissions
    role = db.Column(db.String(50), nullable=False)  # hr_manager, station_manager, admin
    location = db.Column(db.String(50), nullable=True)  # head_office, dandora, tassia, kiambu
    department = db.Column(db.String(50), nullable=True)
    
    # Security and session management
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    last_login = db.Column(db.DateTime, nullable=True)
    login_count = db.Column(db.Integer, default=0)
    failed_login_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime, nullable=True)
    password_changed_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Enhanced profile fields
    avatar_url = db.Column(db.String(255), nullable=True)
    signature = db.Column(db.Text, nullable=True)
    preferences = db.Column(db.Text, nullable=True)  # JSON stored preferences
    timezone = db.Column(db.String(50), default='Africa/Nairobi')
    language = db.Column(db.String(10), default='en')
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    updated_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    # Relationships
    created_employees = db.relationship('Employee', foreign_keys='Employee.created_by', backref='creator', lazy='dynamic')
    approved_leaves = db.relationship('LeaveRequest', foreign_keys='LeaveRequest.approved_by', backref='approver', lazy='dynamic')
    marked_attendance = db.relationship('AttendanceRecord', foreign_keys='AttendanceRecord.marked_by', backref='marker', lazy='dynamic')
    
    def set_password(self, password):
        """Set password hash with enhanced security"""
        self.password_hash = generate_password_hash(password)
        self.password_changed_at = datetime.utcnow()
    
    def check_password(self, password):
        """Check password with account lockout protection"""
        if self.is_locked:
            return False
        return check_password_hash(self.password_hash, password)
    
    def record_login_attempt(self, success):
        """Record login attempt for security tracking"""
        if success:
            self.last_login = datetime.utcnow()
            self.login_count += 1
            self.failed_login_attempts = 0
            self.locked_until = None
        else:
            self.failed_login_attempts += 1
            if self.failed_login_attempts >= 5:
                self.locked_until = datetime.utcnow() + timedelta(minutes=30)
        db.session.commit()
    
    @hybrid_property
    def is_locked(self):
        """Check if account is locked"""
        if self.locked_until:
            return datetime.utcnow() < self.locked_until
        return False
    
    @property
    def full_name(self):
        """Get user's full name"""
        if self.middle_name:
            return f"{self.first_name} {self.middle_name} {self.last_name}"
        return f"{self.first_name} {self.last_name}"
    
    @property
    def initials(self):
        """Get user initials for avatar"""
        return f"{self.first_name[0]}{self.last_name[0]}".upper()
    
    def get_permissions(self):
        """Get user permissions based on role"""
        from config import Config
        user_roles = getattr(Config, 'USER_ROLES', {})
        return user_roles.get(self.role, {}).get('permissions', [])
    
    def has_permission(self, permission):
        """Check if user has specific permission"""
        permissions = self.get_permissions()
        return permission in permissions or 'all_permissions' in permissions
    
    def can_manage_location(self, location):
        """Check if user can manage specific location"""
        if self.role in ['hr_manager', 'admin']:
            return True
        return self.location == location
    
    def get_preferences(self):
        """Get user preferences as dict"""
        try:
            return json.loads(self.preferences) if self.preferences else {}
        except:
            return {}
    
    def set_preferences(self, preferences_dict):
        """Set user preferences from dict"""
        self.preferences = json.dumps(preferences_dict)
    
    def __repr__(self):
        return f'<User {self.username} ({self.role})>'

class Employee(db.Model):
    """Enhanced Employee model with comprehensive HR features"""
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.String(20), unique=True, nullable=False, index=True)
    
    # Personal Information
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    middle_name = db.Column(db.String(50), nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    alternative_phone = db.Column(db.String(20), nullable=True)
    
    # Identity and Personal Details
    national_id = db.Column(db.String(20), unique=True, nullable=False)
    date_of_birth = db.Column(db.Date, nullable=True)
    gender = db.Column(db.String(10), nullable=True)  # male, female, other
    marital_status = db.Column(db.String(20), nullable=True)
    nationality = db.Column(db.String(50), default='Kenyan')
    
    # Address Information
    physical_address = db.Column(db.Text, nullable=True)
    postal_address = db.Column(db.String(255), nullable=True)
    city = db.Column(db.String(50), nullable=True)
    county = db.Column(db.String(50), nullable=True)
    
    # Employment Information
    location = db.Column(db.String(50), nullable=False)  # head_office, dandora, tassia, kiambu
    department = db.Column(db.String(50), nullable=False)
    position = db.Column(db.String(100), nullable=False)
    shift = db.Column(db.String(10), nullable=True)  # day, night (null for head office)
    employment_type = db.Column(db.String(20), default='permanent')  # permanent, contract, casual, intern
    employment_status = db.Column(db.String(20), default='active')  # active, inactive, terminated, suspended
    
    # Employment Dates
    hire_date = db.Column(db.Date, nullable=False, default=date.today)
    probation_start = db.Column(db.Date, nullable=True)
    probation_end = db.Column(db.Date, nullable=True)
    confirmation_date = db.Column(db.Date, nullable=True)
    termination_date = db.Column(db.Date, nullable=True)
    last_promotion_date = db.Column(db.Date, nullable=True)
    
    # Compensation
    basic_salary = db.Column(db.Numeric(12, 2), nullable=True)
    currency = db.Column(db.String(3), default='KES')
    pay_frequency = db.Column(db.String(20), default='monthly')  # monthly, weekly, daily
    allowances = db.Column(db.Text, nullable=True)  # JSON stored allowances
    deductions = db.Column(db.Text, nullable=True)  # JSON stored deductions
    
    # Banking Information
    bank_name = db.Column(db.String(100), nullable=True)
    bank_branch = db.Column(db.String(100), nullable=True)
    bank_account = db.Column(db.String(50), nullable=True)
    
    # Emergency Contacts
    emergency_contact_name = db.Column(db.String(100), nullable=True)
    emergency_contact_relationship = db.Column(db.String(50), nullable=True)
    emergency_contact_phone = db.Column(db.String(20), nullable=True)
    emergency_contact_address = db.Column(db.Text, nullable=True)
    
    # Secondary Emergency Contact
    secondary_emergency_name = db.Column(db.String(100), nullable=True)
    secondary_emergency_relationship = db.Column(db.String(50), nullable=True)
    secondary_emergency_phone = db.Column(db.String(20), nullable=True)
    
    # Additional Information
    photo_url = db.Column(db.String(255), nullable=True)
    skills = db.Column(db.Text, nullable=True)  # JSON stored skills
    certifications = db.Column(db.Text, nullable=True)  # JSON stored certifications
    languages_spoken = db.Column(db.Text, nullable=True)  # JSON stored languages
    medical_conditions = db.Column(db.Text, nullable=True)  # Confidential medical info
    notes = db.Column(db.Text, nullable=True)  # HR notes
    
    # System fields
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    updated_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    # Relationships
    attendance_records = db.relationship('AttendanceRecord', backref='employee', lazy='dynamic', cascade='all, delete-orphan')
    leave_requests = db.relationship('LeaveRequest', backref='employee', lazy='dynamic', cascade='all, delete-orphan')
    performance_reviews = db.relationship('PerformanceReview', backref='employee', lazy='dynamic', cascade='all, delete-orphan')
    disciplinary_actions = db.relationship('DisciplinaryAction', backref='employee', lazy='dynamic', cascade='all, delete-orphan')
    
    @property
    def full_name(self):
        """Get employee's full name"""
        if self.middle_name:
            return f"{self.first_name} {self.middle_name} {self.last_name}"
        return f"{self.first_name} {self.last_name}"
    
    @property
    def age(self):
        """Calculate employee age"""
        if self.date_of_birth:
            return (date.today() - self.date_of_birth).days // 365
        return None
    
    @property
    def years_of_service(self):
        """Calculate years of service"""
        end_date = self.termination_date or date.today()
        return (end_date - self.hire_date).days / 365.25
    
    @property
    def months_of_service(self):
        """Calculate months of service"""
        return int(self.years_of_service * 12)
    
    @property
    def is_on_probation(self):
        """Check if employee is still on probation"""
        if self.probation_end:
            return date.today() <= self.probation_end
        return False
    
    @property
    def days_until_confirmation(self):
        """Days until confirmation if on probation"""
        if self.is_on_probation:
            return (self.probation_end - date.today()).days
        return 0
    
    def get_leave_balance(self, leave_type, year=None):
        """Calculate leave balance for specific type and year"""
        if not year:
            year = date.today().year
        
        # Get leave entitlement based on Kenyan law and company policy
        from config import Config
        leave_policies = getattr(Config, 'LEAVE_POLICIES', {})
        entitlement = leave_policies.get(leave_type, {}).get('max_days', 0)
        
        # For annual leave, check if employee is eligible (minimum service period)
        if leave_type == 'annual_leave' and self.years_of_service < 1:
            entitlement = 0
        
        # Calculate used leave days
        year_start = date(year, 1, 1)
        year_end = date(year, 12, 31)
        
        used_days = db.session.query(func.sum(LeaveRequest.total_days)).filter(
            LeaveRequest.employee_id == self.id,
            LeaveRequest.leave_type == leave_type,
            LeaveRequest.status == 'approved',
            LeaveRequest.start_date >= year_start,
            LeaveRequest.end_date <= year_end
        ).scalar() or 0
        
        return max(0, entitlement - used_days)
    
    def get_attendance_summary(self, start_date=None, end_date=None):
        """Get attendance summary for date range"""
        if not start_date:
            start_date = date.today().replace(day=1)  # Start of current month
        if not end_date:
            end_date = date.today()
        
        records = self.attendance_records.filter(
            AttendanceRecord.date >= start_date,
            AttendanceRecord.date <= end_date
        ).all()
        
        summary = {
            'total_days': len(records),
            'present': len([r for r in records if r.status in ['present', 'late']]),
            'absent': len([r for r in records if r.status == 'absent']),
            'late': len([r for r in records if r.status == 'late']),
            'on_leave': len([r for r in records if 'leave' in r.status]),
            'total_hours': sum(r.hours_worked for r in records if r.hours_worked),
            'overtime_hours': sum(r.overtime_hours or 0 for r in records)
        }
        
        summary['attendance_rate'] = (summary['present'] / summary['total_days'] * 100) if summary['total_days'] > 0 else 0
        return summary
    
    def get_allowances(self):
        """Get allowances as dict"""
        try:
            return json.loads(self.allowances) if self.allowances else {}
        except:
            return {}
    
    def set_allowances(self, allowances_dict):
        """Set allowances from dict"""
        self.allowances = json.dumps(allowances_dict)
    
    def get_skills(self):
        """Get skills as list"""
        try:
            return json.loads(self.skills) if self.skills else []
        except:
            return []
    
    def set_skills(self, skills_list):
        """Set skills from list"""
        self.skills = json.dumps(skills_list)
    
    def __repr__(self):
        return f'<Employee {self.employee_id}: {self.full_name}>'

class AttendanceRecord(db.Model):
    """Enhanced Attendance Record model with comprehensive tracking"""
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, index=True)
    
    # Time tracking with enhanced features
    clock_in = db.Column(db.DateTime, nullable=True)
    clock_out = db.Column(db.DateTime, nullable=True)
    break_start = db.Column(db.DateTime, nullable=True)
    break_end = db.Column(db.DateTime, nullable=True)
    lunch_start = db.Column(db.DateTime, nullable=True)
    lunch_end = db.Column(db.DateTime, nullable=True)
    
    # Status and shift information
    status = db.Column(db.String(30), nullable=False)  # present, absent, late, half_day, sick_leave, annual_leave, etc.
    shift = db.Column(db.String(10), nullable=True)  # day, night
    location_marked = db.Column(db.String(50), nullable=True)  # Where attendance was marked
    
    # Performance metrics
    hours_worked = db.Column(db.Numeric(5, 2), nullable=True)
    overtime_hours = db.Column(db.Numeric(5, 2), nullable=True)
    break_time = db.Column(db.Numeric(4, 2), default=0.0)  # In hours
    late_minutes = db.Column(db.Integer, default=0)
    early_departure_minutes = db.Column(db.Integer, default=0)
    
    # Additional information
    notes = db.Column(db.Text, nullable=True)
    marked_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    verification_method = db.Column(db.String(20), default='manual')  # manual, biometric, card, mobile
    ip_address = db.Column(db.String(45), nullable=True)
    
    # Weather and conditions (for field workers)
    weather_conditions = db.Column(db.String(50), nullable=True)
    work_conditions = db.Column(db.String(100), nullable=True)
    
    # Approval and corrections
    is_corrected = db.Column(db.Boolean, default=False)
    corrected_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    correction_reason = db.Column(db.Text, nullable=True)
    requires_approval = db.Column(db.Boolean, default=False)
    approved_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Unique constraint
    __table_args__ = (db.UniqueConstraint('employee_id', 'date', name='unique_employee_date'),)
    
    # Additional relationships
    corrector = db.relationship('User', foreign_keys=[corrected_by], backref='attendance_corrections')
    attendance_approver = db.relationship('User', foreign_keys=[approved_by], backref='attendance_approvals')
    
    @property
    def total_hours_worked(self):
        """Calculate total hours worked including breaks"""
        if self.clock_in and self.clock_out:
            total_time = (self.clock_out - self.clock_in).total_seconds() / 3600
            return max(0, total_time - self.break_time)
        return 0
    
    @property
    def is_late(self):
        """Check if employee was late"""
        if not self.clock_in:
            return False
        
        # Get standard start times from config
        from config import Config
        locations = getattr(Config, 'COMPANY_LOCATIONS', {})
        location_info = locations.get(self.employee.location, {})
        
        if self.shift == 'day':
            expected_time = self.clock_in.replace(hour=6, minute=0, second=0, microsecond=0)
        elif self.shift == 'night':
            expected_time = self.clock_in.replace(hour=18, minute=0, second=0, microsecond=0)
        else:  # Head office
            expected_time = self.clock_in.replace(hour=8, minute=0, second=0, microsecond=0)
        
        # Grace period from config
        grace_period = getattr(Config, 'ATTENDANCE_GRACE_PERIOD', 15)
        expected_time += timedelta(minutes=grace_period)
        
        return self.clock_in > expected_time
    
    @property
    def is_overtime(self):
        """Check if work qualifies for overtime"""
        from config import Config
        overtime_threshold = getattr(Config, 'OVERTIME_THRESHOLD', 8)
        return self.total_hours_worked > overtime_threshold
    
    def calculate_overtime(self):
        """Calculate overtime hours"""
        if self.is_overtime:
            from config import Config
            overtime_threshold = getattr(Config, 'OVERTIME_THRESHOLD', 8)
            return max(0, self.total_hours_worked - overtime_threshold)
        return 0
    
    def update_hours_worked(self):
        """Update calculated hours worked"""
        self.hours_worked = self.total_hours_worked
        self.overtime_hours = self.calculate_overtime()
        
        if self.is_late:
            expected_start = self.clock_in.replace(hour=8, minute=0, second=0, microsecond=0)
            if self.shift == 'day':
                expected_start = self.clock_in.replace(hour=6, minute=0, second=0, microsecond=0)
            elif self.shift == 'night':
                expected_start = self.clock_in.replace(hour=18, minute=0, second=0, microsecond=0)
            
            self.late_minutes = max(0, (self.clock_in - expected_start).total_seconds() / 60)
    
    def __repr__(self):
        return f'<AttendanceRecord {self.employee.employee_id} - {self.date} ({self.status})>'

class LeaveRequest(db.Model):
    """Enhanced Leave Request model with comprehensive leave management"""
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    
    # Leave details
    leave_type = db.Column(db.String(30), nullable=False)  # annual_leave, sick_leave, maternity_leave, etc.
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    total_days = db.Column(db.Integer, nullable=False)
    working_days = db.Column(db.Integer, nullable=True)  # Excluding weekends and holidays
    
    # Request details
    reason = db.Column(db.Text, nullable=False)
    emergency_contact = db.Column(db.String(100), nullable=True)
    emergency_phone = db.Column(db.String(20), nullable=True)
    handover_notes = db.Column(db.Text, nullable=True)
    replacement_employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=True)
    
    # Supporting documentation
    medical_certificate = db.Column(db.String(255), nullable=True)  # File path
    supporting_documents = db.Column(db.Text, nullable=True)  # JSON list of file paths
    
    # Status and workflow
    status = db.Column(db.String(20), nullable=False, default='pending')  # pending, approved, rejected, cancelled, withdrawn
    priority = db.Column(db.String(10), default='normal')  # urgent, high, normal, low
    
    # Approval workflow
    requested_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    approved_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)
    rejection_reason = db.Column(db.Text, nullable=True)
    
    # HR and compliance
    hr_notes = db.Column(db.Text, nullable=True)
    compliance_checked = db.Column(db.Boolean, default=False)
    exceeds_entitlement = db.Column(db.Boolean, default=False)
    requires_medical_cert = db.Column(db.Boolean, default=False)
    
    # Notification and communication
    employee_notified = db.Column(db.Boolean, default=False)
    manager_notified = db.Column(db.Boolean, default=False)
    hr_notified = db.Column(db.Boolean, default=False)
    emergency_contact_notified = db.Column(db.Boolean, default=False)
    
    # Return from leave
    expected_return_date = db.Column(db.Date, nullable=True)
    actual_return_date = db.Column(db.Date, nullable=True)
    return_notes = db.Column(db.Text, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    requester = db.relationship('User', foreign_keys=[requested_by], backref='leave_requests_made')
    approver = db.relationship('User', foreign_keys=[approved_by], backref='leave_requests_approved')
    replacement = db.relationship('Employee', foreign_keys=[replacement_employee_id], backref='covering_for_leaves')
    
    @property
    def duration_text(self):
        """Human readable duration"""
        if self.total_days == 1:
            return "1 day"
        return f"{self.total_days} days"
    
    @property
    def status_color(self):
        """Bootstrap color class for status"""
        colors = {
            'pending': 'warning',
            'approved': 'success', 
            'rejected': 'danger',
            'cancelled': 'secondary',
            'withdrawn': 'info'
        }
        return colors.get(self.status, 'secondary')
    
    @property
    def priority_color(self):
        """Bootstrap color class for priority"""
        colors = {
            'urgent': 'danger',
            'high': 'warning',
            'normal': 'info',
            'low': 'secondary'
        }
        return colors.get(self.priority, 'info')
    
    def validate_kenyan_law(self):
        """Validate leave request against Kenyan Employment Act 2007"""
        from config import Config
        warnings = []
        
        # Get leave policies
        leave_policies = getattr(Config, 'LEAVE_POLICIES', {})
        policy = leave_policies.get(self.leave_type, {})
        
        if not policy:
            warnings.append(f"No policy defined for {self.leave_type}")
            return warnings
        
        max_days = policy.get('max_days')
        if max_days and self.total_days > max_days:
            warnings.append(f"Requested {self.total_days} days exceeds maximum {max_days} days for {self.leave_type}")
            self.exceeds_entitlement = True
        
        # Check if medical certificate is required
        if self.leave_type == 'sick_leave' and self.total_days > 7:
            if not self.medical_certificate:
                warnings.append("Medical certificate required for sick leave exceeding 7 days")
                self.requires_medical_cert = True
        
        # Check annual leave eligibility
        if self.leave_type == 'annual_leave' and self.employee.years_of_service < 1:
            warnings.append("Employee not eligible for annual leave (minimum 12 months service required)")
            self.exceeds_entitlement = True
        
        # Check notice period
        notice_days = policy.get('notice_days', 0)
        if notice_days > 0:
            notice_given = (self.start_date - date.today()).days
            if notice_given < notice_days:
                warnings.append(f"Insufficient notice: {notice_given} days given, {notice_days} required")
        
        return warnings
    
    def calculate_working_days(self):
        """Calculate working days excluding weekends and holidays"""
        working_days = 0
        current_date = self.start_date
        
        # Get company holidays
        holidays = Holiday.query.filter(
            Holiday.date >= self.start_date,
            Holiday.date <= self.end_date,
            Holiday.is_active == True
        ).all()
        holiday_dates = [h.date for h in holidays]
        
        while current_date <= self.end_date:
            # Skip weekends (Saturday=5, Sunday=6)
            if current_date.weekday() < 5 and current_date not in holiday_dates:
                working_days += 1
            current_date += timedelta(days=1)
        
        self.working_days = working_days
        return working_days
    
    def get_supporting_documents(self):
        """Get supporting documents as list"""
        try:
            return json.loads(self.supporting_documents) if self.supporting_documents else []
        except:
            return []
    
    def set_supporting_documents(self, documents_list):
        """Set supporting documents from list"""
        self.supporting_documents = json.dumps(documents_list)
    
    def __repr__(self):
        return f'<LeaveRequest {self.employee.employee_id} - {self.leave_type} ({self.status})>'

# Additional Models for Enhanced Features

class Holiday(db.Model):
    """Enhanced Holiday model with recurring holidays support"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    date = db.Column(db.Date, nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    # Holiday types and categories
    holiday_type = db.Column(db.String(20), default='public')  # public, company, religious, regional
    category = db.Column(db.String(30), nullable=True)  # national, religious, cultural
    
    # Recurring holiday settings
    is_recurring = db.Column(db.Boolean, default=False)
    recurrence_pattern = db.Column(db.String(50), nullable=True)  # yearly, monthly, weekly
    
    # Location and applicability
    applies_to_locations = db.Column(db.Text, nullable=True)  # JSON list of locations
    applies_to_departments = db.Column(db.Text, nullable=True)  # JSON list of departments
    
    # Status and management
    is_active = db.Column(db.Boolean, default=True)
    is_paid = db.Column(db.Boolean, default=True)
    
    # Timestamps
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    creator = db.relationship('User', backref='holidays_created')
    
    def applies_to_location(self, location):
        """Check if holiday applies to specific location"""
        if not self.applies_to_locations:
            return True  # Applies to all locations if not specified
        try:
            locations = json.loads(self.applies_to_locations)
            return location in locations
        except:
            return True
    
    def __repr__(self):
        return f'<Holiday {self.name} - {self.date}>'

class PerformanceReview(db.Model):
    """Employee performance review model"""
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    reviewer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Review details
    review_period_start = db.Column(db.Date, nullable=False)
    review_period_end = db.Column(db.Date, nullable=False)
    review_type = db.Column(db.String(30), default='annual')  # probation, mid-year, annual, special
    
    # Ratings and scores
    overall_rating = db.Column(db.String(20), nullable=True)  # excellent, good, satisfactory, needs_improvement, poor
    overall_score = db.Column(db.Numeric(3, 1), nullable=True)  # 1.0 to 5.0
    
    # Review sections
    achievements = db.Column(db.Text, nullable=True)
    areas_for_improvement = db.Column(db.Text, nullable=True)
    goals_for_next_period = db.Column(db.Text, nullable=True)
    training_recommendations = db.Column(db.Text, nullable=True)
    
    # Employee feedback
    employee_comments = db.Column(db.Text, nullable=True)
    employee_signature_date = db.Column(db.DateTime, nullable=True)
    
    # Status
    status = db.Column(db.String(20), default='draft')  # draft, completed, acknowledged
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    reviewer = db.relationship('User', backref='performance_reviews_conducted')
    
    def __repr__(self):
        return f'<PerformanceReview {self.employee.employee_id} - {self.review_period_end}>'

class DisciplinaryAction(db.Model):
    """Disciplinary action tracking model"""
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    issued_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Action details
    action_type = db.Column(db.String(30), nullable=False)  # verbal_warning, written_warning, suspension, termination
    severity = db.Column(db.String(20), default='minor')  # minor, major, severe
    
    # Incident details
    incident_date = db.Column(db.Date, nullable=False)
    description = db.Column(db.Text, nullable=False)
    policy_violated = db.Column(db.String(255), nullable=True)
    
    # Action taken
    action_description = db.Column(db.Text, nullable=False)
    effective_date = db.Column(db.Date, nullable=False)
    expiry_date = db.Column(db.Date, nullable=True)  # When warning expires
    
    # Employee response
    employee_acknowledged = db.Column(db.Boolean, default=False)
    employee_comments = db.Column(db.Text, nullable=True)
    employee_signature_date = db.Column(db.DateTime, nullable=True)
    
    # Follow-up
    requires_followup = db.Column(db.Boolean, default=False)
    followup_date = db.Column(db.Date, nullable=True)
    followup_notes = db.Column(db.Text, nullable=True)
    
    # Status
    status = db.Column(db.String(20), default='active')  # active, expired, appealed, overturned
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    issuer = db.relationship('User', backref='disciplinary_actions_issued')
    
    def __repr__(self):
        return f'<DisciplinaryAction {self.employee.employee_id} - {self.action_type}>'

class AuditLog(db.Model):
    """Enhanced Audit log for comprehensive system tracking"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Action details
    action = db.Column(db.String(100), nullable=False)  # login, create_employee, approve_leave, etc.
    target_type = db.Column(db.String(50), nullable=True)  # employee, leave_request, attendance, etc.
    target_id = db.Column(db.Integer, nullable=True)
    
    # Change tracking
    old_values = db.Column(db.Text, nullable=True)  # JSON of old values
    new_values = db.Column(db.Text, nullable=True)  # JSON of new values
    changes_summary = db.Column(db.Text, nullable=True)  # Human-readable summary
    
    # Request details
    details = db.Column(db.Text, nullable=True)  # Additional details
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.Text, nullable=True)
    session_id = db.Column(db.String(255), nullable=True)
    
    # Context information
    location_context = db.Column(db.String(50), nullable=True)  # Location where action was performed
    department_context = db.Column(db.String(50), nullable=True)
    
    # Risk and compliance
    risk_level = db.Column(db.String(20), default='low')  # low, medium, high, critical
    compliance_relevant = db.Column(db.Boolean, default=False)
    requires_review = db.Column(db.Boolean, default=False)
    
    # Status
    is_sensitive = db.Column(db.Boolean, default=False)  # For sensitive data access
    is_automated = db.Column(db.Boolean, default=False)  # System vs user action
    
    # Timestamp
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Relationship
    user = db.relationship('User', backref='audit_logs')
    
    def get_old_values(self):
        """Get old values as dict"""
        try:
            return json.loads(self.old_values) if self.old_values else {}
        except:
            return {}
    
    def set_old_values(self, values_dict):
        """Set old values from dict"""
        self.old_values = json.dumps(values_dict)
    
    def get_new_values(self):
        """Get new values as dict"""
        try:
            return json.loads(self.new_values) if self.new_values else {}
        except:
            return {}
    
    def set_new_values(self, values_dict):
        """Set new values from dict"""
        self.new_values = json.dumps(values_dict)
    
    @staticmethod
    def log_action(user_id, action, target_type=None, target_id=None, 
                   old_values=None, new_values=None, details=None, 
                   ip_address=None, risk_level='low'):
        """Helper method to log actions"""
        log_entry = AuditLog(
            user_id=user_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            details=details,
            ip_address=ip_address,
            risk_level=risk_level
        )
        
        if old_values:
            log_entry.set_old_values(old_values)
        if new_values:
            log_entry.set_new_values(new_values)
        
        db.session.add(log_entry)
        db.session.commit()
        
        return log_entry
    
    def __repr__(self):
        return f'<AuditLog {self.action} by User {self.user_id} at {self.timestamp}>'

# Model Events and Triggers
@db.event.listens_for(Employee, 'before_update')
def log_employee_changes(mapper, connection, target):
    """Log employee record changes"""
    if hasattr(target, '_sa_instance_state'):
        changes = {}
        for attr in mapper.columns.keys():
            hist = db.inspect(target).attrs.get(attr).history
            if hist.has_changes():
                changes[attr] = {
                    'old': hist.deleted[0] if hist.deleted else None,
                    'new': hist.added[0] if hist.added else None
                }
        
        if changes and hasattr(target, 'updated_by') and target.updated_by:
            # Log the changes (will be committed after the main transaction)
            from flask import g
            g.pending_audit_log = {
                'user_id': target.updated_by,
                'action': 'update_employee',
                'target_type': 'employee',
                'target_id': target.id,
                'old_values': {k: v['old'] for k, v in changes.items()},
                'new_values': {k: v['new'] for k, v in changes.items()}
            }