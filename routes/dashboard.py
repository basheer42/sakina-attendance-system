"""
Sakina Gas Company - Dashboard Routes
Built from scratch with full complexity and advanced analytics
Version 3.0 - SQLAlchemy 2.0+ compatible with corrected syntax
FIXED: Models imported inside functions to prevent mapper conflicts
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, g, current_app
from flask_login import login_required, current_user
from sqlalchemy import func, and_, or_, case, text, distinct, desc, asc, extract
from sqlalchemy.orm import aliased
from datetime import date, datetime, timedelta, time
from collections import defaultdict, OrderedDict
import calendar
import json

# FIXED: Removed global model imports to prevent early model registration
from database import db
# NOTE: Models are now imported locally within functions for safety

# Create blueprint
dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@dashboard_bp.route('/main')
@login_required
def main():
    """Enhanced main dashboard with role-based routing"""
    # FIXED: Local imports
    from models.audit import AuditLog
    
    try:
        # Log dashboard access
        AuditLog.log_event( # FIX: Use log_event instead of log_action
            user_id=current_user.id,
            event_type='dashboard_access',
            description=f'User accessed main dashboard',
            ip_address=request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR'))
        )
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to log dashboard access: {e}")
    
    # Route users to appropriate dashboard based on role
    if current_user.role == 'hr_manager':
        return redirect(url_for('dashboard.hr_overview'))
    elif current_user.role == 'station_manager':
        return redirect(url_for('dashboard.station_overview'))
    # Removed finance_manager and admin_overview redirects for simplification/focus
    # For now, default to main template if no specific overview is ready
    
    return render_template('dashboard/main.html')

@dashboard_bp.route('/hr-overview')
@login_required
def hr_overview():
    """Comprehensive HR Manager dashboard with advanced analytics"""
    # FIXED: Local imports
    from models.employee import Employee
    from models.attendance import AttendanceRecord
    from models.leave import LeaveRequest
    from models.user import User
    # from models.holiday import Holiday # FIX: Commented out missing/unverified model
    
    if current_user.role != 'hr_manager':
        flash('Access denied. HR Manager privileges required.', 'error')
        return redirect(url_for('dashboard.main'))
    
    try:
        today = date.today()
        start_of_month = today.replace(day=1)
        start_of_week = today - timedelta(days=today.weekday())
        
        # Employee Statistics
        total_employees = Employee.query.filter(Employee.is_active == True).count()
        new_employees_this_month = Employee.query.filter(
            Employee.hire_date >= start_of_month,
            Employee.is_active == True
        ).count()
        
        # Department breakdown
        department_stats = db.session.query(
            Employee.department,
            func.count(Employee.id).label('count')
        ).filter(Employee.is_active == True).group_by(Employee.department).all()
        
        # Attendance Statistics for Today
        # FIX: Get attendance records from the model's static method or dedicated query
        todays_attendance = AttendanceRecord.query.filter(AttendanceRecord.date == today).all()
        
        # Get employees on approved leave today
        # FIX: Explicitly join LeaveRequest and Employee to resolve AmbiguousForeignKeysError
        on_leave_employees = LeaveRequest.query.join(
            Employee, LeaveRequest.employee_id == Employee.id 
        ).filter(
            LeaveRequest.status == 'approved',
            LeaveRequest.start_date <= today,
            LeaveRequest.end_date >= today
        ).all()
        
        present_count = len([a for a in todays_attendance if a.status in ['present', 'late']])
        absent_count = len([a for a in todays_attendance if a.status == 'absent'])
        late_count = len([a for a in todays_attendance if a.status == 'late'])
        
        # FIX: Calculate not_marked based on all active employees
        employees_with_attendance = {a.employee_id for a in todays_attendance}
        employees_on_leave = {l.employee_id for l in on_leave_employees}

        on_leave_count = len(employees_on_leave.difference(employees_with_attendance))
        not_marked = total_employees - len(employees_with_attendance) - on_leave_count
        
        # Weekly attendance trends
        week_stats = get_weekly_attendance_trends('all')

        # Leave Requests
        pending_leaves = LeaveRequest.query.filter(LeaveRequest.status.in_(['pending', 'pending_hr'])).count() # FIX: Include pending_hr
        approved_leaves_this_month = LeaveRequest.query.filter(
            LeaveRequest.status == 'approved',
            # FIX: Filter by leave END date or requested date, using requested_date for an accurate monthly request count
            LeaveRequest.requested_date >= start_of_month
        ).count()
        
        # Leave type breakdown for this month
        leave_type_stats = db.session.query(
            LeaveRequest.leave_type,
            func.count(LeaveRequest.id).label('count'),
            func.sum(LeaveRequest.total_days).label('total_days')
        ).filter(
            LeaveRequest.requested_date >= start_of_month,
            LeaveRequest.status == 'approved'
        ).group_by(LeaveRequest.leave_type).all()
        
        # Location-wise breakdown
        locations = current_app.config.get('COMPANY_LOCATIONS', {})
        location_stats = {}
        
        for location_key, location_data in locations.items():
            # FIX: Use helper function to get simplified location metrics
            location_metrics = get_location_statistics(location_key)
            # FIX: Use 'name' key for location display if 'display_name' is missing
            display_name = location_data.get('display_name') or location_data.get('name', location_key.title())
            location_stats[location_key] = {
                'name': display_name,
                **location_metrics
            }
            
        # Recent activities
        recent_activities = get_recent_hr_activities()
        
        # Performance metrics
        performance_metrics = get_hr_performance_metrics()
        
        # Alerts and notifications
        alerts = get_hr_alerts()
        
        dashboard_data = {
            'total_employees': total_employees,
            'new_employees_this_month': new_employees_this_month,
            'present_today': present_count,
            'absent_today': absent_count,
            'on_leave_today': on_leave_count,
            'late_today': late_count,
            'not_marked_today': not_marked,
            'pending_leaves': pending_leaves,
            'approved_leaves_this_month': approved_leaves_this_month,
            'location_stats': location_stats,
            'department_stats': {stat.department: stat.count for stat in department_stats},
            'leave_type_stats': {stat.leave_type: {'count': stat.count, 'days': float(stat.total_days or 0)} for stat in leave_type_stats},
            'week_stats': week_stats,
            'attendance_rate': round((present_count / total_employees * 100) if total_employees > 0 else 0, 1),
            'recent_activities': recent_activities,
            'performance_metrics': performance_metrics,
            'alerts': alerts
        }
        
        return render_template('dashboard/hr_overview.html', 
                             dashboard_data=dashboard_data,
                             today=today)
                             
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error in HR dashboard: {e}")
        flash('Error loading dashboard data. Please try again.', 'error')
        return render_template('dashboard/hr_overview.html', 
                             dashboard_data={},
                             today=today)

@dashboard_bp.route('/station-overview')
@login_required 
def station_overview():
    """Comprehensive Station Manager dashboard"""
    # FIXED: Local imports
    from models.employee import Employee
    from models.attendance import AttendanceRecord
    from models.leave import LeaveRequest
    
    if current_user.role != 'station_manager':
        flash('Access denied. Station Manager privileges required.', 'error')
        return redirect(url_for('dashboard.main'))
    
    user_location = current_user.location
    if not user_location:
        flash('No location assigned to your account. Please contact HR.', 'error')
        return redirect(url_for('dashboard.main'))
    
    try:
        today = date.today()
        start_of_month = today.replace(day=1)
        
        # Get location-specific statistics
        location_stats = get_location_statistics(user_location)
        
        # Get today's attendance for the location
        todays_attendance_details = get_todays_location_attendance(user_location)
        
        # Get shift breakdown for gas stations
        shift_breakdown = get_shift_breakdown(user_location)
        
        # Get recent location activities
        recent_activities = get_recent_location_activities(user_location)
        
        # Get pending items for station manager
        pending_items = get_pending_station_items(user_location)
        
        # Get location performance metrics (Placeholder function for now)
        performance_metrics = get_location_performance_detailed(user_location)
        
        # Get staff on duty breakdown
        staff_on_duty = get_staff_on_duty_breakdown(user_location)
        
        # Get weekly attendance trends for location
        weekly_trends = get_weekly_attendance_trends(user_location)
        
        # Get location-specific alerts
        location_alerts = get_location_alerts(user_location)
        
        # Get inventory status (for gas stations)
        inventory_status = get_inventory_status(user_location)
        
        # Get customer service metrics
        customer_metrics = get_customer_service_metrics(user_location)
        
        location_name = current_app.config.get('COMPANY_LOCATIONS', {}).get(user_location, {}).get('display_name', user_location.title())
        
        # FIX: Get today's attendance summary directly for cards
        total_employees = location_stats.get('total_employees', 0)
        location_attendance_summary = {
            'total_expected': total_employees,
            'present': location_stats.get('present_today', 0),
            'late': location_stats.get('late_today', 0),
            'absent': location_stats.get('absent_today', 0),
            'on_leave': location_stats.get('on_leave_today', 0),
            'not_marked': location_stats.get('not_marked_today', 0),
            'attendance_rate': location_stats.get('attendance_rate_today', 0)
        }
        
        # FIX: Get pending leave requests for the manager's location
        location_leave_requests_pending = LeaveRequest.query.join(
            Employee, LeaveRequest.employee_id == Employee.id # Explicit JOIN condition
        ).filter(
            Employee.location == user_location,
            LeaveRequest.status.in_(['pending', 'pending_hr'])
        ).all()
        
        return render_template('dashboard/station_overview.html',
            location=user_location,
            location_name=location_name,
            location_employees=total_employees, # FIX: Pass total_employees explicitly
            location_attendance=location_attendance_summary, # FIX: Pass the correct summary object
            location_leave_requests=[(req, req.employee) for req in location_leave_requests_pending], # FIX: Pass the actual requests
            shift_overview={'has_shifts': bool(shift_breakdown), **shift_breakdown}, # FIX: Reformat shift_breakdown
            recent_activities=recent_activities,
            pending_items=pending_items,
            # FIXED: Renamed 'performance_metrics' to 'location_metrics' to match the station_overview.html template
            location_metrics=performance_metrics, 
            staff_on_duty=staff_on_duty,
            weekly_trends=weekly_trends,
            location_alerts=location_alerts,
            inventory_status=inventory_status,
            customer_metrics=customer_metrics,
            today=today
        )
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error in station_overview: {e}')
        flash('Error loading station dashboard. Please try again.', 'error')
        return redirect(url_for('dashboard.main'))

@dashboard_bp.route('/attendance/overview')
@login_required
def attendance_overview_old():
    """Redirects old /attendance/overview path to the new details page."""
    # FIX: Added redirect to handle deprecated route
    return redirect(url_for('dashboard.attendance_details'))

@dashboard_bp.route('/attendance-overview-details')
@login_required
def attendance_details():
    """Detailed attendance overview for today (renamed from attendance_overview)"""
    # FIXED: Local imports
    from models.employee import Employee
    from models.attendance import AttendanceRecord
    
    today = date.today()
    location_filter = request.args.get('location')
    status_filter = request.args.get('status')
    
    # Set default location based on role
    if current_user.role == 'station_manager':
        location_filter = current_user.location
    elif not location_filter or location_filter == 'all':
        location_filter = 'all'

    
    try:
        # Get the full overview data, which contains the employee_details list
        overview_data = get_attendance_overview_data(
            today, 
            location_filter, 
            department_filter='all', 
            shift_filter='all', 
            status_filter=status_filter or 'all' # FIX: Use status filter
        )
        
        # Get filter options (not strictly needed for this simple details page, but safe to keep)
        filter_options = get_attendance_filter_options(current_user)

        
        # Location name for display
        location_name = current_app.config.get('COMPANY_LOCATIONS', {}).get(
            location_filter, 
            {'display_name': 'Company Wide'}
        ).get('display_name')
        
        return render_template('dashboard/attendance_details.html',
                             attendance_details=overview_data['employee_details'],
                             filter_status=status_filter or 'all',
                             location_name=location_name,
                             today=today)
                             
    except Exception as e:
        current_app.logger.error(f"Error in attendance details view: {e}")
        flash('Error loading attendance data. Please try again.', 'error')
        return redirect(url_for('dashboard.main'))


@dashboard_bp.route('/api/dashboard-stats')
@login_required
def api_dashboard_stats():
    """API endpoint for real-time dashboard statistics"""
    # FIXED: Local imports
    from models.employee import Employee
    from models.attendance import AttendanceRecord
    from models.leave import LeaveRequest
    
    today = date.today()
    
    try:
        # Get HR or Station Manager location filter
        location_filter = current_user.location if current_user.role == 'station_manager' else 'all'
        
        # Use helper function to get comprehensive data
        overview_data = get_attendance_overview_data(
            today, 
            location_filter, 
            department_filter='all', 
            shift_filter='all', 
            status_filter='all'
        )
        
        # Pending leaves
        if current_user.role == 'station_manager':
             pending_leaves = LeaveRequest.query.join(
                Employee, LeaveRequest.employee_id == Employee.id # Explicit JOIN condition
             ).filter(
                Employee.location == current_user.location,
                LeaveRequest.status.in_(['pending', 'pending_hr'])
             ).count()
        else:
             pending_leaves = LeaveRequest.query.filter(
                LeaveRequest.status.in_(['pending', 'pending_hr'])
             ).count()
             
        # Monthly average (Placeholder for chart data)
        monthly_avg = 90.5 # Mock data
        
        stats = {
            'total_employees': overview_data['total_employees'],
            'present_today': overview_data['present_count'],
            'absent_today': overview_data['absent_count'],
            'on_leave_today': overview_data['on_leave_count'],
            'late_today': overview_data['late_count'],
            'not_marked_today': overview_data['not_marked_count'],
            'pending_leaves': pending_leaves,
            'attendance_rate': overview_data['attendance_rate'],
            'monthly_average': monthly_avg,
            'last_updated': datetime.now().strftime('%H:%M:%S')
        }
        
        return jsonify({'success': True, 'data': stats})
        
    except Exception as e:
        current_app.logger.error(f"Error getting dashboard stats: {e}")
        return jsonify({'success': False, 'message': 'Error loading statistics'})

# Helper functions for dashboard functionality

def get_recent_hr_activities():
    """Get recent HR activities for dashboard"""
    # FIXED: Local imports
    from models.audit import AuditLog
    from models.leave import LeaveRequest
    from models.employee import Employee
    
    activities = []
    
    try:
        # Recent audit logs
        recent_logs = AuditLog.query.filter(
            AuditLog.event_action.in_(['employee_created', 'leave_approved', 'leave_rejected', 'employee_updated'])
        ).order_by(desc(AuditLog.timestamp)).limit(5).all()
        
        for log in recent_logs:
            activities.append({
                'type': log.event_action,
                'description': log.description,
                'timestamp': log.timestamp,
                'user_id': log.user_id,
                'event_category': log.event_category
            })
        
        # Recent pending leave requests
        recent_leaves = LeaveRequest.query.filter(
            LeaveRequest.status.in_(['pending', 'pending_hr'])
        ).order_by(desc(LeaveRequest.created_date)).limit(3).all()
        
        for leave in recent_leaves:
            # FIX: Ensure employee relationship is loaded for full_name
            employee_name = leave.employee.get_full_name() if hasattr(leave, 'employee') and leave.employee else "Employee"
            activities.append({
                'type': 'leave_pending',
                'description': f'Pending leave request from {employee_name}',
                'timestamp': leave.requested_date,
                'employee_id': leave.employee_id,
                'event_category': 'leave'
            })
        
    except Exception as e:
        current_app.logger.error(f"Error getting recent activities: {e}")
    
    # Sort by timestamp and return latest 10
    activities.sort(key=lambda x: x['timestamp'], reverse=True)
    return activities[:10]

def get_hr_performance_metrics():
    """Get HR performance metrics"""
    # FIXED: Local imports
    from models.employee import Employee
    from models.attendance import AttendanceRecord
    
    today = date.today()
    start_of_month = today.replace(day=1)
    
    try:
        # Employee turnover rate (simplified calculation)
        total_employees = Employee.query.filter(Employee.is_active == True).count()
        
        # Average attendance rate for the month
        # FIX: Explicitly join Employee to resolve any ambiguity related to its FKs
        month_attendance = AttendanceRecord.query.join(
            Employee, AttendanceRecord.employee_id == Employee.id # Explicit JOIN condition
        ).filter(
            AttendanceRecord.date >= start_of_month,
            AttendanceRecord.date <= today
        ).all()
        
        if month_attendance:
            present_records = [a for a in month_attendance if a.status in ['present', 'late']]
            attendance_rate = len(present_records) / len(month_attendance) * 100
        else:
            attendance_rate = 0
        
        return {
            'total_employees': total_employees,
            'attendance_rate': round(attendance_rate, 1),
            'employee_satisfaction': 85.0,  # Placeholder
            'training_completion': 78.5     # Placeholder
        }
    except Exception as e:
        current_app.logger.error(f"Error getting performance metrics: {e}")
        return {}

def get_hr_alerts():
    """Get HR alerts and notifications"""
    # FIXED: Local imports
    from models.leave import LeaveRequest
    from models.employee import Employee
    from models.attendance import AttendanceRecord # FIX: Added AttendanceRecord import
    from database import db
    from sqlalchemy import and_, or_
    
    alerts = []
    
    try:
        # Pending leave requests
        pending_leaves = LeaveRequest.query.filter(LeaveRequest.status.in_(['pending', 'pending_hr'])).count() # FIX: Include pending_hr
        if pending_leaves > 0:
            alerts.append({
                'type': 'warning',
                'message': f'{pending_leaves} pending leave request(s) need approval',
                'action_url': url_for('leaves.list_leaves', status='pending')
            })
        
        # Employees with no attendance today
        today = date.today()
        
        # FIX: The original query for employees_no_attendance did not exclude employees on approved leave.
        # This is corrected below to only alert for active employees who are NOT marked AND NOT on leave.
        
        # Subquery for employees on approved leave today
        employees_on_leave_today_ids = db.session.query(LeaveRequest.employee_id).filter(
            LeaveRequest.status == 'approved',
            LeaveRequest.start_date <= today,
            LeaveRequest.end_date >= today
        ).subquery()
        
        # Subquery for employees who have marked attendance today
        employees_with_attendance_today_ids = db.session.query(AttendanceRecord.employee_id).filter(
            AttendanceRecord.date == today
        ).subquery()
        
        # Employees who are active AND (not in attendance AND not on leave)
        employees_no_attendance_or_leave = Employee.query.filter(
            Employee.is_active == True,
            ~Employee.id.in_(employees_with_attendance_today_ids),
            ~Employee.id.in_(employees_on_leave_today_ids) # Exclude those on approved leave
        ).count()
        
        if employees_no_attendance_or_leave > 0:
            alerts.append({
                'type': 'info',
                'message': f'{employees_no_attendance_or_leave} active employee(s) have not marked attendance (and are not on approved leave) today',
                'action_url': url_for('dashboard.attendance_details', status='not_marked')
            })
        
    except Exception as e:
        current_app.logger.error(f"Error getting alerts: {e}")
    
    return alerts

def get_location_statistics(location):
    """Get statistics for a specific location"""
    # FIXED: Local imports
    from models.employee import Employee
    from models.attendance import AttendanceRecord
    from models.leave import LeaveRequest # FIX: Added leave import
    
    try:
        today = date.today()
        start_of_month = today.replace(day=1)
        
        total_employees = Employee.query.filter(
            Employee.location == location, 
            Employee.is_active == True
        ).count()
        
        # Today's attendance
        # FIX: Explicitly join Employee to resolve any ambiguity related to its FKs
        todays_attendance = AttendanceRecord.query.join(
            Employee, AttendanceRecord.employee_id == Employee.id # Explicit JOIN condition
        ).filter(
            AttendanceRecord.date == today,
            Employee.location == location,
            Employee.is_active == True
        ).all()
        
        # Approved leave today
        # FIX: Explicitly specify the ON clause for the JOIN due to multiple FKs on Employee model
        on_leave_requests = LeaveRequest.query.join(
            Employee, LeaveRequest.employee_id == Employee.id # Explicit JOIN condition
        ).filter(
            LeaveRequest.status == 'approved',
            LeaveRequest.start_date <= today,
            LeaveRequest.end_date >= today,
            Employee.location == location
        ).all()
        
        present_today = len([a for a in todays_attendance if a.status in ['present', 'late']])
        absent_today = len([a for a in todays_attendance if a.status == 'absent'])
        late_today = len([a for a in todays_attendance if a.status == 'late'])
        
        # Calculate accounted for employees to get accurate not_marked count
        employees_with_attendance = {a.employee_id for a in todays_attendance}
        employees_on_leave = {l.employee_id for l in on_leave_requests}
        employees_accounted_for = employees_with_attendance.union(employees_on_leave)

        on_leave_today = len(employees_on_leave.difference(employees_with_attendance))
        not_marked_today = total_employees - len(employees_accounted_for)
        
        # Month statistics (Attendance rate)
        # FIX: Explicitly specify the ON clause for the JOIN due to multiple FKs on Employee model
        month_attendance_records = AttendanceRecord.query.join(
            Employee, AttendanceRecord.employee_id == Employee.id # Explicit JOIN condition
        ).filter(
            AttendanceRecord.date >= start_of_month,
            AttendanceRecord.date <= today,
            Employee.location == location,
            Employee.is_active == True
        ).all()
        
        month_present = len([a for a in month_attendance_records if a.status in ['present', 'late']])
        month_total = len(month_attendance_records)
        
        # Pending leaves for the location
        # FIX: Explicitly specify the ON clause for the JOIN due to multiple FKs on Employee model
        pending_leaves_count = LeaveRequest.query.join(
            Employee, LeaveRequest.employee_id == Employee.id # Explicit JOIN condition
        ).filter(
            LeaveRequest.status.in_(['pending', 'pending_hr']),
            Employee.location == location
        ).count()
        
        return {
            'total_employees': total_employees,
            'present_today': present_today,
            'absent_today': absent_today,
            'late_today': late_today,
            'on_leave_today': on_leave_today,
            'not_marked_today': not_marked_today,
            'attendance_rate_today': round((present_today / total_employees * 100) if total_employees > 0 else 0, 1),
            'attendance_rate_month': round((month_present / month_total * 100) if month_total > 0 else 0, 1),
            'pending_leaves': pending_leaves_count
        }
        
    except Exception as e:
        current_app.logger.error(f"Error getting location statistics: {e}")
        # Reraise the original error for context in the HR overview query itself if needed, 
        # but here we log and return an empty dict for graceful failure.
        return {} 

def get_todays_location_attendance(location):
    """Get today's attendance details for a location"""
    # FIXED: Local imports
    from models.employee import Employee
    from models.attendance import AttendanceRecord
    
    today = date.today()
    
    try:
        # FIX: Explicitly specify the ON clause for the OUTER JOIN due to multiple FKs on Employee model
        attendance_records = db.session.query(Employee, AttendanceRecord).outerjoin(
            AttendanceRecord,
            and_(Employee.id == AttendanceRecord.employee_id, AttendanceRecord.date == today)
        ).filter(
            Employee.location == location,
            Employee.is_active == True
        ).all()
        
        attendance_data = []
        for employee, attendance in attendance_records:
            status = attendance.status if attendance else 'not_marked'
            clock_in = attendance.clock_in_time if attendance else None
            
            attendance_data.append({
                'employee': employee,
                'status': status,
                'clock_in_time': clock_in,
                'shift': getattr(employee, 'shift', 'day')
            })
        
        return attendance_data
        
    except Exception as e:
        current_app.logger.error(f"Error getting today's attendance: {e}")
        return []

