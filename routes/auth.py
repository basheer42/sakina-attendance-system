"""
Authentication routes for Sakina Gas Attendance System
Login, logout, and session management
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from models import db, User, AuditLog
from datetime import datetime

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.main'))
    
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        remember_me = bool(request.form.get('remember_me'))
        
        if not username or not password:
            flash('Please enter both username and password', 'error')
            return render_template('auth/login.html')
        
        # Find user
        user = db.session.execute(
            db.select(User).where(User.username == username, User.is_active == True)
        ).scalar_one_or_none()
        
        if user and user.check_password(password):
            # Successful login
            login_user(user, remember=remember_me)
            
            # Update last login time
            user.last_login = datetime.utcnow()
            
            # Log the login
            log_entry = AuditLog(
                user_id=user.id,
                action='login',
                details=f"User logged in from IP: {request.remote_addr}",
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent', '')[:255]
            )
            db.session.add(log_entry)
            
            try:
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                print(f"Error logging login: {e}")
            
            flash(f'Welcome back, {user.full_name}!', 'success')
            
            # Redirect to next page or dashboard
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('dashboard.main'))
        
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """User logout"""
    # Log the logout
    log_entry = AuditLog(
        user_id=current_user.id,
        action='logout',
        details=f"User logged out from IP: {request.remote_addr}",
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent', '')[:255]
    )
    db.session.add(log_entry)
    
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error logging logout: {e}")
    
    username = current_user.username
    logout_user()
    
    flash(f'You have been logged out successfully, {username}.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Change user password"""
    if request.method == 'POST':
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        
        # Validate current password
        if not current_user.check_password(current_password):
            flash('Current password is incorrect', 'error')
            return render_template('auth/change_password.html')
        
        # Validate new password
        if len(new_password) < 6:
            flash('New password must be at least 6 characters long', 'error')
            return render_template('auth/change_password.html')
        
        if new_password != confirm_password:
            flash('New passwords do not match', 'error')
            return render_template('auth/change_password.html')
        
        # Update password
        try:
            current_user.set_password(new_password)
            
            # Log the password change
            log_entry = AuditLog(
                user_id=current_user.id,
                action='change_password',
                details='User changed their password',
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent', '')[:255]
            )
            db.session.add(log_entry)
            db.session.commit()
            
            flash('Password changed successfully', 'success')
            return redirect(url_for('dashboard.main'))
            
        except Exception as e:
            db.session.rollback()
            flash('Error changing password. Please try again.', 'error')
            print(f"Error: {e}")
    
    return render_template('auth/change_password.html')