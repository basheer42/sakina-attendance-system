"""
Enhanced User Profile and Settings Routes for Sakina Gas Attendance System
Comprehensive profile management with advanced features, security, and audit logging
FIXED: Models imported inside functions to prevent mapper conflicts
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, g, current_app
from flask_login import login_required, current_user
# FIXED: Removed global model imports to prevent early model registration
from database import db
from datetime import date, datetime, timedelta
from sqlalchemy import func, desc
from werkzeug.utils import secure_filename
import os
import json

profile_bp = Blueprint('profile', __name__)

def get_role_description(role):
    """Get user role description"""
    role_descriptions = {
        'hr_manager': 'Human Resources Manager - Full system access',
        'station_manager': 'Station Manager - Location-specific access',
        'admin': 'System Administrator - Complete system control',
        'employee': 'Employee - Basic access'
    }
    return role_descriptions.get(role, 'Unknown Role')

def calculate_profile_completeness(user):
    """Calculate profile completion percentage"""
    total_fields = 10
    completed_fields = 0
    if user.first_name: completed_fields += 1
    if user.last_name: completed_fields += 1
    if user.email: completed_fields += 1
    if hasattr(user, 'phone') and user.phone: completed_fields += 1
    if hasattr(user, 'department') and user.department: completed_fields += 1
    if hasattr(user, 'location') and user.location: completed_fields += 1
    if hasattr(user, 'timezone') and user.timezone: completed_fields += 1
    if hasattr(user, 'language') and user.language: completed_fields += 1
    if hasattr(user, 'preferences') and user.preferences: completed_fields += 1
    if user.username: completed_fields += 1
    
    return round((completed_fields / total_fields) * 100)

@profile_bp.route('/')
@login_required
def view_profile():
    """Enhanced user profile view with comprehensive information"""
    # FIXED: Local imports
    from models.employee import Employee
    
    # Get user's comprehensive profile data
    profile_data = get_comprehensive_profile_data(current_user)
    
    # Get recent activity (last 30 days)
    recent_activities = get_user_recent_activities(current_user.id, days=30)
    
    # Get security summary
    security_summary = get_user_security_summary(current_user)
    
    # Get associated employee record if exists
    associated_employee = None
    if current_user.role in ['station_manager', 'employee']:
        # Try to find associated employee record
        associated_employee = Employee.query.filter(
            db.or_(
                Employee.employee_id == getattr(current_user, 'employee_id', ''),
                Employee.email == current_user.email
            )
        ).first()
    
    return render_template('profile/view.html',
                         user=current_user,
                         profile_data=profile_data,
                         recent_activities=recent_activities,
                         security_summary=security_summary,
                         associated_employee=associated_employee,
                         profile_completeness=calculate_profile_completeness(current_user),
                         role_description=get_role_description(current_user.role))

@profile_bp.route('/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """Enhanced profile editing with comprehensive validation and security"""
    # FIXED: Local imports
    from models.audit import AuditLog
    
    if request.method == 'POST':
        try:
            # Store old values for audit
            old_values = {
                'first_name': current_user.first_name,
                'last_name': current_user.last_name,
                'email': current_user.email,
                'phone': getattr(current_user, 'phone', ''),
                'timezone': getattr(current_user, 'timezone', ''),
                'language': getattr(current_user, 'language', '')
            }
            
            # Update basic profile information
            current_user.first_name = request.form.get('first_name', '').strip()
            current_user.last_name = request.form.get('last_name', '').strip()
            
            # Email validation and uniqueness check
            new_email = request.form.get('email', '').strip()
            if new_email != current_user.email:
                # FIXED: Local import inside condition
                from models.user import User
                existing_user = User.query.filter_by(email=new_email).first()
                if existing_user:
                    flash('Email address already exists. Please use a different email.', 'error')
                    return render_template('profile/edit.html',
                                         user=current_user,
                                         available_timezones=get_available_timezones(),
                                         available_languages=get_available_languages())
                current_user.email = new_email
            
            # Update optional fields if they exist
            if hasattr(current_user, 'phone'):
                current_user.phone = request.form.get('phone', '').strip()
            
            if hasattr(current_user, 'timezone'):
                current_user.timezone = request.form.get('timezone', 'UTC')
            
            if hasattr(current_user, 'language'):
                current_user.language = request.form.get('language', 'en')
            
            # Handle preferences
            preferences = {}
            if request.form.get('email_notifications'):
                preferences['email_notifications'] = True
            if request.form.get('sms_notifications'):
                preferences['sms_notifications'] = True
            if request.form.get('dashboard_widgets'):
                preferences['dashboard_widgets'] = request.form.getlist('dashboard_widgets')
            
            if hasattr(current_user, 'preferences'):
                current_user.preferences = preferences
            
            # Update last modified timestamp
            if hasattr(current_user, 'last_updated'):
                current_user.last_updated = datetime.utcnow()
            
            # Log the changes
            new_values = {
                'first_name': current_user.first_name,
                'last_name': current_user.last_name,
                'email': current_user.email,
                'phone': getattr(current_user, 'phone', ''),
                'timezone': getattr(current_user, 'timezone', ''),
                'language': getattr(current_user, 'language', '')
            }
            
            AuditLog.log_action(
                user_id=current_user.id,
                action='profile_updated',
                table_name='users',
                record_id=current_user.id,
                description=f'Profile updated for user: {current_user.username}',
                old_values=old_values,
                new_values=new_values
            )
            
            db.session.commit()
            
            flash('Your profile has been updated successfully.', 'success')
            return redirect(url_for('profile.view_profile'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error updating profile for user {current_user.id}: {e}')
            flash(f'Error updating profile: {str(e)}', 'error')
    
    # GET request - show form
    return render_template('profile/edit.html',
                         user=current_user,
                         available_timezones=get_available_timezones(),
                         available_languages=get_available_languages())

@profile_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Enhanced password change with comprehensive security validation"""
    # FIXED: Local imports
    from models.audit import AuditLog
    
    if request.method == 'POST':
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validate current password
        if not current_user.check_password(current_password):
            flash('Current password is incorrect.', 'error')
            
            # Log failed password change attempt
            AuditLog.log_action(
                user_id=current_user.id,
                action='password_change_failed',
                description=f'Failed password change attempt for {current_user.username} - incorrect current password',
                ip_address=request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR'))
            )
            
            return render_template('profile/change_password.html')
        
        # Validate new password confirmation
        if new_password != confirm_password:
            flash('New passwords do not match.', 'error')
            return render_template('profile/change_password.html')
        
        # Password strength validation
        password_errors = validate_password_strength(new_password)
        if password_errors:
            for error in password_errors:
                flash(error, 'error')
            return render_template('profile/change_password.html')
        
        # Check if new password is same as current
        if current_user.check_password(new_password):
            flash('New password must be different from your current password.', 'warning')
            return render_template('profile/change_password.html')
        
        try:
            # Update password
            current_user.set_password(new_password)
            
            # Update last modified timestamp
            if hasattr(current_user, 'last_updated'):
                current_user.last_updated = datetime.utcnow()
            
            if hasattr(current_user, 'last_password_change'):
                current_user.last_password_change = datetime.utcnow()
            
            # Reset failed login attempts
            current_user.failed_login_attempts = 0
            if hasattr(current_user, 'account_locked_until'):
                current_user.account_locked_until = None
            
            db.session.commit()
            
            # Log successful password change
            AuditLog.log_action(
                user_id=current_user.id,
                action='password_changed',
                description=f'User {current_user.username} successfully changed their password',
                ip_address=request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR'))
            )
            
            flash('Your password has been changed successfully!', 'success')
            return redirect(url_for('profile.view_profile'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error changing password for user {current_user.id}: {e}')
            flash(f'Error changing password: {str(e)}', 'error')
    
    return render_template('profile/change_password.html')

@profile_bp.route('/security')
@login_required
def security_dashboard():
    """Enhanced security dashboard with comprehensive information"""
    # FIXED: Local imports
    from models.audit import AuditLog
    
    # Get comprehensive security data
    security_data = get_comprehensive_security_data(current_user)
    
    # Get recent security events
    security_events = get_user_security_events(current_user.id, days=90)
    
    # Get login history
    login_history = get_user_login_history(current_user.id, limit=20)
    
    # Check for security alerts
    security_alerts = check_user_security_alerts(current_user)
    
    return render_template('profile/security.html',
                         user=current_user,
                         security_data=security_data,
                         security_events=security_events,
                         login_history=login_history,
                         security_alerts=security_alerts)

@profile_bp.route('/activity')
@login_required
def activity_log():
    """Enhanced user activity log with filtering and pagination"""
    # FIXED: Local imports
    from models.audit import AuditLog
    
    # Get filter parameters
    action_filter = request.args.get('action', 'all')
    days_filter = request.args.get('days', 30, type=int)
    page = request.args.get('page', 1, type=int)
    per_page = 25
    
    # Get paginated activities
    activities = get_user_activities_paginated(
        current_user.id, days_filter, action_filter, page, per_page
    )
    
    # Get activity summary
    activity_summary = get_user_activity_summary(current_user.id, days_filter)
    
    return render_template('profile/activity.html',
                         user=current_user,
                         activities=activities,
                         activity_summary=activity_summary,
                         action_filter=action_filter,
                         days_filter=days_filter)

@profile_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """User preferences and settings management"""
    if request.method == 'POST':
        try:
            # Update user preferences
            preferences = {}
            
            # Notification preferences
            preferences['email_notifications'] = request.form.get('email_notifications') == 'on'
            preferences['sms_notifications'] = request.form.get('sms_notifications') == 'on'
            preferences['push_notifications'] = request.form.get('push_notifications') == 'on'
            
            # Display preferences
            preferences['items_per_page'] = int(request.form.get('items_per_page', 25))
            preferences['default_date_range'] = request.form.get('default_date_range', '30')
            preferences['dashboard_layout'] = request.form.get('dashboard_layout', 'standard')
            
            # Theme preferences
            preferences['theme'] = request.form.get('theme', 'light')
            preferences['sidebar_collapsed'] = request.form.get('sidebar_collapsed') == 'on'
            
            # Update user preferences
            if hasattr(current_user, 'preferences'):
                current_user.preferences = preferences
            
            # Update timezone and language
            if hasattr(current_user, 'timezone'):
                current_user.timezone = request.form.get('timezone', 'UTC')
            
            if hasattr(current_user, 'language'):
                current_user.language = request.form.get('language', 'en')
            
            db.session.commit()
            
            flash('Settings updated successfully.', 'success')
            return redirect(url_for('profile.settings'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error updating settings for user {current_user.id}: {e}')
            flash(f'Error updating settings: {str(e)}', 'error')
    
    # Get current preferences
    current_preferences = getattr(current_user, 'preferences', {})
    
    return render_template('profile/settings.html',
                         user=current_user,
                         preferences=current_preferences,
                         available_timezones=get_available_timezones(),
                         available_languages=get_available_languages())

@profile_bp.route('/notifications')
@login_required
def notifications():
    """User notifications center"""
    # FIXED: Local imports
    from models.audit import AuditLog
    
    # Get recent important events
    important_events = get_user_important_events(current_user.id, days=7)
    
    # Get system announcements
    announcements = get_system_announcements(limit=5)
    
    # Get unread notification count
    unread_count = len([event for event in important_events if not event.get('read', True)])
    
    return render_template('profile/notifications.html',
                         user=current_user,
                         important_events=important_events,
                         announcements=announcements,
                         unread_count=unread_count)

@profile_bp.route('/export-data')
@login_required
def export_data():
    """Export user data for GDPR compliance"""
    try:
        # Compile user data
        user_data = compile_user_data_export(current_user)
        
        # Create response
        from flask import Response
        import json
        
        response_data = json.dumps(user_data, indent=2, default=str)
        
        return Response(
            response_data,
            mimetype='application/json',
            headers={'Content-Disposition': f'attachment; filename=user_data_{current_user.username}_{date.today().isoformat()}.json'}
        )
        
    except Exception as e:
        current_app.logger.error(f'Error exporting data for user {current_user.id}: {e}')
        flash('Error exporting data. Please try again.', 'error')
        return redirect(url_for('profile.view_profile'))

# Helper Functions

def validate_password_strength(password):
    """Validate password strength"""
    errors = []
    
    if len(password) < 8:
        errors.append("Password must be at least 8 characters long")
    
    if not any(c.isupper() for c in password):
        errors.append("Password must contain at least one uppercase letter")
    
    if not any(c.islower() for c in password):
        errors.append("Password must contain at least one lowercase letter")
    
    if not any(c.isdigit() for c in password):
        errors.append("Password must contain at least one number")
    
    if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        errors.append("Password must contain at least one special character")
    
    # Check for common passwords
    common_passwords = ['password', '123456', 'qwerty', 'admin', 'letmein']
    if password.lower() in common_passwords:
        errors.append("Password is too common")
    
    return errors

def get_user_recent_activities(user_id, days=30):
    """Get user's recent activities"""
    # FIXED: Local imports
    from models.audit import AuditLog
    
    try:
        since_date = datetime.utcnow() - timedelta(days=days)
        return AuditLog.query.filter(
            AuditLog.user_id == user_id,
            AuditLog.timestamp >= since_date
        ).order_by(desc(AuditLog.timestamp)).limit(10).all()
    except:
        return []

def get_user_security_summary(user):
    """Get user security summary"""
    last_password_change = getattr(user, 'last_password_change', datetime.utcnow())
    
    return {
        'password_strength': 'Strong' if (datetime.utcnow() - last_password_change).days < 90 else 'Needs Update',
        'password_age_days': (datetime.utcnow() - last_password_change).days if last_password_change else 0,
        'failed_login_attempts': user.failed_login_attempts,
        'account_locked': getattr(user, 'account_locked_until', None) is not None,
        'last_login': getattr(user, 'last_login', None),
        'two_factor_enabled': getattr(user, 'two_factor_enabled', False)
    }

def get_comprehensive_profile_data(user):
    """Get comprehensive profile data"""
    last_password_change = getattr(user, 'last_password_change', datetime.utcnow())
    created_at = getattr(user, 'created_date', datetime.utcnow())
    
    return {
        'account_age_days': (datetime.utcnow() - created_at).days,
        'last_password_change': last_password_change,
        'password_age_days': (datetime.utcnow() - last_password_change).days if last_password_change else 0,
        'total_logins': getattr(user, 'login_count', 0),
        'last_activity': getattr(user, 'last_activity', None),
        'profile_completion': calculate_profile_completeness(user)
    }

def get_comprehensive_security_data(user):
    """Get comprehensive security data"""
    return {
        'account_created': getattr(user, 'created_date', datetime.utcnow()),
        'password_last_changed': getattr(user, 'last_password_change', datetime.utcnow()),
        'failed_attempts': user.failed_login_attempts,
        'account_locked': getattr(user, 'account_locked_until', None) is not None,
        'two_factor_enabled': getattr(user, 'two_factor_enabled', False),
        'session_timeout': getattr(user, 'session_timeout', 3600),
        'password_expiry_days': 90
    }

def get_user_security_events(user_id, days=90):
    """Get user security events"""
    # FIXED: Local imports
    from models.audit import AuditLog
    
    try:
        since_date = datetime.utcnow() - timedelta(days=days)
        return AuditLog.query.filter(
            AuditLog.user_id == user_id,
            AuditLog.timestamp >= since_date,
            AuditLog.action.in_(['login_successful', 'login_failed', 'password_changed', 'logout'])
        ).order_by(desc(AuditLog.timestamp)).limit(20).all()
    except:
        return []

def get_user_login_history(user_id, limit=20):
    """Get user login history"""
    # FIXED: Local imports
    from models.audit import AuditLog
    
    try:
        return AuditLog.query.filter(
            AuditLog.user_id == user_id,
            AuditLog.action.in_(['login_successful', 'login_failed'])
        ).order_by(desc(AuditLog.timestamp)).limit(limit).all()
    except:
        return []

def check_user_security_alerts(user):
    """Check for security alerts"""
    alerts = []
    summary = get_user_security_summary(user)
    
    if summary['password_age_days'] > 90:
        alerts.append({'type': 'warning', 'title': 'Password Aging', 'message': 'Password change is highly recommended.'})
    
    if summary['failed_login_attempts'] > 0:
        alerts.append({'type': 'error', 'title': 'Failed Logins', 'message': f'{summary["failed_login_attempts"]} failed attempts recorded.'})
    
    if summary['account_locked']:
        alerts.append({'type': 'error', 'title': 'Account Locked', 'message': 'Your account is locked. Contact admin.'})
    
    return alerts

def get_user_activities_paginated(user_id, days=30, action_filter='all', page=1, per_page=25):
    """Get paginated user activities"""
    # FIXED: Local imports
    from models.audit import AuditLog
    
    try:
        since_date = datetime.utcnow() - timedelta(days=days)
        query = AuditLog.query.filter(
            AuditLog.user_id == user_id,
            AuditLog.timestamp >= since_date
        )
        
        if action_filter != 'all':
            query = query.filter(AuditLog.action.like(f'%{action_filter}%'))
        
        return query.order_by(desc(AuditLog.timestamp)).paginate(
            page=page, per_page=per_page, error_out=False
        )
    except:
        # Return empty pagination object
        from flask_sqlalchemy import Pagination
        return Pagination(None, page, per_page, 0, [])

def get_user_activity_summary(user_id, days=30):
    """Get user activity summary"""
    # FIXED: Local imports
    from models.audit import AuditLog
    
    try:
        since_date = datetime.utcnow() - timedelta(days=days)
        
        total_activities = AuditLog.query.filter(
            AuditLog.user_id == user_id,
            AuditLog.timestamp >= since_date
        ).count()
        
        login_count = AuditLog.query.filter(
            AuditLog.user_id == user_id,
            AuditLog.timestamp >= since_date,
            AuditLog.action == 'login_successful'
        ).count()
        
        profile_updates = AuditLog.query.filter(
            AuditLog.user_id == user_id,
            AuditLog.timestamp >= since_date,
            AuditLog.action == 'profile_updated'
        ).count()
        
        return {
            'total_activities': total_activities,
            'login_count': login_count,
            'profile_updates': profile_updates,
            'average_daily_activities': round(total_activities / days, 1) if days > 0 else 0
        }
    except:
        return {
            'total_activities': 0,
            'login_count': 0,
            'profile_updates': 0,
            'average_daily_activities': 0
        }

def get_user_important_events(user_id, days=7):
    """Get user important events"""
    # Mock implementation
    return [
        {'title': 'Leave Request Approved', 'time': '2 days ago', 'type': 'success', 'read': False},
        {'title': 'Profile Updated', 'time': '5 hours ago', 'type': 'info', 'read': True}
    ]

def get_system_announcements(limit=5):
    """Get system announcements"""
    # Mock implementation
    return [
        {'title': 'System Update v3.1', 'message': 'Scheduled for next week', 'type': 'info', 'date': datetime.utcnow()}
    ]

def compile_user_data_export(user):
    """Compile user data for export"""
    return {
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'role': user.role,
        'created_date': getattr(user, 'created_date', datetime.utcnow()).isoformat(),
        'last_login': getattr(user, 'last_login', None).isoformat() if getattr(user, 'last_login', None) else None,
        'preferences': getattr(user, 'preferences', {}),
        'export_date': datetime.utcnow().isoformat()
    }

def get_available_timezones():
    """Get available timezone options"""
    return [
        'UTC', 'Africa/Nairobi', 'America/New_York', 'Europe/London', 
        'Asia/Tokyo', 'Australia/Sydney'
    ]

def get_available_languages():
    """Get available language options"""
    return [
        ('en', 'English'),
        ('sw', 'Swahili'),
        ('fr', 'French'),
        ('es', 'Spanish')
    ]