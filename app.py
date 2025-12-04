"""
Sakina Gas Company - Professional Attendance Management System
Built from scratch - Production ready with all advanced features
Version 3.0 - Complete rewrite matching original complexity
"""

import os
import sys
import logging
import secrets
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from datetime import datetime, date, timedelta
from flask import Flask, render_template, redirect, url_for, request, jsonify, g, session, send_from_directory, current_app
from flask_login import LoginManager, current_user, login_required
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.utils import secure_filename
import click

# Optional imports with graceful fallback
try:
    from flask_mail import Mail
    MAIL_AVAILABLE = True
except ImportError:
    Mail = None
    MAIL_AVAILABLE = False

# Global import place for utility/model functions that don't need to be imported late
from database import db # FIX: Ensure db is imported here for global usage/registration
from sqlalchemy import text # FIX: Ensure text is imported for use in CLI/health checks

def create_app(config_name=None):
    """
    Application Factory Pattern - Enterprise Grade
    """
    app = Flask(__name__)
    
    # Load configuration
    from config import get_config
    config_class = get_config(config_name)
    app.config.from_object(config_class)
    config_class.init_app(app)
    
    # Production middleware
    if app.config.get('ENV') == 'production':
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
    
    # Initialize all components
    initialize_extensions(app)
    register_blueprints(app)
    register_error_handlers(app)
    register_context_processors(app)
    register_cli_commands(app)
    register_security_middleware(app)
    setup_logging(app)
    
    # Initialize database and create default data
    initialize_database(app)
    
    return app

def initialize_extensions(app):
    """Initialize Flask extensions with comprehensive configuration"""
    
    # Import and initialize database
    db.init_app(app)
    app.db = db
    
    # Initialize Flask-Login with enhanced security
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please sign in to access the Sakina Gas attendance system.'
    login_manager.login_message_category = 'info'
    login_manager.session_protection = 'strong'
    login_manager.refresh_view = 'auth.login'
    login_manager.needs_refresh_message = 'Session expired. Please re-authenticate for security.'
    login_manager.needs_refresh_message_category = 'warning'
    
    @login_manager.user_loader
    def load_user(user_id):
        """Load user with comprehensive security checks"""
        # FIX: Changed to use current_app and local import to prevent premature model load
        with current_app.app_context():
            from models.user import User # Local import - safer
            try:
                # Use query.get for better integration with Flask-SQLAlchemy-2.0+
                user = current_app.db.session.get(User, int(user_id))
                
                # Enhanced security checks
                if user and user.is_active:
                    # Check for account lock
                    if hasattr(user, 'is_account_locked') and user.is_account_locked():
                        return None
                    # Check for session timeout
                    if hasattr(user, 'last_activity'):
                        timeout = current_app.config.get('PERMANENT_SESSION_LIFETIME', timedelta(hours=8))
                        if datetime.utcnow() - user.last_activity > timeout:
                            return None
                    
                    # Update last seen and activity
                    user.last_seen = datetime.utcnow()
                    if request.endpoint not in ['static', 'favicon', 'health_check']:  # Don't update for non-app requests
                        user.last_activity = datetime.utcnow()
                    
                    try:
                        current_app.db.session.commit()
                    except:
                        current_app.db.session.rollback()
                        current_app.logger.error("Failed to commit user activity update in load_user.")
                        
                    return user
            except (ValueError, TypeError, AttributeError) as e:
                current_app.logger.error(f"Error in user_loader: {e}")
                pass
            return None
    
    @login_manager.unauthorized_handler
    def unauthorized():
        """Handle unauthorized access with comprehensive logging"""
        # Log unauthorized access attempt
        with current_app.app_context():
            from models.audit import AuditLog # Local import - safer
            try:
                client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR'))
                AuditLog.log_event(
                    event_type='unauthorized_access_attempt',
                    description=f'Unauthorized access to {request.endpoint} from {client_ip}',
                    ip_address=client_ip,
                    user_agent=request.headers.get('User-Agent'),
                    risk_level='medium'
                )
                current_app.db.session.commit()
            except:
                current_app.db.session.rollback()
        
        # API vs Web response
        if request.endpoint and request.endpoint.startswith('api.'):
            return jsonify({
                'error': 'Unauthorized',
                'message': 'Please provide valid authentication credentials',
                'status': 401
            }), 401
        
        # Preserve the URL user was trying to access
        next_url = request.url if request.endpoint != 'auth.login' else None
        return redirect(url_for('auth.login', next=next_url))
    
    # Initialize Flask-Mail with enhanced configuration
    if MAIL_AVAILABLE and app.config.get('MAIL_SERVER'):
        mail = Mail()
        mail.init_app(app)
        app.mail = mail
        app.logger.info('Flask-Mail initialized successfully')
    else:
        app.mail = None
        app.logger.info('Flask-Mail not configured - email features disabled')

