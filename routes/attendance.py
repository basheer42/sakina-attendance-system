"""
Attendance management routes for Sakina Gas Attendance System
Mark attendance, view records, and manage attendance data
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from models import db, Employee, AttendanceRecord, LeaveRequest, AuditLog
from datetime import date, datetime, timedelta

attendance_bp = Blueprint('attendance', __name__)

@attendance_bp.route('/')
@attendance_bp.route('/mark')
@login_required
def mark_attendance():
    """Mark attendance for employees"""
    target_date = date.today()
    
    # Get employees based on user role
    if current_user.role == 'station_manager':
        employees = db.session.execute(
            db.select(Employee).where(
                Employee.location == current_user.location,
                Employee.is_active == True
            ).order_by(Employee.first_name, Employee.last_name)
        ).scalars().all()
    else:
        # HR manager can mark for any location
        location_filter = request.args.get('location', 'all')
        query = db.select(Employee).where(Employee.is_active == True)
        
        if location_filter != 'all':
            query = query.where(Employee.location == location_filter)
        
        employees = db.session.execute(
            query.order_by(Employee.location, Employee.first_name, Employee.last_name)
        ).scalars().all()
    
    # Get existing attendance records for today
    attendance_records = {}
    for employee in employees:
        attendance = db.session.execute(
            db.select(AttendanceRecord).where(
                AttendanceRecord.employee_id == employee.id,
                AttendanceRecord.date == target_date
            )
        ).scalar_one_or_none()
        
        attendance_records[employee.id] = attendance
    
    return render_template('attendance/mark.html',
                         employees=employees,
                         attendance_records=attendance_records,
                         target_date=target_date)

@attendance_bp.route('/mark-employee', methods=['POST'])
@login_required
def mark_employee_attendance():
    """Mark attendance for a specific employee"""
    data = request.get_json()
    employee_id = data.get('employee_id')
    status = data.get('status')  # present, absent, late
    notes = data.get('notes', '')
    target_date_str = data.get('date', date.today().isoformat())
    
    # Parse date
    try:
        target_date = date.fromisoformat(target_date_str)
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid date format'}), 400
    
    # Get employee
    employee = db.session.execute(
        db.select(Employee).where(Employee.id == employee_id, Employee.is_active == True)
    ).scalar_one_or_none()
    
    if not employee:
        return jsonify({'success': False, 'message': 'Employee not found'}), 404
    
    # Check permissions
    if current_user.role == 'station_manager' and employee.location != current_user.location:
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    # Check if attendance already exists
    existing_attendance = db.session.execute(
        db.select(AttendanceRecord).where(
            AttendanceRecord.employee_id == employee.id,
            AttendanceRecord.date == target_date
        )
    ).scalar_one_or_none()
    
    try:
        current_time = datetime.now()
        
        if existing_attendance:
            # Update existing record
            old_status = existing_attendance.status
            existing_attendance.status = status
            existing_attendance.notes = notes
            existing_attendance.marked_by = current_user.id
            existing_attendance.updated_at = current_time
            
            # Set clock in/out times based on status
            if status == 'present' or status == 'late':
                if not existing_attendance.clock_in:
                    existing_attendance.clock_in = current_time
            elif status == 'absent':
                existing_attendance.clock_in = None
                existing_attendance.clock_out = None
            
            action_details = f'Updated attendance for {employee.employee_id} from {old_status} to {status}'
        else:
            # Create new record
            attendance = AttendanceRecord(
                employee_id=employee.id,
                date=target_date,
                status=status,
                shift=employee.shift,
                notes=notes,
                marked_by=current_user.id,
                clock_in=current_time if status in ['present', 'late'] else None
            )
            
            db.session.add(attendance)
            action_details = f'Marked attendance for {employee.employee_id} as {status}'
        
        # Create audit log
        audit_log = AuditLog(
            user_id=current_user.id,
            action='mark_attendance',
            target_type='attendance',
            target_id=employee.id,
            details=action_details,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', '')[:255]
        )
        db.session.add(audit_log)
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'Attendance marked for {employee.full_name}',
            'employee_name': employee.full_name,
            'status': status
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Error marking attendance: {e}")
        return jsonify({'success': False, 'message': 'Error marking attendance'}), 500

@attendance_bp.route('/clock-out', methods=['POST'])
@login_required
def clock_out_employee():
    """Clock out an employee"""
    data = request.get_json()
    employee_id = data.get('employee_id')
    target_date_str = data.get('date', date.today().isoformat())
    
    # Parse date
    try:
        target_date = date.fromisoformat(target_date_str)
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid date format'}), 400
    
    # Get employee
    employee = db.session.execute(
        db.select(Employee).where(Employee.id == employee_id, Employee.is_active == True)
    ).scalar_one_or_none()
    
    if not employee:
        return jsonify({'success': False, 'message': 'Employee not found'}), 404
    
    # Check permissions
    if current_user.role == 'station_manager' and employee.location != current_user.location:
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    # Get attendance record
    attendance = db.session.execute(
        db.select(AttendanceRecord).where(
            AttendanceRecord.employee_id == employee.id,
            AttendanceRecord.date == target_date,
            AttendanceRecord.status.in_(['present', 'late'])
        )
    ).scalar_one_or_none()
    
    if not attendance:
        return jsonify({'success': False, 'message': 'No active attendance record found'}), 404
    
    if attendance.clock_out:
        return jsonify({'success': False, 'message': 'Employee already clocked out'}), 400
    
    try:
        current_time = datetime.now()
        attendance.clock_out = current_time
        attendance.updated_at = current_time
        
        # Create audit log
        audit_log = AuditLog(
            user_id=current_user.id,
            action='clock_out',
            target_type='attendance',
            target_id=employee.id,
            details=f'Clocked out {employee.employee_id} at {current_time.strftime("%H:%M")}',
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', '')[:255]
        )
        db.session.add(audit_log)
        
        db.session.commit()
        
        # Calculate hours worked
        hours_worked = attendance.hours_worked
        
        return jsonify({
            'success': True,
            'message': f'{employee.full_name} clocked out successfully',
            'clock_out_time': current_time.strftime('%H:%M'),
            'hours_worked': round(hours_worked, 2)
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Error clocking out: {e}")
        return jsonify({'success': False, 'message': 'Error clocking out'}), 500

@attendance_bp.route('/history')
@attendance_bp.route('/history/<employee_id>')
@login_required
def attendance_history(employee_id=None):
    """View attendance history"""
    # Date range filters
    start_date_str = request.args.get('start_date', (date.today() - timedelta(days=30)).isoformat())
    end_date_str = request.args.get('end_date', date.today().isoformat())
    
    try:
        start_date = date.fromisoformat(start_date_str)
        end_date = date.fromisoformat(end_date_str)
    except ValueError:
        flash('Invalid date format', 'error')
        start_date = date.today() - timedelta(days=30)
        end_date = date.today()
    
    if employee_id:
        # Single employee history
        employee = db.session.execute(
            db.select(Employee).where(Employee.employee_id == employee_id)
        ).scalar_one_or_none()
        
        if not employee:
            flash('Employee not found', 'error')
            return redirect(url_for('attendance.attendance_history'))
        
        # Check permissions
        if current_user.role == 'station_manager' and employee.location != current_user.location:
            flash('Access denied', 'error')
            return redirect(url_for('attendance.attendance_history'))
        
        # Get attendance records
        attendance_records = db.session.execute(
            db.select(AttendanceRecord).where(
                AttendanceRecord.employee_id == employee.id,
                AttendanceRecord.date >= start_date,
                AttendanceRecord.date <= end_date
            ).order_by(AttendanceRecord.date.desc())
        ).scalars().all()
        
        return render_template('attendance/employee_history.html',
                             employee=employee,
                             attendance_records=attendance_records,
                             start_date=start_date,
                             end_date=end_date)
    
    else:
        # All employees summary
        if current_user.role == 'station_manager':
            employees = db.session.execute(
                db.select(Employee).where(
                    Employee.location == current_user.location,
                    Employee.is_active == True
                ).order_by(Employee.first_name, Employee.last_name)
            ).scalars().all()
        else:
            location_filter = request.args.get('location', 'all')
            query = db.select(Employee).where(Employee.is_active == True)
            
            if location_filter != 'all':
                query = query.where(Employee.location == location_filter)
            
            employees = db.session.execute(
                query.order_by(Employee.location, Employee.first_name, Employee.last_name)
            ).scalars().all()
        
        # Calculate attendance summary for each employee
        employee_summaries = []
        for employee in employees:
            total_days = (end_date - start_date).days + 1
            
            # Get attendance records count
            attendance_count = db.session.execute(
                db.select(db.func.count(AttendanceRecord.id)).where(
                    AttendanceRecord.employee_id == employee.id,
                    AttendanceRecord.date >= start_date,
                    AttendanceRecord.date <= end_date,
                    AttendanceRecord.status.in_(['present', 'late'])
                )
            ).scalar()
            
            # Get leave days count
            leave_count = db.session.execute(
                db.select(db.func.count(AttendanceRecord.id)).where(
                    AttendanceRecord.employee_id == employee.id,
                    AttendanceRecord.date >= start_date,
                    AttendanceRecord.date <= end_date,
                    AttendanceRecord.status == 'on_leave'
                )
            ).scalar()
            
            attendance_rate = round((attendance_count / total_days * 100), 1) if total_days > 0 else 0
            
            employee_summaries.append({
                'employee': employee,
                'total_days': total_days,
                'present_days': attendance_count,
                'leave_days': leave_count,
                'absent_days': total_days - attendance_count - leave_count,
                'attendance_rate': attendance_rate
            })
        
        return render_template('attendance/history.html',
                             employee_summaries=employee_summaries,
                             start_date=start_date,
                             end_date=end_date)

@attendance_bp.route('/bulk-mark', methods=['GET', 'POST'])
@login_required
def bulk_mark_attendance():
    """Bulk mark attendance for multiple employees"""
    if request.method == 'POST':
        attendance_data = request.get_json()
        target_date_str = attendance_data.get('date', date.today().isoformat())
        employee_statuses = attendance_data.get('employees', [])
        
        # Parse date
        try:
            target_date = date.fromisoformat(target_date_str)
        except ValueError:
            return jsonify({'success': False, 'message': 'Invalid date format'}), 400
        
        success_count = 0
        error_count = 0
        
        try:
            for employee_data in employee_statuses:
                employee_id = employee_data.get('employee_id')
                status = employee_data.get('status')
                notes = employee_data.get('notes', '')
                
                # Get employee
                employee = db.session.execute(
                    db.select(Employee).where(Employee.id == employee_id, Employee.is_active == True)
                ).scalar_one_or_none()
                
                if not employee:
                    error_count += 1
                    continue
                
                # Check permissions
                if current_user.role == 'station_manager' and employee.location != current_user.location:
                    error_count += 1
                    continue
                
                # Check if attendance already exists
                existing_attendance = db.session.execute(
                    db.select(AttendanceRecord).where(
                        AttendanceRecord.employee_id == employee.id,
                        AttendanceRecord.date == target_date
                    )
                ).scalar_one_or_none()
                
                current_time = datetime.now()
                
                if existing_attendance:
                    # Update existing record
                    existing_attendance.status = status
                    existing_attendance.notes = notes
                    existing_attendance.marked_by = current_user.id
                    existing_attendance.updated_at = current_time
                    
                    if status == 'present' or status == 'late':
                        if not existing_attendance.clock_in:
                            existing_attendance.clock_in = current_time
                    elif status == 'absent':
                        existing_attendance.clock_in = None
                        existing_attendance.clock_out = None
                else:
                    # Create new record
                    attendance = AttendanceRecord(
                        employee_id=employee.id,
                        date=target_date,
                        status=status,
                        shift=employee.shift,
                        notes=notes,
                        marked_by=current_user.id,
                        clock_in=current_time if status in ['present', 'late'] else None
                    )
                    db.session.add(attendance)
                
                success_count += 1
            
            # Create audit log for bulk operation
            audit_log = AuditLog(
                user_id=current_user.id,
                action='bulk_mark_attendance',
                target_type='attendance',
                details=f'Bulk marked attendance for {success_count} employees on {target_date}',
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent', '')[:255]
            )
            db.session.add(audit_log)
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': f'Successfully marked attendance for {success_count} employees',
                'success_count': success_count,
                'error_count': error_count
            })
            
        except Exception as e:
            db.session.rollback()
            print(f"Error in bulk attendance marking: {e}")
            return jsonify({'success': False, 'message': 'Error marking attendance'}), 500
    
    # GET request - show bulk marking form
    target_date = date.today()
    
    # Get employees based on user role
    if current_user.role == 'station_manager':
        employees = db.session.execute(
            db.select(Employee).where(
                Employee.location == current_user.location,
                Employee.is_active == True
            ).order_by(Employee.first_name, Employee.last_name)
        ).scalars().all()
    else:
        employees = db.session.execute(
            db.select(Employee).where(Employee.is_active == True)
            .order_by(Employee.location, Employee.first_name, Employee.last_name)
        ).scalars().all()
    
    return render_template('attendance/bulk_mark.html',
                         employees=employees,
                         target_date=target_date)