"""
Dashboard routes for Sakina Gas Attendance System
Main overview, attendance statistics, and real-time data
"""
from flask import Blueprint, render_template, redirect, url_for, request, jsonify
from flask_login import login_required, current_user
from models import db, Employee, AttendanceRecord, LeaveRequest, Holiday
from datetime import date, datetime, timedelta
from sqlalchemy import and_, func, select

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
@dashboard_bp.route('/')  # Main dashboard route
@login_required
def main():
    """Main dashboard with attendance overview"""
    target_date = date.today()
    
    # Get attendance overview for today
    attendance_overview = get_attendance_overview(target_date)
    
    # Get recent leave requests for user's scope
    if current_user.role == 'station_manager':
        # Station manager sees their location's leave requests
        recent_leaves = db.session.execute(
            select(LeaveRequest)
            .join(Employee)
            .where(
                Employee.location == current_user.location,
                LeaveRequest.created_at >= datetime.utcnow() - timedelta(days=7)
            )
            .order_by(LeaveRequest.created_at.desc())
            .limit(5)
        ).scalars().all()
    else:
        # HR manager sees all recent leave requests
        recent_leaves = db.session.execute(
            select(LeaveRequest)
            .where(LeaveRequest.created_at >= datetime.utcnow() - timedelta(days=7))
            .order_by(LeaveRequest.created_at.desc())
            .limit(5)
        ).scalars().all()
    
    # Get upcoming holidays
    upcoming_holidays = db.session.execute(
        select(Holiday)
        .where(
            Holiday.date >= target_date,
            Holiday.is_active == True
        )
        .order_by(Holiday.date)
        .limit(3)
    ).scalars().all()
    
    # Calculate summary statistics
    stats = calculate_dashboard_stats(target_date)
    
    return render_template('dashboard/main.html',
                         attendance_overview=attendance_overview,
                         recent_leaves=recent_leaves,
                         upcoming_holidays=upcoming_holidays,
                         stats=stats,
                         target_date=target_date)

@dashboard_bp.route('/attendance-details/<location>')
@dashboard_bp.route('/attendance-details/<location>/<shift>')
@login_required
def attendance_details(location, shift=None):
    """Detailed attendance view for a specific location/shift"""
    target_date_str = request.args.get('date', date.today().isoformat())
    target_date = date.fromisoformat(target_date_str)
    
    # Check permissions
    if current_user.role == 'station_manager' and location != current_user.location:
        flash('Access denied. You can only view your station\'s data.', 'error')
        return redirect(url_for('dashboard.main'))
    
    # Get employees for this location/shift
    employee_query = select(Employee).where(
        Employee.location == location,
        Employee.is_active == True
    )
    
    if shift:
        employee_query = employee_query.where(Employee.shift == shift)
    
    employees = db.session.execute(
        employee_query.order_by(Employee.first_name, Employee.last_name)
    ).scalars().all()
    
    # Get attendance records for these employees on target date
    attendance_data = []
    for employee in employees:
        # Get attendance record
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
        
        attendance_data.append({
            'employee': employee,
            'attendance': attendance,
            'leave_request': leave_request
        })
    
    return render_template('dashboard/attendance_details.html',
                         attendance_data=attendance_data,
                         location=location,
                         shift=shift,
                         target_date=target_date)

@dashboard_bp.route('/api/attendance-overview')
@login_required
def api_attendance_overview():
    """API endpoint for real-time attendance overview"""
    target_date_str = request.args.get('date', date.today().isoformat())
    target_date = date.fromisoformat(target_date_str)
    
    overview = get_attendance_overview(target_date)
    
    return jsonify({
        'date': target_date.isoformat(),
        'overview': overview,
        'timestamp': datetime.utcnow().isoformat()
    })

