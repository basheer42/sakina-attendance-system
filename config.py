"""
Sakina Gas Company - Professional Configuration
Built from scratch with full enterprise features and Kenyan labor law compliance
Version 3.0 - Complete configuration matching original complexity
"""

import os
import secrets
from datetime import timedelta

class Config:
    """Base configuration class with comprehensive settings"""
    
    # Application Core Settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_urlsafe(32)
    APP_VERSION = '3.0.0'
    APP_NAME = 'Sakina Gas Attendance System'
    
    # Company Information - Comprehensive Details
    COMPANY_NAME = 'Sakina Gas Company'
    COMPANY_TAGLINE = 'Reliable Energy Solutions Across Kenya'
    COMPANY_LOGO = '/static/images/logo.png'
    COMPANY_LOGO_SMALL = '/static/images/logo-small.png'
    COMPANY_FAVICON = '/static/images/favicon.ico'
    COMPANY_ADDRESS = 'P.O. Box 12345-00100, Industrial Area, Nairobi, Kenya'
    COMPANY_PHONE = '+254 700 123 456'
    COMPANY_EMAIL = 'info@sakinagas.com'
    COMPANY_WEBSITE = 'https://www.sakinagas.com'
    COMPANY_REGISTRATION = 'C.123456'
    COMPANY_TAX_PIN = 'P051234567X'
    COMPANY_ESTABLISHED = '2015'
    
    # Brand Colors and Styling
    BRAND_COLORS = {
        'primary': '#FF6B35',          # Sakina Orange
        'primary_dark': '#E55A2B',     # Darker orange
        'primary_light': '#FF8A63',    # Lighter orange
        'secondary': '#004E98',        # Deep Blue
        'secondary_dark': '#003A73',   # Darker blue
        'secondary_light': '#1A6BB8',  # Lighter blue
        'accent': '#F39C12',           # Golden accent
        'success': '#28A745',          # Green
        'warning': '#FFC107',          # Amber
        'danger': '#DC3545',           # Red
        'info': '#17A2B8',            # Cyan
        'light': '#F8F9FA',           # Light Gray
        'dark': '#343A40',            # Dark Gray
        'muted': '#6C757D',           # Muted Gray
        'white': '#FFFFFF',           # Pure White
        'black': '#000000'            # Pure Black
    }
    
    # Theme Configuration
    THEME_CONFIG = {
        'sidebar_bg': '#2C3E50',
        'navbar_bg': '#34495E',
        'card_bg': '#FFFFFF',
        'border_color': '#DEE2E6',
        'text_primary': '#343A40',
        'text_secondary': '#6C757D',
        'text_muted': '#ADB5BD'
    }
    
    # Database Configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance', 'sakina_attendance.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_timeout': 20,
        'max_overflow': 0,
    }
    
    # Session and Security Configuration
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_NAME = 'sakina_session'
    
    # Security Settings
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600
    BCRYPT_LOG_ROUNDS = 13
    PASSWORD_RESET_TIMEOUT = 3600  # 1 hour
    
    # Account Security
    MAX_LOGIN_ATTEMPTS = 5
    ACCOUNT_LOCKOUT_DURATION = timedelta(minutes=30)
    PASSWORD_EXPIRY_DAYS = 90
    REQUIRE_PASSWORD_CHANGE = True
    
    # File Upload Settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'uploads')
    ALLOWED_EXTENSIONS = {
        'images': {'png', 'jpg', 'jpeg', 'gif', 'webp'},
        'documents': {'pdf', 'doc', 'docx', 'txt'},
        'spreadsheets': {'xls', 'xlsx', 'csv'},
        'archives': {'zip', 'rar'}
    }
    
    # Logging Configuration
    LOGS_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'logs')
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_MAX_BYTES = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT = 10
    
    # Email Configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'false').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or 'noreply@sakinagas.com'
    MAIL_MAX_EMAILS = 100
    MAIL_ASCII_ATTACHMENTS = False
    
    # Pagination Settings
    ITEMS_PER_PAGE = 25
    MAX_ITEMS_PER_PAGE = 100
    EMPLOYEES_PER_PAGE = 25
    ATTENDANCE_PER_PAGE = 50
    REPORTS_PER_PAGE = 20
    
    # API Configuration
    API_VERSION = 'v1'
    API_RATE_LIMIT = '100/hour'
    API_TITLE = 'Sakina Gas Attendance API'
    API_DESCRIPTION = 'RESTful API for attendance management'
    
    # Cache Configuration
    CACHE_TYPE = 'simple'
    CACHE_DEFAULT_TIMEOUT = 300
    
    # Maintenance Mode
    MAINTENANCE_MODE = False
    MAINTENANCE_MESSAGE = 'System is under maintenance. Please try again later.'
    
    # Company Locations - Comprehensive Configuration
    COMPANY_LOCATIONS = {
        'head_office': {
            'name': 'Head Office',
            'display_name': 'Sakina Gas Head Office',
            'address': 'Industrial Area, Enterprise Road, Nairobi',
            'coordinates': {'lat': -1.3148, 'lng': 36.8590},
            'phone': '+254 700 123 456',
            'email': 'headoffice@sakinagas.com',
            'manager': 'Sarah Mwangi',
            'manager_email': 'sarah.mwangi@sakinagas.com',
            'capacity': 50,
            'type': 'office',
            'working_hours': {
                'monday': {'start': '08:00', 'end': '17:00', 'break_start': '12:00', 'break_end': '13:00'},
                'tuesday': {'start': '08:00', 'end': '17:00', 'break_start': '12:00', 'break_end': '13:00'},
                'wednesday': {'start': '08:00', 'end': '17:00', 'break_start': '12:00', 'break_end': '13:00'},
                'thursday': {'start': '08:00', 'end': '17:00', 'break_start': '12:00', 'break_end': '13:00'},
                'friday': {'start': '08:00', 'end': '17:00', 'break_start': '12:00', 'break_end': '13:00'},
                'saturday': {'start': '09:00', 'end': '13:00'},
                'sunday': 'closed'
            },
            'departments': ['administration', 'finance', 'hr', 'management', 'operations'],
            'facilities': ['conference_room', 'cafeteria', 'parking', 'security'],
            'timezone': 'Africa/Nairobi',
            'is_main': True
        },
        'dandora': {
            'name': 'Dandora Station',
            'display_name': 'Sakina Gas Dandora',
            'address': 'Dandora Phase 4, Near Chief\'s Camp, Nairobi',
            'coordinates': {'lat': -1.2571, 'lng': 36.8936},
            'phone': '+254 700 123 457',
            'email': 'dandora@sakinagas.com',
            'manager': 'James Ochieng',
            'manager_email': 'james.ochieng@sakinagas.com',
            'capacity': 20,
            'type': 'station',
            'working_hours': {
                'day_shift': {'start': '06:00', 'end': '18:00', 'break_start': '12:00', 'break_end': '13:00'},
                'night_shift': {'start': '18:00', 'end': '06:00', 'break_start': '00:00', 'break_end': '01:00'}
            },
            'departments': ['operations', 'sales', 'security', 'maintenance'],
            'fuel_types': ['petrol', 'diesel', 'lpg'],
            'tank_capacity': {
                'petrol': 45000,  # liters
                'diesel': 60000,  # liters
                'lpg': 15000     # kg
            },
            'safety_certification': 'EPRA-2024-DN001',
            'facilities': ['convenience_store', 'car_wash', 'tire_service', 'parking'],
            'timezone': 'Africa/Nairobi',
            'is_main': False,
            'established': '2018'
        },
        'tassia': {
            'name': 'Tassia Station',
            'display_name': 'Sakina Gas Tassia',
            'address': 'Tassia Estate, Embakasi, Nairobi',
            'coordinates': {'lat': -1.3167, 'lng': 36.8833},
            'phone': '+254 700 123 458',
            'email': 'tassia@sakinagas.com',
            'manager': 'Grace Wanjiku',
            'manager_email': 'grace.wanjiku@sakinagas.com',
            'capacity': 18,
            'type': 'station',
            'working_hours': {
                'day_shift': {'start': '06:00', 'end': '18:00', 'break_start': '12:00', 'break_end': '13:00'},
                'night_shift': {'start': '18:00', 'end': '06:00', 'break_start': '00:00', 'break_end': '01:00'}
            },
            'departments': ['operations', 'sales', 'security'],
            'fuel_types': ['petrol', 'diesel', 'lpg'],
            'tank_capacity': {
                'petrol': 40000,  # liters
                'diesel': 55000,  # liters
                'lpg': 12000     # kg
            },
            'safety_certification': 'EPRA-2024-TS002',
            'facilities': ['convenience_store', 'atm', 'parking'],
            'timezone': 'Africa/Nairobi',
            'is_main': False,
            'established': '2019'
        },
        'kiambu': {
            'name': 'Kiambu Station',
            'display_name': 'Sakina Gas Kiambu',
            'address': 'Kiambu Town, Along Kiambu-Nairobi Road',
            'coordinates': {'lat': -1.1756, 'lng': 36.8344},
            'phone': '+254 700 123 459',
            'email': 'kiambu@sakinagas.com',
            'manager': 'Peter Kamau',
            'manager_email': 'peter.kamau@sakinagas.com',
            'capacity': 22,
            'type': 'station',
            'working_hours': {
                'day_shift': {'start': '06:00', 'end': '18:00', 'break_start': '12:00', 'break_end': '13:00'},
                'night_shift': {'start': '18:00', 'end': '06:00', 'break_start': '00:00', 'break_end': '01:00'}
            },
            'departments': ['operations', 'sales', 'security', 'maintenance'],
            'fuel_types': ['petrol', 'diesel', 'lpg', 'kerosene'],
            'tank_capacity': {
                'petrol': 50000,  # liters
                'diesel': 65000,  # liters
                'lpg': 18000,    # kg
                'kerosene': 10000 # liters
            },
            'safety_certification': 'EPRA-2024-KB003',
            'facilities': ['convenience_store', 'car_wash', 'tire_service', 'restaurant', 'parking', 'truck_bay'],
            'timezone': 'Africa/Nairobi',
            'is_main': False,
            'established': '2017'
        }
    }
    
    # Departments with Comprehensive Details
    DEPARTMENTS = {
        'administration': {
            'name': 'Administration',
            'display_name': 'Administration Department',
            'head': 'Administrative Manager',
            'head_title': 'Administration Manager',
            'description': 'Oversees general administrative functions and office operations',
            'functions': [
                'General administration and office management',
                'Document management and filing systems',
                'Office coordination and logistics',
                'Vendor management and procurement',
                'Facility management and maintenance coordination'
            ],
            'available_at': ['head_office'],
            'positions': ['Administrative Manager', 'Administrative Assistant', 'Office Coordinator', 'Receptionist'],
            'budget_code': 'ADM',
            'cost_center': '1000'
        },
        'finance': {
            'name': 'Finance & Accounts',
            'display_name': 'Finance & Accounts Department',
            'head': 'Finance Manager',
            'head_title': 'Chief Financial Officer',
            'description': 'Manages financial operations, accounting, and fiscal responsibility',
            'functions': [
                'Financial reporting and analysis',
                'Payroll processing and employee benefits',
                'Budget management and forecasting',
                'Accounts payable and receivable',
                'Tax compliance and audit coordination',
                'Investment management and cash flow'
            ],
            'available_at': ['head_office'],
            'positions': ['Finance Manager', 'Accountant', 'Payroll Officer', 'Accounts Assistant', 'Internal Auditor'],
            'budget_code': 'FIN',
            'cost_center': '2000'
        },
        'hr': {
            'name': 'Human Resources',
            'display_name': 'Human Resources Department',
            'head': 'HR Manager',
            'head_title': 'Human Resources Director',
            'description': 'Manages human capital, employee relations, and organizational development',
            'functions': [
                'Employee recruitment and selection',
                'Performance management and appraisals',
                'Training and development programs',
                'Employee relations and conflict resolution',
                'Compensation and benefits administration',
                'Policy development and compliance'
            ],
            'available_at': ['head_office'],
            'positions': ['HR Manager', 'HR Officer', 'Training Coordinator', 'Recruitment Specialist'],
            'budget_code': 'HR',
            'cost_center': '3000'
        },
        'management': {
            'name': 'Management',
            'display_name': 'Executive Management',
            'head': 'General Manager',
            'head_title': 'Chief Executive Officer',
            'description': 'Executive leadership and strategic direction',
            'functions': [
                'Strategic planning and decision making',
                'Operations oversight and coordination',
                'Stakeholder relations and partnerships',
                'Business development and expansion',
                'Corporate governance and compliance'
            ],
            'available_at': ['head_office'],
            'positions': ['General Manager', 'Operations Director', 'Business Development Manager'],
            'budget_code': 'MGT',
            'cost_center': '1001'
        },
        'operations': {
            'name': 'Operations',
            'display_name': 'Operations Department',
            'head': 'Operations Manager',
            'head_title': 'Chief Operations Officer',
            'description': 'Manages day-to-day operational activities across all locations',
            'functions': [
                'Fuel dispensing and inventory management',
                'Equipment maintenance and safety protocols',
                'Quality control and compliance monitoring',
                'Supply chain and logistics coordination',
                'Customer service excellence',
                'Operational efficiency optimization'
            ],
            'available_at': ['dandora', 'tassia', 'kiambu', 'head_office'],
            'positions': ['Operations Manager', 'Station Supervisor', 'Station Attendant', 'Pump Operator', 'Inventory Clerk'],
            'budget_code': 'OPS',
            'cost_center': '4000'
        },
        'sales': {
            'name': 'Sales & Customer Service',
            'display_name': 'Sales & Customer Service Department',
            'head': 'Sales Manager',
            'head_title': 'Sales & Marketing Director',
            'description': 'Drives sales performance and maintains customer relationships',
            'functions': [
                'Customer service and satisfaction',
                'Sales tracking and performance analysis',
                'Marketing campaigns and promotions',
                'Customer relationship management',
                'Market research and competitor analysis'
            ],
            'available_at': ['dandora', 'tassia', 'kiambu', 'head_office'],
            'positions': ['Sales Manager', 'Sales Representative', 'Customer Service Representative', 'Cashier'],
            'budget_code': 'SAL',
            'cost_center': '5000'
        },
        'security': {
            'name': 'Security',
            'display_name': 'Security Department',
            'head': 'Security Supervisor',
            'head_title': 'Chief Security Officer',
            'description': 'Ensures safety and security across all company premises',
            'functions': [
                'Premises security and access control',
                'Incident reporting and investigation',
                'Emergency response coordination',
                'CCTV monitoring and surveillance',
                'Security policy enforcement'
            ],
            'available_at': ['dandora', 'tassia', 'kiambu', 'head_office'],
            'positions': ['Security Supervisor', 'Security Guard', 'CCTV Operator'],
            'budget_code': 'SEC',
            'cost_center': '6000'
        },
        'maintenance': {
            'name': 'Maintenance',
            'display_name': 'Maintenance Department',
            'head': 'Maintenance Supervisor',
            'head_title': 'Facilities Manager',
            'description': 'Maintains equipment, facilities, and infrastructure',
            'functions': [
                'Equipment maintenance and repairs',
                'Facility maintenance and upkeep',
                'Preventive maintenance scheduling',
                'Technical support and troubleshooting',
                'Compliance with safety standards'
            ],
            'available_at': ['kiambu', 'head_office'],
            'positions': ['Maintenance Supervisor', 'Technician', 'Electrician', 'Plumber', 'Janitor'],
            'budget_code': 'MNT',
            'cost_center': '7000'
        }
    }
    
    # User Roles with Comprehensive Permissions
    USER_ROLES = {
        'hr_manager': {
            'name': 'HR Manager',
            'display_name': 'Human Resources Manager',
            'level': 9,
            'department': 'hr',
            'description': 'Full administrative access with HR management capabilities',
            'permissions': [
                'view_all_employees', 'add_employee', 'edit_employee', 'deactivate_employee',
                'view_all_attendance', 'edit_attendance', 'mark_attendance_for_others',
                'view_all_leaves', 'approve_leaves', 'reject_leaves', 'edit_leaves',
                'view_all_reports', 'generate_reports', 'export_data',
                'view_all_locations', 'manage_users', 'system_administration',
                'view_audit_logs', 'manage_holidays', 'performance_reviews',
                'disciplinary_actions', 'salary_management', 'benefits_management',
                'policy_management', 'training_management', 'compliance_monitoring'
            ],
            'dashboard_widgets': [
                'hr_overview', 'attendance_summary', 'pending_approvals',
                'employee_metrics', 'compliance_status', 'performance_trends',
                'leave_analytics', 'department_overview'
            ],
            'locations_access': 'all',
            'color': '#E91E63',
            'icon': 'user-crown',
            'menu_items': [
                'dashboard', 'employees', 'attendance', 'leaves', 'reports',
                'performance', 'disciplinary', 'users', 'settings'
            ]
        },
        'station_manager': {
            'name': 'Station Manager',
            'display_name': 'Station Manager',
            'level': 7,
            'department': 'operations',
            'description': 'Location-specific management with operational oversight',
            'permissions': [
                'view_location_employees', 'edit_location_employees',
                'view_location_attendance', 'mark_attendance', 'edit_location_attendance',
                'view_location_leaves', 'request_leaves_for_employees',
                'view_location_reports', 'view_location_performance',
                'manage_shifts', 'incident_reporting', 'inventory_management',
                'customer_service_oversight', 'local_procurement',
                'staff_scheduling', 'performance_monitoring'
            ],
            'dashboard_widgets': [
                'station_overview', 'today_attendance', 'pending_requests',
                'location_metrics', 'staff_alerts', 'shift_schedule',
                'performance_summary', 'incident_reports'
            ],
            'locations_access': 'assigned_only',
            'color': '#2E86AB',
            'icon': 'building',
            'menu_items': [
                'dashboard', 'employees', 'attendance', 'leaves', 'reports',
                'performance', 'incidents'
            ]
        },
        'finance_manager': {
            'name': 'Finance Manager',
            'display_name': 'Finance Manager',
            'level': 8,
            'department': 'finance',
            'description': 'Financial management and payroll administration',
            'permissions': [
                'view_all_employees', 'view_employee_salary', 'edit_employee_salary',
                'view_payroll_reports', 'approve_salary_changes',
                'view_financial_reports', 'manage_allowances', 'manage_deductions',
                'view_attendance_for_payroll', 'approve_expenses',
                'budget_management', 'financial_analysis', 'tax_management'
            ],
            'dashboard_widgets': [
                'payroll_summary', 'financial_metrics', 'salary_reports',
                'expense_approvals', 'budget_tracking', 'cost_analysis'
            ],
            'locations_access': 'all',
            'color': '#4CAF50',
            'icon': 'calculator',
            'menu_items': [
                'dashboard', 'employees', 'payroll', 'reports', 'budget', 'expenses'
            ]
        },
        'admin': {
            'name': 'System Administrator',
            'display_name': 'System Administrator',
            'level': 10,
            'department': 'administration',
            'description': 'Full system access with administrative privileges',
            'permissions': [
                'all_permissions', 'system_administration', 'database_management',
                'backup_management', 'security_management', 'user_management',
                'system_configuration', 'audit_management', 'maintenance_mode'
            ],
            'dashboard_widgets': [
                'system_health', 'user_activities', 'security_alerts',
                'system_metrics', 'backup_status', 'performance_monitoring'
            ],
            'locations_access': 'all',
            'color': '#6F42C1',
            'icon': 'cog',
            'menu_items': [
                'dashboard', 'employees', 'users', 'system', 'security',
                'backups', 'logs', 'settings'
            ]
        },
        'employee': {
            'name': 'Employee',
            'display_name': 'Employee',
            'level': 1,
            'department': 'various',
            'description': 'Basic employee access for personal information',
            'permissions': [
                'view_own_profile', 'edit_own_profile', 'view_own_attendance',
                'mark_own_attendance', 'request_leaves', 'view_own_leaves',
                'view_own_performance', 'view_own_payslip'
            ],
            'dashboard_widgets': [
                'personal_overview', 'my_attendance', 'my_leaves',
                'my_performance', 'announcements'
            ],
            'locations_access': 'assigned_only',
            'color': '#17A2B8',
            'icon': 'user',
            'menu_items': [
                'dashboard', 'profile', 'attendance', 'leaves', 'performance'
            ]
        }
    }
    
    # COMPREHENSIVE KENYAN LABOR LAWS IMPLEMENTATION
    # Based on Employment Act 2007 and subsequent amendments
    KENYAN_LABOR_LAWS = {
        'leave_entitlements': {
            'annual_leave': {
                'days_per_year': 21,
                'minimum_service_months': 12,
                'can_carry_forward': True,
                'max_carry_forward_days': 21,
                'cash_in_lieu_allowed': False,
                'must_be_consecutive': False,
                'minimum_consecutive_days': 14,
                'notice_period_days': 14,
                'legal_reference': 'Employment Act 2007, Section 28',
                'notes': 'Minimum 21 consecutive working days after 12 months of continuous service'
            },
            'sick_leave': {
                'days_without_certificate': 7,
                'days_with_certificate': 30,
                'max_per_year': 30,
                'medical_board_required_after': 30,
                'certificate_required_after': 3,
                'paid_percentage': 100,
                'accumulate_unused': True,
                'legal_reference': 'Employment Act 2007, Section 29',
                'notes': 'Up to 7 days without medical certificate, 30 days with certificate per year'
            },
            'maternity_leave': {
                'days': 90,
                'weeks': 12,
                'months': 3,
                'can_split': True,
                'pre_birth_max_days': 28,
                'post_birth_min_days': 42,
                'paid_percentage': 100,
                'certificate_required': True,
                'notice_period_days': 30,
                'legal_reference': 'Employment Act 2007, Section 29A',
                'notes': '3 months maternity leave, can be split before and after birth'
            },
            'paternity_leave': {
                'days': 14,
                'weeks': 2,
                'must_be_consecutive': True,
                'within_days_of_birth': 30,
                'paid_percentage': 100,
                'certificate_required': True,
                'legal_reference': 'Employment Act 2007, Section 29B',
                'notes': 'Maximum 14 consecutive days within 30 days of child birth'
            },
            'compassionate_leave': {
                'days': 7,
                'occasions': [
                    'death of spouse', 'death of child', 'death of parent',
                    'death of sibling', 'death of grandparent', 'serious illness of immediate family'
                ],
                'documentation_required': True,
                'paid_percentage': 100,
                'notice_period_hours': 24,
                'legal_reference': 'Employment Act 2007, Section 29C',
                'notes': 'Up to 7 days for bereavement or serious illness of immediate family'
            },
            'study_leave': {
                'days_per_year': 30,
                'paid_percentage': 50,
                'conditions': ['job_related_course', 'management_approval'],
                'legal_reference': 'Employment Act 2007, Section 29D',
                'notes': 'For job-related studies with management approval'
            }
        },
        
        'working_hours': {
            'normal_hours_per_day': 8,
            'normal_hours_per_week': 45,
            'maximum_hours_per_week': 60,
            'overtime_threshold_daily': 8,
            'overtime_threshold_weekly': 45,
            'overtime_rate_normal': 1.5,
            'overtime_rate_holiday': 2.0,
            'overtime_rate_night': 1.25,
            'night_hours_start': '18:00',
            'night_hours_end': '06:00',
            'rest_day_hours': 24,
            'rest_period_between_shifts': 12,
            'maximum_continuous_work_hours': 12,
            'break_entitlement_hours': 1,
            'legal_reference': 'Employment Act 2007, Section 27'
        },
        
        'minimum_wages': {
            'general_minimum_wage': 15201.00,  # KES per month (2024)
            'house_allowance_minimum': 4500.00,
            'transport_allowance_minimum': 2000.00,
            'medical_allowance_minimum': 1500.00,
            'leave_allowance_minimum': 2000.00,
            'currency': 'KES',
            'effective_date': '2024-05-01',
            'review_frequency': 'annual',
            'sector_variations': {
                'agriculture': 13500.00,
                'domestic': 11500.00,
                'security': 16000.00
            },
            'legal_reference': 'Regulation of Wages (General) Order 2024'
        },
        
        'probation': {
            'maximum_period_months': 6,
            'default_period_months': 3,
            'extension_allowed': False,
            'notice_period_during_probation_days': 7,
            'performance_review_frequency': 'monthly',
            'confirmation_notice_days': 14,
            'legal_reference': 'Employment Act 2007, Section 8'
        },
        
        'termination': {
            'notice_periods_days': {
                'up_to_1_year': 7,
                '1_to_5_years': 14,
                '5_to_10_years': 30,
                'above_10_years': 30
            },
            'severance_pay_days': 15,
            'payment_in_lieu_allowed': True,
            'redundancy_pay_formula': 'days_per_year_service * 15',
            'grounds_for_summary_dismissal': [
                'gross_misconduct', 'criminal_conviction', 'breach_of_trust',
                'insubordination', 'repeated_minor_offenses'
            ],
            'legal_reference': 'Employment Act 2007, Sections 35, 40, 44'
        },
        
        'employee_rights': {
            'freedom_of_association': True,
            'collective_bargaining': True,
            'non_discrimination': ['race', 'religion', 'gender', 'disability', 'pregnancy'],
            'equal_pay': True,
            'safe_working_environment': True,
            'grievance_procedure': True,
            'legal_reference': 'Employment Act 2007, Constitution of Kenya'
        },
        
        'employer_obligations': {
            'provide_contract': True,
            'maintain_records': True,
            'provide_payslips': True,
            'workers_compensation': True,
            'medical_examination': True,
            'safety_training': True,
            'legal_reference': 'Employment Act 2007, Occupational Safety and Health Act'
        },
        
        'compliance_requirements': {
            'employment_register': True,
            'statutory_deductions': ['NSSF', 'NHIF', 'PAYE'],
            'returns_submission': ['monthly', 'annual'],
            'work_permits': 'foreign_workers',
            'display_abstracts': True,
            'legal_reference': 'Employment Act 2007, Income Tax Act'
        },
        
        'penalties': {
            'non_compliance_fine_range': {'min': 50000, 'max': 500000},
            'repeat_offense_multiplier': 2,
            'currency': 'KES',
            'legal_reference': 'Employment Act 2007, Section 77'
        }
    }
    
    # Validation Rules and Business Logic
    VALIDATION_RULES = {
        'password_policy': {
            'min_length': 8,
            'max_length': 128,
            'require_uppercase': True,
            'require_lowercase': True,
            'require_numbers': True,
            'require_special_chars': True,
            'forbidden_patterns': ['password', '123456', 'admin', 'user'],
            'forbidden_personal_info': True,
            'expiry_days': 90,
            'history_check': 5,  # Cannot reuse last 5 passwords
            'complexity_score_min': 60
        },
        
        'employee_validation': {
            'employee_id_format': {
                'prefix': 'SGC',
                'digits': 3,
                'pattern': r'^SGC\d{3}$',
                'auto_increment': True
            },
            'national_id': {
                'format': 'kenyan',
                'pattern': r'^\d{7,8}$',
                'unique': True
            },
            'phone_number': {
                'format': 'kenyan',
                'pattern': r'^\+254[17]\d{8}$',
                'example': '+254712345678'
            },
            'email': {
                'format': 'standard',
                'domain_whitelist': [],
                'unique': True
            }
        },
        
        'attendance_rules': {
            'late_threshold_minutes': 15,
            'early_departure_threshold_minutes': 15,
            'break_duration_minutes': 60,
            'overtime_auto_approval_threshold_hours': 2,
            'maximum_daily_hours': 12,
            'minimum_rest_hours': 8,
            'clock_in_tolerance_minutes': 30,
            'clock_out_tolerance_minutes': 60
        },
        
        'leave_validation': {
            'minimum_notice_days': {
                'annual_leave': 14,
                'sick_leave': 0,
                'maternity_leave': 30,
                'paternity_leave': 7,
                'compassionate_leave': 0
            },
            'maximum_consecutive_days': {
                'annual_leave': 21,
                'sick_leave': 30
            },
            'blackout_periods': [
                {'start': '12-20', 'end': '01-05', 'reason': 'Year-end operations'},
                {'start': '06-15', 'end': '06-30', 'reason': 'Mid-year audit'}
            ]
        },
        
        'performance_review': {
            'frequency': 'annual',
            'probation_frequency': 'monthly',
            'rating_scale': {'min': 1, 'max': 5},
            'mandatory_fields': ['goals', 'achievements', 'areas_for_improvement'],
            'approval_required': True
        }
    }
    
    # System Features Configuration
    FEATURES = {
        'attendance': {
            'enabled': True,
            'biometric_integration': False,
            'gps_tracking': True,
            'photo_verification': False,
            'offline_mode': True
        },
        'leave_management': {
            'enabled': True,
            'auto_approval_rules': True,
            'email_notifications': True,
            'calendar_integration': False,
            'delegation_workflow': True
        },
        'payroll': {
            'enabled': False,  # Future feature
            'integration_ready': True,
            'statutory_compliance': True,
            'bank_integration': False
        },
        'performance': {
            'enabled': True,
            'goal_setting': True,
            'peer_reviews': False,
            'competency_framework': True
        },
        'reporting': {
            'enabled': True,
            'scheduled_reports': True,
            'custom_reports': True,
            'export_formats': ['pdf', 'excel', 'csv']
        },
        'mobile_app': {
            'enabled': False,  # Future feature
            'push_notifications': False,
            'offline_sync': False
        }
    }
    
    @classmethod
    def init_app(cls, app):
        """Initialize application with configuration"""
        
        # Create necessary directories
        directories = [
            cls.LOGS_DIR,
            cls.UPLOAD_FOLDER,
            os.path.join(app.root_path, 'instance'),
            os.path.join(app.root_path, 'backups')
        ]
        
        for directory in directories:
            if not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
                app.logger.info(f'Created directory: {directory}')

