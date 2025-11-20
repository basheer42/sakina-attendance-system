"""
Enhanced Employee Management Routes for Sakina Gas Attendance System
Built upon your existing comprehensive employee management with advanced HR features
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from models import db, Employee, AttendanceRecord, LeaveRequest, PerformanceReview, DisciplinaryAction, AuditLog
from datetime import date, datetime, timedelta
from sqlalchemy import func, and_, or_, desc
from werkzeug.utils import secure_filename
import os
import json

employees_bp = Blueprint('employees', __name__)

@employees_bp.route('/')
@employees_bp.route('/list')
@login_required
def list_employees():
    """Enhanced employee listing with advanced filtering and search"""
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
        query = query.filter(Employee.employment_status == 'probation')
    elif status_filter == 'permanent':
        query = query.filter(Employee.employment_status == 'permanent')
    
    if location_filter != 'all' and current_user.role != 'station_manager':
        query = query.filter(Employee.location == location_filter)
    
    if department_filter != 'all':
        query = query.filter(Employee.department == department_filter)
    
    if employment_type_filter != 'all':
        query = query.filter(Employee.employment_type == employment_type_filter)
    
    # Apply search
    if search_query:
        search_term = f"%{search_query}%"
        query = query.filter(
            or_(
                Employee.first_name.ilike(search_term),
                Employee.last_name.ilike(search_term),
                Employee.middle_name.ilike(search_term),
                Employee.employee_id.ilike(search_term),
                Employee.position.ilike(search_term),
                Employee.email.ilike(search_term),
                Employee.phone.ilike(search_term),
                Employee.national_id.ilike(search_term)
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
    per_page = 25
    
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
    if current_user.role == 'station_manager':
        flash('Only HR managers can add new employees.', 'danger')
        return redirect(url_for('employees.list_employees'))
    
    if request.method == 'POST':
        try:
            # Generate unique employee ID
            employee_id = generate_employee_id()
            
            # Create employee with comprehensive data
            employee = Employee(
                employee_id=employee_id,
                first_name=request.form['first_name'].strip(),
                last_name=request.form['last_name'].strip(),
                middle_name=request.form.get('middle_name', '').strip() or None,
                email=request.form.get('email', '').strip().lower() or None,
                phone=request.form.get('phone', '').strip() or None,
                alternative_phone=request.form.get('alternative_phone', '').strip() or None,
                
                # Identity information
                national_id=request.form['national_id'].strip(),
                date_of_birth=datetime.strptime(request.form['date_of_birth'], '%Y-%m-%d').date() if request.form.get('date_of_birth') else None,
                gender=request.form.get('gender', '').strip() or None,
                marital_status=request.form.get('marital_status', '').strip() or None,
                nationality=request.form.get('nationality', 'Kenyan'),
                
                # Address information
                physical_address=request.form.get('physical_address', '').strip() or None,
                postal_address=request.form.get('postal_address', '').strip() or None,
                city=request.form.get('city', '').strip() or None,
                county=request.form.get('county', '').strip() or None,
                
                # Employment information
                location=request.form['location'],
                department=request.form['department'],
                position=request.form['position'].strip(),
                shift=request.form.get('shift') or None,
                employment_type=request.form.get('employment_type', 'permanent'),
                employment_status='probation',  # Default for new employees
                
                # Employment dates
                hire_date=datetime.strptime(request.form['hire_date'], '%Y-%m-%d').date(),
                probation_start=datetime.strptime(request.form['hire_date'], '%Y-%m-%d').date(),
                probation_end=datetime.strptime(request.form['hire_date'], '%Y-%m-%d').date() + timedelta(days=90),
                
                # Compensation
                basic_salary=float(request.form.get('basic_salary', 0)),
                currency='KES',
                
                # Banking information
                bank_name=request.form.get('bank_name', '').strip() or None,
                bank_branch=request.form.get('bank_branch', '').strip() or None,
                bank_account=request.form.get('bank_account', '').strip() or None,
                
                # Emergency contacts
                emergency_contact_name=request.form.get('emergency_contact_name', '').strip() or None,
                emergency_contact_relationship=request.form.get('emergency_contact_relationship', '').strip() or None,
                emergency_contact_phone=request.form.get('emergency_contact_phone', '').strip() or None,
                emergency_contact_address=request.form.get('emergency_contact_address', '').strip() or None,
                
                # Secondary emergency contact
                secondary_emergency_name=request.form.get('secondary_emergency_name', '').strip() or None,
                secondary_emergency_relationship=request.form.get('secondary_emergency_relationship', '').strip() or None,
                secondary_emergency_phone=request.form.get('secondary_emergency_phone', '').strip() or None,
                
                # Additional information
                notes=request.form.get('notes', '').strip() or None,
                
                # System fields
                created_by=current_user.id
            )
            
            # Handle allowances (JSON format)
            allowances = {}
            if request.form.get('transport_allowance'):
                allowances['transport'] = float(request.form['transport_allowance'])
            if request.form.get('housing_allowance'):
                allowances['housing'] = float(request.form['housing_allowance'])
            if request.form.get('meal_allowance'):
                allowances['meal'] = float(request.form['meal_allowance'])
            
            if allowances:
                employee.set_allowances(allowances)
            
            # Handle skills (JSON format)
            skills_input = request.form.get('skills', '').strip()
            if skills_input:
                skills = [skill.strip() for skill in skills_input.split(',') if skill.strip()]
                employee.set_skills(skills)
            
            db.session.add(employee)
            db.session.commit()
            
            # Log the creation
            AuditLog.log_action(
                user_id=current_user.id,
                action='employee_created',
                target_type='employee',
                target_id=employee.id,
                details=f'Created employee {employee.full_name} (ID: {employee.employee_id})',
                ip_address=request.remote_addr
            )
            
            flash(f'Employee {employee.full_name} (ID: {employee.employee_id}) added successfully!', 'success')
            return redirect(url_for('employees.view_employee', id=employee.id))
            
        except ValueError as e:
            flash(f'Invalid data provided: {str(e)}', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding employee: {str(e)}', 'danger')
    
    # Get form data for dropdowns
    form_data = get_employee_form_data()
    
    return render_template('employees/add.html', form_data=form_data)

@employees_bp.route('/<int:id>')
@login_required
def view_employee(id):
    """Enhanced employee profile view with comprehensive information"""
    employee = Employee.query.get_or_404(id)
    
    # Check permissions
    if current_user.role == 'station_manager' and employee.location != current_user.location:
        flash('You can only view employees from your station.', 'danger')
        return redirect(url_for('employees.list_employees'))
    
    # Get comprehensive employee data
    employee_data = get_comprehensive_employee_data(employee)
    
    return render_template('employees/view.html', 
                         employee=employee,
                         employee_data=employee_data)

@employees_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_employee(id):
    """Enhanced employee editing with audit trail"""
    if current_user.role == 'station_manager':
        flash('Only HR managers can edit employee details.', 'danger')
        return redirect(url_for('employees.view_employee', id=id))
    
    employee = Employee.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            # Store old values for audit
            old_values = {
                'first_name': employee.first_name,
                'last_name': employee.last_name,
                'middle_name': employee.middle_name,
                'email': employee.email,
                'phone': employee.phone,
                'position': employee.position,
                'department': employee.department,
                'location': employee.location,
                'basic_salary': float(employee.basic_salary) if employee.basic_salary else 0,
                'employment_status': employee.employment_status
            }
            
            # Update employee details
            employee.first_name = request.form['first_name'].strip()
            employee.last_name = request.form['last_name'].strip()
            employee.middle_name = request.form.get('middle_name', '').strip() or None
            employee.email = request.form.get('email', '').strip().lower() or None
            employee.phone = request.form.get('phone', '').strip() or None
            employee.alternative_phone = request.form.get('alternative_phone', '').strip() or None
            
            # Update employment information
            employee.location = request.form['location']
            employee.department = request.form['department']
            employee.position = request.form['position'].strip()
            employee.shift = request.form.get('shift') or None
            employee.employment_type = request.form.get('employment_type', 'permanent')
            employee.employment_status = request.form['employment_status']
            
            # Update compensation
            employee.basic_salary = float(request.form.get('basic_salary', 0))
            
            # Update banking information
            employee.bank_name = request.form.get('bank_name', '').strip() or None
            employee.bank_branch = request.form.get('bank_branch', '').strip() or None
            employee.bank_account = request.form.get('bank_account', '').strip() or None
            
            # Update emergency contacts
            employee.emergency_contact_name = request.form.get('emergency_contact_name', '').strip() or None
            employee.emergency_contact_relationship = request.form.get('emergency_contact_relationship', '').strip() or None
            employee.emergency_contact_phone = request.form.get('emergency_contact_phone', '').strip() or None
            employee.emergency_contact_address = request.form.get('emergency_contact_address', '').strip() or None
            
            # Update additional information
            employee.notes = request.form.get('notes', '').strip() or None
            
            # System fields
            employee.updated_by = current_user.id
            employee.updated_at = datetime.utcnow()
            
            # Handle probation confirmation
            if (old_values['employment_status'] == 'probation' and 
                employee.employment_status == 'permanent'):
                employee.confirmation_date = date.today()
            
            # Store new values for audit
            new_values = {
                'first_name': employee.first_name,
                'last_name': employee.last_name,
                'middle_name': employee.middle_name,
                'email': employee.email,
                'phone': employee.phone,
                'position': employee.position,
                'department': employee.department,
                'location': employee.location,
                'basic_salary': float(employee.basic_salary) if employee.basic_salary else 0,
                'employment_status': employee.employment_status
            }
            
            db.session.commit()
            
            # Log the update with changes
            AuditLog.log_action(
                user_id=current_user.id,
                action='employee_updated',
                target_type='employee',
                target_id=employee.id,
                old_values=old_values,
                new_values=new_values,
                details=f'Updated employee {employee.full_name}',
                ip_address=request.remote_addr
            )
            
            flash(f'Employee {employee.full_name} updated successfully!', 'success')
            return redirect(url_for('employees.view_employee', id=employee.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating employee: {str(e)}', 'danger')
    
    # Get form data
    form_data = get_employee_form_data()
    
    return render_template('employees/edit.html', 
                         employee=employee, 
                         form_data=form_data)

@employees_bp.route('/<int:id>/deactivate', methods=['POST'])
@login_required
def deactivate_employee(id):
    """Deactivate employee with proper workflow"""
    if current_user.role == 'station_manager':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    employee = Employee.query.get_or_404(id)
    
    try:
        # Store reason for deactivation
        termination_reason = request.json.get('reason', 'No reason provided')
        
        employee.is_active = False
        employee.employment_status = 'terminated'
        employee.termination_date = date.today()
        employee.notes = f"{employee.notes or ''}\n\nTerminated on {date.today().isoformat()}: {termination_reason}".strip()
        employee.updated_by = current_user.id
        
        db.session.commit()
        
        # Log the deactivation
        AuditLog.log_action(
            user_id=current_user.id,
            action='employee_deactivated',
            target_type='employee',
            target_id=employee.id,
            details=f'Deactivated employee {employee.full_name}. Reason: {termination_reason}',
            ip_address=request.remote_addr,
            risk_level='medium'
        )
        
        return jsonify({
            'success': True, 
            'message': f'Employee {employee.full_name} has been deactivated'
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@employees_bp.route('/<int:id>/activate', methods=['POST'])
@login_required
def activate_employee(id):
    """Reactivate employee"""
    if current_user.role == 'station_manager':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    employee = Employee.query.get_or_404(id)
    
    try:
        employee.is_active = True
        employee.employment_status = 'permanent'  # Or previous status
        employee.termination_date = None
        employee.updated_by = current_user.id
        
        db.session.commit()
        
        # Log the activation
        AuditLog.log_action(
            user_id=current_user.id,
            action='employee_activated',
            target_type='employee',
            target_id=employee.id,
            details=f'Reactivated employee {employee.full_name}',
            ip_address=request.remote_addr
        )
        
        return jsonify({
            'success': True, 
            'message': f'Employee {employee.full_name} has been reactivated'
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@employees_bp.route('/<int:id>/performance-review', methods=['GET', 'POST'])
@login_required
def performance_review(id):
    """Conduct performance review for employee"""
    if current_user.role not in ['hr_manager', 'admin']:
        flash('Only HR managers can conduct performance reviews.', 'danger')
        return redirect(url_for('employees.view_employee', id=id))
    
    employee = Employee.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            review = PerformanceReview(
                employee_id=employee.id,
                reviewer_id=current_user.id,
                review_period_start=datetime.strptime(request.form['review_period_start'], '%Y-%m-%d').date(),
                review_period_end=datetime.strptime(request.form['review_period_end'], '%Y-%m-%d').date(),
                review_type=request.form.get('review_type', 'annual'),
                overall_rating=request.form.get('overall_rating'),
                overall_score=float(request.form['overall_score']) if request.form.get('overall_score') else None,
                achievements=request.form.get('achievements', '').strip() or None,
                areas_for_improvement=request.form.get('areas_for_improvement', '').strip() or None,
                goals_for_next_period=request.form.get('goals_for_next_period', '').strip() or None,
                training_recommendations=request.form.get('training_recommendations', '').strip() or None,
                status='completed'
            )
            
            db.session.add(review)
            db.session.commit()
            
            # Log the review
            AuditLog.log_action(
                user_id=current_user.id,
                action='performance_review_completed',
                target_type='performance_review',
                target_id=review.id,
                details=f'Completed performance review for {employee.full_name}',
                ip_address=request.remote_addr
            )
            
            flash(f'Performance review completed for {employee.full_name}', 'success')
            return redirect(url_for('employees.view_employee', id=employee.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error saving performance review: {str(e)}', 'danger')
    
    # Get previous reviews
    previous_reviews = PerformanceReview.query.filter(
        PerformanceReview.employee_id == employee.id
    ).order_by(desc(PerformanceReview.review_period_end)).limit(5).all()
    
    return render_template('employees/performance_review.html',
                         employee=employee,
                         previous_reviews=previous_reviews)

@employees_bp.route('/<int:id>/disciplinary-action', methods=['GET', 'POST'])
@login_required
def disciplinary_action(id):
    """Record disciplinary action for employee"""
    if current_user.role not in ['hr_manager', 'admin']:
        flash('Only HR managers can record disciplinary actions.', 'danger')
        return redirect(url_for('employees.view_employee', id=id))
    
    employee = Employee.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            action = DisciplinaryAction(
                employee_id=employee.id,
                issued_by=current_user.id,
                action_type=request.form['action_type'],
                severity=request.form.get('severity', 'minor'),
                incident_date=datetime.strptime(request.form['incident_date'], '%Y-%m-%d').date(),
                description=request.form['description'].strip(),
                policy_violated=request.form.get('policy_violated', '').strip() or None,
                action_description=request.form['action_description'].strip(),
                effective_date=datetime.strptime(request.form['effective_date'], '%Y-%m-%d').date(),
                expiry_date=datetime.strptime(request.form['expiry_date'], '%Y-%m-%d').date() if request.form.get('expiry_date') else None,
                requires_followup=bool(request.form.get('requires_followup')),
                followup_date=datetime.strptime(request.form['followup_date'], '%Y-%m-%d').date() if request.form.get('followup_date') else None
            )
            
            db.session.add(action)
            db.session.commit()
            
            # Log the disciplinary action
            AuditLog.log_action(
                user_id=current_user.id,
                action='disciplinary_action_recorded',
                target_type='disciplinary_action',
                target_id=action.id,
                details=f'Recorded {action.action_type} for {employee.full_name}',
                ip_address=request.remote_addr,
                risk_level='high'
            )
            
            flash(f'Disciplinary action recorded for {employee.full_name}', 'success')
            return redirect(url_for('employees.view_employee', id=employee.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error recording disciplinary action: {str(e)}', 'danger')
    
    return render_template('employees/disciplinary_action.html', employee=employee)

# Helper Functions

def generate_employee_id():
    """Generate unique employee ID"""
    # Get the last employee ID
    last_employee = Employee.query.order_by(desc(Employee.employee_id)).first()
    
    if last_employee:
        # Extract number from SGC001 format
        try:
            last_num = int(last_employee.employee_id[3:])
            new_num = last_num + 1
        except (ValueError, IndexError):
            new_num = 1
    else:
        new_num = 1
    
    return f"SGC{new_num:03d}"

def get_employee_filter_options(user):
    """Get available filter options based on user role"""
    from config import Config
    
    options = {
        'locations': [],
        'departments': list(Config.DEPARTMENTS.keys()),
        'employment_types': ['permanent', 'contract', 'casual', 'intern'],
        'statuses': ['active', 'inactive', 'probation', 'permanent']
    }
    
    # Locations based on role
    if user.role == 'hr_manager':
        options['locations'] = list(Config.COMPANY_LOCATIONS.keys())
    elif user.role == 'station_manager':
        options['locations'] = [user.location]
    
    return options

def get_employee_summary_stats(user):
    """Get employee summary statistics"""
    if user.role == 'station_manager':
        base_query = Employee.query.filter(Employee.location == user.location)
    else:
        base_query = Employee.query
    
    stats = {
        'total': base_query.count(),
        'active': base_query.filter(Employee.is_active == True).count(),
        'inactive': base_query.filter(Employee.is_active == False).count(),
        'probation': base_query.filter(Employee.employment_status == 'probation').count(),
        'permanent': base_query.filter(Employee.employment_status == 'permanent').count()
    }
    
    return stats

def get_employee_form_data():
    """Get data needed for employee forms"""
    from config import Config
    
    return {
        'locations': Config.COMPANY_LOCATIONS,
        'departments': Config.DEPARTMENTS,
        'employment_types': ['permanent', 'contract', 'casual', 'intern'],
        'employment_statuses': ['probation', 'permanent', 'contract', 'terminated'],
        'genders': ['male', 'female', 'other'],
        'marital_statuses': ['single', 'married', 'divorced', 'widowed', 'separated'],
        'shifts': ['day', 'night'],
        'relationships': ['spouse', 'parent', 'child', 'sibling', 'friend', 'other']
    }

def get_comprehensive_employee_data(employee):
    """Get comprehensive data for employee profile"""
    # Recent attendance (last 30 days)
    thirty_days_ago = date.today() - timedelta(days=30)
    recent_attendance = AttendanceRecord.query.filter(
        AttendanceRecord.employee_id == employee.id,
        AttendanceRecord.date >= thirty_days_ago
    ).order_by(desc(AttendanceRecord.date)).limit(30).all()
    
    # Calculate attendance statistics
    attendance_stats = employee.get_attendance_summary(thirty_days_ago, date.today())
    
    # Leave requests and balances
    current_year = date.today().year
    leave_requests = LeaveRequest.query.filter(
        LeaveRequest.employee_id == employee.id,
        LeaveRequest.start_date >= date(current_year, 1, 1)
    ).order_by(desc(LeaveRequest.created_at)).all()
    
    # Calculate leave balances for all leave types
    leave_types = ['annual_leave', 'sick_leave', 'maternity_leave', 'paternity_leave', 'compassionate_leave']
    leave_balances = {}
    for leave_type in leave_types:
        leave_balances[leave_type] = employee.get_leave_balance(leave_type, current_year)
    
    # Performance reviews
    performance_reviews = PerformanceReview.query.filter(
        PerformanceReview.employee_id == employee.id
    ).order_by(desc(PerformanceReview.review_period_end)).limit(5).all()
    
    # Disciplinary actions
    disciplinary_actions = DisciplinaryAction.query.filter(
        DisciplinaryAction.employee_id == employee.id
    ).order_by(desc(DisciplinaryAction.effective_date)).limit(10).all()
    
    # Audit trail (last 20 entries)
    audit_trail = AuditLog.query.filter(
        AuditLog.target_type == 'employee',
        AuditLog.target_id == employee.id
    ).order_by(desc(AuditLog.timestamp)).limit(20).all()
    
    return {
        'recent_attendance': recent_attendance,
        'attendance_stats': attendance_stats,
        'leave_requests': leave_requests,
        'leave_balances': leave_balances,
        'performance_reviews': performance_reviews,
        'disciplinary_actions': disciplinary_actions,
        'audit_trail': audit_trail,
        'allowances': employee.get_allowances(),
        'skills': employee.get_skills()
    }

# API endpoints
@employees_bp.route('/api/search')
@login_required
def api_employee_search():
    """API endpoint for employee search"""
    query = request.args.get('q', '').strip()
    limit = request.args.get('limit', 10, type=int)
    
    if len(query) < 2:
        return jsonify([])
    
    # Base query based on user role
    if current_user.role == 'station_manager':
        employee_query = Employee.query.filter(
            Employee.location == current_user.location,
            Employee.is_active == True
        )
    else:
        employee_query = Employee.query.filter(Employee.is_active == True)
    
    # Search
    search_term = f"%{query}%"
    employees = employee_query.filter(
        or_(
            Employee.first_name.ilike(search_term),
            Employee.last_name.ilike(search_term),
            Employee.employee_id.ilike(search_term)
        )
    ).limit(limit).all()
    
    results = []
    for emp in employees:
        results.append({
            'id': emp.id,
            'employee_id': emp.employee_id,
            'name': emp.full_name,
            'position': emp.position,
            'location': emp.location,
            'department': emp.department
        })
    
    return jsonify(results)

@employees_bp.route('/api/<int:id>/leave-balance')
@login_required
def api_employee_leave_balance(id):
    """API endpoint for employee leave balance"""
    employee = Employee.query.get_or_404(id)
    
    # Check permissions
    if (current_user.role == 'station_manager' and 
        employee.location != current_user.location):
        return jsonify({'error': 'Unauthorized'}), 403
    
    current_year = date.today().year
    leave_types = ['annual_leave', 'sick_leave', 'maternity_leave', 'paternity_leave']
    
    balances = {}
    for leave_type in leave_types:
        balances[leave_type] = employee.get_leave_balance(leave_type, current_year)
    
    return jsonify({
        'employee_id': employee.id,
        'employee_name': employee.full_name,
        'year': current_year,
        'balances': balances,
        'years_of_service': round(employee.years_of_service, 1),
        'eligible_for_annual': employee.is_eligible_for_annual_leave
    })

@employees_bp.route('/export')
@login_required
def export_employees():
    """Export employee list (placeholder for future implementation)"""
    if current_user.role == 'station_manager':
        flash('Only HR managers can export employee data.', 'danger')
        return redirect(url_for('employees.list_employees'))
    
    # TODO: Implement CSV/Excel export
    flash('Export functionality will be available in the next update.', 'info')
    return redirect(url_for('employees.list_employees'))