"""
Models Package - Proper Structure
This __init__.py file only handles imports, not model definitions
"""

# Import the database instance
from database import db

# Import all models for easy access
from models.user import User
from models.employee import Employee
from models.attendance import AttendanceRecord
from models.leave import LeaveRequest
from models.holiday import Holiday
from models.audit import AuditLog
from models.performance import PerformanceReview

# Make all models available when importing from models
__all__ = [
    'db',
    'User', 
    'Employee', 
    'AttendanceRecord', 
    'LeaveRequest', 
    'Holiday',
    'AuditLog',
    'PerformanceReview'
]