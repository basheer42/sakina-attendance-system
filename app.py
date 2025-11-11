#!/usr/bin/env python3
"""
Sakina Gas Company - Attendance Management System
Professional Grade Flask Application
Fixed Version - Resolves URL routing errors
"""

import os
from flask import Flask, render_template, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user, login_required
from datetime import datetime, date

def create_app():
    """Application factory pattern for better organization"""
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'sakina-gas-2024-secure-key-change-in-production')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///sakina_attendance.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['WTF_CSRF_ENABLED'] = True
    
    # Company configuration
    app.config['COMPANY_NAME'] = 'Sakina Gas Company'
    app.config['COMPANY_TAGLINE'] = 'Excellence in Energy Solutions'
    app.config['BRAND_COLORS'] = {
        'primary': '#1B4F72',
        'secondary': '#2E86AB',
        'success': '#28A745',
        'danger': '#DC3545',
        'warning': '#FFC107',
        'info': '#17A2B8'
    }
    
    # Initialize extensions
    from models import db
    db.init_app(app)
    
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    login_manager.session_protection = 'strong'
    
    @login_manager.user_loader
    def load_user(user_id):
        from models import User, db
        # Fixed: Using modern SQLAlchemy syntax
        return db.session.get(User, int(user_id))
    
    # Register blueprints with proper URL prefixes
    register_blueprints(app)
    
    # Error handlers
    register_error_handlers(app)
    
    # Context processors for templates
    register_context_processors(app)
    
    # Create database tables and default data
    with app.app_context():
        db.create_all()
        create_professional_defaults()
    
    # Root route
    @app.route('/')
    def index():
        """Professional landing page logic"""
        if current_user.is_authenticated:
            return redirect(url_for('dashboard.main'))
        return redirect(url_for('auth.login'))
    
    # Health check endpoint for monitoring
    @app.route('/health')
    def health_check():
        """System health check for monitoring"""
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'version': '2.0 Professional',
            'company': 'Sakina Gas Company'
        })
    
    return app

def register_blueprints(app):
    """Register all route blueprints with fixed routing"""
    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.employees import employees_bp
    from routes.attendance import attendance_bp
    from routes.leaves import leaves_bp
    
    # Register with proper URL prefixes
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(dashboard_bp, url_prefix='/')  # Main dashboard at root
    app.register_blueprint(employees_bp, url_prefix='/employees')
    app.register_blueprint(attendance_bp, url_prefix='/attendance')
    app.register_blueprint(leaves_bp, url_prefix='/leaves')

def register_error_handlers(app):
    """Register custom error handlers"""
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        from models import db
        db.session.rollback()
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('errors/403.html'), 403

def register_context_processors(app):
    """Register context processors for templates"""
    @app.context_processor
    def inject_globals():
        """Inject global variables for templates"""
        return {
            'company_name': app.config.get('COMPANY_NAME', 'Sakina Gas Company'),
            'company_tagline': app.config.get('COMPANY_TAGLINE', 'Excellence in Energy Solutions'),
            'brand_colors': app.config.get('BRAND_COLORS', {}),
            'current_year': datetime.now().year,
            'system_version': '2.0 Professional',
            'today': date.today()
        }
    
    # Template filters
    @app.template_filter('datetime_format')
    def datetime_format(value, format='%Y-%m-%d %H:%M'):
        """Format datetime for display"""
        if value is None:
            return ""
        return value.strftime(format)
    
    @app.template_filter('currency')
    def currency_format(value):
        """Format currency in Kenyan Shillings"""
        if value is None:
            return "KSh 0"
        return f"KSh {value:,.2f}"

def create_professional_defaults():
    """Create default users and sample data"""
    from models import db, User, Holiday
    from werkzeug.security import generate_password_hash
    
    # Create default users
    default_users = [
        {
            'username': 'hr_manager',
            'email': 'hr@sakinagas.com', 
            'role': 'hr_manager',
            'location': None,
            'first_name': 'HR',
            'last_name': 'Manager',
            'password': 'admin123'
        },
        {
            'username': 'dandora_manager',
            'email': 'dandora@sakinagas.com',
            'role': 'station_manager', 
            'location': 'dandora',
            'first_name': 'Dandora',
            'last_name': 'Manager',
            'password': 'manager123'
        },
        {
            'username': 'tassia_manager',
            'email': 'tassia@sakinagas.com',
            'role': 'station_manager',
            'location': 'tassia', 
            'first_name': 'Tassia',
            'last_name': 'Manager',
            'password': 'manager123'
        },
        {
            'username': 'kiambu_manager',
            'email': 'kiambu@sakinagas.com',
            'role': 'station_manager',
            'location': 'kiambu',
            'first_name': 'Kiambu',
            'last_name': 'Manager',
            'password': 'manager123'
        }
    ]
    
    for user_data in default_users:
        # Check if user already exists
        existing_user = db.session.execute(
            db.select(User).where(User.username == user_data['username'])
        ).scalar_one_or_none()
        
        if not existing_user:
            user = User(
                username=user_data['username'],
                email=user_data['email'],
                role=user_data['role'],
                location=user_data['location'],
                first_name=user_data['first_name'],
                last_name=user_data['last_name']
            )
            user.set_password(user_data['password'])
            db.session.add(user)
    
    # Create default holidays (Kenyan holidays)
    default_holidays = [
        {'name': 'New Year Day', 'date': date(2024, 1, 1)},
        {'name': 'Good Friday', 'date': date(2024, 3, 29)},
        {'name': 'Easter Monday', 'date': date(2024, 4, 1)},
        {'name': 'Labour Day', 'date': date(2024, 5, 1)},
        {'name': 'Madaraka Day', 'date': date(2024, 6, 1)},
        {'name': 'Mashujaa Day', 'date': date(2024, 10, 20)},
        {'name': 'Jamhuri Day', 'date': date(2024, 12, 12)},
        {'name': 'Christmas Day', 'date': date(2024, 12, 25)},
        {'name': 'Boxing Day', 'date': date(2024, 12, 26)},
    ]
    
    for holiday_data in default_holidays:
        existing_holiday = db.session.execute(
            db.select(Holiday).where(Holiday.date == holiday_data['date'])
        ).scalar_one_or_none()
        
        if not existing_holiday:
            holiday = Holiday(
                name=holiday_data['name'],
                date=holiday_data['date']
            )
            db.session.add(holiday)
    
    try:
        db.session.commit()
        print("✅ Default users and holidays created successfully")
    except Exception as e:
        db.session.rollback()
        print(f"⚠️ Error creating defaults: {e}")

if __name__ == '__main__':
    # Import here to avoid circular imports
    from models import Holiday
    
    app = create_app()
    
    print("🚀 Starting Sakina Gas Attendance Management System")
    print("📍 Access the system at: http://localhost:5000")
    print("👤 Default Login - HR Manager: hr_manager / admin123")
    print("👤 Default Login - Station Manager: dandora_manager / manager123")
    
    # Run the application
    try:
        app.run(debug=True, host='0.0.0.0', port=5000)
    except OSError as e:
        if "Address already in use" in str(e):
            print("⚠️ Port 5000 is busy, trying port 5001...")
            app.run(debug=True, host='0.0.0.0', port=5001)
        else:
            raise e