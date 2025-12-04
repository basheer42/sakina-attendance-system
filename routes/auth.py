"""
Sakina Gas Company - Authentication Routes
Built from scratch with comprehensive security and user management
Version 3.0 - Enterprise grade with advanced security features
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, session, current_app, g # FIX: Added g
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

# FIX: Removed global model imports to prevent early model registration
from database import db

# Create blueprint
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Enhanced login with comprehensive security features"""
    # FIX: Local imports
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
            AuditLog.log_security_event(
                'login_attempt_invalid_input',
                f'Invalid login attempt - missing credentials for: {username_or_email}',
                ip_address=request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR')), # FIX: Use request context
                risk_level='low'
            )
            return render_template('auth/login.html')
        
        # Get client information for security logging
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR'))
        user_agent = request.headers.get('User-Agent', '')
        
        # Find user
        user = User.authenticate(username_or_email, password)
        
        if user is None:
            # Log failed login attempt
            AuditLog.log_security_event(
                'login_failed',
                f'Failed login attempt for: {username_or_email}',
                ip_address=client_ip,
                user_agent=user_agent,
                details={'username_or_email': username_or_email},
                risk_level='medium'
            )
            
            flash('Invalid username/email or password.', 'error')
            return render_template('auth/login.html')
        
        # Check if account is locked
        if user.is_account_locked():
            AuditLog.log_security_event(
                'login_attempt_locked_account',
                f'Login attempt on locked account: {user.username}',
                user_id=user.id,
                ip_address=client_ip,
                user_agent=user_agent,
                risk_level='high'
            )
            
            flash('Account is temporarily locked due to multiple failed login attempts. Please try again later.', 'error')
            return render_template('auth/login.html')
        
        # Check if account is active
        if not user.is_active:
            AuditLog.log_security_event(
                'login_attempt_inactive_account',
                f'Login attempt on inactive account: {user.username}',
                user_id=user.id,
                ip_address=client_ip,
                user_agent=user_agent,
                risk_level='medium'
            )
            
            flash('Your account is inactive. Please contact your administrator.', 'error')
            return render_template('auth/login.html')
        
        # Check if password is expired
        if user.is_password_expired():
            session['password_reset_user_id'] = user.id
            flash('Your password has expired. Please set a new password.', 'warning')
            return redirect(url_for('profile.change_password')) # FIX: Redirect to profile blueprint's change password
        
        # Successful login
        login_user(user, remember=remember_me)
        
        # Generate session token
        session_token = user.generate_session_token()
        session['session_token'] = session_token
        
        # Update user activity
        user.update_last_activity()
        
        # Log successful login
        AuditLog.log_security_event(
            'login_successful',
            f'Successful login: {user.username}',
            user_id=user.id,
            ip_address=client_ip,
            user_agent=user_agent,
            details={
                'remember_me': remember_me,
                'session_token': session_token[:10] + '...'  # Partial token for security
            },
            risk_level='low'
        )
        
        # Commit changes
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error updating user login: {e}')
        
        # Handle next URL
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            # Redirect based on user role
            if user.role == 'hr_manager':
                next_page = url_for('dashboard.hr_overview')
            elif user.role == 'station_manager':
                next_page = url_for('dashboard.station_overview')
            # FIX: Added redirect for other roles
            elif user.role == 'finance_manager':
                next_page = url_for('dashboard.finance_overview')
            elif user.role == 'admin':
                next_page = url_for('dashboard.admin_overview')
            else:
                next_page = url_for('dashboard.main')
        
        # FIX: Removed hardcoded password in flash
        flash(f'Welcome back, {user.get_display_name()}!', 'success')
        return redirect(next_page)
    
    return render_template('auth/login.html')

@auth_bp.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    """Enhanced logout with session cleanup"""
    # FIX: Local imports
    from models.audit import AuditLog
    
    user_id = current_user.id
    username = current_user.username
    session_token = session.get('session_token')
    
    # Log logout
    AuditLog.log_security_event(
        'logout',
        f'User logged out: {username}',
        user_id=user_id,
        details={'session_token': session_token[:10] + '...' if session_token else None},
        risk_level='low'
    )
    
    # Invalidate user session
    if hasattr(current_user, 'invalidate_session'):
        current_user.invalidate_session()
    
    # Clear session data
    session.clear()
    
    # Logout user
    logout_user()
    
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error during logout: {e}')
    
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Redirect to profile blueprint's password change route (FIX for correct URL)"""
    return redirect(url_for('profile.change_password'))

@auth_bp.route('/profile')
@login_required
def profile():
    """Redirect to profile blueprint's view route (FIX for correct URL)"""
    return redirect(url_for('profile.view_profile'))

