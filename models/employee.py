"""
Sakina Gas Company - Employee Model
Built from scratch with comprehensive employee management and HR features
Version 3.0 - Enterprise grade with full complexity
"""

from database import db
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON, Numeric, Date, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, date, timedelta
from decimal import Decimal
import json

class Employee(db.Model):
    """
    Comprehensive Employee model with full HR management capabilities
    """
    __tablename__ = 'employees'
    
    # Primary identification
    id = Column(Integer, primary_key=True)
    employee_id = Column(String(20), unique=True, nullable=False, index=True)
    
    # Personal Information
    first_name = Column(String(50), nullable=False)
    middle_name = Column(String(50), nullable=True)
    last_name = Column(String(50), nullable=False)
    date_of_birth = Column(Date, nullable=True)
    gender = Column(String(10), nullable=True)  # male, female, other
    marital_status = Column(String(20), nullable=True)  # single, married, divorced, widowed
    nationality = Column(String(50), nullable=False, default='Kenyan')
    
    # Contact Information
    email = Column(String(120), nullable=True, index=True)
    phone = Column(String(20), nullable=True)
    alternative_phone = Column(String(20), nullable=True)
    address = Column(Text, nullable=True)
    postal_address = Column(String(200), nullable=True)
    city = Column(String(50), nullable=True)
    county = Column(String(50), nullable=True)
    postal_code = Column(String(10), nullable=True)
    
    # Government Identification
    national_id = Column(String(20), unique=True, nullable=True, index=True)
    passport_number = Column(String(20), unique=True, nullable=True)
    driving_license = Column(String(20), nullable=True)
    
    # Statutory Numbers (Kenya-specific)
    kra_pin = Column(String(15), nullable=True)  # Kenya Revenue Authority PIN
    nssf_number = Column(String(20), nullable=True)  # National Social Security Fund
    nhif_number = Column(String(20), nullable=True)  # National Hospital Insurance Fund
    
    # Employment Details
    location = Column(String(50), nullable=False, index=True)
    department = Column(String(50), nullable=False, index=True)
    position = Column(String(100), nullable=False)
    job_title = Column(String(100), nullable=True)  # Alternative job title
    job_description = Column(Text, nullable=True)
    shift = Column(String(20), nullable=False, default='day')  # day, night
    employment_type = Column(String(30), nullable=False, default='permanent')  # permanent, contract, casual, intern
    employment_status = Column(String(30), nullable=False, default='active')  # active, inactive, suspended, terminated
    
    # Employment Dates
    hire_date = Column(Date, nullable=False)
    probation_start_date = Column(Date, nullable=True)
    probation_end_date = Column(Date, nullable=True)
    confirmation_date = Column(Date, nullable=True)
    termination_date = Column(Date, nullable=True)
    last_promotion_date = Column(Date, nullable=True)
    
    # Reporting Structure
    reports_to = Column(Integer, ForeignKey('employees.id'), nullable=True)
    supervisor_id = Column(String(20), nullable=True)  # Employee ID of supervisor
    
    # Salary and Compensation
    basic_salary = Column(Numeric(12, 2), nullable=False, default=0.00)
    currency = Column(String(5), nullable=False, default='KES')
    salary_grade = Column(String(10), nullable=True)
    pay_frequency = Column(String(20), nullable=False, default='monthly')  # monthly, weekly, daily
    
    # Allowances (stored as JSON)
    allowances = Column(JSON, nullable=True)  # transport, housing, meal, medical, etc.
    
    # Bank Details
    bank_name = Column(String(100), nullable=True)
    bank_branch = Column(String(100), nullable=True)
    account_number = Column(String(30), nullable=True)
    account_name = Column(String(150), nullable=True)
    
    # Emergency Contacts (stored as JSON)
    emergency_contacts = Column(JSON, nullable=True)
    
    # Skills and Qualifications
    education_level = Column(String(50), nullable=True)
    qualifications = Column(JSON, nullable=True)  # Array of qualifications
    skills = Column(JSON, nullable=True)  # Array of skills
    certifications = Column(JSON, nullable=True)  # Array of certifications
    languages = Column(JSON, nullable=True)  # Array of languages
    
    # Work Information
    work_schedule = Column(JSON, nullable=True)  # Custom work schedule if different from standard
    overtime_eligible = Column(Boolean, nullable=False, default=True)
    remote_work_eligible = Column(Boolean, nullable=False, default=False)
    
    # Performance and Development
    performance_rating = Column(String(20), nullable=True)  # excellent, good, satisfactory, needs_improvement
    last_performance_review = Column(Date, nullable=True)
    next_performance_review = Column(Date, nullable=True)
    development_plan = Column(Text, nullable=True)
    career_goals = Column(Text, nullable=True)
    
    # Health and Safety
    medical_conditions = Column(Text, nullable=True)
    allergies = Column(Text, nullable=True)
    blood_group = Column(String(5), nullable=True)
    disability_status = Column(String(20), nullable=True)
    
    # System and Administrative
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    created_date = Column(DateTime, nullable=False, default=func.current_timestamp())
    created_by = Column(Integer, nullable=True)
    last_updated = Column(DateTime, nullable=False, default=func.current_timestamp(), onupdate=func.current_timestamp())
    updated_by = Column(Integer, nullable=True)
    
    # Additional Information
    notes = Column(Text, nullable=True)
    internal_notes = Column(Text, nullable=True)  # HR/Management only
    photo_url = Column(String(255), nullable=True)
    
    # Contract and Legal
    contract_type = Column(String(50), nullable=True)
    contract_start_date = Column(Date, nullable=True)
    contract_end_date = Column(Date, nullable=True)
    notice_period_days = Column(Integer, nullable=False, default=30)
    
    # Leave Balances (calculated fields)
    annual_leave_balance = Column(Numeric(5, 2), nullable=False, default=21.0)
    sick_leave_balance = Column(Numeric(5, 2), nullable=False, default=30.0)
    personal_leave_balance = Column(Numeric(5, 2), nullable=False, default=0.0)
    
    # Metadata
    employee_metadata = Column(JSON, nullable=True)  # Additional flexible data storage (FIX: Renamed from 'metadata')
    
    # Relationships
    # FIX: Use string literal for self-referential relationship
    supervisor = relationship('Employee', remote_side=[id], backref='direct_reports') 
    attendance_records = relationship('AttendanceRecord', backref='employee', lazy='dynamic', cascade='all, delete-orphan') # FIX: Renamed backref to 'employee' for consistency
    leave_requests = relationship('LeaveRequest', foreign_keys='LeaveRequest.employee_id', backref='employee', lazy='dynamic', cascade='all, delete-orphan') # FIX: Renamed backref to 'employee'
    performance_reviews = relationship('PerformanceReview', backref='employee', lazy='dynamic', cascade='all, delete-orphan') # FIX: Renamed backref to 'employee'
    disciplinary_actions = relationship('DisciplinaryAction', backref='employee', lazy='dynamic', cascade='all, delete-orphan') # FIX: Renamed backref to 'employee'
    
    def __init__(self, **kwargs):
        """Initialize employee with default values"""
        super(Employee, self).__init__()
        
        # Set default allowances structure
        self.allowances = {
            'transport': 0.0,
            'housing': 0.0,
            'meal': 0.0,
            'medical': 0.0,
            'communication': 0.0,
            'other': 0.0
        }
        
        # Set default emergency contacts structure
        self.emergency_contacts = {
            'primary': {
                'name': '',
                'relationship': '',
                'phone': '',
                'email': '',
                'address': ''
            },
            'secondary': {
                'name': '',
                'relationship': '',
                'phone': '',
                'email': '',
                'address': ''
            }
        }
        
        # Set default skills and qualifications
        self.skills = []
        self.qualifications = []
        self.certifications = []
        self.languages = ['English', 'Swahili']
        
        # Set creation timestamp
        self.created_date = datetime.utcnow()
        
        # Apply any provided kwargs
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        
        # Calculate probation end date if hire date is provided
        if self.hire_date and not self.probation_end_date:
            self.probation_start_date = self.hire_date
            self.probation_end_date = self.hire_date + timedelta(days=90)  # 3 months probation
    
    def get_full_name(self):
        """Get employee's full name"""
        if self.middle_name:
            return f"{self.first_name} {self.middle_name} {self.last_name}"
        return f"{self.first_name} {self.last_name}"
    
    def get_display_name(self):
        """Get display name for UI"""
        return f"{self.get_full_name()} ({self.employee_id})"
    
    def get_initials(self):
        """Get employee's initials"""
        initials = self.first_name[0].upper() if self.first_name else ''
        if self.middle_name:
            initials += self.middle_name[0].upper()
        if self.last_name:
            initials += self.last_name[0].upper()
        return initials
    
    def calculate_age(self):
        """Calculate employee's age"""
        if not self.date_of_birth:
            return None
        
        today = date.today()
        age = today.year - self.date_of_birth.year
        
        # Adjust if birthday hasn't occurred this year
        if today.month < self.date_of_birth.month or \
           (today.month == self.date_of_birth.month and today.day < self.date_of_birth.day):
            age -= 1
        
        return age
    
    def get_age(self):
        """Wrapper for calculate_age for simple template access"""
        return self.calculate_age()

    def calculate_years_of_service(self):
        """Calculate years of service"""
        if not self.hire_date:
            return 0
        
        end_date = self.termination_date if self.termination_date else date.today()
        
        years = end_date.year - self.hire_date.year
        if end_date.month < self.hire_date.month or \
           (end_date.month == self.hire_date.month and end_date.day < self.hire_date.day):
            years -= 1
        
        return years
    
    def get_years_of_service(self):
        """Wrapper for calculate_years_of_service for simple template access"""
        return self.calculate_years_of_service()

    def calculate_months_of_service(self):
        """Calculate total months of service"""
        if not self.hire_date:
            return 0
        
        end_date = self.termination_date if self.termination_date else date.today()
        
        total_months = (end_date.year - self.hire_date.year) * 12
        total_months += end_date.month - self.hire_date.month
        
        # Adjust for day of month
        if end_date.day < self.hire_date.day:
            total_months -= 1
        
        return total_months
    
    def is_on_probation(self):
        """Check if employee is currently on probation"""
        if not self.probation_end_date:
            return False
        
        return date.today() <= self.probation_end_date
    
    def days_until_probation_end(self):
        """Calculate days until probation ends"""
        if not self.probation_end_date or not self.is_on_probation():
            return 0
        
        return (self.probation_end_date - date.today()).days
    
    def probation_completion_percentage(self):
        """Calculate probation completion percentage"""
        if not self.probation_start_date or not self.probation_end_date:
            return 0

        total_days = (self.probation_end_date - self.probation_start_date).days
        days_passed = (date.today() - self.probation_start_date).days

        if days_passed <= 0:
            return 0
        if days_passed >= total_days:
            return 100
        
        return round((days_passed / total_days) * 100)
    
    def is_contract_expiring_soon(self, days_ahead=30):
        """Check if contract is expiring soon"""
        if not self.contract_end_date:
            return False
        
        warning_date = date.today() + timedelta(days=days_ahead)
        return self.contract_end_date <= warning_date
    
    def get_total_compensation(self):
        """Calculate total monthly compensation including allowances"""
        # Ensure basic_salary is treated as Decimal for precision
        total = Decimal(str(self.basic_salary)) if self.basic_salary else Decimal(0.0)
        
        if self.allowances:
            for allowance_type, amount in self.allowances.items():
                try:
                    # Convert amount to Decimal before adding
                    if amount is not None:
                         total += Decimal(str(amount))
                except Exception:
                     # Log or ignore invalid allowance amount
                     pass
        
        # Return as float for typical presentation, or keep as Decimal for internal use
        return float(total)
    
    def get_position_display(self):
        """Get formatted position with department"""
        return f"{self.position} - {self.department.replace('_', ' ').title()}"
    
    def get_employment_status_display(self):
        """Get human-readable employment status"""
        status_map = {
            'active': 'Active',
            'inactive': 'Inactive', 
            'suspended': 'Suspended',
            'terminated': 'Terminated',
            'resigned': 'Resigned'
        }
        return status_map.get(self.employment_status, self.employment_status.title())

    def get_employment_type_display(self):
        """Get human-readable employment type"""
        type_map = {
            'permanent': 'Permanent',
            'contract': 'Contract', 
            'casual': 'Casual',
            'intern': 'Intern'
        }
        return type_map.get(self.employment_type, self.employment_type.title())

    def get_location_display(self):
        """Get formatted location name"""
        from flask import current_app # Local import
        locations_config = current_app.config.get('COMPANY_LOCATIONS', {})
        location_data = locations_config.get(self.location, {})
        return location_data.get('name', self.location.replace('_', ' ').title())
    
    def get_department_display(self):
        """Get formatted department name"""
        from flask import current_app # Local import
        departments_config = current_app.config.get('DEPARTMENTS', {})
        dept_data = departments_config.get(self.department, {})
        return dept_data.get('name', self.department.replace('_', ' ').title())
    
    def update_allowances(self, allowances_dict):
        """Update employee allowances"""
        if self.allowances is None:
            self.allowances = {}
        
        # Convert all incoming float/int values to Decimal strings for storage (JSON doesn't support Decimal)
        # However, for consistency with how it's used internally (as Decimal in get_total_compensation),
        # we ensure conversion happens during use. Store raw JSON data.
        
        self.allowances.update(allowances_dict)
        self.last_updated = datetime.utcnow()
    
    def add_skill(self, skill_name, level=None, certified=False):
        """Add skill to employee"""
        if self.skills is None:
            self.skills = []
        
        skill = {
            'name': skill_name,
            'level': level,
            'certified': certified,
            'added_date': date.today().isoformat()
        }
        
        # Check if skill already exists
        for i, existing_skill in enumerate(self.skills):
            if existing_skill.get('name', '').lower() == skill_name.lower():
                self.skills[i] = skill
                return
        
        self.skills.append(skill)
        self.last_updated = datetime.utcnow()
    
    def remove_skill(self, skill_name):
        """Remove skill from employee"""
        if not self.skills:
            return
        
        self.skills = [skill for skill in self.skills 
                      if skill.get('name', '').lower() != skill_name.lower()]
        self.last_updated = datetime.utcnow()
    
    def add_qualification(self, qualification_data):
        """Add qualification to employee"""
        if self.qualifications is None:
            self.qualifications = []
        
        # Ensure required fields
        qualification = {
            'institution': qualification_data.get('institution', ''),
            'qualification': qualification_data.get('qualification', ''),
            'field_of_study': qualification_data.get('field_of_study', ''),
            'year_completed': qualification_data.get('year_completed', ''),
            'grade': qualification_data.get('grade', ''),
            'verified': qualification_data.get('verified', False),
            'added_date': date.today().isoformat()
        }
        
        self.qualifications.append(qualification)
        self.last_updated = datetime.utcnow()
    
    def add_certification(self, certification_data):
        """Add certification to employee"""
        if self.certifications is None:
            self.certifications = []
        
        certification = {
            'name': certification_data.get('name', ''),
            'issuing_authority': certification_data.get('issuing_authority', ''),
            'issue_date': certification_data.get('issue_date', ''),
            'expiry_date': certification_data.get('expiry_date', ''),
            'certificate_number': certification_data.get('certificate_number', ''),
            'verified': certification_data.get('verified', False),
            'added_date': date.today().isoformat()
        }
        
        self.certifications.append(certification)
        self.last_updated = datetime.utcnow()
    
    def get_expiring_certifications(self, days_ahead=90):
        """Get certifications expiring within specified days"""
        if not self.certifications:
            return []
        
        expiring = []
        cutoff_date = date.today() + timedelta(days=days_ahead)
        
        for cert in self.certifications:
            expiry_date_str = cert.get('expiry_date')
            if expiry_date_str:
                try:
                    expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d').date()
                    if expiry_date <= cutoff_date:
                        expiring.append(cert)
                except ValueError:
                    pass  # Invalid date format
        
        return expiring
    
    def calculate_leave_balance(self, leave_type, year=None):
        """Calculate leave balance for specific type (Simplified for model access)"""
        from models.leave import LeaveRequest
        from flask import current_app # Local import
        from sqlalchemy import func
        
        if year is None:
            year = date.today().year
        
        # Get Kenyan law entitlements
        labor_laws = current_app.config.get('KENYAN_LABOR_LAWS', {})
        leave_entitlements = labor_laws.get('leave_entitlements', {})
        
        # Calculate entitlement
        entitlement = Decimal(0.0)
        leave_config = leave_entitlements.get(leave_type, {})

        if leave_type == 'annual_leave':
            years_of_service = self.calculate_years_of_service()
            if years_of_service >= 1:
                entitlement = Decimal(leave_config.get('days_per_year', 21))
            else:
                # Prorata accrual if under 1 year
                accrual_rate = Decimal(leave_config.get('days_per_year', 21)) / Decimal(12)
                entitlement = Decimal(self.calculate_months_of_service()) * accrual_rate
        elif leave_type == 'sick_leave':
            entitlement = Decimal(leave_config.get('max_per_year', 30))
        else:
            entitlement = Decimal(leave_config.get('days', 0))

        # Calculate used leave for the current year
        used_leave_sum = db.session.query(func.sum(LeaveRequest.total_days)).filter(
            LeaveRequest.employee_id == self.id,
            LeaveRequest.leave_type == leave_type,
            LeaveRequest.status == 'approved',
            LeaveRequest.start_date.between(date(year, 1, 1), date(year, 12, 31))
        ).scalar() or Decimal(0.0)
        used_leave = Decimal(str(used_leave_sum)) if used_leave_sum else Decimal(0.0)
        
        # Calculate pending leave for the current year
        pending_leave_sum = db.session.query(func.sum(LeaveRequest.total_days)).filter(
            LeaveRequest.employee_id == self.id,
            LeaveRequest.leave_type == leave_type,
            LeaveRequest.status.in_(['pending', 'pending_hr']), # FIX: Include pending_hr
            LeaveRequest.start_date.between(date(year, 1, 1), date(year, 12, 31))
        ).scalar() or Decimal(0.0)
        pending_leave = Decimal(str(pending_leave_sum)) if pending_leave_sum else Decimal(0.0)

        available = max(Decimal(0.0), entitlement - used_leave - pending_leave)
        
        # Return as float/Decimal based on context (keeping Decimal internally for precision)
        return float(round(available, 2))
    
    def get_supervisor(self):
        """Get employee's supervisor"""
        # NOTE: Employee class is defined in this file, so it's safe to use Employee.query
        if self.supervisor_id:
            # FIX: Use employee_id for lookup in case 'reports_to' isn't set up yet
            return Employee.query.filter_by(employee_id=self.supervisor_id).first()
        # FIX: Also check the self-referential relationship 'reports_to' if supervisor_id lookup fails
        if self.reports_to:
            return Employee.query.get(self.reports_to)
        return self.supervisor
    
    def get_direct_reports_count(self):
        """Get count of direct reports"""
        return Employee.query.filter_by(supervisor_id=self.employee_id, is_active=True).count()
    
    def get_team_members(self):
        """Get all team members (direct reports)"""
        return Employee.query.filter_by(supervisor_id=self.employee_id, is_active=True).all()
    
    def get_attendance_rate(self, days=30):
        """Calculate attendance rate for last N days"""
        from models.attendance import AttendanceRecord # Local import to prevent circularity
        
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        total_days_in_period = (end_date - start_date).days + 1
        
        # Only count days where the employee was expected to work (simplified: assumes expected to work all days)
        total_records = AttendanceRecord.query.filter(
            AttendanceRecord.employee_id == self.id,
            AttendanceRecord.date.between(start_date, end_date)
        ).count()
        
        if total_days_in_period == 0: # Avoid division by zero
            return 0.0
        
        present_records = AttendanceRecord.query.filter(
            AttendanceRecord.employee_id == self.id,
            AttendanceRecord.date.between(start_date, end_date),
            AttendanceRecord.status.in_(['present', 'late'])
        ).count()
        
        # Attendance rate is present/attended days over total *expected* days (simplified to total days in period)
        return round((present_records / total_days_in_period) * 100, 2)
    
    def get_punctuality_rate(self, days=30):
        """Calculate punctuality rate (on-time arrivals)"""
        from models.attendance import AttendanceRecord # Local import to prevent circularity
        
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        # Count all present/late days
        attended_records = AttendanceRecord.query.filter(
            AttendanceRecord.employee_id == self.id,
            AttendanceRecord.date.between(start_date, end_date),
            AttendanceRecord.status.in_(['present', 'late'])
        ).count()
        
        if attended_records == 0:
            return 0.0
        
        # Count only on-time days
        on_time_records = AttendanceRecord.query.filter(
            AttendanceRecord.employee_id == self.id,
            AttendanceRecord.date.between(start_date, end_date),
            AttendanceRecord.status == 'present'
        ).count()
        
        return round((on_time_records / attended_records) * 100, 2)
    
    def can_request_leave(self, leave_type, days_requested):
        """Check if employee can request specific leave"""
        from models.leave import LeaveRequest # Local import

        temp_request = LeaveRequest(
            employee_id=self.id,
            leave_type=leave_type,
            start_date=date.today() + timedelta(days=7), # Mock start date for validation
            end_date=date.today() + timedelta(days=7 + days_requested),
            total_days=Decimal(str(days_requested))
        )
        # Manually set employee relationship for validation dependency
        temp_request.employee = self

        is_valid, message = temp_request.validate_against_kenyan_law()
        
        return is_valid, message
    
    def deactivate(self, reason=None, termination_date=None):
        """Deactivate employee"""
        self.is_active = False
        self.employment_status = 'terminated'
        self.termination_date = termination_date or date.today()
        
        if reason:
            if not self.internal_notes:
                self.internal_notes = ""
            self.internal_notes += f"\n\nTerminated on {self.termination_date}: {reason}"
        
        self.last_updated = datetime.utcnow()
    
    def reactivate(self):
        """Reactivate employee"""
        self.is_active = True
        self.employment_status = 'active'
        self.termination_date = None
        self.last_updated = datetime.utcnow()
    
    def promote(self, new_position, new_department=None, new_salary=None, effective_date=None):
        """Promote employee to new position"""
        old_position = self.position
        old_department = self.department
        old_salary = self.basic_salary
        
        self.position = new_position
        if new_department:
            self.department = new_department
        if new_salary:
            self.basic_salary = new_salary
        
        self.last_promotion_date = effective_date or date.today()
        self.last_updated = datetime.utcnow()
        
        # Add to notes
        promotion_note = f"Promoted from {old_position} to {new_position}"
        if new_department and new_department != old_department:
            promotion_note += f" (Department: {old_department} → {new_department})"
        if new_salary and new_salary != old_salary:
            promotion_note += f" (Salary: {old_salary} → {new_salary})"
        
        if not self.notes:
            self.notes = ""
        self.notes += f"\n\n{self.last_promotion_date}: {promotion_note}"
    
    def to_dict(self, include_sensitive=False):
        """Convert employee to dictionary"""
        data = {
            'id': self.id,
            'employee_id': self.employee_id,
            'first_name': self.first_name,
            'middle_name': self.middle_name,
            'last_name': self.last_name,
            'full_name': self.get_full_name(),
            'email': self.email,
            'phone': self.phone,
            'position': self.position,
            'department': self.department,
            'department_display': self.get_department_display(),
            'location': self.location,
            'location_display': self.get_location_display(),
            'employment_status': self.employment_status,
            'employment_status_display': self.get_employment_status_display(),
            'hire_date': self.hire_date.isoformat() if self.hire_date else None,
            'is_active': self.is_active,
            'is_on_probation': self.is_on_probation(),
            'years_of_service': self.calculate_years_of_service(),
            'age': self.calculate_age(),
            'employment_type_display': self.get_employment_type_display() # FIX: Added missing display type
        }
        
        if include_sensitive:
            data.update({
                'national_id': self.national_id,
                'basic_salary': float(self.basic_salary) if self.basic_salary else 0,
                'total_compensation': self.get_total_compensation(),
                'allowances': self.allowances,
                'bank_details': {
                    'bank_name': self.bank_name,
                    'account_number': self.account_number,
                    'account_name': self.account_name
                },
                'emergency_contacts': self.emergency_contacts,
                'attendance_rate': self.get_attendance_rate(),
                'punctuality_rate': self.get_punctuality_rate()
            })
        
        return data
    
    @classmethod
    def generate_employee_id(cls):
        """Generate next available employee ID"""
        # Get the last employee ID
        last_employee = cls.query.filter(
            cls.employee_id.like('SGC%')
        ).order_by(db.desc(cls.employee_id)).first() # FIX: Use db.desc for Flask-SQLAlchemy 2.0+
        
        if not last_employee:
            return 'SGC001'
        
        # Extract number and increment
        try:
            last_number = int(last_employee.employee_id[3:])
            new_number = last_number + 1
            return f'SGC{new_number:03d}'
        except (ValueError, IndexError):
            # Fallback if format is unexpected
            total_employees = cls.query.count()
            return f'SGC{total_employees + 1:03d}'
    
    @classmethod
    def create_employee(cls, first_name, last_name, position, department, location, 
                       hire_date, basic_salary, **kwargs):
        """Class method to create new employee"""
        # Generate employee ID
        employee_id = kwargs.get('employee_id') or cls.generate_employee_id()
        
        # Validate required fields
        if not all([first_name, last_name, position, department, location, hire_date]):
            raise ValueError("Missing required fields")
        
        # Check if employee ID already exists
        if cls.query.filter_by(employee_id=employee_id).first():
            raise ValueError("Employee ID already exists")
        
        # Create employee
        employee = cls(
            employee_id=employee_id,
            first_name=first_name,
            last_name=last_name,
            position=position,
            department=department,
            location=location,
            hire_date=hire_date,
            basic_salary=basic_salary,
            **kwargs
        )
        
        return employee
    
    @classmethod
    def search_employees(cls, query=None, location=None, department=None, 
                        employment_status=None, is_active=True):
        """Search employees with filters"""
        search = cls.query
        
        if query:
            search_term = f"%{query}%"
            search = search.filter(
                db.or_(
                    cls.employee_id.like(search_term),
                    cls.first_name.like(search_term),
                    cls.last_name.like(search_term),
                    cls.email.like(search_term),
                    cls.position.like(search_term)
                )
            )
        
        if location:
            search = search.filter_by(location=location)
        
        if department:
            search = search.filter_by(department=department)
        
        if employment_status:
            search = search.filter_by(employment_status=employment_status)
        
        if is_active is not None:
            search = search.filter_by(is_active=is_active)
        
        return search.order_by(cls.first_name, cls.last_name).all()
    
    @classmethod
    def get_by_location(cls, location, is_active=True):
        """Get employees by location"""
        query = cls.query.filter_by(location=location)
        if is_active is not None:
            query = query.filter_by(is_active=is_active)
        return query.order_by(cls.first_name, cls.last_name).all()
    
    @classmethod
    def get_by_department(cls, department, is_active=True):
        """Get employees by department"""
        query = cls.query.filter_by(department=department)
        if is_active is not None:
            query = query.filter_by(is_active=is_active)
        return query.order_by(cls.first_name, cls.last_name).all()
    
    @classmethod
    def get_probationary_employees(cls):
        """Get employees currently on probation"""
        today = date.today()
        return cls.query.filter(
            cls.is_active == True,
            cls.probation_end_date >= today,
            cls.probation_start_date <= today
        ).all()
    
    @classmethod
    def get_employees_by_supervisor(cls, supervisor_employee_id):
        """Get employees under a specific supervisor"""
        return cls.query.filter_by(
            supervisor_id=supervisor_employee_id,
            is_active=True
        ).order_by(cls.first_name, cls.last_name).all()
    
    def __repr__(self):
        return f'<Employee {self.employee_id}: {self.get_full_name()}>'