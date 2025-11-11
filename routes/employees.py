"""
Employee management routes for Sakina Gas Attendance System
Add, edit, view, and manage employee records
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, Employee, User, AuditLog, AttendanceRecord, LeaveRequest
from datetime import date, datetime

employees_bp = Blueprint('employees', __name__)

@employees_bp.route('/')
@login_required
def list_employees():
    """List all employees with filtering"""
    location_filter = request.args.get('location', 'all')
    status_filter = request.args.get('status', 'active')
    search_query = request.args.get('search', '').strip()
    
    # Base query
    query = db.select(Employee)
    
    # Apply filters based on user role
    if current_user.role == 'station_manager':
        query = query.where(Employee.location == current_user.location)
    elif location_filter != 'all':
        query = query.where(Employee.location == location_filter)
    
    # Status filter
    if status_filter == 'active':
        query = query.where(Employee.is_active == True)
    elif status_filter == 'inactive':
        query = query.where(Employee.is_active == False)
    
    # Search filter
    if search_query:
        search_pattern = f"%{search_query}%"
        query = query.where(
            db.or_(
                Employee.first_name.ilike(search_pattern),
                Employee.last_name.ilike(search_pattern),
                Employee.employee_id.ilike(search_pattern),
                Employee.email.ilike(search_pattern),
                Employee.position.ilike(search_pattern)
            )
        )
    
    # Order by name
    query = query.order_by(Employee.first_name, Employee.last_name)
    
    employees = db.session.execute(query).scalars().all()
    
    return render_template('employees/list.html',
                         employees=employees,
                         location_filter=location_filter,
                         status_filter=status_filter,
                         search_query=search_query)

@employees_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_employee():
    """Add a new employee"""
    # Only HR managers can add employees
    if current_user.role != 'hr_manager':
        flash('Access denied. Only HR managers can add employees.', 'error')
        return redirect(url_for('employees.list_employees'))
    
    if request.method == 'POST':
        # Get form data
        employee_id = request.form['employee_id'].strip().upper()
        first_name = request.form['first_name'].strip()
        last_name = request.form['last_name'].strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        location = request.form['location']
        shift = request.form.get('shift', None)
        department = request.form['department']
        position = request.form['position'].strip()
        hire_date_str = request.form['hire_date']
        salary = request.form.get('salary', '').strip()
        national_id = request.form.get('national_id', '').strip()
        emergency_contact = request.form.get('emergency_contact', '').strip()
        emergency_phone = request.form.get('emergency_phone', '').strip()
        
        # Validation
        if not all([employee_id, first_name, last_name, location, department, position, hire_date_str]):
            flash('Please fill in all required fields', 'error')
            return render_template('employees/add.html')
        
        # Validate employee ID uniqueness
        existing_employee = db.session.execute(
            db.select(Employee).where(Employee.employee_id == employee_id)
        ).scalar_one_or_none()
        
        if existing_employee:
            flash(f'Employee ID {employee_id} already exists', 'error')
            return render_template('employees/add.html')
        
        # Validate email uniqueness if provided
        if email:
            existing_email = db.session.execute(
                db.select(Employee).where(Employee.email == email)
            ).scalar_one_or_none()
            
            if existing_email:
                flash(f'Email {email} is already in use', 'error')
                return render_template('employees/add.html')
        
        # Parse hire date
        try:
            hire_date = date.fromisoformat(hire_date_str)
        except ValueError:
            flash('Invalid hire date format', 'error')
            return render_template('employees/add.html')
        
        # Parse salary
        salary_amount = None
        if salary:
            try:
                salary_amount = float(salary.replace(',', ''))
            except ValueError:
                flash('Invalid salary amount', 'error')
                return render_template('employees/add.html')
        
        # Validate shift requirement
        if location in ['dandora', 'tassia', 'kiambu'] and not shift:
            flash('Shift is required for station employees', 'error')
            return render_template('employees/add.html')
        
        # Create employee
        try:
            employee = Employee(
                employee_id=employee_id,
                first_name=first_name,
                last_name=last_name,
                email=email if email else None,
                phone=phone if phone else None,
                location=location,
                shift=shift if shift else None,
                department=department,
                position=position,
                hire_date=hire_date,
                salary=salary_amount,
                national_id=national_id if national_id else None,
                emergency_contact=emergency_contact if emergency_contact else None,
                emergency_phone=emergency_phone if emergency_phone else None
            )
            
            db.session.add(employee)
            
            # Create audit log
            audit_log = AuditLog(
                user_id=current_user.id,
                action='create_employee',
                target_type='employee',
                target_id=employee.id,
                details=f'Created employee {employee_id}: {first_name} {last_name}',
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent', '')[:255]
            )
            db.session.add(audit_log)
            
            db.session.commit()
            
            flash(f'Employee {employee.full_name} (ID: {employee_id}) added successfully', 'success')
            return redirect(url_for('employees.list_employees'))
            
        except Exception as e:
            db.session.rollback()
            flash('Error adding employee. Please check your input and try again.', 'error')
            print(f"Error details: {e}")
    
    return render_template('employees/add.html')

@employees_bp.route('/view/<employee_id>')
@login_required
def view_employee(employee_id):
    """View employee details"""
    employee = db.session.execute(
        db.select(Employee).where(Employee.employee_id == employee_id)
    ).scalar_one_or_none()
    
    if not employee:
        flash('Employee not found', 'error')
        return redirect(url_for('employees.list_employees'))
    
    # Check permissions
    if current_user.role == 'station_manager' and employee.location != current_user.location:
        flash('Access denied. You can only view employees from your location.', 'error')
        return redirect(url_for('employees.list_employees'))
    
    # Get recent attendance records
    recent_attendance = db.session.execute(
        db.select(AttendanceRecord)
        .where(AttendanceRecord.employee_id == employee.id)
        .order_by(AttendanceRecord.date.desc())
        .limit(10)
    ).scalars().all()
    
    # Get recent leave requests
    recent_leaves = db.session.execute(
        db.select(LeaveRequest)
        .where(LeaveRequest.employee_id == employee.id)
        .order_by(LeaveRequest.created_at.desc())
        .limit(5)
    ).scalars().all()
    
    return render_template('employees/view.html',
                         employee=employee,
                         recent_attendance=recent_attendance,
                         recent_leaves=recent_leaves)

@employees_bp.route('/edit/<employee_id>', methods=['GET', 'POST'])
@login_required
def edit_employee(employee_id):
    """Edit employee details"""
    # Only HR managers can edit employees
    if current_user.role != 'hr_manager':
        flash('Access denied. Only HR managers can edit employees.', 'error')
        return redirect(url_for('employees.view_employee', employee_id=employee_id))
    
    employee = db.session.execute(
        db.select(Employee).where(Employee.employee_id == employee_id)
    ).scalar_one_or_none()
    
    if not employee:
        flash('Employee not found', 'error')
        return redirect(url_for('employees.list_employees'))
    
    if request.method == 'POST':
        # Get form data
        first_name = request.form['first_name'].strip()
        last_name = request.form['last_name'].strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        location = request.form['location']
        shift = request.form.get('shift', None)
        department = request.form['department']
        position = request.form['position'].strip()
        salary = request.form.get('salary', '').strip()
        national_id = request.form.get('national_id', '').strip()
        emergency_contact = request.form.get('emergency_contact', '').strip()
        emergency_phone = request.form.get('emergency_phone', '').strip()
        is_active = bool(request.form.get('is_active'))
        
        # Validation
        if not all([first_name, last_name, location, department, position]):
            flash('Please fill in all required fields', 'error')
            return render_template('employees/edit.html', employee=employee)
        
        # Validate email uniqueness if changed
        if email and email != employee.email:
            existing_email = db.session.execute(
                db.select(Employee).where(
                    Employee.email == email,
                    Employee.id != employee.id
                )
            ).scalar_one_or_none()
            
            if existing_email:
                flash(f'Email {email} is already in use', 'error')
                return render_template('employees/edit.html', employee=employee)
        
        # Parse salary
        salary_amount = None
        if salary:
            try:
                salary_amount = float(salary.replace(',', ''))
            except ValueError:
                flash('Invalid salary amount', 'error')
                return render_template('employees/edit.html', employee=employee)
        
        # Validate shift requirement
        if location in ['dandora', 'tassia', 'kiambu'] and not shift:
            flash('Shift is required for station employees', 'error')
            return render_template('employees/edit.html', employee=employee)
        
        # Update employee
        try:
            # Track changes for audit
            changes = []
            if employee.first_name != first_name:
                changes.append(f"first_name: {employee.first_name} → {first_name}")
                employee.first_name = first_name
            if employee.last_name != last_name:
                changes.append(f"last_name: {employee.last_name} → {last_name}")
                employee.last_name = last_name
            if employee.email != (email if email else None):
                changes.append(f"email: {employee.email} → {email}")
                employee.email = email if email else None
            if employee.phone != (phone if phone else None):
                changes.append(f"phone: {employee.phone} → {phone}")
                employee.phone = phone if phone else None
            if employee.location != location:
                changes.append(f"location: {employee.location} → {location}")
                employee.location = location
            if employee.shift != (shift if shift else None):
                changes.append(f"shift: {employee.shift} → {shift}")
                employee.shift = shift if shift else None
            if employee.department != department:
                changes.append(f"department: {employee.department} → {department}")
                employee.department = department
            if employee.position != position:
                changes.append(f"position: {employee.position} → {position}")
                employee.position = position
            if employee.salary != salary_amount:
                changes.append(f"salary: {employee.salary} → {salary_amount}")
                employee.salary = salary_amount
            if employee.national_id != (national_id if national_id else None):
                changes.append(f"national_id: {employee.national_id} → {national_id}")
                employee.national_id = national_id if national_id else None
            if employee.emergency_contact != (emergency_contact if emergency_contact else None):
                changes.append(f"emergency_contact: {employee.emergency_contact} → {emergency_contact}")
                employee.emergency_contact = emergency_contact if emergency_contact else None
            if employee.emergency_phone != (emergency_phone if emergency_phone else None):
                changes.append(f"emergency_phone: {employee.emergency_phone} → {emergency_phone}")
                employee.emergency_phone = emergency_phone if emergency_phone else None
            if employee.is_active != is_active:
                changes.append(f"is_active: {employee.is_active} → {is_active}")
                employee.is_active = is_active
            
            employee.updated_at = datetime.utcnow()
            
            # Create audit log
            if changes:
                audit_log = AuditLog(
                    user_id=current_user.id,
                    action='edit_employee',
                    target_type='employee',
                    target_id=employee.id,
                    details=f'Updated employee {employee.employee_id}: {"; ".join(changes)}',
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get('User-Agent', '')[:255]
                )
                db.session.add(audit_log)
            
            db.session.commit()
            
            if changes:
                flash(f'Employee {employee.full_name} updated successfully', 'success')
            else:
                flash('No changes were made', 'info')
            
            return redirect(url_for('employees.view_employee', employee_id=employee_id))
            
        except Exception as e:
            db.session.rollback()
            flash('Error updating employee. Please try again.', 'error')
            print(f"Error details: {e}")
    
    return render_template('employees/edit.html', employee=employee)

@employees_bp.route('/deactivate/<employee_id>')
@login_required
def deactivate_employee(employee_id):
    """Deactivate an employee"""
    # Only HR managers can deactivate employees
    if current_user.role != 'hr_manager':
        flash('Access denied. Only HR managers can deactivate employees.', 'error')
        return redirect(url_for('employees.list_employees'))
    
    employee = db.session.execute(
        db.select(Employee).where(Employee.employee_id == employee_id)
    ).scalar_one_or_none()
    
    if not employee:
        flash('Employee not found', 'error')
        return redirect(url_for('employees.list_employees'))
    
    if not employee.is_active:
        flash(f'Employee {employee.full_name} is already inactive', 'warning')
        return redirect(url_for('employees.view_employee', employee_id=employee_id))
    
    try:
        employee.is_active = False
        employee.updated_at = datetime.utcnow()
        
        # Create audit log
        audit_log = AuditLog(
            user_id=current_user.id,
            action='deactivate_employee',
            target_type='employee',
            target_id=employee.id,
            details=f'Deactivated employee {employee.employee_id}: {employee.full_name}',
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', '')[:255]
        )
        db.session.add(audit_log)
        
        db.session.commit()
        
        flash(f'Employee {employee.full_name} has been deactivated', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash('Error deactivating employee. Please try again.', 'error')
        print(f"Error details: {e}")
    
    return redirect(url_for('employees.view_employee', employee_id=employee_id))