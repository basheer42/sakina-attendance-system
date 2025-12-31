"""
Kenyan Labor Laws Compliance Module
Employment Act 2007 - Leave Entitlements and Validations
Complete implementation with all required functions
"""

from decimal import Decimal
from datetime import date, timedelta

# Kenyan Employment Act 2007 - Leave Entitlements
KENYAN_LEAVE_LAWS = {
    'annual_leave': {
        'max_days': 21,
        'name': 'Annual Leave',
        'description': 'Minimum 21 working days per year',
        'notice_required_days': 14,
        'can_accumulate': True,
        'max_accumulation_days': 42,  # 2 years worth
        'legal_reference': 'Employment Act 2007, Section 28'
    },
    'sick_leave': {
        'max_days_without_certificate': 7,
        'max_days_with_certificate': 30,
        'name': 'Sick Leave', 
        'description': 'Up to 7 days without certificate, 30 days with medical certificate',
        'notice_required_days': 0,
        'requires_medical_certificate_after': 7,
        'legal_reference': 'Employment Act 2007, Section 29'
    },
    'maternity_leave': {
        'max_days': 90,  # 3 months
        'name': 'Maternity Leave',
        'description': '3 months maternity leave (can be split before/after birth)',
        'notice_required_days': 30,
        'can_split': True,
        'max_prenatal_days': 14,
        'legal_reference': 'Employment Act 2007, Section 30'
    },
    'paternity_leave': {
        'max_days': 14,
        'name': 'Paternity Leave', 
        'description': 'Maximum 14 consecutive days',
        'notice_required_days': 7,
        'must_be_consecutive': True,
        'legal_reference': 'Employment Act 2007, Section 30A'
    },
    'compassionate_leave': {
        'max_days': 7,
        'name': 'Compassionate Leave',
        'description': 'Up to 7 days for death of close relative',
        'notice_required_days': 0,
        'immediate_family_only': True,
        'legal_reference': 'Employment Act 2007, Section 31'
    },
    'study_leave': {
        'max_days': 30,
        'name': 'Study Leave',
        'description': 'For approved educational courses',
        'notice_required_days': 30,
        'requires_approval': True,
        'may_be_unpaid': True,
        'legal_reference': 'Employment Act 2007, Section 32'
    }
}

# Working hours constants
WORKING_HOURS = {
    'normal_hours_per_day': 8,
    'normal_hours_per_week': 45,
    'maximum_hours_per_week': 60,
    'overtime_threshold_daily': 8,
    'overtime_threshold_weekly': 45,
    'overtime_rate_normal': Decimal('1.5'),
    'overtime_rate_holiday': Decimal('2.0'),
    'overtime_rate_night': Decimal('1.25'),
    'night_shift_start': '18:00',
    'night_shift_end': '06:00',
    'legal_reference': 'Employment Act 2007, Section 27'
}


def calculate_working_days(start_date, end_date, holiday_checker=None):
    """
    Calculate the number of working days between two dates.
    Excludes weekends (Saturday and Sunday) and optionally holidays.
    
    Args:
        start_date: The start date (date object)
        end_date: The end date (date object)
        holiday_checker: Optional callable that takes a date and returns True if it's a holiday
        
    Returns:
        Integer count of working days
    """
    if start_date is None or end_date is None:
        return 0
    
    if start_date > end_date:
        return 0
    
    working_days = 0
    current_date = start_date
    
    while current_date <= end_date:
        # Check if it's a weekday (Monday = 0, Sunday = 6)
        if current_date.weekday() < 5:  # Not Saturday (5) or Sunday (6)
            # Check if it's not a holiday
            is_holiday = False
            if holiday_checker is not None:
                try:
                    is_holiday = holiday_checker(current_date)
                except Exception:
                    is_holiday = False
            
            if not is_holiday:
                working_days += 1
        
        current_date += timedelta(days=1)
    
    return working_days


def calculate_calendar_days(start_date, end_date):
    """
    Calculate the number of calendar days between two dates (inclusive).
    
    Args:
        start_date: The start date (date object)
        end_date: The end date (date object)
        
    Returns:
        Integer count of calendar days
    """
    if start_date is None or end_date is None:
        return 0
    
    if start_date > end_date:
        return 0
    
    return (end_date - start_date).days + 1


