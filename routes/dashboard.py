"""
Dashboard routes for Sakina Gas Attendance System
UPDATED: Fixed SQLAlchemy 2.0 deprecation warnings
"""
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from models import db, Employee, AttendanceRecord, LeaveRequest
from datetime import date, datetime
from config import Config
from sqlalchemy import func, and_, select

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
@login_required
def main():
    """Main dashboard with attendance overview"""
    today = date.today()
    
    # Get attendance overview for all locations
    attendance_overview = get_attendance_overview(today)
    
    return render_template('dashboard/main.html', 
                         attendance_overview=attendance_overview,
                         today=today,
                         locations=Config.LOCATIONS)

def get_attendance_overview(target_date):
    """Get attendance overview for all locations and shifts"""
    overview = {}
    
    for location_key, location_info in Config.LOCATIONS.items():
        location_data = {
            'name': location_info['name'],
            'total_employees': 0,
            'present': 0,
            'absent': 0,
            'on_leave': 0,
            'shifts': {}
        }
        
        if location_info['has_shifts']:
            # For stations with shifts
            for shift in location_info['shifts']:
                shift_data = get_shift_attendance(location_key, shift, target_date)
                location_data['shifts'][shift] = shift_data
                location_data['total_employees'] += shift_data['total_employees']
                location_data['present'] += shift_data['present']
                location_data['absent'] += shift_data['absent']
                location_data['on_leave'] += shift_data['on_leave']
        else:
            # For head office (no shifts)
            shift_data = get_shift_attendance(location_key, None, target_date)
            location_data.update(shift_data)
        
        overview[location_key] = location_data
    
    return overview

def get_shift_attendance(location, shift, target_date):
    """Get attendance data for a specific location and shift"""
    # Base query for employees in this location
    employee_query = select(Employee).where(
        Employee.location == location, 
        Employee.is_active == True
    )
    
    if shift:
        employee_query = employee_query.where(Employee.shift == shift)
    
    employees = db.session.execute(employee_query).scalars().all()
    total_employees = len(employees)
    
    present = 0
    absent = 0
    on_leave = 0
    
    for employee in employees:
        # Check if employee has attendance record for today
        attendance = db.session.execute(
            select(AttendanceRecord).where(
                AttendanceRecord.employee_id == employee.id,
                AttendanceRecord.date == target_date
            )
        ).scalar_one_or_none()
        
        # Check if employee is on approved leave
        leave_request = db.session.execute(
            select(LeaveRequest).where(
                and_(
                    LeaveRequest.employee_id == employee.id,
                    LeaveRequest.start_date <= target_date,
                    LeaveRequest.end_date >= target_date,
                    LeaveRequest.status == 'approved'
                )
            )
        ).scalar_one_or_none()
        
        if leave_request:
            on_leave += 1
        elif attendance and attendance.status in ['present', 'late']:
            present += 1
        else:
            absent += 1
    
    return {
        'total_employees': total_employees,
        'present': present,
        'absent': absent,
        'on_leave': on_leave
    }

@dashboard_bp.route('/attendance-details/<location>')
@dashboard_bp.route('/attendance-details/<location>/<shift>')
@login_required
def attendance_details(location, shift=None):
    """Detailed attendance view for a specific location/shift"""
    today = date.today()
    filter_status = request.args.get('filter', 'all')  # all, present, absent, on_leave
    
    # Get employees for this location/shift
    employee_query = select(Employee).where(
        Employee.location == location, 
        Employee.is_active == True
    )
    if shift:
        employee_query = employee_query.where(Employee.shift == shift)
    
    employees = db.session.execute(employee_query).scalars().all()
    
    # Get detailed attendance information
    attendance_details = []
    for employee in employees:
        # Get attendance record for today
        attendance = db.session.execute(
            select(AttendanceRecord).where(
                AttendanceRecord.employee_id == employee.id,
                AttendanceRecord.date == today
            )
        ).scalar_one_or_none()
        
        # Check for approved leave
        leave_request = db.session.execute(
            select(LeaveRequest).where(
                and_(
                    LeaveRequest.employee_id == employee.id,
                    LeaveRequest.start_date <= today,
                    LeaveRequest.end_date >= today,
                    LeaveRequest.status == 'approved'
                )
            )
        ).scalar_one_or_none()
        
        status = 'absent'
        notes = ''
        
        if leave_request:
            status = 'on_leave'
            notes = f"{leave_request.leave_type.replace('_', ' ').title()}: {leave_request.reason}"
        elif attendance:
            status = attendance.status
            notes = attendance.notes or ''
            # Include both 'present' and 'late' as present for filtering
            if attendance.status == 'late':
                status = 'present'  # For filtering purposes, late is still present
        
        employee_data = {
            'employee': employee,
            'status': status,
            'actual_status': attendance.status if attendance else 'absent',  # Keep original for display
            'notes': notes,
            'clock_in': attendance.clock_in if attendance else None,
            'clock_out': attendance.clock_out if attendance else None
        }
        
        # Apply filter - now includes both present and late employees under "present"
        if filter_status == 'all':
            attendance_details.append(employee_data)
        elif filter_status == 'present' and status in ['present']:
            attendance_details.append(employee_data)
        elif filter_status == 'absent' and status == 'absent':
            attendance_details.append(employee_data)
        elif filter_status == 'on_leave' and status == 'on_leave':
            attendance_details.append(employee_data)
    
    location_name = Config.LOCATIONS[location]['name']
    if shift:
        location_name += f" - {shift.title()} Shift"
    
    return render_template('dashboard/attendance_details.html',
                         attendance_details=attendance_details,
                         location=location,
                         location_name=location_name,
                         shift=shift,
                         today=today,
                         filter_status=filter_status)