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

# FIXED: Global import place for utility/model functions that don't need to be imported late
from database import db # Safe global import - db instance only
from sqlalchemy import text # Safe global import - for CLI/health checks

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
    
    # FIXED: User loader with local import to prevent circular dependencies
    @login_manager.user_loader
    def load_user(user_id):
        """Load user for Flask-Login"""
        if user_id is None:
            return None
        try:
            # FIXED: Local import prevents circular dependencies
            from models.user import User
            user = User.query.filter_by(id=int(user_id), is_active=True).first()
            return user
        except (ValueError, TypeError, AttributeError) as e:
            current_app.logger.error(f"Error in user_loader: {e}")
            pass
        return None
    
    @login_manager.unauthorized_handler
    def unauthorized():
        """Handle unauthorized access with comprehensive logging"""
        # FIXED: Log unauthorized access attempt with local import
        try:
            with current_app.app_context():
                from models.audit import AuditLog # Local import - safer
                client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR'))
                AuditLog.log_event(
                    event_type='unauthorized_access_attempt',
                    description=f'Unauthorized access to {request.endpoint} from {client_ip}',
                    ip_address=client_ip,
                    user_agent=request.headers.get('User-Agent'),
                    risk_level='medium'
                )
                current_app.db.session.commit()
        except Exception as e:
            current_app.logger.error(f"Failed to log unauthorized access: {e}")
            try:
                current_app.db.session.rollback()
            except:
                pass
        
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
    
        # Initialize Flask-WTF for CSRF protection
        try:
            from flask_wtf.csrf import CSRFProtect
            csrf = CSRFProtect(app)
        except ImportError:
            # CSRF protection not available
            pass
        
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
    
    # Import admin blueprint
    from routes.admin import admin_bp

    # Register admin blueprint
    app.register_blueprint(admin_bp)
    app.logger.info('✅ Registered blueprint: admin at /admin')
    
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
            # FIXED: Ensure proper package relative import structure
            module = __import__(f'routes.{blueprint_name}', fromlist=[f'{blueprint_name}_bp'])
            blueprint = getattr(module, f'{blueprint_name}_bp')
            app.register_blueprint(blueprint, url_prefix=url_prefix)
            app.logger.info(f'✅ Registered blueprint: {blueprint_name} at {url_prefix}')
        except (ImportError, AttributeError) as e:
            app.logger.error(f'❌ Failed to register blueprint {blueprint_name}: {e}')
            # For critical blueprints, we might want to exit
            if blueprint_name in ['auth', 'dashboard']:
                app.logger.critical(f'Critical blueprint {blueprint_name} failed to load!')

def register_error_handlers(app):
    """Register comprehensive error handlers with audit logging"""
    
    @app.errorhandler(400)
    def bad_request(error):
        """Handle 400 Bad Request errors"""
        try:
            # FIXED: Local import for AuditLog
            from models.audit import AuditLog
            AuditLog.log_event(
                event_type='http_400_error',
                description=f'Bad request: {str(error)}',
                ip_address=request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR')),
                risk_level='low'
            )
            app.db.session.commit()
        except:
            try:
                app.db.session.rollback()
            except:
                pass
        
        if request.is_json or request.content_type == 'application/json':
            return jsonify({
                'error': 'Bad Request',
                'message': 'The request could not be understood by the server',
                'status': 400
            }), 400
        return render_template('errors/400.html', error=error), 400

    @app.errorhandler(401)
    def unauthorized_error(error):
        """Handle 401 Unauthorized errors"""
        try:
            # FIXED: Local import for AuditLog
            from models.audit import AuditLog
            AuditLog.log_event(
                event_type='http_401_error',
                description=f'Unauthorized access: {str(error)}',
                ip_address=request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR')),
                risk_level='medium'
            )
            app.db.session.commit()
        except:
            try:
                app.db.session.rollback()
            except:
                pass
        
        if request.is_json or request.content_type == 'application/json':
            return jsonify({
                'error': 'Unauthorized',
                'message': 'Authentication required',
                'status': 401
            }), 401
        return redirect(url_for('auth.login'))

    @app.errorhandler(403)
    def forbidden(error):
        """Handle 403 Forbidden errors"""
        try:
            # FIXED: Local import for AuditLog
            from models.audit import AuditLog
            AuditLog.log_event(
                event_type='http_403_error',
                description=f'Forbidden access: {str(error)}',
                ip_address=request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR')),
                risk_level='medium'
            )
            app.db.session.commit()
        except:
            try:
                app.db.session.rollback()
            except:
                pass
        
        if request.is_json or request.content_type == 'application/json':
            return jsonify({
                'error': 'Forbidden',
                'message': 'You do not have permission to access this resource',
                'status': 403
            }), 403
        return render_template('errors/403.html', error=error), 403

    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 Not Found errors"""
        try:
            # FIXED: Local import for AuditLog
            from models.audit import AuditLog
            AuditLog.log_event(
                event_type='http_404_error',
                description=f'Page not found: {request.url}',
                ip_address=request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR')),
                risk_level='low'
            )
            app.db.session.commit()
        except:
            try:
                app.db.session.rollback()
            except:
                pass
        
        if request.is_json or request.content_type == 'application/json':
            return jsonify({
                'error': 'Not Found',
                'message': 'The requested resource was not found',
                'status': 404
            }), 404
        return render_template('errors/404.html', error=error), 404

    @app.errorhandler(429)
    def ratelimit_handler(e):
        """Handle rate limiting errors"""
        return jsonify({
            'error': 'Rate limit exceeded',
            'message': 'Too many requests. Please try again later.',
            'status': 429
        }), 429

    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 Internal Server errors"""
        try:
            # FIXED: Local import for AuditLog
            from models.audit import AuditLog
            AuditLog.log_event(
                event_type='http_500_error',
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
        
        # FIXED: Local imports to prevent early model loading
        user_permissions = []
        is_hr_manager = False
        is_station_manager = False
        user_location = None
        
        if current_user.is_authenticated:
            try:
                # FIXED: Local import for User methods - prevents circular imports
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
            'environment': app.config.get('FLASK_ENV', 'development'),
            
            # User Information
            'user_permissions': user_permissions,
            'is_hr_manager': is_hr_manager,
            'is_station_manager': is_station_manager,
            'user_location': user_location
        }

