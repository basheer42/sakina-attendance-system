"""
Enhanced Leave Management Routes for Sakina Gas Attendance System
Built upon your comprehensive leave system with advanced Kenyan Labor Law compliance
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, g, current_app
from flask_login import login_required, current_user
# FIX: Removed global model imports to prevent early model registration
from database import db
from decimal import Decimal # FIX: Added missing import for Decimal usage
from datetime import date, datetime, timedelta
from sqlalchemy import func, and_, or_, desc
from config import Config
import json

leaves_bp = Blueprint('leaves', __name__)

# Helper Functions (Simplified as the complex logic is in ORM)

def get_leave_filter_options(user):
    """Get filter options for leave listing"""
    from models.employee import Employee
    
    options = {
        'statuses': ['all', 'pending', 'approved', 'rejected', 'cancelled'],
        # FIX: Ensure a fallback if KENYAN_LABOR_LAWS is not fully loaded
        'leave_types': ['all'] + list(current_app.config.get('KENYAN_LABOR_LAWS', {}).get('leave_entitlements', {}).keys()), 
        'locations': [],
        'employees': []
    }
    
    # Locations based on role
    if user.role in ['hr_manager', 'admin']:
        options['locations'] = ['all'] + list(current_app.config.get('COMPANY_LOCATIONS', {}).keys())
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
    from models.leave import LeaveRequest
    from models.employee import Employee
    
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
        'pending': query.filter(LeaveRequest.status.in_(['pending', 'pending_hr'])).count(),
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
        LeaveRequest.requested_date >= current_month_start,
        LeaveRequest.requested_date < next_month_start
    ).count()
    
    return stats

def get_leave_types_info():
    """Get leave types information for the request form"""
    # FIX: Use kl_laws import
    from kenyan_labor_laws import KENYAN_LEAVE_LAWS
    
    info = {}
    for k, v in KENYAN_LEAVE_LAWS.items():
        info[k] = {
            'display_name': v['name'],
            'description': v['description'],
            'max_days': v.get('max_days', None) or v.get('days_with_certificate', None),
            'notice_days': v.get('notice_required_days', 0)
        }
    return info

def calculate_leave_balance(employee, leave_type):
    """Wrapper function to call Employee's ORM method"""
    from models.employee import Employee
    # Check if employee is instance of Employee model for balance calculation
    if not isinstance(employee, Employee):
        from flask_login import current_user
        if current_user.employee_id:
            employee = Employee.query.filter_by(employee_id=current_user.employee_id).first()
        if not employee:
            return 0.0
            
    return employee.calculate_leave_balance(leave_type)

def get_similar_leave_requests(leave_request):
    """Get similar leave requests for comparison"""
    from models.audit import AuditLog
    from models.leave import LeaveRequest # Local import
    
    # Get other requests from same employee, same type, last 2 years
    two_years_ago = date.today() - timedelta(days=730)
    
    similar_requests = LeaveRequest.query.filter(
        LeaveRequest.employee_id == leave_request.employee_id,
        LeaveRequest.leave_type == leave_request.leave_type,
        LeaveRequest.id != leave_request.id,
        LeaveRequest.created_date >= two_years_ago # FIX: Use created_date
    ).order_by(desc(LeaveRequest.created_date)).limit(5).all()
    
    return similar_requests

def get_leave_approval_history(leave_request):
    """Get approval history for leave request"""
    from models.audit import AuditLog
    
    # Get audit logs related to this leave request
    history = AuditLog.query.filter(
        AuditLog.target_type == 'leave_request',
        AuditLog.target_id == leave_request.id
    ).order_by(AuditLog.timestamp).all()
    
    return history

def check_leave_compliance(leave_request):
    """Check leave request compliance with Kenyan law"""
    # Use the method on the model to perform the check
    is_compliant, message = leave_request.validate_against_kenyan_law()
    
    warnings = message.split('\n') if message else []
    
    status = {
        'compliant': is_compliant,
        'warnings': warnings,
        'risk_level': 'low',
        'recommendations': []
    }
    
    if warnings and is_compliant == False:
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


