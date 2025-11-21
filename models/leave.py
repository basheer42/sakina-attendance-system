"""
Leave Model - Leave Request Management
This file contains only the LeaveRequest model
"""

from database import db
from datetime import datetime, date, timedelta

class LeaveRequest(db.Model):
    """Leave request model for managing employee leave"""
    
    __tablename__ = 'leave_requests'
    
    # Primary fields
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False, index=True)
    
    # Leave details
    leave_type = db.Column(db.String(50), nullable=False, index=True)  # annual, sick, maternity, etc.
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    total_days = db.Column(db.Integer, nullable=False)
    
    # Request information
    reason = db.Column(db.Text, nullable=False)
    emergency_contact = db.Column(db.String(100), nullable=True)
    emergency_phone = db.Column(db.String(20), nullable=True)
    
    # Medical information (for sick/maternity leave)
    medical_certificate = db.Column(db.Boolean, default=False, nullable=False)
    doctor_name = db.Column(db.String(100), nullable=True)
    medical_facility = db.Column(db.String(100), nullable=True)
    
    # Status and approval
    status = db.Column(db.String(20), default='pending', nullable=False)  # pending, approved, rejected, cancelled
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)
    
    # Approval details
    approval_notes = db.Column(db.Text, nullable=True)
    rejection_reason = db.Column(db.Text, nullable=True)
    
    # System fields
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    requested_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Who made the request (manager for employee)
    
    # Kenyan labor law compliance
    law_compliant = db.Column(db.Boolean, default=True, nullable=False)
    law_warnings = db.Column(db.Text, nullable=True)  # JSON string of warnings
    hr_override = db.Column(db.Boolean, default=False, nullable=False)
    override_reason = db.Column(db.Text, nullable=True)
    
    # Indexes for better performance
    __table_args__ = (
        db.Index('idx_leave_status_type', 'status', 'leave_type'),
        db.Index('idx_leave_dates', 'start_date', 'end_date'),
        db.Index('idx_leave_employee_year', 'employee_id', 'start_date'),
    )
    
    @property
    def duration_display(self):
        """Get formatted duration display"""
        if self.total_days == 1:
            return "1 day"
        return f"{self.total_days} days"
    
    @property
    def is_pending(self):
        """Check if request is pending"""
        return self.status == 'pending'
    
    @property
    def is_approved(self):
        """Check if request is approved"""
        return self.status == 'approved'
    
    @property
    def is_rejected(self):
        """Check if request is rejected"""
        return self.status == 'rejected'
    
    @property
    def is_active(self):
        """Check if leave is currently active"""
        if not self.is_approved:
            return False
        today = date.today()
        return self.start_date <= today <= self.end_date
    
    @property
    def is_upcoming(self):
        """Check if leave is upcoming"""
        if not self.is_approved:
            return False
        return self.start_date > date.today()
    
    @property
    def is_past(self):
        """Check if leave is in the past"""
        return self.end_date < date.today()
    
    @property
    def status_display(self):
        """Get display-friendly status"""
        status_map = {
            'pending': 'Pending Approval',
            'approved': 'Approved',
            'rejected': 'Rejected',
            'cancelled': 'Cancelled'
        }
        return status_map.get(self.status, self.status.title())
    
    @property
    def status_color(self):
        """Get color class for status display"""
        color_map = {
            'pending': 'warning',
            'approved': 'success',
            'rejected': 'danger',
            'cancelled': 'secondary'
        }
        return color_map.get(self.status, 'secondary')
    
    @property
    def leave_type_display(self):
        """Get display-friendly leave type"""
        type_map = {
            'annual_leave': 'Annual Leave',
            'sick_leave': 'Sick Leave',
            'maternity_leave': 'Maternity Leave',
            'paternity_leave': 'Paternity Leave',
            'compassionate_leave': 'Compassionate Leave',
            'study_leave': 'Study Leave',
            'unpaid_leave': 'Unpaid Leave'
        }
        return type_map.get(self.leave_type, self.leave_type.replace('_', ' ').title())
    
    def calculate_working_days(self):
        """Calculate working days between start and end date"""
        current_date = self.start_date
        working_days = 0
        
        while current_date <= self.end_date:
            # Skip weekends (Saturday=5, Sunday=6)
            if current_date.weekday() < 5:
                working_days += 1
            current_date += timedelta(days=1)
        
        return working_days
    
    def validate_kenyan_law(self):
        """Validate leave request against Kenyan labor laws"""
        from config import Config
        warnings = []
        
        # Get leave law configuration
        kenyan_laws = Config.KENYAN_LABOR_LAWS.get(self.leave_type, {})
        
        if not kenyan_laws:
            warnings.append(f"Leave type '{self.leave_type_display}' not recognized in Kenyan law.")
            return warnings
        
        max_days = kenyan_laws.get('max_days', 0)
        
        # Check maximum days
        if self.total_days > max_days:
            warnings.append(f"{self.leave_type_display} exceeds maximum {max_days} days allowed by Kenyan law. Requested: {self.total_days} days.")
        
        # Check minimum service period for annual leave
        if self.leave_type == 'annual_leave':
            min_service_months = kenyan_laws.get('min_service_months', 12)
            employee_service_months = self.employee.years_of_service * 12
            if employee_service_months < min_service_months:
                warnings.append(f"Annual leave requires minimum {min_service_months} months service. Employee has {employee_service_months} months.")
        
        # Check notice period
        notice_days = kenyan_laws.get('notice_days', 0)
        if notice_days > 0:
            days_notice = (self.start_date - date.today()).days
            if days_notice < notice_days:
                warnings.append(f"{self.leave_type_display} requires {notice_days} days notice. Only {days_notice} days given.")
        
        # Check medical certificate requirement
        if self.leave_type == 'sick_leave':
            requires_cert_after = kenyan_laws.get('requires_certificate_after', 3)
            if self.total_days > requires_cert_after and not self.medical_certificate:
                warnings.append(f"Sick leave exceeding {requires_cert_after} days requires medical certificate.")
        
        # Check maternity leave specifics
        if self.leave_type == 'maternity_leave':
            if self.total_days > 90:
                warnings.append("Maternity leave exceeds 90 days maximum allowed by Kenyan law.")
            if not self.medical_certificate:
                warnings.append("Maternity leave requires medical certificate.")
        
        # Check paternity leave specifics
        if self.leave_type == 'paternity_leave':
            if self.total_days > 14:
                warnings.append("Paternity leave exceeds 14 days maximum allowed by Kenyan law.")
        
        return warnings
    
    def approve(self, approved_by_user, notes=None):
        """Approve the leave request"""
        self.status = 'approved'
        self.approved_by = approved_by_user.id
        self.approved_at = datetime.utcnow()
        self.approval_notes = notes
        
        # Mark as non-compliant if there are warnings
        warnings = self.validate_kenyan_law()
        if warnings:
            self.law_compliant = False
            self.law_warnings = str(warnings)
    
    def reject(self, rejected_by_user, reason):
        """Reject the leave request"""
        self.status = 'rejected'
        self.approved_by = rejected_by_user.id
        self.approved_at = datetime.utcnow()
        self.rejection_reason = reason
    
    def cancel(self):
        """Cancel the leave request"""
        if self.status in ['pending', 'approved']:
            self.status = 'cancelled'
            self.updated_at = datetime.utcnow()
    
    @classmethod
    def get_pending_requests(cls, location=None):
        """Get pending leave requests"""
        query = cls.query.filter_by(status='pending')
        
        if location:
            from models.employee import Employee
            query = query.join(Employee).filter(Employee.location == location)
        
        return query.order_by(cls.created_at).all()
    
    @classmethod
    def get_employee_balance(cls, employee_id, leave_type, year=None):
        """Get employee's leave balance for specific type"""
        if year is None:
            year = date.today().year
        
        year_start = date(year, 1, 1)
        year_end = date(year, 12, 31)
        
        # Get approved leave days for this year
        used_days = db.session.query(db.func.sum(cls.total_days)).filter(
            cls.employee_id == employee_id,
            cls.leave_type == leave_type,
            cls.status == 'approved',
            cls.start_date >= year_start,
            cls.end_date <= year_end
        ).scalar() or 0
        
        return used_days
    
    def __repr__(self):
        return f'<LeaveRequest {self.employee_id}: {self.leave_type} ({self.start_date} to {self.end_date})>'