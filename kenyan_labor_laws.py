"""
Kenyan Labor Laws Compliance Module
Employment Act 2007 - Leave Entitlements and Validations
"""

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
        'name': 'Study Leave',
        'description': 'For approved educational courses',
        'notice_required_days': 30,
        'requires_approval': True,
        'may_be_unpaid': True,
        'legal_reference': 'Employment Act 2007, Section 32'
    }
}

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
                'message': f"Annual leave requires {required_notice} days notice. Current notice: {notice_days} days",
                'law_reference': KENYAN_LEAVE_LAWS['annual_leave']['legal_reference']
            })
        
        # Check employee's remaining balance
        remaining_balance = employee.current_leave_balance
        if days_requested > remaining_balance:
            warnings.append({
                'level': 'error',
                'message': f"Employee has only {remaining_balance} days of annual leave remaining",
                'law_reference': KENYAN_LEAVE_LAWS['annual_leave']['legal_reference']
            })
        
        return warnings
    
    @staticmethod
    def validate_sick_leave(employee, days_requested, has_medical_certificate=False):
        """Validate sick leave request"""
        warnings = []
        
        if not has_medical_certificate:
            max_days = KENYAN_LEAVE_LAWS['sick_leave']['max_days_without_certificate']
            if days_requested > max_days:
                warnings.append({
                    'level': 'error',
                    'message': f"Sick leave without medical certificate cannot exceed {max_days} days",
                    'law_reference': KENYAN_LEAVE_LAWS['sick_leave']['legal_reference']
                })
        else:
            max_days = KENYAN_LEAVE_LAWS['sick_leave']['max_days_with_certificate']
            if days_requested > max_days:
                warnings.append({
                    'level': 'warning',
                    'message': f"Sick leave with certificate should not exceed {max_days} days. Medical board approval may be required.",
                    'law_reference': KENYAN_LEAVE_LAWS['sick_leave']['legal_reference']
                })
        
        # Suggest medical certificate if over threshold
        certificate_threshold = KENYAN_LEAVE_LAWS['sick_leave']['requires_medical_certificate_after']
        if days_requested > certificate_threshold and not has_medical_certificate:
            warnings.append({
                'level': 'warning',
                'message': f"Medical certificate required for sick leave over {certificate_threshold} days",
                'law_reference': KENYAN_LEAVE_LAWS['sick_leave']['legal_reference']
            })
        
        return warnings
    
    @staticmethod
    def validate_maternity_leave(employee, days_requested, start_date, expected_delivery_date=None):
        """Validate maternity leave request"""
        warnings = []
        
        # Check maximum days
        max_days = KENYAN_LEAVE_LAWS['maternity_leave']['max_days']
        if days_requested > max_days:
            warnings.append({
                'level': 'error',
                'message': f"Maternity leave cannot exceed {max_days} days (3 months)",
                'law_reference': KENYAN_LEAVE_LAWS['maternity_leave']['legal_reference']
            })
        
        # Check notice period
        notice_days = (start_date - date.today()).days
        required_notice = KENYAN_LEAVE_LAWS['maternity_leave']['notice_required_days']
        
        if notice_days < required_notice:
            warnings.append({
                'level': 'warning',
                'message': f"Maternity leave requires {required_notice} days notice. Current notice: {notice_days} days",
                'law_reference': KENYAN_LEAVE_LAWS['maternity_leave']['legal_reference']
            })
        
        # Check prenatal period if delivery date is provided
        if expected_delivery_date:
            max_prenatal = KENYAN_LEAVE_LAWS['maternity_leave']['max_prenatal_days']
            prenatal_days = (expected_delivery_date - start_date).days
            
            if prenatal_days > max_prenatal:
                warnings.append({
                    'level': 'warning',
                    'message': f"Prenatal leave should not exceed {max_prenatal} days before delivery",
                    'law_reference': KENYAN_LEAVE_LAWS['maternity_leave']['legal_reference']
                })
        
        return warnings
    
    @staticmethod
    def validate_paternity_leave(employee, days_requested, start_date):
        """Validate paternity leave request"""
        warnings = []
        
        # Check maximum days
        max_days = KENYAN_LEAVE_LAWS['paternity_leave']['max_days']
        if days_requested > max_days:
            warnings.append({
                'level': 'error',
                'message': f"Paternity leave cannot exceed {max_days} consecutive days",
                'law_reference': KENYAN_LEAVE_LAWS['paternity_leave']['legal_reference']
            })
        
        # Check notice period
        notice_days = (start_date - date.today()).days
        required_notice = KENYAN_LEAVE_LAWS['paternity_leave']['notice_required_days']
        
        if notice_days < required_notice:
            warnings.append({
                'level': 'warning',
                'message': f"Paternity leave requires {required_notice} days notice. Current notice: {notice_days} days",
                'law_reference': KENYAN_LEAVE_LAWS['paternity_leave']['legal_reference']
            })
        
        return warnings
    
    @staticmethod
    def validate_compassionate_leave(employee, days_requested, relationship=None):
        """Validate compassionate leave request"""
        warnings = []
        
        # Check maximum days
        max_days = KENYAN_LEAVE_LAWS['compassionate_leave']['max_days']
        if days_requested > max_days:
            warnings.append({
                'level': 'warning',
                'message': f"Compassionate leave typically should not exceed {max_days} days",
                'law_reference': KENYAN_LEAVE_LAWS['compassionate_leave']['legal_reference']
            })
        
        # Check if immediate family (this would need to be implemented based on company policy)
        if relationship and relationship not in ['parent', 'spouse', 'child', 'sibling']:
            warnings.append({
                'level': 'warning',
                'message': "Compassionate leave is typically for immediate family members only",
                'law_reference': KENYAN_LEAVE_LAWS['compassionate_leave']['legal_reference']
            })
        
        return warnings

