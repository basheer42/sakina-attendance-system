"""
Employee management routes for Sakina Gas Attendance System
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, Employee
from datetime import date

employees_bp = Blueprint('employees', __name__)

@employees_bp.route('/')
@login_required
def list_employees():
    """List all employees"""
    location_filter = request.args.get('location', 'all')
    
    if current_user.role == 'station_manager' and current_user.location:
        # Station managers can only see their own location
        employees = Employee.query.filter_by(location=current_user.location, is_active=True).all()
    else:
        # HR managers can see all
        if location_filter != 'all':
            employees = Employee.query.filter_by(location=location_filter, is_active=True).all()
        else:
            employees = Employee.query.filter_by(is_active=True).all()
    
    return render_template('employees/list.html', employees=employees, location_filter=location_filter)

@employees_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_employee():
    """Add new employee (HR Manager only)"""
    if current_user.role != 'hr_manager':
        flash('Only HR Manager can add employees', 'error')
        return redirect(url_for('employees.list_employees'))
    
    if request.method == 'POST':
        # Process form data
        employee = Employee(
            employee_id=request.form['employee_id'].strip(),
            first_name=request.form['first_name'].strip(),
            last_name=request.form['last_name'].strip(),
            email=request.form.get('email', '').strip() or None,  # Optional email
            phone=request.form.get('phone', '').strip() or None,
            location=request.form['location'],
            shift=request.form.get('shift') if request.form['location'] != 'head_office' else None,
            department=request.form['department'],
            position=request.form['position'].strip(),
            hire_date=date.fromisoformat(request.form['hire_date']) if request.form['hire_date'] else date.today()
        )
        
        try:
            db.session.add(employee)
            db.session.commit()
            flash(f'Employee {employee.full_name} added successfully!', 'success')
            return redirect(url_for('employees.list_employees'))
        except Exception as e:
            db.session.rollback()
            flash('Error adding employee. Employee ID might already exist.', 'error')
            print(f"Error details: {e}")  # For debugging
    
    return render_template('employees/add.html')