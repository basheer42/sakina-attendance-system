"""
Sakina Gas Company - Secure Configuration
This file contains sensitive data and should be added to .gitignore
RENAMED to avoid conflict with Python's built-in 'secrets' module

IMPORTANT: Passwords have been standardized to match documentation.
All users use 'Manager123!' as the default password.
"""

import os
import secrets as python_secrets  # Renamed to avoid confusion

# Generate secure keys for production
SECRET_KEY = os.environ.get('SECRET_KEY') or python_secrets.token_urlsafe(32)

# Default user passwords (to be changed on first login)
# FIXED: Standardized to match README.md and setup_users.py documentation
DEFAULT_PASSWORDS = {
    'hr_manager': 'Manager123!',
    'dandora_manager': 'Manager123!',
    'tassia_manager': 'Manager123!',
    'kiambu_manager': 'Manager123!'
}

# Alternative passwords for production (uncomment to use unique passwords)
# These should be changed immediately after deployment
PRODUCTION_PASSWORDS = {
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

# Default password for all managers (for development/testing)
# This should be changed in production
SECURE_DEFAULT_PASSWORD = 'Manager123!'


def get_default_password(username):
    """
    Get the default password for a user.
    
    In production, this should be replaced with a secure password
    generation and distribution mechanism.
    """
    # Use the standardized default password for all users
    return DEFAULT_PASSWORDS.get(username, SECURE_DEFAULT_PASSWORD)


def get_production_password(username):
    """
    Get the production password for a user.
    
    These are unique passwords that should be used in production
    and changed immediately after deployment.
    """
    return PRODUCTION_PASSWORDS.get(username)


def validate_password_strength(password):
    """
    Validate password strength against security requirements.
    
    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []
    
    if len(password) < 8:
        errors.append("Password must be at least 8 characters long")
    
    if not any(c.isupper() for c in password):
        errors.append("Password must contain at least one uppercase letter")
    
    if not any(c.islower() for c in password):
        errors.append("Password must contain at least one lowercase letter")
    
    if not any(c.isdigit() for c in password):
        errors.append("Password must contain at least one number")
    
    if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password):
        errors.append("Password must contain at least one special character")
    
    return len(errors) == 0, errors


# Warning message for development/demo environments
DEV_WARNING = """
================================================================================
WARNING: Development/Demo Environment Detected

Default passwords are in use. This configuration is suitable for:
- Local development
- Testing
- Demonstrations

DO NOT use these default passwords in production environments!

Default Credentials:
- HR Manager: hr_manager / Manager123!
- Dandora Manager: dandora_manager / Manager123!
- Tassia Manager: tassia_manager / Manager123!
- Kiambu Manager: kiambu_manager / Manager123!

Change all passwords immediately after deployment to production.
================================================================================
"""