def get_shift_breakdown(location):
    """Get shift breakdown for a location"""
    # FIXED: Local imports
    from models.employee import Employee
    from models.attendance import AttendanceRecord
    
    today = date.today()
    location_config = current_app.config.get('COMPANY_LOCATIONS', {}).get(location, {})
    shifts = location_config.get('working_hours', {}).keys() # FIX: Use keys from working_hours

    shift_data = {'day_shift': {'total': 0, 'present': 0, 'absent': 0, 'attendance_rate': 0},
                  'night_shift': {'total': 0, 'present': 0, 'absent': 0, 'attendance_rate': 0}}
    
    has_shifts = False
    if 'day_shift' in shifts or 'night_shift' in shifts:
        has_shifts = True
    
    try:
        for shift in ['day', 'night']: # Iterate over standard shifts for gas stations
            shift_key = f'{shift}_shift'
            
            shift_employees = Employee.query.filter(
                Employee.location == location,
                Employee.shift == shift,
                Employee.is_active == True
            ).count()
            
            # FIX: Explicitly specify the ON clause for the JOIN due to multiple FKs on Employee model
            shift_attendance = AttendanceRecord.query.join(
                Employee, AttendanceRecord.employee_id == Employee.id # Explicit JOIN condition
            ).filter(
                AttendanceRecord.date == today,
                Employee.location == location,
                Employee.shift == shift,
                Employee.is_active == True
            ).all()
            
            shift_present = len([a for a in shift_attendance if a.status in ['present', 'late']])
            
            shift_data[shift_key] = {
                'total': shift_employees,
                'present': shift_present,
                'absent': shift_employees - shift_present,
                'attendance_rate': round((shift_present / shift_employees * 100) if shift_employees > 0 else 0, 1)
            }
            
    except Exception as e:
        current_app.logger.error(f"Error getting shift breakdown: {e}")
    
    return {'has_shifts': has_shifts, **shift_data}

