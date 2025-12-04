"""
Sakina Gas Company - Leave Request Model
Built from scratch with comprehensive leave management and Kenyan law compliance
Version 3.0 - Enterprise grade with full complexity
"""

from database import db
from decimal import Decimal # FIX: Added missing import
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON, Date, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, date, timedelta
from decimal import Decimal

class LeaveRequest(db.Model):
    """
    Comprehensive Leave Request model with Kenyan labor law compliance
    """
    __tablename__ = 'leave_requests'
    
    # Primary identification
    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey('employees.id'), nullable=False, index=True)
    request_number = Column(String(20), unique=True, nullable=False, index=True)
    
    # Leave details
    leave_type = Column(String(30), nullable=False, index=True)  # annual, sick, maternity, paternity, compassionate
    start_date = Column(Date, nullable=False, index=True)
    end_date = Column(Date, nullable=False, index=True)
    return_date = Column(Date, nullable=True)  # Expected return date (nullable initially)
    total_days = Column(Numeric(5, 2), nullable=False)  # Including half days
    working_days = Column(Integer, nullable=False, default=0) # FIX: Default added
    
    # Request details
    reason = Column(Text, nullable=False)
    emergency_contact = Column(JSON, nullable=True)  # Contact during leave
    handover_notes = Column(Text, nullable=True)
    covering_employee_id = Column(Integer, ForeignKey('employees.id'), nullable=True)
    
    # Medical details (for sick/maternity leave)
    medical_certificate_required = Column(Boolean, nullable=False, default=False)
    medical_certificate_provided = Column(Boolean, nullable=False, default=False)
    medical_certificate_file = Column(String(255), nullable=True)
    doctor_name = Column(String(100), nullable=True)
    hospital_clinic = Column(String(150), nullable=True)
    
    # Approval workflow
    status = Column(String(20), nullable=False, default='pending', index=True)  # pending, approved, rejected, cancelled
    requested_date = Column(DateTime, nullable=False, default=func.current_timestamp())
    requested_by = Column(Integer, ForeignKey('users.id'), nullable=True)  # If requested by manager
    
    # First level approval (immediate supervisor)
    supervisor_approval_status = Column(String(20), nullable=True, default='pending') # FIX: Default added
    supervisor_approved_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    supervisor_approval_date = Column(DateTime, nullable=True)
    supervisor_comments = Column(Text, nullable=True)
    
    # Final approval (HR)
    hr_approval_status = Column(String(20), nullable=True, default='pending') # FIX: Default added
    hr_approved_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    hr_approval_date = Column(DateTime, nullable=True)
    hr_comments = Column(Text, nullable=True)
    
    # Leave balance impact
    leave_balance_before = Column(Numeric(5, 2), nullable=True)
    leave_balance_after = Column(Numeric(5, 2), nullable=True)
    
    # Actual leave taken
    actual_start_date = Column(Date, nullable=True)
    actual_end_date = Column(Date, nullable=True)
    actual_return_date = Column(Date, nullable=True)
    actual_days_taken = Column(Numeric(5, 2), nullable=True)
    
    # Extensions and modifications
    is_extended = Column(Boolean, nullable=False, default=False)
    extension_days = Column(Integer, nullable=False, default=0)
    extension_reason = Column(Text, nullable=True)
    extension_approved_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    extension_approval_date = Column(DateTime, nullable=True)
    
    # Early return
    returned_early = Column(Boolean, nullable=False, default=False)
    early_return_date = Column(Date, nullable=True)
    early_return_reason = Column(Text, nullable=True)
    
    # Payment details
    is_paid_leave = Column(Boolean, nullable=False, default=True)
    pay_percentage = Column(Numeric(5, 2), nullable=False, default=100.00)  # Percentage of salary
    
    # Compliance and validation
    is_compliant = Column(Boolean, nullable=False, default=True)
    compliance_notes = Column(Text, nullable=True)
    legal_validation = Column(JSON, nullable=True)  # Kenyan law compliance check results
    
    # Cancellation details
    is_cancelled = Column(Boolean, nullable=False, default=False)
    cancellation_date = Column(DateTime, nullable=True)
    cancellation_reason = Column(Text, nullable=True)
    cancelled_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    
    # System metadata
    created_date = Column(DateTime, nullable=False, default=func.current_timestamp())
    created_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    last_updated = Column(DateTime, nullable=False, default=func.current_timestamp(), onupdate=func.current_timestamp())
    updated_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    
    # Flexible data storage
    leave_metadata = Column(JSON, nullable=True) # FIX: Renamed from 'metadata'
    attachments = Column(JSON, nullable=True)  # File attachments
    workflow_history = Column(JSON, nullable=True)  # Approval workflow history
    
    # Notifications and reminders
    email_notifications_sent = Column(JSON, nullable=True)
    reminder_date = Column(Date, nullable=True)  # Reminder for return
    
    # HR processing
    processed_by_hr = Column(Boolean, nullable=False, default=False)
    hr_processing_date = Column(DateTime, nullable=True)
    hr_processing_notes = Column(Text, nullable=True)
    
    # Relationships
    # All relationships use string literals - safe from direct circular imports
    covering_employee = relationship('Employee', foreign_keys=[covering_employee_id], backref='covering_for')
    requested_by_user = relationship('User', foreign_keys=[requested_by], backref='leave_requests_submitted') # FIX: Added backref
    supervisor_approver = relationship('User', foreign_keys=[supervisor_approved_by], backref='leave_requests_supervisor_approved') # FIX: Added backref
    hr_approver = relationship('User', foreign_keys=[hr_approved_by], backref='leave_requests_hr_approved') # FIX: Added backref
    extension_approver = relationship('User', foreign_keys=[extension_approved_by])
    cancelled_by_user = relationship('User', foreign_keys=[cancelled_by])
    creator = relationship('User', foreign_keys=[created_by])
    updater = relationship('User', foreign_keys=[updated_by])
    
    def __init__(self, **kwargs):
        """Initialize leave request with defaults"""
        super(LeaveRequest, self).__init__()
        
        # Set default metadata
        self.leave_metadata = {} # FIX: Renamed from self.metadata
        self.attachments = []
        self.workflow_history = []
        self.email_notifications_sent = []
        self.legal_validation = {}
        
        # Set creation timestamp
        self.created_date = datetime.utcnow()
        
        # Apply any provided kwargs
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        
        # Generate request number if not provided
        if not self.request_number:
            self.request_number = self.generate_request_number()
        
        # Calculate working days and return date on init if dates are present
        if self.start_date and self.end_date:
            self.working_days = self.calculate_working_days()
            self.return_date = self._calculate_return_date()
    
    def generate_request_number(self):
        """Generate unique leave request number"""
        year = datetime.now().year
        
        # Count existing requests this year
        year_start = date(year, 1, 1)
        year_end = date(year, 12, 31)
        
        # FIX: Using direct query on the model is safe within a model method
        count = LeaveRequest.query.filter(
            LeaveRequest.requested_date.between(year_start, year_end)
        ).count()
        
        return f"LR{year}{count + 1:04d}"
    
    def calculate_working_days(self):
        """Calculate working days excluding weekends and holidays"""
        from kenyan_labor_laws import calculate_working_days as kl_working_days
        from models.holiday import Holiday
        
        if self.start_date is None or self.end_date is None:
            return 0
        
        # FIX: Pass the Holiday.is_holiday checker to the utility function
        return kl_working_days(
            self.start_date, 
            self.end_date, 
            holiday_checker=Holiday.is_holiday
        )
    
    def validate_against_kenyan_law(self):
        """Validate leave request against Kenyan Employment Act 2007"""
        from kenyan_labor_laws import validate_leave_request as kl_validate_request
        from kenyan_labor_laws import create_leave_warning_message as kl_create_warning_message

        # NOTE: Using self.employee assumes the relationship has been eagerly loaded or is available
        if not self.employee:
            return False, "Employee record not found for validation"
        
        # Get validation warnings
        validation_warnings = kl_validate_request(
            self.employee, # Employee ORM object
            self.leave_type, 
            float(self.total_days), 
            self.start_date,
            employee_service_months=self.employee.calculate_months_of_service(),
            employee_gender=self.employee.gender
        )
        
        # Create consolidated message
        message = kl_create_warning_message(validation_warnings)

        # Determine compliance status
        is_compliant = not any(w['level'] == 'error' for w in validation_warnings)
        
        # Store validation results
        self.legal_validation = {
            'is_compliant': is_compliant,
            'warnings': validation_warnings,
            'validation_date': datetime.utcnow().isoformat(),
            'employee_gender': self.employee.gender
        }
        
        self.is_compliant = is_compliant
        self.compliance_notes = message
        
        return is_compliant, message
    
    def check_leave_balance(self):
        """Check if employee has sufficient leave balance"""
        if not self.employee:
            return False, "Employee record not found for balance check"
            
        if self.leave_type in ['annual_leave', 'sick_leave']:
            # FIX: Use employee's dedicated balance calculation method
            available_balance = self.employee.calculate_leave_balance(self.leave_type, self.start_date.year)
        else:
            return True, "Leave type doesn't require hard balance check (e.g., Maternity, Paternity)"
        
        self.leave_balance_before = Decimal(str(available_balance))
        
        if float(self.total_days) > float(available_balance):
            return False, f"Insufficient leave balance. Available: {available_balance:.1f} days"
        
        self.leave_balance_after = Decimal(str(available_balance)) - self.total_days
        return True, "Sufficient leave balance"
    
    def submit_request(self, submitted_by_user_id=None):
        """Submit leave request for approval"""
        # Validate against Kenyan law
        is_valid, validation_message = self.validate_against_kenyan_law()
        
        # Check leave balance for applicable leave types
        has_balance, balance_message = self.check_leave_balance()
        
        # Only raise error if there's a legal or balance violation
        if not is_valid and 'LEGAL VIOLATIONS' in validation_message:
            raise ValueError(validation_message)
        
        if not has_balance:
            raise ValueError(balance_message)
        
        # Calculate working days and return date
        self.working_days = self.calculate_working_days()
        self.return_date = self._calculate_return_date()
        
        # Set request details
        self.status = 'pending'
        self.requested_date = datetime.utcnow()
        if submitted_by_user_id:
            self.requested_by = submitted_by_user_id
        
        # Add to workflow history
        self._add_workflow_entry('submitted', submitted_by_user_id, 
                               f"Leave request submitted for {self.total_days} days")
        
        # Determine if medical certificate is required
        self._check_medical_certificate_requirement()
        
        return True
    
    def _calculate_return_date(self):
        """Calculate the return date (next working day after leave ends)"""
        from models.holiday import Holiday # Local import
        
        if self.end_date is None:
            return None
        
        return_date = self.end_date + timedelta(days=1)
        
        # Find next working day
        while return_date.weekday() >= 5 or Holiday.is_holiday(return_date):
            return_date += timedelta(days=1)
        
        return return_date
    
    def _check_medical_certificate_requirement(self):
        """Check if medical certificate is required"""
        if self.leave_type == 'sick_leave':
            # Require medical certificate for sick leave > 3 days
            self.medical_certificate_required = float(self.total_days) > 3
        elif self.leave_type == 'maternity_leave':
            self.medical_certificate_required = True
        else:
            self.medical_certificate_required = False
    
    def approve_by_supervisor(self, supervisor_user_id, comments=None):
        """Approve leave request at supervisor level"""
        self.supervisor_approval_status = 'approved'
        self.supervisor_approved_by = supervisor_user_id
        self.supervisor_approval_date = datetime.utcnow()
        self.supervisor_comments = comments
        
        # Check if HR approval is also needed
        if self._requires_hr_approval():
            self.hr_approval_status = 'pending'
            self.status = 'pending_hr' # FIX: Intermediate status
        else:
            # Auto-approve if HR approval not needed
            self.status = 'approved'
            self._process_leave_balance() # Deduct balance on final approval
        
        self._add_workflow_entry('supervisor_approved', supervisor_user_id, 
                               comments or "Approved by supervisor")
    
    def reject_by_supervisor(self, supervisor_user_id, reason):
        """Reject leave request at supervisor level"""
        self.supervisor_approval_status = 'rejected'
        self.supervisor_approved_by = supervisor_user_id
        self.supervisor_approval_date = datetime.utcnow()
        self.supervisor_comments = reason
        self.status = 'rejected'
        
        self._add_workflow_entry('supervisor_rejected', supervisor_user_id, reason)
    
    def approve_by_hr(self, hr_user_id, comments=None):
        """Approve leave request at HR level"""
        # Final approval logic
        self.hr_approval_status = 'approved'
        self.hr_approved_by = hr_user_id
        self.hr_approval_date = datetime.utcnow()
        self.hr_comments = comments
        self.status = 'approved'
        
        # Process leave balance deduction
        self._process_leave_balance()
        
        self._add_workflow_entry('hr_approved', hr_user_id, 
                               comments or "Approved by HR")
    
    def reject_by_hr(self, hr_user_id, reason):
        """Reject leave request at HR level"""
        self.hr_approval_status = 'rejected'
        self.hr_approved_by = hr_user_id
        self.hr_approval_date = datetime.utcnow()
        self.hr_comments = reason
        self.status = 'rejected'
        
        self._add_workflow_entry('hr_rejected', hr_user_id, reason)
    
    def _requires_hr_approval(self):
        """Check if HR approval is required"""
        if self.leave_type in ['maternity_leave', 'paternity_leave']:
            return True
        
        if self.leave_type == 'sick_leave' and float(self.total_days) > 7:
            return True
        
        if float(self.total_days) > 5:
            return True
        
        return False
    
    def _process_leave_balance(self):
        """Process leave balance deduction"""
        if not self.employee:
            return
            
        # FIX: Directly manipulate the Decimal column fields
        if self.leave_type == 'annual_leave' and self.employee.annual_leave_balance is not None:
            self.employee.annual_leave_balance -= self.total_days
        elif self.leave_type == 'sick_leave' and self.employee.sick_leave_balance is not None:
            self.employee.sick_leave_balance -= self.total_days
        
        db.session.commit()
    
    def extend_leave(self, additional_days, reason, approved_by_user_id):
        """Extend the leave period"""
        self.is_extended = True
        self.extension_days += additional_days
        self.extension_reason = reason
        self.extension_approved_by = approved_by_user_id
        self.extension_approval_date = datetime.utcnow()
        
        # Update end date and return date
        self.end_date += timedelta(days=additional_days)
        self.return_date = self._calculate_return_date()
        self.total_days += Decimal(str(additional_days))
        
        self._add_workflow_entry('extended', approved_by_user_id, 
                               f"Leave extended by {additional_days} days: {reason}")
    
    def return_early(self, return_date, reason):
        """Record early return from leave"""
        if return_date >= self.end_date:
            raise ValueError("Early return date must be before original end date")
        
        self.returned_early = True
        self.early_return_date = return_date
        self.actual_end_date = return_date
        self.actual_return_date = return_date
        
        # Calculate actual days taken
        start_date_effective = self.actual_start_date or self.start_date
        actual_days = (return_date - start_date_effective).days + 1
        self.actual_days_taken = Decimal(str(actual_days))
        
        # Refund unused leave balance if applicable
        unused_days = float(self.total_days) - actual_days
        if unused_days > 0 and self.leave_type == 'annual_leave':
            self.employee.annual_leave_balance += Decimal(str(unused_days))
            db.session.commit()
        
        self._add_workflow_entry('early_return', None, 
                               f"Returned early on {return_date}: {reason}")
    
    def cancel_request(self, cancelled_by_user_id, reason):
        """Cancel the leave request"""
        if self.status == 'approved':
            # Restore leave balance if already deducted
            if self.leave_type == 'annual_leave' and self.employee.annual_leave_balance is not None:
                self.employee.annual_leave_balance += self.total_days
            elif self.leave_type == 'sick_leave' and self.employee.sick_leave_balance is not None:
                self.employee.sick_leave_balance += self.total_days
        
        self.is_cancelled = True
        self.cancellation_date = datetime.utcnow()
        self.cancellation_reason = reason
        self.cancelled_by = cancelled_by_user_id
        self.status = 'cancelled'
        
        self._add_workflow_entry('cancelled', cancelled_by_user_id, reason)
    
    def _add_workflow_entry(self, action, user_id, notes):
        """Add entry to workflow history"""
        if self.workflow_history is None:
            self.workflow_history = []
        
        entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'action': action,
            'user_id': user_id,
            'notes': notes
        }
        
        self.workflow_history.append(entry)
    
    def get_status_display(self):
        """Get human-readable status"""
        status_map = {
            'pending': 'Pending Approval',
            'pending_hr': 'Pending HR Approval', # FIX: Added new intermediate status
            'approved': 'Approved',
            'rejected': 'Rejected',
            'cancelled': 'Cancelled'
        }
        return status_map.get(self.status, self.status.title())
    
    def get_leave_type_display(self):
        """Get human-readable leave type"""
        from kenyan_labor_laws import format_leave_type_display as kl_format_type
        return kl_format_type(self.leave_type)
    
    def get_duration_display(self):
        """Get formatted duration"""
        if float(self.total_days) == 1:
            return "1 day"
        elif float(self.total_days) == int(self.total_days):
            return f"{int(self.total_days)} days"
        else:
            return f"{self.total_days} days"
    
    def is_current(self):
        """Check if leave is currently active"""
        if self.status != 'approved':
            return False
        
        today = date.today()
        start = self.actual_start_date or self.start_date
        end = self.actual_end_date or self.end_date
        
        return start <= today <= end
    
    def is_upcoming(self):
        """Check if leave is upcoming"""
        return self.status == 'approved' and self.start_date > date.today()
    
    def is_overdue_return(self):
        """Check if employee is overdue to return"""
        if self.status != 'approved':
            return False
        
        expected_return = self.actual_return_date or self.return_date
        return expected_return is not None and date.today() > expected_return
    
    def to_dict(self, include_sensitive=False):
        """Convert leave request to dictionary"""
        data = {
            'id': self.id,
            'employee_id': self.employee_id,
            'request_number': self.request_number,
            'leave_type': self.leave_type,
            'leave_type_display': self.get_leave_type_display(),
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'return_date': self.return_date.isoformat() if self.return_date else None,
            'total_days': float(self.total_days),
            'duration_display': self.get_duration_display(),
            'reason': self.reason,
            'status': self.status,
            'status_display': self.get_status_display(),
            'requested_date': self.requested_date.isoformat(),
            'is_current': self.is_current(),
            'is_upcoming': self.is_upcoming(),
            'is_compliant': self.is_compliant
        }
        
        if include_sensitive:
            data.update({
                'supervisor_approval_status': self.supervisor_approval_status,
                'hr_approval_status': self.hr_approval_status,
                'supervisor_comments': self.supervisor_comments,
                'hr_comments': self.hr_comments,
                'leave_balance_before': float(self.leave_balance_before) if self.leave_balance_before else None,
                'leave_balance_after': float(self.leave_balance_after) if self.leave_balance_after else None,
                'medical_certificate_required': self.medical_certificate_required,
                'medical_certificate_provided': self.medical_certificate_provided,
                'compliance_notes': self.compliance_notes,
                'workflow_history': self.workflow_history
            })
        
        return data
    
    @classmethod
    def get_pending_requests(cls, location=None, department=None):
        """Get pending leave requests"""
        from models.employee import Employee # Local import
        
        query = cls.query.join(Employee).filter(cls.status.in_(['pending', 'pending_hr'])) # FIX: Include pending_hr
        
        if location:
            query = query.filter(Employee.location == location)
        
        if department:
            query = query.filter(Employee.department == department)
        
        return query.order_by(cls.requested_date).all()
    
    @classmethod
    def get_current_leaves(cls, location=None):
        """Get currently active leaves"""
        from models.employee import Employee # Local import
        
        today = date.today()
        query = cls.query.join(Employee).filter(
            cls.status == 'approved',
            cls.start_date <= today,
            cls.end_date >= today
        )
        
        if location:
            query = query.filter(Employee.location == location)
        
        return query.all()
    
    @classmethod
    def get_upcoming_leaves(cls, days_ahead=30, location=None):
        """Get upcoming approved leaves"""
        from models.employee import Employee # Local import
        
        start_date = date.today() + timedelta(days=1)
        end_date = date.today() + timedelta(days=days_ahead)
        
        query = cls.query.join(Employee).filter(
            cls.status == 'approved',
            cls.start_date.between(start_date, end_date)
        )
        
        if location:
            query = query.filter(Employee.location == location)
        
        return query.order_by(cls.start_date).all()
    
    @classmethod
    def create_leave_request(cls, employee_id, leave_type, start_date, end_date, 
                           reason, **kwargs):
        """Create new leave request"""
        # Calculate total days
        total_days = (end_date - start_date).days + 1
        
        request = cls(
            employee_id=employee_id,
            leave_type=leave_type,
            start_date=start_date,
            end_date=end_date,
            total_days=Decimal(str(total_days)),
            reason=reason,
            **kwargs
        )
        
        return request
    
    def __repr__(self):
        # FIX: Ensure safe access to employee.get_full_name()
        employee_name = self.employee.get_full_name() if self.employee and hasattr(self.employee, 'get_full_name') else str(self.employee_id)
        return f'<LeaveRequest {self.request_number}: {employee_name} - {self.leave_type}>'