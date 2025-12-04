"""
Sakina Gas Company - Models Package
Ensures all models are imported so SQLAlchemy knows about them.
"""

# FIX: Import all model classes at the end of the package's __init__
# This ensures SQLAlchemy registers them correctly and resolves forward references.
from .attendance import AttendanceRecord
from .audit import AuditLog
from .disciplinary_action import DisciplinaryAction
from .employee import Employee
from .holiday import Holiday
from .leave import LeaveRequest
from .performance import PerformanceReview
from .user import User
# The Base class is imported from database.py into the models module scope
# to support DeclarativeBase inheritance, but it is defined outside this package
from database import Base # Ensure Base is accessible in the models package

# This file is intentionally minimal to avoid multiple mapper definitions