"""
Sakina Gas Company - Secure Configuration
This file contains sensitive data and should be added to .gitignore
RENAMED to avoid conflict with Python's built-in 'secrets' module
"""

import os
import secrets as python_secrets  # Renamed to avoid confusion

# Generate secure keys for production
SECRET_KEY = os.environ.get('SECRET_KEY') or python_secrets.token_urlsafe(32)

# Default user passwords (to be changed on first login)
DEFAULT_PASSWORDS = {
    'hr_manager': 'HRManager123!',
    'dandora_manager': 'Dandora456!',
    'tassia_manager': 'Tassia789!',
    'kiambu_manager': 'Kiambu012!'
}

# Database credentials (if using external database)
DATABASE_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'port': os.environ.get('DB_PORT', '5432'),
    'username': os.environ.get('DB_USERNAME', ''),
    'password': os.environ.get('DB_PASSWORD', ''),
    'database': os.environ.get('DB_NAME', 'sakina_attendance')
}

# Email configuration (for password reset, notifications)
EMAIL_CONFIG = {
    'smtp_server': os.environ.get('MAIL_SERVER', 'smtp.gmail.com'),
    'smtp_port': int(os.environ.get('MAIL_PORT', '587')),
    'username': os.environ.get('MAIL_USERNAME', ''),
    'password': os.environ.get('MAIL_PASSWORD', ''),
    'use_tls': os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'
}

# API Keys (if needed for external services)
API_KEYS = {
    'sms_service': os.environ.get('SMS_API_KEY', ''),
    'backup_service': os.environ.get('BACKUP_API_KEY', ''),
    'monitoring': os.environ.get('MONITORING_API_KEY', '')
}

# Security configuration
SECURITY_CONFIG = {
    'max_login_attempts': 5,
    'lockout_duration_minutes': 30,
    'session_timeout_hours': 8,
    'password_expiry_days': 90
}