def get_attendance_overview(target_date):
    """Get attendance overview for all locations and shifts"""
    overview = {}
    
    # Define locations and their shifts
    locations = {
        'head_office': {
            'name': 'Head Office',
            'shifts': [None],  # No shifts for head office
            'color': '#1B4F72'
        },
        'dandora': {
            'name': 'Dandora Station',
            'shifts': ['day', 'night'],
            'color': '#2E86AB'
        },
        'tassia': {
            'name': 'Tassia Station', 
            'shifts': ['day', 'night'],
            'color': '#28A745'
        },
        'kiambu': {
            'name': 'Kiambu Station',
            'shifts': ['day', 'night'],
            'color': '#FD7E14'
        }
    }
    
    for location_key, location_info in locations.items():
        # Skip if station manager doesn't have access
        if current_user.role == 'station_manager' and location_key != current_user.location:
            continue
            
        location_data = {
            'name': location_info['name'],
            'color': location_info['color'],
            'shifts': {},
            'total_employees': 0,
            'total_present': 0,
            'total_absent': 0,
            'total_on_leave': 0
        }
        
        if location_info['shifts'] == [None]:
            # Head office - no shifts
            shift_data = get_shift_attendance(location_key, None, target_date)
            location_data.update(shift_data)
        else:
            # Stations with day/night shifts
            for shift in location_info['shifts']:
                shift_data = get_shift_attendance(location_key, shift, target_date)
                location_data['shifts'][shift] = shift_data
                
                # Add to totals
                location_data['total_employees'] += shift_data['total_employees']
                location_data['total_present'] += shift_data['present']
                location_data['total_absent'] += shift_data['absent']
                location_data['total_on_leave'] += shift_data['on_leave']
        
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
    late = 0
    
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
            if attendance.status == 'late':
                late += 1
        else:
            absent += 1
    
    return {
        'total_employees': total_employees,
        'present': present,
        'absent': absent,
        'on_leave': on_leave,
        'late': late,
        'attendance_rate': round((present / total_employees * 100) if total_employees > 0 else 0, 1)
    }

def calculate_dashboard_stats(target_date):
    """Calculate summary statistics for dashboard"""
    # Get total employees based on user role
    if current_user.role == 'station_manager':
        total_employees = db.session.execute(
            select(func.count(Employee.id)).where(
                Employee.location == current_user.location,
                Employee.is_active == True
            )
        ).scalar()
    else:
        total_employees = db.session.execute(
            select(func.count(Employee.id)).where(Employee.is_active == True)
        ).scalar()
    
    # Get pending leave requests count
    if current_user.role == 'station_manager':
        pending_leaves = db.session.execute(
            select(func.count(LeaveRequest.id))
            .join(Employee)
            .where(
                Employee.location == current_user.location,
                LeaveRequest.status == 'pending'
            )
        ).scalar()
    else:
        pending_leaves = db.session.execute(
            select(func.count(LeaveRequest.id)).where(LeaveRequest.status == 'pending')
        ).scalar()
    
    # Get today's attendance rate
    if current_user.role == 'station_manager':
        location_overview = get_shift_attendance(current_user.location, None, target_date)
        if current_user.location in ['dandora', 'tassia', 'kiambu']:
            # For stations, get combined day/night shift data
            day_data = get_shift_attendance(current_user.location, 'day', target_date)
            night_data = get_shift_attendance(current_user.location, 'night', target_date)
            today_attendance_rate = round(
                ((day_data['present'] + night_data['present']) / 
                 (day_data['total_employees'] + night_data['total_employees']) * 100) 
                if (day_data['total_employees'] + night_data['total_employees']) > 0 else 0, 1
            )
        else:
            today_attendance_rate = location_overview['attendance_rate']
    else:
        # HR manager - get overall attendance rate
        overview = get_attendance_overview(target_date)
        total_present = sum(loc['total_present'] for loc in overview.values())
        total_emps = sum(loc['total_employees'] for loc in overview.values())
        today_attendance_rate = round((total_present / total_emps * 100) if total_emps > 0 else 0, 1)
    
    # Get this week's average attendance
    week_start = target_date - timedelta(days=target_date.weekday())
    weekly_rates = []
    for i in range(7):
        check_date = week_start + timedelta(days=i)
        if check_date <= target_date:  # Don't calculate future dates
            daily_overview = get_attendance_overview(check_date)
            daily_present = sum(loc['total_present'] for loc in daily_overview.values())
            daily_total = sum(loc['total_employees'] for loc in daily_overview.values())
            if daily_total > 0:
                weekly_rates.append(daily_present / daily_total * 100)
    
    week_avg_attendance = round(sum(weekly_rates) / len(weekly_rates), 1) if weekly_rates else 0
    
    return {
        'total_employees': total_employees,
        'pending_leaves': pending_leaves,
        'today_attendance_rate': today_attendance_rate,
        'week_avg_attendance': week_avg_attendance
    }