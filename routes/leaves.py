"""
Leave management routes for Sakina Gas Attendance System
Enhanced with Kenyan Labor Law Compliance
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from models import db, Employee, LeaveRequest
from kenyan_labor_laws import KenyanLaborLaws, create_leave_warning_message, format_leave_type_display
from datetime import date, datetime

leaves_bp = Blueprint('leaves', __name__)

@leaves_bp.route('/')
@login_required
def list_leaves():
    """List all leave requests"""
    status_filter = request.args.get('status', 'all')
    
    query = LeaveRequest.query.join(Employee)
    
    if current_user.role == 'station_manager':
        query = query.filter(Employee.location == current_user.location)
    
    if status_filter != 'all':
        query = query.filter(LeaveRequest.status == status_filter)
    
    leave_requests = query.order_by(LeaveRequest.created_at.desc()).all()
    
    return render_template('leaves/list.html', 
                         leave_requests=leave_requests, 
                         status_filter=status_filter)

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
        
        employee = Employee.query.filter_by(employee_id=employee_id, is_active=True).first()
        if not employee:
            flash('Employee not found', 'error')
            return redirect(request.url)
        
        # Calculate total days
        total_days = (end_date - start_date).days + 1
        
        # Validate against Kenyan labor laws
        validation = KenyanLaborLaws.validate_leave_request(leave_type, total_days, employee.id)
        
        if not validation['is_valid'] and not override_warning:
            # Return validation errors as JSON for frontend handling
            warning_message = create_leave_warning_message(validation)
            return jsonify({
                'success': False,
                'warning': True,
                'message': warning_message,
                'validation': validation
            })
        
        # Create leave request
        leave_request = LeaveRequest(
            employee_id=employee.id,
            leave_type=leave_type,
            start_date=start_date,
            end_date=end_date,
            total_days=total_days,
            reason=reason,
            requested_by=current_user.id
        )
        
        # Auto-approve certain types for station managers (can be overridden by HR)
        if leave_type in ['sick_leave', 'unpaid_leave'] and current_user.role == 'station_manager':
            leave_request.status = 'approved'
            leave_request.approved_by = current_user.id
            leave_request.approved_at = datetime.utcnow()
            flash_msg = 'Leave request submitted and automatically approved'
        else:
            flash_msg = 'Leave request submitted for HR approval'
        
        # Add compliance warning to reason if law was overridden
        if not validation['is_valid'] and override_warning:
            leave_request.reason += f"\n\n[COMPLIANCE WARNING OVERRIDDEN: {', '.join(validation['warnings'])}]"
        
        try:
            db.session.add(leave_request)
            db.session.commit()
            
            if request.is_json:
                return jsonify({'success': True, 'message': flash_msg})
            else:
                flash(flash_msg, 'success')
                return redirect(url_for('leaves.list_leaves'))
        except Exception as e:
            db.session.rollback()
            flash('Error submitting leave request', 'error')
            if request.is_json:
                return jsonify({'success': False, 'message': 'Error submitting leave request'})
    
    # Get employees for dropdown
    if current_user.role == 'station_manager':
        employees = Employee.query.filter_by(location=current_user.location, is_active=True).all()
    else:
        employees = Employee.query.filter_by(is_active=True).all()
    
    # Get leave type information for frontend
    leave_types_info = {}
    for leave_type, info in KenyanLaborLaws.LEAVE_LIMITS.items():
        leave_types_info[leave_type] = {
            'display_name': format_leave_type_display(leave_type),
            'max_days': info['max_days'],
            'description': info['description']
        }
    
    return render_template('leaves/request.html', 
                         employees=employees,
                         leave_types_info=leave_types_info)

@leaves_bp.route('/approve/<int:leave_id>', methods=['GET', 'POST'])
@login_required
def approve_leave(leave_id):
    """Approve leave request (HR Manager only) with optional notes"""
    if current_user.role != 'hr_manager':
        flash('Only HR Manager can approve leave requests', 'error')
        return redirect(url_for('leaves.list_leaves'))
    
    leave_request = LeaveRequest.query.get_or_404(leave_id)
    
    if request.method == 'POST':
        approval_notes = request.form.get('approval_notes', '')
        
        leave_request.status = 'approved'
        leave_request.approved_by = current_user.id
        leave_request.approved_at = datetime.utcnow()
        
        if approval_notes:
            leave_request.reason += f"\n\n[HR APPROVAL NOTES: {approval_notes}]"
        
        db.session.commit()
        flash(f'Leave request for {leave_request.employee.full_name} approved', 'success')
        return redirect(url_for('leaves.list_leaves'))
    
    # GET request - show approval form with leave details
    return render_template('leaves/approve.html', leave_request=leave_request)

@leaves_bp.route('/reject/<int:leave_id>', methods=['GET', 'POST'])
@login_required
def reject_leave(leave_id):
    """Reject leave request (HR Manager only) with mandatory notes"""
    if current_user.role != 'hr_manager':
        flash('Only HR Manager can reject leave requests', 'error')
        return redirect(url_for('leaves.list_leaves'))
    
    leave_request = LeaveRequest.query.get_or_404(leave_id)
    
    if request.method == 'POST':
        rejection_reason = request.form.get('rejection_reason', '').strip()
        
        if not rejection_reason:
            flash('Rejection reason is required', 'error')
            return render_template('leaves/reject.html', leave_request=leave_request)
        
        leave_request.status = 'rejected'
        leave_request.reason += f"\n\n[HR REJECTION REASON: {rejection_reason}]"
        
        db.session.commit()
        flash(f'Leave request for {leave_request.employee.full_name} rejected', 'warning')
        return redirect(url_for('leaves.list_leaves'))
    
    # GET request - show rejection form
    return render_template('leaves/reject.html', leave_request=leave_request)

@leaves_bp.route('/leave-balance/<int:employee_id>')
@login_required
def check_leave_balance(employee_id):
    """Check employee leave balance (API endpoint)"""
    employee = Employee.query.get_or_404(employee_id)
    
    # Calculate leave balance for current year
    current_year = datetime.now().year
    
    leave_balance = {}
    for leave_type in KenyanLaborLaws.LEAVE_LIMITS.keys():
        balance_info = KenyanLaborLaws.get_leave_balance_info(employee_id, leave_type, current_year)
        leave_balance[leave_type] = balance_info
    
    return jsonify({
        'employee': {
            'id': employee.id,
            'name': employee.full_name,
            'employee_id': employee.employee_id
        },
        'leave_balance': leave_balance,
        'year': current_year
    })

@leaves_bp.route('/compliance-report')
@login_required
def compliance_report():
    """Generate Kenyan labor law compliance report (HR Manager only)"""
    if current_user.role != 'hr_manager':
        flash('Only HR Manager can access compliance reports', 'error')
        return redirect(url_for('leaves.list_leaves'))
    
    # Get all leave requests for current year
    current_year = datetime.now().year
    leave_requests = LeaveRequest.query.filter(
        db.extract('year', LeaveRequest.start_date) == current_year
    ).all()
    
    # Generate compliance report
    report = KenyanLaborLaws.generate_compliance_report(leave_requests)
    
    return render_template('leaves/compliance_report.html', 
                         report=report, 
                         year=current_year)
