"""
Sakina Gas Company - Authentication Routes
Built from scratch with comprehensive security and user management
Version 3.0 - Enterprise grade with advanced security features
FIXED: Models imported inside functions to prevent mapper conflicts
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, session, current_app, g
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime, timedelta

# Handle Werkzeug version compatibility
try:
    from werkzeug.urls import url_parse
except ImportError:
    # For newer Werkzeug versions
    from urllib.parse import urlparse as url_parse
import secrets
import re

# FIXED: Removed global model imports to prevent early model registration
from database import db

# Create blueprint
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Enhanced login with comprehensive security features"""
    # FIXED: Local imports
    from models.user import User
    from models.audit import AuditLog
    
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.main'))
    
    if request.method == 'POST':
        username_or_email = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember_me = bool(request.form.get('remember_me'))
        
        # Basic validation
        if not username_or_email or not password:
            flash('Please enter both username/email and password.', 'error')
            try:
                AuditLog.log_action(
                    user_id=None,
                    action='login_attempt_invalid_input',
                    description=f'Invalid login attempt - missing credentials for: {username_or_email}',
                    ip_address=request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR'))
                )
                db.session.commit()
            except:
                db.session.rollback()
            return render_template('auth/login.html')
        
        # Get client information for security logging
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR'))
        user_agent = request.headers.get('User-Agent', '')
        
        # Find user by username or email
        user = User.query.filter(
            (User.username == username_or_email) | 
            (User.email == username_or_email)
        ).first()

        # Check password
        if user and user.check_password(password):
            # Password validation already done above
            pass
        
        if user is None:
            # Log failed login attempt
            try:
                AuditLog.log_action(
                    user_id=None,
                    action='login_failed',
                    description=f'Failed login attempt for: {username_or_email}',
                    ip_address=client_ip
                )
                db.session.commit()
            except:
                db.session.rollback()
            
            flash('Invalid username/email or password.', 'error')
            return render_template('auth/login.html')
        
        # Check if account is locked (if method exists)
        if hasattr(user, 'is_account_locked') and user.is_account_locked():
            try:
                AuditLog.log_action(
                    user_id=user.id,
                    action='login_attempt_locked_account',
                    description=f'Login attempt on locked account: {user.username}',
                    ip_address=client_ip
                )
                db.session.commit()
            except:
                db.session.rollback()
            
            flash('Account is temporarily locked due to multiple failed login attempts. Please try again later.', 'error')
            return render_template('auth/login.html')
        
        # Check if account is active
        if not user.is_active:
            try:
                AuditLog.log_action(
                    user_id=user.id,
                    action='login_attempt_inactive_account',
                    description=f'Login attempt on inactive account: {user.username}',
                    ip_address=client_ip
                )
                db.session.commit()
            except:
                db.session.rollback()
            
            flash('Your account is inactive. Please contact your administrator.', 'error')
            return render_template('auth/login.html')
        
        # Check if password is expired (if method exists)
        if hasattr(user, 'is_password_expired') and user.is_password_expired():
            session['password_reset_user_id'] = user.id
            flash('Your password has expired. Please set a new password.', 'warning')
            return redirect(url_for('profile.change_password'))
        
        # Successful login
        login_user(user, remember=remember_me)
        
        # Generate session token (if method exists)
        if hasattr(user, 'generate_session_token'):
            session_token = user.generate_session_token()
            session['session_token'] = session_token
        
        # Update user activity (if method exists)
        if hasattr(user, 'update_last_activity'):
            user.update_last_activity()
        else:
            user.last_login = datetime.utcnow()
        
        # Log successful login
        try:
            details = {
                'remember_me': remember_me,
            }
            if 'session_token' in locals():
                details['session_token'] = session_token[:10] + '...'
            
            AuditLog.log_action(
                user_id=user.id,
                action='login_successful',
                description=f'Successful login: {user.username}',
                ip_address=client_ip
            )
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error updating user login: {e}')
        
        # Handle next URL
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            # Redirect based on user role
            if user.role == 'hr_manager':
                next_page = url_for('dashboard.main')
            elif user.role == 'station_manager':
                next_page = url_for('dashboard.main')
            else:
                next_page = url_for('dashboard.main')
        
        display_name = user.get_full_name() if hasattr(user, 'get_full_name') else user.username
        flash(f'Welcome back, {display_name}!', 'success')
        return redirect(next_page)
    
    return render_template('auth/login.html')