def validate_leave_request(employee, leave_type, days_requested, start_date, **kwargs):
    """Main validation function for all leave types"""
    validator = KenyanLaborLaws()
    
    if leave_type == 'annual_leave':
        return validator.validate_annual_leave(employee, days_requested, start_date)
    elif leave_type == 'sick_leave':
        has_certificate = kwargs.get('has_medical_certificate', False)
        return validator.validate_sick_leave(employee, days_requested, has_certificate)
    elif leave_type == 'maternity_leave':
        delivery_date = kwargs.get('expected_delivery_date')
        return validator.validate_maternity_leave(employee, days_requested, start_date, delivery_date)
    elif leave_type == 'paternity_leave':
        return validator.validate_paternity_leave(employee, days_requested, start_date)
    elif leave_type == 'compassionate_leave':
        relationship = kwargs.get('relationship')
        return validator.validate_compassionate_leave(employee, days_requested, relationship)
    else:
        return []  # No specific validation for other leave types

def create_leave_warning_message(warnings):
    """Create a formatted warning message from validation results"""
    if not warnings:
        return None
    
    error_messages = [w['message'] for w in warnings if w['level'] == 'error']
    warning_messages = [w['message'] for w in warnings if w['level'] == 'warning']
    
    message_parts = []
    
    if error_messages:
        message_parts.append("⛔ LEGAL VIOLATIONS:")
        message_parts.extend([f"• {msg}" for msg in error_messages])
    
    if warning_messages:
        if error_messages:
            message_parts.append("")
        message_parts.append("⚠️ WARNINGS:")
        message_parts.extend([f"• {msg}" for msg in warning_messages])
    
    return "\n".join(message_parts)

def format_leave_type_display(leave_type):
    """Format leave type for display"""
    return KENYAN_LEAVE_LAWS.get(leave_type, {}).get('name', leave_type.replace('_', ' ').title())

def get_leave_type_info(leave_type):
    """Get detailed information about a leave type"""
    return KENYAN_LEAVE_LAWS.get(leave_type, {})

def calculate_working_days(start_date, end_date, exclude_weekends=True, exclude_holidays=None):
    """Calculate working days between two dates"""
    if start_date > end_date:
        return 0
    
    working_days = 0
    current_date = start_date
    
    # Get holidays to exclude
    holidays = exclude_holidays or []
    holiday_dates = [h.date if hasattr(h, 'date') else h for h in holidays]
    
    while current_date <= end_date:
        # Skip weekends if requested
        if exclude_weekends and current_date.weekday() >= 5:  # Saturday = 5, Sunday = 6
            current_date += timedelta(days=1)
            continue
        
        # Skip holidays
        if current_date in holiday_dates:
            current_date += timedelta(days=1)
            continue
        
        working_days += 1
        current_date += timedelta(days=1)
    
    return working_days

# Quick reference constants
ANNUAL_LEAVE_DAYS = 21
SICK_LEAVE_DAYS_NO_CERT = 7
SICK_LEAVE_DAYS_WITH_CERT = 30
MATERNITY_LEAVE_DAYS = 90
PATERNITY_LEAVE_DAYS = 14
COMPASSIONATE_LEAVE_DAYS = 7