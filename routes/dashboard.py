"""
Dashboard routes for Sakina Gas Attendance System
"""
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from models import db, Employee, AttendanceRecord, LeaveRequest
from datetime import date, datetime
from config import Config
from sqlalchemy import func, and_

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
    employee_query = Employee.query.filter_by(location=location, is_active=True)
    
    if shift:
        employee_query = employee_query.filter_by(shift=shift)
    
    employees = employee_query.all()
    total_employees = len(employees)
    
    present = 0
    absent = 0
    on_leave = 0
    
    for employee in employees:
        # Check if employee has attendance record for today
        attendance = AttendanceRecord.query.filter_by(
            employee_id=employee.id,
            date=target_date
        ).first()
        
        # Check if employee is on approved leave
        leave_request = LeaveRequest.query.filter(
            and_(
                LeaveRequest.employee_id == employee.id,
                LeaveRequest.start_date <= target_date,
                LeaveRequest.end_date >= target_date,
                LeaveRequest.status == 'approved'
            )
        ).first()
        
        if leave_request:
            on_leave += 1
        elif attendance and attendance.status == 'present':
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
    employee_query = Employee.query.filter_by(location=location, is_active=True)
    if shift:
        employee_query = employee_query.filter_by(shift=shift)
    
    employees = employee_query.all()
    
    # Get detailed attendance information
    attendance_details = []
    for employee in employees:
        # Get attendance record for today
        attendance = AttendanceRecord.query.filter_by(
            employee_id=employee.id,
            date=today
        ).first()
        
        # Check for approved leave
        leave_request = LeaveRequest.query.filter(
            and_(
                LeaveRequest.employee_id == employee.id,
                LeaveRequest.start_date <= today,
                LeaveRequest.end_date >= today,
                LeaveRequest.status == 'approved'
            )
        ).first()
        
        status = 'absent'
        notes = ''
        
        if leave_request:
            status = 'on_leave'
            notes = f"{leave_request.leave_type.replace('_', ' ').title()}: {leave_request.reason}"
        elif attendance:
            status = attendance.status
            notes = attendance.notes or ''
        
        employee_data = {
            'employee': employee,
            'status': status,
            'notes': notes,
            'clock_in': attendance.clock_in if attendance else None,
            'clock_out': attendance.clock_out if attendance else None
        }
        
        # Apply filter
        if filter_status == 'all' or status == filter_status:
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
