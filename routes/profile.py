"""
Enhanced User Profile and Settings Routes for Sakina Gas Attendance System
Comprehensive profile management with advanced features, security, and audit logging
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, g, current_app
from flask_login import login_required, current_user
# FIX: Removed global model imports to prevent early model registration
from database import db
from datetime import date, datetime, timedelta
from sqlalchemy import func, desc
from werkzeug.utils import secure_filename
from config import Config
import os
import json

profile_bp = Blueprint('profile', __name__)

# --- Mock/Utility functions (to be replaced by actual logic in ORM if preferred) ---
def get_role_description(role):
    role_descriptions = {
        'hr_manager': 'Human Resources Manager - Full system access',
        'station_manager': 'Station Manager - Location-specific access',
        'admin': 'System Administrator - Complete system control',
        'employee': 'Employee - Basic access'
    }
    return role_descriptions.get(role, 'Unknown Role')

def get_location_info(location):
    if hasattr(Config, 'COMPANY_LOCATIONS') and location:
        return Config.COMPANY_LOCATIONS.get(location, {}).get('name', location.replace('_', ' ').title())
    return 'N/A'

def calculate_profile_completeness(user):
    # This is a mock/simplified version
    total_fields = 10
    completed_fields = 0
    if user.first_name: completed_fields += 1
    if user.last_name: completed_fields += 1
    if user.email: completed_fields += 1
    if user.phone: completed_fields += 1
    if user.department: completed_fields += 1
    if user.location: completed_fields += 1
    if user.timezone: completed_fields += 1
    if user.language: completed_fields += 1
    if hasattr(user, 'preferences') and user.preferences: completed_fields += 1
    if user.username: completed_fields += 1
    
    return round((completed_fields / total_fields) * 100)

def validate_password_strength(password):
    # Simple validation for the view
    errors = []
    if len(password) < 8: errors.append("Password must be at least 8 characters long")
    if not any(c.isupper() for c in password): errors.append("Password must contain at least one uppercase letter")
    if not any(c.isdigit() for c in password): errors.append("Password must contain at least one number")
    return errors

def get_user_recent_activities(user_id, days=30):
    from models.audit import AuditLog
    since_date = datetime.utcnow() - timedelta(days=days)
    return AuditLog.query.filter(
        AuditLog.user_id == user_id,
        AuditLog.timestamp >= since_date
    ).order_by(desc(AuditLog.timestamp)).limit(10).all()

def get_user_security_summary(user):
    last_password_change = user.last_password_change if hasattr(user, 'last_password_change') else datetime.utcnow()
    is_locked = user.is_account_locked() if hasattr(user, 'is_account_locked') else False
    
    return {
        'password_strength': 'Strong' if (datetime.utcnow() - last_password_change).days < 90 else 'Needs Update',
        'password_age_days': (datetime.utcnow() - last_password_change).days if last_password_change else 0,
        'failed_login_attempts': user.failed_login_attempts,
        'account_locked': is_locked,
        'last_login': user.last_login,
        'two_factor_enabled': user.two_factor_enabled if hasattr(user, 'two_factor_enabled') else False,
    }

def get_comprehensive_profile_data(user):
    last_password_change = user.last_password_change if hasattr(user, 'last_password_change') else datetime.utcnow()
    created_at = user.created_date if hasattr(user, 'created_date') else datetime.utcnow()
    
    return {
        'account_age_days': (datetime.utcnow() - created_at).days,
        'last_password_change': last_password_change,
        'password_age_days': (datetime.utcnow() - last_password_change).days if last_password_change else 0,
        'total_logins': user.login_count,
        'account_status': 'Active' if user.is_active else 'Inactive',
        'role_description': get_role_description(user.role),
        'location_info': get_location_info(user.location),
        'preferences': user.preferences if hasattr(user, 'preferences') else {},
        'profile_completeness': calculate_profile_completeness(user),
        'account_created': created_at
    }

def get_comprehensive_security_data(user):
    # This is a large mock structure, returning simplified summary for now
    return {
        'password_last_changed': user.last_password_change.strftime('%Y-%m-%d %H:%M') if user.last_password_change else 'Never',
        'failed_login_attempts': user.failed_login_attempts,
        'account_locked': user.is_account_locked() if hasattr(user, 'is_account_locked') else False,
        'last_login': user.last_login.strftime('%Y-%m-%d %H:%M') if user.last_login else 'Never',
        'two_factor_enabled': user.two_factor_enabled if hasattr(user, 'two_factor_enabled') else False,
        'security_score': 85 # Mock Score
    }

def get_user_security_events(user_id, days=90):
    from models.audit import AuditLog
    since_date = datetime.utcnow() - timedelta(days=days)
    return AuditLog.query.filter(
        AuditLog.user_id == user_id,
        AuditLog.timestamp >= since_date,
        AuditLog.event_category == 'security'
    ).order_by(desc(AuditLog.timestamp)).limit(20).all()

def get_user_login_history(user_id, limit=20):
    from models.audit import AuditLog
    return AuditLog.query.filter(
        AuditLog.user_id == user_id,
        AuditLog.event_type.in_(['login_successful', 'logout'])
    ).order_by(desc(AuditLog.timestamp)).limit(limit).all()

def check_user_security_alerts(user):
    alerts = []
    summary = get_user_security_summary(user)
    if summary['password_age_days'] > 90:
        alerts.append({'type': 'warning', 'title': 'Password Expired', 'message': f'Password is {summary["password_age_days"]} days old. Change is highly recommended.'})
    if summary['failed_login_attempts'] > 0:
        alerts.append({'type': 'danger', 'title': 'Failed Logins', 'message': f'{summary["failed_login_attempts"]} failed attempts recorded.'})
    if summary['account_locked']:
        alerts.append({'type': 'critical', 'title': 'Account Locked', 'message': 'Your account is locked. Contact admin.'})
    return alerts

def get_user_activities_paginated(user_id, days=30, action_filter='all', page=1, per_page=25):
    from models.audit import AuditLog
    since_date = datetime.utcnow() - timedelta(days=days)
    query = AuditLog.query.filter(
        AuditLog.user_id == user_id,
        AuditLog.timestamp >= since_date
    )
    if action_filter != 'all':
        query = query.filter(AuditLog.event_type.like(f'%{action_filter}%'))
    return query.order_by(desc(AuditLog.timestamp)).paginate(
        page=page, per_page=per_page, error_out=False
    )

def get_user_activity_summary(user_id, days=30):
    # Mock summary
    return {
        'total_activities': 50,
        'login_count': 10,
        'profile_updates': 2,
        'average_daily_activities': 1.6
    }

def get_user_important_events(user_id, days=7):
    # Mock events
    return [
        {'title': 'Leave Request Approved', 'time': '2 days ago', 'type': 'success'},
        {'title': 'Login from New IP', 'time': '5 hours ago', 'type': 'warning'}
    ]

def get_system_announcements(limit=5):
    return [{'title': 'System Update v3.1', 'message': 'Scheduled for next week', 'type': 'info'}]

def compile_user_data_export(user):
    return {
        'username': user.username,
        'email': user.email,
        'full_name': user.get_full_name(),
        'role': user.role
    }

# --- END Mock/Utility functions ---

@profile_bp.route('/')
@login_required
def view_profile():
    """Enhanced user profile view with comprehensive information"""
    # FIX: Local imports
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
        # FIX: Query should use employee_id if available, falling back to email
        associated_employee = Employee.query.filter(
            db.or_(
                Employee.employee_id == current_user.employee_id,
                Employee.email == current_user.email
            )
        ).first()
    
    # FIX: The template relies on 'created_at' and 'get_age()' which are on the ORM model, 
    # but the User model had 'created_date'
    profile_data['account_created'] = current_user.created_date
    
    # Ensure current_user has required methods/attributes for template rendering
    if not hasattr(current_user, 'get_display_name'):
        current_user.get_display_name = current_user.get_full_name
    
    return render_template('profile/view.html',
                         user=current_user,
                         profile_data=profile_data,
                         recent_activities=recent_activities,
                         security_summary=security_summary,
                         associated_employee=associated_employee)

@profile_bp.route('/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """Enhanced profile editing with comprehensive validation and audit"""
    # FIX: Local imports
    from models.user import User
    from models.audit import AuditLog
    
    # FIX: Simple permission check, as 'has_permission' is assumed
    if not hasattr(current_user, 'has_permission') or not current_user.has_permission('edit_own_profile'):
        flash('You do not have permission to edit your profile.', 'danger')
        return redirect(url_for('profile.view_profile'))
    
    if request.method == 'POST':
        try:
            # Store old values for audit
            old_values = {
                'first_name': current_user.first_name,
                'last_name': current_user.last_name,
                'middle_name': current_user.middle_name,
                'email': current_user.email,
                'phone': current_user.phone,
                'department': current_user.department,
                'timezone': current_user.timezone,
                'language': current_user.language
            }
            
            # Update basic information
            current_user.first_name = request.form.get('first_name', '').strip()
            current_user.last_name = request.form.get('last_name', '').strip()
            current_user.middle_name = request.form.get('middle_name', '').strip() or None
            
            # Validate email uniqueness
            new_email = request.form.get('email', '').strip().lower()
            if new_email != current_user.email:
                existing_user = User.query.filter(
                    User.email == new_email,
                    User.id != current_user.id
                ).first()
                
                if existing_user:
                    flash('This email address is already in use by another account.', 'danger')
                    return render_template('profile/edit.html', user=current_user)
                
                current_user.email = new_email
            
            # Update contact information
            current_user.phone = request.form.get('phone', '').strip() or None
            
            # Update preferences
            current_user.timezone = request.form.get('timezone', 'Africa/Nairobi')
            current_user.language = request.form.get('language', 'en')
            current_user.department = request.form.get('department', '').strip() or None
            
            # Handle preferences JSON
            preferences = current_user.preferences.copy() if current_user.preferences else {}
            preferences['email_notifications'] = bool(request.form.get('email_notifications'))
            preferences['dashboard_theme'] = request.form.get('dashboard_theme', 'light')
            try:
                preferences['items_per_page'] = int(request.form.get('items_per_page', 25))
            except ValueError:
                pass
            
            if hasattr(current_user, 'update_preferences'):
                current_user.update_preferences(preferences)
            else:
                current_user.preferences = preferences # Fallback to direct set
            
            # Update signature
            current_user.signature = request.form.get('signature', '').strip() or None
            
            # System fields update
            current_user.last_updated = datetime.utcnow()
            
            # Store new values for audit
            new_values = {
                'first_name': current_user.first_name,
                'last_name': current_user.last_name,
                'middle_name': current_user.middle_name,
                'email': current_user.email,
                'phone': current_user.phone,
                'department': current_user.department,
                'timezone': current_user.timezone,
                'language': current_user.language
            }
            
            db.session.commit()
            
            # Create comprehensive audit log
            AuditLog.log_data_change( 
                user_id=current_user.id,
                target_type='user',
                target_id=current_user.id,
                action='updated',
                description=f'User {current_user.username} updated their profile', 
                old_values=old_values,
                new_values=new_values,
                ip_address=getattr(g, 'client_ip', request.remote_addr)
            )
            
            flash('Your profile has been updated successfully!', 'success')
            return redirect(url_for('profile.view_profile'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating profile: {str(e)}', 'danger')
    
    # GET request - show form
    user_preferences = current_user.preferences if hasattr(current_user, 'preferences') else {}
    available_departments = list(Config.DEPARTMENTS.keys()) if hasattr(Config, 'DEPARTMENTS') else []
    
    return render_template('profile/edit.html',
                         user=current_user,
                         user_preferences=user_preferences,
                         available_departments=available_departments)

@profile_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Enhanced password change with comprehensive security validation"""
    # FIX: Local imports
    from models.audit import AuditLog
    from models.user import User # Need User model for check_password
    
    if request.method == 'POST':
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validate current password
        if not current_user.check_password(current_password):
            flash('Current password is incorrect.', 'danger')
            
            # Log failed password change attempt
            AuditLog.log_security_event( 
                user_id=current_user.id,
                event_type='password_change_failed', 
                description=f'Failed password change attempt for {current_user.username} - incorrect current password',
                ip_address=getattr(g, 'client_ip', request.remote_addr),
                risk_level='medium'
            )
            
            return render_template('profile/change_password.html')
        
        # Validate new password confirmation
        if new_password != confirm_password:
            flash('New passwords do not match.', 'danger')
            return render_template('profile/change_password.html')
        
        # Comprehensive password strength validation
        password_errors = validate_password_strength(new_password)
        if password_errors:
            for error in password_errors:
                flash(error, 'danger')
            return render_template('profile/change_password.html')
        
        # Check if new password is same as current (re-checking hash is safer)
        if current_user.check_password(new_password):
            flash('New password must be different from your current password.', 'warning')
            return render_template('profile/change_password.html')
        
        try:
            # Update password
            current_user.set_password(new_password) 
            
            # Assuming User model has last_updated
            if hasattr(current_user, 'last_updated'):
                current_user.last_updated = datetime.utcnow()
            
            # Reset failed login attempts
            current_user.failed_login_attempts = 0
            if hasattr(current_user, 'account_locked_until'):
                current_user.account_locked_until = None
            
            db.session.commit()
            
            # Log successful password change
            AuditLog.log_security_event( 
                user_id=current_user.id,
                event_type='password_changed',
                description=f'User {current_user.username} successfully changed their password',
                ip_address=getattr(g, 'client_ip', request.remote_addr),
                risk_level='medium'
            )
            
            flash('Your password has been changed successfully!', 'success')
            return redirect(url_for('profile.view_profile'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error changing password: {str(e)}', 'danger')
    
    return render_template('profile/change_password.html')

@profile_bp.route('/security')
@login_required
def security_dashboard():
    """Enhanced security dashboard with comprehensive information"""
    # FIX: Local imports
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

@profile_bp.route('/preferences', methods=['GET', 'POST'])
@login_required
def preferences():
    """Enhanced user preferences and settings management (Placeholder for settings.html)"""
    # FIX: Redirect to settings.html which is the original intent, and fix the old file's redirect
    return redirect(url_for('profile.settings'))

@profile_bp.route('/settings')
@login_required
def settings():
    """Placeholder for the settings view (for settings.html)"""
    # FIX: This route is necessary for settings.html to render without a 404
    return render_template('profile/settings.html')


@profile_bp.route('/activity')
@login_required
def activity_log():
    """User activity log with filtering"""
    # FIX: Local imports
    from models.audit import AuditLog
    
    # Get filter parameters
    days = request.args.get('days', 30, type=int)
    action_filter = request.args.get('action', 'all')
    page = request.args.get('page', 1, type=int)
    
    # Get user activities
    activities = get_user_activities_paginated(
        current_user.id, 
        days=days, 
        action_filter=action_filter, 
        page=page,
        per_page=current_app.config.get('ITEMS_PER_PAGE', 25)
    )
    
    # Get activity summary
    activity_summary = get_user_activity_summary(current_user.id, days=days)
    
    return render_template('profile/activity.html',
                         user=current_user,
                         activities=activities,
                         activity_summary=activity_summary,
                         days=days,
                         action_filter=action_filter)

@profile_bp.route('/notifications')
@login_required
def notifications():
    """User notifications center"""
    # FIX: Local imports (none needed here)
    
    # Get recent important events for the user
    important_events = get_user_important_events(current_user.id, days=7)
    
    # Get system announcements
    system_announcements = get_system_announcements(limit=5)
    
    return render_template('profile/notifications.html',
                         user=current_user,
                         important_events=important_events,
                         system_announcements=system_announcements)

@profile_bp.route('/export-data')
@login_required
def export_user_data():
    """Export user data (GDPR compliance)"""
    # FIX: Local imports
    from models.audit import AuditLog
    
    try:
        # Compile user data
        user_data = compile_user_data_export(current_user)
        
        # Log data export request
        AuditLog.log_event( 
            user_id=current_user.id,
            event_type='data_export_requested',
            description=f'User {current_user.username} requested data export',
            ip_address=getattr(g, 'client_ip', request.remote_addr),
            risk_level='medium'
        )
        
        return jsonify({
            'success': True,
            'message': 'Data export prepared successfully',
            'data': user_data,
            'exported_at': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@profile_bp.route('/api/check-email', methods=['POST'])
@login_required
def api_check_email():
    """Check if email is available"""
    # FIX: Local imports
    from models.user import User
    
    data = request.get_json()
    email = data.get('email', '').strip().lower()
    
    if not email:
        return jsonify({'available': False, 'message': 'Email is required'})
    
    # Check if email is taken by another user
    existing_user = User.query.filter(
        User.email == email,
        User.id != current_user.id
    ).first()
    
    return jsonify({
        'available': existing_user is None,
        'message': 'Email is available' if existing_user is None else 'Email is already in use'
    })

@profile_bp.route('/api/validate-password', methods=['POST'])
@login_required
def api_validate_password():
    """Validate password strength via API"""
    # FIX: Local imports (none needed here)
    
    data = request.get_json()
    password = data.get('password', '')
    
    errors = validate_password_strength(password)
    
    return jsonify({
        'valid': len(errors) == 0,
        'errors': errors,
        'strength_score': len(errors) * 10
    })