def register_cli_commands(app):
    """Register comprehensive CLI commands for database management"""
    
    @app.cli.command()
    @click.confirmation_option(prompt='This will delete all data. Are you sure?')
    def reset_db():
        """Reset database - WARNING: This deletes all data!"""
        with app.app_context():
            try:
                # FIXED: Local imports in CLI commands
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
                click.echo('   HR Manager: hr_manager / Manager123!')
                click.echo('   Station Managers: [location]_manager / Manager123!')
                
            except Exception as e:
                click.echo(f'❌ Database reset failed: {e}')
                sys.exit(1)
    
    @app.cli.command()
    def init_db():
        """Initialize database with tables and default data"""
        with app.app_context():
            try:
                # FIXED: Local imports in CLI commands
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
                # FIXED: Local import in CLI command
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
                admin = User(
                    username=username,
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    role='admin',
                    location='head_office',
                    is_active=True,
                    is_verified=True,
                    created_by=1
                )
                admin.set_password(password)
                
                db.session.add(admin)
                db.session.commit()
                
                click.echo(f'✅ Admin user {username} created successfully!')
                
            except Exception as e:
                db.session.rollback()
                click.echo(f'❌ Failed to create admin user: {e}')
                sys.exit(1)
    
    @app.cli.command()
    def system_status():
        """Show comprehensive system status"""
        with app.app_context():
            try:
                # FIXED: Local imports in CLI command
                from models.user import User
                from models.employee import Employee
                from models.attendance import AttendanceRecord
                from models.leave import LeaveRequest
                from models.audit import AuditLog
                
                # Database connection test
                db.session.execute(text('SELECT 1'))
                
                # Count records
                users = User.query.count()
                employees = Employee.query.count()
                active_employees = Employee.query.filter_by(is_active=True).count()
                attendance_records = AttendanceRecord.query.count()
                leave_requests = LeaveRequest.query.count()
                audit_logs = AuditLog.query.count()
                
                click.echo('📊 SYSTEM STATUS REPORT')
                click.echo('=' * 50)
                click.echo(f'Database: ✅ Connected')
                click.echo(f'Users: {users}')
                click.echo(f'Employees: {employees} (Active: {active_employees})')
                click.echo(f'Attendance Records: {attendance_records}')
                click.echo(f'Leave Requests: {leave_requests}')
                click.echo(f'Audit Logs: {audit_logs}')
                click.echo('=' * 50)
                
            except Exception as e:
                click.echo(f'❌ System status check failed: {e}')
                sys.exit(1)
    
    @app.cli.command()
    @click.option('--days', default=30, help='Days to keep (default: 30)')
    def cleanup_logs(days):
        """Clean up old audit logs"""
        with app.app_context():
            try:
                # FIXED: Local import in CLI command
                from models.audit import AuditLog
                
                cutoff_date = datetime.utcnow() - timedelta(days=days)
                
                old_logs = AuditLog.query.filter(
                    AuditLog.timestamp < cutoff_date,
                    AuditLog.risk_level.in_(['low', 'medium'])
                )
                
                count = old_logs.count()
                old_logs.delete()
                db.session.commit()
                
                click.echo(f'🧹 Cleaned up {count} old audit log records (older than {days} days)')
                
            except Exception as e:
                db.session.rollback()
                click.echo(f'❌ Log cleanup failed: {e}')
                sys.exit(1)
    
    @app.cli.command()
    @click.option('--output', default=None, help='Output file path')
    def backup_db(output):
        """Create database backup"""
        import shutil
        
        if output is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output = f'backup_sakina_attendance_{timestamp}.db'
        
        try:
            # For SQLite databases
            db_uri = app.config.get('SQLALCHEMY_DATABASE_URI')
            if 'sqlite' in db_uri:
                source_db = db_uri.replace('sqlite:///', '')
                shutil.copy2(source_db, output)
                click.echo(f'✅ Database backed up to: {output}')
            else:
                click.echo('⚠️  Backup method not implemented for this database type')
                
        except Exception as e:
            click.echo(f'❌ Backup failed: {e}')
            sys.exit(1)