@leaves_bp.route('/')
@leaves_bp.route('/list')
@login_required
def list_leaves():
    """Enhanced leave requests listing with advanced filtering"""
    # FIX: Local imports
    from models.leave import LeaveRequest
    from models.employee import Employee
    
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
        if status_filter == 'pending':
             query = query.filter(LeaveRequest.status.in_(['pending', 'pending_hr'])) # FIX: Include pending_hr
        else:
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
    per_page = current_app.config.get('ITEMS_PER_PAGE', 25)
    
    leave_requests = query.order_by(
        desc(LeaveRequest.requested_date)
    ).paginate(page=page, per_page=per_page, error_out=False)
    
    # Get filter options
    filter_options = get_leave_filter_options(current_user)
    
    # Get summary statistics
    summary_stats = get_leave_summary_stats(current_user, status_filter, leave_type_filter)
    
    return render_template('leaves/list.html',
                         leave_requests=leave_requests.items, # FIX: Pass items not pagination object
                         pagination=leave_requests,
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
    # FIX: Local imports
    from models.leave import LeaveRequest
    from models.employee import Employee
    from models.audit import AuditLog
    
    # Determine employee
    if employee_id:
        employee = Employee.query.get_or_404(employee_id)
        if current_user.role == 'station_manager' and employee.location != current_user.location:
             flash('Access denied. You can only request leave for your station employees.', 'danger')
             return redirect(url_for('leaves.list_leaves'))
    else:
        # Default to the employee associated with the current user
        employee = Employee.query.filter_by(email=current_user.email).first()
        if not employee:
            flash('Employee record not found. Please contact HR.', 'danger')
            return redirect(url_for('leaves.list_leaves'))
    
    if request.method == 'POST':
        try:
            # Get form data
            leave_type = request.form['leave_type']
            start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d').date()
            end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d').date()
            reason = request.form['reason'].strip()
            # FIX: Simplified emergency contact handling as the model is complex
            
            # Basic validation
            if start_date > end_date:
                flash('Start date cannot be after end date.', 'danger')
                raise ValueError('Invalid date range')
            
            if start_date < date.today():
                flash('Leave cannot be requested for past dates.', 'danger')
                raise ValueError('Past date not allowed')
            
            # Calculate total days
            total_days = (end_date - start_date).days + 1
            
            # Create leave request object for validation and submission
            leave_request = LeaveRequest(
                employee_id=employee.id,
                leave_type=leave_type,
                start_date=start_date,
                end_date=end_date,
                total_days=Decimal(str(total_days)), # FIX: Decimal is now imported
                reason=reason,
                requested_by=current_user.id
            )
            
            # Manually set employee relationship for validation dependency
            leave_request.employee = employee
            
            # Validate against Kenyan Labor Law and Check Balance
            leave_request.submit_request(submitted_by_user_id=current_user.id) # Submits and validates
            
            # Handle validation warnings
            if not leave_request.is_compliant:
                warning_messages = leave_request.compliance_notes.split('\n')
                
                # Check if HR override is provided
                hr_override = request.form.get('hr_override') == 'true'
                hr_override_reason = request.form.get('hr_override_reason', '').strip()
                
                if not hr_override:
                    # Show warnings to user for confirmation (Logic handled in JS/Template for re-submission)
                    # For a standard Flask post, this is difficult, we rely on the client-side validation to catch it
                    flash(f'Validation failed. Requires HR Override: {leave_request.compliance_notes}', 'warning')
                    return redirect(url_for('leaves.list_leaves'))

                else:
                    # HR override - log the override
                    AuditLog.log_security_event(
                        user_id=current_user.id,
                        event_type='leave_law_override',
                        description=f'HR override for {employee.get_full_name()} - {leave_type} - Reason: {hr_override_reason}',
                        risk_level='high',
                        details={'compliance_notes': leave_request.compliance_notes}
                    )
            
            # Logic for auto-approval is handled within LeaveRequest.submit_request or approve_by_hr

            db.session.add(leave_request)
            db.session.commit()
            
            # Log the request
            AuditLog.log_event(
                user_id=current_user.id,
                event_type='leave_request_created',
                target_type='leave_request',
                target_id=leave_request.id,
                description=f'Created {leave_type} request for {employee.get_full_name()} ({start_date} to {end_date})',
                ip_address=request.remote_addr,
                event_category='leave'
            )
            
            flash(f'Leave request submitted successfully!', 'success')
            return redirect(url_for('leaves.list_leaves'))
            
        except ValueError as e:
            flash(f'Error submitting request: {str(e)}', 'danger')
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error processing leave request: {e}')
            flash(f'System Error submitting leave request: {str(e)}', 'danger')
    
    # GET request - show form
    employees = Employee.query.filter(Employee.is_active == True).all()
    leave_types_info = get_leave_types_info()
    
    return render_template('leaves/request.html',
                         employees=employees,
                         employee=employee,
                         leave_types_info=leave_types_info)

@leaves_bp.route('/<int:id>')
@login_required
def view_leave(id):
    """Enhanced leave request view with comprehensive details"""
    # FIX: Local imports
    from models.leave import LeaveRequest
    
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

@leaves_bp.route('/<int:id>/approve', methods=['GET', 'POST']) # FIX: Added GET for template access
@login_required
def approve_leave(id):
    """Enhanced leave approval with compliance checking"""
    # FIX: Local imports
    from models.leave import LeaveRequest
    from models.audit import AuditLog
    
    leave_request = LeaveRequest.query.get_or_404(id)
    
    if current_user.role not in ['hr_manager', 'admin']:
        flash('Unauthorized to approve leaves.', 'danger')
        return redirect(url_for('leaves.list_leaves'))
    
    if leave_request.status not in ['pending', 'pending_hr']:
        flash('Leave request is not pending approval.', 'warning')
        return redirect(url_for('leaves.list_leaves'))
        
    if request.method == 'POST':
        try:
            data = request.form # FIX: Use request.form for standard form submission
            approval_notes = data.get('approval_notes', '').strip()
            
            # Final compliance check is done here (can be ignored if override is present)
            is_compliant, compliance_message = leave_request.validate_against_kenyan_law()
            
            # Approve the request
            leave_request.approve_by_hr(current_user.id, comments=approval_notes)
            
            db.session.commit()
            
            # Log the approval
            AuditLog.log_event(
                user_id=current_user.id,
                event_type='leave_approved',
                target_type='leave_request',
                target_id=leave_request.id,
                description=f'Approved {leave_request.leave_type} for {leave_request.employee.get_full_name()}',
                ip_address=request.remote_addr,
                risk_level='low',
                event_category='leave'
            )
            
            flash(f'Leave request approved for {leave_request.employee.get_full_name()}', 'success')
            return redirect(url_for('leaves.list_leaves'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error approving leave: {str(e)}', 'danger')
    
    # GET request - show approval page
    return render_template('leaves/approve.html', leave_request=leave_request, today=date.today())

@leaves_bp.route('/<int:id>/reject', methods=['GET', 'POST']) # FIX: Added GET for template access
@login_required
def reject_leave(id):
    """Enhanced leave rejection with detailed reasoning"""
    # FIX: Local imports
    from models.leave import LeaveRequest
    from models.audit import AuditLog
    
    leave_request = LeaveRequest.query.get_or_404(id)
    
    if current_user.role not in ['hr_manager', 'admin']:
        flash('Unauthorized to reject leaves.', 'danger')
        return redirect(url_for('leaves.list_leaves'))
    
    if leave_request.status not in ['pending', 'pending_hr']:
        flash('Leave request is not pending approval.', 'warning')
        return redirect(url_for('leaves.list_leaves'))
        
    if request.method == 'POST':
        try:
            data = request.form # FIX: Use request.form for standard form submission
            rejection_reason = data.get('rejection_reason', '').strip()
            
            if not rejection_reason:
                flash('Rejection reason is required.', 'danger')
                return render_template('leaves/reject.html', leave_request=leave_request, today=date.today())
            
            # Reject the request
            leave_request.reject_by_hr(current_user.id, reason=rejection_reason)
            
            db.session.commit()
            
            # Log the rejection
            AuditLog.log_event(
                user_id=current_user.id,
                event_type='leave_rejected',
                target_type='leave_request',
                target_id=leave_request.id,
                description=f'Rejected {leave_request.leave_type} for {leave_request.employee.get_full_name()} - Reason: {rejection_reason}',
                ip_address=request.remote_addr,
                risk_level='medium',
                event_category='leave'
            )
            
            flash(f'Leave request rejected for {leave_request.employee.get_full_name()}', 'success')
            return redirect(url_for('leaves.list_leaves'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error rejecting leave: {str(e)}', 'danger')
    
    # GET request - show rejection page
    return render_template('leaves/reject.html', leave_request=leave_request, today=date.today())

@leaves_bp.route('/<int:id>/cancel', methods=['POST'])
@login_required
def cancel_leave(id):
    """Cancel leave request (employee or HR)"""
    # FIX: Local imports
    from models.leave import LeaveRequest
    from models.audit import AuditLog
    
    leave_request = LeaveRequest.query.get_or_404(id)
    
    # Check permissions
    can_cancel = (
        current_user.role in ['hr_manager', 'admin'] or
        (current_user.role == 'station_manager' and 
         leave_request.employee.location == current_user.location)
    )
    
    if not can_cancel:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    if leave_request.status not in ['pending', 'approved', 'pending_hr']: # FIX: Include pending_hr
        return jsonify({'success': False, 'message': 'Cannot cancel this leave request'}), 400
    
    # Check if leave has already started
    if leave_request.start_date <= date.today():
        return jsonify({'success': False, 'message': 'Cannot cancel leave that has already started'}), 400
    
    try:
        data = request.get_json()
        cancellation_reason = data.get('reason', '').strip()
        
        # Cancel the request
        old_status = leave_request.status
        leave_request.cancel_request(current_user.id, reason=cancellation_reason)
        
        db.session.commit()
        
        # Log the cancellation
        AuditLog.log_event(
            user_id=current_user.id,
            event_type='leave_cancelled',
            target_type='leave_request',
            target_id=leave_request.id,
            description=f'Cancelled {leave_request.leave_type} for {leave_request.employee.get_full_name()} (was {old_status})',
            ip_address=request.remote_addr,
            event_category='leave'
        )
        
        return jsonify({
            'success': True,
            'message': f'Leave request cancelled for {leave_request.employee.get_full_name()}'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@leaves_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_leave(id):
    """Placeholder for edit route"""
    # FIX: Placeholder route to prevent 404s from template links
    from models.leave import LeaveRequest
    leave_request = LeaveRequest.query.get_or_404(id)
    flash('Edit functionality is under development.', 'info')
    return redirect(url_for('leaves.list_leaves'))

@leaves_bp.route('/<int:id>/delete', methods=['GET', 'POST'])
@login_required
def delete_leave(id):
    """Placeholder for delete route"""
    # FIX: Placeholder route to prevent 404s from template links
    from models.leave import LeaveRequest
    leave_request = LeaveRequest.query.get_or_404(id)
    flash('Delete functionality is disabled for audit compliance.', 'danger')
    return redirect(url_for('leaves.list_leaves'))

@leaves_bp.route('/calendar')
@login_required
def leave_calendar():
    """Enhanced leave calendar view (Placeholder)"""
    # FIX: Placeholder route to prevent 404s
    flash('Leave calendar is coming soon!', 'info')
    return redirect(url_for('leaves.list_leaves'))

@leaves_bp.route('/balance/<int:employee_id>')
@login_required
def leave_balance(employee_id):
    """View employee leave balance (Placeholder)"""
    # FIX: Placeholder route to prevent 404s
    flash('Leave balance view is coming soon!', 'info')
    return redirect(url_for('leaves.list_leaves'))

@leaves_bp.route('/reports')
@login_required
def leave_reports():
    """Enhanced leave reporting dashboard (Placeholder)"""
    # FIX: Placeholder route to prevent 404s
    return redirect(url_for('reports.reports_dashboard'))