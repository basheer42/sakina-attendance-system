"""
Enhanced Sakina Gas Company Attendance Management System
Main Application - Built upon your existing comprehensive structure
Professional Flask Application with Advanced Features
"""

import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime, date
from flask import Flask, render_template, redirect, url_for, request, jsonify, g, session
from flask_login import LoginManager, current_user, login_required
# Optional imports with graceful fallback
try:
    from flask_mail import Mail
    MAIL_AVAILABLE = True
except ImportError:
    Mail = None
    MAIL_AVAILABLE = False
from werkzeug.middleware.proxy_fix import ProxyFix

# Import our enhanced modules
from config import get_config

def create_app(config_name=None):
    """
    Enhanced Application Factory Pattern
    Creates and configures the Flask application with comprehensive features
    """
    app = Flask(__name__)
    
    # Load configuration
    config_class = get_config(config_name)
    app.config.from_object(config_class)
    config_class.init_app(app)
    
    # Handle proxy headers for deployment
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
    
    # Initialize extensions
    initialize_extensions(app)
    
    # Register blueprints
    register_blueprints(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register context processors
    register_context_processors(app)
    
    # Register CLI commands
    register_cli_commands(app)
    
    # Set up logging
    setup_logging(app)
    
    # Initialize database and create default data
    initialize_database(app)
    
    # Register request hooks
    register_request_hooks(app)
    
    return app

def initialize_extensions(app):
    """Initialize Flask extensions with enhanced configuration"""
    
    # Import SQLAlchemy here and create db instance
    from flask_sqlalchemy import SQLAlchemy
    
    # Create db instance here instead of importing from models
    db = SQLAlchemy()
    
    # Initialize SQLAlchemy
    db.init_app(app)
    
    # Make db available to app for use in other functions
    app.db = db
    
    # Initialize Flask-Login with enhanced security
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please sign in to access the Sakina Gas attendance system.'
    login_manager.login_message_category = 'info'
    login_manager.session_protection = 'strong'
    login_manager.refresh_view = 'auth.login'
    login_manager.needs_refresh_message = 'To protect your account, please re-authenticate.'
    login_manager.needs_refresh_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        """Load user with enhanced security checks"""
        try:
            # Import User model here when needed
            from models import User
            user = app.db.session.get(User, int(user_id))
            if user and user.is_active and not user.is_locked:
                return user
        except (ValueError, TypeError):
            pass
        return None
    
    @login_manager.unauthorized_handler
    def unauthorized():
        """Handle unauthorized access with proper logging"""
        if request.endpoint and request.endpoint.startswith('api.'):
            return jsonify({'error': 'Authentication required'}), 401
        return redirect(url_for('auth.login', next=request.url))
    
    # Initialize Flask-Mail (optional)
    if MAIL_AVAILABLE and Mail:
        mail = Mail()
        mail.init_app(app)
        app.mail = mail
        app.logger.info('Flask-Mail initialized successfully')
    else:
        app.mail = None
        app.logger.warning('Flask-Mail not available - email features will be disabled')

def register_blueprints(app):
    """Register all application blueprints with proper URL prefixes"""
    
    # Import and register blueprints
    try:
        # Authentication routes
        from routes.auth import auth_bp
        app.register_blueprint(auth_bp, url_prefix='/auth')
        
        # Main dashboard (at root for convenience)
        from routes.dashboard import dashboard_bp
        app.register_blueprint(dashboard_bp, url_prefix='/')
        
        # Employee management
        from routes.employees import employees_bp
        app.register_blueprint(employees_bp, url_prefix='/employees')
        
        # Attendance management
        from routes.attendance import attendance_bp
        app.register_blueprint(attendance_bp, url_prefix='/attendance')
        
        # Leave management
        from routes.leaves import leaves_bp
        app.register_blueprint(leaves_bp, url_prefix='/leaves')
        
        # Enhanced profile management
        from routes.profile import profile_bp
        app.register_blueprint(profile_bp, url_prefix='/profile')
        
        # Reports and analytics
        from routes.reports import reports_bp
        app.register_blueprint(reports_bp, url_prefix='/reports')
        
        # API endpoints
        from routes.api import api_bp
        app.register_blueprint(api_bp, url_prefix='/api/v2')
        
        app.logger.info('All blueprints registered successfully')
        
    except ImportError as e:
        app.logger.warning(f'Some blueprints not available: {e}')
        # Create minimal routes for testing
        register_minimal_routes(app)

def register_minimal_routes(app):
    """Register minimal routes for basic functionality"""
    
    @app.route('/')
    def index():
        """Root route"""
        if current_user.is_authenticated:
            return render_template('dashboard/main.html')
        return redirect('/auth/login')
    
    @app.route('/auth/login', methods=['GET', 'POST'])
    def login():
        """Basic login route"""
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            
            from models import User
            user = User.query.filter_by(username=username).first()
            if user and user.check_password(password) and user.is_active:
                from flask_login import login_user
                login_user(user)
                return redirect('/')
            
            return render_template('auth/login.html', error='Invalid credentials')
        
        return render_template('auth/login.html')
    
    @app.route('/auth/logout')
    @login_required
    def logout():
        """Basic logout route"""
        from flask_login import logout_user
        logout_user()
        return redirect('/auth/login')

def register_error_handlers(app):
    """Register comprehensive error handlers"""
    
    @app.errorhandler(400)
    def bad_request(error):
        """Handle 400 Bad Request errors"""
        if request.is_json:
            return jsonify({'error': 'Bad request'}), 400
        return f'<h1>400 Bad Request</h1><p>The request could not be understood.</p>', 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        """Handle 401 Unauthorized errors"""
        if request.is_json:
            return jsonify({'error': 'Unauthorized'}), 401
        return f'<h1>401 Unauthorized</h1><p>Please log in to access this resource.</p>', 401
    
    @app.errorhandler(403)
    def forbidden(error):
        """Handle 403 Forbidden errors"""
        if request.is_json:
            return jsonify({'error': 'Forbidden'}), 403
        return f'<h1>403 Forbidden</h1><p>You do not have permission to access this resource.</p>', 403
    
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 Not Found errors"""
        if request.is_json:
            return jsonify({'error': 'Not found'}), 404
        return f'<h1>404 Not Found</h1><p>The requested page could not be found.</p>', 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 Internal Server errors with database rollback"""
        app.db.session.rollback()
        app.logger.error(f'Server Error: {error}')
        
        if request.is_json:
            return jsonify({'error': 'Internal server error'}), 500
        return f'<h1>500 Internal Server Error</h1><p>Something went wrong. Please try again.</p>', 500

def register_context_processors(app):
    """Register template context processors for global variables"""
    
    @app.context_processor
    def inject_template_vars():
        """Inject global variables into all templates"""
        return {
            'company_name': app.config['COMPANY_NAME'],
            'company_tagline': app.config['COMPANY_TAGLINE'],
            'company_logo': app.config['COMPANY_LOGO'],
            'brand_colors': app.config['BRAND_COLORS'],
            'locations': app.config['COMPANY_LOCATIONS'],
            'departments': app.config['DEPARTMENTS'],
            'current_year': datetime.now().year,
            'current_date': date.today(),
            'app_version': app.config.get('API_VERSION', '2.0'),
            'environment': app.config.get('FLASK_ENV', 'production'),
            'user': current_user if current_user.is_authenticated else None,
            'maintenance_mode': app.config.get('MAINTENANCE_MODE', False)
        }

def register_cli_commands(app):
    """Register CLI commands for administration"""
    
    @app.cli.command()
    def init_db():
        """Initialize the database with tables and default data"""
        db.create_all()
        create_professional_defaults(app)
        print('✅ Database initialized successfully!')
    
    @app.cli.command()
    def reset_db():
        """Reset the database (WARNING: This will delete all data!)"""
        import click
        if click.confirm('This will delete all data. Are you sure?'):
            db.drop_all()
            db.create_all()
            create_professional_defaults(app)
            print('✅ Database reset successfully!')
    
    @app.cli.command()
    def create_admin():
        """Create an admin user"""
        import click
        username = click.prompt('Admin username')
        email = click.prompt('Admin email')
        password = click.prompt('Admin password', hide_input=True)
        
        admin = User(
            username=username,
            email=email,
            first_name='System',
            last_name='Administrator',
            role='admin',
            location='head_office'
        )
        admin.set_password(password)
        
        app.db.session.add(admin)
        app.db.session.commit()
        print(f'✅ Admin user {username} created successfully!')

def setup_logging(app):
    """Set up comprehensive logging"""
    
    if not app.debug and not app.testing:
        # Create logs directory if it doesn't exist
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        # Set up file logging with rotation
        file_handler = RotatingFileHandler(
            'logs/sakina_attendance.log',
            maxBytes=app.config.get('LOG_MAX_BYTES', 10485760),
            backupCount=app.config.get('LOG_BACKUP_COUNT', 5)
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        
        # Set logging level
        log_level = getattr(logging, app.config.get('LOG_LEVEL', 'INFO'))
        app.logger.setLevel(log_level)
        app.logger.info('Sakina Gas Attendance System startup')

def initialize_database(app):
    """Initialize database with tables and default data"""
    with app.app_context():
        try:
            # Initialize models with the db instance
            from models import init_models
            init_models(app.db)
            
            # Import models after initialization
            from models import User, Employee, AttendanceRecord, LeaveRequest, Holiday
            
            # Create all tables
            app.db.create_all()
            app.logger.info('Database tables created successfully')
            
            # Create default data
            create_professional_defaults(app)
            app.logger.info('Default data initialization completed')
            
        except Exception as e:
            app.logger.error(f'Error initializing database: {str(e)}')
            # Don't raise in production, just log the error

def create_professional_defaults(app):
    """Create comprehensive default data for professional deployment"""
    
    # Import models here to avoid circular imports
    from models import User, Employee, Holiday
    
    # Check if data already exists
    if User.query.first():
        app.logger.info('Default data already exists, skipping creation')
        return
    
    try:
        # Create default users with enhanced profiles
        users_data = [
            {
                'username': 'hr_manager',
                'email': 'hr@sakinagas.com',
                'first_name': 'Sarah',
                'last_name': 'Wanjiku',
                'role': 'hr_manager',
                'location': 'head_office',
                'department': 'hr',
                'phone': '+254 700 001 001'
            },
            {
                'username': 'dandora_manager',
                'email': 'dandora.manager@sakinagas.com',
                'first_name': 'James',
                'last_name': 'Mwangi',
                'role': 'station_manager',
                'location': 'dandora',
                'department': 'operations',
                'phone': '+254 700 002 001'
            },
            {
                'username': 'tassia_manager',
                'email': 'tassia.manager@sakinagas.com',
                'first_name': 'Grace',
                'last_name': 'Achieng',
                'role': 'station_manager',
                'location': 'tassia',
                'department': 'operations',
                'phone': '+254 700 003 001'
            },
            {
                'username': 'kiambu_manager',
                'email': 'kiambu.manager@sakinagas.com',
                'first_name': 'Peter',
                'last_name': 'Kamau',
                'role': 'station_manager',
                'location': 'kiambu',
                'department': 'operations',
                'phone': '+254 700 004 001'
            }
        ]
        
        for user_data in users_data:
            user = User(**user_data)
            user.set_password('manager123')  # Default password
            app.db.session.add(user)
        
        # Create comprehensive sample employees
        employees_data = [
            {
                'employee_id': 'SGC001',
                'first_name': 'John',
                'last_name': 'Doe',
                'email': 'john.doe@sakinagas.com',
                'phone': '+254 701 000 001',
                'national_id': '12345001',
                'location': 'dandora',
                'department': 'operations',
                'position': 'Station Attendant',
                'shift': 'day',
                'hire_date': date(2024, 1, 15),
                'basic_salary': 35000.00,
                'employment_type': 'permanent'
            },
            {
                'employee_id': 'SGC002',
                'first_name': 'Jane',
                'last_name': 'Smith',
                'email': 'jane.smith@sakinagas.com',
                'phone': '+254 701 000 002',
                'national_id': '12345002',
                'location': 'tassia',
                'department': 'operations',
                'position': 'Cashier',
                'shift': 'day',
                'hire_date': date(2024, 2, 1),
                'basic_salary': 32000.00,
                'employment_type': 'permanent'
            },
            {
                'employee_id': 'SGC003',
                'first_name': 'Peter',
                'last_name': 'Mwangi',
                'email': 'peter.mwangi@sakinagas.com',
                'phone': '+254 701 000 003',
                'national_id': '12345003',
                'location': 'kiambu',
                'department': 'operations',
                'position': 'Supervisor',
                'shift': 'day',
                'hire_date': date(2023, 11, 1),
                'basic_salary': 45000.00,
                'employment_type': 'permanent'
            },
            {
                'employee_id': 'SGC004',
                'first_name': 'Mary',
                'last_name': 'Wanjiku',
                'email': 'mary.wanjiku@sakinagas.com',
                'phone': '+254 701 000 004',
                'national_id': '12345004',
                'location': 'head_office',
                'department': 'finance',
                'position': 'Accountant',
                'shift': None,
                'hire_date': date(2023, 8, 15),
                'basic_salary': 55000.00,
                'employment_type': 'permanent'
            },
            {
                'employee_id': 'SGC005',
                'first_name': 'David',
                'last_name': 'Kiprotich',
                'email': 'david.kiprotich@sakinagas.com',
                'phone': '+254 701 000 005',
                'national_id': '12345005',
                'location': 'dandora',
                'department': 'security',
                'position': 'Security Guard',
                'shift': 'night',
                'hire_date': date(2024, 3, 1),
                'basic_salary': 28000.00,
                'employment_type': 'contract'
            }
        ]
        
        for emp_data in employees_data:
            employee = Employee(**emp_data)
            app.db.session.add(employee)
        
        # Create sample company holidays
        holidays_data = [
            {'name': 'New Year Day', 'date': date(2024, 1, 1), 'holiday_type': 'public'},
            {'name': 'Good Friday', 'date': date(2024, 3, 29), 'holiday_type': 'public'},
            {'name': 'Easter Monday', 'date': date(2024, 4, 1), 'holiday_type': 'public'},
            {'name': 'Labour Day', 'date': date(2024, 5, 1), 'holiday_type': 'public'},
            {'name': 'Madaraka Day', 'date': date(2024, 6, 1), 'holiday_type': 'public'},
            {'name': 'Huduma Day', 'date': date(2024, 10, 10), 'holiday_type': 'public'},
            {'name': 'Mashujaa Day', 'date': date(2024, 10, 20), 'holiday_type': 'public'},
            {'name': 'Independence Day', 'date': date(2024, 12, 12), 'holiday_type': 'public'},
            {'name': 'Christmas Day', 'date': date(2024, 12, 25), 'holiday_type': 'public'},
            {'name': 'Boxing Day', 'date': date(2024, 12, 26), 'holiday_type': 'public'}
        ]
        
        for holiday_data in holidays_data:
            holiday = Holiday(**holiday_data)
            app.db.session.add(holiday)
        
        # Commit all default data
        app.db.session.commit()
        print('✅ Professional default data created successfully')
        app.logger.info('Professional default data created successfully')
        
    except Exception as e:
        app.db.session.rollback()
        print(f'❌ Error creating default data: {str(e)}')
        app.logger.error(f'Error creating default data: {str(e)}')

def register_request_hooks(app):
    """Register request hooks for security and audit"""
    
    @app.before_request
    def before_request():
        """Execute before each request"""
        # Check maintenance mode
        if app.config.get('MAINTENANCE_MODE') and request.endpoint != 'static':
            if not (current_user.is_authenticated and 
                   current_user.has_permission('system_administration')):
                return '<h1>System Maintenance</h1><p>The system is currently under maintenance.</p>', 503
        
        # Store request start time for performance monitoring
        g.request_start_time = datetime.utcnow()
        
        # Store IP address for audit logging
        g.ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', 
                                          request.environ.get('REMOTE_ADDR'))
    
    @app.after_request
    def after_request(response):
        """Execute after each request"""
        # Security headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        return response

# Main application routes
@login_required
def api_quick_stats():
    """Enhanced quick statistics API for dashboard"""
    try:
        today = date.today()
        
        # Base employee query based on user permissions
        if current_user.role == 'station_manager':
            employee_query = Employee.query.filter(
                Employee.location == current_user.location,
                Employee.is_active == True
            )
        else:
            employee_query = Employee.query.filter(Employee.is_active == True)
        
        total_employees = employee_query.count()
        
        # Today's attendance statistics
        attendance_query = app.db.session.query(AttendanceRecord).join(Employee).filter(
            AttendanceRecord.date == today,
            Employee.is_active == True
        )
        
        if current_user.role == 'station_manager':
            attendance_query = attendance_query.filter(Employee.location == current_user.location)
        
        # Count by status
        present_count = attendance_query.filter(
            AttendanceRecord.status.in_(['present', 'late'])
        ).count()
        
        absent_count = attendance_query.filter(
            AttendanceRecord.status == 'absent'
        ).count()
        
        on_leave_count = attendance_query.filter(
            AttendanceRecord.status.like('%leave%')
        ).count()
        
        # Pending leave requests
        leave_query = app.db.session.query(LeaveRequest).join(Employee).filter(
            LeaveRequest.status == 'pending',
            Employee.is_active == True
        )
        
        if current_user.role == 'station_manager':
            leave_query = leave_query.filter(Employee.location == current_user.location)
        
        pending_leaves = leave_query.count()
        
        # Calculate attendance rate
        marked_count = present_count + absent_count + on_leave_count
        not_marked = total_employees - marked_count
        attendance_rate = round((present_count / total_employees * 100), 1) if total_employees > 0 else 0
        
        return jsonify({
            'total_employees': total_employees,
            'present_today': present_count,
            'absent_today': absent_count,
            'on_leave_today': on_leave_count,
            'not_marked': not_marked,
            'pending_leave_requests': pending_leaves,
            'attendance_rate': attendance_rate,
            'last_updated': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': 'Unable to fetch statistics'}), 500

# Main application entry point
if __name__ == '__main__':
    # Determine environment
    config_name = os.environ.get('FLASK_CONFIG', 'development')
    app = create_app(config_name)
    
    # Add the API route directly since we may not have blueprints yet
    app.add_url_rule('/api/quick-stats', 'api_quick_stats', api_quick_stats, methods=['GET'])
    
    # Application startup banner
    print("=" * 70)
    print("🏢 SAKINA GAS COMPANY - ENHANCED ATTENDANCE MANAGEMENT SYSTEM")
    print("=" * 70)
    print(f"🚀 Environment: {config_name.upper()}")
    print(f"📊 Version: {app.config.get('API_VERSION', '2.0')} Professional Enhanced")
    print(f"🌐 Access URL: http://localhost:5000")
    print("=" * 70)
    print("👤 DEFAULT LOGIN CREDENTIALS:")
    print("   HR Manager: hr_manager / manager123")
    print("   Station Managers:")
    print("   - dandora_manager / manager123 (Dandora Station)")
    print("   - tassia_manager / manager123 (Tassia Station)") 
    print("   - kiambu_manager / manager123 (Kiambu Station)")
    print("=" * 70)
    print("📋 ENHANCED FEATURES:")
    print("   ✅ Multi-location Management (4 locations)")
    print("   ✅ Enhanced Kenyan Labor Law Compliance")
    print("   ✅ Real-time Executive Dashboard")
    print("   ✅ Advanced Leave Management System")
    print("   ✅ Comprehensive Employee Profiles")
    print("   ✅ Professional Performance Tracking")
    print("   ✅ Advanced Audit Trail System")
    print("   ✅ Email Notification System")
    print("   ✅ Mobile-Ready Responsive Design")
    print("=" * 70)
    print("🔧 CLI COMMANDS:")
    print("   flask init-db      - Initialize database")
    print("   flask reset-db     - Reset database (WARNING!)")
    print("   flask create-admin - Create admin user")
    print("=" * 70)
    print("⚙️  SYSTEM STATUS:")
    
    # System health check
    with app.app_context():
        try:
            app.db.session.execute(db.text('SELECT 1'))
            print("   ✅ Database: Connected")
        except:
            print("   ❌ Database: Connection failed")
        
        user_count = User.query.count()
        employee_count = Employee.query.count()
        print(f"   📊 Users: {user_count} | Employees: {employee_count}")
    
    print("=" * 70)
    
    # Run the application
    try:
        app.run(
            debug=app.config.get('DEBUG', False),
            host='0.0.0.0',
            port=int(os.environ.get('PORT', 5000)),
            threaded=True
        )
    except KeyboardInterrupt:
        print("\n🛑 Application stopped by user")
    except Exception as e:
        print(f"\n❌ Application failed to start: {str(e)}")
        if hasattr(app, 'logger'):
            app.logger.error(f'Application startup error: {str(e)}')