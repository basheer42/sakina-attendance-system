"""
User Profile and Settings routes for Sakina Gas Attendance System
Allows users to manage their personal information and passwords
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, User
from werkzeug.security import check_password_hash
from sqlalchemy import select

profile_bp = Blueprint('profile', __name__)

@profile_bp.route('/')
@login_required
def view_profile():
    """View user profile"""
    return render_template('profile/view.html', user=current_user)

@profile_bp.route('/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """Edit user profile information"""
    if request.method == 'POST':
        # Update user information
        current_user.email = request.form['email']
        
        # Only HR Manager can change role/location
        if current_user.role == 'hr_manager':
            if request.form.get('role'):
                current_user.role = request.form['role']
            if request.form.get('location'):
                current_user.location = request.form['location']
        
        try:
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('profile.view_profile'))
        except Exception as e:
            db.session.rollback()
            flash('Error updating profile. Please try again.', 'error')
    
    return render_template('profile/edit.html', user=current_user)

@profile_bp.route('/change-password', methods=['GET', 'POST'])
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
            return render_template('profile/change_password.html')
        
        # Validate new password
        if len(new_password) < 6:
            flash('New password must be at least 6 characters long', 'error')
            return render_template('profile/change_password.html')
        
        if new_password != confirm_password:
            flash('New passwords do not match', 'error')
            return render_template('profile/change_password.html')
        
        # Update password
        current_user.set_password(new_password)
        
        try:
            db.session.commit()
            flash('Password changed successfully!', 'success')
            return redirect(url_for('profile.view_profile'))
        except Exception as e:
            db.session.rollback()
            flash('Error changing password. Please try again.', 'error')
    
    return render_template('profile/change_password.html')

@profile_bp.route('/settings')
@login_required
def settings():
    """User settings and preferences"""
    return render_template('profile/settings.html')