def get_recent_location_activities(location):
    """Get recent activities for a specific location"""
    # FIXED: Local imports
    from models.audit import AuditLog
    from models.employee import Employee
    
    try:
        # Get recent audit logs for this location
        # Filter based on employee location and/or location name in description
        location_employee_ids = db.session.query(Employee.id).filter(
            Employee.location == location,
            Employee.is_active == True
        ).subquery()
        
        recent_logs = AuditLog.query.filter(
            or_(
                AuditLog.description.like(f'%{location}%'),
                AuditLog.target_id.in_(location_employee_ids)
            )
        ).order_by(desc(AuditLog.timestamp)).limit(10).all()
        
        activities = []
        for log in recent_logs:
            activities.append({
                'action': log.event_action,
                'description': log.description,
                'timestamp': log.timestamp,
                'user_id': log.user_id,
                'event_category': log.event_category
            })
        
        return activities
        
    except Exception as e:
        current_app.logger.error(f"Error getting recent activities: {e}")
        return []

def get_pending_station_items(location):
    """Get pending items that need station manager attention"""
    # FIXED: Local imports
    from models.leave import LeaveRequest
    from models.employee import Employee
    
    pending_items = {
        'leaves': 0
    }
    
    try:
        # Pending leave requests for this location
        # FIX: Explicitly specify the ON clause for the JOIN due to multiple FKs on Employee model
        pending_leaves = LeaveRequest.query.join(
            Employee, LeaveRequest.employee_id == Employee.id # Explicit JOIN condition
        ).filter(
            LeaveRequest.status.in_(['pending', 'pending_hr']),
            Employee.location == location
        ).count()
        
        pending_items['leaves'] = pending_leaves
        
    except Exception as e:
        current_app.logger.error(f"Error getting pending items: {e}")
    
    return pending_items

