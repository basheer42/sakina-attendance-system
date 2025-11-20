"""
Enhanced Leave Management Routes for Sakina Gas Attendance System
Built upon your comprehensive leave system with advanced Kenyan Labor Law compliance
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, g
from flask_login import login_required, current_user
from models import db, Employee, LeaveRequest, Holiday, AuditLog
from datetime import date, datetime, timedelta
from sqlalchemy import func, and_, or_, desc
from config import Config
import json

leaves_bp = Blueprint('leaves', __name__)

@leaves_bp.route('/')
@leaves_bp.route('/list')
@login_required
def list_leaves():
    """Enhanced leave requests listing with advanced filtering"""
    # Get filter parameters
    status_filter = request.args.get('status', 'all')
    leave_type_filter = request.args.get('leave_type', 'all')
    employee_filter = request.args.get('employee', 'all')
    location_filter = request.args.get('location', 'all')
    start_date_str = request.args.get('start_date', '')
    end_date_str = request.args.get('end_date', '')
    
    # Base query based on user role
    if current_user.role == 'station_manager':
        query = db.session.query(LeaveRequest).join(Employee).filter(
            Employee.location == current_user.location,
            Employee.is_active == True
        )
    else:
        query = db.session.query(LeaveRequest).join(Employee).filter(
            Employee.is_active == True
        )
    
    # Apply filters
    if status_filter != 'all':
        query = query.filter(LeaveRequest.status == status_filter)
    
    if leave_type_filter != 'all':
        query = query.filter(LeaveRequest.leave_type == leave_type_filter)
    
    if employee_filter != 'all':
        query = query.filter(Employee.id == employee_filter)
    
    if location_filter != 'all' and current_user.role != 'station_manager':
        query = query.filter(Employee.location == location_filter)
    
    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            query = query.filter(LeaveRequest.start_date >= start_date)
        except ValueError:
            pass
    
    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            query = query.filter(LeaveRequest.end_date <= end_date)
        except ValueError:
            pass
    
    # Order and paginate
    page = request.args.get('page', 1, type=int)
    per_page = 25
    
    leave_requests = query.order_by(
        desc(LeaveRequest.created_at)
    ).paginate(page=page, per_page=per_page, error_out=False)
    
    # Get filter options
    filter_options = get_leave_filter_options(current_user)
    
    # Get summary statistics
    summary_stats = get_leave_summary_stats(current_user, status_filter, leave_type_filter)
    
    return render_template('leaves/list.html',
                         leave_requests=leave_requests,
                         filter_options=filter_options,
                         summary_stats=summary_stats,
                         status_filter=status_filter,
                         leave_type_filter=leave_type_filter,
                         employee_filter=employee_filter,
                         location_filter=location_filter,
                         start_date_str=start_date_str,
                         end_date_str=end_date_str)

@leaves_bp.route('/request', methods=['GET', 'POST'])
@leaves_bp.route('/request/<int:employee_id>', methods=['GET', 'POST'])
@login_required
def request_leave(employee_id=None):
    """Enhanced leave request with comprehensive Kenyan law validation"""
    # Determine employee
    if employee_id:
        # HR manager requesting for specific employee
        if current_user.role not in ['hr_manager', 'admin']:
            flash('Only HR managers can request leave for other employees.', 'danger')
            return redirect(url_for('leaves.list_leaves'))
        
        employee = Employee.query.get_or_404(employee_id)
    else:
        # Self-request (future enhancement for employee self-service)
        flash('Employee self-service portal coming soon. Please contact HR for leave requests.', 'info')
        return redirect(url_for('leaves.list_leaves'))
    
    if request.method == 'POST':
        try:
            # Get form data
            leave_type = request.form['leave_type']
            start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d').date()
            end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d').date()
            reason = request.form['reason'].strip()
            emergency_contact = request.form.get('emergency_contact', '').strip()
            emergency_phone = request.form.get('emergency_phone', '').strip()
            handover_notes = request.form.get('handover_notes', '').strip()
            replacement_employee_id = request.form.get('replacement_employee_id') or None
            
            # Basic validation
            if start_date > end_date:
                flash('Start date cannot be after end date.', 'danger')
                raise ValueError('Invalid date range')
            
            if start_date < date.today():
                flash('Leave cannot be requested for past dates.', 'danger')
                raise ValueError('Past date not allowed')
            
            # Calculate total days
            total_days = (end_date - start_date).days + 1
            
            # Create leave request object for validation
            leave_request = LeaveRequest(
                employee_id=employee.id,
                leave_type=leave_type,
                start_date=start_date,
                end_date=end_date,
                total_days=total_days,
                reason=reason,
                emergency_contact=emergency_contact,
                emergency_phone=emergency_phone,
                handover_notes=handover_notes,
                replacement_employee_id=replacement_employee_id,
                requested_by=current_user.id,
                status='pending'
            )
            
            # Calculate working days (excluding weekends and holidays)
            leave_request.calculate_working_days()
            
            # Validate against Kenyan Labor Law
            validation_warnings = leave_request.validate_kenyan_law()
            
            # Check for overlapping leave requests
            overlapping_leaves = LeaveRequest.query.filter(
                LeaveRequest.employee_id == employee.id,
                LeaveRequest.status.in_(['pending', 'approved']),
                or_(
                    and_(LeaveRequest.start_date <= start_date, LeaveRequest.end_date >= start_date),
                    and_(LeaveRequest.start_date <= end_date, LeaveRequest.end_date >= end_date),
                    and_(LeaveRequest.start_date >= start_date, LeaveRequest.end_date <= end_date)
                )
            ).first()
            
            if overlapping_leaves:
                flash(f'Employee already has {overlapping_leaves.leave_type} from {overlapping_leaves.start_date} to {overlapping_leaves.end_date}.', 'danger')
                raise ValueError('Overlapping leave request')
            
            # Handle validation warnings
            if validation_warnings:
                warning_messages = []
                for warning in validation_warnings:
                    warning_messages.append(warning)
                    
                # Check if HR override is provided
                hr_override = request.form.get('hr_override') == 'true'
                hr_override_reason = request.form.get('hr_override_reason', '').strip()
                
                if not hr_override:
                    # Show warnings to user for confirmation
                    return render_template('leaves/request.html',
                                         employee=employee,
                                         form_data=get_leave_form_data(),
                                         validation_warnings=validation_warnings,
                                         form_values=request.form.to_dict(),
                                         warning_messages=warning_messages)
                else:
                    # HR override - log the override
                    leave_request.exceeds_entitlement = True
                    leave_request.hr_notes = f"HR Override: {hr_override_reason}"
                    
                    # Log the override
                    AuditLog.log_action(
                        user_id=current_user.id,
                        action='leave_law_override',
                        target_type='leave_request',
                        details=f'HR override for {employee.full_name} - {leave_type} - Reason: {hr_override_reason}',
                        ip_address=request.remote_addr,
                        risk_level='high',
                        compliance_relevant=True
                    )
            
            # Set priority based on leave type and urgency
            if leave_type in ['sick_leave', 'compassionate_leave']:
                leave_request.priority = 'high'
            elif leave_type in ['maternity_leave', 'paternity_leave']:
                leave_request.priority = 'urgent'
            else:
                leave_request.priority = 'normal'
            
            # Auto-approve certain types based on policy
            auto_approve_types = ['sick_leave']  # Can be configured
            if (leave_type in auto_approve_types and 
                total_days <= 3 and 
                not validation_warnings):
                leave_request.status = 'approved'
                leave_request.approved_by = current_user.id
                leave_request.approved_at = datetime.utcnow()
                approval_message = ' and auto-approved'
            else:
                approval_message = ''
            
            db.session.add(leave_request)
            db.session.commit()
            
            # Log the request
            AuditLog.log_action(
                user_id=current_user.id,
                action='leave_request_created',
                target_type='leave_request',
                target_id=leave_request.id,
                details=f'Created {leave_type} request for {employee.full_name} ({start_date} to {end_date})',
                ip_address=request.remote_addr
            )
            
            flash(f'Leave request submitted successfully{approval_message}!', 'success')
            return redirect(url_for('leaves.view_leave', id=leave_request.id))
            
        except ValueError:
            # Validation error already flashed
            pass
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating leave request: {str(e)}', 'danger')
    
    # GET request - show form
    form_data = get_leave_form_data()
    return render_template('leaves/request.html',
                         employee=employee,
                         form_data=form_data)

@leaves_bp.route('/<int:id>')
@login_required
def view_leave(id):
    """Enhanced leave request view with comprehensive details"""
    leave_request = LeaveRequest.query.get_or_404(id)
    
    # Check permissions
    if (current_user.role == 'station_manager' and 
        leave_request.employee.location != current_user.location):
        flash('You can only view leave requests for your station employees.', 'danger')
        return redirect(url_for('leaves.list_leaves'))
    
    # Get additional data
    leave_balance = calculate_leave_balance(leave_request.employee, leave_request.leave_type)
    similar_requests = get_similar_leave_requests(leave_request)
    approval_history = get_leave_approval_history(leave_request)
    
    # Check for compliance issues
    compliance_status = check_leave_compliance(leave_request)
    
    return render_template('leaves/view.html',
                         leave_request=leave_request,
                         leave_balance=leave_balance,
                         similar_requests=similar_requests,
                         approval_history=approval_history,
                         compliance_status=compliance_status)

@leaves_bp.route('/<int:id>/approve', methods=['POST'])
@login_required
def approve_leave(id):
    """Enhanced leave approval with compliance checking"""
    if current_user.role not in ['hr_manager', 'admin']:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    leave_request = LeaveRequest.query.get_or_404(id)
    
    if leave_request.status != 'pending':
        return jsonify({'success': False, 'message': 'Leave request is not pending'}), 400
    
    try:
        data = request.get_json()
        approval_notes = data.get('notes', '').strip()
        override_compliance = data.get('override_compliance', False)
        override_reason = data.get('override_reason', '').strip()
        
        # Final compliance check
        validation_warnings = leave_request.validate_kenyan_law()
        
        if validation_warnings and not override_compliance:
            return jsonify({
                'success': False,
                'message': 'Compliance issues detected',
                'warnings': validation_warnings,
                'requires_override': True
            }), 400
        
        # Approve the request
        leave_request.status = 'approved'
        leave_request.approved_by = current_user.id
        leave_request.approved_at = datetime.utcnow()
        leave_request.hr_notes = approval_notes
        leave_request.compliance_checked = True
        
        if override_compliance:
            leave_request.exceeds_entitlement = True
            leave_request.hr_notes += f"\n\nCompliance Override: {override_reason}"
        
        db.session.commit()
        
        # Log the approval
        AuditLog.log_action(
            user_id=current_user.id,
            action='leave_approved',
            target_type='leave_request',
            target_id=leave_request.id,
            details=f'Approved {leave_request.leave_type} for {leave_request.employee.full_name}',
            ip_address=request.remote_addr,
            risk_level='medium' if override_compliance else 'low',
            compliance_relevant=True
        )
        
        # TODO: Send notification email to employee
        
        return jsonify({
            'success': True,
            'message': f'Leave request approved for {leave_request.employee.full_name}',
            'approved_at': leave_request.approved_at.isoformat()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@leaves_bp.route('/<int:id>/reject', methods=['POST'])
@login_required
def reject_leave(id):
    """Enhanced leave rejection with detailed reasoning"""
    if current_user.role not in ['hr_manager', 'admin']:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    leave_request = LeaveRequest.query.get_or_404(id)
    
    if leave_request.status != 'pending':
        return jsonify({'success': False, 'message': 'Leave request is not pending'}), 400
    
    try:
        data = request.get_json()
        rejection_reason = data.get('reason', '').strip()
        
        if not rejection_reason:
            return jsonify({'success': False, 'message': 'Rejection reason is required'}), 400
        
        # Reject the request
        leave_request.status = 'rejected'
        leave_request.approved_by = current_user.id
        leave_request.approved_at = datetime.utcnow()
        leave_request.rejection_reason = rejection_reason
        
        db.session.commit()
        
        # Log the rejection
        AuditLog.log_action(
            user_id=current_user.id,
            action='leave_rejected',
            target_type='leave_request',
            target_id=leave_request.id,
            details=f'Rejected {leave_request.leave_type} for {leave_request.employee.full_name} - Reason: {rejection_reason}',
            ip_address=request.remote_addr,
            risk_level='medium',
            compliance_relevant=True
        )
        
        # TODO: Send notification email to employee
        
        return jsonify({
            'success': True,
            'message': f'Leave request rejected for {leave_request.employee.full_name}',
            'rejected_at': leave_request.approved_at.isoformat()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@leaves_bp.route('/<int:id>/cancel', methods=['POST'])
@login_required
def cancel_leave(id):
    """Cancel leave request (employee or HR)"""
    leave_request = LeaveRequest.query.get_or_404(id)
    
    # Check permissions
    can_cancel = (
        current_user.role in ['hr_manager', 'admin'] or
        (current_user.role == 'station_manager' and 
         leave_request.employee.location == current_user.location)
    )
    
    if not can_cancel:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    if leave_request.status not in ['pending', 'approved']:
        return jsonify({'success': False, 'message': 'Cannot cancel this leave request'}), 400
    
    # Check if leave has already started
    if leave_request.start_date <= date.today():
        return jsonify({'success': False, 'message': 'Cannot cancel leave that has already started'}), 400
    
    try:
        data = request.get_json()
        cancellation_reason = data.get('reason', '').strip()
        
        # Cancel the request
        old_status = leave_request.status
        leave_request.status = 'cancelled'
        leave_request.hr_notes = f"{leave_request.hr_notes or ''}\n\nCancelled: {cancellation_reason}".strip()
        
        db.session.commit()
        
        # Log the cancellation
        AuditLog.log_action(
            user_id=current_user.id,
            action='leave_cancelled',
            target_type='leave_request',
            target_id=leave_request.id,
            details=f'Cancelled {leave_request.leave_type} for {leave_request.employee.full_name} (was {old_status})',
            ip_address=request.remote_addr
        )
        
        return jsonify({
            'success': True,
            'message': f'Leave request cancelled for {leave_request.employee.full_name}'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@leaves_bp.route('/calendar')
@login_required
def leave_calendar():
    """Enhanced leave calendar view"""
    # Get month and year from request
    month = request.args.get('month', datetime.now().month, type=int)
    year = request.args.get('year', datetime.now().year, type=int)
    
    # Validate month and year
    if month < 1 or month > 12:
        month = datetime.now().month
    if year < 2020 or year > 2030:
        year = datetime.now().year
    
    # Get calendar data
    calendar_data = generate_leave_calendar(month, year, current_user)
    
    return render_template('leaves/calendar.html',
                         calendar_data=calendar_data,
                         current_month=month,
                         current_year=year)

@leaves_bp.route('/balance/<int:employee_id>')
@login_required
def leave_balance(employee_id):
    """View employee leave balance"""
    employee = Employee.query.get_or_404(employee_id)
    
    # Check permissions
    if (current_user.role == 'station_manager' and 
        employee.location != current_user.location):
        flash('Access denied.', 'danger')
        return redirect(url_for('leaves.list_leaves'))
    
    # Calculate leave balances for all types
    current_year = date.today().year
    leave_balances = {}
    leave_history = {}
    
    for leave_type in Config.KENYAN_LABOR_LAWS.keys():
        leave_balances[leave_type] = employee.get_leave_balance(leave_type, current_year)
        
        # Get leave history for this type
        leave_history[leave_type] = LeaveRequest.query.filter(
            LeaveRequest.employee_id == employee.id,
            LeaveRequest.leave_type == leave_type,
            LeaveRequest.status == 'approved',
            LeaveRequest.start_date >= date(current_year, 1, 1)
        ).order_by(desc(LeaveRequest.start_date)).all()
    
    return render_template('leaves/balance.html',
                         employee=employee,
                         leave_balances=leave_balances,
                         leave_history=leave_history,
                         current_year=current_year)

@leaves_bp.route('/reports')
@login_required
def leave_reports():
    """Enhanced leave reporting dashboard"""
    if current_user.role not in ['hr_manager', 'admin']:
        flash('Access denied. HR Manager privileges required.', 'danger')
        return redirect(url_for('leaves.list_leaves'))
    
    # Get report parameters
    report_type = request.args.get('type', 'summary')
    start_date_str = request.args.get('start_date', date.today().replace(month=1, day=1).isoformat())
    end_date_str = request.args.get('end_date', date.today().isoformat())
    
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    except ValueError:
        start_date = date.today().replace(month=1, day=1)
        end_date = date.today()
    
    # Generate reports
    if report_type == 'summary':
        report_data = generate_leave_summary_report(start_date, end_date)
    elif report_type == 'compliance':
        report_data = generate_compliance_report(start_date, end_date)
    elif report_type == 'utilization':
        report_data = generate_utilization_report(start_date, end_date)
    elif report_type == 'trends':
        report_data = generate_trends_report(start_date, end_date)
    else:
        report_data = generate_leave_summary_report(start_date, end_date)
    
    return render_template('leaves/reports.html',
                         report_data=report_data,
                         report_type=report_type,
                         start_date=start_date,
                         end_date=end_date)

# Helper Functions

def get_leave_filter_options(user):
    """Get filter options for leave listing"""
    options = {
        'statuses': ['all', 'pending', 'approved', 'rejected', 'cancelled'],
        'leave_types': ['all'] + list(Config.KENYAN_LABOR_LAWS.keys()),
        'locations': [],
        'employees': []
    }
    
    # Locations based on role
    if user.role == 'hr_manager':
        options['locations'] = ['all'] + list(Config.COMPANY_LOCATIONS.keys())
        options['employees'] = Employee.query.filter(Employee.is_active == True).order_by(
            Employee.first_name, Employee.last_name
        ).all()
    elif user.role == 'station_manager':
        options['locations'] = [user.location]
        options['employees'] = Employee.query.filter(
            Employee.location == user.location,
            Employee.is_active == True
        ).order_by(Employee.first_name, Employee.last_name).all()
    
    return options

def get_leave_summary_stats(user, status_filter, leave_type_filter):
    """Get summary statistics for leave requests"""
    # Base query
    if user.role == 'station_manager':
        query = db.session.query(LeaveRequest).join(Employee).filter(
            Employee.location == user.location,
            Employee.is_active == True
        )
    else:
        query = db.session.query(LeaveRequest).join(Employee).filter(
            Employee.is_active == True
        )
    
    # Calculate stats
    stats = {
        'total': query.count(),
        'pending': query.filter(LeaveRequest.status == 'pending').count(),
        'approved': query.filter(LeaveRequest.status == 'approved').count(),
        'rejected': query.filter(LeaveRequest.status == 'rejected').count(),
        'cancelled': query.filter(LeaveRequest.status == 'cancelled').count()
    }
    
    # Current month stats
    current_month_start = date.today().replace(day=1)
    if current_month_start.month == 12:
        next_month_start = current_month_start.replace(year=current_month_start.year + 1, month=1)
    else:
        next_month_start = current_month_start.replace(month=current_month_start.month + 1)
    
    stats['this_month'] = query.filter(
        LeaveRequest.created_at >= current_month_start,
        LeaveRequest.created_at < next_month_start
    ).count()
    
    return stats

def get_leave_form_data():
    """Get data needed for leave request form"""
    form_data = {
        'leave_types': Config.KENYAN_LABOR_LAWS,
        'employees': Employee.query.filter(Employee.is_active == True).order_by(
            Employee.first_name, Employee.last_name
        ).all(),
        'priorities': ['normal', 'high', 'urgent']
    }
    
    return form_data

def calculate_leave_balance(employee, leave_type):
    """Calculate current leave balance for employee and leave type"""
    current_year = date.today().year
    balance_info = {
        'entitlement': 0,
        'used': 0,
        'pending': 0,
        'available': 0,
        'carry_forward': 0
    }
    
    # Get policy information
    policy = Config.KENYAN_LABOR_LAWS.get(leave_type, {})
    max_days = policy.get('max_days', 0)
    
    if max_days:
        # Calculate entitlement
        if leave_type == 'annual_leave':
            # Pro-rata based on service
            service_months = employee.months_of_service
            if service_months >= 12:
                balance_info['entitlement'] = max_days
            else:
                balance_info['entitlement'] = round((max_days * service_months) / 12, 1)
        else:
            balance_info['entitlement'] = max_days
        
        # Calculate used leave
        used_leave = db.session.query(func.sum(LeaveRequest.total_days)).filter(
            LeaveRequest.employee_id == employee.id,
            LeaveRequest.leave_type == leave_type,
            LeaveRequest.status == 'approved',
            LeaveRequest.start_date >= date(current_year, 1, 1),
            LeaveRequest.end_date <= date(current_year, 12, 31)
        ).scalar() or 0
        
        balance_info['used'] = used_leave
        
        # Calculate pending leave
        pending_leave = db.session.query(func.sum(LeaveRequest.total_days)).filter(
            LeaveRequest.employee_id == employee.id,
            LeaveRequest.leave_type == leave_type,
            LeaveRequest.status == 'pending',
            LeaveRequest.start_date >= date(current_year, 1, 1)
        ).scalar() or 0
        
        balance_info['pending'] = pending_leave
        
        # Calculate available balance
        balance_info['available'] = max(0, balance_info['entitlement'] - used_leave - pending_leave)
    
    return balance_info

def get_similar_leave_requests(leave_request):
    """Get similar leave requests for comparison"""
    # Get other requests from same employee, same type, last 2 years
    two_years_ago = date.today() - timedelta(days=730)
    
    similar_requests = LeaveRequest.query.filter(
        LeaveRequest.employee_id == leave_request.employee_id,
        LeaveRequest.leave_type == leave_request.leave_type,
        LeaveRequest.id != leave_request.id,
        LeaveRequest.created_at >= two_years_ago
    ).order_by(desc(LeaveRequest.created_at)).limit(5).all()
    
    return similar_requests

def get_leave_approval_history(leave_request):
    """Get approval history for leave request"""
    # Get audit logs related to this leave request
    history = AuditLog.query.filter(
        AuditLog.target_type == 'leave_request',
        AuditLog.target_id == leave_request.id
    ).order_by(AuditLog.timestamp).all()
    
    return history

def check_leave_compliance(leave_request):
    """Check leave request compliance with Kenyan law"""
    warnings = leave_request.validate_kenyan_law()
    
    status = {
        'compliant': len(warnings) == 0,
        'warnings': warnings,
        'risk_level': 'low',
        'recommendations': []
    }
    
    if warnings:
        status['risk_level'] = 'medium' if len(warnings) <= 2 else 'high'
        
        # Add recommendations based on warnings
        for warning in warnings:
            if 'exceeds maximum' in warning:
                status['recommendations'].append('Consider splitting leave into multiple periods')
            elif 'certificate required' in warning:
                status['recommendations'].append('Ensure medical certificate is provided')
            elif 'insufficient notice' in warning:
                status['recommendations'].append('Future requests should provide adequate notice')
    
    return status

def generate_leave_calendar(month, year, user):
    """Generate calendar data for leave visualization"""
    # Get month start and end dates
    month_start = date(year, month, 1)
    if month == 12:
        month_end = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        month_end = date(year, month + 1, 1) - timedelta(days=1)
    
    # Get leave requests for the month
    if user.role == 'station_manager':
        leave_requests = db.session.query(LeaveRequest).join(Employee).filter(
            Employee.location == user.location,
            Employee.is_active == True,
            or_(
                and_(LeaveRequest.start_date <= month_end, LeaveRequest.end_date >= month_start),
                and_(LeaveRequest.start_date >= month_start, LeaveRequest.start_date <= month_end)
            ),
            LeaveRequest.status == 'approved'
        ).all()
    else:
        leave_requests = LeaveRequest.query.join(Employee).filter(
            Employee.is_active == True,
            or_(
                and_(LeaveRequest.start_date <= month_end, LeaveRequest.end_date >= month_start),
                and_(LeaveRequest.start_date >= month_start, LeaveRequest.start_date <= month_end)
            ),
            LeaveRequest.status == 'approved'
        ).all()
    
    # Get holidays for the month
    holidays = Holiday.query.filter(
        Holiday.date >= month_start,
        Holiday.date <= month_end,
        Holiday.is_active == True
    ).all()
    
    calendar_data = {
        'month': month,
        'year': year,
        'month_name': month_start.strftime('%B'),
        'leave_requests': leave_requests,
        'holidays': holidays,
        'days_in_month': month_end.day
    }
    
    return calendar_data

def generate_leave_summary_report(start_date, end_date):
    """Generate leave summary report"""
    # Get all leave requests in date range
    leave_requests = LeaveRequest.query.filter(
        LeaveRequest.start_date >= start_date,
        LeaveRequest.end_date <= end_date
    ).all()
    
    # Calculate statistics by leave type
    stats_by_type = {}
    for leave_type in Config.KENYAN_LABOR_LAWS.keys():
        type_requests = [lr for lr in leave_requests if lr.leave_type == leave_type]
        stats_by_type[leave_type] = {
            'total_requests': len(type_requests),
            'approved': len([lr for lr in type_requests if lr.status == 'approved']),
            'pending': len([lr for lr in type_requests if lr.status == 'pending']),
            'rejected': len([lr for lr in type_requests if lr.status == 'rejected']),
            'total_days': sum(lr.total_days for lr in type_requests if lr.status == 'approved')
        }
    
    # Calculate statistics by location
    stats_by_location = {}
    for location in Config.COMPANY_LOCATIONS.keys():
        location_requests = [lr for lr in leave_requests if lr.employee.location == location]
        stats_by_location[location] = {
            'total_requests': len(location_requests),
            'total_days': sum(lr.total_days for lr in location_requests if lr.status == 'approved')
        }
    
    return {
        'type': 'summary',
        'period': f"{start_date} to {end_date}",
        'stats_by_type': stats_by_type,
        'stats_by_location': stats_by_location,
        'total_requests': len(leave_requests),
        'total_approved': len([lr for lr in leave_requests if lr.status == 'approved'])
    }

def generate_compliance_report(start_date, end_date):
    """Generate compliance report"""
    # Get leave requests with compliance issues
    compliance_issues = LeaveRequest.query.filter(
        LeaveRequest.start_date >= start_date,
        LeaveRequest.end_date <= end_date,
        LeaveRequest.exceeds_entitlement == True
    ).all()
    
    return {
        'type': 'compliance',
        'period': f"{start_date} to {end_date}",
        'compliance_issues': compliance_issues,
        'total_issues': len(compliance_issues)
    }

def generate_utilization_report(start_date, end_date):
    """Generate leave utilization report"""
    return {
        'type': 'utilization',
        'period': f"{start_date} to {end_date}",
        'message': 'Utilization report generation in progress'
    }

def generate_trends_report(start_date, end_date):
    """Generate leave trends report"""
    return {
        'type': 'trends',
        'period': f"{start_date} to {end_date}",
        'message': 'Trends report generation in progress'
    }

# API Endpoints

@leaves_bp.route('/api/employee-balance/<int:employee_id>')
@login_required
def api_employee_leave_balance(employee_id):
    """API endpoint for employee leave balance"""
    employee = Employee.query.get_or_404(employee_id)
    
    # Check permissions
    if (current_user.role == 'station_manager' and 
        employee.location != current_user.location):
        return jsonify({'error': 'Unauthorized'}), 403
    
    balances = {}
    for leave_type in Config.KENYAN_LABOR_LAWS.keys():
        balances[leave_type] = calculate_leave_balance(employee, leave_type)
    
    return jsonify({
        'employee_id': employee.id,
        'employee_name': employee.full_name,
        'balances': balances,
        'years_of_service': round(employee.years_of_service, 1)
    })

@leaves_bp.route('/api/validate-request', methods=['POST'])
@login_required
def api_validate_leave_request():
    """API endpoint for leave request validation"""
    data = request.get_json()
    
    employee_id = data.get('employee_id')
    leave_type = data.get('leave_type')
    start_date_str = data.get('start_date')
    end_date_str = data.get('end_date')
    
    try:
        employee = Employee.query.get_or_404(employee_id)
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        
        # Create temporary leave request for validation
        temp_request = LeaveRequest(
            employee_id=employee.id,
            leave_type=leave_type,
            start_date=start_date,
            end_date=end_date,
            total_days=(end_date - start_date).days + 1
        )
        temp_request.calculate_working_days()
        
        # Validate
        warnings = temp_request.validate_kenyan_law()
        
        # Check balance
        balance = calculate_leave_balance(employee, leave_type)
        
        return jsonify({
            'valid': len(warnings) == 0,
            'warnings': warnings,
            'total_days': temp_request.total_days,
            'working_days': temp_request.working_days,
            'balance': balance
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400