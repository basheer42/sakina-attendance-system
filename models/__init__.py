"""
Sakina Gas Company - Database Models Package
This module provides centralized model imports and prevents circular dependencies.

IMPORTANT: Models should be imported from this package in routes and other modules.
Direct imports from individual model files should only be done within model files
themselves or when using local imports inside functions.

Usage:
    # Correct usage in routes (inside functions):
    from models.user import User
    from models.employee import Employee
    
    # Or import all at once (use carefully):
    from models import User, Employee, AttendanceRecord

Version: 3.0.0
"""

# =============================================================================
# Model Imports - Lazy Loading to Prevent Circular Dependencies
# =============================================================================

# Note: These imports should be used carefully. In Flask routes, it's recommended
# to import models inside functions to prevent mapper conflicts during app startup.


def get_user_model():
    """Get the User model - use this to avoid circular imports"""
    from models.user import User
    return User


def get_employee_model():
    """Get the Employee model - use this to avoid circular imports"""
    from models.employee import Employee
    return Employee


def get_attendance_model():
    """Get the AttendanceRecord model - use this to avoid circular imports"""
    from models.attendance import AttendanceRecord
    return AttendanceRecord


def get_leave_model():
    """Get the LeaveRequest model - use this to avoid circular imports"""
    from models.leave import LeaveRequest
    return LeaveRequest


def get_holiday_model():
    """Get the Holiday model - use this to avoid circular imports"""
    from models.holiday import Holiday
    return Holiday


def get_audit_model():
    """Get the AuditLog model - use this to avoid circular imports"""
    from models.audit import AuditLog
    return AuditLog


def get_performance_model():
    """Get the PerformanceReview model - use this to avoid circular imports"""
    from models.performance import PerformanceReview
    return PerformanceReview


def get_disciplinary_model():
    """Get the DisciplinaryAction model - use this to avoid circular imports"""
    from models.disciplinary_action import DisciplinaryAction
    return DisciplinaryAction


# =============================================================================
# Direct Model Access (Use with caution - may cause circular import issues)
# =============================================================================

# These are provided for convenience but should be used carefully.
# Prefer using the get_*_model() functions or local imports in functions.

# Lazy imports - only executed when explicitly accessed
_User = None
_Employee = None
_AttendanceRecord = None
_LeaveRequest = None
_Holiday = None
_AuditLog = None
_PerformanceReview = None
_DisciplinaryAction = None


def __getattr__(name):
    """
    Lazy loading of models to prevent circular import issues.
    This is called when an attribute is accessed that doesn't exist.
    """
    global _User, _Employee, _AttendanceRecord, _LeaveRequest
    global _Holiday, _AuditLog, _PerformanceReview, _DisciplinaryAction
    
    if name == 'User':
        if _User is None:
            from models.user import User
            _User = User
        return _User
    
    elif name == 'Employee':
        if _Employee is None:
            from models.employee import Employee
            _Employee = Employee
        return _Employee
    
    elif name == 'AttendanceRecord':
        if _AttendanceRecord is None:
            from models.attendance import AttendanceRecord
            _AttendanceRecord = AttendanceRecord
        return _AttendanceRecord
    
    elif name == 'LeaveRequest':
        if _LeaveRequest is None:
            from models.leave import LeaveRequest
            _LeaveRequest = LeaveRequest
        return _LeaveRequest
    
    elif name == 'Holiday':
        if _Holiday is None:
            from models.holiday import Holiday
            _Holiday = Holiday
        return _Holiday
    
    elif name == 'AuditLog':
        if _AuditLog is None:
            from models.audit import AuditLog
            _AuditLog = AuditLog
        return _AuditLog
    
    elif name == 'PerformanceReview':
        if _PerformanceReview is None:
            from models.performance import PerformanceReview
            _PerformanceReview = PerformanceReview
        return _PerformanceReview
    
    elif name == 'DisciplinaryAction':
        if _DisciplinaryAction is None:
            from models.disciplinary_action import DisciplinaryAction
            _DisciplinaryAction = DisciplinaryAction
        return _DisciplinaryAction
    
    raise AttributeError(f"module 'models' has no attribute '{name}'")


# =============================================================================
# Utility Functions
# =============================================================================

def init_models(app):
    """
    Initialize all models with the Flask application.
    This should be called during app startup after db.init_app().
    
    Args:
        app: Flask application instance
    """
    with app.app_context():
        # Import all models to ensure they're registered with SQLAlchemy
        from models.user import User
        from models.employee import Employee
        from models.attendance import AttendanceRecord
        from models.leave import LeaveRequest
        from models.holiday import Holiday
        from models.audit import AuditLog
        
        # Optional models
        try:
            from models.performance import PerformanceReview
        except ImportError:
            pass
        
        try:
            from models.disciplinary_action import DisciplinaryAction
        except ImportError:
            pass
        
        app.logger.info("All models initialized successfully")


def get_all_models():
    """
    Get a dictionary of all available models.
    Useful for dynamic model access.
    
    Returns:
        Dictionary mapping model names to model classes
    """
    models = {}
    
    try:
        from models.user import User
        models['User'] = User
    except ImportError:
        pass
    
    try:
        from models.employee import Employee
        models['Employee'] = Employee
    except ImportError:
        pass
    
    try:
        from models.attendance import AttendanceRecord
        models['AttendanceRecord'] = AttendanceRecord
    except ImportError:
        pass
    
    try:
        from models.leave import LeaveRequest
        models['LeaveRequest'] = LeaveRequest
    except ImportError:
        pass
    
    try:
        from models.holiday import Holiday
        models['Holiday'] = Holiday
    except ImportError:
        pass
    
    try:
        from models.audit import AuditLog
        models['AuditLog'] = AuditLog
    except ImportError:
        pass
    
    try:
        from models.performance import PerformanceReview
        models['PerformanceReview'] = PerformanceReview
    except ImportError:
        pass
    
    try:
        from models.disciplinary_action import DisciplinaryAction
        models['DisciplinaryAction'] = DisciplinaryAction
    except ImportError:
        pass
    
    return models


# =============================================================================
# Model Name Constants
# =============================================================================

MODEL_NAMES = [
    'User',
    'Employee',
    'AttendanceRecord',
    'LeaveRequest',
    'Holiday',
    'AuditLog',
    'PerformanceReview',
    'DisciplinaryAction'
]

# Expose model names for external use
__all__ = [
    # Model getter functions (recommended)
    'get_user_model',
    'get_employee_model',
    'get_attendance_model',
    'get_leave_model',
    'get_holiday_model',
    'get_audit_model',
    'get_performance_model',
    'get_disciplinary_model',
    # Utility functions
    'init_models',
    'get_all_models',
    'MODEL_NAMES',
    # Direct model names (use with caution)
    'User',
    'Employee',
    'AttendanceRecord',
    'LeaveRequest',
    'Holiday',
    'AuditLog',
    'PerformanceReview',
    'DisciplinaryAction'
]