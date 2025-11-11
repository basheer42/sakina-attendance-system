"""
Database models for Sakina Gas Attendance System
Professional Grade - Complete Models
"""
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """User model for authentication"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False)  # hr_manager, station_manager, admin
    location = db.Column(db.String(50), nullable=True)  # for station managers
    first_name = db.Column(db.String(50), nullable=True)
    last_name = db.Column(db.String(50), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    @property
    def full_name(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username
    
    def __repr__(self):
        return f'<User {self.username}>'

class Employee(db.Model):
    """Employee model"""
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.String(20), unique=True, nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    location = db.Column(db.String(50), nullable=False)  # head_office, dandora, tassia, kiambu
    shift = db.Column(db.String(10), nullable=True)  # day, night (null for head office)
    department = db.Column(db.String(50), nullable=False)
    position = db.Column(db.String(100), nullable=False)
    hire_date = db.Column(db.Date, nullable=False, default=date.today)
    salary = db.Column(db.Float, nullable=True)
    national_id = db.Column(db.String(20), nullable=True)
    bank_account = db.Column(db.String(50), nullable=True)
    emergency_contact = db.Column(db.String(100), nullable=True)
    emergency_phone = db.Column(db.String(20), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    attendance_records = db.relationship('AttendanceRecord', backref='employee', lazy=True, cascade='all, delete-orphan')
    leave_requests = db.relationship('LeaveRequest', backref='employee', lazy=True, cascade='all, delete-orphan')
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def current_leave_balance(self):
        """Calculate current leave balance for the year"""
        current_year = date.today().year
        approved_leaves = LeaveRequest.query.filter_by(
            employee_id=self.id, 
            status='approved'
        ).filter(
            db.extract('year', LeaveRequest.start_date) == current_year
        ).all()
        
        total_taken = sum(leave.total_days for leave in approved_leaves)
        return max(0, 21 - total_taken)  # 21 days annual leave
    
    def __repr__(self):
        return f'<Employee {self.employee_id}: {self.full_name}>'

class AttendanceRecord(db.Model):
    """Attendance tracking model"""
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=date.today)
    clock_in = db.Column(db.DateTime, nullable=True)
    clock_out = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), nullable=False, default='absent')  # present, absent, late, on_leave
    shift = db.Column(db.String(10), nullable=True)  # day, night
    notes = db.Column(db.Text, nullable=True)
    marked_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    overtime_hours = db.Column(db.Float, default=0.0)
    break_time = db.Column(db.Float, default=0.0)  # in hours
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    marker = db.relationship('User', backref='marked_attendance')
    
    # Unique constraint to prevent duplicate records for same employee/date
    __table_args__ = (db.UniqueConstraint('employee_id', 'date', name='unique_employee_date'),)
    
    @property
    def hours_worked(self):
        """Calculate total hours worked"""
        if self.clock_in and self.clock_out:
            total_time = (self.clock_out - self.clock_in).total_seconds() / 3600
            return max(0, total_time - self.break_time)
        return 0
    
    @property
    def is_late(self):
        """Check if employee was late"""
        if not self.clock_in:
            return False
        
        # Standard work start times
        if self.shift == 'day':
            start_time = self.clock_in.replace(hour=6, minute=0, second=0, microsecond=0)
        elif self.shift == 'night':
            start_time = self.clock_in.replace(hour=18, minute=0, second=0, microsecond=0)
        else:  # Head office
            start_time = self.clock_in.replace(hour=8, minute=0, second=0, microsecond=0)
        
        return self.clock_in > start_time
    
    def __repr__(self):
        return f'<AttendanceRecord {self.employee.employee_id} - {self.date}>'

class LeaveRequest(db.Model):
    """Leave request model"""
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    leave_type = db.Column(db.String(30), nullable=False)  # annual_leave, sick_leave, maternity_leave, etc.
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    total_days = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')  # pending, approved, rejected, cancelled
    requested_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    approved_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)
    rejection_reason = db.Column(db.Text, nullable=True)
    medical_certificate = db.Column(db.String(255), nullable=True)  # file path
    emergency_contact_notified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    requester = db.relationship('User', foreign_keys=[requested_by], backref='leave_requests_made')
    approver = db.relationship('User', foreign_keys=[approved_by], backref='leave_requests_approved')
    
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
            'cancelled': 'secondary'
        }
        return colors.get(self.status, 'secondary')
    
    def __repr__(self):
        return f'<LeaveRequest {self.employee.employee_id} - {self.leave_type}>'

class Holiday(db.Model):
    """Company holidays model"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    date = db.Column(db.Date, nullable=False)
    description = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    is_recurring = db.Column(db.Boolean, default=False)  # for annual holidays
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    creator = db.relationship('User', backref='holidays_created')
    
    def __repr__(self):
        return f'<Holiday {self.name} - {self.date}>'

class AuditLog(db.Model):
    """Audit log for tracking system changes"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    action = db.Column(db.String(100), nullable=False)  # login, create_employee, approve_leave, etc.
    target_type = db.Column(db.String(50), nullable=True)  # employee, leave_request, etc.
    target_id = db.Column(db.Integer, nullable=True)
    details = db.Column(db.Text, nullable=True)  # JSON formatted details
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    user = db.relationship('User', backref='audit_logs')
    
    def __repr__(self):
        return f'<AuditLog {self.action} by {self.user.username}>'