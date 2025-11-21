"""
Database Configuration and Instance
This file creates the database instance and handles initialization
"""

from flask_sqlalchemy import SQLAlchemy

# Create the database instance
db = SQLAlchemy()

def init_database(app):
    """Initialize the database with the Flask app"""
    db.init_app(app)
    
    # Import models after db initialization to avoid circular imports
    from models.user import User
    from models.employee import Employee
    from models.attendance import AttendanceRecord
    from models.leave import LeaveRequest
    from models.holiday import Holiday
    from models.audit import AuditLog
    from models.performance import PerformanceReview
    
    # Create all tables
    with app.app_context():
        db.create_all()
        print("✅ Database tables created successfully!")
        
    return db