def get_leave_entitlement(leave_type):
    """
    Get the leave entitlement details for a specific leave type.
    
    Args:
        leave_type: String identifier for the leave type
        
    Returns:
        Dictionary with leave entitlement details or None if not found
    """
    return KENYAN_LEAVE_LAWS.get(leave_type)


def get_max_leave_days(leave_type):
    """
    Get the maximum allowed days for a specific leave type.
    
    Args:
        leave_type: String identifier for the leave type
        
    Returns:
        Integer maximum days or 0 if leave type not found
    """
    leave_info = KENYAN_LEAVE_LAWS.get(leave_type, {})
    
    # Handle sick leave specially (has two limits)
    if leave_type == 'sick_leave':
        return leave_info.get('max_days_with_certificate', 30)
    
    return leave_info.get('max_days', 0)


def get_notice_required_days(leave_type):
    """
    Get the notice period required for a specific leave type.
    
    Args:
        leave_type: String identifier for the leave type
        
    Returns:
        Integer notice days required or 0 if not specified
    """
    leave_info = KENYAN_LEAVE_LAWS.get(leave_type, {})
    return leave_info.get('notice_required_days', 0)


def validate_leave_notice(leave_type, start_date, request_date=None):
    """
    Validate if sufficient notice has been given for a leave request.
    
    Args:
        leave_type: String identifier for the leave type
        start_date: The requested leave start date
        request_date: The date the request was made (defaults to today)
        
    Returns:
        Tuple of (is_valid, message)
    """
    if request_date is None:
        request_date = date.today()
    
    required_notice = get_notice_required_days(leave_type)
    
    if required_notice == 0:
        return True, "No advance notice required for this leave type."
    
    actual_notice = (start_date - request_date).days
    
    if actual_notice < required_notice:
        return False, f"Insufficient notice period. {leave_type.replace('_', ' ').title()} requires {required_notice} days notice. Only {actual_notice} days provided."
    
    return True, f"Notice period requirement met ({actual_notice} days provided, {required_notice} required)."


