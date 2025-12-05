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
from datetime import date, datetime, timedelta
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
        AuditLog.log_action(
            user_id=current_user.id,
            action='dashboard_access',
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
    elif current_user.role == 'finance_manager':
        return redirect(url_for('dashboard.finance_overview'))
    elif current_user.role == 'admin':
        return redirect(url_for('dashboard.admin_overview'))
    else:
        # Employee or other roles - basic dashboard
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
    from models.holiday import Holiday
    
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
        today_attendance = AttendanceRecord.query.filter(AttendanceRecord.date == today).all()
        present_count = len([a for a in today_attendance if a.status in ['present', 'late']])
        absent_count = len([a for a in today_attendance if a.status == 'absent'])
        on_leave_count = len([a for a in today_attendance if a.status == 'on_leave'])
        late_count = len([a for a in today_attendance if a.status == 'late'])
        not_marked = total_employees - len(today_attendance)
        
        # Weekly attendance trends
        week_stats = []
        for i in range(7):
            day = start_of_week + timedelta(days=i)
            if day <= today:
                day_attendance = AttendanceRecord.query.filter(AttendanceRecord.date == day).all()
                day_present = len([a for a in day_attendance if a.status in ['present', 'late']])
                week_stats.append({
                    'date': day.strftime('%Y-%m-%d'),
                    'day_name': day.strftime('%A'),
                    'present': day_present,
                    'total': len(day_attendance),
                    'rate': round((day_present / len(day_attendance) * 100) if day_attendance else 0, 1)
                })
        
        # Leave Requests
        pending_leaves = LeaveRequest.query.filter(LeaveRequest.status == 'pending').count()
        approved_leaves_this_month = LeaveRequest.query.filter(
            LeaveRequest.status == 'approved',
            LeaveRequest.start_date >= start_of_month
        ).count()
        
        # Leave type breakdown for this month
        leave_type_stats = db.session.query(
            LeaveRequest.leave_type,
            func.count(LeaveRequest.id).label('count'),
            func.sum(LeaveRequest.total_days).label('total_days')
        ).filter(
            LeaveRequest.start_date >= start_of_month,
            LeaveRequest.status == 'approved'
        ).group_by(LeaveRequest.leave_type).all()
        
        # Location-wise breakdown
        locations = current_app.config.get('COMPANY_LOCATIONS', {})
        location_stats = {}
        
        for location_key, location_data in locations.items():
            location_employees = Employee.query.filter(
                Employee.location == location_key, 
                Employee.is_active == True
            ).count()
            
            location_attendance = AttendanceRecord.query.join(Employee).filter(
                AttendanceRecord.date == today,
                Employee.location == location_key,
                Employee.is_active == True
            ).all()
            
            location_present = len([a for a in location_attendance if a.status in ['present', 'late']])
            location_absent = len([a for a in location_attendance if a.status == 'absent'])
            location_on_leave = len([a for a in location_attendance if a.status == 'on_leave'])
            location_late = len([a for a in location_attendance if a.status == 'late'])
            
            # Shift breakdown for gas stations
            shift_breakdown = {}
            if location_data.get('shifts'):
                for shift in location_data['shifts']:
                    shift_employees = Employee.query.filter(
                        Employee.location == location_key,
                        Employee.shift == shift,
                        Employee.is_active == True
                    ).count()
                    
                    shift_attendance = AttendanceRecord.query.join(Employee).filter(
                        AttendanceRecord.date == today,
                        Employee.location == location_key,
                        Employee.shift == shift,
                        Employee.is_active == True
                    ).all()
                    
                    shift_present = len([a for a in shift_attendance if a.status in ['present', 'late']])
                    
                    shift_breakdown[shift] = {
                        'total_employees': shift_employees,
                        'present': shift_present,
                        'absent': shift_employees - shift_present,
                        'attendance_rate': round((shift_present / shift_employees * 100) if shift_employees > 0 else 0, 1)
                    }
            
            location_stats[location_key] = {
                'name': location_data['display_name'],
                'total_employees': location_employees,
                'present': location_present,
                'absent': location_absent,
                'on_leave': location_on_leave,
                'late': location_late,
                'not_marked': location_employees - len(location_attendance),
                'attendance_rate': round((location_present / location_employees * 100) if location_employees > 0 else 0, 1),
                'shift_breakdown': shift_breakdown
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
        start_of_week = today - timedelta(days=today.weekday())
        
        # Get location-specific statistics
        location_stats = get_location_statistics(user_location)
        
        # Get today's attendance for the location
        todays_attendance = get_todays_location_attendance(user_location)
        
        # Get shift breakdown for gas stations
        shift_breakdown = get_shift_breakdown(user_location)
        
        # Get recent location activities
        recent_activities = get_recent_location_activities(user_location)
        
        # Get pending items for station manager
        pending_items = get_pending_station_items(user_location)
        
        # Get location performance metrics
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
        
        return render_template('dashboard/station_overview.html',
            location=user_location,
            location_name=location_name,
            location_stats=location_stats,
            todays_attendance=todays_attendance,
            shift_breakdown=shift_breakdown,
            recent_activities=recent_activities,
            pending_items=pending_items,
            performance_metrics=performance_metrics,
            staff_on_duty=staff_on_duty,
            weekly_trends=weekly_trends,
            location_alerts=location_alerts,
            inventory_status=inventory_status,
            customer_metrics=customer_metrics,
            today=today
        )
        
    except Exception as e:
        current_app.logger.error(f'Error in station_overview: {e}')
        flash('Error loading station dashboard. Please try again.', 'error')
        return redirect(url_for('dashboard.main'))

@dashboard_bp.route('/finance-overview')
@login_required
def finance_overview():
    """Finance Manager dashboard"""
    # FIXED: Local imports
    from models.employee import Employee
    from models.attendance import AttendanceRecord
    
    if current_user.role != 'finance_manager':
        flash('Access denied. Finance Manager privileges required.', 'error')
        return redirect(url_for('dashboard.main'))
    
    try:
        today = date.today()
        start_of_month = today.replace(day=1)
        
        # Financial metrics related to attendance
        total_employees = Employee.query.filter(Employee.is_active == True).count()
        
        # Calculate total work hours for payroll
        month_attendance = AttendanceRecord.query.filter(
            AttendanceRecord.date >= start_of_month,
            AttendanceRecord.date <= today
        ).all()
        
        total_hours = sum(float(getattr(record, 'work_hours', 0) or 0) for record in month_attendance)
        total_overtime = sum(float(getattr(record, 'overtime_hours', 0) or 0) for record in month_attendance)
        
        # Placeholder financial data
        finance_data = {
            'total_employees': total_employees,
            'total_hours_this_month': round(total_hours, 2),
            'total_overtime_this_month': round(total_overtime, 2),
            'estimated_payroll': round(total_hours * 50 + total_overtime * 75, 2),  # Example calculation
            'attendance_rate': 95.2  # Example value
        }
        
        return render_template('dashboard/finance_overview.html', finance_data=finance_data, today=today)
        
    except Exception as e:
        current_app.logger.error(f'Error in finance_overview: {e}')
        flash('Error loading finance dashboard. Please try again.', 'error')
        return redirect(url_for('dashboard.main'))

@dashboard_bp.route('/admin-overview')
@login_required
def admin_overview():
    """System Administrator dashboard"""
    # FIXED: Local imports
    from models.user import User
    from models.employee import Employee
    from models.audit import AuditLog
    
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard.main'))
    
    try:
        # System statistics
        total_users = User.query.count()
        active_users = User.query.filter(User.is_active == True).count()
        total_employees = Employee.query.count()
        active_employees = Employee.query.filter(Employee.is_active == True).count()
        
        # Recent audit logs
        recent_logs = AuditLog.query.order_by(desc(AuditLog.timestamp)).limit(10).all()
        
        # System health metrics
        admin_data = {
            'total_users': total_users,
            'active_users': active_users,
            'total_employees': total_employees,
            'active_employees': active_employees,
            'recent_logs': recent_logs,
            'system_health': 'Operational'  # Example value
        }
        
        return render_template('dashboard/admin_overview.html', admin_data=admin_data)
        
    except Exception as e:
        current_app.logger.error(f'Error in admin_overview: {e}')
        flash('Error loading admin dashboard. Please try again.', 'error')
        return redirect(url_for('dashboard.main'))

@dashboard_bp.route('/attendance-overview')
@login_required
def attendance_overview():
    """Detailed attendance overview for today"""
    # FIXED: Local imports
    from models.employee import Employee
    from models.attendance import AttendanceRecord
    
    today = date.today()
    location_filter = request.args.get('location')
    status_filter = request.args.get('status')
    department_filter = request.args.get('department')
    page = request.args.get('page', 1, type=int)
    per_page = 50
    
    try:
        # Base query
        query = db.session.query(Employee, AttendanceRecord).outerjoin(
            AttendanceRecord, 
            and_(Employee.id == AttendanceRecord.employee_id, AttendanceRecord.date == today)
        ).filter(Employee.is_active == True)
        
        # Apply location filter based on user role
        if current_user.role == 'station_manager':
            query = query.filter(Employee.location == current_user.location)
        elif location_filter and location_filter != 'all':
            query = query.filter(Employee.location == location_filter)
        
        # Apply department filter
        if department_filter and department_filter != 'all':
            query = query.filter(Employee.department == department_filter)
        
        # Apply status filter
        if status_filter:
            if status_filter == 'present':
                query = query.filter(AttendanceRecord.status.in_(['present', 'late']))
            elif status_filter == 'absent':
                query = query.filter(AttendanceRecord.status == 'absent')
            elif status_filter == 'not_marked':
                query = query.filter(AttendanceRecord.id.is_(None))
            elif status_filter != 'all':
                query = query.filter(AttendanceRecord.status == status_filter)
        
        # Order by employee name
        query = query.order_by(Employee.first_name, Employee.last_name)
        
        # Paginate
        results = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # Process results
        attendance_data = []
        for employee, attendance in results.items:
            if attendance:
                status = attendance.status
                clock_in = attendance.clock_in_time
                clock_out = attendance.clock_out_time
                work_hours = getattr(attendance, 'work_hours', None)
            else:
                status = 'not_marked'
                clock_in = None
                clock_out = None
                work_hours = None
            
            attendance_data.append({
                'employee': employee,
                'status': status,
                'clock_in_time': clock_in,
                'clock_out_time': clock_out,
                'work_hours': work_hours,
                'attendance_id': attendance.id if attendance else None
            })
        
        # Get filter options
        filter_options = get_attendance_filter_options(current_user)
        
        # Calculate summary stats
        total_count = len(attendance_data)
        present_count = len([a for a in attendance_data if a['status'] in ['present', 'late']])
        absent_count = len([a for a in attendance_data if a['status'] == 'absent'])
        not_marked_count = len([a for a in attendance_data if a['status'] == 'not_marked'])
        
        summary_stats = {
            'total': total_count,
            'present': present_count,
            'absent': absent_count,
            'not_marked': not_marked_count,
            'attendance_rate': round((present_count / total_count * 100) if total_count > 0 else 0, 1)
        }
        
        return render_template('dashboard/attendance_overview.html',
                             attendance_data=attendance_data,
                             pagination=results,
                             filter_options=filter_options,
                             summary_stats=summary_stats,
                             today=today,
                             selected_location=location_filter,
                             selected_status=status_filter,
                             selected_department=department_filter)
                             
    except Exception as e:
        current_app.logger.error(f"Error in attendance overview: {e}")
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
        # Basic stats
        if current_user.role == 'hr_manager':
            # HR sees all data
            total_employees = Employee.query.filter(Employee.is_active == True).count()
            today_attendance = AttendanceRecord.query.filter(AttendanceRecord.date == today).all()
        else:
            # Station manager sees only their location
            total_employees = Employee.query.filter(
                Employee.location == current_user.location,
                Employee.is_active == True
            ).count()
            today_attendance = AttendanceRecord.query.join(Employee).filter(
                AttendanceRecord.date == today,
                Employee.location == current_user.location
            ).all()
        
        present = len([a for a in today_attendance if a.status in ['present', 'late']])
        absent = len([a for a in today_attendance if a.status == 'absent'])
        on_leave = len([a for a in today_attendance if a.status == 'on_leave'])
        late = len([a for a in today_attendance if a.status == 'late'])
        not_marked = total_employees - len(today_attendance)
        
        stats = {
            'total_employees': total_employees,
            'present': present,
            'absent': absent,
            'on_leave': on_leave,
            'late': late,
            'not_marked': not_marked,
            'attendance_rate': round((present / total_employees * 100) if total_employees > 0 else 0, 1),
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
            AuditLog.action.in_(['employee_created', 'leave_approved', 'leave_rejected', 'employee_updated'])
        ).order_by(desc(AuditLog.timestamp)).limit(5).all()
        
        for log in recent_logs:
            activities.append({
                'type': log.action,
                'description': log.description,
                'timestamp': log.timestamp,
                'user_id': log.user_id
            })
        
        # Recent leave requests
        recent_leaves = LeaveRequest.query.filter(
            LeaveRequest.status == 'pending'
        ).order_by(desc(LeaveRequest.created_date)).limit(3).all()
        
        for leave in recent_leaves:
            activities.append({
                'type': 'leave_pending',
                'description': f'Pending leave request from {leave.employee.get_full_name() if hasattr(leave, "employee") else "Employee"}',
                'timestamp': leave.created_date,
                'employee_id': leave.employee_id
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
        month_attendance = AttendanceRecord.query.filter(
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
    
    alerts = []
    
    try:
        # Pending leave requests
        pending_leaves = LeaveRequest.query.filter(LeaveRequest.status == 'pending').count()
        if pending_leaves > 0:
            alerts.append({
                'type': 'warning',
                'message': f'{pending_leaves} pending leave request(s) need approval',
                'action_url': url_for('leaves.list_leaves', status='pending')
            })
        
        # Employees with no attendance today
        today = date.today()
        employees_no_attendance = Employee.query.filter(
            Employee.is_active == True,
            ~Employee.id.in_(
                db.session.query(AttendanceRecord.employee_id).filter(
                    AttendanceRecord.date == today
                )
            )
        ).count()
        
        if employees_no_attendance > 0:
            alerts.append({
                'type': 'info',
                'message': f'{employees_no_attendance} employee(s) have not marked attendance today',
                'action_url': url_for('dashboard.attendance_overview', status='not_marked')
            })
        
    except Exception as e:
        current_app.logger.error(f"Error getting alerts: {e}")
    
    return alerts

def get_location_statistics(location):
    """Get statistics for a specific location"""
    # FIXED: Local imports
    from models.employee import Employee
    from models.attendance import AttendanceRecord
    
    try:
        today = date.today()
        start_of_month = today.replace(day=1)
        
        total_employees = Employee.query.filter(
            Employee.location == location, 
            Employee.is_active == True
        ).count()
        
        # Today's attendance
        todays_attendance = AttendanceRecord.query.join(Employee).filter(
            AttendanceRecord.date == today,
            Employee.location == location,
            Employee.is_active == True
        ).all()
        
        present_today = len([a for a in todays_attendance if a.status in ['present', 'late']])
        absent_today = len([a for a in todays_attendance if a.status == 'absent'])
        late_today = len([a for a in todays_attendance if a.status == 'late'])
        
        # Month statistics
        month_attendance = AttendanceRecord.query.join(Employee).filter(
            AttendanceRecord.date >= start_of_month,
            AttendanceRecord.date <= today,
            Employee.location == location,
            Employee.is_active == True
        ).all()
        
        month_present = len([a for a in month_attendance if a.status in ['present', 'late']])
        month_total = len(month_attendance)
        
        return {
            'total_employees': total_employees,
            'present_today': present_today,
            'absent_today': absent_today,
            'late_today': late_today,
            'not_marked_today': total_employees - len(todays_attendance),
            'attendance_rate_today': round((present_today / total_employees * 100) if total_employees > 0 else 0, 1),
            'attendance_rate_month': round((month_present / month_total * 100) if month_total > 0 else 0, 1)
        }
        
    except Exception as e:
        current_app.logger.error(f"Error getting location statistics: {e}")
        return {}

def get_todays_location_attendance(location):
    """Get today's attendance details for a location"""
    # FIXED: Local imports
    from models.employee import Employee
    from models.attendance import AttendanceRecord
    
    today = date.today()
    
    try:
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
    shifts = location_config.get('shifts', ['day'])
    
    shift_data = {}
    
    try:
        for shift in shifts:
            shift_employees = Employee.query.filter(
                Employee.location == location,
                Employee.shift == shift,
                Employee.is_active == True
            ).count()
            
            shift_attendance = AttendanceRecord.query.join(Employee).filter(
                AttendanceRecord.date == today,
                Employee.location == location,
                Employee.shift == shift,
                Employee.is_active == True
            ).all()
            
            shift_present = len([a for a in shift_attendance if a.status in ['present', 'late']])
            
            shift_data[shift] = {
                'total_employees': shift_employees,
                'present': shift_present,
                'absent': shift_employees - shift_present,
                'attendance_rate': round((shift_present / shift_employees * 100) if shift_employees > 0 else 0, 1)
            }
            
    except Exception as e:
        current_app.logger.error(f"Error getting shift breakdown: {e}")
    
    return shift_data

def get_recent_location_activities(location):
    """Get recent activities for a specific location"""
    # FIXED: Local imports
    from models.audit import AuditLog
    from models.employee import Employee
    
    try:
        # Get recent audit logs for this location
        location_employee_ids = db.session.query(Employee.id).filter(
            Employee.location == location,
            Employee.is_active == True
        ).subquery()
        
        recent_logs = AuditLog.query.filter(
            or_(
                AuditLog.description.like(f'%{location}%'),
                AuditLog.record_id.in_(location_employee_ids)
            )
        ).order_by(desc(AuditLog.timestamp)).limit(10).all()
        
        activities = []
        for log in recent_logs:
            activities.append({
                'action': log.action,
                'description': log.description,
                'timestamp': log.timestamp,
                'user_id': log.user_id
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
    
    pending_items = []
    
    try:
        # Pending leave requests for this location
        pending_leaves = LeaveRequest.query.join(Employee).filter(
            LeaveRequest.status == 'pending',
            Employee.location == location
        ).count()
        
        if pending_leaves > 0:
            pending_items.append({
                'type': 'leaves',
                'count': pending_leaves,
                'message': f'{pending_leaves} pending leave request(s)',
                'url': url_for('leaves.list_leaves', status='pending')
            })
        
        # Add more pending items as needed
        
    except Exception as e:
        current_app.logger.error(f"Error getting pending items: {e}")
    
    return pending_items

def get_location_performance_detailed(location):
    """Get detailed performance metrics for a location"""
    today = date.today()
    start_of_month = today.replace(day=1)
    
    # Placeholder performance metrics
    return {
        'customer_satisfaction': 92.5,
        'sales_target_achievement': 88.2,
        'safety_score': 96.8,
        'efficiency_rating': 91.3
    }

def get_staff_on_duty_breakdown(location):
    """Get breakdown of staff currently on duty"""
    # FIXED: Local imports
    from models.employee import Employee
    from models.attendance import AttendanceRecord
    
    today = date.today()
    current_hour = datetime.now().hour
    
    try:
        # Determine current shift based on time
        if 6 <= current_hour < 18:
            current_shift = 'day'
        else:
            current_shift = 'night'
        
        # Get employees on current shift who are present
        on_duty = AttendanceRecord.query.join(Employee).filter(
            AttendanceRecord.date == today,
            AttendanceRecord.status.in_(['present', 'late']),
            Employee.location == location,
            Employee.shift == current_shift,
            Employee.is_active == True
        ).all()
        
        duty_breakdown = {
            'current_shift': current_shift,
            'total_on_duty': len(on_duty),
            'by_department': {}
        }
        
        # Group by department
        for record in on_duty:
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
                day_attendance = AttendanceRecord.query.join(Employee).filter(
                    AttendanceRecord.date == day,
                    Employee.location == location,
                    Employee.is_active == True
                ).all()
                
                present_count = len([a for a in day_attendance if a.status in ['present', 'late']])
                total_count = len(day_attendance)
                
                weekly_data.append({
                    'date': day.strftime('%Y-%m-%d'),
                    'day_name': day.strftime('%A'),
                    'present': present_count,
                    'total': total_count,
                    'rate': round((present_count / total_count * 100) if total_count > 0 else 0, 1)
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
        'message': 'All systems operational',
        'timestamp': datetime.now()
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