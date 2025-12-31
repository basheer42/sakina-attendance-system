"""
Sakina Gas Company - Authentication Routes
Built from scratch with comprehensive security and user management
Version 3.0 - Enterprise grade with advanced security features
FIXED: All AuditLog.log_event() calls now use event_type= instead of action=
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
                AuditLog.log_event(
                    event_type='login_attempt_invalid_input',  # FIXED: was action=
                    user_id=None,
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
        
        if user is None:
            # Log failed login attempt
            try:
                AuditLog.log_event(
                    event_type='login_failed',  # FIXED: was action=
                    user_id=None,
                    description=f'Failed login attempt for: {username_or_email}',
                    ip_address=client_ip
                )
                db.session.commit()
            except:
                db.session.rollback()
            
            flash('Invalid username/email or password.', 'error')
            return render_template('auth/login.html')
        
        # Check password
        if not user.check_password(password):
            # Log failed password attempt
            try:
                AuditLog.log_event(
                    event_type='login_failed_password',  # FIXED: was action=
                    user_id=user.id,
                    description=f'Failed login attempt - wrong password for: {username_or_email}',
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
                AuditLog.log_event(
                    event_type='login_attempt_locked_account',  # FIXED: was action=
                    user_id=user.id,
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
                AuditLog.log_event(
                    event_type='login_attempt_inactive_account',  # FIXED: was action=
                    user_id=user.id,
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
            
            AuditLog.log_event(
                event_type='login_successful',  # FIXED: was action=
                user_id=user.id,
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
        
        AuditLog.log_event(
            event_type='logout',  # FIXED: was action=
            user_id=user_id,
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
                AuditLog.log_event(
                    event_type='password_reset_requested',  # FIXED: was action=
                    user_id=user.id,
                    description=f'Password reset requested for: {user.username}',
                    ip_address=request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR'))
                )
                db.session.commit()
            except:
                db.session.rollback()
        else:
            # Log attempt on non-existent email
            try:
                AuditLog.log_event(
                    event_type='password_reset_invalid_email',  # FIXED: was action=
                    user_id=None,
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
            AuditLog.log_event(
                event_type='password_reset_completed',  # FIXED: was action=
                user_id=user.id,
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


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration (for self-registration if enabled)"""
    # FIXED: Local imports
    from models.user import User
    from models.audit import AuditLog
    
    # Check if self-registration is enabled
    if not current_app.config.get('ALLOW_SELF_REGISTRATION', False):
        flash('Self-registration is not enabled. Please contact your administrator.', 'info')
        return redirect(url_for('auth.login'))
    
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.main'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        
        # Validate required fields
        if not all([username, email, password, first_name, last_name]):
            flash('All fields are required.', 'error')
            return render_template('auth/register.html')
        
        # Validate email format
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            flash('Please enter a valid email address.', 'error')
            return render_template('auth/register.html')
        
        # Validate password match
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('auth/register.html')
        
        # Check if username exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'error')
            return render_template('auth/register.html')
        
        # Check if email exists
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'error')
            return render_template('auth/register.html')
        
        try:
            # Create new user
            user = User(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                role='employee',  # Default role for self-registration
                is_active=False  # Require admin approval
            )
            user.set_password(password)
            
            db.session.add(user)
            db.session.commit()
            
            # Log registration
            AuditLog.log_event(
                event_type='user_registered',  # FIXED: was action=
                user_id=user.id,
                description=f'New user registered: {username}',
                ip_address=request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR'))
            )
            db.session.commit()
            
            flash('Registration successful! Your account is pending approval.', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error during registration: {e}')
            flash('An error occurred during registration. Please try again.', 'error')
    
    return render_template('auth/register.html')


@auth_bp.route('/verify-email/<token>')
def verify_email(token):
    """Email verification"""
    # FIXED: Local imports
    from models.user import User
    from models.audit import AuditLog
    
    # Verify token and find user
    user = None
    if hasattr(User, 'verify_email_token'):
        user = User.verify_email_token(token)
    
    if not user:
        flash('Invalid or expired email verification token.', 'error')
        return redirect(url_for('auth.login'))
    
    try:
        if hasattr(user, 'email_verified'):
            user.email_verified = True
        
        db.session.commit()
        
        # Log verification
        AuditLog.log_event(
            event_type='email_verified',  # FIXED: was action=
            user_id=user.id,
            description=f'Email verified for: {user.username}',
            ip_address=request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR'))
        )
        db.session.commit()
        
        flash('Your email has been verified successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error verifying email: {e}')
        flash('An error occurred during email verification.', 'error')
    
    return redirect(url_for('auth.login'))


@auth_bp.route('/resend-verification', methods=['GET', 'POST'])
def resend_verification():
    """Resend email verification"""
    # FIXED: Local imports
    from models.user import User
    from models.audit import AuditLog
    
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.main'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        
        if not email:
            flash('Please enter your email address.', 'error')
            return render_template('auth/resend_verification.html')
        
        user = User.query.filter_by(email=email).first()
        
        if user and hasattr(user, 'email_verified') and not user.email_verified:
            # Generate and send new verification email
            if hasattr(user, 'generate_email_verification_token'):
                user.generate_email_verification_token()
                db.session.commit()
            
            # Log action
            try:
                AuditLog.log_event(
                    event_type='verification_email_resent',  # FIXED: was action=
                    user_id=user.id,
                    description=f'Verification email resent for: {user.username}',
                    ip_address=request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR'))
                )
                db.session.commit()
            except:
                db.session.rollback()
        
        # Always show success for security
        flash('If an account with that email exists and requires verification, a new email has been sent.', 'info')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/resend_verification.html')


# =============================================================================
# API Endpoints for AJAX calls
# =============================================================================

@auth_bp.route('/api/check-username', methods=['POST'])
def check_username():
    """Check if username is available"""
    # FIXED: Local imports
    from models.user import User
    
    username = request.json.get('username', '').strip()
    
    if not username:
        return jsonify({'available': False, 'message': 'Username is required'})
    
    if len(username) < 3:
        return jsonify({'available': False, 'message': 'Username must be at least 3 characters'})
    
    exists = User.query.filter_by(username=username).first() is not None
    
    return jsonify({
        'available': not exists,
        'message': 'Username is taken' if exists else 'Username is available'
    })


@auth_bp.route('/api/check-email', methods=['POST'])
def check_email():
    """Check if email is available"""
    # FIXED: Local imports
    from models.user import User
    
    email = request.json.get('email', '').strip()
    
    if not email:
        return jsonify({'available': False, 'message': 'Email is required'})
    
    # Validate email format
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        return jsonify({'available': False, 'message': 'Invalid email format'})
    
    exists = User.query.filter_by(email=email).first() is not None
    
    return jsonify({
        'available': not exists,
        'message': 'Email is already registered' if exists else 'Email is available'
    })


@auth_bp.route('/api/session-status')
@login_required
def session_status():
    """Check session status for frontend"""
    return jsonify({
        'authenticated': True,
        'user_id': current_user.id,
        'username': current_user.username,
        'role': current_user.role
    })


# =============================================================================
# Before Request Handler
# =============================================================================

@auth_bp.before_app_request
def before_request():
    """Execute before each request"""
    if current_user.is_authenticated:
        # Update last activity
        if hasattr(current_user, 'update_last_activity'):
            current_user.update_last_activity()
        
        # Check for session timeout
        session_timeout = current_app.config.get('SESSION_TIMEOUT_MINUTES', 60)
        last_activity = session.get('last_activity')
        
        if last_activity:
            try:
                last_activity_time = datetime.fromisoformat(last_activity)
                if datetime.utcnow() - last_activity_time > timedelta(minutes=session_timeout):
                    # Session expired
                    logout_user()
                    session.clear()
                    flash('Your session has expired. Please log in again.', 'warning')
                    return redirect(url_for('auth.login'))
            except (ValueError, TypeError):
                pass
        
        # Update last activity in session
        session['last_activity'] = datetime.utcnow().isoformat()
        
        # Store user info in g for easy access
        g.user = current_user
        g.is_hr_manager = current_user.role == 'hr_manager'
        g.is_station_manager = current_user.role == 'station_manager'