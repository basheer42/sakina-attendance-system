"""
Admin Routes for Sakina Gas Attendance System
Complete admin dashboard for user management, system settings, and administration
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from functools import wraps
from database import db
from datetime import datetime, timedelta
from sqlalchemy import func, desc, or_

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access the admin area.', 'error')
            return redirect(url_for('auth.login'))
        
        if current_user.role not in ['admin', 'hr_manager']:
            flash('You do not have permission to access the admin area.', 'error')
            return redirect(url_for('dashboard.main'))
        
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    """Admin dashboard overview"""
    # Local imports to prevent circular imports
    from models.user import User
    from models.employee import Employee
    from models.audit import AuditLog
    
    # System statistics
    total_users = User.query.count()
    active_users = User.query.filter_by(is_active=True).count()
    total_employees = Employee.query.count()
    active_employees = Employee.query.filter_by(is_active=True).count()
    
    # Recent activity
    recent_logins = User.query.filter(
        User.last_login.isnot(None)
    ).order_by(desc(User.last_login)).limit(10).all()
    
    recent_audit_logs = AuditLog.query.order_by(desc(AuditLog.timestamp)).limit(20).all()
    
    # Role distribution
    role_stats = db.session.query(
        User.role,
        func.count(User.id).label('count')
    ).group_by(User.role).all()
    
    # Location distribution  
    location_stats = db.session.query(
        User.location,
        func.count(User.id).label('count')
    ).group_by(User.location).all()
    
    return render_template('admin/dashboard.html',
                         total_users=total_users,
                         active_users=active_users,
                         total_employees=total_employees,
                         active_employees=active_employees,
                         recent_logins=recent_logins,
                         recent_audit_logs=recent_audit_logs,
                         role_stats=role_stats,
                         location_stats=location_stats)

@admin_bp.route('/users')
@login_required
@admin_required
def list_users():
    """List all users with filtering and search"""
    from models.user import User
    
    # Get filter parameters
    search_query = request.args.get('search', '').strip()
    role_filter = request.args.get('role', '')
    location_filter = request.args.get('location', '')
    status_filter = request.args.get('status', 'all')
    sort_by = request.args.get('sort_by', 'created_date')
    sort_order = request.args.get('sort_order', 'desc')
    page = request.args.get('page', 1, type=int)
    per_page = 25
    
    # Build query
    query = User.query
    
    # Apply search filter
    if search_query:
        search_pattern = f"%{search_query}%"
        query = query.filter(or_(
            User.username.ilike(search_pattern),
            User.email.ilike(search_pattern),
            User.first_name.ilike(search_pattern),
            User.last_name.ilike(search_pattern)
        ))
    
    # Apply role filter
    if role_filter and role_filter != 'all':
        query = query.filter(User.role == role_filter)
    
    # Apply location filter
    if location_filter and location_filter != 'all':
        query = query.filter(User.location == location_filter)
    
    # Apply status filter
    if status_filter == 'active':
        query = query.filter(User.is_active == True)
    elif status_filter == 'inactive':
        query = query.filter(User.is_active == False)
    
    # Apply sorting
    if hasattr(User, sort_by):
        sort_column = getattr(User, sort_by)
        if sort_order == 'desc':
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(sort_column)
    
    # Paginate results
    users = query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('admin/users/list.html',
                         users=users,
                         search_query=search_query,
                         role_filter=role_filter,
                         location_filter=location_filter,
                         status_filter=status_filter,
                         sort_by=sort_by,
                         sort_order=sort_order)

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
            first_name = request.form.get('first_name', '').strip()
            last_name = request.form.get('last_name', '').strip()
            role = request.form.get('role', 'employee')
            location = request.form.get('location', 'head_office')
            department = request.form.get('department', '').strip()
            password = request.form.get('password', '')
            is_active = bool(request.form.get('is_active'))
            
            # Validate required fields
            if not all([username, email, first_name, last_name, password]):
                flash('All required fields must be filled.', 'error')
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
            
            # Log action
            AuditLog.log_action(
                user_id=current_user.id,
                action='user_created',
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
            
            # Log action
            new_values = {
                'username': user.username,
                'email': user.email,
                'role': user.role,
                'location': user.location,
                'is_active': user.is_active
            }
            
            AuditLog.log_action(
                user_id=current_user.id,
                action='user_updated',
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
        
        # Log action
        AuditLog.log_action(
            user_id=current_user.id,
            action='password_reset',
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
        
        # Log action
        action = 'user_activated' if user.is_active else 'user_deactivated'
        AuditLog.log_action(
            user_id=current_user.id,
            action=action,
            description=f'Admin {"activated" if user.is_active else "deactivated"} user: {user.username}',
            target_type='User',
            target_id=user.id
        )
        
        status_text = 'activated' if user.is_active else 'deactivated'
        return jsonify({'success': True, 'message': f'User {user.username} {status_text}'})
        
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
            AuditLog.event_action == 'login'
        ).scalar() or 0,
        'failed_logins': db.session.query(func.count(AuditLog.id)).filter(
            AuditLog.event_action == 'login_failed'
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
    event_types = [et[0] for et in event_types]
    
    return render_template('admin/audit_logs.html',
                         logs=logs,
                         event_types=event_types,
                         event_type=event_type,
                         risk_level=risk_level,
                         date_from=date_from,
                         date_to=date_to)