"""
Enhanced Configuration for Sakina Gas Attendance System
Built upon your existing comprehensive configuration with additional professional features
"""
import os
from datetime import timedelta

class Config:
    """Base configuration class with enhanced professional features"""
    
    # Core Flask Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'sakina-gas-2024-ultra-secure-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///sakina_professional.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Enhanced Security Configuration
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600  # 1 hour
    WTF_CSRF_SECRET_KEY = SECRET_KEY
    
    # Session Management with Enhanced Security
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)  # 8-hour work day
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_REFRESH_EACH_REQUEST = True
    
    # Rate Limiting
    RATELIMIT_STORAGE_URL = 'memory://'
    RATELIMIT_DEFAULT = "1000 per hour"
    RATELIMIT_HEADERS_ENABLED = True
    
    # Company Information
    COMPANY_NAME = 'Sakina Gas Company'
    COMPANY_TAGLINE = 'Excellence in Energy Solutions Since 1995'
    COMPANY_LOGO = 'images/logo.png'
    COMPANY_ADDRESS = 'Industrial Area, Nairobi, Kenya'
    COMPANY_PHONE = '+254 700 000 000'
    COMPANY_EMAIL = 'info@sakinagas.com'
    COMPANY_WEBSITE = 'www.sakinagas.com'
    
    # Enhanced Company Locations with Detailed Configuration
    COMPANY_LOCATIONS = {
        'head_office': {
            'name': 'Head Office',
            'address': 'Industrial Area, Nairobi, Kenya',
            'phone': '+254 700 001 000',
            'email': 'headoffice@sakinagas.com',
            'manager_email': 'manager.ho@sakinagas.com',
            'coordinates': {'lat': -1.3067, 'lng': 36.8331},
            'working_hours': {
                'monday_friday': {'start': '08:00', 'end': '17:00'},
                'saturday': {'start': '08:00', 'end': '13:00'},
                'sunday': 'closed'
            },
            'shifts': ['day'],
            'departments': ['administration', 'finance', 'hr', 'management'],
            'facilities': ['parking', 'cafeteria', 'conference_rooms', 'security'],
            'capacity': 50,
            'timezone': 'Africa/Nairobi'
        },
        'dandora': {
            'name': 'Dandora Gas Station',
            'address': 'Dandora Phase 4, Nairobi, Kenya',
            'phone': '+254 700 002 000',
            'email': 'dandora@sakinagas.com',
            'manager_email': 'manager.dandora@sakinagas.com',
            'coordinates': {'lat': -1.2574, 'lng': 36.8944},
            'working_hours': {
                'day_shift': {'start': '06:00', 'end': '18:00'}, 
                'night_shift': {'start': '18:00', 'end': '06:00'}
            },
            'shifts': ['day', 'night'],
            'departments': ['operations', 'sales', 'security', 'maintenance'],
            'services': ['lpg_refill', 'cylinder_exchange', 'retail_gas', 'delivery'],
            'facilities': ['storage_tanks', 'loading_bay', 'customer_service', 'safety_equipment'],
            'capacity': 15,
            'daily_capacity_kg': 5000,
            'safety_certifications': ['KBS', 'NEMA', 'Fire_Department'],
            'timezone': 'Africa/Nairobi'
        },
        'tassia': {
            'name': 'Tassia Gas Station',
            'address': 'Tassia, Embakasi South, Nairobi, Kenya',
            'phone': '+254 700 003 000',
            'email': 'tassia@sakinagas.com',
            'manager_email': 'manager.tassia@sakinagas.com',
            'coordinates': {'lat': -1.3373, 'lng': 36.8994},
            'working_hours': {
                'day_shift': {'start': '06:00', 'end': '18:00'}, 
                'night_shift': {'start': '18:00', 'end': '06:00'}
            },
            'shifts': ['day', 'night'],
            'departments': ['operations', 'sales', 'security', 'maintenance'],
            'services': ['lpg_refill', 'cylinder_exchange', 'retail_gas', 'home_delivery'],
            'facilities': ['storage_tanks', 'loading_bay', 'customer_service', 'parking'],
            'capacity': 12,
            'daily_capacity_kg': 4000,
            'safety_certifications': ['KBS', 'NEMA', 'Fire_Department'],
            'timezone': 'Africa/Nairobi'
        },
        'kiambu': {
            'name': 'Kiambu Gas Station',
            'address': 'Kiambu Town Center, Kiambu County, Kenya',
            'phone': '+254 700 004 000',
            'email': 'kiambu@sakinagas.com',
            'manager_email': 'manager.kiambu@sakinagas.com',
            'coordinates': {'lat': -1.1714, 'lng': 36.8356},
            'working_hours': {
                'day_shift': {'start': '06:00', 'end': '18:00'}, 
                'night_shift': {'start': '18:00', 'end': '06:00'}
            },
            'shifts': ['day', 'night'],
            'departments': ['operations', 'sales', 'security', 'maintenance'],
            'services': ['lpg_refill', 'cylinder_exchange', 'retail_gas', 'bulk_supply'],
            'facilities': ['storage_tanks', 'loading_bay', 'customer_service', 'rest_area'],
            'capacity': 10,
            'daily_capacity_kg': 3500,
            'safety_certifications': ['KBS', 'NEMA', 'Fire_Department'],
            'timezone': 'Africa/Nairobi'
        }
    }
    
    # Enhanced Brand Colors and Theme
    BRAND_COLORS = {
        'primary': '#1B4F72',        # Deep Blue - Professional, trustworthy
        'secondary': '#2E86AB',      # Ocean Blue - Innovation, reliability
        'accent': '#A23B72',         # Burgundy - Premium, sophisticated  
        'success': '#28A745',        # Green - Success, growth
        'info': '#17A2B8',          # Cyan - Information, clarity
        'warning': '#FFC107',        # Amber - Warning, attention
        'danger': '#DC3545',         # Red - Error, critical
        'light': '#F8F9FA',         # Light Gray - Background
        'dark': '#343A40',          # Dark Gray - Text
        'muted': '#6C757D',         # Muted Gray - Secondary text
        'white': '#FFFFFF',         # Pure white
        'black': '#000000',         # Pure black
        # Gas industry specific colors
        'gas_blue': '#4A90E2',      # Gas cylinder blue
        'safety_orange': '#FF6B35', # Safety equipment orange
        'energy_yellow': '#FFD23F'  # Energy and efficiency yellow
    }
    
    # Comprehensive Kenyan Labor Law Configuration (Employment Act 2007)
    KENYAN_LABOR_LAWS = {
        'annual_leave': {
            'name': 'Annual Leave',
            'max_days': 21,
            'min_service_months': 12,
            'notice_days': 14,
            'can_carry_forward': True,
            'max_carry_forward': 7,
            'cash_conversion_allowed': False,
            'pro_rata_calculation': True,
            'color': '#28A745',
            'icon': 'calendar-check',
            'description': 'Minimum 21 working days per year after 12 months continuous service',
            'legal_reference': 'Employment Act 2007, Section 28'
        },
        'sick_leave': {
            'name': 'Sick Leave',
            'max_days': 7,
            'max_days_with_certificate': 30,
            'notice_hours': 24,
            'requires_certificate_after': 3,
            'medical_board_required_after': 30,
            'pay_percentage': 100,
            'color': '#DC3545',
            'icon': 'thermometer-half',
            'description': 'Up to 7 days without certificate, more with medical certification',
            'legal_reference': 'Employment Act 2007, Section 29'
        },
        'maternity_leave': {
            'name': 'Maternity Leave',
            'max_days': 90,
            'prenatal_max': 30,
            'postnatal_min': 60,
            'notice_days': 90,
            'pay_percentage': 100,
            'requires_certificate': True,
            'can_be_split': True,
            'color': '#E91E63',
            'icon': 'baby-carriage',
            'description': '3 months total (can be split before/after birth)',
            'legal_reference': 'Employment Act 2007, Section 29A'
        },
        'paternity_leave': {
            'name': 'Paternity Leave',
            'max_days': 14,
            'must_be_consecutive': True,
            'notice_days': 30,
            'pay_percentage': 100,
            'requires_birth_certificate': True,
            'color': '#007BFF',
            'icon': 'user-tie',
            'description': 'Maximum 14 consecutive days',
            'legal_reference': 'Employment Act 2007, Section 29B'
        },
        'compassionate_leave': {
            'name': 'Compassionate Leave',
            'max_days': 7,
            'family_members': ['spouse', 'parent', 'child', 'sibling', 'grandparent'],
            'notice_hours': 48,
            'requires_documentation': True,
            'pay_percentage': 100,
            'color': '#6F42C1',
            'icon': 'heart',
            'description': 'Up to 7 days for family bereavement',
            'legal_reference': 'Employment Act 2007, Section 29C'
        },
        'study_leave': {
            'name': 'Study Leave',
            'max_days': None,
            'requires_approval': True,
            'notice_days': 60,
            'pay_percentage': 0,
            'requires_bond': True,
            'bond_period_years': 2,
            'color': '#20C997',
            'icon': 'graduation-cap',
            'description': 'Educational advancement leave with employer approval'
        },
        'special_leave': {
            'name': 'Special Leave',
            'max_days': 3,
            'occasions': ['wedding', 'graduation', 'religious_obligations'],
            'notice_days': 7,
            'pay_percentage': 100,
            'requires_approval': True,
            'color': '#FD7E14',
            'icon': 'star',
            'description': 'Special occasions and religious obligations'
        },
        'unpaid_leave': {
            'name': 'Unpaid Leave',
            'max_days': None,
            'requires_approval': True, 
            'notice_days': 14,
            'pay_percentage': 0,
            'affects_benefits': True,
            'color': '#9E9E9E',
            'icon': 'clock',
            'description': 'Extended leave without pay'
        }
    }
    
    # Enhanced Department Structure with Detailed Information
    DEPARTMENTS = {
        'operations': {
            'name': 'Operations', 
            'code': 'OPS',
            'color': '#FF5722',
            'icon': 'gear',
            'head_title': 'Operations Manager',
            'description': 'Gas distribution and station operations',
            'locations': ['dandora', 'tassia', 'kiambu'],
            'positions': ['Station Manager', 'Station Attendant', 'Loader', 'Security Guard'],
            'kpis': ['daily_sales', 'safety_incidents', 'customer_satisfaction', 'equipment_uptime'],
            'budget_code': 'OPS-2024'
        },
        'administration': {
            'name': 'Administration', 
            'code': 'ADM',
            'color': '#1976D2',
            'icon': 'building',
            'head_title': 'Administration Manager',
            'description': 'Administrative and office management',
            'locations': ['head_office'],
            'positions': ['Admin Assistant', 'Receptionist', 'Office Clerk', 'Records Officer'],
            'kpis': ['document_processing_time', 'customer_service_rating', 'office_efficiency'],
            'budget_code': 'ADM-2024'
        },
        'finance': {
            'name': 'Finance', 
            'code': 'FIN',
            'color': '#4CAF50',
            'icon': 'calculator',
            'head_title': 'Finance Manager',
            'description': 'Financial management and accounting',
            'locations': ['head_office'],
            'positions': ['Accountant', 'Finance Officer', 'Cashier', 'Auditor'],
            'kpis': ['revenue_growth', 'cost_control', 'cash_flow', 'financial_accuracy'],
            'budget_code': 'FIN-2024'
        },
        'hr': {
            'name': 'Human Resources', 
            'code': 'HR',
            'color': '#E91E63',
            'icon': 'people',
            'head_title': 'HR Manager',
            'description': 'Human resources management',
            'locations': ['head_office'],
            'positions': ['HR Officer', 'Recruitment Specialist', 'Training Coordinator'],
            'kpis': ['employee_satisfaction', 'turnover_rate', 'training_completion', 'compliance_rate'],
            'budget_code': 'HR-2024'
        },
        'security': {
            'name': 'Security', 
            'code': 'SEC',
            'color': '#795548',
            'icon': 'shield-check',
            'head_title': 'Security Manager',
            'description': 'Security and safety operations',
            'locations': ['head_office', 'dandora', 'tassia', 'kiambu'],
            'positions': ['Security Supervisor', 'Security Guard', 'Safety Officer'],
            'kpis': ['incident_response_time', 'safety_compliance', 'security_breaches'],
            'budget_code': 'SEC-2024'
        },
        'maintenance': {
            'name': 'Maintenance', 
            'code': 'MNT',
            'color': '#607D8B',
            'icon': 'wrench',
            'head_title': 'Maintenance Manager',
            'description': 'Equipment and facility maintenance',
            'locations': ['dandora', 'tassia', 'kiambu'],
            'positions': ['Maintenance Technician', 'Equipment Specialist', 'Facility Coordinator'],
            'kpis': ['equipment_uptime', 'maintenance_costs', 'response_time'],
            'budget_code': 'MNT-2024'
        },
        'transport': {
            'name': 'Transport', 
            'code': 'TRP',
            'color': '#FF9800',
            'icon': 'truck',
            'head_title': 'Transport Manager',
            'description': 'Vehicle fleet and logistics',
            'locations': ['head_office', 'dandora', 'tassia', 'kiambu'],
            'positions': ['Driver', 'Fleet Coordinator', 'Logistics Officer'],
            'kpis': ['delivery_time', 'fuel_efficiency', 'vehicle_uptime', 'customer_delivery_rating'],
            'budget_code': 'TRP-2024'
        },
        'sales': {
            'name': 'Sales & Marketing',
            'code': 'SAL',
            'color': '#9C27B0',
            'icon': 'chart-line',
            'head_title': 'Sales Manager',
            'description': 'Sales and marketing operations',
            'locations': ['head_office', 'dandora', 'tassia', 'kiambu'],
            'positions': ['Sales Representative', 'Marketing Officer', 'Customer Service Rep'],
            'kpis': ['sales_revenue', 'customer_acquisition', 'market_share', 'customer_retention'],
            'budget_code': 'SAL-2024'
        }
    }
    
    # Enhanced User Roles with Detailed Permissions
    USER_ROLES = {
        'hr_manager': {
            'name': 'HR Manager',
            'level': 9,
            'department': 'hr',
            'locations': ['all'],
            'permissions': [
                'view_all_employees',
                'add_employees', 
                'edit_employees',
                'deactivate_employees',
                'view_employee_salary',
                'edit_employee_salary',
                'approve_all_leaves',
                'reject_all_leaves',
                'view_all_attendance',
                'edit_all_attendance',
                'override_attendance_rules',
                'view_all_reports',
                'export_reports',
                'manage_holidays',
                'manage_users',
                'manage_departments',
                'view_audit_logs',
                'manage_system_settings',
                'approve_overtime',
                'conduct_disciplinary_actions',
                'manage_performance_reviews'
            ],
            'dashboard_widgets': ['employee_overview', 'leave_approvals', 'attendance_summary', 
                                'compliance_alerts', 'hr_metrics', 'recent_activities'],
            'color': '#E91E63',
            'icon': 'user-crown'
        },
        'station_manager': {
            'name': 'Station Manager',
            'level': 7,
            'department': 'operations',
            'locations': ['location_specific'],
            'permissions': [
                'view_location_employees',
                'mark_attendance',
                'request_leaves_for_employees',
                'view_location_attendance',
                'edit_location_attendance',
                'view_location_reports',
                'manage_location_shifts',
                'approve_location_overtime',
                'view_location_performance',
                'submit_incident_reports',
                'manage_location_schedules'
            ],
            'dashboard_widgets': ['location_overview', 'today_attendance', 'pending_requests',
                                'location_metrics', 'staff_alerts'],
            'color': '#2E86AB',
            'icon': 'building'
        },
        'finance_manager': {
            'name': 'Finance Manager',
            'level': 8,
            'department': 'finance',
            'locations': ['head_office'],
            'permissions': [
                'view_all_employees',
                'view_employee_salary',
                'edit_employee_salary',
                'view_payroll_reports',
                'approve_salary_changes',
                'view_financial_reports',
                'manage_allowances',
                'manage_deductions',
                'view_attendance_for_payroll',
                'approve_expenses'
            ],
            'dashboard_widgets': ['payroll_summary', 'financial_metrics', 'salary_reports',
                                'expense_approvals', 'budget_tracking'],
            'color': '#4CAF50',
            'icon': 'calculator'
        },
        'admin': {
            'name': 'System Administrator',
            'level': 10,
            'department': 'administration',
            'locations': ['all'],
            'permissions': [
                'all_permissions',
                'system_administration',
                'database_management',
                'backup_management',
                'security_management',
                'user_management',
                'system_configuration'
            ],
            'dashboard_widgets': ['system_health', 'user_activities', 'security_alerts',
                                'system_metrics', 'backup_status'],
            'color': '#6F42C1',
            'icon': 'cog'
        },
        'employee': {
            'name': 'Employee',
            'level': 1,
            'department': 'any',
            'locations': ['location_specific'],
            'permissions': [
                'view_own_profile',
                'edit_own_profile',
                'view_own_attendance',
                'request_own_leave',
                'view_own_payslip',
                'clock_in_out'
            ],
            'dashboard_widgets': ['my_attendance', 'my_leaves', 'my_profile'],
            'color': '#17A2B8',
            'icon': 'user'
        }
    }
    
    # Enhanced Attendance Configuration
    ATTENDANCE_GRACE_PERIOD = 15  # minutes late before marked as late
    OVERTIME_THRESHOLD = 8  # hours before overtime kicks in
    OVERTIME_RATES = {
        'weekday': 1.5,    # 150% of normal rate
        'weekend': 2.0,    # 200% of normal rate
        'holiday': 2.5     # 250% of normal rate
    }
    MAX_DAILY_HOURS = 12   # Maximum hours in a day
    BREAK_TIME_MINUTES = 60  # Standard break time
    LATE_PENALTY_AFTER_MINUTES = 30  # When late penalties apply
    
    # Enhanced File Upload Configuration
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
    ALLOWED_EXTENSIONS = {
        'documents': ['pdf', 'doc', 'docx'],
        'images': ['png', 'jpg', 'jpeg', 'gif'],
        'spreadsheets': ['xls', 'xlsx', 'csv'],
        'certificates': ['pdf', 'jpg', 'png']
    }
    
    # Email Configuration for Notifications
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', '587'))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = ('Sakina Gas HR System', 'noreply@sakinagas.com')
    
    # Email Templates
    EMAIL_TEMPLATES = {
        'leave_request': {
            'subject': 'Leave Request Submitted - {employee_name}',
            'template': 'emails/leave_request.html'
        },
        'leave_approved': {
            'subject': 'Leave Request Approved - {leave_type}',
            'template': 'emails/leave_approved.html'
        },
        'leave_rejected': {
            'subject': 'Leave Request Rejected - {leave_type}',
            'template': 'emails/leave_rejected.html'
        },
        'attendance_alert': {
            'subject': 'Attendance Alert - {employee_name}',
            'template': 'emails/attendance_alert.html'
        }
    }
    
    # Pagination and Display
    ITEMS_PER_PAGE = 25
    DASHBOARD_RECENT_ITEMS = 10
    CHART_DEFAULT_DAYS = 30
    
    # Logging Configuration
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.environ.get('LOG_FILE', 'sakina_attendance.log')
    LOG_MAX_BYTES = 10485760  # 10MB
    LOG_BACKUP_COUNT = 5
    
    # Cache Configuration
    CACHE_TYPE = "SimpleCache"
    CACHE_DEFAULT_TIMEOUT = 300  # 5 minutes
    
    # API Configuration
    API_VERSION = "2.0"
    API_RATE_LIMIT = "1000 per hour"
    API_TITLE = "Sakina Gas Attendance API"
    
    # Mobile App Configuration
    MOBILE_APP_NAME = "Sakina Attendance"
    MOBILE_APP_VERSION = "1.0.0"
    PUSH_NOTIFICATIONS_ENABLED = False
    
    # Backup and Maintenance
    BACKUP_SCHEDULE = "daily"  # daily, weekly, monthly
    BACKUP_RETENTION_DAYS = 30
    MAINTENANCE_MODE = False
    
    # Security Settings
    PASSWORD_MIN_LENGTH = 8
    PASSWORD_REQUIRE_UPPERCASE = True
    PASSWORD_REQUIRE_LOWERCASE = True
    PASSWORD_REQUIRE_NUMBERS = True
    PASSWORD_REQUIRE_SPECIAL = True
    MAX_LOGIN_ATTEMPTS = 5
    ACCOUNT_LOCKOUT_DURATION = 30  # minutes
    
    # Timezone and Localization
    TIMEZONE = 'Africa/Nairobi'
    LANGUAGES = ['en', 'sw']  # English, Swahili
    DEFAULT_LANGUAGE = 'en'
    
    # Business Rules
    PROBATION_PERIOD_DAYS = 90  # 3 months
    NOTICE_PERIOD_DAYS = 30
    RETIREMENT_AGE = 65
    MINIMUM_WAGE_KES = 13572  # Kenya minimum wage 2024
    
    @staticmethod
    def init_app(app):
        """Initialize application with configuration"""
        pass

