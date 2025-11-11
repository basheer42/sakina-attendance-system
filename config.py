"""
Configuration settings for Sakina Gas Attendance System
Production-ready configuration with security best practices
"""
import os
from datetime import timedelta

class Config:
    """Base configuration class"""
    
    # Security Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'sakina-gas-2024-secure-key-change-in-production'
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600  # 1 hour
    
    # Database Configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///sakina_attendance.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    
    # Session Configuration
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)  # 8 hour work day
    SESSION_PROTECTION = 'strong'
    
    # Company Information
    COMPANY_NAME = 'Sakina Gas Company'
    COMPANY_TAGLINE = 'Excellence in Energy Solutions'
    COMPANY_ADDRESS = 'Nairobi, Kenya'
    COMPANY_PHONE = '+254 700 000 000'
    COMPANY_EMAIL = 'info@sakinagas.com'
    
    # Brand Colors (Professional Blue Theme)
    BRAND_COLORS = {
        'primary': '#1B4F72',      # Dark Blue
        'secondary': '#2E86AB',    # Medium Blue  
        'accent': '#A23B72',       # Accent Purple
        'success': '#28A745',      # Green
        'warning': '#FFC107',      # Yellow
        'danger': '#DC3545',       # Red
        'info': '#17A2B8',         # Cyan
        'light': '#F8F9FA',        # Light Gray
        'dark': '#343A40'          # Dark Gray
    }
    
    # Location Configuration
    LOCATIONS = {
        'head_office': {
            'name': 'Head Office',
            'address': 'CBD, Nairobi',
            'shifts': [],  # No shifts for head office
            'work_hours': {'start': '08:00', 'end': '17:00'},
            'color': '#1B4F72'
        },
        'dandora': {
            'name': 'Dandora Station',
            'address': 'Dandora, Nairobi',
            'shifts': ['day', 'night'],
            'work_hours': {
                'day': {'start': '06:00', 'end': '18:00'},
                'night': {'start': '18:00', 'end': '06:00'}
            },
            'color': '#2E86AB'
        },
        'tassia': {
            'name': 'Tassia Station',
            'address': 'Tassia, Nairobi',
            'shifts': ['day', 'night'],
            'work_hours': {
                'day': {'start': '06:00', 'end': '18:00'},
                'night': {'start': '18:00', 'end': '06:00'}
            },
            'color': '#28A745'
        },
        'kiambu': {
            'name': 'Kiambu Station',
            'address': 'Kiambu Town',
            'shifts': ['day', 'night'],
            'work_hours': {
                'day': {'start': '06:00', 'end': '18:00'},
                'night': {'start': '18:00', 'end': '06:00'}
            },
            'color': '#FD7E14'
        }
    }
    
    # Leave Type Configuration (Updated for Kenya)
    LEAVE_TYPES = {
        'annual_leave': {
            'name': 'Annual Leave',
            'max_days': 21,
            'requires_approval': True,
            'notice_days': 14,
            'color': '#007BFF',
            'icon': 'calendar-check'
        },
        'sick_leave': {
            'name': 'Sick Leave',
            'max_days': 7,  # Without certificate
            'requires_approval': True,
            'notice_days': 0,
            'color': '#DC3545',
            'icon': 'heart-pulse'
        },
        'maternity_leave': {
            'name': 'Maternity Leave',
            'max_days': 90,  # 3 months
            'requires_approval': True,
            'notice_days': 30,
            'color': '#E91E63',
            'icon': 'baby'
        },
        'paternity_leave': {
            'name': 'Paternity Leave',
            'max_days': 14,
            'requires_approval': True, 
            'notice_days': 7,
            'color': '#2196F3',
            'icon': 'person'
        },
        'compassionate_leave': {
            'name': 'Compassionate Leave',
            'max_days': 7,
            'requires_approval': True,
            'notice_days': 0,
            'color': '#795548',
            'icon': 'heart'
        },
        'study_leave': {
            'name': 'Study Leave',
            'max_days': None,  # Varies
            'requires_approval': True,
            'notice_days': 30,
            'color': '#9C27B0',
            'icon': 'book'
        },
        'unpaid_leave': {
            'name': 'Unpaid Leave',
            'max_days': None,
            'requires_approval': True, 
            'notice_days': 14,
            'color': '#9E9E9E',
            'icon': 'clock'
        }
    }
    
    # Department Structure
    DEPARTMENTS = {
        'operations': {
            'name': 'Operations', 
            'code': 'OPS',
            'color': '#FF5722',
            'description': 'Gas distribution and station operations'
        },
        'administration': {
            'name': 'Administration', 
            'code': 'ADM',
            'color': '#1976D2',
            'description': 'Administrative and office management'
        },
        'finance': {
            'name': 'Finance', 
            'code': 'FIN',
            'color': '#4CAF50',
            'description': 'Financial management and accounting'
        },
        'hr': {
            'name': 'Human Resources', 
            'code': 'HR',
            'color': '#E91E63',
            'description': 'Human resources management'
        },
        'security': {
            'name': 'Security', 
            'code': 'SEC',
            'color': '#795548',
            'description': 'Security and safety operations'
        },
        'maintenance': {
            'name': 'Maintenance', 
            'code': 'MNT',
            'color': '#607D8B',
            'description': 'Equipment and facility maintenance'
        },
        'transport': {
            'name': 'Transport', 
            'code': 'TRP',
            'color': '#FF9800',
            'description': 'Vehicle fleet and logistics'
        }
    }
    
    # User Roles Configuration
    USER_ROLES = {
        'hr_manager': {
            'name': 'HR Manager',
            'permissions': [
                'view_all_employees',
                'add_employees', 
                'edit_employees',
                'delete_employees',
                'approve_leaves',
                'reject_leaves',
                'view_all_attendance',
                'edit_attendance',
                'view_reports',
                'manage_holidays',
                'manage_users'
            ]
        },
        'station_manager': {
            'name': 'Station Manager',
            'permissions': [
                'view_location_employees',
                'mark_attendance',
                'request_leaves',
                'view_location_attendance',
                'view_location_reports'
            ]
        },
        'admin': {
            'name': 'System Administrator',
            'permissions': [
                'all_permissions'
            ]
        }
    }
    
    # Attendance Configuration
    ATTENDANCE_GRACE_PERIOD = 15  # minutes late before marked as late
    OVERTIME_THRESHOLD = 8  # hours before overtime
    
    # File Upload Configuration
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx'}
    
    # Email Configuration (for notifications)
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', '587'))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    
    # Pagination
    ITEMS_PER_PAGE = 25
    
    # Logging Configuration
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.environ.get('LOG_FILE', 'sakina_attendance.log')

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    DEVELOPMENT = True
    WTF_CSRF_ENABLED = False  # Disable CSRF for development
    
class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    
    # Enhanced security for production
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Force HTTPS
    PREFERRED_URL_SCHEME = 'https'
    
class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    
# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}