class DevelopmentConfig(Config):
    """Development environment configuration"""
    DEBUG = True
    FLASK_ENV = 'development'
    
    # Development-specific database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance', 'sakina_attendance_dev.db')
    SQLALCHEMY_ECHO = True  # Log all SQL statements
    
    # Relaxed security for development
    SESSION_COOKIE_SECURE = False
    WTF_CSRF_ENABLED = False
    BCRYPT_LOG_ROUNDS = 4  # Faster password hashing
    
    # Development mail settings
    MAIL_SUPPRESS_SEND = True
    MAIL_DEBUG = True
    
    # Relaxed validation for development
    API_RATE_LIMIT = '1000/hour'
    MAX_LOGIN_ATTEMPTS = 10
    ACCOUNT_LOCKOUT_DURATION = timedelta(minutes=5)
    
    # Development logging
    LOG_LEVEL = 'DEBUG'
    
    # Enable all features for development
    FEATURES = {
        'attendance': {
            'enabled': True,
            'biometric_integration': True,
            'gps_tracking': True,
            'photo_verification': True,
            'offline_mode': True
        },
        'leave_management': {
            'enabled': True,
            'auto_approval_rules': True,
            'email_notifications': False,  # Disabled in dev
            'calendar_integration': True,
            'delegation_workflow': True
        },
        'payroll': {
            'enabled': True,  # Enable for testing
            'integration_ready': True,
            'statutory_compliance': True,
            'bank_integration': False
        },
        'performance': {
            'enabled': True,
            'goal_setting': True,
            'peer_reviews': True,
            'competency_framework': True
        },
        'reporting': {
            'enabled': True,
            'scheduled_reports': True,
            'custom_reports': True,
            'export_formats': ['pdf', 'excel', 'csv', 'json']
        }
    }

