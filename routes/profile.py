"""
Enhanced User Profile and Settings Routes for Sakina Gas Attendance System
Comprehensive profile management with advanced features, security, and audit logging
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, g
from flask_login import login_required, current_user
from models import db, User, Employee, AuditLog, AttendanceRecord, LeaveRequest
from datetime import date, datetime, timedelta
from sqlalchemy import func, desc
from werkzeug.utils import secure_filename
from config import Config
import os
import json

profile_bp = Blueprint('profile', __name__)

@profile_bp.route('/')
@login_required
def view_profile():
    """Enhanced user profile view with comprehensive information"""
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
            Employee.email == current_user.email
        ).first()
        
        if not associated_employee and current_user.role == 'station_manager':
            # For station managers, try to find by location and position
            associated_employee = Employee.query.filter(
                Employee.location == current_user.location,
                Employee.position.like('%Manager%'),
                Employee.is_active == True
            ).first()
    
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
            current_user.department = request.form.get('department', '').strip() or None
            
            # Update preferences
            current_user.timezone = request.form.get('timezone', 'Africa/Nairobi')
            current_user.language = request.form.get('language', 'en')
            
            # Handle preferences JSON
            preferences = {}
            if request.form.get('email_notifications'):
                preferences['email_notifications'] = True
            if request.form.get('dashboard_theme'):
                preferences['dashboard_theme'] = request.form.get('dashboard_theme')
            if request.form.get('items_per_page'):
                try:
                    preferences['items_per_page'] = int(request.form.get('items_per_page'))
                except ValueError:
                    preferences['items_per_page'] = 25
            
            current_user.set_preferences(preferences)
            
            # Update signature
            current_user.signature = request.form.get('signature', '').strip() or None
            
            # Only allow certain role/location changes
            if current_user.role == 'hr_manager':
                # HR managers can change their own department
                if request.form.get('department'):
                    current_user.department = request.form.get('department')
            
            # Set updated timestamp and user
            current_user.updated_at = datetime.utcnow()
            current_user.updated_by = current_user.id
            
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
            AuditLog.log_action(
                user_id=current_user.id,
                action='profile_updated',
                target_type='user',
                target_id=current_user.id,
                old_values=old_values,
                new_values=new_values,
                details=f'User {current_user.username} updated their profile',
                ip_address=getattr(g, 'ip_address', request.remote_addr)
            )
            
            flash('Your profile has been updated successfully!', 'success')
            return redirect(url_for('profile.view_profile'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating profile: {str(e)}', 'danger')
    
    # GET request - show form
    user_preferences = current_user.get_preferences()
    available_departments = list(Config.DEPARTMENTS.keys()) if hasattr(Config, 'DEPARTMENTS') else []
    
    return render_template('profile/edit.html',
                         user=current_user,
                         user_preferences=user_preferences,
                         available_departments=available_departments)

@profile_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Enhanced password change with comprehensive security validation"""
    if request.method == 'POST':
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validate current password
        if not current_user.check_password(current_password):
            flash('Current password is incorrect.', 'danger')
            
            # Log failed password change attempt
            AuditLog.log_action(
                user_id=current_user.id,
                action='password_change_failed',
                target_type='user',
                target_id=current_user.id,
                details=f'Failed password change attempt for {current_user.username} - incorrect current password',
                ip_address=getattr(g, 'ip_address', request.remote_addr),
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
        
        # Check if new password is same as current
        if current_user.check_password(new_password):
            flash('New password must be different from your current password.', 'warning')
            return render_template('profile/change_password.html')
        
        try:
            # Update password
            old_password_changed_at = current_user.password_changed_at
            current_user.set_password(new_password)
            current_user.updated_at = datetime.utcnow()
            
            # Reset failed login attempts
            current_user.failed_login_attempts = 0
            current_user.locked_until = None
            
            db.session.commit()
            
            # Log successful password change
            AuditLog.log_action(
                user_id=current_user.id,
                action='password_changed',
                target_type='user',
                target_id=current_user.id,
                details=f'User {current_user.username} successfully changed their password',
                ip_address=getattr(g, 'ip_address', request.remote_addr),
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
    """Enhanced user preferences and settings management"""
    if request.method == 'POST':
        try:
            # Get current preferences
            current_preferences = current_user.get_preferences()
            
            # Update preferences from form
            new_preferences = {
                'theme': request.form.get('theme', 'light'),
                'language': request.form.get('language', 'en'),
                'timezone': request.form.get('timezone', 'Africa/Nairobi'),
                'items_per_page': int(request.form.get('items_per_page', 25)),
                'email_notifications': {
                    'leave_requests': bool(request.form.get('email_leave_requests')),
                    'attendance_alerts': bool(request.form.get('email_attendance_alerts')),
                    'system_updates': bool(request.form.get('email_system_updates')),
                    'security_alerts': bool(request.form.get('email_security_alerts'))
                },
                'dashboard_widgets': {
                    'show_quick_stats': bool(request.form.get('show_quick_stats')),
                    'show_recent_activity': bool(request.form.get('show_recent_activity')),
                    'show_calendar': bool(request.form.get('show_calendar')),
                    'show_announcements': bool(request.form.get('show_announcements'))
                },
                'accessibility': {
                    'high_contrast': bool(request.form.get('high_contrast')),
                    'large_text': bool(request.form.get('large_text')),
                    'reduced_motion': bool(request.form.get('reduced_motion'))
                }
            }
            
            # Update user preferences
            current_user.set_preferences(new_preferences)
            current_user.language = new_preferences['language']
            current_user.timezone = new_preferences['timezone']
            current_user.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            # Log preferences update
            AuditLog.log_action(
                user_id=current_user.id,
                action='preferences_updated',
                target_type='user',
                target_id=current_user.id,
                details=f'User {current_user.username} updated their preferences',
                ip_address=getattr(g, 'ip_address', request.remote_addr)
            )
            
            flash('Your preferences have been updated successfully!', 'success')
            return redirect(url_for('profile.preferences'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating preferences: {str(e)}', 'danger')
    
    # GET request - show preferences form
    user_preferences = current_user.get_preferences()
    
    return render_template('profile/preferences.html',
                         user=current_user,
                         preferences=user_preferences)

@profile_bp.route('/activity')
@login_required
def activity_log():
    """User activity log with filtering"""
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
        per_page=25
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
    # This would integrate with a notification system
    # For now, show recent important activities
    
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
    try:
        # Compile user data
        user_data = compile_user_data_export(current_user)
        
        # Log data export request
        AuditLog.log_action(
            user_id=current_user.id,
            action='data_export_requested',
            target_type='user',
            target_id=current_user.id,
            details=f'User {current_user.username} requested data export',
            ip_address=getattr(g, 'ip_address', request.remote_addr),
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

# Helper Functions

def get_comprehensive_profile_data(user):
    """Get comprehensive profile data for user"""
    profile_data = {
        'account_age_days': (datetime.utcnow() - user.created_at).days,
        'last_password_change': user.password_changed_at,
        'password_age_days': (datetime.utcnow() - user.password_changed_at).days if user.password_changed_at else None,
        'total_logins': user.login_count,
        'account_status': 'Active' if user.is_active and not user.is_locked else ('Locked' if user.is_locked else 'Inactive'),
        'role_description': get_role_description(user.role),
        'location_info': get_location_info(user.location),
        'preferences': user.get_preferences(),
        'profile_completeness': calculate_profile_completeness(user)
    }
    
    return profile_data

def get_user_recent_activities(user_id, days=30):
    """Get user's recent activities"""
    since_date = datetime.utcnow() - timedelta(days=days)
    
    activities = AuditLog.query.filter(
        AuditLog.user_id == user_id,
        AuditLog.timestamp >= since_date
    ).order_by(desc(AuditLog.timestamp)).limit(10).all()
    
    return activities

def get_user_security_summary(user):
    """Get security summary for user"""
    summary = {
        'password_strength': 'Strong' if user.password_changed_at and 
                           (datetime.utcnow() - user.password_changed_at).days < 90 else 'Needs Update',
        'failed_login_attempts': user.failed_login_attempts,
        'account_locked': user.is_locked,
        'last_login': user.last_login,
        'two_factor_enabled': False,  # Placeholder for future 2FA implementation
        'security_score': calculate_security_score(user)
    }
    
    return summary

def get_comprehensive_security_data(user):
    """Get comprehensive security data"""
    return {
        'password_last_changed': user.password_changed_at,
        'password_age_days': (datetime.utcnow() - user.password_changed_at).days if user.password_changed_at else None,
        'failed_login_attempts': user.failed_login_attempts,
        'account_locked': user.is_locked,
        'locked_until': user.locked_until,
        'last_login': user.last_login,
        'total_logins': user.login_count,
        'account_created': user.created_at,
        'two_factor_enabled': False,  # Placeholder
        'trusted_devices': [],  # Placeholder for future implementation
        'security_score': calculate_security_score(user),
        'recent_ip_addresses': get_user_recent_ips(user.id, days=30)
    }

def get_user_security_events(user_id, days=90):
    """Get user security-related events"""
    since_date = datetime.utcnow() - timedelta(days=days)
    
    security_events = AuditLog.query.filter(
        AuditLog.user_id == user_id,
        AuditLog.timestamp >= since_date,
        AuditLog.action.in_([
            'login_success', 'login_failure', 'logout', 
            'password_changed', 'password_change_failed',
            'profile_updated', 'preferences_updated'
        ])
    ).order_by(desc(AuditLog.timestamp)).limit(50).all()
    
    return security_events

def get_user_login_history(user_id, limit=20):
    """Get user login history"""
    login_history = AuditLog.query.filter(
        AuditLog.user_id == user_id,
        AuditLog.action.in_(['login_success', 'logout'])
    ).order_by(desc(AuditLog.timestamp)).limit(limit).all()
    
    return login_history

def check_user_security_alerts(user):
    """Check for security alerts for user"""
    alerts = []
    
    # Password age check
    if user.password_changed_at:
        password_age = (datetime.utcnow() - user.password_changed_at).days
        if password_age > 90:
            alerts.append({
                'type': 'warning',
                'title': 'Password Age',
                'message': f'Your password is {password_age} days old. Consider changing it.',
                'action': 'change_password'
            })
    
    # Failed login attempts
    if user.failed_login_attempts > 3:
        alerts.append({
            'type': 'danger',
            'title': 'Failed Login Attempts',
            'message': f'There have been {user.failed_login_attempts} failed login attempts on your account.',
            'action': 'review_security'
        })
    
    # Account locked
    if user.is_locked:
        alerts.append({
            'type': 'danger',
            'title': 'Account Locked',
            'message': 'Your account is currently locked. Contact your administrator.',
            'action': 'contact_admin'
        })
    
    return alerts

def get_user_activities_paginated(user_id, days=30, action_filter='all', page=1, per_page=25):
    """Get paginated user activities"""
    since_date = datetime.utcnow() - timedelta(days=days)
    
    query = AuditLog.query.filter(
        AuditLog.user_id == user_id,
        AuditLog.timestamp >= since_date
    )
    
    if action_filter != 'all':
        query = query.filter(AuditLog.action.like(f'%{action_filter}%'))
    
    activities = query.order_by(desc(AuditLog.timestamp)).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return activities

def get_user_activity_summary(user_id, days=30):
    """Get user activity summary"""
    since_date = datetime.utcnow() - timedelta(days=days)
    
    # Count different types of activities
    total_activities = AuditLog.query.filter(
        AuditLog.user_id == user_id,
        AuditLog.timestamp >= since_date
    ).count()
    
    login_count = AuditLog.query.filter(
        AuditLog.user_id == user_id,
        AuditLog.timestamp >= since_date,
        AuditLog.action == 'login_success'
    ).count()
    
    profile_updates = AuditLog.query.filter(
        AuditLog.user_id == user_id,
        AuditLog.timestamp >= since_date,
        AuditLog.action.like('%profile%')
    ).count()
    
    return {
        'total_activities': total_activities,
        'login_count': login_count,
        'profile_updates': profile_updates,
        'average_daily_activities': round(total_activities / days, 1) if days > 0 else 0
    }

def validate_password_strength(password):
    """Comprehensive password strength validation"""
    errors = []
    
    if len(password) < 8:
        errors.append("Password must be at least 8 characters long")
    
    if not any(c.isupper() for c in password):
        errors.append("Password must contain at least one uppercase letter")
    
    if not any(c.islower() for c in password):
        errors.append("Password must contain at least one lowercase letter")
    
    if not any(c.isdigit() for c in password):
        errors.append("Password must contain at least one number")
    
    if not any(c in '!@#$%^&*(),.?":{}|<>' for c in password):
        errors.append("Password must contain at least one special character")
    
    # Check against common passwords (basic implementation)
    common_passwords = ['password', '123456', 'admin', 'user', 'guest', 'root']
    if password.lower() in common_passwords:
        errors.append("Password is too common. Please choose a more secure password")
    
    return errors

def get_role_description(role):
    """Get role description"""
    role_descriptions = {
        'hr_manager': 'Human Resources Manager - Full system access',
        'station_manager': 'Station Manager - Location-specific access',
        'admin': 'System Administrator - Complete system control',
        'employee': 'Employee - Basic access'
    }
    return role_descriptions.get(role, 'Unknown Role')

def get_location_info(location):
    """Get location information"""
    if hasattr(Config, 'COMPANY_LOCATIONS') and location:
        return Config.COMPANY_LOCATIONS.get(location, {})
    return {}

def calculate_profile_completeness(user):
    """Calculate profile completeness percentage"""
    total_fields = 10
    completed_fields = 0
    
    if user.first_name: completed_fields += 1
    if user.last_name: completed_fields += 1
    if user.email: completed_fields += 1
    if user.phone: completed_fields += 1
    if user.department: completed_fields += 1
    if user.signature: completed_fields += 1
    if user.preferences: completed_fields += 1
    if user.timezone != 'Africa/Nairobi': completed_fields += 1  # Non-default timezone
    if user.password_changed_at: completed_fields += 1
    completed_fields += 1  # Username is always present
    
    return round((completed_fields / total_fields) * 100)

def calculate_security_score(user):
    """Calculate user security score"""
    score = 0
    
    # Password age (0-30 points)
    if user.password_changed_at:
        password_age = (datetime.utcnow() - user.password_changed_at).days
        if password_age < 30:
            score += 30
        elif password_age < 90:
            score += 20
        else:
            score += 10
    
    # Failed login attempts (0-20 points)
    if user.failed_login_attempts == 0:
        score += 20
    elif user.failed_login_attempts < 3:
        score += 10
    
    # Account status (0-20 points)
    if user.is_active and not user.is_locked:
        score += 20
    
    # Login activity (0-30 points)
    if user.last_login:
        days_since_login = (datetime.utcnow() - user.last_login).days
        if days_since_login < 7:
            score += 30
        elif days_since_login < 30:
            score += 20
        else:
            score += 10
    
    return min(score, 100)  # Cap at 100

def get_user_recent_ips(user_id, days=30):
    """Get user's recent IP addresses"""
    since_date = datetime.utcnow() - timedelta(days=days)
    
    # Get unique IP addresses from recent audit logs
    recent_ips = db.session.query(AuditLog.ip_address).filter(
        AuditLog.user_id == user_id,
        AuditLog.timestamp >= since_date,
        AuditLog.ip_address.isnot(None)
    ).distinct().all()
    
    return [ip[0] for ip in recent_ips if ip[0]]

def get_user_important_events(user_id, days=7):
    """Get important events for user notifications"""
    since_date = datetime.utcnow() - timedelta(days=days)
    
    # Get important events like approvals, rejections, etc.
    important_events = AuditLog.query.filter(
        AuditLog.user_id == user_id,
        AuditLog.timestamp >= since_date,
        AuditLog.action.in_([
            'leave_approved', 'leave_rejected', 'employee_created',
            'performance_review_completed', 'disciplinary_action_recorded'
        ])
    ).order_by(desc(AuditLog.timestamp)).limit(10).all()
    
    return important_events

def get_system_announcements(limit=5):
    """Get system announcements (placeholder for future implementation)"""
    # This would typically come from an announcements table
    # For now, return some sample announcements
    return [
        {
            'id': 1,
            'title': 'System Maintenance Scheduled',
            'message': 'System maintenance is scheduled for this weekend.',
            'type': 'info',
            'created_at': datetime.utcnow() - timedelta(days=1)
        }
    ]

def compile_user_data_export(user):
    """Compile user data for export (GDPR compliance)"""
    return {
        'personal_info': {
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'middle_name': user.middle_name,
            'phone': user.phone,
            'role': user.role,
            'location': user.location,
            'department': user.department
        },
        'account_info': {
            'created_at': user.created_at.isoformat(),
            'last_login': user.last_login.isoformat() if user.last_login else None,
            'login_count': user.login_count,
            'timezone': user.timezone,
            'language': user.language
        },
        'preferences': user.get_preferences(),
        'security_info': {
            'password_changed_at': user.password_changed_at.isoformat() if user.password_changed_at else None,
            'failed_login_attempts': user.failed_login_attempts,
            'is_locked': user.is_locked
        }
    }

# API Endpoints for AJAX requests

@profile_bp.route('/api/check-email', methods=['POST'])
@login_required
def api_check_email():
    """Check if email is available"""
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
    data = request.get_json()
    password = data.get('password', '')
    
    errors = validate_password_strength(password)
    
    return jsonify({
        'valid': len(errors) == 0,
        'errors': errors,
        'strength_score': calculate_password_strength_score(password)
    })

def calculate_password_strength_score(password):
    """Calculate password strength score (0-100)"""
    score = 0
    
    # Length bonus
    if len(password) >= 8:
        score += 20
    if len(password) >= 12:
        score += 10
    
    # Character variety
    if any(c.isupper() for c in password):
        score += 15
    if any(c.islower() for c in password):
        score += 15
    if any(c.isdigit() for c in password):
        score += 15
    if any(c in '!@#$%^&*(),.?":{}|<>' for c in password):
        score += 25
    
    return min(score, 100)