def get_location_performance_detailed(location):
    """Get detailed performance metrics for a location"""
    # FIX: Use simplified calculated metrics from the get_location_statistics helper
    stats = get_location_statistics(location)

    return {
        'week_attendance_rate': stats.get('attendance_rate_week', 90.0), # Mock
        'month_attendance_rate': stats.get('attendance_rate_month', 92.5),
        'approved_leaves_month': 5, # Mock
        'customer_satisfaction': 92.5, # Mock
        'sales_target_achievement': 88.2, # Mock
    }

def get_staff_on_duty_breakdown(location):
    """Get breakdown of staff currently on duty"""
    # FIXED: Local imports
    from models.employee import Employee
    from models.attendance import AttendanceRecord
    
    today = date.today()
    current_time = datetime.now()
    current_hour = current_time.hour
    
    try:
        # Determine current shift based on time (6:00-18:00 Day, 18:00-06:00 Night)
        if 6 <= current_hour < 18:
            current_shift = 'day'
        else:
            current_shift = 'night'
        
        # Get employees on current shift who are present
        # FIX: Explicitly specify the ON clause for the JOIN due to multiple FKs on Employee model
        on_duty_records = AttendanceRecord.query.join(
            Employee, AttendanceRecord.employee_id == Employee.id # Explicit JOIN condition
        ).filter(
            AttendanceRecord.date == today,
            AttendanceRecord.status.in_(['present', 'late']),
            Employee.location == location,
            Employee.shift == current_shift,
            Employee.is_active == True
        ).all()
        
        duty_breakdown = {
            'current_shift': current_shift,
            'total_on_duty': len(on_duty_records),
            'by_department': {}
        }
        
        # Group by department
        for record in on_duty_records:
            dept = record.employee.department
            if dept not in duty_breakdown['by_department']:
                duty_breakdown['by_department'][dept] = 0
            duty_breakdown['by_department'][dept] += 1
        
        return duty_breakdown
        
    except Exception as e:
        current_app.logger.error(f"Error getting staff on duty: {e}")
        return {}

