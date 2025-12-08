"""
Sakina Gas Company - Database Configuration
FIXED to prevent mapper conflicts - ONLY circular import issues fixed
"""

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

# Define naming convention for constraints
naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s", 
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

# Create metadata with naming convention
metadata = MetaData(naming_convention=naming_convention)

# Create custom base class
class Base(DeclarativeBase):
    pass

# Initialize SQLAlchemy with custom base
db = SQLAlchemy(model_class=Base, metadata=metadata) 

def init_database(app):
    """Initialize database with application context"""
    with app.app_context():
        # FIXED: Import models only when absolutely necessary and in correct order
        # This prevents "primary key mapper already defined" errors
        try:
            # Import models one by one to register them with SQLAlchemy
            from models.user import User
            from models.employee import Employee
            from models.attendance import AttendanceRecord
            from models.leave import LeaveRequest
            from models.holiday import Holiday
            from models.audit import AuditLog
            
            # Import optional models if they exist
            try:
                from models.performance import PerformanceReview
                from models.disciplinary_action import DisciplinaryAction
            except ImportError:
                pass  # These models may not be implemented yet
            
            print("✅ Models imported successfully")
            
        except Exception as e:
            print(f"❌ Failed to import models: {e}")
            app.logger.error(f"Failed to import models: {e}")
            raise

        # Create all tables
        try:
            db.create_all()
            print("✅ Database tables created successfully")
            app.logger.info('Database tables created successfully')
        except Exception as e:
            print(f"❌ Database table creation failed: {e}")
            app.logger.error(f'Database table creation failed: {e}')
            raise
        
        # Verify database connection
        try:
            db.session.execute(db.text('SELECT 1'))
            print("✅ Database connection verified")
            app.logger.info('Database connection verified')
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            app.logger.error(f'Database connection failed: {e}')
            raise

# Export the db instance
__all__ = ['db', 'init_database']