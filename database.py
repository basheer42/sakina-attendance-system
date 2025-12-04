"""
Sakina Gas Company - Database Configuration
Built from scratch - Professional database setup and initialization
Version 3.0 - SQLAlchemy 2.0+ compatible
"""

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase
from flask import Flask # FIX: Added Flask import for proper app context


# Define naming convention for constraints (helps with migrations)
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
    """
    Initialize database with application context
    This function should be called from the main application
    """
    with app.app_context():
        # Import all models via the package __init__ to register them with SQLAlchemy once
        try:
            import models
            # Access a single attribute to ensure the models module is fully loaded
            app.logger.debug(f"Loaded {len(models.Base.registry.mappers)} models.")
        except Exception as e:
            app.logger.error(f"Failed to import models package: {e}")
            raise

        # Create all tables
        db.create_all()
        
        app.logger.info('Database tables created successfully')
        
        # Verify database connection
        try:
            db.session.execute(db.text('SELECT 1'))
            app.logger.info('Database connection verified')
        except Exception as e:
            app.logger.error(f'Database connection failed: {e}')
            raise

# Export the db instance for use in models and routes
__all__ = ['db', 'init_database']