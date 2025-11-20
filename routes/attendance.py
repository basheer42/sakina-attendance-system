"""
Enhanced Attendance Management Routes for Sakina Gas Attendance System
Built upon your existing comprehensive attendance system with advanced tracking and validation
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, g
from flask_login import login_required, current_user
from models import db, Employee, AttendanceRecord, LeaveRequest, Holiday, AuditLog
from datetime import date, datetime, timedelta
from sqlalchemy import func, and_, or_, desc, select
from config import Config
import json

attendance_bp = Blueprint('attendance', __name__)

@attendance_bp.route('/')
@attendance_bp.route('/mark')
@login_required
def mark_attendance():
    """Enhanced attendance marking with real-time validation"""
    target_date_str = request.args.get('date', date.today().isoformat())
    location_filter = request.args.get('location', 'all')
    shift_filter = request.args.get('shift', 'all')
    
    try:
        target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
    except ValueError:
        target_date = date.today()
    
    # Base query for employees based on user role
    if current_user.role == 'station_manager':
        employee_query = Employee.query.filter(
            Employee.location == current_user.location,
            Employee.is_active == True
        )
    else:
        employee_query = Employee.query.filter(Employee.is_active == True)
        
        # Apply location filter for HR managers
        if location_filter != 'all':
            employee_query = employee_query.filter(Employee.location == location_filter)
    
    # Apply shift filter
    if shift_filter != 'all':
        employee_query = employee_query.filter(Employee.shift == shift_filter)
    
    # Order by location, department, and name
    employees = employee_query.order_by(
        Employee.location,
        Employee.department, 
        Employee.first_name,
        Employee.last_name
    ).all()
    
    # Get existing attendance records with comprehensive data
    attendance_data = {}
    leave_data = {}
    
    for employee in employees:
        # Check attendance record
        attendance = AttendanceRecord.query.filter(
            AttendanceRecord.employee_id == employee.id,
            AttendanceRecord.date == target_date
        ).first()
        
        # Check approved leave
        leave_request = LeaveRequest.query.filter(
            LeaveRequest.employee_id == employee.id,
            LeaveRequest.start_date <= target_date,
            LeaveRequest.end_date >= target_date,
            LeaveRequest.status == 'approved'
        ).first()
        
        attendance_data[employee.id] = attendance
        leave_data[employee.id] = leave_request
    
    # Get filter options
    filter_options = get_attendance_filter_options(current_user)
    
    # Calculate summary for the day
    day_summary = calculate_day_summary(employees, attendance_data, leave_data)
    
    # Check if it's a holiday
    holiday = Holiday.query.filter(
        Holiday.date == target_date,
        Holiday.is_active == True
    ).first()
    
    return render_template('attendance/mark.html',
                         employees=employees,
                         attendance_data=attendance_data,
                         leave_data=leave_data,
                         target_date=target_date,
                         location_filter=location_filter,
                         shift_filter=shift_filter,
                         filter_options=filter_options,
                         day_summary=day_summary,
                         holiday=holiday)

@attendance_bp.route('/mark-employee', methods=['POST'])
@login_required
def mark_employee_attendance():
    """Enhanced individual attendance marking with validation"""
    data = request.get_json()
    
    employee_id = data.get('employee_id')
    status = data.get('status')  # present, absent, late, half_day
    notes = data.get('notes', '').strip()
    target_date_str = data.get('date', date.today().isoformat())
    clock_in_time = data.get('clock_in_time')
    
    # Validate input
    if not employee_id or not status:
        return jsonify({'success': False, 'message': 'Employee ID and status are required'}), 400
    
    # Parse date
    try:
        target_date = date.fromisoformat(target_date_str)
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid date format'}), 400
    
    # Get employee with validation
    employee = Employee.query.filter(
        Employee.id == employee_id,
        Employee.is_active == True
    ).first()
    
    if not employee:
        return jsonify({'success': False, 'message': 'Employee not found or inactive'}), 404
    
    # Check permissions
    if current_user.role == 'station_manager' and employee.location != current_user.location:
        return jsonify({'success': False, 'message': 'Access denied. You can only mark attendance for your station employees.'}), 403
    
    # Check for approved leave
    leave_request = LeaveRequest.query.filter(
        LeaveRequest.employee_id == employee.id,
        LeaveRequest.start_date <= target_date,
        LeaveRequest.end_date >= target_date,
        LeaveRequest.status == 'approved'
    ).first()
    
    if leave_request and status in ['present', 'late']:
        return jsonify({
            'success': False, 
            'message': f'Employee is on approved {leave_request.leave_type} from {leave_request.start_date} to {leave_request.end_date}'
        }), 400
    
    try:
        current_time = datetime.now()
        
        # Check if attendance already exists
        existing_attendance = AttendanceRecord.query.filter(
            AttendanceRecord.employee_id == employee.id,
            AttendanceRecord.date == target_date
        ).first()
        
        if existing_attendance:
            # Update existing record
            old_status = existing_attendance.status
            existing_attendance.status = status
            existing_attendance.notes = notes
            existing_attendance.marked_by = current_user.id
            existing_attendance.updated_at = current_time
            existing_attendance.is_corrected = True
            existing_attendance.corrected_by = current_user.id
            existing_attendance.correction_reason = f'Status changed from {old_status} to {status}'
            
            # Handle clock times
            if status in ['present', 'late', 'half_day']:
                if not existing_attendance.clock_in or clock_in_time:
                    if clock_in_time:
                        existing_attendance.clock_in = datetime.combine(target_date, datetime.strptime(clock_in_time, '%H:%M').time())
                    else:
                        existing_attendance.clock_in = current_time
            elif status == 'absent':
                existing_attendance.clock_in = None
                existing_attendance.clock_out = None
            
            action_type = 'attendance_updated'
            action_details = f'Updated attendance for {employee.employee_id} ({employee.full_name}) from {old_status} to {status}'
            
        else:
            # Create new record
            attendance = AttendanceRecord(
                employee_id=employee.id,
                date=target_date,
                status=status,
                shift=employee.shift,
                notes=notes,
                marked_by=current_user.id,
                location_marked=employee.location,
                verification_method='manual',
                ip_address=request.remote_addr
            )
            
            # Set clock times
            if status in ['present', 'late', 'half_day']:
                if clock_in_time:
                    attendance.clock_in = datetime.combine(target_date, datetime.strptime(clock_in_time, '%H:%M').time())
                else:
                    attendance.clock_in = current_time
            
            # Determine if late
            if status == 'present' and attendance.clock_in:
                if is_employee_late(employee, attendance.clock_in):
                    attendance.status = 'late'
                    attendance.late_minutes = calculate_late_minutes(employee, attendance.clock_in)
            
            db.session.add(attendance)
            action_type = 'attendance_marked'
            action_details = f'Marked attendance for {employee.employee_id} ({employee.full_name}) as {status}'
        
        # Create audit log
        AuditLog.log_action(
            user_id=current_user.id,
            action=action_type,
            target_type='attendance',
            target_id=employee.id,
            details=action_details,
            ip_address=request.remote_addr
        )
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Attendance marked successfully for {employee.full_name}',
            'status': status,
            'employee_name': employee.full_name
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error marking attendance: {str(e)}'}), 500

@attendance_bp.route('/bulk-mark', methods=['GET', 'POST'])
@login_required
def bulk_mark_attendance():
    """Enhanced bulk attendance marking with validation and error handling"""
    if request.method == 'POST':
        data = request.get_json()
        target_date_str = data.get('date', date.today().isoformat())
        employee_statuses = data.get('employees', [])
        
        if not employee_statuses:
            return jsonify({'success': False, 'message': 'No employee data provided'}), 400
        
        try:
            target_date = date.fromisoformat(target_date_str)
        except ValueError:
            return jsonify({'success': False, 'message': 'Invalid date format'}), 400
        
        success_count = 0
        error_count = 0
        errors = []
        
        try:
            for employee_data in employee_statuses:
                employee_id = employee_data.get('employee_id')
                status = employee_data.get('status')
                notes = employee_data.get('notes', '')
                
                # Validate employee
                employee = Employee.query.filter(
                    Employee.id == employee_id,
                    Employee.is_active == True
                ).first()
                
                if not employee:
                    error_count += 1
                    errors.append(f'Employee ID {employee_id}: Not found or inactive')
                    continue
                
                # Check permissions
                if current_user.role == 'station_manager' and employee.location != current_user.location:
                    error_count += 1
                    errors.append(f'{employee.full_name}: Access denied')
                    continue
                
                # Check for leave conflicts
                leave_request = LeaveRequest.query.filter(
                    LeaveRequest.employee_id == employee.id,
                    LeaveRequest.start_date <= target_date,
                    LeaveRequest.end_date >= target_date,
                    LeaveRequest.status == 'approved'
                ).first()
                
                if leave_request and status in ['present', 'late']:
                    error_count += 1
                    errors.append(f'{employee.full_name}: On approved leave')
                    continue
                
                # Process attendance
                current_time = datetime.now()
                existing_attendance = AttendanceRecord.query.filter(
                    AttendanceRecord.employee_id == employee.id,
                    AttendanceRecord.date == target_date
                ).first()
                
                if existing_attendance:
                    # Update existing
                    existing_attendance.status = status
                    existing_attendance.notes = notes
                    existing_attendance.marked_by = current_user.id
                    existing_attendance.updated_at = current_time
                else:
                    # Create new
                    attendance = AttendanceRecord(
                        employee_id=employee.id,
                        date=target_date,
                        status=status,
                        shift=employee.shift,
                        notes=notes,
                        marked_by=current_user.id,
                        clock_in=current_time if status in ['present', 'late'] else None,
                        location_marked=employee.location,
                        verification_method='bulk_manual',
                        ip_address=request.remote_addr
                    )
                    db.session.add(attendance)
                
                success_count += 1
            
            # Create bulk audit log
            AuditLog.log_action(
                user_id=current_user.id,
                action='bulk_attendance_marked',
                target_type='attendance',
                details=f'Bulk marked attendance for {success_count} employees on {target_date}. Errors: {error_count}',
                ip_address=request.remote_addr
            )
            
            db.session.commit()
            
            response_data = {
                'success': True,
                'message': f'Bulk attendance completed. Success: {success_count}, Errors: {error_count}',
                'success_count': success_count,
                'error_count': error_count
            }
            
            if errors:
                response_data['errors'] = errors
            
            return jsonify(response_data)
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': f'Error processing bulk attendance: {str(e)}'}), 500
    
    # GET request - show bulk marking interface
    target_date = date.today()
    
    # Get employees for bulk marking
    if current_user.role == 'station_manager':
        employees = Employee.query.filter(
            Employee.location == current_user.location,
            Employee.is_active == True
        ).order_by(Employee.first_name, Employee.last_name).all()
    else:
        employees = Employee.query.filter(Employee.is_active == True).order_by(
            Employee.location, Employee.first_name, Employee.last_name
        ).all()
    
    # Get existing attendance for today
    existing_attendance = {}
    for employee in employees:
        attendance = AttendanceRecord.query.filter(
            AttendanceRecord.employee_id == employee.id,
            AttendanceRecord.date == target_date
        ).first()
        existing_attendance[employee.id] = attendance
    
    return render_template('attendance/bulk_mark.html',
                         employees=employees,
                         existing_attendance=existing_attendance,
                         target_date=target_date)

@attendance_bp.route('/clock-in/<int:employee_id>', methods=['POST'])
@login_required
def clock_in_employee(employee_id):
    """Enhanced clock-in with time validation"""
    employee = Employee.query.get_or_404(employee_id)
    
    # Check permissions
    if current_user.role == 'station_manager' and employee.location != current_user.location:
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    today = date.today()
    
    # Check if already clocked in
    existing_attendance = AttendanceRecord.query.filter(
        AttendanceRecord.employee_id == employee.id,
        AttendanceRecord.date == today
    ).first()
    
    if existing_attendance and existing_attendance.clock_in:
        return jsonify({
            'success': False, 
            'message': 'Employee already clocked in today',
            'clock_in_time': existing_attendance.clock_in.strftime('%H:%M')
        }), 400
    
    try:
        current_time = datetime.now()
        
        # Determine if late
        is_late = is_employee_late(employee, current_time)
        status = 'late' if is_late else 'present'
        late_minutes = calculate_late_minutes(employee, current_time) if is_late else 0
        
        if existing_attendance:
            # Update existing record
            existing_attendance.clock_in = current_time
            existing_attendance.status = status
            existing_attendance.late_minutes = late_minutes
            existing_attendance.marked_by = current_user.id
        else:
            # Create new record
            attendance = AttendanceRecord(
                employee_id=employee.id,
                date=today,
                status=status,
                shift=employee.shift,
                clock_in=current_time,
                late_minutes=late_minutes,
                marked_by=current_user.id,
                location_marked=employee.location,
                verification_method='clock_in',
                ip_address=request.remote_addr
            )
            db.session.add(attendance)
        
        # Create audit log
        AuditLog.log_action(
            user_id=current_user.id,
            action='clock_in',
            target_type='attendance',
            target_id=employee.id,
            details=f'Clocked in {employee.employee_id} at {current_time.strftime("%H:%M")} - {status}',
            ip_address=request.remote_addr
        )
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'{employee.full_name} clocked in successfully',
            'status': status,
            'clock_in_time': current_time.strftime('%H:%M'),
            'late_minutes': late_minutes,
            'is_late': is_late
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error clocking in: {str(e)}'}), 500

@attendance_bp.route('/clock-out/<int:employee_id>', methods=['POST'])
@login_required
def clock_out_employee(employee_id):
    """Enhanced clock-out with hours calculation"""
    employee = Employee.query.get_or_404(employee_id)
    
    # Check permissions
    if current_user.role == 'station_manager' and employee.location != current_user.location:
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    today = date.today()
    
    # Find active attendance record
    attendance = AttendanceRecord.query.filter(
        AttendanceRecord.employee_id == employee.id,
        AttendanceRecord.date == today,
        AttendanceRecord.status.in_(['present', 'late'])
    ).first()
    
    if not attendance:
        return jsonify({'success': False, 'message': 'No active attendance record found'}), 404
    
    if attendance.clock_out:
        return jsonify({
            'success': False, 
            'message': 'Employee already clocked out',
            'clock_out_time': attendance.clock_out.strftime('%H:%M')
        }), 400
    
    try:
        current_time = datetime.now()
        attendance.clock_out = current_time
        attendance.updated_at = current_time
        
        # Calculate hours worked and overtime
        attendance.update_hours_worked()
        
        # Create audit log
        AuditLog.log_action(
            user_id=current_user.id,
            action='clock_out',
            target_type='attendance',
            target_id=employee.id,
            details=f'Clocked out {employee.employee_id} at {current_time.strftime("%H:%M")}. Hours worked: {attendance.hours_worked}',
            ip_address=request.remote_addr
        )
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'{employee.full_name} clocked out successfully',
            'clock_out_time': current_time.strftime('%H:%M'),
            'hours_worked': round(float(attendance.hours_worked), 2),
            'overtime_hours': round(float(attendance.overtime_hours or 0), 2),
            'total_break_time': round(attendance.break_time, 2)
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error clocking out: {str(e)}'}), 500

@attendance_bp.route('/history')
@login_required
def attendance_history():
    """Enhanced attendance history with advanced filtering"""
    # Get filter parameters
    start_date_str = request.args.get('start_date', (date.today() - timedelta(days=30)).isoformat())
    end_date_str = request.args.get('end_date', date.today().isoformat())
    employee_filter = request.args.get('employee', 'all')
    location_filter = request.args.get('location', 'all')
    department_filter = request.args.get('department', 'all')
    status_filter = request.args.get('status', 'all')
    
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    except ValueError:
        start_date = date.today() - timedelta(days=30)
        end_date = date.today()
    
    # Build query based on user role
    if current_user.role == 'station_manager':
        base_query = db.session.query(AttendanceRecord).join(Employee).filter(
            Employee.location == current_user.location,
            Employee.is_active == True,
            AttendanceRecord.date >= start_date,
            AttendanceRecord.date <= end_date
        )
    else:
        base_query = db.session.query(AttendanceRecord).join(Employee).filter(
            Employee.is_active == True,
            AttendanceRecord.date >= start_date,
            AttendanceRecord.date <= end_date
        )
    
    # Apply filters
    if employee_filter != 'all':
        base_query = base_query.filter(Employee.id == employee_filter)
    
    if location_filter != 'all' and current_user.role != 'station_manager':
        base_query = base_query.filter(Employee.location == location_filter)
    
    if department_filter != 'all':
        base_query = base_query.filter(Employee.department == department_filter)
    
    if status_filter != 'all':
        if status_filter == 'present_late':
            base_query = base_query.filter(AttendanceRecord.status.in_(['present', 'late']))
        else:
            base_query = base_query.filter(AttendanceRecord.status == status_filter)
    
    # Order and paginate
    page = request.args.get('page', 1, type=int)
    per_page = 50
    
    attendance_records = base_query.order_by(
        desc(AttendanceRecord.date),
        Employee.first_name,
        Employee.last_name
    ).paginate(page=page, per_page=per_page, error_out=False)
    
    # Calculate summary statistics
    summary_stats = calculate_history_summary(base_query.all())
    
    # Get filter options
    filter_options = get_history_filter_options(current_user)
    
    return render_template('attendance/history.html',
                         attendance_records=attendance_records,
                         summary_stats=summary_stats,
                         filter_options=filter_options,
                         start_date=start_date,
                         end_date=end_date,
                         employee_filter=employee_filter,
                         location_filter=location_filter,
                         department_filter=department_filter,
                         status_filter=status_filter)

@attendance_bp.route('/reports')
@login_required
def attendance_reports():
    """Enhanced attendance reporting dashboard"""
    if current_user.role == 'station_manager':
        flash('Access denied. HR Manager privileges required for detailed reports.', 'danger')
        return redirect(url_for('attendance.mark_attendance'))
    
    # Get report parameters
    report_type = request.args.get('type', 'daily')
    start_date_str = request.args.get('start_date', date.today().isoformat())
    end_date_str = request.args.get('end_date', date.today().isoformat())
    
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    except ValueError:
        start_date = end_date = date.today()
    
    # Generate reports based on type
    if report_type == 'daily':
        report_data = generate_daily_report(start_date)
    elif report_type == 'weekly':
        report_data = generate_weekly_report(start_date, end_date)
    elif report_type == 'monthly':
        report_data = generate_monthly_report(start_date, end_date)
    elif report_type == 'department':
        report_data = generate_department_report(start_date, end_date)
    elif report_type == 'location':
        report_data = generate_location_report(start_date, end_date)
    else:
        report_data = generate_daily_report(date.today())
    
    return render_template('attendance/reports.html',
                         report_data=report_data,
                         report_type=report_type,
                         start_date=start_date,
                         end_date=end_date)

# Helper Functions

def get_attendance_filter_options(user):
    """Get filter options for attendance marking"""
    options = {
        'locations': [],
        'shifts': ['all', 'day', 'night'],
        'statuses': ['present', 'absent', 'late', 'half_day']
    }
    
    if user.role == 'hr_manager':
        options['locations'] = ['all'] + list(Config.COMPANY_LOCATIONS.keys())
    elif user.role == 'station_manager':
        options['locations'] = [user.location]
    
    return options

def calculate_day_summary(employees, attendance_data, leave_data):
    """Calculate summary statistics for the day"""
    total = len(employees)
    present = sum(1 for emp in employees if attendance_data.get(emp.id) and attendance_data[emp.id].status in ['present', 'late'])
    absent = sum(1 for emp in employees if attendance_data.get(emp.id) and attendance_data[emp.id].status == 'absent')
    on_leave = sum(1 for emp in employees if leave_data.get(emp.id))
    not_marked = total - present - absent - on_leave
    late = sum(1 for emp in employees if attendance_data.get(emp.id) and attendance_data[emp.id].status == 'late')
    
    return {
        'total': total,
        'present': present,
        'absent': absent,
        'on_leave': on_leave,
        'not_marked': not_marked,
        'late': late,
        'attendance_rate': round((present / total * 100), 1) if total > 0 else 0
    }

def is_employee_late(employee, clock_in_time):
    """Check if employee is late based on shift and grace period"""
    # Get expected start time based on shift
    if employee.shift == 'day':
        expected_start = clock_in_time.replace(hour=6, minute=0, second=0, microsecond=0)
    elif employee.shift == 'night':
        expected_start = clock_in_time.replace(hour=18, minute=0, second=0, microsecond=0)
    else:  # Head office or no shift
        expected_start = clock_in_time.replace(hour=8, minute=0, second=0, microsecond=0)
    
    # Add grace period
    grace_period = Config.ATTENDANCE_GRACE_PERIOD  # minutes
    expected_start_with_grace = expected_start + timedelta(minutes=grace_period)
    
    return clock_in_time > expected_start_with_grace

def calculate_late_minutes(employee, clock_in_time):
    """Calculate how many minutes late the employee is"""
    # Get expected start time based on shift
    if employee.shift == 'day':
        expected_start = clock_in_time.replace(hour=6, minute=0, second=0, microsecond=0)
    elif employee.shift == 'night':
        expected_start = clock_in_time.replace(hour=18, minute=0, second=0, microsecond=0)
    else:  # Head office or no shift
        expected_start = clock_in_time.replace(hour=8, minute=0, second=0, microsecond=0)
    
    if clock_in_time > expected_start:
        return int((clock_in_time - expected_start).total_seconds() / 60)
    return 0

def calculate_history_summary(attendance_records):
    """Calculate summary statistics for attendance history"""
    if not attendance_records:
        return {'total': 0}
    
    total = len(attendance_records)
    present = sum(1 for record in attendance_records if record.status in ['present', 'late'])
    absent = sum(1 for record in attendance_records if record.status == 'absent')
    late = sum(1 for record in attendance_records if record.status == 'late')
    on_leave = sum(1 for record in attendance_records if 'leave' in record.status)
    
    # Calculate total hours worked
    total_hours = sum(float(record.hours_worked or 0) for record in attendance_records)
    total_overtime = sum(float(record.overtime_hours or 0) for record in attendance_records)
    
    return {
        'total': total,
        'present': present,
        'absent': absent,
        'late': late,
        'on_leave': on_leave,
        'attendance_rate': round((present / total * 100), 1) if total > 0 else 0,
        'total_hours': round(total_hours, 2),
        'total_overtime': round(total_overtime, 2),
        'average_daily_hours': round(total_hours / total, 2) if total > 0 else 0
    }

def get_history_filter_options(user):
    """Get filter options for attendance history"""
    options = {
        'locations': [],
        'departments': list(Config.DEPARTMENTS.keys()),
        'statuses': ['all', 'present', 'absent', 'late', 'present_late', 'half_day']
    }
    
    if user.role == 'hr_manager':
        options['locations'] = ['all'] + list(Config.COMPANY_LOCATIONS.keys())
        
        # Get employees for dropdown
        options['employees'] = Employee.query.filter(Employee.is_active == True).order_by(
            Employee.first_name, Employee.last_name
        ).all()
    elif user.role == 'station_manager':
        options['locations'] = [user.location]
        
        # Get station employees
        options['employees'] = Employee.query.filter(
            Employee.location == user.location,
            Employee.is_active == True
        ).order_by(Employee.first_name, Employee.last_name).all()
    
    return options

def generate_daily_report(target_date):
    """Generate daily attendance report"""
    # Get all employees with their attendance for the day
    employees = Employee.query.filter(Employee.is_active == True).all()
    
    report_data = {
        'date': target_date,
        'type': 'daily',
        'locations': {},
        'summary': {'total': 0, 'present': 0, 'absent': 0, 'late': 0, 'on_leave': 0}
    }
    
    for location in Config.COMPANY_LOCATIONS.keys():
        location_employees = [emp for emp in employees if emp.location == location]
        location_attendance = []
        
        for employee in location_employees:
            attendance = AttendanceRecord.query.filter(
                AttendanceRecord.employee_id == employee.id,
                AttendanceRecord.date == target_date
            ).first()
            
            leave_request = LeaveRequest.query.filter(
                LeaveRequest.employee_id == employee.id,
                LeaveRequest.start_date <= target_date,
                LeaveRequest.end_date >= target_date,
                LeaveRequest.status == 'approved'
            ).first()
            
            status = 'not_marked'
            if leave_request:
                status = 'on_leave'
            elif attendance:
                status = attendance.status
            
            location_attendance.append({
                'employee': employee,
                'attendance': attendance,
                'leave_request': leave_request,
                'status': status
            })
            
            # Update summary
            report_data['summary']['total'] += 1
            if status in ['present', 'late']:
                report_data['summary']['present'] += 1
            elif status == 'absent':
                report_data['summary']['absent'] += 1
            elif status == 'late':
                report_data['summary']['late'] += 1
            elif status == 'on_leave':
                report_data['summary']['on_leave'] += 1
        
        report_data['locations'][location] = location_attendance
    
    # Calculate attendance rate
    if report_data['summary']['total'] > 0:
        report_data['summary']['attendance_rate'] = round(
            (report_data['summary']['present'] / report_data['summary']['total'] * 100), 1
        )
    
    return report_data

def generate_weekly_report(start_date, end_date):
    """Generate weekly attendance report"""
    # Implementation for weekly report
    return {'type': 'weekly', 'message': 'Weekly report generation in progress'}

def generate_monthly_report(start_date, end_date):
    """Generate monthly attendance report"""
    # Implementation for monthly report
    return {'type': 'monthly', 'message': 'Monthly report generation in progress'}

def generate_department_report(start_date, end_date):
    """Generate department-wise attendance report"""
    # Implementation for department report
    return {'type': 'department', 'message': 'Department report generation in progress'}

def generate_location_report(start_date, end_date):
    """Generate location-wise attendance report"""
    # Implementation for location report
    return {'type': 'location', 'message': 'Location report generation in progress'}

# API Endpoints

@attendance_bp.route('/api/daily-summary')
@login_required
def api_daily_summary():
    """API endpoint for daily attendance summary"""
    target_date_str = request.args.get('date', date.today().isoformat())
    
    try:
        target_date = date.fromisoformat(target_date_str)
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400
    
    # Get summary based on user role
    if current_user.role == 'station_manager':
        employees = Employee.query.filter(
            Employee.location == current_user.location,
            Employee.is_active == True
        ).all()
    else:
        employees = Employee.query.filter(Employee.is_active == True).all()
    
    # Calculate statistics
    total = len(employees)
    present = absent = late = on_leave = 0
    
    for employee in employees:
        # Check attendance
        attendance = AttendanceRecord.query.filter(
            AttendanceRecord.employee_id == employee.id,
            AttendanceRecord.date == target_date
        ).first()
        
        # Check leave
        leave_request = LeaveRequest.query.filter(
            LeaveRequest.employee_id == employee.id,
            LeaveRequest.start_date <= target_date,
            LeaveRequest.end_date >= target_date,
            LeaveRequest.status == 'approved'
        ).first()
        
        if leave_request:
            on_leave += 1
        elif attendance:
            if attendance.status in ['present', 'late']:
                present += 1
                if attendance.status == 'late':
                    late += 1
            elif attendance.status == 'absent':
                absent += 1
    
    return jsonify({
        'date': target_date.isoformat(),
        'total_employees': total,
        'present': present,
        'absent': absent,
        'late': late,
        'on_leave': on_leave,
        'not_marked': total - present - absent - on_leave,
        'attendance_rate': round((present / total * 100), 1) if total > 0 else 0
    })

@attendance_bp.route('/api/employee-status/<int:employee_id>')
@login_required
def api_employee_status(employee_id):
    """API endpoint for individual employee attendance status"""
    employee = Employee.query.get_or_404(employee_id)
    
    # Check permissions
    if (current_user.role == 'station_manager' and 
        employee.location != current_user.location):
        return jsonify({'error': 'Unauthorized'}), 403
    
    target_date_str = request.args.get('date', date.today().isoformat())
    
    try:
        target_date = date.fromisoformat(target_date_str)
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400
    
    # Get attendance record
    attendance = AttendanceRecord.query.filter(
        AttendanceRecord.employee_id == employee.id,
        AttendanceRecord.date == target_date
    ).first()
    
    # Get leave request
    leave_request = LeaveRequest.query.filter(
        LeaveRequest.employee_id == employee.id,
        LeaveRequest.start_date <= target_date,
        LeaveRequest.end_date >= target_date,
        LeaveRequest.status == 'approved'
    ).first()
    
    response_data = {
        'employee_id': employee.id,
        'employee_name': employee.full_name,
        'date': target_date.isoformat(),
        'status': 'not_marked',
        'clock_in': None,
        'clock_out': None,
        'hours_worked': 0,
        'on_leave': False,
        'leave_type': None
    }
    
    if leave_request:
        response_data.update({
            'status': 'on_leave',
            'on_leave': True,
            'leave_type': leave_request.leave_type
        })
    elif attendance:
        response_data.update({
            'status': attendance.status,
            'clock_in': attendance.clock_in.strftime('%H:%M') if attendance.clock_in else None,
            'clock_out': attendance.clock_out.strftime('%H:%M') if attendance.clock_out else None,
            'hours_worked': float(attendance.hours_worked) if attendance.hours_worked else 0,
            'notes': attendance.notes
        })
    
    return jsonify(response_data)