def get_weekly_attendance_trends(location):
    """Get weekly attendance trends for a location"""
    # FIXED: Local imports
    from models.employee import Employee
    from models.attendance import AttendanceRecord
    
    today = date.today()
    start_of_week = today - timedelta(days=today.weekday())
    
    weekly_data = []
    
    try:
        for i in range(7):
            day = start_of_week + timedelta(days=i)
            if day <= today:
                
                # Determine total active employees for normalization
                employee_query = Employee.query.filter(Employee.is_active == True)
                if location != 'all':
                    employee_query = employee_query.filter(Employee.location == location)
                total_employees = employee_query.count()
                
                # Get attendance records
                # FIX: Explicitly specify the ON clause for the JOIN due to multiple FKs on Employee model
                attendance_query = AttendanceRecord.query.join(
                    Employee, AttendanceRecord.employee_id == Employee.id # Explicit JOIN condition
                ).filter(
                    AttendanceRecord.date == day,
                    Employee.is_active == True
                )
                if location != 'all':
                    attendance_query = attendance_query.filter(Employee.location == location)
                
                day_attendance = attendance_query.all()
                
                present_count = len([a for a in day_attendance if a.status in ['present', 'late']])
                
                weekly_data.append({
                    'date': day.isoformat(),
                    'day_name': day.strftime('%A'),
                    'present': present_count,
                    'total': total_employees,
                    'rate': round((present_count / total_employees * 100) if total_employees > 0 else 0, 1)
                })
        
        return weekly_data
        
    except Exception as e:
        current_app.logger.error(f"Error getting weekly trends: {e}")
        return []

