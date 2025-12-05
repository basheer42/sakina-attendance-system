"""
Enhanced Employee Management Routes for Sakina Gas Attendance System
COMPLETE VERSION - Built upon existing comprehensive employee management with all advanced HR features
FIXED: Models imported inside functions to prevent mapper conflicts
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app, g
from flask_login import login_required, current_user
# FIXED: Removed global model imports to prevent early model registration
from database import db
from datetime import date, datetime, timedelta
from sqlalchemy import func, and_, or_, desc
from werkzeug.utils import secure_filename
import os
import json

employees_bp = Blueprint('employees', __name__)

def check_employee_permission(permission_level):
    """Check if user has required employee management permission"""
    if current_user.role == 'admin':
        return True
    if current_user.role == 'hr_manager' and permission_level in ['add', 'edit', 'deactivate', 'view']:
        return True
    if current_user.role == 'station_manager' and permission_level in ['view', 'mark']:
        return True
    return False

@employees_bp.route('/')
@employees_bp.route('/list')
@login_required
def list_employees():
    """Enhanced employee listing with advanced filtering and search"""
    # FIXED: Local imports
    from models.employee import Employee
    
    # Check general view permission
    if not check_employee_permission('view'):
        flash('You do not have permission to view the employee list.', 'error')
        return redirect(url_for('dashboard.main'))
    
    # Get filter parameters
    search_query = request.args.get('search', '').strip()
    department_filter = request.args.get('department', '')
    location_filter = request.args.get('location', '')
    employment_type_filter = request.args.get('employment_type', '')
    status_filter = request.args.get('status', 'active')
    sort_by = request.args.get('sort_by', 'employee_id')
    sort_order = request.args.get('sort_order', 'asc')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 25, type=int)
    
    try:
        # Base query with eager loading for performance
        query = Employee.query
        
        # Apply location restriction for station managers
        if current_user.role == 'station_manager':
            query = query.filter(Employee.location == current_user.location)
        elif location_filter and location_filter != 'all':
            query = query.filter(Employee.location == location_filter)
        
        # Apply search filter
        if search_query:
            search_pattern = f"%{search_query}%"
            query = query.filter(or_(
                Employee.first_name.ilike(search_pattern),
                Employee.last_name.ilike(search_pattern),
                Employee.employee_id.ilike(search_pattern),
                Employee.email.ilike(search_pattern),
                Employee.phone_number.ilike(search_pattern),
                Employee.position.ilike(search_pattern)
            ))
        
        # Apply other filters
        if department_filter and department_filter != 'all':
            query = query.filter(Employee.department == department_filter)
        
        if employment_type_filter and employment_type_filter != 'all':
            query = query.filter(Employee.employment_type == employment_type_filter)
        
        if status_filter == 'active':
            query = query.filter(Employee.is_active == True)
        elif status_filter == 'inactive':
            query = query.filter(Employee.is_active == False)
        elif status_filter == 'probation':
            query = query.filter(
                Employee.is_active == True,
                Employee.probation_end_date >= date.today()
            )
        # 'all' means no status filter
        
        # Apply sorting
        sort_column = getattr(Employee, sort_by, Employee.employee_id)
        if sort_order == 'desc':
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(sort_column)
        
        # Paginate results
        employees = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # Get filter options and summary stats
        filter_options = get_employee_filter_options(current_user)
        summary_stats = get_employee_summary_stats(current_user)
        
        return render_template('employees/list.html',
                             employees=employees,
                             filter_options=filter_options,
                             summary_stats=summary_stats,
                             search_query=search_query,
                             department_filter=department_filter,
                             location_filter=location_filter,
                             employment_type_filter=employment_type_filter,
                             status_filter=status_filter,
                             sort_by=sort_by,
                             sort_order=sort_order,
                             per_page=per_page)
                             
    except Exception as e:
        current_app.logger.error(f"Error in employee list: {e}")
        flash('Error loading employee list. Please try again.', 'error')
        return redirect(url_for('dashboard.main'))

@employees_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_employee():
    """Add new employee with comprehensive validation and features"""
    # FIXED: Local imports
    from models.employee import Employee
    from models.audit import AuditLog
    
    if not check_employee_permission('add'):
        flash('You do not have permission to add employees.', 'error')
        return redirect(url_for('employees.list_employees'))
    
    if request.method == 'POST':
        try:
            # Comprehensive form data collection
            employee_data = {
                'employee_id': request.form.get('employee_id', '').strip(),
                'first_name': request.form.get('first_name', '').strip(),
                'last_name': request.form.get('last_name', '').strip(),
                'middle_name': request.form.get('middle_name', '').strip() or None,
                'email': request.form.get('email', '').strip() or None,
                'phone_number': request.form.get('phone_number', '').strip() or None,
                'national_id': request.form.get('national_id', '').strip() or None,
                'date_of_birth': datetime.strptime(request.form.get('date_of_birth'), '%Y-%m-%d').date() if request.form.get('date_of_birth') else None,
                'gender': request.form.get('gender', ''),
                'marital_status': request.form.get('marital_status', ''),
                'address': request.form.get('address', '').strip() or None,
                'department': request.form.get('department', ''),
                'position': request.form.get('position', '').strip(),
                'location': request.form.get('location', ''),
                'shift': request.form.get('shift', 'day'),
                'employment_type': request.form.get('employment_type', 'permanent'),
                'hire_date': datetime.strptime(request.form.get('hire_date'), '%Y-%m-%d').date(),
                'basic_salary': float(request.form.get('basic_salary', 0)),
                'bank_name': request.form.get('bank_name', '').strip() or None,
                'account_number': request.form.get('account_number', '').strip() or None,
                'bank_branch': request.form.get('bank_branch', '').strip() or None,
                'emergency_contact_name': request.form.get('emergency_contact_name', '').strip() or None,
                'emergency_contact_phone': request.form.get('emergency_contact_phone', '').strip() or None,
                'emergency_contact_relationship': request.form.get('emergency_contact_relationship', '').strip() or None,
                'education_level': request.form.get('education_level', '').strip() or None,
                'notes': request.form.get('notes', '').strip() or None
            }
            
            # Comprehensive validation
            validation_errors = validate_employee_data(employee_data)
            if validation_errors:
                for error in validation_errors:
                    flash(error, 'error')
                return render_template('employees/add.html', 
                                     form_data=get_employee_form_data(),
                                     employee_data=employee_data)
            
            # Check for duplicates
            if Employee.query.filter_by(employee_id=employee_data['employee_id']).first():
                flash('Employee ID already exists. Please use a different ID.', 'error')
                return render_template('employees/add.html',
                                     form_data=get_employee_form_data(),
                                     employee_data=employee_data)
            
            if employee_data['email'] and Employee.query.filter_by(email=employee_data['email']).first():
                flash('Email address already exists. Please use a different email.', 'error')
                return render_template('employees/add.html',
                                     form_data=get_employee_form_data(),
                                     employee_data=employee_data)
            
            if employee_data['national_id'] and Employee.query.filter_by(national_id=employee_data['national_id']).first():
                flash('National ID already exists. Please check the ID number.', 'error')
                return render_template('employees/add.html',
                                     form_data=get_employee_form_data(),
                                     employee_data=employee_data)
            
            # Handle allowances
            allowances = {}
            if request.form.get('transport_allowance'):
                allowances['transport'] = float(request.form.get('transport_allowance', 0))
            if request.form.get('housing_allowance'):
                allowances['housing'] = float(request.form.get('housing_allowance', 0))
            if request.form.get('meal_allowance'):
                allowances['meal'] = float(request.form.get('meal_allowance', 0))
            employee_data['allowances'] = allowances
            
            # Handle skills
            skills_input = request.form.get('skills', '').strip()
            if skills_input:
                skills = [skill.strip() for skill in skills_input.split(',') if skill.strip()]
                employee_data['skills'] = skills
            
            # Set probation period if new employee
            if employee_data['employment_type'] == 'permanent':
                probation_months = int(request.form.get('probation_months', 3))
                employee_data['probation_end_date'] = employee_data['hire_date'] + timedelta(days=30 * probation_months)
            
            # Create employee
            employee = Employee(**employee_data)
            db.session.add(employee)
            db.session.flush()  # Get the ID
            
            # Log the action
            AuditLog.log_action(
                user_id=current_user.id,
                action='employee_created',
                table_name='employees',
                record_id=employee.id,
                description=f'Created employee: {employee.get_full_name()} ({employee.employee_id})',
                new_values=employee.to_dict()
            )
            
            db.session.commit()
            
            flash(f'Employee {employee.get_full_name()} has been added successfully.', 'success')
            return redirect(url_for('employees.view_employee', id=employee.id))
            
        except ValueError as e:
            flash(f'Invalid data provided: {str(e)}', 'error')
            db.session.rollback()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error adding employee: {e}')
            flash(f'Error adding employee: {str(e)}', 'error')
        
        # If we get here, there was an error - redisplay form
        return render_template('employees/add.html',
                             form_data=get_employee_form_data(),
                             employee_data=employee_data)
    
    # GET request - show form
    form_data = get_employee_form_data()
    return render_template('employees/add.html', form_data=form_data)

@employees_bp.route('/<int:id>')
@login_required
def view_employee(id):
    """Enhanced employee profile view with comprehensive information"""
    # FIXED: Local imports
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
    
    try:
        # Get comprehensive employee data
        employee_data = get_comprehensive_employee_data(employee)
        
        # Get recent attendance records
        recent_attendance = AttendanceRecord.query.filter_by(
            employee_id=employee.id
        ).order_by(desc(AttendanceRecord.date)).limit(10).all()
        
        # Get recent leave requests
        recent_leaves = LeaveRequest.query.filter_by(
            employee_id=employee.id
        ).filter(
            LeaveRequest.status.in_(['approved', 'pending', 'rejected'])
        ).order_by(desc(LeaveRequest.start_date)).limit(5).all()
        
        # Get performance reviews (if available)
        try:
            performance_reviews = PerformanceReview.query.filter_by(
                employee_id=employee.id
            ).order_by(desc(PerformanceReview.review_date)).limit(3).all()
        except:
            performance_reviews = []
        
        # Get disciplinary actions (if available)
        try:
            disciplinary_actions = DisciplinaryAction.query.filter_by(
                employee_id=employee.id
            ).order_by(desc(DisciplinaryAction.action_date)).limit(3).all()
        except:
            disciplinary_actions = []
        
        # Calculate attendance metrics
        attendance_rate = calculate_employee_attendance_rate(employee)
        punctuality_rate = calculate_employee_punctuality_rate(employee)
        
        return render_template('employees/view.html',
                             employee=employee,
                             employee_data=employee_data,
                             recent_attendance=recent_attendance,
                             recent_leaves=recent_leaves,
                             performance_reviews=performance_reviews,
                             disciplinary_actions=disciplinary_actions,
                             attendance_rate=attendance_rate,
                             punctuality_rate=punctuality_rate)
                             
    except Exception as e:
        current_app.logger.error(f"Error viewing employee {id}: {e}")
        flash('Error loading employee data. Please try again.', 'error')
        return redirect(url_for('employees.list_employees'))

@employees_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required  
def edit_employee(id):
    """Enhanced employee editing with comprehensive validation"""
    # FIXED: Local imports
    from models.employee import Employee
    from models.audit import AuditLog
    
    employee = Employee.query.get_or_404(id)
    
    # Check permissions
    if not check_employee_permission('edit'):
        flash('You do not have permission to edit this employee.', 'error')
        return redirect(url_for('employees.view_employee', id=id))
    
    if current_user.role == 'station_manager' and employee.location != current_user.location:
        flash('You can only edit employees from your station.', 'warning')
        return redirect(url_for('employees.view_employee', id=id))
    
    if request.method == 'POST':
        try:
            # Store old values for audit
            old_values = employee.to_dict()
            
            # Update employee fields
            employee.first_name = request.form.get('first_name', '').strip()
            employee.last_name = request.form.get('last_name', '').strip()
            employee.middle_name = request.form.get('middle_name', '').strip() or None
            
            # Email uniqueness check
            new_email = request.form.get('email', '').strip() or None
            if new_email and new_email != employee.email:
                existing_employee = Employee.query.filter_by(email=new_email).first()
                if existing_employee:
                    flash('An employee with this email already exists.', 'error')
                    return render_template('employees/edit.html', 
                                         employee=employee, 
                                         form_data=get_employee_form_data())
            
            employee.email = new_email
            employee.phone_number = request.form.get('phone_number', '').strip() or None
            employee.address = request.form.get('address', '').strip() or None
            
            # Employment details
            employee.location = request.form.get('location', '')
            employee.department = request.form.get('department', '')
            employee.position = request.form.get('position', '').strip()
            employee.employment_type = request.form.get('employment_type', 'permanent')
            employee.shift = request.form.get('shift', 'day')
            
            # Salary information
            if request.form.get('basic_salary'):
                employee.basic_salary = float(request.form.get('basic_salary'))
            
            # Bank information
            employee.bank_name = request.form.get('bank_name', '').strip() or None
            employee.account_number = request.form.get('account_number', '').strip() or None
            employee.bank_branch = request.form.get('bank_branch', '').strip() or None
            
            # Emergency contact
            employee.emergency_contact_name = request.form.get('emergency_contact_name', '').strip() or None
            employee.emergency_contact_phone = request.form.get('emergency_contact_phone', '').strip() or None
            employee.emergency_contact_relationship = request.form.get('emergency_contact_relationship', '').strip() or None
            
            # Professional info
            employee.education_level = request.form.get('education_level', '').strip() or None
            employee.notes = request.form.get('notes', '').strip() or None
            
            # Update allowances
            allowances = {}
            if request.form.get('transport_allowance'):
                allowances['transport'] = float(request.form.get('transport_allowance', 0))
            if request.form.get('housing_allowance'):
                allowances['housing'] = float(request.form.get('housing_allowance', 0))
            if request.form.get('meal_allowance'):
                allowances['meal'] = float(request.form.get('meal_allowance', 0))
            employee.allowances = allowances
            
            # Update skills
            skills_input = request.form.get('skills', '').strip()
            if skills_input:
                skills = [skill.strip() for skill in skills_input.split(',') if skill.strip()]
                employee.skills = skills
            else:
                employee.skills = []
            
            # Update last modified
            employee.last_updated = datetime.utcnow()
            
            # Log the changes
            AuditLog.log_action(
                user_id=current_user.id,
                action='employee_updated',
                table_name='employees',
                record_id=employee.id,
                description=f'Updated employee: {employee.get_full_name()} ({employee.employee_id})',
                old_values=old_values,
                new_values=employee.to_dict()
            )
            
            db.session.commit()
            
            flash(f'Employee {employee.get_full_name()} has been updated successfully.', 'success')
            return redirect(url_for('employees.view_employee', id=employee.id))
            
        except ValueError as e:
            flash(f'Invalid data provided: {str(e)}', 'error')
            db.session.rollback()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error updating employee {id}: {e}')
            flash(f'Error updating employee: {str(e)}', 'error')
    
    # GET request or error - show form
    form_data = get_employee_form_data()
    return render_template('employees/edit.html', 
                         employee=employee, 
                         form_data=form_data)

@employees_bp.route('/<int:id>/deactivate', methods=['POST'])
@login_required
def deactivate_employee(id):
    """Deactivate employee (soft delete) with comprehensive audit trail"""
    # FIXED: Local imports
    from models.employee import Employee
    from models.audit import AuditLog
    
    employee = Employee.query.get_or_404(id)
    
    # Check permissions
    if not check_employee_permission('deactivate'):
        flash('You do not have permission to deactivate employees.', 'error')
        return redirect(url_for('employees.view_employee', id=id))
    
    if current_user.role == 'station_manager' and employee.location != current_user.location:
        flash('You can only deactivate employees from your station.', 'warning')
        return redirect(url_for('employees.view_employee', id=id))
    
    try:
        reason = request.form.get('reason', '').strip()
        if not reason:
            flash('Deactivation reason is required.', 'error')
            return redirect(url_for('employees.view_employee', id=id))
        
        # Store old values for audit
        old_values = employee.to_dict()
        
        # Deactivate employee
        employee.is_active = False
        employee.deactivation_date = date.today()
        employee.deactivation_reason = reason
        employee.last_updated = datetime.utcnow()
        
        # Log the action
        AuditLog.log_action(
            user_id=current_user.id,
            action='employee_deactivated',
            table_name='employees',
            record_id=employee.id,
            description=f'Deactivated employee: {employee.get_full_name()} ({employee.employee_id}). Reason: {reason}',
            old_values=old_values,
            new_values=employee.to_dict()
        )
        
        db.session.commit()
        
        flash(f'Employee {employee.get_full_name()} has been deactivated.', 'warning')
        return redirect(url_for('employees.list_employees'))
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error deactivating employee {id}: {e}')
        flash(f'Error deactivating employee: {str(e)}', 'error')
        return redirect(url_for('employees.view_employee', id=id))

@employees_bp.route('/<int:id>/reactivate', methods=['POST'])
@login_required
def reactivate_employee(id):
    """Reactivate a deactivated employee"""
    # FIXED: Local imports
    from models.employee import Employee
    from models.audit import AuditLog
    
    employee = Employee.query.get_or_404(id)
    
    # Check permissions
    if current_user.role not in ['hr_manager', 'admin']:
        flash('You do not have permission to reactivate employees.', 'error')
        return redirect(url_for('employees.view_employee', id=id))
    
    try:
        # Store old values for audit
        old_values = employee.to_dict()
        
        # Reactivate employee
        employee.is_active = True
        employee.deactivation_date = None
        employee.deactivation_reason = None
        employee.last_updated = datetime.utcnow()
        
        # Log the action
        AuditLog.log_action(
            user_id=current_user.id,
            action='employee_reactivated',
            table_name='employees',
            record_id=employee.id,
            description=f'Reactivated employee: {employee.get_full_name()} ({employee.employee_id})',
            old_values=old_values,
            new_values=employee.to_dict()
        )
        
        db.session.commit()
        
        flash(f'Employee {employee.get_full_name()} has been reactivated.', 'success')
        return redirect(url_for('employees.view_employee', id=id))
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error reactivating employee {id}: {e}')
        flash(f'Error reactivating employee: {str(e)}', 'error')
        return redirect(url_for('employees.view_employee', id=id))

@employees_bp.route('/export')
@login_required
def export_employees():
    """Export employee data to CSV"""
    # FIXED: Local imports
    from models.employee import Employee
    
    if not check_employee_permission('view'):
        flash('You do not have permission to export employee data.', 'error')
        return redirect(url_for('employees.list_employees'))
    
    try:
        # Get employees based on user role
        if current_user.role == 'station_manager':
            employees = Employee.query.filter_by(
                location=current_user.location
            ).order_by(Employee.employee_id).all()
        else:
            employees = Employee.query.order_by(Employee.employee_id).all()
        
        # Generate CSV response
        from flask import Response
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write headers
        headers = [
            'Employee ID', 'First Name', 'Last Name', 'Email', 'Phone',
            'Department', 'Position', 'Location', 'Hire Date', 'Employment Type',
            'Status', 'Basic Salary'
        ]
        writer.writerow(headers)
        
        # Write employee data
        for employee in employees:
            writer.writerow([
                employee.employee_id,
                employee.first_name,
                employee.last_name,
                employee.email or '',
                employee.phone_number or '',
                employee.department,
                employee.position,
                employee.location,
                employee.hire_date.strftime('%Y-%m-%d') if employee.hire_date else '',
                employee.employment_type,
                'Active' if employee.is_active else 'Inactive',
                employee.basic_salary or 0
            ])
        
        output.seek(0)
        
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename=employees_{date.today().strftime("%Y%m%d")}.csv'}
        )
        
    except Exception as e:
        current_app.logger.error(f'Error exporting employees: {e}')
        flash('Error exporting employee data. Please try again.', 'error')
        return redirect(url_for('employees.list_employees'))

@employees_bp.route('/api/search')
@login_required
def api_search_employees():
    """API endpoint for employee search (for autocomplete, etc.)"""
    # FIXED: Local imports
    from models.employee import Employee
    
    query = request.args.get('q', '').strip()
    limit = min(request.args.get('limit', 10, type=int), 50)  # Max 50 results
    
    if not query or len(query) < 2:
        return jsonify([])
    
    try:
        # Base query
        search_query = Employee.query.filter(Employee.is_active == True)
        
        # Apply location restriction for station managers
        if current_user.role == 'station_manager':
            search_query = search_query.filter(Employee.location == current_user.location)
        
        # Search across multiple fields
        search_pattern = f"%{query}%"
        search_query = search_query.filter(or_(
            Employee.first_name.ilike(search_pattern),
            Employee.last_name.ilike(search_pattern),
            Employee.employee_id.ilike(search_pattern),
            Employee.position.ilike(search_pattern)
        )).limit(limit)
        
        employees = search_query.all()
        
        results = []
        for employee in employees:
            results.append({
                'id': employee.id,
                'employee_id': employee.employee_id,
                'name': employee.get_full_name(),
                'position': employee.position,
                'department': employee.department,
                'location': employee.location
            })
        
        return jsonify(results)
        
    except Exception as e:
        current_app.logger.error(f'Error in employee search: {e}')
        return jsonify([])

# Helper Functions

def get_employee_filter_options(user):
    """Get available filter options based on user role"""
    options = {
        'locations': [],
        'departments': list(current_app.config.get('DEPARTMENTS', {}).keys()),
        'employment_types': ['permanent', 'contract', 'casual', 'intern'],
        'statuses': ['active', 'inactive', 'probation', 'all']
    }
    
    # Locations based on role
    if user.role in ['hr_manager', 'admin']:
        options['locations'] = ['all'] + list(current_app.config.get('COMPANY_LOCATIONS', {}).keys())
    elif user.role == 'station_manager':
        options['locations'] = [user.location]
    
    return options

def get_employee_summary_stats(user):
    """Get employee summary statistics"""
    # FIXED: Local imports
    from models.employee import Employee
    
    if user.role == 'station_manager':
        base_query = Employee.query.filter(Employee.location == user.location)
    else:
        base_query = Employee.query
    
    stats = {
        'total': base_query.count(),
        'active': base_query.filter(Employee.is_active == True).count(),
        'inactive': base_query.filter(Employee.is_active == False).count(),
        'by_department': {},
        'by_location': {}
    }
    
    # Probation count
    try:
        stats['probation'] = base_query.filter(
            Employee.is_active == True,
            Employee.probation_end_date >= date.today()
        ).count()
    except:
        stats['probation'] = 0
    
    # Department breakdown
    try:
        dept_stats = db.session.query(
            Employee.department,
            func.count(Employee.id).label('count')
        ).filter(
            Employee.id.in_(
                db.session.query(Employee.id).filter(
                    Employee.location == user.location if user.role == 'station_manager' else True
                )
            )
        ).group_by(Employee.department).all()
        
        for dept, count in dept_stats:
            stats['by_department'][dept] = count
    except:
        pass
    
    # Location breakdown (for HR managers)
    if user.role in ['hr_manager', 'admin']:
        try:
            location_stats = db.session.query(
                Employee.location,
                func.count(Employee.id).label('count')
            ).filter(Employee.is_active == True).group_by(Employee.location).all()
            
            for location, count in location_stats:
                stats['by_location'][location] = count
        except:
            pass
    
    return stats

def get_employee_form_data():
    """Get form data for employee add/edit forms"""
    return {
        'departments': current_app.config.get('DEPARTMENTS', {}),
        'locations': current_app.config.get('COMPANY_LOCATIONS', {}),
        'employment_types': [
            ('permanent', 'Permanent'),
            ('contract', 'Contract'),
            ('casual', 'Casual'),
            ('intern', 'Intern')
        ],
        'shifts': [
            ('day', 'Day Shift'),
            ('night', 'Night Shift')
        ],
        'genders': [
            ('male', 'Male'),
            ('female', 'Female'),
            ('other', 'Other')
        ],
        'marital_statuses': [
            ('single', 'Single'),
            ('married', 'Married'),
            ('divorced', 'Divorced'),
            ('widowed', 'Widowed')
        ],
        'education_levels': [
            ('primary', 'Primary Education'),
            ('secondary', 'Secondary Education'),
            ('certificate', 'Certificate'),
            ('diploma', 'Diploma'),
            ('bachelor', "Bachelor's Degree"),
            ('master', "Master's Degree"),
            ('phd', 'PhD')
        ]
    }

def validate_employee_data(data):
    """Validate employee data and return list of errors"""
    errors = []
    
    # Required fields
    required_fields = ['employee_id', 'first_name', 'last_name', 'department', 
                      'position', 'location', 'hire_date']
    
    for field in required_fields:
        if not data.get(field):
            field_name = field.replace('_', ' ').title()
            errors.append(f'{field_name} is required.')
    
    # Email validation
    if data.get('email'):
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, data['email']):
            errors.append('Invalid email format.')
    
    # Phone validation
    if data.get('phone_number'):
        phone = re.sub(r'[^\d+]', '', data['phone_number'])
        if len(phone) < 10:
            errors.append('Phone number must be at least 10 digits.')
    
    # Salary validation
    if data.get('basic_salary') and data['basic_salary'] < 0:
        errors.append('Basic salary cannot be negative.')
    
    # Date validations
    if data.get('hire_date'):
        if data['hire_date'] > date.today():
            errors.append('Hire date cannot be in the future.')
    
    if data.get('date_of_birth'):
        age = (date.today() - data['date_of_birth']).days // 365
        if age < 18:
            errors.append('Employee must be at least 18 years old.')
        if age > 70:
            errors.append('Employee age cannot exceed 70 years.')
    
    return errors

def get_comprehensive_employee_data(employee):
    """Get comprehensive data for employee view"""
    # FIXED: Local imports
    from models.attendance import AttendanceRecord
    from models.leave import LeaveRequest
    
    today = date.today()
    current_year = today.year
    
    data = {
        'employment_duration': (today - employee.hire_date).days if employee.hire_date else 0,
        'age': (today - employee.date_of_birth).days // 365 if employee.date_of_birth else None,
        'probation_status': 'Active' if employee.probation_end_date and employee.probation_end_date >= today else 'Completed',
        'total_leave_days_used': 0,
        'total_attendance_records': 0,
        'recent_activities': []
    }
    
    try:
        # Calculate leave days used this year
        leave_days_used = db.session.query(func.sum(LeaveRequest.total_days)).filter(
            LeaveRequest.employee_id == employee.id,
            LeaveRequest.status == 'approved',
            extract('year', LeaveRequest.start_date) == current_year
        ).scalar()
        data['total_leave_days_used'] = int(leave_days_used or 0)
        
        # Count attendance records
        data['total_attendance_records'] = AttendanceRecord.query.filter_by(
            employee_id=employee.id
        ).count()
        
    except Exception as e:
        current_app.logger.error(f"Error getting comprehensive employee data: {e}")
    
    return data

def calculate_employee_attendance_rate(employee):
    """Calculate employee attendance rate for the current month"""
    # FIXED: Local imports
    from models.attendance import AttendanceRecord
    
    try:
        today = date.today()
        start_of_month = today.replace(day=1)
        
        attendance_records = AttendanceRecord.query.filter(
            AttendanceRecord.employee_id == employee.id,
            AttendanceRecord.date >= start_of_month,
            AttendanceRecord.date <= today
        ).all()
        
        if not attendance_records:
            return 0.0
        
        present_count = len([r for r in attendance_records if r.status in ['present', 'late']])
        return round((present_count / len(attendance_records)) * 100, 1)
        
    except Exception:
        return 0.0

def calculate_employee_punctuality_rate(employee):
    """Calculate employee punctuality rate for the current month"""
    # FIXED: Local imports
    from models.attendance import AttendanceRecord
    
    try:
        today = date.today()
        start_of_month = today.replace(day=1)
        
        attendance_records = AttendanceRecord.query.filter(
            AttendanceRecord.employee_id == employee.id,
            AttendanceRecord.date >= start_of_month,
            AttendanceRecord.date <= today,
            AttendanceRecord.status.in_(['present', 'late'])
        ).all()
        
        if not attendance_records:
            return 0.0
        
        on_time_count = len([r for r in attendance_records if r.status == 'present'])
        return round((on_time_count / len(attendance_records)) * 100, 1)
        
    except Exception:
        return 0.0