"""
Enhanced Dashboard Routes for Sakina Gas Attendance System
Built upon your existing comprehensive dashboard with advanced analytics
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, g
from flask_login import login_required, current_user
from models import db, Employee, AttendanceRecord, LeaveRequest, Holiday, User, AuditLog, PerformanceReview
from datetime import date, datetime, timedelta
from sqlalchemy import func, and_, or_, select, desc
from collections import defaultdict, OrderedDict
import calendar

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@dashboard_bp.route('/main')
@login_required
def main():
    """Enhanced main dashboard with comprehensive analytics"""
    return redirect(url_for(f'dashboard.{current_user.role}_overview'))

@dashboard_bp.route('/hr-overview')
@login_required
def hr_overview():
    """Comprehensive HR Manager dashboard"""
    if current_user.role != 'hr_manager':
        flash('Access denied. HR Manager privileges required.', 'danger')
        return redirect(url_for('dashboard.main'))
    
    today = date.today()
    
    # Overall statistics
    total_employees = Employee.query.filter(Employee.is_active == True).count()
    
    # Today's attendance overview
    attendance_overview = get_comprehensive_attendance_overview(today)
    
    # Recent activities (last 7 days)
    recent_activities = get_recent_hr_activities(days=7)
    
    # Pending approvals
    pending_items = get_pending_hr_approvals()
    
    # Department breakdown
    department_stats = get_department_statistics()
    
    # Location performance metrics
    location_performance = get_location_performance_metrics()
    
    # Compliance alerts
    compliance_alerts = get_compliance_alerts()
    
    # Monthly trends
    monthly_trends = get_monthly_attendance_trends()
    
    # Employee anniversary alerts (upcoming)
    upcoming_anniversaries = get_upcoming_work_anniversaries()
    
    # Performance review due alerts
    performance_due = get_performance_reviews_due()
    
    return render_template('dashboard/hr_overview.html',
                         total_employees=total_employees,
                         attendance_overview=attendance_overview,
                         recent_activities=recent_activities,
                         pending_items=pending_items,
                         department_stats=department_stats,
                         location_performance=location_performance,
                         compliance_alerts=compliance_alerts,
                         monthly_trends=monthly_trends,
                         upcoming_anniversaries=upcoming_anniversaries,
                         performance_due=performance_due,
                         today=today)

@dashboard_bp.route('/station-overview')
@login_required
def station_overview():
    """Enhanced Station Manager dashboard"""
    if current_user.role != 'station_manager':
        flash('Access denied. Station Manager privileges required.', 'danger')
        return redirect(url_for('dashboard.main'))
    
    today = date.today()
    location = current_user.location
    
    # Station-specific statistics
    station_employees = Employee.query.filter(
        Employee.location == location,
        Employee.is_active == True
    ).count()
    
    # Today's attendance for this station
    station_attendance = get_station_attendance_overview(location, today)
    
    # Shift breakdown (if applicable)
    shift_breakdown = get_station_shift_breakdown(location, today)
    
    # Recent station activities
    recent_activities = get_recent_station_activities(location, days=7)
    
    # Station pending items
    pending_items = get_station_pending_items(location)
    
    # Week performance
    week_performance = get_station_week_performance(location)
    
    # Staff alerts (birthdays, anniversaries, etc.)
    staff_alerts = get_station_staff_alerts(location)
    
    # Equipment/facility status (placeholder for future enhancement)
    facility_status = get_station_facility_status(location)
    
    return render_template('dashboard/station_overview.html',
                         location=location,
                         station_employees=station_employees,
                         station_attendance=station_attendance,
                         shift_breakdown=shift_breakdown,
                         recent_activities=recent_activities,
                         pending_items=pending_items,
                         week_performance=week_performance,
                         staff_alerts=staff_alerts,
                         facility_status=facility_status,
                         today=today)

@dashboard_bp.route('/attendance-details')
@login_required
def attendance_details():
    """Enhanced detailed attendance view with advanced filtering"""
    target_date_str = request.args.get('date', date.today().isoformat())
    location_filter = request.args.get('location', 'all')
    shift_filter = request.args.get('shift', 'all')
    status_filter = request.args.get('status', 'all')
    department_filter = request.args.get('department', 'all')
    
    try:
        target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
    except ValueError:
        target_date = date.today()
    
    # Build query based on user permissions
    query = db.session.query(
        Employee.id,
        Employee.employee_id,
        Employee.first_name,
        Employee.last_name,
        Employee.location,
        Employee.department,
        Employee.position,
        Employee.shift,
        AttendanceRecord.status,
        AttendanceRecord.clock_in,
        AttendanceRecord.clock_out,
        AttendanceRecord.notes,
        AttendanceRecord.hours_worked,
        AttendanceRecord.late_minutes,
        AttendanceRecord.overtime_hours
    ).outerjoin(
        AttendanceRecord,
        and_(
            AttendanceRecord.employee_id == Employee.id,
            AttendanceRecord.date == target_date
        )
    ).filter(Employee.is_active == True)
    
    # Apply location filter based on user role
    if current_user.role == 'station_manager':
        query = query.filter(Employee.location == current_user.location)
    elif location_filter != 'all':
        query = query.filter(Employee.location == location_filter)
    
    # Apply additional filters
    if shift_filter != 'all':
        query = query.filter(Employee.shift == shift_filter)
    
    if department_filter != 'all':
        query = query.filter(Employee.department == department_filter)
    
    if status_filter != 'all':
        if status_filter == 'not_marked':
            query = query.filter(AttendanceRecord.status.is_(None))
        elif status_filter == 'present_late':
            query = query.filter(AttendanceRecord.status.in_(['present', 'late']))
        elif status_filter == 'on_leave':
            query = query.filter(AttendanceRecord.status.like('%leave%'))
        else:
            query = query.filter(AttendanceRecord.status == status_filter)
    
    # Order results
    query = query.order_by(Employee.location, Employee.department, Employee.first_name)
    
    attendance_details = query.all()
    
    # Get summary statistics
    summary_stats = calculate_attendance_summary(attendance_details)
    
    # Get available filter options
    filter_options = get_attendance_filter_options(current_user)
    
    return render_template('dashboard/attendance_details.html',
                         attendance_details=attendance_details,
                         summary_stats=summary_stats,
                         filter_options=filter_options,
                         target_date=target_date,
                         location_filter=location_filter,
                         shift_filter=shift_filter,
                         status_filter=status_filter,
                         department_filter=department_filter)

@dashboard_bp.route('/analytics')
@login_required
def analytics():
    """Advanced analytics dashboard"""
    if current_user.role not in ['hr_manager', 'admin']:
        flash('Access denied. HR Manager privileges required.', 'danger')
        return redirect(url_for('dashboard.main'))
    
    # Date range from request (default: last 30 days)
    end_date = datetime.strptime(request.args.get('end_date', date.today().isoformat()), '%Y-%m-%d').date()
    start_date = datetime.strptime(request.args.get('start_date', (end_date - timedelta(days=30)).isoformat()), '%Y-%m-%d').date()
    
    # Attendance trend analysis
    attendance_trends = get_attendance_trend_analysis(start_date, end_date)
    
    # Leave utilization analysis
    leave_analytics = get_leave_utilization_analytics(start_date, end_date)
    
    # Department performance comparison
    department_comparison = get_department_performance_comparison(start_date, end_date)
    
    # Location efficiency metrics
    location_metrics = get_location_efficiency_metrics(start_date, end_date)
    
    # Employee productivity insights
    productivity_insights = get_employee_productivity_insights(start_date, end_date)
    
    # Cost analysis
    cost_analysis = get_attendance_cost_analysis(start_date, end_date)
    
    return render_template('dashboard/analytics.html',
                         attendance_trends=attendance_trends,
                         leave_analytics=leave_analytics,
                         department_comparison=department_comparison,
                         location_metrics=location_metrics,
                         productivity_insights=productivity_insights,
                         cost_analysis=cost_analysis,
                         start_date=start_date,
                         end_date=end_date)

# Helper Functions

def get_comprehensive_attendance_overview(target_date):
    """Get comprehensive attendance overview for all locations"""
    from config import Config
    locations = Config.COMPANY_LOCATIONS
    overview = OrderedDict()
    
    for location_key, location_info in locations.items():
        location_data = {
            'name': location_info['name'],
            'total_employees': 0,
            'present': 0,
            'absent': 0,
            'late': 0,
            'on_leave': 0,
            'not_marked': 0,
            'attendance_rate': 0,
            'shifts': {}
        }
        
        # Process shifts if location has them
        if 'shifts' in location_info:
            for shift in location_info['shifts']:
                shift_data = get_shift_attendance_data(location_key, shift, target_date)
                location_data['shifts'][shift] = shift_data
                
                # Aggregate to location totals
                location_data['total_employees'] += shift_data['total_employees']
                location_data['present'] += shift_data['present']
                location_data['absent'] += shift_data['absent']
                location_data['late'] += shift_data['late']
                location_data['on_leave'] += shift_data['on_leave']
                location_data['not_marked'] += shift_data['not_marked']
        else:
            # No shifts (like head office)
            shift_data = get_shift_attendance_data(location_key, None, target_date)
            location_data.update(shift_data)
        
        # Calculate attendance rate
        if location_data['total_employees'] > 0:
            location_data['attendance_rate'] = round(
                (location_data['present'] / location_data['total_employees']) * 100, 1
            )
        
        overview[location_key] = location_data
    
    return overview

def get_shift_attendance_data(location, shift, target_date):
    """Get attendance data for specific location and shift"""
    # Base employee query
    employee_query = Employee.query.filter(
        Employee.location == location,
        Employee.is_active == True
    )
    
    if shift:
        employee_query = employee_query.filter(Employee.shift == shift)
    
    employees = employee_query.all()
    total_employees = len(employees)
    
    # Initialize counters
    present = absent = late = on_leave = not_marked = 0
    
    for employee in employees:
        # Get attendance record
        attendance = AttendanceRecord.query.filter(
            AttendanceRecord.employee_id == employee.id,
            AttendanceRecord.date == target_date
        ).first()
        
        # Check for approved leave
        leave_request = LeaveRequest.query.filter(
            LeaveRequest.employee_id == employee.id,
            LeaveRequest.start_date <= target_date,
            LeaveRequest.end_date >= target_date,
            LeaveRequest.status == 'approved'
        ).first()
        
        if leave_request:
            on_leave += 1
        elif attendance:
            if attendance.status == 'present':
                present += 1
            elif attendance.status == 'late':
                present += 1
                late += 1
            elif attendance.status == 'absent':
                absent += 1
            elif 'leave' in attendance.status:
                on_leave += 1
        else:
            not_marked += 1
    
    return {
        'total_employees': total_employees,
        'present': present,
        'absent': absent,
        'late': late,
        'on_leave': on_leave,
        'not_marked': not_marked,
        'attendance_rate': round((present / total_employees * 100), 1) if total_employees > 0 else 0
    }

def get_recent_hr_activities(days=7):
    """Get recent HR-relevant activities"""
    since_date = datetime.utcnow() - timedelta(days=days)
    
    activities = AuditLog.query.filter(
        AuditLog.timestamp >= since_date,
        AuditLog.action.in_([
            'employee_created', 'employee_updated', 'leave_approved', 
            'leave_rejected', 'attendance_corrected', 'user_created'
        ])
    ).order_by(AuditLog.timestamp.desc()).limit(20).all()
    
    return activities

def get_pending_hr_approvals():
    """Get items pending HR approval"""
    pending = {}
    
    # Pending leave requests
    pending['leave_requests'] = LeaveRequest.query.filter(
        LeaveRequest.status == 'pending'
    ).count()
    
    # Employees requiring confirmation after probation
    pending['probation_confirmations'] = Employee.query.filter(
        Employee.employment_status == 'probation',
        Employee.probation_end_date <= date.today(),
        Employee.is_active == True
    ).count()
    
    # Performance reviews due
    pending['performance_reviews'] = get_overdue_performance_reviews_count()
    
    # Attendance corrections requiring approval
    pending['attendance_corrections'] = AttendanceRecord.query.filter(
        AttendanceRecord.requires_approval == True,
        AttendanceRecord.approved_by.is_(None)
    ).count()
    
    return pending

def get_department_statistics():
    """Get employee statistics by department"""
    from config import Config
    departments = Config.DEPARTMENTS
    
    stats = {}
    for dept_key, dept_info in departments.items():
        employee_count = Employee.query.filter(
            Employee.department == dept_key,
            Employee.is_active == True
        ).count()
        
        # Get today's attendance for this department
        today = date.today()
        present_count = db.session.query(AttendanceRecord).join(Employee).filter(
            Employee.department == dept_key,
            Employee.is_active == True,
            AttendanceRecord.date == today,
            AttendanceRecord.status.in_(['present', 'late'])
        ).count()
        
        stats[dept_key] = {
            'name': dept_info['name'],
            'total_employees': employee_count,
            'present_today': present_count,
            'attendance_rate': round((present_count / employee_count * 100), 1) if employee_count > 0 else 0,
            'color': dept_info.get('color', '#6c757d')
        }
    
    return stats

def get_location_performance_metrics():
    """Get performance metrics by location"""
    locations = ['head_office', 'dandora', 'tassia', 'kiambu']
    metrics = {}
    
    # Last 30 days
    end_date = date.today()
    start_date = end_date - timedelta(days=30)
    
    for location in locations:
        # Calculate average attendance rate
        daily_rates = []
        current_date = start_date
        
        while current_date <= end_date:
            if current_date.weekday() < 5:  # Weekdays only
                location_data = get_shift_attendance_data(location, None, current_date)
                if location_data['total_employees'] > 0:
                    daily_rates.append(location_data['attendance_rate'])
            current_date += timedelta(days=1)
        
        avg_attendance = round(sum(daily_rates) / len(daily_rates), 1) if daily_rates else 0
        
        # Get employee satisfaction placeholder (would come from surveys)
        satisfaction_score = 85  # Placeholder
        
        # Get incident count (placeholder)
        incident_count = 2  # Placeholder
        
        metrics[location] = {
            'avg_attendance_rate': avg_attendance,
            'satisfaction_score': satisfaction_score,
            'incident_count': incident_count,
            'performance_trend': 'improving' if avg_attendance > 85 else 'stable'
        }
    
    return metrics

def get_compliance_alerts():
    """Get compliance-related alerts"""
    alerts = []
    
    # Employees exceeding leave limits
    current_year = date.today().year
    year_start = date(current_year, 1, 1)
    year_end = date(current_year, 12, 31)
    
    # Check for employees who might be exceeding annual leave
    excessive_leave = db.session.query(
        LeaveRequest.employee_id,
        func.sum(LeaveRequest.days_requested)
    ).filter(
        LeaveRequest.leave_type == 'annual_leave',
        LeaveRequest.status == 'approved',
        LeaveRequest.start_date >= year_start,
        LeaveRequest.end_date <= year_end
    ).group_by(LeaveRequest.employee_id).having(
        func.sum(LeaveRequest.days_requested) > 21
    ).all()
    
    if excessive_leave:
        alerts.append({
            'type': 'warning',
            'title': 'Annual Leave Compliance',
            'message': f'{len(excessive_leave)} employees have exceeded annual leave limits',
            'action_url': url_for('dashboard.compliance_report')
        })
    
    # Employees with long absence streaks
    long_absences = get_employees_with_long_absences()
    if long_absences:
        alerts.append({
            'type': 'danger',
            'title': 'Excessive Absences',
            'message': f'{len(long_absences)} employees have been absent for 5+ consecutive days',
            'action_url': url_for('dashboard.absence_report')
        })
    
    return alerts

def get_monthly_attendance_trends():
    """Get attendance trends for the last 6 months"""
    today = date.today()
    trends = []
    
    for i in range(6):
        # Calculate month start and end
        if today.month - i <= 0:
            month = 12 + (today.month - i)
            year = today.year - 1
        else:
            month = today.month - i
            year = today.year
        
        month_start = date(year, month, 1)
        if month == 12:
            month_end = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            month_end = date(year, month + 1, 1) - timedelta(days=1)
        
        # Calculate average attendance for the month
        month_avg = calculate_monthly_attendance_average(month_start, month_end)
        
        trends.append({
            'month': calendar.month_name[month],
            'year': year,
            'attendance_rate': month_avg,
            'date': month_start
        })
    
    return list(reversed(trends))

def calculate_monthly_attendance_average(start_date, end_date):
    """Calculate average attendance rate for a date range"""
    daily_rates = []
    current_date = start_date
    
    while current_date <= end_date:
        if current_date.weekday() < 5:  # Weekdays only
            total_employees = Employee.query.filter(Employee.is_active == True).count()
            present_count = db.session.query(AttendanceRecord).join(Employee).filter(
                AttendanceRecord.date == current_date,
                Employee.is_active == True,
                AttendanceRecord.status.in_(['present', 'late'])
            ).count()
            
            if total_employees > 0:
                daily_rates.append((present_count / total_employees) * 100)
        
        current_date += timedelta(days=1)
    
    return round(sum(daily_rates) / len(daily_rates), 1) if daily_rates else 0

def get_upcoming_work_anniversaries():
    """Get employees with upcoming work anniversaries"""
    today = date.today()
    next_30_days = today + timedelta(days=30)
    
    employees = Employee.query.filter(
        Employee.is_active == True,
        func.date_part('month', Employee.hire_date) == today.month,
        func.date_part('day', Employee.hire_date) >= today.day
    ).order_by(Employee.hire_date).limit(10).all()
    
    anniversaries = []
    for employee in employees:
        years_of_service = (today - employee.hire_date).days // 365
        if years_of_service > 0:  # Don't include first year
            anniversary_date = date(today.year, employee.hire_date.month, employee.hire_date.day)
            if anniversary_date >= today:
                anniversaries.append({
                    'employee': employee,
                    'years': years_of_service,
                    'date': anniversary_date
                })
    
    return anniversaries

def get_performance_reviews_due():
    """Get performance reviews that are due"""
    # This would check for employees who haven't had a review in the last year
    one_year_ago = date.today() - timedelta(days=365)
    
    employees_due = Employee.query.outerjoin(PerformanceReview).filter(
        Employee.is_active == True,
        or_(
            PerformanceReview.id.is_(None),  # Never had a review
            PerformanceReview.review_period_end < one_year_ago  # Last review was over a year ago
        )
    ).limit(10).all()
    
    return employees_due

def get_overdue_performance_reviews_count():
    """Count overdue performance reviews"""
    one_year_ago = date.today() - timedelta(days=365)
    
    return Employee.query.outerjoin(PerformanceReview).filter(
        Employee.is_active == True,
        Employee.employment_status == 'permanent',
        or_(
            PerformanceReview.id.is_(None),
            PerformanceReview.review_period_end < one_year_ago
        )
    ).count()

def get_employees_with_long_absences():
    """Get employees with consecutive absences of 5+ days"""
    # This is a simplified version - in practice, you'd need more complex logic
    # to detect consecutive absences
    recent_date = date.today() - timedelta(days=5)
    
    frequent_absent = db.session.query(
        AttendanceRecord.employee_id,
        func.count(AttendanceRecord.id)
    ).filter(
        AttendanceRecord.date >= recent_date,
        AttendanceRecord.status == 'absent'
    ).group_by(AttendanceRecord.employee_id).having(
        func.count(AttendanceRecord.id) >= 5
    ).all()
    
    return [emp_id for emp_id, count in frequent_absent]

def calculate_attendance_summary(attendance_details):
    """Calculate summary statistics from attendance details"""
    total = len(attendance_details)
    present = sum(1 for detail in attendance_details if detail.status in ['present', 'late'])
    absent = sum(1 for detail in attendance_details if detail.status == 'absent')
    on_leave = sum(1 for detail in attendance_details if detail.status and 'leave' in detail.status)
    not_marked = sum(1 for detail in attendance_details if not detail.status)
    late = sum(1 for detail in attendance_details if detail.status == 'late')
    
    return {
        'total': total,
        'present': present,
        'absent': absent,
        'on_leave': on_leave,
        'not_marked': not_marked,
        'late': late,
        'attendance_rate': round((present / total * 100), 1) if total > 0 else 0
    }

def get_attendance_filter_options(user):
    """Get available filter options based on user role"""
    options = {
        'locations': [],
        'shifts': ['all', 'day', 'night'],
        'departments': [],
        'statuses': [
            'all', 'present', 'absent', 'late', 'present_late', 
            'on_leave', 'not_marked'
        ]
    }
    
    # Locations based on role
    if user.role == 'hr_manager':
        options['locations'] = ['all', 'head_office', 'dandora', 'tassia', 'kiambu']
    elif user.role == 'station_manager':
        options['locations'] = [user.location]
    
    # Departments
    from config import Config
    departments = Config.DEPARTMENTS
    options['departments'] = ['all'] + list(departments.keys())
    
    return options

# Station-specific helper functions
def get_station_attendance_overview(location, target_date):
    """Get attendance overview for specific station"""
    return get_shift_attendance_data(location, None, target_date)

def get_station_shift_breakdown(location, target_date):
    """Get shift breakdown for station"""
    from config import Config
    location_info = Config.COMPANY_LOCATIONS.get(location, {})
    shifts = location_info.get('shifts', [])
    
    breakdown = {}
    for shift in shifts:
        breakdown[shift] = get_shift_attendance_data(location, shift, target_date)
    
    return breakdown

def get_recent_station_activities(location, days=7):
    """Get recent activities for specific station"""
    since_date = datetime.utcnow() - timedelta(days=days)
    
    # Get activities related to employees at this location
    employee_ids = [emp.id for emp in Employee.query.filter(
        Employee.location == location,
        Employee.is_active == True
    ).all()]
    
    activities = AuditLog.query.filter(
        AuditLog.timestamp >= since_date,
        or_(
            AuditLog.target_id.in_(employee_ids),
            AuditLog.location_context == location
        )
    ).order_by(AuditLog.timestamp.desc()).limit(10).all()
    
    return activities

def get_station_pending_items(location):
    """Get pending items for specific station"""
    pending = {}
    
    # Pending leave requests for this station
    pending['leave_requests'] = db.session.query(LeaveRequest).join(Employee).filter(
        Employee.location == location,
        LeaveRequest.status == 'pending'
    ).count()
    
    # Unmarked attendance today
    today = date.today()
    total_employees = Employee.query.filter(
        Employee.location == location,
        Employee.is_active == True
    ).count()
    
    marked_today = db.session.query(AttendanceRecord).join(Employee).filter(
        AttendanceRecord.date == today,
        Employee.location == location,
        Employee.is_active == True
    ).count()
    
    pending['unmarked_attendance'] = total_employees - marked_today
    
    return pending

def get_station_week_performance(location):
    """Get performance metrics for the current week"""
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    
    daily_performance = []
    for i in range(7):
        day = week_start + timedelta(days=i)
        if day <= today:
            performance = get_shift_attendance_data(location, None, day)
            daily_performance.append({
                'date': day,
                'day_name': day.strftime('%A'),
                'attendance_rate': performance['attendance_rate'],
                'present': performance['present'],
                'total': performance['total_employees']
            })
    
    return daily_performance

def get_station_staff_alerts(location):
    """Get staff alerts for specific station (birthdays, anniversaries, etc.)"""
    alerts = []
    
    # Upcoming birthdays (if birth dates are stored)
    # This would require adding birth_date to Employee model
    
    # Work anniversaries this month
    today = date.today()
    anniversaries = Employee.query.filter(
        Employee.location == location,
        Employee.is_active == True,
        func.extract('month', Employee.hire_date) == today.month
    ).all()
    
    for emp in anniversaries:
        years = (today - emp.hire_date).days // 365
        if years > 0:
            alerts.append({
                'type': 'anniversary',
                'employee': emp,
                'message': f'{emp.full_name} celebrates {years} year{"s" if years != 1 else ""} of service this month'
            })
    
    return alerts

def get_station_facility_status(location):
    """Get facility/equipment status for station (placeholder for future)"""
    # This would integrate with facility management systems
    return {
        'overall_status': 'operational',
        'equipment_alerts': 0,
        'maintenance_due': 1,
        'safety_compliance': 'good'
    }

# API endpoints for real-time updates
@dashboard_bp.route('/api/live-stats')
@login_required
def api_live_stats():
    """Get real-time statistics for dashboard updates"""
    try:
        today = date.today()
        
        if current_user.role == 'hr_manager':
            overview = get_comprehensive_attendance_overview(today)
            return jsonify({
                'success': True,
                'data': overview,
                'timestamp': datetime.utcnow().isoformat()
            })
        elif current_user.role == 'station_manager':
            station_data = get_station_attendance_overview(current_user.location, today)
            return jsonify({
                'success': True,
                'data': {current_user.location: station_data},
                'timestamp': datetime.utcnow().isoformat()
            })
        else:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@dashboard_bp.route('/api/quick-metrics')
@login_required
def api_quick_metrics():
    """Get quick metrics for dashboard cards"""
    try:
        today = date.today()
        
        # Base employee count
        if current_user.role == 'station_manager':
            total_employees = Employee.query.filter(
                Employee.location == current_user.location,
                Employee.is_active == True
            ).count()
        else:
            total_employees = Employee.query.filter(Employee.is_active == True).count()
        
        # Today's basic stats
        if current_user.role == 'station_manager':
            station_stats = get_station_attendance_overview(current_user.location, today)
            return jsonify({
                'success': True,
                'metrics': {
                    'total_employees': total_employees,
                    'present_today': station_stats['present'],
                    'absent_today': station_stats['absent'],
                    'not_marked': station_stats['not_marked'],
                    'attendance_rate': station_stats['attendance_rate']
                }
            })
        else:
            overview = get_comprehensive_attendance_overview(today)
            total_present = sum(loc['present'] for loc in overview.values())
            total_absent = sum(loc['absent'] for loc in overview.values())
            total_not_marked = sum(loc['not_marked'] for loc in overview.values())
            
            return jsonify({
                'success': True,
                'metrics': {
                    'total_employees': total_employees,
                    'present_today': total_present,
                    'absent_today': total_absent,
                    'not_marked': total_not_marked,
                    'attendance_rate': round((total_present / total_employees * 100), 1) if total_employees > 0 else 0
                }
            })
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500