class DevelopmentConfig(Config):
    """Development configuration with debug features"""
    DEBUG = True
    DEVELOPMENT = True
    WTF_CSRF_ENABLED = False  # Disable CSRF for easier development
    SESSION_COOKIE_SECURE = False
    MAIL_SUPPRESS_SEND = True  # Don't send emails in development
    
    # Development database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'sqlite:///sakina_attendance_dev.db'
    
    # Development logging
    LOG_LEVEL = 'DEBUG'
    
    # Cache disabled in development
    CACHE_TYPE = "NullCache"

class ProductionConfig(Config):
    """Production configuration with enhanced security and performance"""
    DEBUG = False
    TESTING = False
    
    # Production database (PostgreSQL recommended)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///sakina_attendance.db'
    
    # Enhanced security for production
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    WTF_CSRF_ENABLED = True
    
    # Force HTTPS
    PREFERRED_URL_SCHEME = 'https'
    
    # Production logging
    LOG_LEVEL = 'INFO'
    
    # Email enabled in production
    MAIL_SUPPRESS_SEND = False
    
    # Cache configuration for production
    CACHE_TYPE = "RedisCache"
    CACHE_REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379')
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # Log to stderr in production
        import logging
        from logging import StreamHandler
        file_handler = StreamHandler()
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        
        # Send error emails to admins
        if os.environ.get('ADMIN_EMAIL'):
            import logging
            from logging.handlers import SMTPHandler
            credentials = None
            secure = None
            if os.environ.get('MAIL_USERNAME') or os.environ.get('MAIL_PASSWORD'):
                credentials = (os.environ.get('MAIL_USERNAME'),
                              os.environ.get('MAIL_PASSWORD'))
                if os.environ.get('MAIL_USE_TLS'):
                    secure = ()
            mail_handler = SMTPHandler(
                mailhost=(os.environ.get('MAIL_SERVER', 'localhost'), 587),
                fromaddr='noreply@sakinagas.com',
                toaddrs=[os.environ.get('ADMIN_EMAIL')],
                subject='Sakina Gas Attendance System Error',
                credentials=credentials,
                secure=secure)
            mail_handler.setLevel(logging.ERROR)
            app.logger.addHandler(mail_handler)

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    MAIL_SUPPRESS_SEND = True
    
    # Fast password hashing for tests
    BCRYPT_LOG_ROUNDS = 4
    
    # Disable cache for tests
    CACHE_TYPE = "NullCache"

class StagingConfig(Config):
    """Staging configuration for testing in production-like environment"""
    DEBUG = False
    TESTING = False
    
    # Staging database
    SQLALCHEMY_DATABASE_URI = os.environ.get('STAGING_DATABASE_URL') or \
        'sqlite:///sakina_attendance_staging.db'
    
    # Moderate security (not full production)
    SESSION_COOKIE_SECURE = False
    WTF_CSRF_ENABLED = True
    
    # Email testing
    MAIL_SUPPRESS_SEND = True
    
    # Debug logging
    LOG_LEVEL = 'DEBUG'

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'staging': StagingConfig,
    'default': DevelopmentConfig
}

def get_config(config_name=None):
    """Get configuration class by name"""
    if config_name is None:
        config_name = os.environ.get('FLASK_CONFIG', 'default')
    return config.get(config_name, DevelopmentConfig)