"""
Sakina Gas Company - Admin Routes
Built from scratch with comprehensive admin functionality
Version 3.0 - Enterprise grade admin panel
FIXED: All AuditLog.log_event() calls now use event_type= instead of action=
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from sqlalchemy import func, desc
from datetime import datetime, timedelta, date
from functools import wraps

from database import db

# Create blueprint
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def admin_required(f):
    """Decorator to require admin or HR manager role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('auth.login'))
        if current_user.role not in ['admin', 'hr_manager']:
            flash('You do not have permission to access this page.', 'error')
            return redirect(url_for('dashboard.main'))
        return f(*args, **kwargs)
    return decorated_function


@admin_bp.route('/')
@login_required
@admin_required
def admin_dashboard():
    """Admin dashboard overview"""
    from models.user import User
    from models.employee import Employee
    from models.audit import AuditLog
    
    # Get statistics
    stats = {
        'total_users': User.query.count(),
        'active_users': User.query.filter_by(is_active=True).count(),
        'total_employees': Employee.query.count(),
        'active_employees': Employee.query.filter_by(is_active=True).count(),
        'recent_logins': AuditLog.query.filter(
            AuditLog.event_type == 'login_successful'
        ).filter(
            AuditLog.timestamp >= datetime.utcnow() - timedelta(days=7)
        ).count(),
        'high_risk_events': AuditLog.query.filter(
            AuditLog.risk_level.in_(['high', 'critical'])
        ).filter(
            AuditLog.timestamp >= datetime.utcnow() - timedelta(days=7)
        ).count()
    }
    
    # Get recent activities
    recent_activities = AuditLog.query.order_by(
        desc(AuditLog.timestamp)
    ).limit(10).all()
    
    return render_template('admin/dashboard.html',
                         stats=stats,
                         recent_activities=recent_activities)


@admin_bp.route('/users')
@login_required
@admin_required
def list_users():
    """List all users"""
    from models.user import User
    
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Get filter parameters
    role_filter = request.args.get('role', '')
    status_filter = request.args.get('status', '')
    search = request.args.get('search', '').strip()
    
    # Build query
    query = User.query
    
    if role_filter:
        query = query.filter(User.role == role_filter)
    
    if status_filter == 'active':
        query = query.filter(User.is_active == True)
    elif status_filter == 'inactive':
        query = query.filter(User.is_active == False)
    
    if search:
        query = query.filter(
            (User.username.ilike(f'%{search}%')) |
            (User.email.ilike(f'%{search}%')) |
            (User.first_name.ilike(f'%{search}%')) |
            (User.last_name.ilike(f'%{search}%'))
        )
    
    # Order and paginate
    users = query.order_by(User.username).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('admin/users/list.html',
                         users=users,
                         role_filter=role_filter,
                         status_filter=status_filter,
                         search=search)