@auth_bp.route('/update-profile', methods=['POST'])
@login_required
def update_profile():
    """Redirect to profile blueprint's edit route (FIX for correct URL)"""
    return redirect(url_for('profile.edit_profile'))

@auth_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """Redirect to profile blueprint's preferences route (FIX for correct URL)"""
    return redirect(url_for('profile.preferences'))

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Password reset request"""
    # FIX: Local imports
    from models.user import User
    from models.audit import AuditLog
    
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.main'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        
        if not email:
            flash('Please enter your email address.', 'error')
            return render_template('auth/forgot_password.html')
        
        user = User.query.filter_by(email=email, is_active=True).first()
        
        if user:
            try:
                # Generate reset token
                reset_token = user.generate_password_reset_token()
                
                # Log password reset request
                AuditLog.log_security_event(
                    'password_reset_requested',
                    f'Password reset requested for user: {user.username}',
                    user_id=user.id,
                    details={'email': email},
                    risk_level='medium'
                )
                
                db.session.commit()
                
                # In a real application, send email here
                # For now, we'll just show a success message
                flash('If your email address is registered, you will receive password reset instructions.', 'info')
                
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f'Error generating reset token: {e}')
                flash('An error occurred. Please try again later.', 'error')
        else:
            # Still show success message for security (don't reveal if email exists)
            flash('If your email address is registered, you will receive password reset instructions.', 'info')
        
        return redirect(url_for('auth.login'))
    
    return render_template('auth/forgot_password.html')

@auth_bp.route('/security-logs')
@login_required
def security_logs():
    """Redirect to profile blueprint's activity log route (FIX for correct URL)"""
    return redirect(url_for('profile.activity_log'))

# API Endpoints

@auth_bp.route('/api/check-session', methods=['GET'])
@login_required
def api_check_session():
    """Check if current session is valid"""
    # FIX: Local imports (none needed here)
    
    session_token = session.get('session_token')
    
    if not session_token or (hasattr(current_user, 'is_session_valid') and not current_user.is_session_valid(session_token)):
        return jsonify({
            'valid': False,
            'message': 'Session expired'
        }), 401
    
    return jsonify({
        'valid': True,
        'user': current_user.get_display_name(),
        'expires_in': int((current_user.session_expires - datetime.utcnow()).total_seconds())
    })

@auth_bp.route('/api/extend-session', methods=['POST'])
@login_required
def api_extend_session():
    """Extend current session"""
    # FIX: Local imports
    from models.audit import AuditLog
    
    try:
        current_user.extend_session()
        
        AuditLog.log_security_event(
            'session_extended',
            f'Session extended for user: {current_user.username}',
            user_id=current_user.id,
            risk_level='low'
        )
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Session extended',
            'expires_in': int((current_user.session_expires - datetime.utcnow()).total_seconds())
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'Failed to extend session'
        }), 500

@auth_bp.route('/api/password-strength', methods=['POST'])
def api_password_strength():
    """Check password strength"""
    # FIX: Local imports (none needed here)
    
    password = request.json.get('password', '') if request.is_json else request.form.get('password', '')
    
    if not password:
        return jsonify({
            'score': 0,
            'strength': 'Very Weak',
            'feedback': ['Password is required']
        })
    
    score = 0
    feedback = []
    
    # Length check
    if len(password) >= 8:
        score += 25
    else:
        feedback.append('Password must be at least 8 characters long')
    
    # Complexity checks
    if re.search(r'[A-Z]', password):
        score += 20
    else:
        feedback.append('Include at least one uppercase letter')
    
    if re.search(r'[a-z]', password):
        score += 20
    else:
        feedback.append('Include at least one lowercase letter')
    
    if re.search(r'\d', password):
        score += 20
    else:
        feedback.append('Include at least one number')
    
    if re.search(r'[!@#$%^&*()_+\-=\[\]{};:"\\|,.<>\?]', password):
        score += 15
    else:
        feedback.append('Include at least one special character')
    
    # Common password check
    common_passwords = ['password', '123456', 'admin', 'user', 'test']
    if password.lower() in common_passwords:
        score = max(0, score - 30)
        feedback.append('Avoid common passwords')
    
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

# Request hooks for authentication blueprint

@auth_bp.before_request
def before_auth_request():
    """Security checks before authentication requests"""
    # Track IP addresses for suspicious activity
    client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR'))
    
    # Check for suspicious user agents
    user_agent = request.headers.get('User-Agent', '').lower()
    suspicious_agents = ['curl', 'wget', 'python-requests', 'bot', 'crawler']
    
    if any(agent in user_agent for agent in suspicious_agents):
        current_app.logger.warning(f'Suspicious user agent from {client_ip}: {user_agent}')
    
    # Store client info for use in views
    # FIX: Use g object for request-scoped data
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