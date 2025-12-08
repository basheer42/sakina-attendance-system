"""
Sakina Gas Company - Models Package
FIXED: Prevents circular imports and SQLAlchemy mapper conflicts

CRITICAL: Do NOT import any model classes at the package level!
This prevents "primary key mapper already defined" errors.
Models will be imported individually inside functions when needed.
"""

# Only make Base class available for inheritance
from database import Base

# IMPORTANT: Models are NOT imported here to prevent circular imports
# Import them individually in functions like this:
#   from models.user import User
#   from models.employee import Employee

__all__ = ['Base']