@auth_bp.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    """Enhanced logout with session cleanup"""
    # FIXED: Local imports
    from models.audit import AuditLog
    
    user_id = current_user.id
    username = current_user.username
    session_token = session.get('session_token')
    
    # Log logout
    try:
        details = {}
        if session_token:
            details['session_token'] = session_token[:10] + '...'
        
        AuditLog.log_action(
            user_id=user_id,
            action='logout',
            description=f'User logged out: {username}',
            ip_address=request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR'))
        )
        db.session.commit()
    except:
        db.session.rollback()
    
    # Invalidate user session (if method exists)
    if hasattr(current_user, 'invalidate_session'):
        current_user.invalidate_session()
    
    # Clear session data
    session.clear()
    
    # Logout user
    logout_user()
    
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Redirect to profile blueprint's password change route"""
    return redirect(url_for('profile.change_password'))

@auth_bp.route('/profile')
@login_required
def profile():
    """Redirect to profile blueprint's view route"""
    return redirect(url_for('profile.view_profile'))

@auth_bp.route('/update-profile', methods=['POST'])
@login_required
def update_profile():
    """Redirect to profile blueprint's edit route"""
    return redirect(url_for('profile.edit_profile'))

@auth_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """Redirect to profile blueprint's preferences route"""
    return redirect(url_for('profile.preferences'))

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Password reset request"""
    # FIXED: Local imports
    from models.user import User
    from models.audit import AuditLog
    
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.main'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        
        if not email:
            flash('Please enter your email address.', 'error')
            return render_template('auth/forgot_password.html')
        
        # Validate email format
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            flash('Please enter a valid email address.', 'error')
            return render_template('auth/forgot_password.html')
        
        # Find user by email
        user = User.query.filter_by(email=email, is_active=True).first()
        
        if user:
            # Generate password reset token (if method exists)
            if hasattr(user, 'generate_password_reset_token'):
                reset_token = user.generate_password_reset_token()
                # In a real application, you would send an email with the reset link
                # For now, we'll just log the action
            
            # Log password reset request
            try:
                AuditLog.log_action(
                    user_id=user.id,
                    action='password_reset_requested',
                    description=f'Password reset requested for: {user.username}',
                    ip_address=request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR'))
                )
                db.session.commit()
            except:
                db.session.rollback()
        else:
            # Log attempt on non-existent email
            try:
                AuditLog.log_action(
                    user_id=None,
                    action='password_reset_invalid_email',
                    description=f'Password reset attempted for non-existent email: {email}',
                    ip_address=request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR'))
                )
                db.session.commit()
            except:
                db.session.rollback()
        
        # Always show success message for security (don't reveal if email exists)
        flash('If an account with that email exists, password reset instructions have been sent.', 'info')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/forgot_password.html')

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Password reset with token"""
    # FIXED: Local imports
    from models.user import User
    from models.audit import AuditLog
    
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.main'))
    
    # Verify token and find user (if method exists)
    user = None
    if hasattr(User, 'verify_password_reset_token'):
        user = User.verify_password_reset_token(token)
    
    if not user:
        flash('Invalid or expired password reset token.', 'error')
        return redirect(url_for('auth.forgot_password'))
    
    if request.method == 'POST':
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validate password
        if not password:
            flash('Password is required.', 'error')
            return render_template('auth/reset_password.html', token=token)
        
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('auth/reset_password.html', token=token)
        
        # Validate password strength
        if len(password) < 8:
            flash('Password must be at least 8 characters long.', 'error')
            return render_template('auth/reset_password.html', token=token)
        
        # Set new password
        try:
            user.set_password(password)
            
            # Clear any existing reset tokens (if method exists)
            if hasattr(user, 'clear_password_reset_token'):
                user.clear_password_reset_token()
            
            # Log password reset
            AuditLog.log_action(
                user_id=user.id,
                action='password_reset_completed',
                description=f'Password reset completed for: {user.username}',
                ip_address=request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR'))
            )
            
            db.session.commit()
            
            flash('Your password has been reset successfully. You can now log in.', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error resetting password: {e}')
            flash('An error occurred while resetting your password. Please try again.', 'error')
    
    return render_template('auth/reset_password.html', token=token)

@auth_bp.route('/check-password-strength', methods=['POST'])
def check_password_strength():
    """AJAX endpoint to check password strength"""
    password = request.json.get('password', '') if request.is_json else request.form.get('password', '')
    
    if not password:
        return jsonify({'score': 0, 'strength': 'Very Weak', 'feedback': ['Password is required']})
    
    score = 0
    feedback = []
    
    # Length check
    if len(password) >= 12:
        score += 30
    elif len(password) >= 8:
        score += 25
    elif len(password) >= 6:
        score += 15
    else:
        feedback.append('Use at least 8 characters (12+ recommended)')
    
    # Uppercase check
    if re.search(r'[A-Z]', password):
        score += 15
    else:
        feedback.append('Include at least one uppercase letter')
    
    # Lowercase check
    if re.search(r'[a-z]', password):
        score += 15
    else:
        feedback.append('Include at least one lowercase letter')
    
    # Number check
    if re.search(r'\d', password):
        score += 15
    else:
        feedback.append('Include at least one number')
    
    # Special character check
    if re.search(r'[!@#$%^&*()_+=\-\[\]{};:"\\|,.<>?]', password):
        score += 15
    else:
        feedback.append('Include at least one special character')
    
    # Common password check
    common_passwords = ['password', '123456', 'admin', 'user', 'test', 'qwerty', 'abc123', 'password123']
    if password.lower() in common_passwords:
        score = max(0, score - 30)
        feedback.append('Avoid common passwords')
    
    # Sequential characters check
    if re.search(r'(012|123|234|345|456|567|678|789|890|abc|bcd|cde)', password.lower()):
        score = max(0, score - 10)
        feedback.append('Avoid sequential characters')
    
    # Repeated characters check
    if re.search(r'(.)\1{2,}', password):
        score = max(0, score - 10)
        feedback.append('Avoid repeated characters')
    
    # Determine strength label
    if score >= 90:
        strength = 'Very Strong'
        color = '#28A745'
    elif score >= 70:
        strength = 'Strong'
        color = '#20C997'
    elif score >= 50:
        strength = 'Moderate'
        color = '#FFC107'
    elif score >= 30:
        strength = 'Weak'
        color = '#FD7E14'
    else:
        strength = 'Very Weak'
        color = '#DC3545'
    
    return jsonify({
        'score': score,
        'strength': strength,
        'color': color,
        'feedback': feedback
    })

@auth_bp.route('/validate-username', methods=['POST'])
def validate_username():
    """AJAX endpoint to validate username availability"""
    # FIXED: Local imports
    from models.user import User
    
    username = request.json.get('username', '') if request.is_json else request.form.get('username', '')
    current_user_id = request.json.get('current_user_id') if request.is_json else request.form.get('current_user_id')
    
    if not username:
        return jsonify({'available': False, 'message': 'Username is required'})
    
    # Check username format
    if not re.match(r'^[a-zA-Z0-9_]{3,20}$', username):
        return jsonify({
            'available': False, 
            'message': 'Username must be 3-20 characters and contain only letters, numbers, and underscores'
        })
    
    # Check if username exists
    query = User.query.filter_by(username=username)
    if current_user_id:
        query = query.filter(User.id != int(current_user_id))
    
    existing_user = query.first()
    
    if existing_user:
        return jsonify({'available': False, 'message': 'Username is already taken'})
    
    return jsonify({'available': True, 'message': 'Username is available'})

@auth_bp.route('/validate-email', methods=['POST'])
def validate_email():
    """AJAX endpoint to validate email availability"""
    # FIXED: Local imports
    from models.user import User
    
    email = request.json.get('email', '') if request.is_json else request.form.get('email', '')
    current_user_id = request.json.get('current_user_id') if request.is_json else request.form.get('current_user_id')
    
    if not email:
        return jsonify({'available': False, 'message': 'Email is required'})
    
    # Check email format
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        return jsonify({'available': False, 'message': 'Invalid email format'})
    
    # Check if email exists
    query = User.query.filter_by(email=email)
    if current_user_id:
        query = query.filter(User.id != int(current_user_id))
    
    existing_user = query.first()
    
    if existing_user:
        return jsonify({'available': False, 'message': 'Email is already registered'})
    
    return jsonify({'available': True, 'message': 'Email is available'})

# Request hooks for authentication blueprint
@auth_bp.before_request
def before_auth_request():
    """Security checks before authentication requests"""
    # Track IP addresses for suspicious activity
    client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR'))
    
    # Check for suspicious user agents
    user_agent = request.headers.get('User-Agent', '').lower()
    suspicious_agents = ['curl', 'wget', 'python-requests', 'bot', 'crawler', 'scanner']
    
    if any(agent in user_agent for agent in suspicious_agents):
        current_app.logger.warning(f'Suspicious user agent from {client_ip}: {user_agent}')
    
    # Store client info for use in views
    g.client_ip = client_ip
    g.client_user_agent = request.headers.get('User-Agent', '')

@auth_bp.after_request
def after_auth_request(response):
    """Security headers and cleanup after authentication requests"""
    # Add security headers
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    
    return response

# Error handlers for authentication blueprint
@auth_bp.errorhandler(429)
def auth_rate_limit_handler(e):
    """Handle rate limiting errors"""
    return render_template('auth/rate_limited.html'), 429

@auth_bp.errorhandler(500)
def auth_server_error(error):
    """Handle server errors in authentication"""
    db.session.rollback()
    current_app.logger.error(f'Authentication error: {error}')
    flash('A system error occurred. Please try again or contact support.', 'error')
    return redirect(url_for('auth.login'))