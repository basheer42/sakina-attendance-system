"""
Sakina Gas Company - Models Package
Fixed to prevent primary mapper conflicts
"""

# Make the Base class accessible for models to inherit from
from database import Base

# DO NOT import any model classes here to prevent mapper conflicts
# Models will be imported individually when needed

__all__ = ['Base']