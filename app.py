"""
Sakina Gas Company - Professional Attendance Management System
Main Application File with Enhanced Enterprise Features
UPDATED: Fixed SQLAlchemy 2.0 deprecation warnings
"""
from flask import Flask, render_template, redirect, url_for, request, jsonify
from flask_login import LoginManager, login_required, current_user
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
import os

# Import our configuration (fixed import)
from config import config

def create_app(config_name=None):
    """Application factory pattern for professional deployment"""
    app = Flask(__name__)
    
    # Load configuration
    if config_name is None:
        config_name = os.environ.get('FLASK_CONFIG', 'development')
    
    if hasattr(config, config_name):
        app.config.from_object(config[config_name])
    else:
        app.config.from_object(config['development'])
    
    # Initialize extensions
    from models import db
    db.init_app(app)
    
    # Initialize Flask-Login with enhanced security
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please sign in to access the Sakina Gas attendance system.'
    login_manager.login_message_category = 'info'
    login_manager.session_protection = 'strong'
    
    @login_manager.user_loader
    def load_user(user_id):
        from models import User, db
        # FIXED: Using db.session.get() instead of deprecated User.query.get()
        return db.session.get(User, int(user_id))
    
    # Register professional blueprints
    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.employees import employees_bp
    from routes.attendance import attendance_bp
    from routes.leaves import leaves_bp
    from routes.profile import profile_bp
      
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(dashboard_bp, url_prefix='/')
    app.register_blueprint(employees_bp, url_prefix='/employees')
    app.register_blueprint(attendance_bp, url_prefix='/attendance')
    app.register_blueprint(leaves_bp, url_prefix='/leaves')
    app.register_blueprint(profile_bp, url_prefix='/profile')
    
    # Professional error handlers
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
    
    # Professional context processors
    @app.context_processor
    def inject_globals():
        """Inject global variables for professional templates"""
        return {
            'company_name': app.config.get('COMPANY_NAME', 'Sakina Gas Company'),
            'company_tagline': app.config.get('COMPANY_TAGLINE', 'Excellence in Energy Solutions'),
            'brand_colors': app.config.get('BRAND_COLORS', {}),
            'current_year': datetime.now().year,
            'system_version': '2.0 Professional',
            'today': date.today()  # Added for templates
        }
    
    # Professional template filters
    @app.template_filter('datetime_format')
    def datetime_format(value, format='%Y-%m-%d %H:%M'):
        """Format datetime for professional display"""
        if value is None:
            return ""
        return value.strftime(format)
    
    @app.template_filter('currency')
    def currency_format(value):
        """Format currency in Kenyan Shillings"""
        if value is None:
            return "KSh 0"
        return f"KSh {value:,.2f}"
    
    @app.template_filter('percentage')
    def percentage_format(value, decimals=1):
        """Format percentage values"""
        if value is None:
            return "0%"
        return f"{value:.{decimals}f}%"
    
    # Create database tables and default data
    with app.app_context():
        db.create_all()
        create_professional_defaults()
    
    # Root route with professional redirect
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
    
    # API endpoint for real-time dashboard updates
    @app.route('/api/dashboard/stats')
    @login_required
    def dashboard_stats():
        """Real-time dashboard statistics API"""
        from routes.dashboard import get_attendance_overview
        
        today = date.today()
        stats = get_attendance_overview(today)
        
        return jsonify({
            'date': today.isoformat(),
            'stats': stats,
            'timestamp': datetime.utcnow().isoformat()
        })
    
    return app

def create_professional_defaults():
    """Create professional default users and sample data"""
    from models import db, User, Employee, Holiday
    from werkzeug.security import generate_password_hash
    
    # Create default users with enhanced security
    default_users = [
        {
            'username': 'hr_manager',
            'email': 'hr@sakinagas.com', 
            'role': 'hr_manager',
            'location': None,
            'password': 'admin123'  # Change in production
        },
        {
            'username': 'dandora_manager',
            'email': 'dandora@sakinagas.com',
            'role': 'station_manager', 
            'location': 'dandora',
            'password': 'manager123'
        },
        {
            'username': 'tassia_manager',
            'email': 'tassia@sakinagas.com',
            'role': 'station_manager',
            'location': 'tassia', 
            'password': 'manager123'
        },
        {
            'username': 'kiambu_manager',
            'email': 'kiambu@sakinagas.com',
            'role': 'station_manager',
            'location': 'kiambu',
            'password': 'manager123'
        }
    ]
    
    for user_data in default_users:
        # FIXED: Using db.session.get() instead of deprecated User.query.filter_by().first()
        existing_user = db.session.execute(
            db.select(User).where(User.username == user_data['username'])
        ).scalar_one_or_none()
        
        if not existing_user:
            user = User(
                username=user_data['username'],
                email=user_data['email'],
                role=user_data['role'],
                location=user_data['location']
            )
            user.set_password(user_data['password'])
            db.session.add(user)
    
    # Create sample holidays for 2025 (Kenyan public holidays)
    kenyan_holidays_2025 = [
        ('New Year\'s Day', '2025-01-01'),
        ('Good Friday', '2025-04-18'),
        ('Easter Monday', '2025-04-21'), 
        ('Labour Day', '2025-05-01'),
        ('Madaraka Day', '2025-06-01'),
        ('Mashujaa Day', '2025-10-20'),
        ('Jamhuri Day', '2025-12-12'),
        ('Christmas Day', '2025-12-25'),
        ('Boxing Day', '2025-12-26')
    ]
    
    for holiday_name, holiday_date in kenyan_holidays_2025:
        holiday_date_obj = datetime.strptime(holiday_date, '%Y-%m-%d').date()
        # FIXED: Using db.session.get() instead of deprecated Holiday.query.filter_by().first()
        existing_holiday = db.session.execute(
            db.select(Holiday).where(Holiday.date == holiday_date_obj)
        ).scalar_one_or_none()
        
        if not existing_holiday:
            holiday = Holiday(
                name=holiday_name,
                date=holiday_date_obj
            )
            db.session.add(holiday)
    
    try:
        db.session.commit()
        print("✅ Professional default users and holidays created successfully!")
    except Exception as e:
        db.session.rollback()
        print(f"⚠️  Error creating defaults: {e}")

if __name__ == '__main__':
    app = create_app()
    
    # Professional startup banner
    print("=" * 80)
    print("🏢 SAKINA GAS COMPANY - PROFESSIONAL ATTENDANCE SYSTEM")
    print("=" * 80)
    print("🌐 Server: http://localhost:5000")
    print("👤 HR Manager: hr_manager / admin123")
    print("🏪 Station Manager: dandora_manager / manager123")
    print("📊 System: Professional Enterprise Edition v2.0")
    print("🔒 Security: Enhanced with SQLAlchemy 2.0 compatibility")
    print("=" * 80)
    
    # Run with professional settings
    app.run(
        debug=True,
        host='0.0.0.0',
        port=5000,
        threaded=True
    )