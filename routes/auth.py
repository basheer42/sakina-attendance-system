"""
Authentication routes for Sakina Gas Attendance System
UPDATED: Fixed SQLAlchemy 2.0 deprecation warnings
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User
from urllib.parse import urlparse
from sqlalchemy import select

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.main'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        remember_me = request.form.get('remember_me', False)
        
        # FIXED: Using modern SQLAlchemy syntax
        user = db.session.execute(
            select(User).where(User.username == username)
        ).scalar_one_or_none()
        
        if user and user.check_password(password) and user.is_active:
            login_user(user, remember=remember_me)
            next_page = request.args.get('next')
            if not next_page or urlparse(next_page).netloc != '':
                next_page = url_for('dashboard.main')
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(next_page)
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully', 'info')
    return redirect(url_for('auth.login'))