def get_location_alerts(location):
    """Get location-specific alerts"""
    alerts = []
    
    # Placeholder alerts - you can add real logic here
    alerts.append({
        'type': 'info',
        'title': 'System Status',
        'message': 'All attendance systems are operational.',
        'timestamp': datetime.now()
    })
    
    # Mock Security Alert (High priority)
    if location == 'dandora':
         alerts.append({
            'type': 'danger',
            'title': 'Security Incident',
            'message': 'CCTV offline in bay 3. Check physical connection.',
            'timestamp': datetime.now() - timedelta(hours=3)
        })
    
    return alerts

def get_inventory_status(location):
    """Get inventory status for gas stations"""
    # Placeholder inventory data
    return {
        'fuel_level': 85.2,
        'lubricants': 92.8,
        'retail_items': 78.5,
        'last_updated': datetime.now().strftime('%H:%M')
    }

def get_customer_service_metrics(location):
    """Get customer service metrics"""
    # Placeholder customer metrics
    return {
        'customer_satisfaction': 94.2,
        'average_service_time': '3:24',
        'daily_transactions': 156,
        'peak_hours': '07:00-09:00, 17:00-19:00'
    }

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
        # FIX: Explicitly join Employee to resolve any ambiguity related to its FKs (even though this query is simple)
        attendance_query = AttendanceRecord.query.join(
            Employee, AttendanceRecord.employee_id == Employee.id
        ).filter(
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
        # FIX: Explicitly join LeaveRequest and Employee to resolve multiple FK ambiguity
        leave_requests = LeaveRequest.query.join(
            Employee, LeaveRequest.employee_id == Employee.id # Explicit JOIN condition
        ).filter(
            LeaveRequest.employee_id.in_([emp.id for emp in employees]),
            LeaveRequest.start_date <= target_date,
            LeaveRequest.end_date >= target_date,
            LeaveRequest.status == 'approved'
        ).all()
    
    # Calculate statistics
    present_count = len([r for r in attendance_records if r.status in ['present', 'late']])
    absent_count = len([r for r in attendance_records if r.status == 'absent'])
    late_count = len([r for r in attendance_records if r.status == 'late'])
    
    # FIX: Correctly calculate not_marked and on_leave to avoid double counting and ensure accuracy
    employees_with_attendance = {r.employee_id for r in attendance_records}
    employees_on_leave = {r.employee_id for r in leave_requests}
    
    # Employees who are on approved leave and do NOT have an attendance record
    on_leave_only_count = len(employees_on_leave.difference(employees_with_attendance))
    
    # Employees who are accounted for (either by attendance or approved leave)
    employees_accounted_for = employees_with_attendance.union(employees_on_leave)

    not_marked_count = total_employees - len(employees_accounted_for)
    
    # Build detailed employee list
    employee_details = []
    attendance_dict = {r.employee_id: r for r in attendance_records}
    leave_dict = {r.employee_id: r for r in leave_requests}
    
    for employee in employees:
        attendance = attendance_dict.get(employee.id)
        leave = leave_dict.get(employee.id)
        
        status = 'not_marked'
        status_detail = 'Not Marked'
        clock_in_display = None
        clock_out_display = None

        if leave and not attendance: 
            status = 'on_leave'
            status_detail = f"On {leave.leave_type.replace('_', ' ').title()}"

        elif attendance:
            status = attendance.status
            status_detail = status.replace('_', ' ').title()
            clock_in_display = attendance.clock_in_time.strftime('%H:%M') if attendance.clock_in_time else None
            clock_out_display = attendance.clock_out_time.strftime('%H:%M') if attendance.clock_out_time else None

            if clock_in_display:
                status_detail += f" (In: {clock_in_display})"
            if clock_out_display:
                status_detail += f" (Out: {clock_out_display})"

        # Apply filter post-calculation to return only filtered list
        if status_filter == 'all' or \
           status == status_filter or \
           (status_filter == 'present_late' and status in ['present', 'late']):
            
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
        'on_leave_count': on_leave_only_count, 
        'not_marked_count': not_marked_count,
        'attendance_rate': round((present_count / total_employees * 100), 1) if total_employees > 0 else 0,
        'employee_details': employee_details,
        'date': target_date
    }

def get_attendance_filter_options(user):
    """Get available filter options for attendance details"""
    options = {
        'locations': [],
        'departments': list(current_app.config.get('DEPARTMENTS', {}).keys()),
        'shifts': ['day', 'night'],
        'statuses': ['all', 'present', 'absent', 'late', 'on_leave', 'not_marked']
    }
    
    # Locations based on role
    if user.role == 'hr_manager':
        options['locations'] = ['all'] + list(current_app.config.get('COMPANY_LOCATIONS', {}).keys())
    elif user.role == 'station_manager':
        options['locations'] = [user.location]
    
    return options