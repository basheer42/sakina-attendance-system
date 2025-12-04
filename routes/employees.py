"""
Enhanced Employee Management Routes for Sakina Gas Attendance System
COMPLETE VERSION - Built upon your existing comprehensive employee management with all advanced HR features
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app, g
from flask_login import login_required, current_user
# FIX: Removed global model imports to prevent early model registration
from database import db
from datetime import date, datetime, timedelta
from sqlalchemy import func, and_, or_, desc
from werkzeug.utils import secure_filename
import os
import json
from config import Config

employees_bp = Blueprint('employees', __name__)

# Mock for current_user.has_permission as it is not implemented in the provided User model
def check_employee_permission(permission_level):
    if current_user.role == 'admin':
        return True
    if current_user.role == 'hr_manager' and permission_level in ['add', 'edit', 'deactivate']:
        return True
    if current_user.role == 'station_manager' and permission_level in ['view', 'mark']:
        return True
    return False

@employees_bp.route('/')
@employees_bp.route('/list')
@login_required
def list_employees():
    """Enhanced employee listing with advanced filtering and search"""
    # FIX: Local imports
    from models.employee import Employee
    
    # Check general view permission
    if not current_user.has_permission('view_location_employees'):
        flash('You do not have permission to view the employee list.', 'danger')
        return redirect(url_for('dashboard.main'))

    # Get filter parameters
    location_filter = request.args.get('location', 'all')
    department_filter = request.args.get('department', 'all')
    status_filter = request.args.get('status', 'active')
    employment_type_filter = request.args.get('employment_type', 'all')
    search_query = request.args.get('search', '').strip()
    sort_by = request.args.get('sort', 'name')
    sort_order = request.args.get('order', 'asc')
    
    # Base query based on user role
    if current_user.role == 'station_manager':
        query = Employee.query.filter(Employee.location == current_user.location)
    else:
        query = Employee.query
    
    # Apply filters
    if status_filter == 'active':
        query = query.filter(Employee.is_active == True)
    elif status_filter == 'inactive':
        query = query.filter(Employee.is_active == False)
    elif status_filter == 'probation':
        query = query.filter(
            Employee.is_active == True,
            Employee.probation_end_date >= date.today()
        )
    elif status_filter == 'all':
        pass # All employees regardless of active status
    
    # Location filter
    if location_filter != 'all':
        # Ensure HR/Admin can filter, but Station Manager is always restricted
        if current_user.role == 'hr_manager' or current_user.role == 'admin':
            query = query.filter(Employee.location == location_filter)
    
    # Department filter  
    if department_filter != 'all':
        query = query.filter(Employee.department == department_filter)
    
    # Employment type filter
    if employment_type_filter != 'all':
        query = query.filter(Employee.employment_type == employment_type_filter)
    
    # Search query
    if search_query:
        search_pattern = f'%{search_query}%'
        query = query.filter(
            or_(
                Employee.first_name.ilike(search_pattern),
                Employee.last_name.ilike(search_pattern),
                Employee.employee_id.ilike(search_pattern),
                Employee.email.ilike(search_pattern),
                Employee.phone.ilike(search_pattern),
                Employee.position.ilike(search_pattern)
            )
        )
    
    # Apply sorting
    if sort_by == 'name':
        if sort_order == 'desc':
            query = query.order_by(desc(Employee.first_name), desc(Employee.last_name))
        else:
            query = query.order_by(Employee.first_name, Employee.last_name)
    elif sort_by == 'employee_id':
        if sort_order == 'desc':
            query = query.order_by(desc(Employee.employee_id))
        else:
            query = query.order_by(Employee.employee_id)
    elif sort_by == 'hire_date':
        if sort_order == 'desc':
            query = query.order_by(desc(Employee.hire_date))
        else:
            query = query.order_by(Employee.hire_date)
    elif sort_by == 'department':
        if sort_order == 'desc':
            query = query.order_by(desc(Employee.department), Employee.first_name)
        else:
            query = query.order_by(Employee.department, Employee.first_name)
    
    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config.get('EMPLOYEES_PER_PAGE', 25)
    
    employees = query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Get filter options
    filter_options = get_employee_filter_options(current_user)
    
    # Get summary statistics
    summary_stats = get_employee_summary_stats(current_user)
    
    return render_template('employees/list.html',
                         employees=employees,
                         filter_options=filter_options,
                         summary_stats=summary_stats,
                         location_filter=location_filter,
                         department_filter=department_filter,
                         status_filter=status_filter,
                         employment_type_filter=employment_type_filter,
                         search_query=search_query,
                         sort_by=sort_by,
                         sort_order=sort_order)

@employees_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_employee():
    """Enhanced employee creation with comprehensive data collection"""
    # FIX: Local imports
    from models.employee import Employee
    from models.audit import AuditLog
    
    # Check for HR/Admin permissions
    if current_user.role not in ['hr_manager', 'admin']:
        flash('Only HR managers and Admins can add new employees.', 'warning')
        return redirect(url_for('employees.list_employees'))
    
    if request.method == 'POST':
        try:
            # Basic validation
            required_fields = [
                'first_name', 'last_name', 'national_id', 'location', 
                'department', 'position', 'hire_date', 'basic_salary', 'employment_type'
            ]
            
            form_data_dict = request.form.to_dict()
            for field in required_fields:
                if not form_data_dict.get(field, '').strip():
                    flash(f'{field.replace("_", " ").title()} is required.', 'danger')
                    return render_template('employees/add.html', form_data=get_employee_form_data(form_data_dict))
            
            # Check for duplicate employee ID and national ID
            employee_id = Employee.generate_employee_id()
            national_id = form_data_dict['national_id'].strip()
            
            if Employee.query.filter_by(national_id=national_id).first():
                flash('An employee with this National ID already exists.', 'danger')
                return render_template('employees/add.html', form_data=get_employee_form_data(form_data_dict))
            
            # Check email uniqueness if provided
            email = form_data_dict.get('email', '').strip()
            if email and Employee.query.filter_by(email=email).first():
                flash('An employee with this email already exists.', 'danger')
                return render_template('employees/add.html', form_data=get_employee_form_data(form_data_dict))
            
            # Parse dates
            hire_date = datetime.strptime(form_data_dict['hire_date'], '%Y-%m-%d').date()
            date_of_birth = None
            if form_data_dict.get('date_of_birth'):
                date_of_birth = datetime.strptime(form_data_dict['date_of_birth'], '%Y-%m-%d').date()
            
            # Create new employee
            employee = Employee(
                employee_id=employee_id,
                first_name=form_data_dict['first_name'].strip(),
                last_name=form_data_dict['last_name'].strip(),
                middle_name=form_data_dict.get('middle_name', '').strip() or None,
                date_of_birth=date_of_birth,
                gender=form_data_dict.get('gender', '') or None,
                
                # Contact information
                email=email or None,
                phone=form_data_dict.get('phone', '').strip() or None,
                address=form_data_dict.get('address', '').strip() or None,
                
                # Government identification
                national_id=national_id,
                kra_pin=form_data_dict.get('kra_pin', '').strip() or None,
                nssf_number=form_data_dict.get('nssf_number', '').strip() or None,
                nhif_number=form_data_dict.get('nhif_number', '').strip() or None,
                
                # Employment details
                location=form_data_dict['location'],
                department=form_data_dict['department'],
                position=form_data_dict['position'].strip(),
                employment_type=form_data_dict['employment_type'],
                shift=form_data_dict.get('shift') or 'day',
                hire_date=hire_date,
                
                # Salary information
                basic_salary=float(form_data_dict['basic_salary']),
                currency='KES',
                
                # Bank information
                bank_name=form_data_dict.get('bank_name', '').strip() or None,
                account_number=form_data_dict.get('account_number', '').strip() or None,
                bank_branch=form_data_dict.get('bank_branch', '').strip() or None,
                
                # System fields
                created_by=current_user.id
            )
            
            # Handle allowances (JSON format)
            allowances = {}
            if form_data_dict.get('transport_allowance'):
                allowances['transport'] = float(form_data_dict['transport_allowance'])
            if form_data_dict.get('housing_allowance'):
                allowances['housing'] = float(form_data_dict['housing_allowance'])
            if form_data_dict.get('meal_allowance'):
                allowances['meal'] = float(form_data_dict['meal_allowance'])
            employee.allowances = allowances
            
            # Handle skills (JSON format)
            skills_input = form_data_dict.get('skills', '').strip()
            if skills_input:
                skills = [skill.strip() for skill in skills_input.split(',') if skill.strip()]
                employee.skills = skills
            
            db.session.add(employee)
            db.session.commit()
            
            # Log the creation
            try:
                AuditLog.log_event(
                    user_id=current_user.id,
                    event_type='employee_created',
                    target_type='employee',
                    target_id=employee.id,
                    target_identifier=employee.employee_id,
                    description=f'Created employee {employee.get_full_name()} (ID: {employee.employee_id})',
                    ip_address=request.remote_addr,
                    event_category='employee'
                )
                db.session.commit()
            except Exception as e:
                current_app.logger.error(f'Audit logging failed after employee creation: {e}')
            
            flash(f'Employee {employee.get_full_name()} (ID: {employee.employee_id}) added successfully!', 'success')
            return redirect(url_for('employees.view_employee', id=employee.id))
            
        except ValueError as e:
            flash(f'Invalid data provided: {str(e)}', 'danger')
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error adding employee: {e}')
            flash(f'Error adding employee: {str(e)}', 'danger')
    
    # GET request - show form
    form_data = get_employee_form_data()
    return render_template('employees/add.html', form_data=form_data)

@employees_bp.route('/<int:id>')
@login_required
def view_employee(id):
    """Enhanced employee profile view with comprehensive information"""
    # FIX: Local imports
    from models.employee import Employee
    from models.attendance import AttendanceRecord
    from models.leave import LeaveRequest
    from models.performance import PerformanceReview
    from models.disciplinary_action import DisciplinaryAction
    
    employee = Employee.query.get_or_404(id)
    
    # Check permissions
    if current_user.role == 'station_manager' and employee.location != current_user.location:
        flash('You can only view employees from your station.', 'warning')
        return redirect(url_for('employees.list_employees'))
    
    # Get comprehensive employee data
    employee_data = get_comprehensive_employee_data(employee)
    
    return render_template('employees/view.html', 
                         employee=employee, 
                         employee_data=employee_data,
                         attendance_rate=employee.get_attendance_rate(),
                         punctuality_rate=employee.get_punctuality_rate(),
                         recent_attendance=employee.attendance_records.order_by(desc(AttendanceRecord.date)).limit(5).all(),
                         recent_leaves=employee.leave_requests.filter(LeaveRequest.status.in_(['approved', 'pending'])).order_by(desc(LeaveRequest.start_date)).limit(5).all(),
                         performance_reviews=employee.performance_reviews.order_by(desc(PerformanceReview.review_date)).limit(3).all(),
                         disciplinary_actions=employee.disciplinary_actions.order_by(desc(DisciplinaryAction.action_date)).limit(3).all(),
                         supervisor=employee.get_supervisor(),
                         direct_reports=employee.get_team_members()
                         )

@employees_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required  
def edit_employee(id):
    """Enhanced employee editing with comprehensive validation"""
    # FIX: Local imports
    from models.employee import Employee
    from models.audit import AuditLog
    
    employee = Employee.query.get_or_404(id)
    
    # Check permissions
    if current_user.role not in ['hr_manager', 'admin']:
        flash('You do not have permission to edit this employee.', 'danger')
        return redirect(url_for('employees.view_employee', id=id))
    
    if request.method == 'POST':
        try:
            # Store old values for audit
            old_values = employee.to_dict(include_sensitive=True) # Full export for comprehensive audit
            
            # Update employee fields
            employee.first_name = request.form['first_name'].strip()
            employee.last_name = request.form['last_name'].strip()
            employee.middle_name = request.form.get('middle_name', '').strip() or None
            
            # Email uniqueness check
            new_email = request.form.get('email', '').strip() or None
            if new_email and new_email != employee.email and Employee.query.filter_by(email=new_email).first():
                 flash('An employee with this email already exists.', 'danger')
                 return render_template('employees/edit.html', employee=employee, form_data=get_employee_form_data())

            employee.email = new_email
            employee.phone = request.form.get('phone', '').strip() or None
            employee.address = request.form.get('address', '').strip() or None
            
            # Employment details
            employee.location = request.form['location']
            employee.department = request.form['department'] 
            employee.position = request.form['position'].strip()
            employee.employment_type = request.form['employment_type']
            employee.shift = request.form.get('shift') or 'day'
            employee.basic_salary = float(request.form['basic_salary'])
            
            # Bank information
            employee.bank_name = request.form.get('bank_name', '').strip() or None
            employee.account_number = request.form.get('account_number', '').strip() or None
            employee.bank_branch = request.form.get('bank_branch', '').strip() or None
            
            # Professional info
            employee.education_level = request.form.get('education_level', '').strip() or None
            employee.notes = request.form.get('notes', '').strip() or None
            
            # Update allowances
            allowances = {}
            if request.form.get('transport_allowance'):
                allowances['transport'] = float(request.form['transport_allowance'])
            if request.form.get('housing_allowance'):
                allowances['housing'] = float(request.form['housing_allowance'])
            if request.form.get('meal_allowance'):
                allowances['meal'] = float(request.form['meal_allowance'])
            employee.allowances = allowances
            
            # Update skills
            skills_input = request.form.get('skills', '').strip()
            if skills_input:
                skills = [skill.strip() for skill in skills_input.split(',') if skill.strip()]
                employee.skills = skills
            else:
                employee.skills = []
            
            employee.last_updated = datetime.utcnow()
            employee.updated_by = current_user.id
            db.session.commit()
            
            # Store new values for audit
            new_values = employee.to_dict(include_sensitive=True) # Full export for comprehensive audit
            
            # Log the update
            try:
                AuditLog.log_data_change( 
                    user_id=current_user.id,
                    target_type='employee',
                    target_id=employee.id,
                    action='updated',
                    description=f'Updated employee {employee.get_full_name()}',
                    old_values=old_values,
                    new_values=new_values,
                    ip_address=request.remote_addr
                )
                db.session.commit()
            except Exception as e:
                current_app.logger.error(f'Audit logging failed: {e}')
            
            flash(f'Employee {employee.get_full_name()} updated successfully!', 'success')
            return redirect(url_for('employees.view_employee', id=employee.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating employee: {str(e)}', 'danger')
    
    # GET request - show form
    form_data = get_employee_form_data()
    return render_template('employees/edit.html', employee=employee, form_data=form_data)

@employees_bp.route('/<int:id>/deactivate', methods=['POST'])
@login_required
def deactivate_employee(id):
    """Deactivate an employee"""
    # FIX: Local imports
    from models.employee import Employee
    from models.audit import AuditLog
    
    if current_user.role not in ['hr_manager', 'admin']:
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    employee = Employee.query.get_or_404(id)
    
    if not employee.is_active:
        return jsonify({'success': False, 'message': 'Employee is already inactive'}), 400

    try:
        reason = request.form.get('reason', 'Deactivated by HR/Admin').strip()
        
        employee.deactivate(reason=reason)
        employee.updated_by = current_user.id
        db.session.commit()
        
        # Log the deactivation
        try:
            AuditLog.log_event( 
                user_id=current_user.id,
                event_type='employee_deactivated',
                target_type='employee',
                target_id=employee.id,
                description=f'Deactivated employee {employee.get_full_name()}. Reason: {reason}',
                ip_address=request.remote_addr,
                event_category='employee'
            )
            db.session.commit()
        except Exception as e:
            current_app.logger.error(f'Audit logging failed: {e}')
        
        return jsonify({'success': True, 'message': f'Employee {employee.get_full_name()} has been deactivated.'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error deactivating employee: {str(e)}'}), 500

@employees_bp.route('/<int:id>/activate', methods=['POST'])
@login_required
def activate_employee(id):
    """Reactivate an employee"""
    # FIX: Local imports
    from models.employee import Employee
    from models.audit import AuditLog
    
    if current_user.role not in ['hr_manager', 'admin']:
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    employee = Employee.query.get_or_404(id)
    
    if employee.is_active:
        return jsonify({'success': False, 'message': 'Employee is already active'}), 400
    
    try:
        employee.reactivate()
        employee.updated_by = current_user.id
        db.session.commit()
        
        # Log the activation
        try:
            AuditLog.log_event( 
                user_id=current_user.id,
                event_type='employee_activated',
                target_type='employee', 
                target_id=employee.id,
                description=f'Activated employee {employee.get_full_name()}',
                ip_address=request.remote_addr,
                event_category='employee'
            )
            db.session.commit()
        except Exception as e:
            current_app.logger.error(f'Audit logging failed: {e}')
        
        return jsonify({'success': True, 'message': f'Employee {employee.get_full_name()} has been activated.'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error activating employee: {str(e)}'}), 500

@employees_bp.route('/<int:id>/performance-review', methods=['GET', 'POST'])
@login_required
def performance_review(id):
    """Add performance review for employee"""
    # FIX: Local imports
    from models.employee import Employee
    from models.performance import PerformanceReview
    from models.audit import AuditLog
    
    employee = Employee.query.get_or_404(id)
    
    # Check permissions
    if current_user.role not in ['hr_manager', 'admin']:
        flash('You do not have permission to record performance reviews.', 'danger')
        return redirect(url_for('employees.view_employee', id=id))
    
    if request.method == 'POST':
        try:
            # FIX: Ensure all required fields are used
            review = PerformanceReview(
                employee_id=employee.id,
                reviewer_id=current_user.id,
                review_type=request.form.get('review_type', 'annual'),
                review_period_start=datetime.strptime(request.form['review_period_start'], '%Y-%m-%d').date(),
                review_period_end=datetime.strptime(request.form['review_period_end'], '%Y-%m-%d').date(),
                review_date=date.today(),
                overall_rating=float(request.form['overall_rating']),
                strengths=request.form.get('strengths', '').strip(),
                areas_for_improvement=request.form.get('areas_for_improvement', '').strip(),
                development_plan=request.form.get('development_plan', '').strip(),
                next_review_date=datetime.strptime(request.form['next_review_date'], '%Y-%m-%d').date()
            )
            
            db.session.add(review)
            db.session.commit()
            
            # Log the review
            try:
                AuditLog.log_event( 
                    user_id=current_user.id,
                    event_type='performance_review_created',
                    target_type='performance_review', # FIX: Correct target type
                    target_id=review.id,
                    description=f'Created performance review for {employee.get_full_name()} (ID: {review.review_number})',
                    ip_address=request.remote_addr,
                    event_category='performance'
                )
                db.session.commit()
            except Exception as e:
                current_app.logger.error(f'Audit logging failed: {e}')
            
            flash(f'Performance review for {employee.get_full_name()} recorded successfully!', 'success')
            return redirect(url_for('employees.view_employee', id=employee.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error recording performance review: {str(e)}', 'danger')
    
    return render_template('employees/performance_review.html', employee=employee)

@employees_bp.route('/<int:id>/disciplinary-action', methods=['GET', 'POST'])
@login_required
def disciplinary_action(id):
    """Record disciplinary action for employee"""
    # FIX: Local imports
    from models.employee import Employee
    from models.disciplinary_action import DisciplinaryAction
    from models.audit import AuditLog
    
    if current_user.role not in ['hr_manager', 'admin']:
        flash('You do not have permission to record disciplinary actions.', 'danger')
        return redirect(url_for('employees.view_employee', id=id))
    
    employee = Employee.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            # FIX: Use helper to set action type if not provided, and set required fields
            action = DisciplinaryAction(
                employee_id=employee.id,
                action_taken_by=current_user.id,
                action_type=request.form.get('action_type', DisciplinaryAction.determine_progressive_discipline_level(employee.id)), # FIX: Use helper method
                incident_description=request.form['incident_description'],
                incident_category=request.form.get('incident_category', 'misconduct').strip(),
                action_description=request.form['action_description'],
                action_reason=request.form.get('action_reason', 'Incident reported'),
                effective_date=datetime.strptime(request.form['effective_date'], '%Y-%m-%d').date(),
                follow_up_required=bool(request.form.get('follow_up_required')),
                follow_up_date=datetime.strptime(request.form['follow_up_date'], '%Y-%m-%d').date() if request.form.get('follow_up_date') else None,
                incident_date=datetime.utcnow()
            )
            
            db.session.add(action)
            db.session.commit()
            
            # Log the disciplinary action
            try:
                AuditLog.log_event( 
                    user_id=current_user.id,
                    event_type='disciplinary_action_recorded',
                    target_type='disciplinary_action', # FIX: Correct target type
                    target_id=action.id,
                    description=f'Recorded {action.action_type} for {employee.get_full_name()}: {action.incident_description}',
                    ip_address=request.remote_addr,
                    event_category='employee'
                )
                db.session.commit()
            except Exception as e:
                current_app.logger.error(f'Audit logging failed: {e}')
            
            flash(f'Disciplinary action for {employee.get_full_name()} recorded successfully!', 'success')
            return redirect(url_for('employees.view_employee', id=employee.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error recording disciplinary action: {str(e)}', 'danger')
    
    return render_template('employees/disciplinary_action.html', employee=employee)

# Helper Functions

# FIX: Removed generate_employee_id as it's defined on the model now

def get_employee_filter_options(user):
    """Get available filter options based on user role"""
    from flask import current_app
    from models.employee import Employee
    
    options = {
        'locations': [],
        'departments': list(current_app.config.get('DEPARTMENTS', {}).keys()),
        'employment_types': ['permanent', 'contract', 'casual', 'intern'],
        'statuses': ['active', 'inactive', 'probation', 'all']
    }
    
    # Locations based on role
    if user.role == 'hr_manager' or user.role == 'admin':
        options['locations'] = ['all'] + list(current_app.config.get('COMPANY_LOCATIONS', {}).keys())
    elif user.role == 'station_manager':
        options['locations'] = [user.location]
    
    return options

def get_employee_summary_stats(user):
    """Get employee summary statistics"""
    # FIX: Local imports
    from models.employee import Employee
    
    if user.role == 'station_manager':
        base_query = Employee.query.filter(Employee.location == user.location)
    else:
        base_query = Employee.query
    
    stats = {
        'total': base_query.count(),
        'active': base_query.filter(Employee.is_active == True).count(),
        'inactive': base_query.filter(Employee.is_active == False).count(),
        'probation': base_query.filter(
            Employee.is_active == True,
            Employee.probation_end_date >= date.today()
        ).count(),
        'by_department': {},
        'by_location': {}
    }
    
    # Department breakdown
    dept_stats = db.session.query(
        Employee.department,
        func.count(Employee.id).label('count')
    ).filter(
        Employee.id.in_([emp.id for emp in base_query.all()])
    ).group_by(Employee.department).all()
    
    for dept, count in dept_stats:
        stats['by_department'][dept] = count
    
    # Location breakdown (for HR managers)
    if user.role == 'hr_manager' or user.role == 'admin':
        location_stats = db.session.query(
            Employee.location,
            func.count(Employee.id).label('count')
        ).filter(Employee.is_active == True).group_by(Employee.location).all()
        
        for location, count in location_stats:
            stats['by_location'][location] = count
    
    return stats

def get_employee_form_data(form_data_dict=None):
    """Get data for employee forms, including optional pre-filled values"""
    from flask import current_app
    
    data = {
        'locations': current_app.config.get('COMPANY_LOCATIONS', {}),
        'departments': current_app.config.get('DEPARTMENTS', {}),
        'employment_types': [
            ('permanent', 'Permanent'),
            ('contract', 'Contract'),
            ('casual', 'Casual'),
            ('intern', 'Intern')
        ],
        'shifts': [
            ('day', 'Day Shift'),
            ('night', 'Night Shift'),
            ('rotating', 'Rotating')
        ],
        'genders': [
            ('male', 'Male'),
            ('female', 'Female'),
            ('other', 'Other')
        ],
        'education_levels': [
            ('primary', 'Primary'),
            ('secondary', 'Secondary'),
            ('diploma', 'Diploma'),
            ('degree', 'Bachelor\'s Degree'),
            ('masters', 'Master\'s Degree'),
            ('phd', 'PhD')
        ],
        'form_data': form_data_dict or {}
    }
    
    return data

def get_comprehensive_employee_data(employee):
    """Get comprehensive data for employee view (Placeholder - data passed directly in route)"""
    # This helper is kept to maintain the original structure but the route now passes data directly
    # from ORM queries.
    return {}

def get_employee_attendance_summary(employee):
    """Get attendance summary for employee using Employee ORM methods"""
    # This helper is replaced by direct calls in the view function for clarity
    return {}

def get_employee_leave_summary(employee):
    """Get leave summary for employee using Employee ORM methods"""
    # This helper is replaced by direct calls in the view function for clarity
    return {}

def get_employee_performance_reviews(employee):
    """Get performance reviews for employee"""
    # This helper is replaced by direct calls in the view function for clarity
    return []

def get_employee_disciplinary_actions(employee):
    """Get disciplinary actions for employee"""
    # This helper is replaced by direct calls in the view function for clarity
    return []

def get_employee_recent_activities(employee):
    """Get recent activities for employee"""
    # This helper is replaced by direct calls in the view function for clarity
    return []

# API endpoints for AJAX requests
@employees_bp.route('/api/search')
@login_required
def api_employee_search():
    """API endpoint for employee search"""
    # FIX: Local imports
    from models.employee import Employee
    
    query = request.args.get('q', '').strip()
    
    if len(query) < 2:
        return jsonify([])
    
    # Base query based on user role
    if current_user.role == 'station_manager':
        base_query = Employee.query.filter(
            Employee.location == current_user.location,
            Employee.is_active == True
        )
    else:
        base_query = Employee.query.filter(Employee.is_active == True)
    
    # Search
    search_pattern = f'%{query}%'
    employees = base_query.filter(
        or_(
            Employee.first_name.ilike(search_pattern),
            Employee.last_name.ilike(search_pattern),
            Employee.employee_id.ilike(search_pattern),
            Employee.email.ilike(search_pattern)
        )
    ).limit(10).all()
    
    results = []
    for emp in employees:
        results.append({
            'id': emp.id,
            'employee_id': emp.employee_id,
            'name': emp.get_full_name(), # FIX: Use get_full_name
            'position': emp.position,
            'department': emp.get_department_display(),
            'location': emp.get_location_display()
        })
    
    return jsonify(results)