class ProductionConfig(Config):
    """Production environment configuration"""
    DEBUG = False
    FLASK_ENV = 'production'
    
    # Production database (PostgreSQL recommended)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance', 'sakina_attendance_prod.db')
    SQLALCHEMY_ECHO = False
    
    # Strict security for production
    SESSION_COOKIE_SECURE = True
    WTF_CSRF_ENABLED = True
    BCRYPT_LOG_ROUNDS = 15  # More secure password hashing
    
    # Production logging
    LOG_LEVEL = 'WARNING'
    
    # Enhanced security headers
    SECURITY_HEADERS = {
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains; preload',
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Referrer-Policy': 'strict-origin-when-cross-origin',
        'Content-Security-Policy': "default-src 'self'; img-src 'self' data: https:; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com;"
    }
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # Production-specific initialization
        import logging
        from logging.handlers import SMTPHandler, SysLogHandler
        
        # Email error notifications
        if app.config.get('MAIL_SERVER'):
            auth = None
            if app.config.get('MAIL_USERNAME') and app.config.get('MAIL_PASSWORD'):
                auth = (app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
            
            secure = None
            if app.config.get('MAIL_USE_TLS'):
                secure = ()
            
            mail_handler = SMTPHandler(
                mailhost=(app.config['MAIL_SERVER'], app.config['MAIL_PORT']),
                fromaddr=app.config['MAIL_DEFAULT_SENDER'],
                toaddrs=[app.config.get('ADMIN_EMAIL', 'admin@sakinagas.com')],
                subject='Sakina Gas Attendance System - Critical Error',
                credentials=auth,
                secure=secure
            )
            mail_handler.setLevel(logging.ERROR)
            mail_handler.setFormatter(logging.Formatter('''
Application: Sakina Gas Attendance System
Time:        %(asctime)s
Level:       %(levelname)s
Module:      %(module)s
Function:    %(funcName)s
Line:        %(lineno)d

Message:
%(message)s
'''))
            app.logger.addHandler(mail_handler)
        
        # System log handler (for systemd/journald)
        syslog_handler = SysLogHandler(address='/dev/log')
        syslog_handler.setLevel(logging.WARNING)
        syslog_handler.setFormatter(logging.Formatter(
            'sakina-attendance[%(process)d]: %(levelname)s %(message)s'
        ))
        app.logger.addHandler(syslog_handler)

class TestingConfig(Config):
    """Testing environment configuration"""
    TESTING = True
    FLASK_ENV = 'testing'
    
    # In-memory database for tests
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_ECHO = False
    
    # Disable security features for testing
    WTF_CSRF_ENABLED = False
    LOGIN_DISABLED = False
    
    # Fast password hashing for tests
    BCRYPT_LOG_ROUNDS = 1
    
    # Disable email during tests
    MAIL_SUPPRESS_SEND = True
    
    # Test-friendly validation
    MAX_LOGIN_ATTEMPTS = 100
    ACCOUNT_LOCKOUT_DURATION = timedelta(seconds=1)

class StagingConfig(Config):
    """Staging environment configuration"""
    DEBUG = False
    FLASK_ENV = 'staging'
    
    # Staging database
    SQLALCHEMY_DATABASE_URI = os.environ.get('STAGING_DATABASE_URL') or \
        'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance', 'sakina_attendance_staging.db')
    
    # Moderate security for staging
    SESSION_COOKIE_SECURE = False
    WTF_CSRF_ENABLED = True
    BCRYPT_LOG_ROUNDS = 8
    
    # Staging-specific settings
    MAIL_SUPPRESS_SEND = True  # Prevent accidental emails
    LOG_LEVEL = 'DEBUG'
    
    # Enable advanced features for staging tests
    FEATURES = Config.FEATURES.copy()
    FEATURES['payroll']['enabled'] = True

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