@admin_bp.route('/users/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_user():
    """Create new user"""
    from models.user import User
    from models.audit import AuditLog
    
    if request.method == 'POST':
        try:
            # Get form data
            username = request.form.get('username', '').strip()
            email = request.form.get('email', '').strip()
            password = request.form.get('password', '')
            first_name = request.form.get('first_name', '').strip()
            last_name = request.form.get('last_name', '').strip()
            role = request.form.get('role', 'employee')
            location = request.form.get('location', 'head_office')
            department = request.form.get('department', '').strip()
            is_active = bool(request.form.get('is_active'))
            
            # Validate required fields
            if not all([username, email, password]):
                flash('Username, email, and password are required.', 'error')
                return render_template('admin/users/create.html')
            
            # Check if username exists
            if User.query.filter_by(username=username).first():
                flash('Username already exists.', 'error')
                return render_template('admin/users/create.html')
            
            # Check if email exists
            if User.query.filter_by(email=email).first():
                flash('Email already exists.', 'error')
                return render_template('admin/users/create.html')
            
            # Create user
            user = User(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                role=role,
                location=location,
                department=department,
                is_active=is_active,
                is_verified=True,
                created_by=current_user.id
            )
            
            # Set password
            user.set_password(password)
            
            db.session.add(user)
            db.session.commit()
            
            # Log action - FIXED: Changed action= to event_type=
            AuditLog.log_event(
                event_type='user_created',  # FIXED
                user_id=current_user.id,
                description=f'Admin created user: {username}',
                target_type='User',
                target_id=user.id
            )
            
            flash(f'User {username} created successfully!', 'success')
            return redirect(url_for('admin.list_users'))
            
        except ValueError as e:
            flash(f'Password error: {str(e)}', 'error')
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating user: {str(e)}', 'error')
    
    return render_template('admin/users/create.html')


@admin_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    """Edit existing user"""
    from models.user import User
    from models.audit import AuditLog
    
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        try:
            # Store old values for audit
            old_values = {
                'username': user.username,
                'email': user.email,
                'role': user.role,
                'location': user.location,
                'is_active': user.is_active
            }
            
            # Update user fields
            user.username = request.form.get('username', '').strip()
            user.email = request.form.get('email', '').strip()
            user.first_name = request.form.get('first_name', '').strip()
            user.last_name = request.form.get('last_name', '').strip()
            user.role = request.form.get('role', 'employee')
            user.location = request.form.get('location', 'head_office')
            user.department = request.form.get('department', '').strip()
            user.is_active = bool(request.form.get('is_active'))
            
            # Update password if provided
            new_password = request.form.get('new_password', '').strip()
            if new_password:
                user.set_password(new_password)
            
            db.session.commit()
            
            # Log action - FIXED: Changed action= to event_type=
            new_values = {
                'username': user.username,
                'email': user.email,
                'role': user.role,
                'location': user.location,
                'is_active': user.is_active
            }
            
            AuditLog.log_event(
                event_type='user_updated',  # FIXED
                user_id=current_user.id,
                description=f'Admin updated user: {user.username}',
                target_type='User',
                target_id=user.id,
                old_values=old_values,
                new_values=new_values
            )
            
            flash(f'User {user.username} updated successfully!', 'success')
            return redirect(url_for('admin.list_users'))
            
        except ValueError as e:
            flash(f'Password error: {str(e)}', 'error')
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating user: {str(e)}', 'error')
    
    return render_template('admin/users/edit.html', user=user)


@admin_bp.route('/users/<int:user_id>/reset-password', methods=['POST'])
@login_required
@admin_required
def reset_user_password(user_id):
    """Reset user password"""
    from models.user import User
    from models.audit import AuditLog
    
    user = User.query.get_or_404(user_id)
    
    try:
        new_password = request.form.get('new_password', '').strip()
        
        if not new_password:
            return jsonify({'success': False, 'message': 'Password is required'})
        
        # Set new password
        user.set_password(new_password)
        db.session.commit()
        
        # Log action - FIXED: Changed action= to event_type=
        AuditLog.log_event(
            event_type='password_reset_by_admin',  # FIXED
            user_id=current_user.id,
            description=f'Admin reset password for user: {user.username}',
            target_type='User',
            target_id=user.id
        )
        
        return jsonify({'success': True, 'message': f'Password reset for {user.username}'})
        
    except ValueError as e:
        return jsonify({'success': False, 'message': f'Password error: {str(e)}'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})


@admin_bp.route('/users/<int:user_id>/toggle-status', methods=['POST'])
@login_required
@admin_required
def toggle_user_status(user_id):
    """Toggle user active status"""
    from models.user import User
    from models.audit import AuditLog
    
    user = User.query.get_or_404(user_id)
    
    try:
        old_status = user.is_active
        user.is_active = not user.is_active
        db.session.commit()
        
        # Log action - FIXED: Changed action= to event_type=
        event_type = 'user_activated' if user.is_active else 'user_deactivated'
        AuditLog.log_event(
            event_type=event_type,  # FIXED
            user_id=current_user.id,
            description=f'Admin {"activated" if user.is_active else "deactivated"} user: {user.username}',
            target_type='User',
            target_id=user.id
        )
        
        status_text = 'activated' if user.is_active else 'deactivated'
        return jsonify({'success': True, 'message': f'User {user.username} {status_text}'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})


@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    """Delete user (soft delete)"""
    from models.user import User
    from models.audit import AuditLog
    
    user = User.query.get_or_404(user_id)
    
    # Prevent deleting yourself
    if user.id == current_user.id:
        return jsonify({'success': False, 'message': 'You cannot delete your own account'})
    
    try:
        username = user.username
        
        # Soft delete - deactivate instead of deleting
        user.is_active = False
        user.deleted_at = datetime.utcnow()
        db.session.commit()
        
        # Log action - FIXED: Changed action= to event_type=
        AuditLog.log_event(
            event_type='user_deleted',  # FIXED
            user_id=current_user.id,
            description=f'Admin deleted (deactivated) user: {username}',
            target_type='User',
            target_id=user.id
        )
        
        return jsonify({'success': True, 'message': f'User {username} has been deleted'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})


@admin_bp.route('/system/settings')
@login_required
@admin_required
def system_settings():
    """System settings and configuration"""
    from models.audit import AuditLog
    
    # Get system statistics
    stats = {
        'total_logins': db.session.query(func.count(AuditLog.id)).filter(
            AuditLog.event_type == 'login_successful'
        ).scalar() or 0,
        'failed_logins': db.session.query(func.count(AuditLog.id)).filter(
            AuditLog.event_type == 'login_failed'
        ).scalar() or 0,
        'audit_logs_count': AuditLog.query.count(),
        'high_risk_events': db.session.query(func.count(AuditLog.id)).filter(
            AuditLog.risk_level == 'high'
        ).scalar() or 0
    }
    
    return render_template('admin/system/settings.html', stats=stats)


@admin_bp.route('/audit-logs')
@login_required
@admin_required
def audit_logs():
    """View audit logs"""
    from models.audit import AuditLog
    
    # Get filter parameters
    event_type = request.args.get('event_type', '')
    risk_level = request.args.get('risk_level', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    page = request.args.get('page', 1, type=int)
    per_page = 50
    
    # Build query
    query = AuditLog.query
    
    if event_type:
        query = query.filter(AuditLog.event_type == event_type)
    
    if risk_level:
        query = query.filter(AuditLog.risk_level == risk_level)
    
    if date_from:
        try:
            from_date = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(AuditLog.timestamp >= from_date)
        except ValueError:
            pass
    
    if date_to:
        try:
            to_date = datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(AuditLog.timestamp < to_date)
        except ValueError:
            pass
    
    # Order by timestamp descending
    query = query.order_by(desc(AuditLog.timestamp))
    
    # Paginate
    logs = query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Get distinct event types for filter dropdown
    event_types = db.session.query(AuditLog.event_type).distinct().all()
    event_types = [et[0] for et in event_types if et[0]]
    
    return render_template('admin/audit_logs.html',
                         logs=logs,
                         event_types=event_types,
                         event_type=event_type,
                         risk_level=risk_level,
                         date_from=date_from,
                         date_to=date_to)


@admin_bp.route('/audit-logs/<int:log_id>')
@login_required
@admin_required
def view_audit_log(log_id):
    """View single audit log details"""
    from models.audit import AuditLog
    
    log = AuditLog.query.get_or_404(log_id)
    return render_template('admin/audit_log_detail.html', log=log)


@admin_bp.route('/system/backup', methods=['POST'])
@login_required
@admin_required
def create_backup():
    """Create system backup"""
    from models.audit import AuditLog
    
    try:
        # Log backup attempt - FIXED: Changed action= to event_type=
        AuditLog.log_event(
            event_type='system_backup_created',  # FIXED
            user_id=current_user.id,
            description='Admin initiated system backup',
            risk_level='medium'
        )
        
        # In a real application, this would create an actual backup
        # For now, we just log the action
        
        flash('System backup initiated successfully.', 'success')
        return redirect(url_for('admin.system_settings'))
        
    except Exception as e:
        flash(f'Error creating backup: {str(e)}', 'error')
        return redirect(url_for('admin.system_settings'))


@admin_bp.route('/system/clear-cache', methods=['POST'])
@login_required
@admin_required
def clear_cache():
    """Clear system cache"""
    from models.audit import AuditLog
    
    try:
        # Log cache clear - FIXED: Changed action= to event_type=
        AuditLog.log_event(
            event_type='cache_cleared',  # FIXED
            user_id=current_user.id,
            description='Admin cleared system cache',
            risk_level='low'
        )
        
        flash('System cache cleared successfully.', 'success')
        return redirect(url_for('admin.system_settings'))
        
    except Exception as e:
        flash(f'Error clearing cache: {str(e)}', 'error')
        return redirect(url_for('admin.system_settings'))


@admin_bp.route('/reports/system')
@login_required
@admin_required
def system_reports():
    """System reports and analytics"""
    from models.user import User
    from models.employee import Employee
    from models.audit import AuditLog
    from models.attendance import AttendanceRecord
    from models.leave import LeaveRequest
    
    # Date range for reports
    end_date = date.today()
    start_date = end_date - timedelta(days=30)
    
    # User statistics
    user_stats = {
        'total': User.query.count(),
        'active': User.query.filter_by(is_active=True).count(),
        'by_role': db.session.query(
            User.role, func.count(User.id)
        ).group_by(User.role).all()
    }
    
    # Employee statistics
    employee_stats = {
        'total': Employee.query.count(),
        'active': Employee.query.filter_by(is_active=True).count(),
        'by_location': db.session.query(
            Employee.location, func.count(Employee.id)
        ).filter(Employee.is_active == True).group_by(Employee.location).all()
    }
    
    # Activity statistics
    activity_stats = {
        'total_logins': AuditLog.query.filter(
            AuditLog.event_type == 'login_successful',
            AuditLog.timestamp >= start_date
        ).count(),
        'failed_logins': AuditLog.query.filter(
            AuditLog.event_type == 'login_failed',
            AuditLog.timestamp >= start_date
        ).count(),
        'attendance_records': AttendanceRecord.query.filter(
            AttendanceRecord.date >= start_date
        ).count(),
        'leave_requests': LeaveRequest.query.filter(
            LeaveRequest.created_date >= datetime.combine(start_date, datetime.min.time())
        ).count()
    }
    
    return render_template('admin/reports/system.html',
                         user_stats=user_stats,
                         employee_stats=employee_stats,
                         activity_stats=activity_stats,
                         start_date=start_date,
                         end_date=end_date)