class KenyanLaborLaws:
    """Kenyan labor law compliance validator"""
    
    @staticmethod
    def validate_annual_leave(employee, days_requested, start_date):
        """Validate annual leave request"""
        warnings = []
        
        # Check maximum days
        if days_requested > KENYAN_LEAVE_LAWS['annual_leave']['max_days']:
            warnings.append({
                'level': 'error',
                'message': f"Annual leave cannot exceed {KENYAN_LEAVE_LAWS['annual_leave']['max_days']} days per year",
                'law_reference': KENYAN_LEAVE_LAWS['annual_leave']['legal_reference']
            })
        
        # Check notice period
        notice_days = (start_date - date.today()).days
        required_notice = KENYAN_LEAVE_LAWS['annual_leave']['notice_required_days']
        
        if notice_days < required_notice:
            warnings.append({
                'level': 'warning',
                'message': f"Annual leave requires {required_notice} days notice. Only {notice_days} days provided.",
                'law_reference': KENYAN_LEAVE_LAWS['annual_leave']['legal_reference']
            })
        
        return warnings
    
    @staticmethod
    def validate_sick_leave(employee, days_requested, has_medical_certificate=False):
        """Validate sick leave request"""
        warnings = []
        
        max_without_cert = KENYAN_LEAVE_LAWS['sick_leave']['max_days_without_certificate']
        max_with_cert = KENYAN_LEAVE_LAWS['sick_leave']['max_days_with_certificate']
        
        if days_requested > max_without_cert and not has_medical_certificate:
            warnings.append({
                'level': 'error',
                'message': f"Sick leave over {max_without_cert} days requires a medical certificate",
                'law_reference': KENYAN_LEAVE_LAWS['sick_leave']['legal_reference']
            })
        
        if days_requested > max_with_cert:
            warnings.append({
                'level': 'error',
                'message': f"Sick leave cannot exceed {max_with_cert} days per year",
                'law_reference': KENYAN_LEAVE_LAWS['sick_leave']['legal_reference']
            })
        
        return warnings
    
    @staticmethod
    def validate_maternity_leave(employee, days_requested, start_date):
        """Validate maternity leave request"""
        warnings = []
        
        max_days = KENYAN_LEAVE_LAWS['maternity_leave']['max_days']
        required_notice = KENYAN_LEAVE_LAWS['maternity_leave']['notice_required_days']
        
        if days_requested > max_days:
            warnings.append({
                'level': 'error',
                'message': f"Maternity leave cannot exceed {max_days} days (3 months)",
                'law_reference': KENYAN_LEAVE_LAWS['maternity_leave']['legal_reference']
            })
        
        notice_days = (start_date - date.today()).days
        if notice_days < required_notice:
            warnings.append({
                'level': 'warning',
                'message': f"Maternity leave ideally requires {required_notice} days notice. Only {notice_days} days provided.",
                'law_reference': KENYAN_LEAVE_LAWS['maternity_leave']['legal_reference']
            })
        
        return warnings
    
    @staticmethod
    def validate_paternity_leave(employee, days_requested, start_date):
        """Validate paternity leave request"""
        warnings = []
        
        max_days = KENYAN_LEAVE_LAWS['paternity_leave']['max_days']
        
        if days_requested > max_days:
            warnings.append({
                'level': 'error',
                'message': f"Paternity leave cannot exceed {max_days} consecutive days",
                'law_reference': KENYAN_LEAVE_LAWS['paternity_leave']['legal_reference']
            })
        
        return warnings
    
    @staticmethod
    def validate_compassionate_leave(employee, days_requested, reason=None):
        """Validate compassionate/bereavement leave request"""
        warnings = []
        
        max_days = KENYAN_LEAVE_LAWS['compassionate_leave']['max_days']
        
        if days_requested > max_days:
            warnings.append({
                'level': 'warning',
                'message': f"Compassionate leave typically limited to {max_days} days. Extended leave may require HR approval.",
                'law_reference': KENYAN_LEAVE_LAWS['compassionate_leave']['legal_reference']
            })
        
        return warnings
    
    @staticmethod
    def validate_leave_request(leave_type, employee, days_requested, start_date, **kwargs):
        """
        Main validation method that routes to specific leave type validators.
        
        Args:
            leave_type: String identifier for leave type
            employee: Employee object
            days_requested: Number of days requested
            start_date: Start date of leave
            **kwargs: Additional arguments for specific leave types
            
        Returns:
            Tuple of (is_compliant, warnings_list)
        """
        warnings = []
        
        if leave_type == 'annual_leave':
            warnings = KenyanLaborLaws.validate_annual_leave(employee, days_requested, start_date)
        elif leave_type == 'sick_leave':
            has_cert = kwargs.get('has_medical_certificate', False)
            warnings = KenyanLaborLaws.validate_sick_leave(employee, days_requested, has_cert)
        elif leave_type == 'maternity_leave':
            warnings = KenyanLaborLaws.validate_maternity_leave(employee, days_requested, start_date)
        elif leave_type == 'paternity_leave':
            warnings = KenyanLaborLaws.validate_paternity_leave(employee, days_requested, start_date)
        elif leave_type == 'compassionate_leave':
            reason = kwargs.get('reason')
            warnings = KenyanLaborLaws.validate_compassionate_leave(employee, days_requested, reason)
        elif leave_type == 'study_leave':
            max_days = KENYAN_LEAVE_LAWS['study_leave']['max_days']
            if days_requested > max_days:
                warnings.append({
                    'level': 'warning',
                    'message': f"Study leave typically limited to {max_days} days per year",
                    'law_reference': KENYAN_LEAVE_LAWS['study_leave']['legal_reference']
                })
        
        # Determine overall compliance
        has_errors = any(w.get('level') == 'error' for w in warnings)
        is_compliant = not has_errors
        
        return is_compliant, warnings
    
    @staticmethod
    def get_overtime_rate(hours_worked, is_holiday=False, is_night_shift=False):
        """
        Calculate the overtime rate multiplier.
        
        Args:
            hours_worked: Total hours worked
            is_holiday: Whether work was on a holiday
            is_night_shift: Whether work was during night hours
            
        Returns:
            Decimal multiplier for overtime pay
        """
        normal_hours = WORKING_HOURS['normal_hours_per_day']
        
        if hours_worked <= normal_hours:
            return Decimal('1.0')  # Normal rate
        
        if is_holiday:
            return WORKING_HOURS['overtime_rate_holiday']
        
        if is_night_shift:
            return WORKING_HOURS['overtime_rate_night']
        
        return WORKING_HOURS['overtime_rate_normal']
    
    @staticmethod
    def calculate_overtime_hours(hours_worked, shift_type='day'):
        """
        Calculate overtime hours from total hours worked.
        
        Args:
            hours_worked: Total hours worked
            shift_type: 'day' or 'night'
            
        Returns:
            Decimal overtime hours
        """
        normal_hours = Decimal(str(WORKING_HOURS['normal_hours_per_day']))
        total_hours = Decimal(str(hours_worked))
        
        if total_hours <= normal_hours:
            return Decimal('0')
        
        return total_hours - normal_hours
    
    @staticmethod
    def get_leave_type_display(leave_type):
        """Get human-readable name for leave type"""
        leave_info = KENYAN_LEAVE_LAWS.get(leave_type)
        if leave_info:
            return leave_info.get('name', leave_type.replace('_', ' ').title())
        return leave_type.replace('_', ' ').title()
    
    @staticmethod
    def get_all_leave_types():
        """Get all available leave types with their details"""
        return {
            key: {
                'name': value.get('name', key.replace('_', ' ').title()),
                'max_days': value.get('max_days', value.get('max_days_with_certificate', 0)),
                'notice_days': value.get('notice_required_days', 0),
                'description': value.get('description', ''),
                'legal_reference': value.get('legal_reference', '')
            }
            for key, value in KENYAN_LEAVE_LAWS.items()
        }


