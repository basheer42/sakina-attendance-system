"""
Leave management routes for Sakina Gas Attendance System
FIXED VERSION: Proper route naming to resolve URL building errors
Enhanced with Kenyan Labor Law Compliance
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from models import db, Employee, LeaveRequest, User
from datetime import date, datetime, timedelta

leaves_bp = Blueprint('leaves', __name__)

@leaves_bp.route('/')
@login_required
def list_requests():
    """List all leave requests - FIXED route name"""
    status_filter = request.args.get('status', 'all')
    
    # Build query based on user role
    if current_user.role == 'station_manager':
        # Station managers only see their location
        employees_query = db.select(Employee).where(
            Employee.location == current_user.location,
            Employee.is_active == True
        )
        employees = db.session.execute(employees_query).scalars().all()
        employee_ids = [emp.id for emp in employees]
        
        query = db.select(LeaveRequest).where(
            LeaveRequest.employee_id.in_(employee_ids)
        )
    else:
        # HR managers see all leave requests
        query = db.select(LeaveRequest)
    
    # Apply status filter
    if status_filter != 'all':
        query = query.where(LeaveRequest.status == status_filter)
    
    # Order by most recent
    query = query.order_by(LeaveRequest.created_at.desc())
    leave_requests = db.session.execute(query).scalars().all()
    
    return render_template('leaves/list.html', 
                         leave_requests=leave_requests, 
                         status_filter=status_filter)

# FIXED: Adding this alias for backward compatibility
@leaves_bp.route('/list')
@login_required
def list_leaves():
    """Alias for list_requests to fix URL routing"""
    return list_requests()

@leaves_bp.route('/request', methods=['GET', 'POST'])
@login_required
def request_leave():
    """Request leave for an employee with Kenyan law compliance"""
    if request.method == 'POST':
        employee_id = request.form['employee_id']
        leave_type = request.form['leave_type']
        start_date = date.fromisoformat(request.form['start_date'])
        end_date = date.fromisoformat(request.form['end_date'])
        reason = request.form['reason']
        override_warning = request.form.get('override_warning', False)
        
        # Get employee
        employee = db.session.execute(
            db.select(Employee).where(
                Employee.employee_id == employee_id, 
                Employee.is_active == True
            )
        ).scalar_one_or_none()
        
        if not employee:
            flash('Employee not found', 'error')
            return redirect(request.url)
        
        # Calculate total days (excluding weekends)
        total_days = calculate_working_days(start_date, end_date)
        
        if total_days <= 0:
            flash('Invalid date range. End date must be after start date.', 'error')
            return redirect(request.url)
        
        # Validate against Kenyan labor laws
        validation_result = validate_leave_request(employee, leave_type, total_days, start_date)
        
        if validation_result['has_warning'] and not override_warning:
            # Return JSON for AJAX handling
            if request.is_json or request.headers.get('Content-Type') == 'application/json':
                return jsonify({
                    'success': False,
                    'warning': True,
                    'message': validation_result['message']
                })
            else:
                flash(f"⚠️ Legal Warning: {validation_result['message']}", 'warning')
                return redirect(request.url)
        
        # Create leave request
        try:
            leave_request = LeaveRequest(
                employee_id=employee.id,
                leave_type=leave_type,
                start_date=start_date,
                end_date=end_date,
                total_days=total_days,
                reason=reason,
                requested_by=current_user.id,
                status='pending'
            )
            
            db.session.add(leave_request)
            db.session.commit()
            
            flash(f'Leave request submitted successfully for {employee.full_name}', 'success')
            return redirect(url_for('leaves.list_requests'))
            
        except Exception as e:
            db.session.rollback()
            flash('Error submitting leave request. Please try again.', 'error')
            print(f"Error details: {e}")
    
    # GET request - show form
    if current_user.role == 'station_manager':
        employees = db.session.execute(
            db.select(Employee).where(
                Employee.location == current_user.location, 
                Employee.is_active == True
            ).order_by(Employee.first_name)
        ).scalars().all()
    else:
        employees = db.session.execute(
            db.select(Employee).where(Employee.is_active == True)
            .order_by(Employee.location, Employee.first_name)
        ).scalars().all()
    
    # Leave type information
    leave_types_info = {
        'annual_leave': {
            'display_name': 'Annual Leave',
            'max_days': 21,
            'description': '21 days per year (Kenyan Employment Act)',
            'notice_days': 14
        },
        'sick_leave': {
            'display_name': 'Sick Leave',
            'max_days': 7,
            'description': 'Up to 7 days without medical certificate',
            'notice_days': 0
        },
        'maternity_leave': {
            'display_name': 'Maternity Leave',
            'max_days': 90,
            'description': '3 months maternity leave',
            'notice_days': 30
        },
        'paternity_leave': {
            'display_name': 'Paternity Leave',
            'max_days': 14,
            'description': '14 days paternity leave',
            'notice_days': 7
        },
        'compassionate_leave': {
            'display_name': 'Compassionate Leave',
            'max_days': 7,
            'description': '7 days for bereavement',
            'notice_days': 0
        }
    }
    
    return render_template('leaves/request.html', 
                         employees=employees,
                         leave_types_info=leave_types_info)

@leaves_bp.route('/approve/<int:request_id>')
@login_required
def approve_leave(request_id):
    """Approve a leave request (HR only)"""
    if current_user.role != 'hr_manager':
        flash('Access denied. Only HR managers can approve leave requests.', 'error')
        return redirect(url_for('leaves.list_requests'))
    
    leave_request = db.session.get(LeaveRequest, request_id)
    if not leave_request:
        flash('Leave request not found', 'error')
        return redirect(url_for('leaves.list_requests'))
    
    if leave_request.status != 'pending':
        flash('This leave request has already been processed', 'warning')
        return redirect(url_for('leaves.list_requests'))
    
    try:
        leave_request.status = 'approved'
        leave_request.approved_by = current_user.id
        leave_request.approved_at = datetime.utcnow()
        
        db.session.commit()
        
        flash(f'Leave request approved for {leave_request.employee.full_name}', 'success')
        
        # TODO: Send email notification to employee and manager
        
    except Exception as e:
        db.session.rollback()
        flash('Error approving leave request', 'error')
        print(f"Error: {e}")
    
    return redirect(url_for('leaves.list_requests'))

@leaves_bp.route('/reject/<int:request_id>', methods=['GET', 'POST'])
@login_required
def reject_leave(request_id):
    """Reject a leave request (HR only)"""
    if current_user.role != 'hr_manager':
        flash('Access denied. Only HR managers can reject leave requests.', 'error')
        return redirect(url_for('leaves.list_requests'))
    
    leave_request = db.session.get(LeaveRequest, request_id)
    if not leave_request:
        flash('Leave request not found', 'error')
        return redirect(url_for('leaves.list_requests'))
    
    if request.method == 'POST':
        rejection_reason = request.form.get('rejection_reason', '')
        
        try:
            leave_request.status = 'rejected'
            leave_request.approved_by = current_user.id
            leave_request.approved_at = datetime.utcnow()
            leave_request.rejection_reason = rejection_reason
            
            db.session.commit()
            
            flash(f'Leave request rejected for {leave_request.employee.full_name}', 'success')
            
            # TODO: Send email notification to employee and manager
            
        except Exception as e:
            db.session.rollback()
            flash('Error rejecting leave request', 'error')
            print(f"Error: {e}")
        
        return redirect(url_for('leaves.list_requests'))
    
    return render_template('leaves/reject.html', leave_request=leave_request)

@leaves_bp.route('/cancel/<int:request_id>')
@login_required
def cancel_leave(request_id):
    """Cancel a leave request"""
    leave_request = db.session.get(LeaveRequest, request_id)
    if not leave_request:
        flash('Leave request not found', 'error')
        return redirect(url_for('leaves.list_requests'))
    
    # Check permissions
    if current_user.role == 'station_manager':
        employee = leave_request.employee
        if employee.location != current_user.location:
            flash('Access denied', 'error')
            return redirect(url_for('leaves.list_requests'))
    
    if leave_request.status not in ['pending', 'approved']:
        flash('Cannot cancel this leave request', 'warning')
        return redirect(url_for('leaves.list_requests'))
    
    try:
        leave_request.status = 'cancelled'
        db.session.commit()
        
        flash(f'Leave request cancelled for {leave_request.employee.full_name}', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash('Error cancelling leave request', 'error')
        print(f"Error: {e}")
    
    return redirect(url_for('leaves.list_requests'))

@leaves_bp.route('/employee_balance/<employee_id>')
@login_required
def get_employee_leave_balance(employee_id):
    """Get employee leave balance via AJAX"""
    employee = db.session.execute(
        db.select(Employee).where(Employee.employee_id == employee_id)
    ).scalar_one_or_none()
    
    if not employee:
        return jsonify({'error': 'Employee not found'}), 404
    
    # Calculate leave balances for current year
    current_year = date.today().year
    approved_leaves = db.session.execute(
        db.select(LeaveRequest).where(
            LeaveRequest.employee_id == employee.id,
            LeaveRequest.status == 'approved',
            db.extract('year', LeaveRequest.start_date) == current_year
        )
    ).scalars().all()
    
    # Group by leave type
    leave_taken = {}
    for leave in approved_leaves:
        if leave.leave_type not in leave_taken:
            leave_taken[leave.leave_type] = 0
        leave_taken[leave.leave_type] += leave.total_days
    
    # Calculate remaining balances
    balances = {
        'annual_leave': max(0, 21 - leave_taken.get('annual_leave', 0)),
        'sick_leave': max(0, 30 - leave_taken.get('sick_leave', 0)),  # 30 days total sick leave
        'maternity_leave': max(0, 90 - leave_taken.get('maternity_leave', 0)),
        'paternity_leave': max(0, 14 - leave_taken.get('paternity_leave', 0)),
        'compassionate_leave': max(0, 7 - leave_taken.get('compassionate_leave', 0))
    }
    
    return jsonify({
        'employee_id': employee.employee_id,
        'employee_name': employee.full_name,
        'balances': balances,
        'total_taken': leave_taken
    })

# Helper functions
def calculate_working_days(start_date, end_date):
    """Calculate working days excluding weekends"""
    if start_date > end_date:
        return 0
    
    current_date = start_date
    working_days = 0
    
    while current_date <= end_date:
        # Monday = 0, Sunday = 6
        if current_date.weekday() < 5:  # Monday to Friday
            working_days += 1
        current_date += timedelta(days=1)
    
    return working_days

def validate_leave_request(employee, leave_type, total_days, start_date):
    """Validate leave request against Kenyan labor laws"""
    result = {'has_warning': False, 'message': ''}
    
    # Maximum days per leave type (Kenyan Employment Act 2007)
    max_days = {
        'annual_leave': 21,
        'sick_leave': 7,  # Without medical certificate
        'maternity_leave': 90,
        'paternity_leave': 14,
        'compassionate_leave': 7
    }
    
    # Check if exceeds maximum
    if leave_type in max_days and total_days > max_days[leave_type]:
        result['has_warning'] = True
        result['message'] = f"Request exceeds Kenyan law maximum of {max_days[leave_type]} days for {leave_type.replace('_', ' ').title()}. HR approval required."
    
    # Check annual leave balance
    if leave_type == 'annual_leave':
        current_balance = employee.current_leave_balance
        if total_days > current_balance:
            result['has_warning'] = True
            result['message'] = f"Employee only has {current_balance} days of annual leave remaining."
    
    # Check notice period
    notice_requirements = {
        'annual_leave': 14,  # 2 weeks notice
        'maternity_leave': 30,  # 1 month notice
        'paternity_leave': 7   # 1 week notice
    }
    
    if leave_type in notice_requirements:
        days_notice = (start_date - date.today()).days
        required_notice = notice_requirements[leave_type]
        
        if days_notice < required_notice:
            if not result['has_warning']:  # Don't override existing warnings
                result['has_warning'] = True
                result['message'] = f"Insufficient notice period. {leave_type.replace('_', ' ').title()} requires {required_notice} days notice."
    
    return result