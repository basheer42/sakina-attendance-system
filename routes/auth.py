"""
Enhanced Authentication Routes for Sakina Gas Attendance System
Built upon your existing comprehensive authentication with advanced security features
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, session, g
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User, AuditLog
from datetime import datetime, timedelta
from urllib.parse import urlparse, urljoin
import re

auth_bp = Blueprint('auth', __name__)

def is_safe_url(target):
    """Check if redirect URL is safe (prevents open redirects)"""
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc

def validate_password_strength(password):
    """Validate password against security policy"""
    errors = []
    
    if len(password) < 8:
        errors.append("Password must be at least 8 characters long")
    
    if not re.search(r"[A-Z]", password):
        errors.append("Password must contain at least one uppercase letter")
    
    if not re.search(r"[a-z]", password):
        errors.append("Password must contain at least one lowercase letter")
    
    if not re.search(r"\d", password):
        errors.append("Password must contain at least one number")
    
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        errors.append("Password must contain at least one special character")
    
    return errors

def log_security_event(event_type, details=None, risk_level='low'):
    """Log security-related events for audit"""
    if current_user.is_authenticated:
        user_id = current_user.id
    else:
        user_id = None
    
    try:
        audit_entry = AuditLog(
            user_id=user_id,
            action=event_type,
            target_type='security',
            details=details,
            ip_address=getattr(g, 'ip_address', None),
            user_agent=request.headers.get('User-Agent'),
            risk_level=risk_level,
            compliance_relevant=True
        )
        db.session.add(audit_entry)
        db.session.commit()
    except Exception as e:
        # Don't let audit logging break the application
        print(f"Audit logging error: {e}")

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Enhanced login with comprehensive security features"""
    # If user is already authenticated, redirect to dashboard
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.main'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember_me = bool(request.form.get('remember_me'))
        
        # Basic validation
        if not username or not password:
            flash('Please enter both username and password.', 'danger')
            log_security_event('login_attempt_incomplete', 
                             f'Missing credentials for username: {username}', 'medium')
            return render_template('auth/login.html')
        
        # Find user
        user = User.query.filter_by(username=username).first()
        
        if user:
            # Check if account is locked
            if user.is_locked:
                flash('Account is temporarily locked due to multiple failed login attempts. '
                     'Please try again later or contact your administrator.', 'warning')
                log_security_event('login_attempt_locked_account', 
                                 f'Attempt to access locked account: {username}', 'high')
                return render_template('auth/login.html')
            
            # Check if account is active
            if not user.is_active:
                flash('Your account has been deactivated. Please contact your administrator.', 'danger')
                log_security_event('login_attempt_inactive_account', 
                                 f'Attempt to access inactive account: {username}', 'high')
                return render_template('auth/login.html')
            
            # Check password
            if user.check_password(password):
                # Successful login
                user.record_login_attempt(success=True)
                login_user(user, remember=remember_me)
                
                # Log successful login
                log_security_event('login_success', 
                                 f'User {username} logged in successfully', 'low')
                
                # Set session security
                session.permanent = remember_me
                
                # Welcome message
                flash(f'Welcome back, {user.first_name}!', 'success')
                
                # Redirect to next page or dashboard
                next_page = request.args.get('next')
                if next_page and is_safe_url(next_page):
                    return redirect(next_page)
                
                # Role-based redirection
                if user.role == 'hr_manager':
                    return redirect(url_for('dashboard.hr_overview'))
                elif user.role == 'station_manager':
                    return redirect(url_for('dashboard.station_overview'))
                else:
                    return redirect(url_for('dashboard.main'))
            else:
                # Failed login
                user.record_login_attempt(success=False)
                flash('Invalid username or password. Please try again.', 'danger')
                log_security_event('login_failure', 
                                 f'Failed login attempt for username: {username}', 'medium')
        else:
            # User not found
            flash('Invalid username or password. Please try again.', 'danger')
            log_security_event('login_failure', 
                             f'Login attempt for non-existent user: {username}', 'medium')
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """Enhanced logout with session cleanup and audit logging"""
    username = current_user.username
    user_id = current_user.id
    
    # Log the logout
    log_security_event('logout', f'User {username} logged out', 'low')
    
    # Clear session data
    session.clear()
    
    # Logout user
    logout_user()
    
    # Success message
    flash(f'You have been logged out successfully. Goodbye!', 'info')
    
    return redirect(url_for('auth.login'))