# Utility functions for external use
def get_statutory_deductions():
    """
    Get information about statutory deductions in Kenya.
    
    Returns:
        Dictionary with NSSF, NHIF, and PAYE information
    """
    return {
        'NSSF': {
            'name': 'National Social Security Fund',
            'employee_rate': Decimal('0.06'),  # 6%
            'employer_rate': Decimal('0.06'),  # 6%
            'max_contribution': 2160,  # KES
            'legal_reference': 'NSSF Act 2013'
        },
        'NHIF': {
            'name': 'National Hospital Insurance Fund',
            'rate_type': 'graduated',  # Based on income brackets
            'min_contribution': 150,  # KES
            'max_contribution': 1700,  # KES
            'legal_reference': 'NHIF Act 1998'
        },
        'PAYE': {
            'name': 'Pay As You Earn',
            'rate_type': 'progressive',  # Based on income tax bands
            'personal_relief': 2400,  # KES per month
            'legal_reference': 'Income Tax Act'
        }
    }


def get_termination_notice_period(years_of_service):
    """
    Get the required notice period for termination based on service length.
    
    Args:
        years_of_service: Number of years the employee has worked
        
    Returns:
        Integer days of notice required
    """
    if years_of_service < 1:
        return 7  # 7 days
    elif years_of_service < 5:
        return 14  # 14 days (2 weeks)
    else:
        return 30  # 30 days (1 month)


def calculate_severance_pay(monthly_salary, years_of_service):
    """
    Calculate severance pay according to Kenyan law.
    
    Args:
        monthly_salary: Employee's monthly salary
        years_of_service: Number of years of service
        
    Returns:
        Decimal severance pay amount
    """
    # 15 days pay for each completed year of service
    daily_salary = Decimal(str(monthly_salary)) / Decimal('30')
    severance_days = 15
    
    return daily_salary * severance_days * Decimal(str(years_of_service))


# Export commonly used items
__all__ = [
    'KENYAN_LEAVE_LAWS',
    'WORKING_HOURS',
    'calculate_working_days',
    'calculate_calendar_days',
    'get_leave_entitlement',
    'get_max_leave_days',
    'get_notice_required_days',
    'validate_leave_notice',
    'KenyanLaborLaws',
    'get_statutory_deductions',
    'get_termination_notice_period',
    'calculate_severance_pay'
]