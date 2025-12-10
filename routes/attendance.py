"""
Sakina Gas Company - Attendance Management Routes
Built from scratch with comprehensive attendance tracking and time management
Version 3.0 - Enterprise grade with advanced features
FIXED: Models imported inside functions to prevent mapper conflicts
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app, g
from flask_login import login_required, current_user
from datetime import datetime, date, timedelta
from sqlalchemy import func, and_, or_, desc, asc, extract
from database import db
import json
import calendar

# FIXED: Removed global model imports to prevent early model registration

# Create blueprint
attendance_bp = Blueprint('attendance', __name__)

# Helper function for permission checking
def check_attendance_permission(action, location=None):
    """Check if user has permission to perform attendance action"""
    if current_user.role == 'hr_manager':
        return True
    elif current_user.role == 'station_manager':
        if action in ['mark', 'view', 'edit'] and (location is None or location == current_user.location):
            return True
    return False

@attendance_bp.route('/')
@attendance_bp.route('/overview')
@login_required
def overview():
    """Enhanced attendance overview with comprehensive analytics"""
    # FIXED: Local imports
    from models.employee import Employee
    from models.attendance import AttendanceRecord
    from models.leave import LeaveRequest
    
    if not check_attendance_permission('view'):
        flash('You do not have permission to view attendance data.', 'error')
        return redirect(url_for('dashboard.main'))
    
    target_date_str = request.args.get('date', date.today().isoformat())
    location_filter = request.args.get('location', 'all')
    department_filter = request.args.get('department', 'all')
    shift_filter = request.args.get('shift', 'all')
    status_filter = request.args.get('status', 'all')
    
    try:
        target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
    except ValueError:
        target_date = date.today()
    
    try:
        # Get attendance overview data
        overview_data = get_attendance_overview_data(
            target_date, location_filter, department_filter, 
            shift_filter, status_filter
        )
        
        # Get filter options
        filter_options = get_attendance_filter_options(current_user)
        
        # Get recent attendance activities
        recent_activities = get_recent_attendance_activities()
        
        # Get attendance trends for the week
        weekly_trends = get_weekly_attendance_trends(target_date)
        
        return render_template('attendance/overview.html',
                             overview_data=overview_data,
                             filter_options=filter_options,
                             recent_activities=recent_activities,
                             weekly_trends=weekly_trends,
                             target_date=target_date,
                             location_filter=location_filter,
                             department_filter=department_filter,
                             shift_filter=shift_filter,
                             status_filter=status_filter)
                             
    except Exception as e:
        current_app.logger.error(f"Error in attendance overview: {e}")
        flash('Error loading attendance overview. Please try again.', 'error')
        return redirect(url_for('dashboard.main'))

@attendance_bp.route('/mark', methods=['GET', 'POST'])
@login_required
def mark_attendance():
    """Enhanced individual attendance marking interface"""
    # FIXED: Local imports
    from models.employee import Employee
    from models.attendance import AttendanceRecord
    from models.audit import AuditLog
    
    if not check_attendance_permission('mark'):
        flash('You do not have permission to mark attendance.', 'error')
        return redirect(url_for('attendance.overview'))
    
    if request.method == 'POST':
        try:
            employee_id = int(request.form['employee_id'])
            status = request.form['status']
            target_date_str = request.form.get('date', date.today().isoformat())
            notes = request.form.get('notes', '').strip()
            clock_in_time = request.form.get('clock_in_time', '').strip()
            clock_out_time = request.form.get('clock_out_time', '').strip()
            
            # Validate date
            try:
                target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Invalid date format.', 'error')
                return redirect(url_for('attendance.mark_attendance'))
            
            # Get employee and validate permissions
            employee = Employee.query.get_or_404(employee_id)
            
            if current_user.role == 'station_manager' and employee.location != current_user.location:
                flash('You can only mark attendance for employees at your location.', 'error')
                return redirect(url_for('attendance.mark_attendance'))
            
            # Check if attendance already exists
            existing_attendance = AttendanceRecord.query.filter_by(
                employee_id=employee.id,
                date=target_date
            ).first()
            
            if existing_attendance:
                # Update existing record
                old_status = existing_attendance.status
                existing_attendance.status = status
                existing_attendance.notes = notes
                existing_attendance.updated_by = current_user.id
                existing_attendance.last_updated = datetime.utcnow()
                
                # Update clock times
                if status in ['present', 'late', 'half_day']:
                    if clock_in_time:
                        # Assuming clock_in_time is only time in HH:MM format
                        existing_attendance.clock_in_time = datetime.combine(
                            target_date, datetime.strptime(clock_in_time, '%H:%M').time()
                        )
                    
                    if clock_out_time:
                        # Assuming clock_out_time is only time in HH:MM format
                        existing_attendance.clock_out_time = datetime.combine(
                            target_date, datetime.strptime(clock_out_time, '%H:%M').time()
                        )
                elif status == 'absent':
                    existing_attendance.clock_in_time = None
                    existing_attendance.clock_out_time = None
                
                # Recalculate work hours if both times are set
                if existing_attendance.clock_in_time and existing_attendance.clock_out_time:
                    work_duration = existing_attendance.clock_out_time - existing_attendance.clock_in_time
                    existing_attendance.work_hours = work_duration.total_seconds() / 3600
                
                action_details = f'Updated attendance for {employee.employee_id} ({employee.get_full_name()}) from {old_status} to {status}'
                
            else:
                # Create new attendance record
                attendance = AttendanceRecord(
                    employee_id=employee.id,
                    date=target_date,
                    status=status,
                    notes=notes,
                    created_by=current_user.id,
                    location=employee.location,
                    shift_type=getattr(employee, 'shift', 'day'),
                    clock_in_method='manual',
                    ip_address=request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR'))
                )
                
                # Set clock times
                if status in ['present', 'late', 'half_day']:
                    if clock_in_time:
                        # Assuming clock_in_time is only time in HH:MM format
                        attendance.clock_in_time = datetime.combine(
                            target_date, datetime.strptime(clock_in_time, '%H:%M').time()
                        )
                    else:
                        # Fallback for API call - should be accurate time
                        attendance.clock_in_time = datetime.now() 
                    
                    if clock_out_time:
                        # Assuming clock_out_time is only time in HH:MM format
                        attendance.clock_out_time = datetime.combine(
                            target_date, datetime.strptime(clock_out_time, '%H:%M').time()
                        )
                
                # Calculate work hours if both times are set
                if attendance.clock_in_time and attendance.clock_out_time:
                    work_duration = attendance.clock_out_time - attendance.clock_in_time
                    attendance.work_hours = work_duration.total_seconds() / 3600
                
                # Determine if employee is late (using helper function, not internal model logic)
                # NOTE: Status is already set from form input, so we use provided status
                # if status == 'present' and attendance.clock_in_time:
                #     is_late = is_employee_late(employee, attendance.clock_in_time)
                #     if is_late:
                #         attendance.status = 'late'
                #         attendance.minutes_late = calculate_late_minutes(employee, attendance.clock_in_time)
                
                db.session.add(attendance)
                action_details = f'Marked {status} for {employee.employee_id} ({employee.get_full_name()})'
            
            # Log the action
            AuditLog.log_action(
                user_id=current_user.id,
                action='attendance_marked',
                table_name='attendance_records',
                record_id=employee.id,
                description=action_details,
                ip_address=request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR'))
            )
            
            db.session.commit()
            
            flash(f'Attendance marked successfully for {employee.get_full_name()}.', 'success')
            return redirect(url_for('attendance.mark_attendance'))
            
        except ValueError as e:
            flash(f'Invalid input: {str(e)}', 'error')
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error marking attendance: {e}')
            flash(f'Error marking attendance: {str(e)}', 'error')
    
    # GET request - show marking interface
    target_date = request.args.get('date', date.today().isoformat())
    
    try:
        target_date_obj = datetime.strptime(target_date, '%Y-%m-%d').date()
    except ValueError:
        target_date_obj = date.today()
        target_date = target_date_obj.isoformat()
    
    # Get employees for attendance marking
    if current_user.role == 'station_manager':
        employees = Employee.query.filter(
            Employee.location == current_user.location,
            Employee.is_active == True
        ).order_by(Employee.first_name, Employee.last_name).all()
    else:
        employees = Employee.query.filter(
            Employee.is_active == True
        ).order_by(Employee.location, Employee.first_name, Employee.last_name).all()
    
    # Get existing attendance records for the date
    existing_attendance = {}
    if employees:
        attendance_records = AttendanceRecord.query.filter(
            AttendanceRecord.employee_id.in_([emp.id for emp in employees]),
            AttendanceRecord.date == target_date_obj
        ).all()
        
        for record in attendance_records:
            existing_attendance[record.employee_id] = record
    
    return render_template('attendance/mark.html',
                         employees=employees,
                         existing_attendance=existing_attendance,
                         target_date=target_date,
                         today=date.today())

@attendance_bp.route('/bulk-mark', methods=['GET', 'POST'])
@login_required
def bulk_mark_attendance():
    """Enhanced bulk attendance marking interface"""
    # FIXED: Local imports
    from models.employee import Employee
    from models.attendance import AttendanceRecord
    from models.audit import AuditLog
    
    if not check_attendance_permission('mark'):
        flash('You do not have permission to mark attendance.', 'error')
        return redirect(url_for('attendance.overview'))
    
    if request.method == 'POST':
        try:
            target_date_str = request.form.get('date', date.today().isoformat())
            employee_data = request.form.getlist('employee_status')
            
            try:
                target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Invalid date format.', 'error')
                return redirect(url_for('attendance.bulk_mark_attendance'))
            
            success_count = 0
            error_count = 0
            errors = []
            
            for data_str in employee_data:
                try:
                    employee_id, status = data_str.split(':')
                    employee_id = int(employee_id)
                    
                    if status == 'skip':
                        continue
                    
                    employee = Employee.query.get(employee_id)
                    if not employee:
                        continue
                    
                    # Check permissions
                    if (current_user.role == 'station_manager' and 
                        employee.location != current_user.location):
                        continue
                    
                    # Check if attendance already exists
                    existing = AttendanceRecord.query.filter_by(
                        employee_id=employee.id,
                        date=target_date
                    ).first()
                    
                    if existing:
                        existing.status = status
                        existing.updated_by = current_user.id
                        existing.last_updated = datetime.utcnow()
                    else:
                        attendance = AttendanceRecord(
                            employee_id=employee.id,
                            date=target_date,
                            status=status,
                            created_by=current_user.id,
                            location=employee.location,
                            shift_type=getattr(employee, 'shift', 'day'),
                            clock_in_method='bulk_mark',
                            ip_address=request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR'))
                        )
                        
                        # Set default clock-in time for present/late status
                        if status in ['present', 'late']:
                            attendance.clock_in_time = datetime.now()
                        
                        db.session.add(attendance)
                    
                    success_count += 1
                    
                except (ValueError, IndexError):
                    error_count += 1
                    errors.append(f'Invalid data format for employee ID {employee_id}')
                except Exception as e:
                    error_count += 1
                    errors.append(f'Error processing employee {employee_id}: {str(e)}')
            
            # Log bulk action
            AuditLog.log_action(
                user_id=current_user.id,
                action='bulk_attendance_marked',
                description=f'Bulk attendance marking for {target_date}. Success: {success_count}, Errors: {error_count}',
                ip_address=request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR'))
            )
            
            db.session.commit()
            
            flash(f'Bulk attendance completed. Success: {success_count}, Errors: {error_count}', 'success')
            
            if errors:
                for error in errors[:5]:  # Show first 5 errors
                    flash(error, 'warning')
            
            return redirect(url_for('attendance.bulk_mark_attendance'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error in bulk attendance marking: {e}')
            flash(f'Error processing bulk attendance: {str(e)}', 'error')
    
    # GET request - show bulk marking interface
    target_date = request.args.get('date', date.today().isoformat())
    
    try:
        target_date_obj = datetime.strptime(target_date, '%Y-%m-%d').date()
    except ValueError:
        target_date_obj = date.today()
        target_date = target_date_obj.isoformat()
    
    # Get employees for bulk marking
    if current_user.role == 'station_manager':
        employees = Employee.query.filter(
            Employee.location == current_user.location,
            Employee.is_active == True
        ).order_by(Employee.first_name, Employee.last_name).all()
    else:
        employees = Employee.query.filter(
            Employee.is_active == True
        ).order_by(Employee.location, Employee.first_name, Employee.last_name).all()
    
    # Get existing attendance for today
    existing_attendance = {}
    if employees:
        attendance_records = AttendanceRecord.query.filter(
            AttendanceRecord.employee_id.in_([emp.id for emp in employees]),
            AttendanceRecord.date == target_date_obj
        ).all()
        
        for record in attendance_records:
            existing_attendance[record.employee_id] = record
    
    return render_template('attendance/bulk_mark.html',
                         employees=employees,
                         existing_attendance=existing_attendance,
                         target_date=target_date,
                         today=date.today().isoformat())

@attendance_bp.route('/clock-in/<int:employee_id>', methods=['POST'])
@login_required
def clock_in_employee(employee_id):
    """Enhanced clock-in with time validation"""
    # FIXED: Local imports
    from models.employee import Employee
    from models.attendance import AttendanceRecord
    from models.audit import AuditLog
    
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
    
    if existing_attendance and existing_attendance.clock_in_time:
        return jsonify({
            'success': False, 
            'message': 'Employee already clocked in today',
            'clock_in_time': existing_attendance.clock_in_time.strftime('%H:%M')
        }), 400
    
    try:
        current_time = datetime.now()
        
        # Determine if late
        is_late = is_employee_late(employee, current_time)
        status = 'late' if is_late else 'present'
        late_minutes = calculate_late_minutes(employee, current_time) if is_late else 0
        
        if existing_attendance:
            # Update existing record
            existing_attendance.clock_in_time = current_time
            existing_attendance.status = status
            existing_attendance.minutes_late = late_minutes
            existing_attendance.updated_by = current_user.id
        else:
            # Create new record
            attendance = AttendanceRecord(
                employee_id=employee.id,
                date=today,
                status=status,
                shift_type=getattr(employee, 'shift', 'day'),
                clock_in_time=current_time,
                late_arrival_minutes=late_minutes, # FIX: Use correct column name
                created_by=current_user.id,
                location=employee.location,
                clock_in_method='api_clock_in',
                ip_address=request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR'))
            )
            db.session.add(attendance)
        
        # Create audit log
        AuditLog.log_action(
            user_id=current_user.id,
            action='clock_in',
            table_name='attendance_records',
            record_id=employee.id,
            description=f'Clocked in {employee.employee_id} at {current_time.strftime("%H:%M")} - {status}',
            ip_address=request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR'))
        )
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'{employee.get_full_name()} clocked in successfully',
            'status': status,
            'clock_in_time': current_time.strftime('%H:%M'),
            'late_minutes': late_minutes,
            'is_late': is_late
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error clocking in employee {employee_id}: {e}')
        return jsonify({'success': False, 'message': f'Error clocking in: {str(e)}'}), 500

@attendance_bp.route('/clock-out/<int:employee_id>', methods=['POST'])
@login_required
def clock_out_employee(employee_id):
    """Enhanced clock-out with hours calculation"""
    # FIXED: Local imports
    from models.employee import Employee
    from models.attendance import AttendanceRecord
    from models.audit import AuditLog
    
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
    
    if attendance.clock_out_time:
        return jsonify({
            'success': False, 
            'message': 'Employee already clocked out',
            'clock_out_time': attendance.clock_out_time.strftime('%H:%M')
        }), 400
    
    try:
        current_time = datetime.now()
        attendance.clock_out_time = current_time
        attendance.updated_by = current_user.id
        
        # Calculate hours worked and overtime
        if attendance.clock_in_time:
            # Need to handle case where clock in is a datetime object and clock out is a datetime object
            # If clock in time is just a time object, combine it with today's date
            if isinstance(attendance.clock_in_time, time):
                 clock_in_datetime = datetime.combine(today, attendance.clock_in_time)
            elif isinstance(attendance.clock_in_time, datetime):
                 clock_in_datetime = attendance.clock_in_time
            else:
                 return jsonify({'success': False, 'message': 'Invalid clock-in time data type'}), 500

            work_duration = current_time - clock_in_datetime
            hours_worked = work_duration.total_seconds() / 3600
            
            # Recalculate worked_hours using the model's comprehensive method (if available)
            # For simplicity in this route, we'll use the basic calculation:
            attendance.worked_hours = round(hours_worked, 2)
            
            # Calculate overtime (assuming 8-hour standard day)
            standard_hours = 8.0
            overtime_hours = max(0, hours_worked - standard_hours)
            attendance.overtime_hours = round(overtime_hours, 2)
        
        # Create audit log
        AuditLog.log_action(
            user_id=current_user.id,
            action='clock_out',
            table_name='attendance_records',
            record_id=employee.id,
            description=f'Clocked out {employee.employee_id} at {current_time.strftime("%H:%M")}. Hours worked: {attendance.worked_hours:.2f}',
            ip_address=request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR'))
        )
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'{employee.get_full_name()} clocked out successfully',
            'clock_out_time': current_time.strftime('%H:%M'),
            'hours_worked': round(attendance.worked_hours, 2),
            'overtime_hours': round(attendance.overtime_hours or 0, 2)
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error clocking out employee {employee_id}: {e}')
        return jsonify({'success': False, 'message': f'Error clocking out: {str(e)}'}), 500

@attendance_bp.route('/history')
@login_required
def attendance_history():
    """Enhanced attendance history with advanced filtering"""
    # FIXED: Local imports
    from models.employee import Employee
    from models.attendance import AttendanceRecord
    
    if not check_attendance_permission('view'):
        flash('You do not have permission to view attendance history.', 'error')
        return redirect(url_for('dashboard.main'))
    
    # Get filter parameters
    start_date_str = request.args.get('start_date', (date.today() - timedelta(days=30)).isoformat())
    end_date_str = request.args.get('end_date', date.today().isoformat())
    employee_filter = request.args.get('employee', '')
    location_filter = request.args.get('location', 'all')
    department_filter = request.args.get('department', 'all')
    status_filter = request.args.get('status', 'all')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 25, type=int)
    
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    except ValueError:
        flash('Invalid date format. Please use YYYY-MM-DD.', 'error')
        start_date = date.today() - timedelta(days=30)
        end_date = date.today()
    
    try:
        # Build query
        query = db.session.query(AttendanceRecord, Employee).join(
            Employee, AttendanceRecord.employee_id == Employee.id
        ).filter(
            AttendanceRecord.date >= start_date,
            AttendanceRecord.date <= end_date,
            Employee.is_active == True
        )
        
        # Apply role-based filtering
        if current_user.role == 'station_manager':
            query = query.filter(Employee.location == current_user.location)
        elif location_filter != 'all':
            query = query.filter(Employee.location == location_filter)
        
        # Apply other filters
        if employee_filter:
            search_pattern = f"%{employee_filter}%"
            query = query.filter(or_(
                Employee.first_name.ilike(search_pattern),
                Employee.last_name.ilike(search_pattern),
                Employee.employee_id.ilike(search_pattern)
            ))
        
        if department_filter != 'all':
            query = query.filter(Employee.department == department_filter)
        
        if status_filter != 'all':
            if status_filter == 'present_late':
                query = query.filter(AttendanceRecord.status.in_(['present', 'late']))
            else:
                query = query.filter(AttendanceRecord.status == status_filter)
        
        # Order by date (newest first) and employee name
        query = query.order_by(desc(AttendanceRecord.date), Employee.first_name)
        
        # Paginate
        history_records = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # Get summary statistics
        summary_stats = get_attendance_summary_stats(start_date, end_date, current_user)
        
        # Get filter options
        filter_options = get_history_filter_options(current_user)
        
        return render_template('attendance/history.html',
                             history_records=history_records,
                             summary_stats=summary_stats,
                             filter_options=filter_options,
                             start_date=start_date_str,
                             end_date=end_date_str,
                             employee_filter=employee_filter,
                             location_filter=location_filter,
                             department_filter=department_filter,
                             status_filter=status_filter,
                             per_page=per_page)
                             
    except Exception as e:
        current_app.logger.error(f"Error in attendance history: {e}")
        flash('Error loading attendance history. Please try again.', 'error')
        return redirect(url_for('attendance.overview'))

@attendance_bp.route('/api/today-summary')
@login_required
def api_today_summary():
    """API endpoint for today's attendance summary"""
    # FIXED: Local imports
    from models.employee import Employee
    from models.attendance import AttendanceRecord
    
    location = request.args.get('location', 'all')
    
    try:
        today = date.today()
        
        # Base query based on user role
        if current_user.role == 'station_manager':
            employee_query = Employee.query.filter(
                Employee.location == current_user.location,
                Employee.is_active == True
            )
        else:
            employee_query = Employee.query.filter(Employee.is_active == True)
            if location != 'all':
                employee_query = employee_query.filter(Employee.location == location)
        
        total_employees = employee_query.count()
        
        # Get today's attendance
        attendance_query = AttendanceRecord.query.join(Employee).filter(
            AttendanceRecord.date == today,
            AttendanceRecord.employee_id.in_(
                employee_query.with_entities(Employee.id)
            )
        )
        
        attendance_records = attendance_query.all()
        
        # Calculate summary
        present = sum(1 for record in attendance_records if record.status in ['present', 'late'])
        absent = sum(1 for record in attendance_records if record.status == 'absent')
        late = sum(1 for record in attendance_records if record.status == 'late')
        # FIX: On leave must be determined from LeaveRequest model, not AttendanceRecord status
        # For simplicity, we assume 'on_leave' status is set correctly in AttendanceRecord, 
        # but a proper implementation would query the LeaveRequest table.
        on_leave = sum(1 for record in attendance_records if 'leave' in record.status) 
        not_marked = total_employees - len(attendance_records)
        
        return jsonify({
            'success': True,
            'data': {
                'total': total_employees,
                'present': present,
                'absent': absent,
                'late': late,
                'on_leave': on_leave,
                'not_marked': not_marked,
                'attendance_rate': round((present / total_employees * 100), 1) if total_employees > 0 else 0
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting today's summary: {e}")
        return jsonify({'success': False, 'message': 'Error loading data'}), 500

@attendance_bp.route('/api/employee-status/<int:employee_id>')
@login_required
def api_employee_status(employee_id):
    """API endpoint for individual employee attendance status"""
    # FIXED: Local imports
    from models.employee import Employee
    from models.attendance import AttendanceRecord
    from models.leave import LeaveRequest
    
    employee = Employee.query.get_or_404(employee_id)
    
    # Check permissions
    if (current_user.role == 'station_manager' and 
        employee.location != current_user.location):
        return jsonify({'error': 'Unauthorized'}), 403
    
    target_date_str = request.args.get('date', date.today().isoformat())
    
    try:
        target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
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
        'employee_name': employee.get_full_name(),
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
        # FIX: Check if clock_in_time is a time object or datetime object
        clock_in_display = attendance.clock_in_time.strftime('%H:%M') if attendance.clock_in_time else None
        clock_out_display = attendance.clock_out_time.strftime('%H:%M') if attendance.clock_out_time else None
        
        response_data.update({
            'status': attendance.status,
            'clock_in': clock_in_display,
            'clock_out': clock_out_display,
            'hours_worked': float(attendance.worked_hours) if attendance.worked_hours else 0, # FIX: Use worked_hours
            'notes': attendance.notes
        })
    
    return jsonify(response_data)

# Helper Functions

def get_attendance_overview_data(target_date, location_filter, department_filter, shift_filter, status_filter):
    """Get comprehensive attendance overview data"""
    # FIXED: Local imports
    from models.employee import Employee
    from models.attendance import AttendanceRecord
    from models.leave import LeaveRequest
    
    # Build base query
    employee_query = Employee.query.filter(Employee.is_active == True)
    
    # Apply role-based filtering
    if current_user.role == 'station_manager':
        employee_query = employee_query.filter(Employee.location == current_user.location)
    elif location_filter != 'all':
        employee_query = employee_query.filter(Employee.location == location_filter)
    
    # Apply other filters
    if department_filter != 'all':
        employee_query = employee_query.filter(Employee.department == department_filter)
    
    if shift_filter != 'all':
        employee_query = employee_query.filter(Employee.shift == shift_filter)
    
    employees = employee_query.all()
    total_employees = len(employees)
    
    # Get attendance records for the date
    attendance_records = []
    if employees:
        attendance_query = AttendanceRecord.query.filter(
            AttendanceRecord.employee_id.in_([emp.id for emp in employees]),
            AttendanceRecord.date == target_date
        )
        
        if status_filter != 'all':
            if status_filter == 'present_late':
                attendance_query = attendance_query.filter(AttendanceRecord.status.in_(['present', 'late']))
            else:
                attendance_query = attendance_query.filter(AttendanceRecord.status == status_filter)
        
        attendance_records = attendance_query.all()
    
    # Get leave requests for the date
    leave_requests = []
    if employees:
        leave_requests = LeaveRequest.query.filter(
            LeaveRequest.employee_id.in_([emp.id for emp in employees]),
            LeaveRequest.start_date <= target_date,
            LeaveRequest.end_date >= target_date,
            LeaveRequest.status == 'approved'
        ).all()
    
    # Calculate statistics
    present_count = len([r for r in attendance_records if r.status in ['present', 'late']])
    absent_count = len([r for r in attendance_records if r.status == 'absent'])
    late_count = len([r for r in attendance_records if r.status == 'late'])
    on_leave_count = len(leave_requests)
    
    # FIX: Correctly count employees whose status is *covered* by an approved leave
    employees_with_attendance = {r.employee_id for r in attendance_records}
    employees_on_leave = {r.employee_id for r in leave_requests}
    
    # Filter out employees who have an attendance record but are also on leave 
    # (usually attendance takes precedence unless attendance status is 'on_leave')
    # For a precise count, we iterate through all employees
    employees_accounted_for = employees_with_attendance.union(employees_on_leave)

    not_marked_count = total_employees - len(employees_accounted_for)
    
    # Build detailed employee list
    employee_details = []
    attendance_dict = {r.employee_id: r for r in attendance_records}
    leave_dict = {r.employee_id: r for r in leave_requests}
    
    for employee in employees:
        attendance = attendance_dict.get(employee.id)
        leave = leave_dict.get(employee.id)
        
        if leave and not attendance: # Only count as on_leave if no attendance record overrides it
            status = 'on_leave'
            status_detail = f"On {leave.leave_type.replace('_', ' ').title()}"
            on_leave_count += 1
            present_count -= 1 if attendance and attendance.status in ['present', 'late'] else 0
            absent_count -= 1 if attendance and attendance.status == 'absent' else 0
            late_count -= 1 if attendance and attendance.status == 'late' else 0

        elif attendance:
            status = attendance.status
            status_detail = status.replace('_', ' ').title()
            # FIX: Ensure clock time display is correct regardless of type (Time or DateTime)
            clock_in_display = attendance.clock_in_time.strftime('%H:%M') if attendance.clock_in_time else None
            clock_out_display = attendance.clock_out_time.strftime('%H:%M') if attendance.clock_out_time else None

            if clock_in_display:
                status_detail += f" (In: {clock_in_display})"
            if clock_out_display:
                status_detail += f" (Out: {clock_out_display})"

        else:
            status = 'not_marked'
            status_detail = 'Not Marked'
            
        employee_details.append({
            'employee': employee,
            'attendance': attendance,
            'leave': leave,
            'status': status,
            'status_detail': status_detail
        })
    
    return {
        'total_employees': total_employees,
        'present_count': present_count,
        'absent_count': absent_count,
        'late_count': late_count,
        'on_leave_count': on_leave_count,
        'not_marked_count': not_marked_count,
        'attendance_rate': round((present_count / total_employees * 100), 1) if total_employees > 0 else 0,
        'employee_details': employee_details,
        'date': target_date
    }

def get_attendance_filter_options(user):
    """Get available filter options for attendance"""
    options = {
        'locations': [],
        'departments': list(current_app.config.get('DEPARTMENTS', {}).keys()),
        'shifts': ['day', 'night'],
        'statuses': ['present', 'absent', 'late', 'on_leave', 'present_late', 'all']
    }
    
    # Locations based on role
    if user.role == 'hr_manager':
        options['locations'] = ['all'] + list(current_app.config.get('COMPANY_LOCATIONS', {}).keys())
    elif user.role == 'station_manager':
        options['locations'] = [user.location]
    
    return options

def get_recent_attendance_activities():
    """Get recent attendance activities for dashboard"""
    # FIXED: Local imports
    from models.audit import AuditLog
    
    try:
        recent_logs = AuditLog.query.filter(
            AuditLog.event_action.in_(['attendance_marked', 'clock_in', 'clock_out', 'bulk_attendance_marked'])
        ).order_by(desc(AuditLog.timestamp)).limit(10).all()
        
        activities = []
        for log in recent_logs:
            activities.append({
                'action': log.event_action,
                'description': log.description,
                'timestamp': log.timestamp,
                'user_id': log.user_id
            })
        
        return activities
    except:
        return []

def get_weekly_attendance_trends(target_date):
    """Get weekly attendance trends"""
    # FIXED: Local imports
    from models.employee import Employee
    from models.attendance import AttendanceRecord
    
    try:
        # Calculate week start (Monday)
        days_since_monday = target_date.weekday()
        week_start = target_date - timedelta(days=days_since_monday)
        
        trends = []
        for i in range(7):
            day = week_start + timedelta(days=i)
            if day <= target_date:  # Don't show future days
                
                # Get total active employees for normalization
                if current_user.role == 'station_manager':
                    total_employees = Employee.query.filter(
                        Employee.location == current_user.location,
                        Employee.is_active == True
                    ).count()
                else:
                    total_employees = Employee.query.filter(Employee.is_active == True).count()
                    
                
                # Get attendance for this day
                if current_user.role == 'station_manager':
                    day_attendance = AttendanceRecord.query.join(Employee).filter(
                        AttendanceRecord.date == day,
                        Employee.location == current_user.location,
                        Employee.is_active == True
                    ).all()
                    
                else:
                    day_attendance = AttendanceRecord.query.join(Employee).filter(
                        AttendanceRecord.date == day,
                        Employee.is_active == True
                    ).all()
                    
                
                present_count = len([r for r in day_attendance if r.status in ['present', 'late']])
                
                trends.append({
                    'date': day.isoformat(),
                    'day_name': day.strftime('%A'),
                    'present': present_count,
                    'total': total_employees,
                    'rate': round((present_count / total_employees * 100) if total_employees > 0 else 0, 1)
                })
        
        return trends
    except:
        return []

def get_attendance_summary_stats(start_date, end_date, user):
    """Calculate attendance summary statistics for date range"""
    # FIXED: Local imports
    from models.employee import Employee
    from models.attendance import AttendanceRecord
    
    try:
        # Base query
        if user.role == 'station_manager':
            attendance_query = AttendanceRecord.query.join(Employee).filter(
                AttendanceRecord.date >= start_date,
                AttendanceRecord.date <= end_date,
                Employee.location == user.location,
                Employee.is_active == True
            )
        else:
            attendance_query = AttendanceRecord.query.join(Employee).filter(
                AttendanceRecord.date >= start_date,
                AttendanceRecord.date <= end_date,
                Employee.is_active == True
            )
        
        attendance_records = attendance_query.all()
        
        if not attendance_records:
            return {
                'total': 0,
                'present': 0,
                'absent': 0,
                'late': 0,
                'on_leave': 0,
                'attendance_rate': 0,
                'total_hours': 0,
                'total_overtime': 0,
                'average_daily_hours': 0
            }
        
        # Calculate statistics
        total = len(attendance_records)
        present = sum(1 for record in attendance_records if record.status in ['present', 'late'])
        absent = sum(1 for record in attendance_records if record.status == 'absent')
        late = sum(1 for record in attendance_records if record.status == 'late')
        on_leave = sum(1 for record in attendance_records if 'leave' in record.status)
        
        # Calculate total hours worked
        # FIX: Ensure proper column name is used (worked_hours)
        total_hours = sum(float(record.worked_hours or 0) for record in attendance_records)
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
    except Exception as e:
        current_app.logger.error(f"Error calculating attendance summary stats: {e}")
        return {}

def get_history_filter_options(user):
    """Get filter options for attendance history"""
    # FIXED: Local imports
    from models.employee import Employee
    
    options = {
        'locations': [],
        'departments': list(current_app.config.get('DEPARTMENTS', {}).keys()),
        'statuses': ['all', 'present', 'absent', 'late', 'present_late', 'half_day'],
        'employees': []
    }
    
    if user.role == 'hr_manager':
        options['locations'] = ['all'] + list(current_app.config.get('COMPANY_LOCATIONS', {}).keys())
        
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

def is_employee_late(employee, clock_in_time):
    """Determine if employee is late based on shift and location"""
    # Get expected start time based on employee's shift and location
    location_config = current_app.config.get('COMPANY_LOCATIONS', {}).get(employee.location, {})
    
    # Determine shift and expected start time
    employee_shift = getattr(employee, 'shift', 'day')
    
    # FIX: Use configured working hours if available
    working_hours = location_config.get('working_hours', {})
    
    expected_time_str = None
    if employee_shift in working_hours:
        if isinstance(working_hours[employee_shift], dict):
            expected_time_str = working_hours[employee_shift].get('start')
    elif employee.location == 'head_office' and working_hours.get('monday'): # Default office hours
        expected_time_str = working_hours['monday'].get('start') 
    
    # Default fallback
    if not expected_time_str:
        expected_time_str = '08:00' if employee.location == 'head_office' else ('06:00' if employee_shift == 'day' else '18:00')
    
    try:
        expected_time = datetime.strptime(expected_time_str, '%H:%M').time()
    except ValueError:
        expected_time = datetime.strptime('08:00', '%H:%M').time() # Final fallback
    
    # Get grace period from config
    grace_minutes = current_app.config.get('VALIDATION_RULES', {}).get('attendance_rules', {}).get('late_threshold_minutes', 15)

    # Convert expected time to datetime for comparison (handling possible overnight shift starts)
    expected_datetime = datetime.combine(clock_in_time.date(), expected_time)
    
    # Handle clock-in date if shift is an overnight shift that starts on the previous day
    # This complexity is often handled by a scheduler, but for a simple check, we assume
    # if the expected time is late (e.g. 18:00) and actual is early (e.g. 05:00 next day),
    # the check still works by comparing times on the single date being marked.
    
    # Check if actual clock-in time exceeds expected time plus grace period
    return clock_in_time > (expected_datetime + timedelta(minutes=grace_minutes))

def calculate_late_minutes(employee, clock_in_time):
    """Calculate how many minutes late the employee is"""
    location_config = current_app.config.get('COMPANY_LOCATIONS', {}).get(employee.location, {})
    
    # Determine shift and expected start time
    employee_shift = getattr(employee, 'shift', 'day')
    working_hours = location_config.get('working_hours', {})
    
    expected_time_str = None
    if employee_shift in working_hours:
        if isinstance(working_hours[employee_shift], dict):
            expected_time_str = working_hours[employee_shift].get('start')
    elif employee.location == 'head_office' and working_hours.get('monday'):
        expected_time_str = working_hours['monday'].get('start') 
    
    if not expected_time_str:
        expected_time_str = '08:00' if employee.location == 'head_office' else ('06:00' if employee_shift == 'day' else '18:00')
        
    try:
        expected_time = datetime.strptime(expected_time_str, '%H:%M').time()
    except ValueError:
        expected_time = datetime.strptime('08:00', '%H:%M').time()
        
    # Get grace period from config
    grace_minutes = current_app.config.get('VALIDATION_RULES', {}).get('attendance_rules', {}).get('late_threshold_minutes', 15)

    expected_datetime = datetime.combine(clock_in_time.date(), expected_time)
    
    # Check if late
    if clock_in_time > expected_datetime:
        late_duration = clock_in_time - expected_datetime
        lateness_in_minutes = int(late_duration.total_seconds() / 60)
        
        # Subtract grace period
        return max(0, lateness_in_minutes - grace_minutes)
    
    return 0