@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Allow users to change their password"""
    if request.method == 'POST':
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validate current password
        if not current_user.check_password(current_password):
            flash('Current password is incorrect.', 'danger')
            return render_template('auth/change_password.html')
        
        # Validate new password
        if new_password != confirm_password:
            flash('New passwords do not match.', 'danger')
            return render_template('auth/change_password.html')
        
        # Check password strength
        password_errors = validate_password_strength(new_password)
        if password_errors:
            for error in password_errors:
                flash(error, 'danger')
            return render_template('auth/change_password.html')
        
        # Update password
        current_user.set_password(new_password)
        db.session.commit()
        
        # Log password change
        log_security_event('password_change', 
                         f'User {current_user.username} changed password', 'medium')
        
        flash('Your password has been updated successfully!', 'success')
        return redirect(url_for('dashboard.main'))
    
    return render_template('auth/change_password.html')

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Password reset request (basic implementation)"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        
        if not email:
            flash('Please enter your email address.', 'danger')
            return render_template('auth/forgot_password.html')
        
        # Check if user exists
        user = User.query.filter_by(email=email).first()
        
        if user:
            # Log password reset request
            log_security_event('password_reset_request', 
                             f'Password reset requested for {user.username}', 'medium')
            
            # In a real implementation, you would:
            # 1. Generate a secure reset token
            # 2. Send email with reset link
            # 3. Store token with expiration
            
            flash('If an account with that email exists, password reset instructions '
                 'have been sent. Please contact your administrator.', 'info')
        else:
            # Don't reveal if email exists or not (security best practice)
            flash('If an account with that email exists, password reset instructions '
                 'have been sent. Please contact your administrator.', 'info')
            
            # Still log the attempt
            log_security_event('password_reset_request_invalid', 
                             f'Password reset requested for non-existent email: {email}', 'medium')
        
        return redirect(url_for('auth.login'))
    
    return render_template('auth/forgot_password.html')

@auth_bp.route('/profile')
@login_required
def profile():
    """User profile view"""
    # Get user's recent login history
    recent_logins = AuditLog.query.filter(
        AuditLog.user_id == current_user.id,
        AuditLog.action.in_(['login_success', 'logout'])
    ).order_by(AuditLog.timestamp.desc()).limit(10).all()
    
    return render_template('auth/profile.html', recent_logins=recent_logins)

@auth_bp.route('/update-profile', methods=['POST'])
@login_required
def update_profile():
    """Update user profile information"""
    try:
        # Get form data
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        phone = request.form.get('phone', '').strip()
        
        # Validate required fields
        if not first_name or not last_name or not email:
            flash('First name, last name, and email are required.', 'danger')
            return redirect(url_for('auth.profile'))
        
        # Check if email is already taken by another user
        existing_user = User.query.filter(
            User.email == email,
            User.id != current_user.id
        ).first()
        
        if existing_user:
            flash('This email address is already in use by another account.', 'danger')
            return redirect(url_for('auth.profile'))
        
        # Store old values for audit
        old_values = {
            'first_name': current_user.first_name,
            'last_name': current_user.last_name,
            'email': current_user.email,
            'phone': current_user.phone
        }
        
        # Update user information
        current_user.first_name = first_name
        current_user.last_name = last_name
        current_user.email = email
        current_user.phone = phone
        current_user.updated_at = datetime.utcnow()
        
        # Store new values for audit
        new_values = {
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'phone': phone
        }
        
        db.session.commit()
        
        # Log profile update
        audit_entry = AuditLog(
            user_id=current_user.id,
            action='profile_update',
            target_type='user',
            target_id=current_user.id,
            ip_address=getattr(g, 'ip_address', None),
            user_agent=request.headers.get('User-Agent')
        )
        audit_entry.set_old_values(old_values)
        audit_entry.set_new_values(new_values)
        db.session.add(audit_entry)
        db.session.commit()
        
        flash('Your profile has been updated successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating profile: {str(e)}', 'danger')
    
    return redirect(url_for('auth.profile'))

@auth_bp.route('/security-logs')
@login_required
def security_logs():
    """View user's security activity logs"""
    # Only allow users to see their own security logs
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    logs = AuditLog.query.filter(
        AuditLog.user_id == current_user.id,
        AuditLog.action.in_([
            'login_success', 'login_failure', 'logout', 
            'password_change', 'profile_update', 'password_reset_request'
        ])
    ).order_by(AuditLog.timestamp.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('auth/security_logs.html', logs=logs)

@auth_bp.route('/unauthorized')
def unauthorized():
    """Handle unauthorized access attempts"""
    log_security_event('unauthorized_access', 
                     f'Unauthorized access attempt to {request.referrer}', 'medium')
    
    flash('You do not have permission to access that page.', 'warning')
    
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.main'))
    else:
        return redirect(url_for('auth.login'))

# API endpoints for AJAX requests
@auth_bp.route('/api/check-session')
@login_required
def check_session():
    """Check if user session is still valid"""
    return jsonify({
        'authenticated': True,
        'user': {
            'username': current_user.username,
            'role': current_user.role,
            'location': current_user.location,
            'last_login': current_user.last_login.isoformat() if current_user.last_login else None
        },
        'session_expires': session.permanent
    })

@auth_bp.route('/api/extend-session', methods=['POST'])
@login_required
def extend_session():
    """Extend user session"""
    session.permanent = True
    return jsonify({'success': True, 'message': 'Session extended'})

# Error handlers specific to auth
@auth_bp.errorhandler(401)
def auth_unauthorized(error):
    """Handle 401 errors in auth blueprint"""
    if request.is_json:
        return jsonify({'error': 'Authentication required'}), 401
    
    flash('Please log in to access this page.', 'info')
    return redirect(url_for('auth.login', next=request.url))

@auth_bp.errorhandler(403)
def auth_forbidden(error):
    """Handle 403 errors in auth blueprint"""
    if request.is_json:
        return jsonify({'error': 'Access forbidden'}), 403
    
    flash('You do not have permission to access this resource.', 'danger')
    return redirect(url_for('auth.unauthorized'))

# Security helper functions
def get_client_ip():
    """Get real client IP address"""
    if request.headers.getlist("X-Forwarded-For"):
        return request.headers.getlist("X-Forwarded-For")[0].split(',')[0]
    else:
        return request.remote_addr

def is_password_compromised(password):
    """Check if password appears in common password lists (placeholder)"""
    # In a real implementation, you might check against:
    # - HaveIBeenPwned API
    # - Common password lists
    # - Previously used passwords
    common_passwords = ['password', '123456', 'admin', 'user']
    return password.lower() in common_passwords

# Session management helpers
@auth_bp.before_request
def before_auth_request():
    """Security checks before auth requests"""
    # Store IP for audit logging
    g.ip_address = get_client_ip()
    
    # Check for suspicious patterns
    user_agent = request.headers.get('User-Agent', '')
    if not user_agent or len(user_agent) < 10:
        log_security_event('suspicious_request', 
                         'Request with suspicious or missing User-Agent', 'medium')

@auth_bp.after_request
def after_auth_request(response):
    """Security headers for auth responses"""
    # Prevent caching of sensitive pages
    if request.endpoint in ['auth.login', 'auth.profile', 'auth.change_password']:
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    
    return response