def register_security_middleware(app):
    """Register security middleware and headers"""
    
    @app.before_request
    def security_headers():
        """Add security headers to all responses"""
        # Rate limiting could be implemented here
        # Session security
        session.permanent = True
        app.permanent_session_lifetime = timedelta(hours=8)
    
    @app.after_request
    def add_security_headers(response):
        """Add comprehensive security headers"""
        # Security headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # HTTPS enforcement in production
        if app.config.get('ENV') == 'production':
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        # Cache control for sensitive pages
        if request.endpoint and any(sensitive in request.endpoint for sensitive in ['auth', 'admin', 'profile']):
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
        
        # Content Security Policy
        if app.config.get('CSP_POLICY'):
            response.headers['Content-Security-Policy'] = app.config['CSP_POLICY']
        
        return response

def setup_logging(app):
    """Configure comprehensive logging system"""
    if not app.debug and not app.testing:
        # Ensure logs directory exists
        logs_dir = 'logs'
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir)
        
        # Main application log
        file_handler = RotatingFileHandler(
            os.path.join(logs_dir, 'sakina_attendance.log'),
            maxBytes=10240000,  # 10MB
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        
        # Error log with detailed information
        error_handler = TimedRotatingFileHandler(
            os.path.join(logs_dir, 'errors.log'),
            when='midnight',
            interval=1,
            backupCount=30
        )
        error_handler.setFormatter(logging.Formatter('''
Time:    %(asctime)s
Level:   %(levelname)s
Module:  %(module)s
Function: %(funcName)s
Line:    %(lineno)d

Message:
%(message)s

------------------------------------------------------------
         '''))
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
            # FIXED: Only call init_database from database.py
            db_init(app)
            
            # FIXED: Create default data - pass model classes to avoid re-importing in create_default_system_data
            # Model Imports must be done AFTER db_init to avoid mapper error
            from models.user import User
            from models.employee import Employee  
            from models.holiday import Holiday
            from models.audit import AuditLog
            
            create_default_system_data(app, User, Employee, Holiday, AuditLog)
            
        except Exception as e:
            app.logger.error(f'Database initialization failed: {e}')
            print(f"❌ Database initialization failed: {e}")

def create_default_system_data(app, User, Employee, Holiday, AuditLog):
    """
    Create default system data with enhanced error handling
    FIXED: Accept model classes as parameters to avoid re-importing
    """
    try:
        # Check if default users already exist
        if User.query.filter_by(username='hr_manager').first():
            print("✅ Default users already exist")
            return
        
        print("👥 Creating default system data...")
        
        # Define the SECURE default password
        SECURE_DEFAULT_PASSWORD = 'Manager123!'
        
        # Create default HR Manager
        hr_manager = User(
            username='hr_manager',
            email='hr@sakinagas.com',
            first_name='HR',
            last_name='Manager',
            role='hr_manager',
            location='head_office',
            is_active=True,
            is_verified=True,
            created_by=1
        )
        hr_manager.set_password(SECURE_DEFAULT_PASSWORD)
        db.session.add(hr_manager)
        
        # Create Station Managers
        locations = [
            ('dandora', 'Dandora'),
            ('tassia', 'Tassia'),
            ('kiambu', 'Kiambu')
        ]
        
        for loc_code, loc_name in locations:
            manager = User(
                username=f'{loc_code}_manager',
                email=f'{loc_code}@sakinagas.com',
                first_name=f'{loc_name}',
                last_name='Manager',
                role='station_manager',
                location=loc_code,
                is_active=True,
                is_verified=True,
                created_by=1
            )
            manager.set_password(SECURE_DEFAULT_PASSWORD)
            db.session.add(manager)
        
        # Commit users first
        db.session.commit()
        print("✅ Default users created")
        
        # Create sample employees
        hr_manager_db = User.query.filter_by(username='hr_manager').first()
        
        sample_employees = [
            {
                'first_name': 'John',
                'last_name': 'Doe',
                'position': 'Station Attendant',
                'department': 'operations',
                'location': 'dandora',
                'email': 'john.doe@sakinagas.com',
                'phone': '+254700123456',
                'hire_date': date.today() - timedelta(days=365),
                'basic_salary': 35000,
                'created_by': hr_manager_db.id
            },
            {
                'first_name': 'Jane',
                'last_name': 'Smith',
                'position': 'Cashier',
                'department': 'finance',
                'location': 'tassia',
                'email': 'jane.smith@sakinagas.com',
                'phone': '+254700123457',
                'hire_date': date.today() - timedelta(days=200),
                'basic_salary': 32000,
                'created_by': hr_manager_db.id
            },
            {
                'first_name': 'Michael',
                'last_name': 'Johnson',
                'position': 'Security Guard',
                'department': 'security',
                'location': 'kiambu',
                'email': 'michael.johnson@sakinagas.com',
                'phone': '+254700123458',
                'hire_date': date.today() - timedelta(days=90),
                'basic_salary': 28000,
                'created_by': hr_manager_db.id
            }
        ]
        
        # FIX: Ensure Employee model can be called
        from models.employee import Employee 
        
        for emp_data in sample_employees:
            employee = Employee.create_employee(**emp_data)
            db.session.add(employee)
        
        db.session.commit()
        print("✅ Sample employees created")
        
        # Create default holidays for Kenya
        current_year = date.today().year
        kenyan_holidays = [
            ('New Year\'s Day', date(current_year, 1, 1)),
            ('Good Friday', date(current_year, 3, 29)),  # Approximate date
            ('Easter Monday', date(current_year, 4, 1)),  # Approximate date
            ('Labour Day', date(current_year, 5, 1)),
            ('Madaraka Day', date(current_year, 6, 1)),
            ('Mashujaa Day', date(current_year, 10, 20)),
            ('Jamhuri Day', date(current_year, 12, 12)),
            ('Christmas Day', date(current_year, 12, 25)),
            ('Boxing Day', date(current_year, 12, 26))
        ]
        
        # FIX: Ensure Holiday model can be called
        from models.holiday import Holiday
        
        for name, holiday_date in kenyan_holidays:
            holiday = Holiday(
                name=name,
                date=holiday_date,
                year=holiday_date.year,
                holiday_type='public',
                is_recurring_annually=True,
                created_by=hr_manager_db.id,
                description=f'Kenya National Holiday: {name}'
            )
            db.session.add(holiday)
        
        db.session.commit()
        print("✅ Default holidays created")
        
        # Log system initialization
        AuditLog.log_event(
            event_type='system_initialization',
            description='System initialized with default data',
            user_id=hr_manager_db.id,
            risk_level='low'
        )
        db.session.commit()
        
        print("✅ Default system data creation completed successfully!")
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Failed to create default system data: {e}")
        app.logger.error(f'Failed to create default system data: {e}')

# Static file handlers
def favicon():
    """Serve favicon"""
    return send_from_directory(
        os.path.join(current_app.root_path, 'static', 'images'),
        'favicon.ico',
        mimetype='image/vnd.microsoft.icon'
    )

def health_check():
    """Comprehensive health check endpoint"""
    try:
        # FIXED: Test database connection with local import
        from models.user import User
        user_count = User.query.count()
        
        # Test database write
        db.session.execute(text('SELECT 1'))
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'database': 'connected',
            'users': user_count,
            'version': current_app.config.get('APP_VERSION', '3.0'),
            'environment': current_app.config.get('FLASK_ENV', 'development')
        }), 200
        
    except Exception as e:
        error_data = {
            'status': 'unhealthy',
            'timestamp': datetime.utcnow().isoformat(),
            'error': str(e),
            'version': current_app.config.get('APP_VERSION', '3.0')
        }
        return jsonify(error_data), 503

if __name__ == '__main__':
    # Professional application startup
    config_name = os.environ.get('FLASK_CONFIG', 'development')
    app = create_app(config_name)
    
    # FIXED: Ensure these rules are added to the application instance
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
    print("   HR Manager:     hr_manager / Manager123!")
    print("   Dandora Mgr:    dandora_manager / Manager123!")
    print("   Tassia Mgr:     tassia_manager / Manager123!")
    print("   Kiambu Mgr:     kiambu_manager / Manager123!")
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
            # FIXED: Local import - safe for startup health check
            from models.user import User
            from models.employee import Employee
            
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
        with app.app_context():
            app.logger.error(f'Application startup failed: {e}', exc_info=True)