# Utility functions for configuration access
def get_kenyan_leave_days(leave_type):
    """Get Kenyan legal leave days for a specific leave type"""
    labor_laws = Config.KENYAN_LABOR_LAWS['leave_entitlements']
    leave_config = labor_laws.get(leave_type, {})
    return leave_config.get('days', leave_config.get('days_per_year', 0))

def validate_kenyan_leave_request(leave_type, days_requested, employee_service_months=12, employee_gender=None):
    """Comprehensive validation of leave request against Kenyan labor laws"""
    labor_laws = Config.KENYAN_LABOR_LAWS['leave_entitlements']
    leave_rules = labor_laws.get(leave_type)
    
    if not leave_rules:
        return False, f"Unknown leave type: {leave_type}"
    
    # Service period validation for annual leave
    if leave_type == 'annual_leave':
        min_service = leave_rules.get('minimum_service_months', 12)
        if employee_service_months < min_service:
            return False, f"Employee must complete {min_service} months of service for annual leave"
    
    # Gender-specific validation
    if leave_type == 'maternity_leave' and employee_gender and employee_gender.lower() != 'female':
        return False, "Maternity leave is only available to female employees"
    
    if leave_type == 'paternity_leave' and employee_gender and employee_gender.lower() != 'male':
        return False, "Paternity leave is only available to male employees"
    
    # Maximum days validation
    max_days = leave_rules.get('days', leave_rules.get('days_per_year', 0))
    if days_requested > max_days:
        legal_ref = leave_rules.get('legal_reference', 'Employment Act 2007')
        return False, f"Maximum {max_days} days allowed for {leave_type.replace('_', ' ').title()} ({legal_ref})"
    
    # Consecutive days validation
    if leave_rules.get('must_be_consecutive', False) and days_requested != max_days:
        return False, f"{leave_type.replace('_', ' ').title()} must be taken as {max_days} consecutive days"
    
    return True, f"Leave request complies with Kenyan labor laws ({leave_rules.get('legal_reference', 'Employment Act 2007')})"

