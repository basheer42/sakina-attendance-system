"""
Kenyan Labor Law Compliance Module
Based on Employment Act 2007 and current regulations
"""

class KenyanLaborLaws:
    """
    Kenyan labor law requirements for leave management
    Source: Employment Act No. 11 of 2007
    """
    
    # Maximum leave days allowed by Kenyan law
    LEAVE_LIMITS = {
        'annual_leave': {
            'max_days': 21,
            'description': 'Annual leave (minimum 21 working days per year)',
            'law_reference': 'Employment Act 2007, Section 28'
        },
        'sick_leave': {
            'max_days': 7,  # Without medical certificate
            'description': 'Sick leave (7 days without certificate, more with medical board approval)',
            'law_reference': 'Employment Act 2007, Section 29'
        },
        'maternity_leave': {
            'max_days': 90,  # 3 months
            'description': 'Maternity leave (3 months total)',
            'law_reference': 'Employment Act 2007, Section 30'
        },
        'paternity_leave': {
            'max_days': 14,
            'description': 'Paternity leave (maximum 14 consecutive days)',
            'law_reference': 'Employment Act 2007, Section 30A'
        },
        'compassionate_leave': {
            'max_days': 7,
            'description': 'Compassionate leave (up to 7 days for family bereavement)',
            'law_reference': 'Employment Act 2007, Section 31'
        },
        'study_leave': {
            'max_days': 30,  # Per year, with approval
            'description': 'Study leave (up to 30 days per year with employer approval)',
            'law_reference': 'Employment Act 2007, Section 32'
        },
        'unpaid_leave': {
            'max_days': None,  # No legal limit, employer discretion
            'description': 'Unpaid leave (employer discretion)',
            'law_reference': 'Employment Act 2007, General provisions'
        }
    }
    
    @classmethod
    def validate_leave_request(cls, leave_type, requested_days, employee_id=None):
        """
        Validate leave request against Kenyan labor laws
        Returns: dict with validation result and warnings
        """
        result = {
            'is_valid': True,
            'warnings': [],
            'max_allowed': None,
            'law_reference': None
        }
        
        if leave_type not in cls.LEAVE_LIMITS:
            result['is_valid'] = False
            result['warnings'].append(f"Unknown leave type: {leave_type}")
            return result
        
        leave_info = cls.LEAVE_LIMITS[leave_type]
        max_days = leave_info['max_days']
        
        if max_days is not None and requested_days > max_days:
            result['is_valid'] = False
            result['warnings'].append(
                f"Requested {requested_days} days exceeds maximum of {max_days} days "
                f"allowed for {leave_type.replace('_', ' ')} under Kenyan law."
            )
            result['max_allowed'] = max_days
            result['law_reference'] = leave_info['law_reference']
        
        # Additional validations
        if leave_type == 'maternity_leave':
            if requested_days > 90:
                result['warnings'].append(
                    "Maternity leave exceeds 3 months (90 days) as per Employment Act 2007. "
                    "Additional leave may be unpaid and require medical justification."
                )
        
        elif leave_type == 'paternity_leave':
            if requested_days > 14:
                result['warnings'].append(
                    "Paternity leave exceeds 14 consecutive days as per Employment Act 2007. "
                    "This violates Section 30A of the Employment Act."
                )
        
        elif leave_type == 'sick_leave':
            if requested_days > 7:
                result['warnings'].append(
                    "Sick leave over 7 days requires medical certificate "
                    "as per Employment Act 2007, Section 29."
                )
        
        return result
    
    @classmethod
    def get_leave_balance_info(cls, employee_id, leave_type, year=None):
        """
        Calculate remaining leave balance for an employee
        This would integrate with actual database queries
        """
        # This is a placeholder - in actual implementation,
        # this would query the database for used leave days
        return {
            'total_entitled': cls.LEAVE_LIMITS.get(leave_type, {}).get('max_days', 0),
            'used_days': 0,  # Query from database
            'remaining_days': 0,  # Calculate
            'year': year or 2025
        }
    
    @classmethod
    def generate_compliance_report(cls, leave_requests):
        """
        Generate compliance report for HR review
        """
        violations = []
        warnings = []
        
        for request in leave_requests:
            validation = cls.validate_leave_request(
                request.leave_type, 
                request.total_days, 
                request.employee_id
            )
            
            if not validation['is_valid']:
                violations.append({
                    'employee': request.employee.full_name,
                    'leave_type': request.leave_type,
                    'requested_days': request.total_days,
                    'warnings': validation['warnings'],
                    'law_reference': validation['law_reference']
                })
        
        return {
            'total_requests': len(leave_requests),
            'violations': violations,
            'violation_count': len(violations),
            'compliance_rate': (len(leave_requests) - len(violations)) / len(leave_requests) * 100 if leave_requests else 100
        }

# Additional helper functions for the web interface

def create_leave_warning_message(validation_result):
    """Create user-friendly warning message for the frontend"""
    if validation_result['is_valid']:
        return None
    
    warning_msg = "⚠️ LEGAL COMPLIANCE WARNING\n\n"
    for warning in validation_result['warnings']:
        warning_msg += f"• {warning}\n"
    
    if validation_result['law_reference']:
        warning_msg += f"\nLegal Reference: {validation_result['law_reference']}"
    
    warning_msg += "\n\nDo you wish to proceed anyway? (HR Manager approval required)"
    
    return warning_msg

def format_leave_type_display(leave_type):
    """Format leave type for display"""
    type_mapping = {
        'annual_leave': 'Annual Leave',
        'sick_leave': 'Sick Leave',
        'maternity_leave': 'Maternity Leave',
        'paternity_leave': 'Paternity Leave',
        'compassionate_leave': 'Compassionate Leave',
        'study_leave': 'Study Leave',
        'unpaid_leave': 'Unpaid Leave'
    }
    return type_mapping.get(leave_type, leave_type.replace('_', ' ').title())