def register_blueprints(app):
    """Register all application blueprints with comprehensive error handling"""
    
    blueprints = [
        ('auth', '/auth'),
        ('dashboard', '/'),
        ('employees', '/employees'),
        ('attendance', '/attendance'),
        ('leaves', '/leaves'),
        ('profile', '/profile'),
        ('reports', '/reports'),
        ('api', '/api/v1')
    ]
    
    for blueprint_name, url_prefix in blueprints:
        try:
            # FIX: Ensure proper package relative import structure
            module = __import__(f'routes.{blueprint_name}', fromlist=[f'{blueprint_name}_bp'])
            blueprint = getattr(module, f'{blueprint_name}_bp')
            app.register_blueprint(blueprint, url_prefix=url_prefix)
            app.logger.info(f'✅ Registered blueprint: {blueprint_name} at {url_prefix}')
        except (ImportError, AttributeError) as e:
            app.logger.error(f'❌ Failed to register blueprint {blueprint_name}: {e}')
            # For critical blueprints, we might want to exit
            if blueprint_name in ['auth', 'dashboard']:
                app.logger.critical(f'Critical blueprint {blueprint_name} failed to load!')
                sys.exit(1)

def register_error_handlers(app):
    """Register comprehensive error handlers"""
    
    @app.errorhandler(400)
    def bad_request(error):
        """Handle bad request errors"""
        app.logger.warning(f'Bad request: {error} from {request.remote_addr}')
        if request.is_json or request.content_type == 'application/json':
            return jsonify({
                'error': 'Bad Request',
                'message': 'The request could not be understood by the server',
                'status': 400
            }), 400
        return render_template('errors/400.html', error=error), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        """Handle unauthorized errors"""
        if request.is_json or request.content_type == 'application/json':
            return jsonify({
                'error': 'Unauthorized',
                'message': 'Authentication required',
                'status': 401
            }), 401
        return render_template('errors/401.html', error=error), 401
    
    @app.errorhandler(403)
    def forbidden(error):
        """Handle forbidden errors"""
        app.logger.warning(f'Forbidden access attempt: {error} from {request.remote_addr}')
        if request.is_json or request.content_type == 'application/json':
            return jsonify({
                'error': 'Forbidden',
                'message': 'Access to this resource is forbidden',
                'status': 403
            }), 403
        return render_template('errors/403.html', error=error), 403
    
    @app.errorhandler(404)
    def not_found(error):
        """Handle not found errors"""
        if request.is_json or request.content_type == 'application/json':
            return jsonify({
                'error': 'Not Found',
                'message': 'The requested resource was not found',
                'status': 404
            }), 404
        return render_template('errors/404.html', error=error), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle internal server errors"""
        # Ensure rollback in case of database error
        try:
            app.db.session.rollback()
        except:
            pass
            
        app.logger.error(f'Server Error: {error}', exc_info=True)
        
        # Log to audit trail if possible
        try:
            from models.audit import AuditLog
            AuditLog.log_event(
                event_type='system_error',
                description=f'Internal server error: {str(error)}',
                ip_address=request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR')),
                risk_level='high'
            )
            app.db.session.commit()
        except:
            try:
                app.db.session.rollback()
            except:
                pass
        
        if request.is_json or request.content_type == 'application/json':
            return jsonify({
                'error': 'Internal Server Error',
                'message': 'An unexpected error occurred',
                'status': 500
            }), 500
        return render_template('errors/500.html', error=error), 500

def register_context_processors(app):
    """Register template context processors"""
    
    @app.context_processor
    def inject_global_vars():
        """Inject global variables available in all templates"""
        
        # FIX: Local imports to prevent early model loading
        user_permissions = []
        is_hr_manager = False
        is_station_manager = False
        user_location = None
        
        if current_user.is_authenticated:
            try:
                from models.user import User # Local import for methods
                if hasattr(current_user, 'get_permissions'):
                    user_permissions = current_user.get_permissions()
                is_hr_manager = current_user.role == 'hr_manager'
                is_station_manager = current_user.role == 'station_manager'
                user_location = current_user.location
            except:
                pass
            
        return {
            # Company Information
            'company_name': app.config.get('COMPANY_NAME', 'Sakina Gas Company'),
            'company_tagline': app.config.get('COMPANY_TAGLINE', 'Reliable Energy Solutions'),
            'company_logo': app.config.get('COMPANY_LOGO', '/static/images/logo.png'),
            
            # Brand Configuration
            'brand_colors': app.config.get('BRAND_COLORS', {}),
            
            # Operational Data
            'locations': app.config.get('COMPANY_LOCATIONS', {}),
            'departments': app.config.get('DEPARTMENTS', {}),
            'user_roles': app.config.get('USER_ROLES', {}),
            
            # System Information
            'current_year': datetime.now().year,
            'current_date': date.today(),
            'app_version': app.config.get('APP_VERSION', '3.0'),
            'environment': app.config.get('FLASK_ENV', 'production'),
            
            # Navigation helpers
            'is_hr_manager': is_hr_manager,
            'is_station_manager': is_station_manager,
            'user_location': user_location,
            'user_permissions': user_permissions,
            
            # Utility functions
            'enumerate': enumerate,
            'len': len,
            'str': str,
            'int': int
        }
    
    @app.context_processor
    def inject_navigation_data():
        """Inject navigation-specific data"""
        if current_user.is_authenticated:
            try:
                # Get pending notifications/counts
                pending_counts = {}
                
                # FIX: Local imports to prevent early model loading
                from models.leave import LeaveRequest
                from models.employee import Employee
                from models.attendance import AttendanceRecord
                
                if current_user.role == 'hr_manager':
                    
                    # Pending leave requests
                    pending_counts['pending_leaves'] = LeaveRequest.query.filter(LeaveRequest.status.in_(['pending', 'pending_hr'])).count() # FIX: Use correct statuses
                    
                    # Employees on probation ending soon (next 30 days)
                    probation_ending = Employee.query.filter(
                        Employee.is_active == True,
                        Employee.probation_end_date.between(date.today(), date.today() + timedelta(days=30))
                    ).count()
                    pending_counts['probation_ending'] = probation_ending
                    
                elif current_user.role == 'station_manager':
                    
                    # Today's attendance for their location
                    location_employees = Employee.query.filter_by(
                        location=current_user.location,
                        is_active=True
                    ).count()
                    
                    # Today's Attendance for Location (Present or Late)
                    today_attended = AttendanceRecord.query.join(Employee).filter(
                        AttendanceRecord.date == date.today(),
                        Employee.location == current_user.location,
                        AttendanceRecord.status.in_(['present', 'late'])
                    ).count()
                    
                    pending_counts['attendance_rate'] = round((today_attended / location_employees * 100) if location_employees > 0 else 0, 1)
                
                return {'pending_counts': pending_counts}
                
            except Exception as e:
                # app.logger.error(f'Error in navigation context processor: {e}') # Temporarily commented for startup stability
                return {'pending_counts': {}}
        
        return {'pending_counts': {}}

def register_security_middleware(app):
    """Register security middleware and hooks"""
    
    @app.before_request
    def before_request_security():
        """Security checks before each request"""
        # Skip security checks for static files and some endpoints
        if request.endpoint in ['static', 'health_check', 'favicon']:
            return
        
        # Track request for security monitoring
        g.request_start_time = datetime.utcnow()
        g.client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR'))
        g.user_agent = request.headers.get('User-Agent', '')
        
        # Check for suspicious activity
        if len(g.user_agent) > 500:  # Suspiciously long user agent
            app.logger.warning(f'Suspicious user agent from {g.client_ip}: {g.user_agent[:100]}...')
        
        # Rate limiting check (basic implementation)
        # In production, use Redis or similar for distributed rate limiting
        session_key = f"requests:{g.client_ip}"
        current_requests = session.get(session_key, 0)
        
        # Only rate limit if we're not authenticated (prevents DOS on login/forgot password)
        if not current_user.is_authenticated and current_requests > 100:  # 100 requests per hour per IP (simplified)
             app.logger.warning(f'Rate limit exceeded for {g.client_ip}')
             return jsonify({'error': 'Rate limit exceeded'}), 429
        session[session_key] = current_requests + 1
        
        # Maintenance mode check
        if app.config.get('MAINTENANCE_MODE', False) and request.endpoint != 'maintenance':
            if not (current_user.is_authenticated and current_user.role == 'admin'):
                return render_template('maintenance.html'), 503
    
    @app.after_request
    def after_request_security(response):
        """Security headers and cleanup after each request"""
        # Security headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # HSTS for HTTPS
        if request.is_secure:
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'
        
        # Content Security Policy
        if not app.debug:
            csp = "default-src 'self'; img-src 'self' data: https:; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net; font-src 'self' https://fonts.gstatic.com https://cdn.jsdelivr.net;"
            response.headers['Content-Security-Policy'] = csp
        
        # Cache control for sensitive pages
        if request.endpoint and any(x in request.endpoint for x in ['auth', 'profile', 'admin']):
            response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response.headers['Pragma'] = 'no-cache'
        
        # Log slow requests
        if hasattr(g, 'request_start_time'):
            duration = (datetime.utcnow() - g.request_start_time).total_seconds()
            if duration > 2.0:  # Log requests taking more than 2 seconds
                app.logger.warning(f'Slow request: {request.endpoint} took {duration:.2f}s from {g.client_ip}')
        
        return response

def setup_logging(app):
    """Setup comprehensive logging system"""
    
    if not app.debug and not app.testing:
        # Ensure logs directory exists
        logs_dir = app.config.get('LOGS_DIR', 'logs')
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir)
        
        # Main application log
        file_handler = RotatingFileHandler(
            os.path.join(logs_dir, 'sakina_attendance.log'),
            maxBytes=10485760,  # 10MB
            backupCount=20
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        
        # Error log with daily rotation
        error_handler = TimedRotatingFileHandler(
            os.path.join(logs_dir, 'errors.log'),
            when='midnight',
            interval=1,
            backupCount=30
        )
        error_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]\n'
            'Remote Address: %(request_remote_addr)s\n'
            'Request Path: %(request_path)s\n'
            'User: %(current_user)s\n',
            defaults={
                'request_remote_addr': lambda: getattr(request, 'remote_addr', 'N/A'),
                'request_path': lambda: getattr(request, 'path', 'N/A'),
                'current_user': lambda: getattr(current_user, 'username', 'Anonymous')
            }
        ))
        error_handler.setLevel(logging.ERROR)
        
        # Security audit log
        security_handler = TimedRotatingFileHandler(
            os.path.join(logs_dir, 'security.log'),
            when='midnight',
            interval=1,
            backupCount=365  # Keep for 1 year
        )
        security_handler.setFormatter(logging.Formatter(
            '%(asctime)s SECURITY [%(levelname)s]: %(message)s'
        ))
        security_handler.setLevel(logging.WARNING)
        
        # Performance log
        perf_handler = RotatingFileHandler(
            os.path.join(logs_dir, 'performance.log'),
            maxBytes=5242880,  # 5MB
            backupCount=10
        )
        perf_handler.setFormatter(logging.Formatter(
            '%(asctime)s PERF: %(message)s'
        ))
        
        # Add all handlers
        app.logger.addHandler(file_handler)
        app.logger.addHandler(error_handler)
        
        # Create specialized loggers
        security_logger = logging.getLogger('security')
        security_logger.addHandler(security_handler)
        security_logger.setLevel(logging.WARNING)
        
        perf_logger = logging.getLogger('performance')
        perf_logger.addHandler(perf_handler)
        perf_logger.setLevel(logging.INFO)
        
        app.logger.setLevel(logging.INFO)
        app.logger.info('Sakina Gas Attendance System logging initialized')

def initialize_database(app):
    """Initialize database with comprehensive setup"""
    from database import init_database as db_init
    with app.app_context():
        try:
            # FIX: Only call init_database from database.py
            db_init(app)
            
            # Create default data - pass model classes to avoid re-importing in create_default_system_data
            # FIX: Model Imports must be done AFTER db_init to avoid mapper error
            from models.user import User
            from models.employee import Employee  
            from models.holiday import Holiday
            from models.audit import AuditLog
            
            create_default_system_data(app, User, Employee, Holiday, AuditLog)
            
            app.logger.info('Database initialization completed successfully')
            
        except Exception as e:
            app.logger.error(f'Database initialization failed: {e}')
            sys.exit(1)

def create_default_system_data(app, User, Employee, Holiday, AuditLog): # FIX: Accepts models as arguments
    """Create comprehensive default system data"""
    try:
        # Skip if system already has data
        if User.query.count() > 0:
            app.logger.info('System already has data, skipping default data creation')
            return
        
        app.logger.info('Creating default system data...')
        
        # Create default admin users
        default_users = [
            {
                'username': 'hr_manager',
                'email': 'hr@sakinagas.com',
                'first_name': 'Sarah',
                'last_name': 'Mwangi',
                'role': 'hr_manager',
                'location': 'head_office',
                'department': 'hr',
                'is_active': True,
                'password': 'manager123'
            },
            {
                'username': 'dandora_manager',
                'email': 'dandora@sakinagas.com',
                'first_name': 'James',
                'last_name': 'Ochieng',
                'role': 'station_manager',
                'location': 'dandora',
                'department': 'operations',
                'is_active': True,
                'password': 'manager123'
            },
            {
                'username': 'tassia_manager',
                'email': 'tassia@sakinagas.com',
                'first_name': 'Grace',
                'last_name': 'Wanjiku',
                'role': 'station_manager',
                'location': 'tassia',
                'department': 'operations',
                'is_active': True,
                'password': 'manager123'
            },
            {
                'username': 'kiambu_manager',
                'email': 'kiambu@sakinagas.com',
                'first_name': 'Peter',
                'last_name': 'Kamau',
                'role': 'station_manager',
                'location': 'kiambu',
                'department': 'operations',
                'is_active': True,
                'password': 'manager123'
            }
        ]
        
        for user_data in default_users:
            password = user_data.pop('password')
            user = User(**user_data)
            user.set_password(password)
            user.created_date = datetime.utcnow()
            user.last_password_change = datetime.utcnow()
            app.db.session.add(user)
            app.logger.info(f'Created user: {user.username}')
        
        # Create sample employees
        sample_employees = [
            {
                'employee_id': 'SGC001',
                'first_name': 'John',
                'middle_name': 'Kipchoge',
                'last_name': 'Mutua',
                'email': 'john.mutua@sakinagas.com',
                'phone': '+254712345001',
                'national_id': '12345678',
                'location': 'dandora',
                'department': 'operations',
                'position': 'Station Attendant',
                'shift': 'day',
                'hire_date': date(2024, 1, 15),
                'basic_salary': 35000.00,
                'gender': 'male',
                'is_active': True,
                'employment_type': 'permanent'
            },
            {
                'employee_id': 'SGC002',
                'first_name': 'Jane',
                'middle_name': 'Wambui',
                'last_name': 'Kamau',
                'email': 'jane.kamau@sakinagas.com',
                'phone': '+254712345002',
                'national_id': '23456789',
                'location': 'tassia',
                'department': 'operations',
                'position': 'Cashier',
                'shift': 'day',
                'hire_date': date(2024, 2, 1),
                'basic_salary': 32000.00,
                'gender': 'female',
                'is_active': True,
                'employment_type': 'permanent'
            },
            {
                'employee_id': 'SGC003',
                'first_name': 'David',
                'middle_name': 'Kiprotich',
                'last_name': 'Cheruiyot',
                'email': 'david.cheruiyot@sakinagas.com',
                'phone': '+254712345003',
                'national_id': '34567890',
                'location': 'kiambu',
                'department': 'security',
                'position': 'Security Guard',
                'shift': 'night',
                'hire_date': date(2024, 3, 1),
                'basic_salary': 28000.00,
                'gender': 'male',
                'is_active': True,
                'employment_type': 'contract'
            },
            {
                'employee_id': 'SGC004',
                'first_name': 'Mary',
                'middle_name': 'Njeri',
                'last_name': 'Wairimu',
                'email': 'mary.wairimu@sakinagas.com',
                'phone': '+254712345004',
                'national_id': '45678901',
                'location': 'head_office',
                'department': 'administration',
                'position': 'Administrative Assistant',
                'shift': 'day',
                'hire_date': date(2024, 1, 8),
                'basic_salary': 38000.00,
                'gender': 'female',
                'is_active': True,
                'employment_type': 'permanent'
            }
        ]
        
        for emp_data in sample_employees:
            # Set probation end date
            emp_data['probation_end_date'] = emp_data['hire_date'] + timedelta(days=90)
            employee = Employee(**emp_data)
            app.db.session.add(employee)
            app.logger.info(f'Created employee: {employee.employee_id} - {employee.first_name} {employee.last_name}')
        
        # Create Kenyan public holidays for 2024-2025
        # FIX: The model import is now handled by the function argument
        holidays_to_add = Holiday.create_kenyan_holidays_2024_2025()
        
        for holiday in holidays_to_add:
            app.db.session.add(holiday)
        
        app.logger.info(f'Created {len(holidays_to_add)} holidays')
        
        # Create initial audit log entry
        AuditLog.log_event(
            event_type='system_initialization',
            description='System initialized with default data',
            user_id=None,
            ip_address='127.0.0.1',
            user_agent='System',
            risk_level='low'
        )
        
        # Commit all changes
        app.db.session.commit()
        app.logger.info('✅ Default system data created successfully')
        
    except Exception as e:
        app.db.session.rollback()
        app.logger.error(f'Failed to create default data: {e}')
        raise

def register_cli_commands(app):
    """Register comprehensive CLI commands for system administration"""
    
    @app.cli.command()
    @click.option('--force', is_flag=True, help='Force reset without confirmation')
    def reset_db(force):
        """Reset database completely - WARNING: Deletes all data"""
        if not force:
            click.confirm(
                '⚠️  This will permanently DELETE ALL DATA in the database.\n'
                'This includes all users, employees, attendance records, etc.\n'
                'Are you absolutely sure you want to continue?',
                abort=True
            )
        
        with app.app_context():
            try:
                from models.user import User
                from models.employee import Employee
                from models.holiday import Holiday
                from models.audit import AuditLog
                
                # Drop all tables
                db.drop_all()
                click.echo('🗑️  Dropped all database tables')
                
                # Recreate tables
                db.create_all()
                click.echo('🏗️  Created fresh database tables')
                
                # Create default data
                create_default_system_data(app, User, Employee, Holiday, AuditLog)
                click.echo('👥 Created default users and sample data')
                
                click.echo('✅ Database reset completed successfully!')
                click.echo('\n📋 Default login credentials:')
                click.echo('   HR Manager: hr_manager / manager123')
                click.echo('   Station Managers: [location]_manager / manager123')
                
            except Exception as e:
                click.echo(f'❌ Database reset failed: {e}')
                sys.exit(1)
    
    @app.cli.command()
    def init_db():
        """Initialize database with tables and default data"""
        with app.app_context():
            try:
                from models.user import User
                from models.employee import Employee
                from models.holiday import Holiday
                from models.audit import AuditLog
                
                # Create tables
                db.create_all()
                click.echo('🏗️  Database tables initialized')
                
                # Create default data if needed
                create_default_system_data(app, User, Employee, Holiday, AuditLog)
                click.echo('✅ Database initialization completed!')
                
            except Exception as e:
                click.echo(f'❌ Database initialization failed: {e}')
                sys.exit(1)
    
    @app.cli.command()
    @click.option('--username', prompt=True, help='Admin username')
    @click.option('--email', prompt=True, help='Admin email')
    @click.option('--first-name', prompt=True, help='First name')
    @click.option('--last-name', prompt=True, help='Last name')
    @click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True, help='Password')
    def create_admin(username, email, first_name, last_name, password):
        """Create a new admin user interactively"""
        with app.app_context():
            try:
                from models.user import User
                
                # Check if username exists
                if User.query.filter_by(username=username).first():
                    click.echo('❌ Username already exists!')
                    return
                
                # Check if email exists
                if User.query.filter_by(email=email).first():
                    click.echo('❌ Email already exists!')
                    return
                
                # Create admin user
                user = User(
                    username=username,
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    role='hr_manager',
                    location='head_office',
                    department='hr',
                    is_active=True
                )
                user.set_password(password)
                user.created_date = datetime.utcnow()
                user.last_password_change = datetime.utcnow()
                
                app.db.session.add(user)
                app.db.session.commit()
                
                click.echo(f'✅ Admin user "{username}" created successfully!')
                
            except Exception as e:
                app.db.session.rollback()
                click.echo(f'❌ Failed to create admin user: {e}')
    
    @app.cli.command()
    @click.option('--days', default=30, help='Days of logs to keep')
    def cleanup_logs(days):
        """Clean up old log entries and system data"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        with app.app_context():
            try:
                from models.audit import AuditLog
                
                # Clean old audit logs
                old_logs_count = AuditLog.query.filter(AuditLog.timestamp < cutoff_date).count()
                AuditLog.query.filter(AuditLog.timestamp < cutoff_date).delete()
                
                # Clean old attendance records (optional - keep for compliance)
                # For now, we'll keep all attendance records
                
                db.session.commit()
                
                click.echo(f'✅ Cleaned up {old_logs_count} old audit log entries')
                click.echo(f'   (Logs older than {days} days were removed)')
                
            except Exception as e:
                db.session.rollback()
                click.echo(f'❌ Cleanup failed: {e}')
    
    @app.cli.command()
    def system_status():
        """Show comprehensive system status and health check"""
        with app.app_context():
            try:
                from models.user import User
                from models.employee import Employee
                from models.attendance import AttendanceRecord
                from models.leave import LeaveRequest
                from models.audit import AuditLog
                
                click.echo('=' * 60)
                click.echo('📊 SAKINA GAS ATTENDANCE SYSTEM - STATUS REPORT')
                click.echo('=' * 60)
                
                # Database connectivity test
                try:
                    db.session.execute(text('SELECT 1'))
                    db_status = '✅ Connected'
                except Exception as e:
                    db_status = f'❌ Error: {e.args[0] if e.args else e}'
                
                # System statistics
                stats = {
                    'Database Status': db_status,
                    'Total Users': User.query.count(),
                    'Active Users': User.query.filter_by(is_active=True).count(),
                    'Total Employees': Employee.query.count(),
                    'Active Employees': Employee.query.filter_by(is_active=True).count(),
                    'Today\'s Attendance Records': AttendanceRecord.query.filter_by(date=date.today()).count(),
                    'Pending Leave Requests': LeaveRequest.query.filter(LeaveRequest.status.in_(['pending', 'pending_hr'])).count(), # FIX: Use correct statuses
                    'Audit Log Entries (Last 7 days)': AuditLog.query.filter(
                        AuditLog.timestamp >= datetime.utcnow() - timedelta(days=7)
                    ).count()
                }
                
                # System configuration
                config_info = {
                    'Environment': app.config.get('FLASK_ENV', 'unknown'),
                    'Debug Mode': app.debug,
                    'App Version': app.config.get('APP_VERSION', 'unknown'),
                    'Database URL': app.config['SQLALCHEMY_DATABASE_URI'].split('/')[-1] if 'sqlite' in app.config['SQLALCHEMY_DATABASE_URI'] else 'External DB',
                    'Mail Configured': 'Yes' if app.mail else 'No'
                }
                
                # Display statistics
                click.echo('\n📊 SYSTEM STATISTICS:')
                for key, value in stats.items():
                    click.echo(f'   {key:.<30} {value}')
                
                click.echo('\n⚙️  CONFIGURATION:')
                for key, value in config_info.items():
                    click.echo(f'   {key:.<30} {value}')
                
                # Location breakdown
                click.echo('\n🏢 LOCATION BREAKDOWN:')
                locations = app.config.get('COMPANY_LOCATIONS', {})
                for loc_key, loc_data in locations.items():
                    emp_count = Employee.query.filter_by(location=loc_key, is_active=True).count()
                    click.echo(f'   {loc_data.get("name", loc_key):.<25} {emp_count} employees')
                
                # Recent activity
                click.echo('\n📈 RECENT ACTIVITY (Last 24 hours):')
                recent_logins = AuditLog.query.filter(
                    AuditLog.timestamp >= datetime.utcnow() - timedelta(hours=24),
                    AuditLog.event_type == 'login_successful' # FIX: Use correct event type
                ).count()
                
                recent_attendance = AttendanceRecord.query.filter(
                    AttendanceRecord.date >= date.today() - timedelta(days=1)
                ).count()
                
                click.echo(f'   User Logins:................. {recent_logins}')
                click.echo(f'   Attendance Records:.......... {recent_attendance}')
                
                click.echo('\n' + '=' * 60)
                
            except Exception as e:
                click.echo(f'❌ Error generating status report: {e}')
    
    @app.cli.command()
    def backup_db():
        """Create a backup of the database"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        with app.app_context():
            try:
                import shutil
                import os
                
                # Check for SQLite database file
                db_uri = app.config['SQLALCHEMY_DATABASE_URI']
                if not db_uri.startswith('sqlite:///'):
                    click.echo('⚠️  Skipping backup: Only SQLite databases can be backed up via simple file copy.')
                    return

                db_path = db_uri.replace('sqlite:///', '')
                backup_dir = 'backups'
                
                if not os.path.exists(backup_dir):
                    os.makedirs(backup_dir)
                
                backup_path = os.path.join(backup_dir, f'sakina_attendance_backup_{timestamp}.db')
                shutil.copy2(db_path, backup_path)
                
                click.echo(f'✅ Database backup created: {backup_path}')
                
            except Exception as e:
                click.echo(f'❌ Backup failed: {e}')

# Application routes
def favicon():
    """Serve favicon with proper headers"""
    # NOTE: relies on 'app' being in global scope via __name__ == '__main__'
    # FIX: Need to check if app is available or rely on the werkzeug routing to the static file
    if current_app.debug or current_app.testing:
        return current_app.send_static_file('images/favicon.ico')
    
    response = send_from_directory(
        os.path.join(current_app.root_path, 'static', 'images'),
        'favicon.ico',
        mimetype='image/vnd.microsoft.icon'
    )
    # Cache favicon for 1 week
    response.cache_control.max_age = 604800
    return response

def health_check():
    """Comprehensive health check endpoint for monitoring"""
    with current_app.app_context():
        try:
            from models.user import User # Local import - safe
            
            # Database connectivity test
            db.session.execute(text('SELECT 1'))
            
            # Basic functionality test
            user_count = User.query.count()
            
            health_data = {
                'status': 'healthy',
                'timestamp': datetime.utcnow().isoformat(),
                'version': current_app.config.get('APP_VERSION', '3.0'),
                'environment': current_app.config.get('FLASK_ENV', 'production'),
                'database': {
                    'status': 'connected',
                    'users_count': user_count
                },
                'services': {
                    'database': 'operational',
                    'mail': 'operational' if current_app.mail else 'disabled',
                    'logging': 'operational'
                }
            }
            
            return jsonify(health_data), 200
            
        except Exception as e:
            error_data = {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat(),
                'version': current_app.config.get('APP_VERSION', '3.0')
            }
            return jsonify(error_data), 503

if __name__ == '__main__':
    # Professional application startup
    config_name = os.environ.get('FLASK_CONFIG', 'development')
    app = create_app(config_name)
    
    # Add additional routes
    # FIX: Ensure these rules are added to the application instance
    app.add_url_rule('/favicon.ico', 'favicon', favicon, methods=['GET'])
    app.add_url_rule('/health', 'health_check', health_check, methods=['GET'])
    
    # Professional startup banner
    print("=" * 80)
    print("🏢 SAKINA GAS COMPANY - PROFESSIONAL ATTENDANCE SYSTEM v3.0")
    print("=" * 80)
    print(f"🚀 Environment: {config_name.upper()}")
    print(f"🌐 Server URL: http://localhost:5000")
    print(f"🔧 Health Check: http://localhost:5000/health")
    print("=" * 80)
    print("👤 DEFAULT LOGIN CREDENTIALS:")
    print("   HR Manager:     hr_manager / manager123")
    print("   Dandora Mgr:    dandora_manager / manager123")
    print("   Tassia Mgr:     tassia_manager / manager123")
    print("   Kiambu Mgr:     kiambu_manager / manager123")
    print("=" * 80)
    print("🔧 AVAILABLE CLI COMMANDS:")
    print("   flask init-db           - Initialize database")
    print("   flask reset-db          - Reset database (WARNING!)")
    print("   flask create-admin      - Create new admin user")
    print("   flask system-status     - Show system health")
    print("   flask cleanup-logs      - Clean old audit logs")
    print("   flask backup-db         - Create database backup")
    print("=" * 80)
    
    # System health check on startup
    with app.app_context():
        try:
            from models.user import User # Local import - safe
            from models.employee import Employee # Local import - safe
            
            # Test database connectivity
            db.session.execute(text('SELECT 1'))
            user_count = User.query.count()
            emp_count = Employee.query.filter_by(is_active=True).count()
            
            print(f"📊 System Status: ✅ Connected")
            print(f"👥 Users: {user_count} | 👔 Active Employees: {emp_count}")
            
        except Exception as e:
            print(f"📊 System Status: ❌ Database Error - {e.args[0] if e.args else e}")
            print("⚠️  Run 'flask init-db' to initialize the database")
    
    print("=" * 80)
    print("🎯 System ready! Access the application at: http://localhost:5000")
    print("=" * 80)
    
    # Run the application
    try:
        port = int(os.environ.get('PORT', 5000))
        app.run(
            host='0.0.0.0',
            port=port,
            debug=app.config.get('DEBUG', False),
            threaded=True,
            use_reloader=False  # Disable reloader to prevent double initialization
        )
    except KeyboardInterrupt:
        print("\n🛑 Application stopped by user")
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"\n⚠️  Port {port} is already in use")
            print("   Try using a different port or stop the existing application")
            print(f"   Alternative: python app.py --port {port + 1}")
        else:
            print(f"\n❌ Startup failed: {e}")
    except Exception as e:
        print(f"\n❌ Unexpected error during startup: {e}")
        app.logger.error(f'Application startup failed: {e}', exc_info=True)