"""
Professional Configuration for Sakina Gas Attendance Management System
Enhanced with brand styling and enterprise features
"""
import os
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    # Core Flask Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'sakina-gas-professional-2025-secret-key'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'sakina_professional.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 300,
        'pool_pre_ping': True
    }
    
    # Session and Security
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)  # Work day duration
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600
    
    # Company Branding (from uploaded logo)
    COMPANY_NAME = "Sakina Gas Company"
    COMPANY_TAGLINE = "Excellence in Energy Solutions"
    COMPANY_LOGO = "logo.png"
    
    # Brand Colors from Logo
    BRAND_COLORS = {
        'primary_orange': '#FF5722',
        'secondary_orange': '#FF9800', 
        'primary_blue': '#1976D2',
        'light_blue': '#42A5F5',
        'success_green': '#4CAF50',
        'warning_amber': '#FFC107',
        'danger_red': '#F44336',
        'dark_gray': '#263238',
        'light_gray': '#FAFAFA',
        'white': '#FFFFFF'
    }
    
    # System Configuration
    LOCATIONS = {
        'head_office': {
            'name': 'Head Office',
            'code': 'HQ',
            'address': 'Nairobi, Kenya',
            'has_shifts': False,
            'shifts': [],
            'timezone': 'Africa/Nairobi'
        },
        'dandora': {
            'name': 'Dandora Station', 
            'code': 'DAN',
            'address': 'Dandora, Nairobi',
            'has_shifts': True,
            'shifts': ['day', 'night'],
            'timezone': 'Africa/Nairobi'
        },
        'tassia': {
            'name': 'Tassia Station',
            'code': 'TAS', 
            'address': 'Tassia, Nairobi',
            'has_shifts': True,
            'shifts': ['day', 'night'],
            'timezone': 'Africa/Nairobi'
        },
        'kiambu': {
            'name': 'Kiambu Station',
            'code': 'KIA',
            'address': 'Kiambu County',
            'has_shifts': True, 
            'shifts': ['day', 'night'],
            'timezone': 'Africa/Nairobi'
        }
    }
    
    # Shift Configuration
    SHIFT_SCHEDULES = {
        'day': {
            'name': 'Day Shift',
            'start_time': '06:00',
            'end_time': '18:00',
            'duration_hours': 12,
            'break_minutes': 60
        },
        'night': {
            'name': 'Night Shift', 
            'start_time': '18:00',
            'end_time': '06:00',
            'duration_hours': 12,
            'break_minutes': 60
        }
    }
    
    # Leave Types (Kenyan Employment Act 2007 Compliant)
    LEAVE_TYPES = {
        'annual_leave': {
            'name': 'Annual Leave',
            'max_days': 21,
            'requires_approval': True,
            'notice_days': 14,
            'color': '#4CAF50'
        },
        'sick_leave': {
            'name': 'Sick Leave', 
            'max_days': 7,
            'requires_approval': False,
            'notice_days': 0,
            'color': '#FF9800',
            'requires_certificate': True
        },
        'maternity_leave': {
            'name': 'Maternity Leave',
            'max_days': 90, 
            'requires_approval': True,
            'notice_days': 30,
            'color': '#E91E63'
        },
        'paternity_leave': {
            'name': 'Paternity Leave',
            'max_days': 14,
            'requires_approval': True, 
            'notice_days': 7,
            'color': '#2196F3'
        },
        'compassionate_leave': {
            'name': 'Compassionate Leave',
            'max_days': 7,
            'requires_approval': True,
            'notice_days': 0,
            'color': '#795548'
        },
        'unpaid_leave': {
            'name': 'Unpaid Leave',
            'max_days': None,
            'requires_approval': True, 
            'notice_days': 14,
            'color': '#9E9E9E'
        }
    }
    
    # Department Structure
    DEPARTMENTS = {
        'operations': {
            'name': 'Operations',
            'code': 'OPS',
            'color': '#FF5722'
        },
        'administration': {
            'name': 'Administration', 
            'code': 'ADM',
            'color': '#1976D2'
        },
        'finance': {
            'name': 'Finance',
            'code': 'FIN', 
            'color': '#4CAF50'
        },
        'hr': {
            'name': 'Human Resources',
            'code': 'HR',
            'color': '#E91E63'
        },
        'security': {
            'name': 'Security',
            'code': 'SEC',
            'color': '#795548'
        },
        'maintenance': {
            'name': 'Maintenance',
            'code': 'MNT',
            'color': '#607D8B'
        }
    }
    
    # Application Settings
    ITEMS_PER_PAGE = 25
    MAX_UPLOAD_SIZE = 5 * 1024 * 1024  # 5MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf', 'doc', 'docx'}
    
    # Email Configuration (for future notifications)
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', '587'))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    
    # Reporting and Analytics
    ENABLE_ANALYTICS = True
    CHART_COLORS = ['#FF5722', '#1976D2', '#4CAF50', '#FF9800', '#E91E63', '#795548']
    
    # System Limits
    MAX_EMPLOYEES_PER_LOCATION = 100
    MAX_LEAVE_REQUESTS_PER_MONTH = 50
    SESSION_TIMEOUT_MINUTES = 480  # 8 hours

class DevelopmentConfig(Config):
    DEBUG = True
    DEVELOPMENT = True

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    
class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}