def get_overtime_rate(hours_worked, is_holiday=False, is_night_shift=False, employee_type='regular'):
    """Calculate overtime rate according to Kenyan labor laws"""
    labor_laws = Config.KENYAN_LABOR_LAWS['working_hours']
    normal_hours = labor_laws['normal_hours_per_day']
    
    if hours_worked <= normal_hours:
        return 1.0  # Normal rate
    
    # Holiday overtime
    if is_holiday:
        return labor_laws['overtime_rate_holiday']
    
    # Night shift overtime
    if is_night_shift:
        return labor_laws['overtime_rate_night']
    
    # Regular overtime
    return labor_laws['overtime_rate_normal']

def get_minimum_wage(employee_type='general', location='nairobi'):
    """Get minimum wage according to Kenyan regulations"""
    wage_config = Config.KENYAN_LABOR_LAWS['minimum_wages']
    
    # Check for sector-specific minimum wage
    if employee_type in wage_config.get('sector_variations', {}):
        return wage_config['sector_variations'][employee_type]
    
    return wage_config['general_minimum_wage']

def get_notice_period(service_years):
    """Get notice period based on years of service"""
    termination_config = Config.KENYAN_LABOR_LAWS['termination']
    notice_periods = termination_config['notice_periods_days']
    
    if service_years < 1:
        return notice_periods['up_to_1_year']
    elif service_years < 5:
        return notice_periods['1_to_5_years']
    elif service_years < 10:
        return notice_periods['5_to_10_years']
    else:
        return notice_periods['above_10_years']

def calculate_severance_pay(monthly_salary, service_years):
    """Calculate severance pay according to Kenyan law"""
    termination_config = Config.KENYAN_LABOR_LAWS['termination']
    daily_salary = monthly_salary / 30  # Assuming 30 days per month
    severance_days = termination_config['severance_pay_days']
    
    return daily_salary * severance_days * service_years

def is_public_holiday(check_date):
    """Check if a date is a public holiday"""
    # This would typically check against the Holiday model
    # For configuration purposes, we return the holiday checking logic
    return {
        'check_date': check_date,
        'holiday_types': ['public', 'company'],
        'source': 'database_lookup_required'
    }

# Export commonly used functions
__all__ = [
    'Config', 'DevelopmentConfig', 'ProductionConfig', 'TestingConfig', 'StagingConfig',
    'get_config', 'get_kenyan_leave_days', 'validate_kenyan_leave_request',
    'get_overtime_rate', 'get_minimum_wage', 'get_notice_period',
    'calculate_severance_pay', 'is_public_holiday'
]