"""
Attendance management routes for Sakina Gas Attendance System
UPDATED: Fixed SQLAlchemy 2.0 deprecation warnings + Enhanced timing logic
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from models import db, Employee, AttendanceRecord, User
from datetime import date, datetime, time, timedelta
from sqlalchemy import select
from config import Config
import pytz

attendance_bp = Blueprint('attendance', __name__)

# Kenyan timezone
NAIROBI_TZ = pytz.timezone('Africa/Nairobi')

def get_nairobi_time():
    """Get current time in Nairobi timezone"""
    return datetime.now(NAIROBI_TZ)

def check_late_status(employee, clock_in_time):
    """Check if employee is late based on location and shift"""
    if employee.location == 'head_office':
        # Head office: 9:00 AM start, 30min grace period
        expected_time = time(9, 0)  # 9:00 AM
        grace_time = time(9, 30)    # 9:30 AM
    else:
        # Station shifts
        if employee.shift == 'day':
            expected_time = time(6, 0)   # 6:00 AM
            grace_time = time(6, 30)     # 6:30 AM
        else:  # night shift
            expected_time = time(18, 0)  # 6:00 PM
            grace_time = time(18, 30)    # 6:30 PM
    
    actual_time = clock_in_time.time()
    
    if actual_time <= grace_time:
        return 'present'
    else:
        return 'late'

def get_auto_clock_out_time(employee, clock_in_date):
    """Get automatic clock out time based on employee location and shift"""
    nairobi_tz = pytz.timezone('Africa/Nairobi')
    
    if employee.location == 'head_office':
        # Head office: 5:00 PM
        clock_out = datetime.combine(clock_in_date, time(17, 0))
        return nairobi_tz.localize(clock_out)
    else:
        # Station shifts
        if employee.shift == 'day':
            clock_out = datetime.combine(clock_in_date, time(18, 0))  # 6:00 PM
            return nairobi_tz.localize(clock_out)
        else:  # night shift
            # Night shift ends next day at 6:00 AM
            next_day = clock_in_date + timedelta(days=1)
            clock_out = datetime.combine(next_day, time(6, 0))
            return nairobi_tz.localize(clock_out)

@attendance_bp.route('/mark', methods=['GET', 'POST'])
@login_required
def mark_attendance():
    """Mark attendance for employees with enhanced timing logic"""
    if request.method == 'POST':
        employee_id = request.form['employee_id']
        status = request.form['status']
        notes = request.form.get('notes', '')
        manual_clock_in_time = request.form.get('clock_in_time', '')
        
        # Get employee
        employee = db.session.execute(
            select(Employee).where(
                Employee.employee_id == employee_id, 
                Employee.is_active == True
            )
        ).scalar_one_or_none()
        
        if not employee:
            flash('Employee not found', 'error')
            return redirect(request.url)
        
        # Check if attendance already marked for today
        today = date.today()
        existing_record = db.session.execute(
            select(AttendanceRecord).where(
                AttendanceRecord.employee_id == employee.id,
                AttendanceRecord.date == today
            )
        ).scalar_one_or_none()
        
        nairobi_now = get_nairobi_time()
        
        # Handle manual clock in time if provided
        if manual_clock_in_time and status == 'present':
            try:
                # Parse the manual time
                manual_time = datetime.strptime(manual_clock_in_time, '%H:%M').time()
                # Combine with today's date and set Nairobi timezone
                naive_datetime = datetime.combine(today, manual_time)
                actual_clock_in = NAIROBI_TZ.localize(naive_datetime)
            except ValueError:
                actual_clock_in = nairobi_now
        else:
            actual_clock_in = nairobi_now if status == 'present' else None
        
        if existing_record:
            # Update existing record (allows editing)
            if status == 'present':
                existing_record.status = check_late_status(employee, actual_clock_in)
                existing_record.clock_in = actual_clock_in
                existing_record.clock_out = get_auto_clock_out_time(employee, today)
            else:
                existing_record.status = status
                # If changing from present to absent, clear clock times
                if status in ['absent', 'on_leave']:
                    existing_record.clock_in = None
                    existing_record.clock_out = None
            
            existing_record.notes = notes
            existing_record.marked_by = current_user.id
            existing_record.updated_at = nairobi_now
            flash(f'Attendance updated for {employee.full_name}', 'success')
        else:
            # Create new record
            actual_status = check_late_status(employee, actual_clock_in) if status == 'present' else status
            
            attendance = AttendanceRecord(
                employee_id=employee.id,
                date=today,
                status=actual_status,
                shift=employee.shift,
                notes=notes,
                marked_by=current_user.id,
                clock_in=actual_clock_in,
                clock_out=get_auto_clock_out_time(employee, today) if status == 'present' else None
            )
            db.session.add(attendance)
            flash(f'Attendance marked for {employee.full_name}', 'success')
        
        db.session.commit()
        return redirect(request.url)
    
    # GET request - show form with real employees
    if current_user.role == 'station_manager' and current_user.location:
        # Station managers see only their location employees
        employees = db.session.execute(
            select(Employee).where(
                Employee.location == current_user.location,
                Employee.is_active == True
            ).order_by(Employee.employee_id)
        ).scalars().all()
    else:
        # HR managers see all employees
        employees = db.session.execute(
            select(Employee).where(Employee.is_active == True)
            .order_by(Employee.location, Employee.employee_id)
        ).scalars().all()
    
    return render_template('attendance/mark.html', 
                         employees=employees, 
                         locations=Config.LOCATIONS,
                         current_time=get_nairobi_time())

@attendance_bp.route('/api/attendance-status/<employee_id>')
@login_required
def get_attendance_status(employee_id):
    """Get current attendance status for an employee"""
    employee = db.session.execute(
        select(Employee).where(
            Employee.employee_id == employee_id, 
            Employee.is_active == True
        )
    ).scalar_one_or_none()
    
    if not employee:
        return jsonify({'error': 'Employee not found'}), 404
    
    today = date.today()
    attendance = db.session.execute(
        select(AttendanceRecord).where(
            AttendanceRecord.employee_id == employee.id,
            AttendanceRecord.date == today
        )
    ).scalar_one_or_none()
    
    if attendance:
        # Get the user who marked the attendance
        marker = db.session.execute(
            select(User).where(User.id == attendance.marked_by)
        ).scalar_one_or_none()
        
        return jsonify({
            'has_attendance': True,
            'status': attendance.status,
            'clock_in': attendance.clock_in.isoformat() if attendance.clock_in else None,
            'clock_out': attendance.clock_out.isoformat() if attendance.clock_out else None,
            'notes': attendance.notes or '',
            'marked_by': marker.username if marker else 'System'
        })
    else:
        return jsonify({
            'has_attendance': False
        })

@attendance_bp.route('/clock/<action>/<employee_id>')
@login_required
def clock_action(action, employee_id):
    """Handle clock in actions only (clock out is automatic)"""
    if action != 'in':
        return jsonify({'success': False, 'message': 'Clock out is automatic - no manual clock out needed'})
        
    employee = db.session.execute(
        select(Employee).where(
            Employee.employee_id == employee_id, 
            Employee.is_active == True
        )
    ).scalar_one_or_none()
    
    if not employee:
        return jsonify({'success': False, 'message': 'Employee not found'})
    
    today = date.today()
    existing_record = db.session.execute(
        select(AttendanceRecord).where(
            AttendanceRecord.employee_id == employee.id,
            AttendanceRecord.date == today
        )
    ).scalar_one_or_none()
    
    nairobi_now = get_nairobi_time()
    
    if existing_record and existing_record.clock_in:
        return jsonify({'success': False, 'message': f'{employee.full_name} already clocked in today'})
    
    if not existing_record:
        attendance = AttendanceRecord(
            employee_id=employee.id,
            date=today,
            shift=employee.shift,
            marked_by=current_user.id
        )
        db.session.add(attendance)
    else:
        attendance = existing_record
    
    attendance.clock_in = nairobi_now
    attendance.status = check_late_status(employee, nairobi_now)
    attendance.clock_out = get_auto_clock_out_time(employee, today)
    attendance.updated_at = nairobi_now
    
    db.session.commit()
    
    status_msg = "on time" if attendance.status == 'present' else "LATE"
    expected_out = attendance.clock_out.strftime("%H:%M") if attendance.clock_out else "Unknown"
    
    message = f'{employee.full_name} clocked in at {nairobi_now.strftime("%H:%M")} ({status_msg}). Auto clock out: {expected_out}'
    
    return jsonify({'success': True, 'message': message})