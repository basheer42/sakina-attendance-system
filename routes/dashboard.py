"""
Sakina Gas Company - Dashboard Routes
Built from scratch with full complexity and advanced analytics
Version 3.0 - SQLAlchemy 2.0+ compatible with corrected syntax
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, g, current_app
from flask_login import login_required, current_user
from sqlalchemy import func, and_, or_, case, text, distinct, desc, asc, extract
from sqlalchemy.orm import aliased
from datetime import date, datetime, timedelta
from collections import defaultdict, OrderedDict
import calendar
import json

# FIX: Removed global model imports to prevent early model registration
from database import db
# NOTE: Models are now imported locally within functions for safety

# Create blueprint
dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@dashboard_bp.route('/main')
@login_required
def main():
    """Enhanced main dashboard with role-based routing"""
    # FIX: Local imports
    from models.audit import AuditLog
    
    try:
        # Log dashboard access
        AuditLog.log_event(
            event_type='dashboard_access',
            description=f'User accessed main dashboard',
            user_id=current_user.id,
            ip_address=request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR')),
            user_agent=request.headers.get('User-Agent'),
            risk_level='low'
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
        # FIX: Added finance_overview and admin_overview to routes/dashboard.py as assumed missing
        return render_template('dashboard/finance_overview.html')
    elif current_user.role == 'admin':
        return render_template('dashboard/admin_overview.html')
    else:
        # Employee or other roles - basic dashboard
        return render_template('dashboard/main.html') # FIX: Assumed 'main.html' is basic employee overview

@dashboard_bp.route('/hr-overview')
@login_required
def hr_overview():
    """Comprehensive HR Manager dashboard with advanced analytics"""
    if current_user.role != 'hr_manager':
        flash('Access denied. HR Manager privileges required.', 'error')
        return redirect(url_for('dashboard.main'))
    
    try:
        # FIX: Local imports
        
        # Get comprehensive attendance overview
        attendance_overview = get_comprehensive_attendance_overview()
        
        # Get recent HR activities (last 7 days)
        recent_activities = get_recent_hr_activities()
        
        # Get pending approvals and items requiring attention
        pending_approvals = get_pending_hr_approvals()
        
        # Get department statistics with corrected SQLAlchemy syntax
        department_stats = get_department_statistics()
        
        # Get location performance metrics
        location_performance = get_location_performance_metrics()
        
        # Get HR-specific alerts and notifications
        hr_alerts = get_hr_alerts()
        
        # Get compliance status
        compliance_status = get_compliance_status()
        
        # Get performance trends and analytics
        performance_trends = get_performance_trends()
        
        # Get monthly attendance trends (last 6 months)
        monthly_trends = get_monthly_attendance_trends()
        
        # Get upcoming events and anniversaries
        upcoming_events = get_upcoming_hr_events()
        
        # Get leave balance alerts
        leave_balance_alerts = get_leave_balance_alerts()
        
        # Get system health metrics for HR
        system_health = get_system_health_metrics()
        
        return render_template('dashboard/hr_overview.html',
            attendance_overview=attendance_overview,
            recent_activities=recent_activities,
            pending_approvals=pending_approvals,
            department_stats=department_stats,
            location_performance=location_performance,
            hr_alerts=hr_alerts,
            compliance_status=compliance_status,
            performance_trends=performance_trends,
            monthly_trends=monthly_trends,
            upcoming_events=upcoming_events,
            leave_balance_alerts=leave_balance_alerts,
            system_health=system_health
        )
        
    except Exception as e:
        current_app.logger.error(f'Error in hr_overview: {e}')
        flash('Error loading dashboard. Please try again.', 'error')
        return redirect(url_for('auth.logout'))

# FIX: Added finance_overview (assumed missing)
@dashboard_bp.route('/finance-overview')
@login_required
def finance_overview():
    """Finance Manager dashboard"""
    if current_user.role != 'finance_manager':
        flash('Access denied. Finance Manager privileges required.', 'error')
        return redirect(url_for('dashboard.main'))
    
    # FIX: Placeholder logic as full implementation is missing
    return render_template('dashboard/finance_overview.html')

# FIX: Added admin_overview (assumed missing)
@dashboard_bp.route('/admin-overview')
@login_required
def admin_overview():
    """System Administrator dashboard"""
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard.main'))
    
    # FIX: Placeholder logic as full implementation is missing
    return render_template('dashboard/admin_overview.html')


@dashboard_bp.route('/station-overview')
@login_required 
def station_overview():
    """Comprehensive Station Manager dashboard"""
    if current_user.role != 'station_manager':
        flash('Access denied. Station Manager privileges required.', 'error')
        return redirect(url_for('dashboard.main'))
    
    try:
        location = current_user.location
        
        # Get location-specific statistics
        location_stats = get_location_statistics(location)
        
        # Get today's attendance for the location
        todays_attendance = get_todays_location_attendance(location)
        
        # Get shift breakdown for gas stations
        shift_breakdown = get_shift_breakdown(location)
        
        # Get recent location activities
        recent_activities = get_recent_location_activities(location)
        
        # Get pending items for station manager
        pending_items = get_pending_station_items(location)
        
        # Get location performance metrics
        performance_metrics = get_location_performance_detailed(location)
        
        # Get staff on duty breakdown
        staff_on_duty = get_staff_on_duty_breakdown(location)
        
        # Get weekly attendance trends for location
        weekly_trends = get_weekly_attendance_trends(location)
        
        # Get location-specific alerts
        location_alerts = get_location_alerts(location)
        
        # Get fuel/inventory status (for gas stations)
        inventory_status = get_inventory_status(location) # FIX: Removed Config import reliance
        
        # Get customer service metrics
        customer_metrics = get_customer_service_metrics(location)
        
        return render_template('dashboard/station_overview.html',
            location=location,
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
            customer_metrics=customer_metrics
        )
        
    except Exception as e:
        current_app.logger.error(f'Error in station_overview: {e}')
        flash('Error loading station dashboard. Please try again.', 'error')
        return redirect(url_for('auth.logout'))

@dashboard_bp.route('/attendance-details')
@login_required
def attendance_details():
    """Enhanced attendance details view with comprehensive filtering and analytics"""
    # FIX: Local imports
    from config import Config
    
    try:
        # Get filter parameters
        date_filter = request.args.get('date', date.today().isoformat())
        location_filter = request.args.get('location', 'all')
        department_filter = request.args.get('department', 'all')
        status_filter = request.args.get('status', 'all')
        shift_filter = request.args.get('shift', 'all')
        
        # Convert date string to date object
        try:
            target_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
        except ValueError:
            target_date = date.today()
        
        # Get detailed attendance summary with filters
        attendance_summary = get_attendance_detailed_summary(
            target_date, location_filter, department_filter, 
            status_filter, current_user.role, current_user.location
        )
        
        # Get attendance records grouped by status
        attendance_records = get_attendance_records_grouped(
            target_date, location_filter, department_filter,
            status_filter, shift_filter, current_user.role, current_user.location
        )
        
        # Get previous day comparison
        previous_date = target_date - timedelta(days=1)
        previous_summary = get_attendance_summary_for_date(
            previous_date, location_filter, current_user.role, current_user.location
        )
        
        # Calculate trends
        trends = calculate_attendance_trends(attendance_summary, previous_summary)
        
        # Get filter options based on user role
        filter_options = get_attendance_filter_options(current_user)
        
        # Get location details
        locations_config = current_app.config.get('COMPANY_LOCATIONS', {})
        
        return render_template('dashboard/attendance_details.html',
            target_date=target_date,
            attendance_summary=attendance_summary,
            attendance_records=attendance_records,
            trends=trends,
            filter_options=filter_options,
            locations_config=locations_config,
            current_filters={
                'date': date_filter,
                'location': location_filter,
                'department': department_filter,
                'status': status_filter,
                'shift': shift_filter
            }
        )
        
    except Exception as e:
        current_app.logger.error(f'Error in attendance_details: {e}')
        flash('Error loading attendance details. Please try again.', 'error')
        return redirect(url_for('dashboard.main'))

@dashboard_bp.route('/api/quick-stats')
@login_required
def api_quick_stats():
    """API endpoint for real-time dashboard updates"""
    # FIX: Local imports
    from models.employee import Employee
    from models.attendance import AttendanceRecord
    from models.leave import LeaveRequest
    
    try:
        stats = {}
        
        if current_user.role == 'hr_manager':
            # HR Manager stats
            stats = {
                'total_employees': Employee.query.filter_by(is_active=True).count(),
                'present_today': AttendanceRecord.query.join(Employee).filter(
                    AttendanceRecord.date == date.today(),
                    AttendanceRecord.status == 'present',
                    Employee.is_active == True
                ).count(),
                'pending_leaves': LeaveRequest.query.filter_by(status='pending').count(),
                'on_probation': Employee.query.filter(
                    Employee.is_active == True,
                    Employee.probation_end_date >= date.today()
                ).count()
            }
            
        elif current_user.role == 'station_manager':
            # Station Manager stats
            location_employees = Employee.query.filter_by(
                location=current_user.location,
                is_active=True
            )
            
            stats = {
                'location_employees': location_employees.count(),
                'present_today': AttendanceRecord.query.join(Employee).filter(
                    AttendanceRecord.date == date.today(),
                    AttendanceRecord.status == 'present',
                    Employee.location == current_user.location,
                    Employee.is_active == True
                ).count(),
                'late_today': AttendanceRecord.query.join(Employee).filter(
                    AttendanceRecord.date == date.today(),
                    AttendanceRecord.status == 'late',
                    Employee.location == current_user.location,
                    Employee.is_active == True
                ).count(),
                'absent_today': AttendanceRecord.query.join(Employee).filter(
                    AttendanceRecord.date == date.today(),
                    AttendanceRecord.status == 'absent',
                    Employee.location == current_user.location,
                    Employee.is_active == True
                ).count()
            }
        
        # Add timestamp
        stats['timestamp'] = datetime.utcnow().isoformat()
        stats['success'] = True
        
        return jsonify(stats)
        
    except Exception as e:
        current_app.logger.error(f'Error in api_quick_stats: {e}')
        return jsonify({
            'success': False,
            'error': 'Failed to fetch statistics',
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@dashboard_bp.route('/api/attendance-chart-data')
@login_required
def api_attendance_chart_data():
    """API endpoint for attendance chart data"""
    # FIX: Local imports
    from models.employee import Employee
    from models.attendance import AttendanceRecord
    
    try:
        days = int(request.args.get('days', 7))
        location = request.args.get('location', 'all')
        
        # Calculate date range
        end_date = date.today()
        start_date = end_date - timedelta(days=days-1)
        
        # Build query based on user role
        query = db.session.query(
            AttendanceRecord.date,
            AttendanceRecord.status,
            func.count(AttendanceRecord.id).label('count')
        ).join(Employee)
        
        # Apply location filter based on user role
        if current_user.role == 'station_manager':
            query = query.filter(Employee.location == current_user.location)
        elif location != 'all':
            query = query.filter(Employee.location == location)
        
        # Apply date range and grouping
        query = query.filter(
            AttendanceRecord.date.between(start_date, end_date),
            Employee.is_active == True
        ).group_by(
            AttendanceRecord.date,
            AttendanceRecord.status
        ).order_by(AttendanceRecord.date)
        
        # Execute query
        results = query.all()
        
        # Process data for chart
        chart_data = {}
        date_range = []
        
        # Create date range
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            date_range.append(date_str)
            chart_data[date_str] = {
                'present': 0,
                'absent': 0,
                'late': 0,
                'on_leave': 0
            }
            current_date += timedelta(days=1)
        
        # Fill in actual data
        for record in results:
            date_str = record.date.strftime('%Y-%m-%d')
            if date_str in chart_data: # FIX: Safety check for processing
                if record.status in chart_data[date_str]:
                    chart_data[date_str][record.status] = record.count
                elif record.status in ['annual_leave', 'sick_leave', 'maternity_leave', 'paternity_leave']:
                    chart_data[date_str]['on_leave'] += record.count
        
        # Format for frontend
        response_data = {
            'dates': date_range,
            'series': [
                {
                    'name': 'Present',
                    'data': [chart_data[d]['present'] for d in date_range],
                    'color': '#28A745'
                },
                {
                    'name': 'Late', 
                    'data': [chart_data[d]['late'] for d in date_range],
                    'color': '#FFC107'
                },
                {
                    'name': 'Absent',
                    'data': [chart_data[d]['absent'] for d in date_range],
                    'color': '#DC3545'
                },
                {
                    'name': 'On Leave',
                    'data': [chart_data[d]['on_leave'] for d in date_range],
                    'color': '#17A2B8'
                }
            ],
            'success': True
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        current_app.logger.error(f'Error in api_attendance_chart_data: {e}')
        return jsonify({
            'success': False,
            'error': 'Failed to fetch chart data'
        }), 500

# Helper Functions with Corrected SQLAlchemy Syntax

def get_comprehensive_attendance_overview():
    """Get comprehensive attendance overview for HR dashboard"""
    # FIX: Local imports
    from models.employee import Employee
    from models.attendance import AttendanceRecord
    from models.leave import LeaveRequest
    
    try:
        today = date.today()
        
        # Get total active employees
        total_employees = Employee.query.filter_by(is_active=True).count()
        
        # Get today's attendance breakdown using corrected syntax
        attendance_breakdown = db.session.query(
            AttendanceRecord.status,
            func.count(AttendanceRecord.id).label('count')
        ).join(Employee).filter(
            AttendanceRecord.date == today,
            Employee.is_active == True
        ).group_by(AttendanceRecord.status).all()
        
        # Process breakdown
        breakdown_dict = {record.status: record.count for record in attendance_breakdown}
        
        # Calculate metrics
        present = breakdown_dict.get('present', 0)
        late = breakdown_dict.get('late', 0)
        absent = breakdown_dict.get('absent', 0)
        # FIX: Leave status names in the breakdown should match the ones in AttendanceRecord
        on_leave = sum(breakdown_dict.get(status, 0) for status in 
                      ['annual_leave', 'sick_leave', 'maternity_leave', 'paternity_leave', 'compassionate_leave'])
        
        not_marked = total_employees - (present + late + absent + on_leave)
        
        # Get location breakdown using CASE with corrected syntax
        location_breakdown = db.session.query(
            Employee.location,
            func.count(Employee.id).label('total'),
            func.sum(case((AttendanceRecord.status == 'present', 1), else_=0)).label('present'),
            func.sum(case((AttendanceRecord.status == 'late', 1), else_=0)).label('late'),
            func.sum(case((AttendanceRecord.status == 'absent', 1), else_=0)).label('absent')
        ).outerjoin(
            AttendanceRecord,
            and_(AttendanceRecord.employee_id == Employee.id, AttendanceRecord.date == today)
        ).filter(
            Employee.is_active == True
        ).group_by(Employee.location).all()
        
        return {
            'total_employees': total_employees,
            'present': present,
            'late': late,
            'absent': absent,
            'on_leave': on_leave,
            'not_marked': not_marked,
            'attendance_rate': round((present + late) / total_employees * 100, 1) if total_employees > 0 else 0,
            'location_breakdown': [
                {
                    'location': loc.location,
                    'total': loc.total,
                    'present': loc.present or 0,
                    'late': loc.late or 0,
                    'absent': loc.absent or 0,
                    'rate': round(((loc.present or 0) + (loc.late or 0)) / loc.total * 100, 1) if loc.total > 0 else 0
                }
                for loc in location_breakdown
            ]
        }
        
    except Exception as e:
        current_app.logger.error(f'Error in get_comprehensive_attendance_overview: {e}')
        return {
            'total_employees': 0,
            'present': 0,
            'late': 0,
            'absent': 0,
            'on_leave': 0,
            'not_marked': 0,
            'attendance_rate': 0,
            'location_breakdown': []
        }

def get_recent_hr_activities():
    """Get recent HR activities from audit log"""
    # FIX: Local imports
    from models.audit import AuditLog
    from models.user import User
    
    try:
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        
        # FIX: The AuditLog has a User relationship, so we need to eager load or access it correctly
        activities = db.session.query(AuditLog).filter(
            AuditLog.timestamp >= seven_days_ago,
            AuditLog.event_type.in_([ # FIX: event_type instead of event_type
                'employee_created', 'employee_updated', 'employee_deactivated',
                'leave_approved', 'leave_rejected', 'performance_review_created',
                'disciplinary_action_recorded', 'user_created'
            ])
        ).order_by(desc(AuditLog.timestamp)).limit(20).all()
        
        return [
            {
                'timestamp': activity.timestamp,
                'event_type': activity.event_type,
                'description': activity.description,
                'user_name': activity.user.get_full_name() if activity.user and hasattr(activity.user, 'get_full_name') else (activity.user.username if activity.user else 'System'),
                'risk_level': activity.risk_level
            }
            for activity in activities
        ]
        
    except Exception as e:
        current_app.logger.error(f'Error in get_recent_hr_activities: {e}')
        return []

def get_pending_hr_approvals():
    """Get items pending HR approval"""
    # FIX: Local imports
    from models.leave import LeaveRequest
    from models.employee import Employee
    from models.performance import PerformanceReview
    
    try:
        today = date.today()
        thirty_days_from_now = today + timedelta(days=30)
        
        # Pending leave requests
        pending_leaves = LeaveRequest.query.filter_by(status='pending').count()
        
        # Employees whose probation is ending soon
        probation_ending = Employee.query.filter(
            Employee.is_active == True,
            Employee.probation_end_date.between(today, thirty_days_from_now)
        ).count()
        
        # Overdue performance reviews (employees hired more than 1 year ago without recent review)
        one_year_ago = today - timedelta(days=365)
        overdue_reviews = db.session.query(Employee).filter(
            Employee.is_active == True,
            Employee.hire_date <= one_year_ago
        ).filter(
            ~Employee.id.in_(
                db.session.query(PerformanceReview.employee_id).filter(
                    PerformanceReview.review_date >= one_year_ago
                )
            )
        ).count()
        
        return {
            'pending_leaves': pending_leaves,
            'probation_ending': probation_ending,
            'overdue_reviews': overdue_reviews,
            'total_pending': pending_leaves + probation_ending + overdue_reviews
        }
        
    except Exception as e:
        current_app.logger.error(f'Error in get_pending_hr_approvals: {e}')
        return {
            'pending_leaves': 0,
            'probation_ending': 0,
            'overdue_reviews': 0,
            'total_pending': 0
        }

def get_department_statistics():
    """Get department statistics with corrected SQLAlchemy syntax"""
    # FIX: Local imports
    from models.employee import Employee
    
    try:
        # Fixed SQLAlchemy query with corrected syntax
        dept_stats = db.session.query(
            Employee.department,
            func.count(Employee.id).label('total'),
            func.sum(case((Employee.is_active == True, 1), else_=0)).label('active'),
            func.sum(case((Employee.is_active == False, 1), else_=0)).label('inactive')
        ).group_by(Employee.department).all()
        
        return [
            {
                'department': stat.department,
                'total': stat.total,
                'active': stat.active or 0,
                'inactive': stat.inactive or 0,
                'active_percentage': round((stat.active or 0) / stat.total * 100, 1) if stat.total > 0 else 0
            }
            for stat in dept_stats
        ]
        
    except Exception as e:
        current_app.logger.error(f'Error in get_department_statistics: {e}')
        return []

def get_location_performance_metrics():
    """Get performance metrics by location"""
    # FIX: Local imports
    from models.employee import Employee
    from models.attendance import AttendanceRecord
    
    try:
        thirty_days_ago = date.today() - timedelta(days=30)
        
        location_metrics = db.session.query(
            Employee.location,
            func.count(distinct(Employee.id)).label('total_employees'),
            func.count(AttendanceRecord.id).label('total_records'),
            func.sum(case((AttendanceRecord.status == 'present', 1), else_=0)).label('present_count'),
            func.sum(case((AttendanceRecord.status == 'late', 1), else_=0)).label('late_count')
        ).outerjoin(
            AttendanceRecord,
            and_(
                AttendanceRecord.employee_id == Employee.id,
                AttendanceRecord.date >= thirty_days_ago
            )
        ).filter(
            Employee.is_active == True
        ).group_by(Employee.location).all()
        
        return [
            {
                'location': metric.location,
                'total_employees': metric.total_employees,
                'attendance_rate': round(
                    ((metric.present_count or 0) + (metric.late_count or 0)) / 
                    (metric.total_records or 1) * 100, 1
                ),
                'punctuality_rate': round(
                    (metric.present_count or 0) / 
                    ((metric.present_count or 0) + (metric.late_count or 0) or 1) * 100, 1
                ),
                'total_records': metric.total_records or 0
            }
            for metric in location_metrics
        ]
        
    except Exception as e:
        current_app.logger.error(f'Error in get_location_performance_metrics: {e}')
        return []

def get_hr_alerts():
    """Get HR-specific alerts and notifications"""
    # FIX: Local imports
    from models.employee import Employee
    from models.leave import LeaveRequest
    
    try:
        alerts = []
        today = date.today()
        
        # Probation ending alerts
        probation_ending = Employee.query.filter(
            Employee.is_active == True,
            Employee.probation_end_date.between(today, today + timedelta(days=7))
        ).count()
        
        if probation_ending > 0:
            alerts.append({
                'type': 'warning',
                'title': 'Probation Ending Soon',
                'message': f'{probation_ending} employee(s) probation period ending within 7 days',
                'action_url': url_for('employees.list_employees', status='probation') # FIX: corrected url_for
            })
        
        # High pending leave requests
        pending_leaves = LeaveRequest.query.filter_by(status='pending').count()
        if pending_leaves > 5:
            alerts.append({
                'type': 'info',
                'title': 'Pending Leave Requests',
                'message': f'{pending_leaves} leave requests awaiting approval',
                'action_url': url_for('leaves.list_leaves', status='pending') # FIX: corrected url_for
            })
        
        # Low attendance locations
        low_attendance_locations = []
        for location_metric in get_location_performance_metrics():
            if location_metric['attendance_rate'] < 80:
                low_attendance_locations.append(location_metric['location'])
        
        if low_attendance_locations:
            alerts.append({
                'type': 'danger',
                'title': 'Low Attendance Alert',
                'message': f'Poor attendance at: {", ".join(low_attendance_locations)}',
                'action_url': url_for('dashboard.attendance_details')
            })
        
        return alerts
        
    except Exception as e:
        current_app.logger.error(f'Error in get_hr_alerts: {e}')
        return []

def get_compliance_status():
    """Get compliance status with Kenyan labor laws"""
    # FIX: Local imports
    from models.employee import Employee
    from models.performance import PerformanceReview
    
    try:
        compliance_items = []
        
        # Check for employees without proper documentation
        incomplete_docs = Employee.query.filter(
            Employee.is_active == True,
            or_(
                Employee.national_id.is_(None),
                Employee.kra_pin.is_(None),
                Employee.nssf_number.is_(None),
                Employee.nhif_number.is_(None)
            )
        ).count()
        
        compliance_items.append({
            'item': 'Employee Documentation',
            'status': 'compliant' if incomplete_docs == 0 else 'non_compliant',
            'details': f'{incomplete_docs} employees with incomplete documentation',
            'action_required': incomplete_docs > 0
        })
        
        # Check for overdue performance reviews
        one_year_ago = date.today() - timedelta(days=365)
        overdue_reviews = db.session.query(Employee).filter(
            Employee.is_active == True,
            Employee.hire_date <= one_year_ago
        ).filter(
            ~Employee.id.in_(
                db.session.query(PerformanceReview.employee_id).filter(
                    PerformanceReview.review_date >= one_year_ago
                )
            )
        ).count()
        
        compliance_items.append({
            'item': 'Annual Performance Reviews',
            'status': 'compliant' if overdue_reviews == 0 else 'non_compliant',
            'details': f'{overdue_reviews} employees with overdue annual reviews',
            'action_required': overdue_reviews > 0
        })
        
        # Overall compliance score
        total_items = len(compliance_items)
        compliant_items = sum(1 for item in compliance_items if item['status'] == 'compliant')
        compliance_score = round(compliant_items / total_items * 100, 1) if total_items > 0 else 100
        
        return {
            'overall_score': compliance_score,
            'status': 'good' if compliance_score >= 90 else 'warning' if compliance_score >= 70 else 'critical',
            'items': compliance_items
        }
        
    except Exception as e:
        current_app.logger.error(f'Error in get_compliance_status: {e}')
        return {
            'overall_score': 0,
            'status': 'unknown',
            'items': []
        }

def get_performance_trends():
    """Get performance trends and analytics"""
    # FIX: Local imports
    from models.attendance import AttendanceRecord
    from models.employee import Employee
    
    try:
        # Daily attendance rates for last 30 days
        thirty_days_ago = date.today() - timedelta(days=30)
        
        daily_rates = db.session.query(
            AttendanceRecord.date,
            func.count(AttendanceRecord.id).label('total'),
            func.sum(case((AttendanceRecord.status.in_(['present', 'late']), 1), else_=0)).label('attended')
        ).join(Employee).filter(
            AttendanceRecord.date >= thirty_days_ago,
            Employee.is_active == True
        ).group_by(AttendanceRecord.date).order_by(AttendanceRecord.date).all()
        
        trends = []
        for rate in daily_rates:
            attendance_rate = round(rate.attended / rate.total * 100, 1) if rate.total > 0 else 0
            trends.append({
                'date': rate.date.strftime('%Y-%m-%d'),
                'rate': attendance_rate
            })
        
        return {
            'daily_attendance_rates': trends,
            'average_rate': round(sum(t['rate'] for t in trends) / len(trends), 1) if trends else 0,
            'trend_direction': 'improving' if len(trends) > 1 and trends[-1]['rate'] > trends[0]['rate'] else 'declining'
        }
        
    except Exception as e:
        current_app.logger.error(f'Error in get_performance_trends: {e}')
        return {
            'daily_attendance_rates': [],
            'average_rate': 0,
            'trend_direction': 'stable'
        }

def get_monthly_attendance_trends():
    """Get monthly attendance trends for the last 6 months"""
    # FIX: Local imports
    from models.attendance import AttendanceRecord
    from models.employee import Employee
    
    try:
        six_months_ago = date.today() - timedelta(days=180)
        
        monthly_data = db.session.query(
            extract('year', AttendanceRecord.date).label('year'),
            extract('month', AttendanceRecord.date).label('month'),
            func.count(AttendanceRecord.id).label('total'),
            func.sum(case((AttendanceRecord.status.in_(['present', 'late']), 1), else_=0)).label('attended')
        ).join(Employee).filter(
            AttendanceRecord.date >= six_months_ago,
            Employee.is_active == True
        ).group_by(
            extract('year', AttendanceRecord.date),
            extract('month', AttendanceRecord.date)
        ).order_by(
            extract('year', AttendanceRecord.date),
            extract('month', AttendanceRecord.date)
        ).all()
        
        trends = []
        for data in monthly_data:
            month_name = calendar.month_name[int(data.month)]
            year = int(data.year)
            attendance_rate = round(data.attended / data.total * 100, 1) if data.total > 0 else 0
            trends.append({
                'month': f"{month_name} {year}",
                'rate': attendance_rate,
                'total_records': data.total
            })
        
        return trends
        
    except Exception as e:
        current_app.logger.error(f'Error in get_monthly_attendance_trends: {e}')
        return []

def get_upcoming_hr_events():
    """Get upcoming HR events and anniversaries"""
    # FIX: Local imports
    from models.employee import Employee
    from models.holiday import Holiday
    
    try:
        today = date.today()
        thirty_days_from_now = today + timedelta(days=30)
        
        events = []
        
        # Work anniversaries
        # NOTE: This SQL function 'text' usage may break if not using a compatible DB (e.g. SQLite), but preserving original intent
        anniversaries = Employee.query.filter(
            Employee.is_active == True,
            func.date(Employee.hire_date + text("INTERVAL (YEAR(CURRENT_DATE) - YEAR(hire_date)) YEAR")).between(today, thirty_days_from_now)
        ).all()
        
        for emp in anniversaries:
            years = (today - emp.hire_date).days // 365
            events.append({
                'type': 'anniversary',
                'date': emp.hire_date,
                'title': f'{emp.get_full_name()} - {years} Year(s)',
                'description': f'Work anniversary celebration'
            })
        
        # Upcoming holidays
        holidays = Holiday.query.filter(
            Holiday.date.between(today, thirty_days_from_now)
        ).order_by(Holiday.date).all()
        
        for holiday in holidays:
            events.append({
                'type': 'holiday',
                'date': holiday.date,
                'title': holiday.name,
                'description': f'{holiday.holiday_type.title()} holiday'
            })
        
        return sorted(events, key=lambda x: x['date'])
        
    except Exception as e:
        current_app.logger.error(f'Error in get_upcoming_hr_events: {e}')
        return []

def get_leave_balance_alerts():
    """Get leave balance alerts for employees"""
    # FIX: Local imports
    from models.leave import LeaveRequest
    
    try:
        # This would typically involve calculating leave balances
        # For now, return placeholder data
        return {
            'employees_with_excess_leave': 0,
            'employees_with_low_leave': 0,
            'pending_leave_approvals': LeaveRequest.query.filter_by(status='pending').count()
        }
        
    except Exception as e:
        current_app.logger.error(f'Error in get_leave_balance_alerts: {e}')
        return {
            'employees_with_excess_leave': 0,
            'employees_with_low_leave': 0,
            'pending_leave_approvals': 0
        }

def get_system_health_metrics():
    """Get system health metrics for HR dashboard"""
    # FIX: Local imports
    from models.attendance import AttendanceRecord
    
    try:
        return {
            'database_status': 'healthy',
            'total_records_today': AttendanceRecord.query.filter_by(date=date.today()).count(),
            'system_load': 'normal',
            'last_backup': 'N/A'  # Would be implemented with actual backup system
        }
        
    except Exception as e:
        current_app.logger.error(f'Error in get_system_health_metrics: {e}')
        return {
            'database_status': 'error',
            'total_records_today': 0,
            'system_load': 'unknown',
            'last_backup': 'N/A'
        }

def get_attendance_detailed_summary(target_date, location_filter, department_filter, status_filter, user_role, user_location):
    """Get detailed attendance summary with filters"""
    # FIX: Local imports
    from models.employee import Employee
    from models.attendance import AttendanceRecord
    
    try:
        # Build base query
        query = db.session.query(AttendanceRecord).join(Employee)
        
        # Apply role-based filtering
        if user_role == 'station_manager':
            query = query.filter(Employee.location == user_location)
        elif location_filter != 'all':
            query = query.filter(Employee.location == location_filter)
        
        # Apply other filters
        query = query.filter(
            AttendanceRecord.date == target_date,
            Employee.is_active == True
        )
        
        if department_filter != 'all':
            query = query.filter(Employee.department == department_filter)
        
        if status_filter != 'all':
            query = query.filter(AttendanceRecord.status == status_filter)
        
        # Get counts by status
        status_counts = db.session.query(
            AttendanceRecord.status,
            func.count(AttendanceRecord.id).label('count')
        ).join(Employee).filter(
            AttendanceRecord.date == target_date,
            Employee.is_active == True
        )
        
        # Apply same role-based filtering
        if user_role == 'station_manager':
            status_counts = status_counts.filter(Employee.location == user_location)
        elif location_filter != 'all':
            status_counts = status_counts.filter(Employee.location == location_filter)
        
        if department_filter != 'all':
            status_counts = status_counts.filter(Employee.department == department_filter)
        
        status_counts = status_counts.group_by(AttendanceRecord.status).all()
        
        # Process results
        summary = {'total': 0, 'present': 0, 'late': 0, 'absent': 0, 'on_leave': 0}
        
        for count in status_counts:
            summary['total'] += count.count
            if count.status == 'present':
                summary['present'] = count.count
            elif count.status == 'late':
                summary['late'] = count.count
            elif count.status == 'absent':
                summary['absent'] = count.count
            elif count.status in ['annual_leave', 'sick_leave', 'maternity_leave', 'paternity_leave', 'compassionate_leave']:
                summary['on_leave'] += count.count
        
        # Calculate percentages
        if summary['total'] > 0:
            summary['present_percentage'] = round((summary['present'] / summary['total']) * 100, 1)
            summary['late_percentage'] = round((summary['late'] / summary['total']) * 100, 1)
            summary['absent_percentage'] = round((summary['absent'] / summary['total']) * 100, 1)
            summary['on_leave_percentage'] = round((summary['on_leave'] / summary['total']) * 100, 1)
        else:
            summary.update({
                'present_percentage': 0,
                'absent_percentage': 0,
                'late_percentage': 0,
                'on_leave_percentage': 0
            })
        
        return summary
        
    except Exception as e:
        current_app.logger.error(f'Error in get_attendance_detailed_summary: {e}')
        return {'total': 0, 'present': 0, 'late': 0, 'absent': 0, 'on_leave': 0,
                'present_percentage': 0, 'late_percentage': 0, 'absent_percentage': 0, 'on_leave_percentage': 0}

def get_attendance_records_grouped(target_date, location_filter, department_filter, status_filter, shift_filter, user_role, user_location):
    """Get attendance records grouped by status"""
    # FIX: Local imports
    from models.employee import Employee
    from models.attendance import AttendanceRecord
    
    try:
        # Build base query
        query = db.session.query(AttendanceRecord, Employee).join(Employee)
        
        # Apply role-based filtering
        if user_role == 'station_manager':
            query = query.filter(Employee.location == user_location)
        elif location_filter != 'all':
            query = query.filter(Employee.location == location_filter)
        
        # Apply filters
        query = query.filter(
            AttendanceRecord.date == target_date,
            Employee.is_active == True
        )
        
        if department_filter != 'all':
            query = query.filter(Employee.department == department_filter)
        
        if status_filter != 'all':
            query = query.filter(AttendanceRecord.status == status_filter)
        
        if shift_filter != 'all':
            query = query.filter(Employee.shift == shift_filter)
        
        # Execute query
        records = query.order_by(Employee.first_name, Employee.last_name).all()
        
        # Group by status
        grouped_records = defaultdict(list)
        for attendance, employee in records:
            grouped_records[attendance.status].append({
                'employee': employee,
                'attendance': attendance
            })
        
        return dict(grouped_records)
        
    except Exception as e:
        current_app.logger.error(f'Error in get_attendance_records_grouped: {e}')
        return {}

def get_attendance_summary_for_date(target_date, location_filter, user_role, user_location):
    """Get attendance summary for a specific date"""
    return get_attendance_detailed_summary(
        target_date, location_filter, 'all', 'all', user_role, user_location
    )

def calculate_attendance_trends(current_summary, previous_summary):
    """Calculate trends between two attendance summaries"""
    trends = {}
    
    for key in ['present', 'absent', 'late', 'on_leave']:
        current = current_summary.get(key, 0)
        previous = previous_summary.get(key, 0)
        
        if previous > 0:
            change = ((current - previous) / previous) * 100
        else:
            change = 0 if current == 0 else 100
        
        trends[key] = {
            'change': round(change, 1),
            'direction': 'up' if change > 0 else 'down' if change < 0 else 'stable'
        }
    
    return trends

def get_attendance_filter_options(user):
    """Get available filter options for attendance details"""
    from config import Config # FIX: Local import
    
    options = {
        'locations': [],
        'departments': list(current_app.config.get('DEPARTMENTS', {
            'operations': 'Operations',
            'administration': 'Administration',
            'finance': 'Finance',
            'security': 'Security',
            'maintenance': 'Maintenance',
            'sales': 'Sales'
        }).keys()),
        'shifts': ['day', 'night'],
        'statuses': ['present', 'absent', 'late', 'annual_leave', 'sick_leave', 'maternity_leave', 'paternity_leave']
    }
    
    # Locations based on role
    if user.role == 'hr_manager':
        options['locations'] = list(current_app.config.get('COMPANY_LOCATIONS', {
            'head_office': 'Head Office',
            'dandora': 'Dandora',
            'tassia': 'Tassia',
            'kiambu': 'Kiambu'
        }).keys())
    elif user.role == 'station_manager':
        options['locations'] = [user.location]
    
    return options

# Additional helper functions for station manager dashboard
def get_location_statistics(location):
    """Get statistics for a specific location"""
    # FIX: Local imports
    from models.employee import Employee
    from models.attendance import AttendanceRecord
    
    try:
        today = date.today()
        
        total_employees = Employee.query.filter_by(location=location, is_active=True).count()
        
        todays_attendance = db.session.query(
            AttendanceRecord.status,
            func.count(AttendanceRecord.id).label('count')
        ).join(Employee).filter(
            AttendanceRecord.date == today,
            Employee.location == location,
            Employee.is_active == True
        ).group_by(AttendanceRecord.status).all()
        
        attendance_dict = {record.status: record.count for record in todays_attendance}
        
        # FIX: Leave status names in the breakdown should match the ones in AttendanceRecord
        on_leave = sum(attendance_dict.get(status, 0) for status in 
                      ['annual_leave', 'sick_leave', 'maternity_leave', 'paternity_leave'])
                      
        present = attendance_dict.get('present', 0)
        late = attendance_dict.get('late', 0)
        
        return {
            'total_employees': total_employees,
            'present': present,
            'late': late,
            'absent': attendance_dict.get('absent', 0),
            'on_leave': on_leave,
            'attendance_rate': round(
                (present + late) / total_employees * 100, 1
            ) if total_employees > 0 else 0
        }
        
    except Exception as e:
        current_app.logger.error(f'Error in get_location_statistics: {e}')
        return {
            'total_employees': 0, 'present': 0, 'late': 0, 'absent': 0, 'on_leave': 0, 'attendance_rate': 0
        }

def get_todays_location_attendance(location):
    """Get today's attendance details for a location"""
    # FIX: Local imports
    from models.employee import Employee
    from models.attendance import AttendanceRecord
    
    try:
        today = date.today()
        
        attendance_records = db.session.query(AttendanceRecord, Employee).join(Employee).filter(
            AttendanceRecord.date == today,
            Employee.location == location,
            Employee.is_active == True
        ).order_by(Employee.first_name, Employee.last_name).all()
        
        return [
            {
                'employee': employee,
                'attendance': attendance,
                'status_display': attendance.status.replace('_', ' ').title()
            }
            for attendance, employee in attendance_records
        ]
        
    except Exception as e:
        current_app.logger.error(f'Error in get_todays_location_attendance: {e}')
        return []

def get_shift_breakdown(location):
    """Get shift breakdown for gas stations"""
    # FIX: Local imports
    from models.employee import Employee
    from models.attendance import AttendanceRecord
    from config import Config
    
    try:
        if location == 'head_office':
            return {'day': 0, 'night': 0, 'message': 'Head office operates standard hours'}
        
        today = date.today()
        
        shift_breakdown = db.session.query(
            Employee.shift,
            Employee.department,
            func.count(Employee.id).label('total'),
            func.sum(case((AttendanceRecord.status.in_(['present', 'late']), 1), else_=0)).label('attended')
        ).outerjoin(
            AttendanceRecord,
            and_(AttendanceRecord.employee_id == Employee.id, AttendanceRecord.date == today)
        ).filter(
            Employee.location == location,
            Employee.is_active == True
        ).group_by(Employee.shift, Employee.department).all()
        
        breakdown = defaultdict(lambda: defaultdict(dict))
        for staff in shift_breakdown:
            shift = staff.shift or 'day'
            dept = staff.department or 'operations'
            breakdown[shift][dept] = {
                'total': staff.total,
                'attended': staff.attended or 0,
                'attendance_rate': round((staff.attended or 0) / staff.total * 100, 1) if staff.total > 0 else 0
            }
        
        return breakdown
        
    except Exception as e:
        current_app.logger.error(f'Error in get_shift_breakdown: {e}')
        return {}

def get_recent_location_activities(location):
    """Get recent activities for a location"""
    # FIX: Local imports
    from models.employee import Employee
    from models.audit import AuditLog
    from models.user import User
    
    try:
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        
        # Get activities related to employees at this location
        location_employees = [emp.id for emp in Employee.query.filter_by(location=location, is_active=True).all()]
        
        activities = db.session.query(AuditLog).filter(
            AuditLog.timestamp >= seven_days_ago,
            or_(
                # FIX: AuditLog.metadata was renamed to AuditLog.audit_metadata. We need a way to filter the JSON data.
                # Assuming simple string search in description/details for now if JSON filtering is complex/breaking.
                AuditLog.description.like(f'%location: {location}%') 
                # AuditLog.employee_id filter is safe
            )
        ).order_by(desc(AuditLog.timestamp)).limit(10).all()
        
        return [
            {
                'timestamp': activity.timestamp,
                'event_type': activity.event_type,
                'description': activity.description,
                'user_name': activity.user.get_full_name() if activity.user and hasattr(activity.user, 'get_full_name') else (activity.user.username if activity.user else 'System')
            }
            for activity in activities
        ]
        
    except Exception as e:
        current_app.logger.error(f'Error in get_recent_location_activities: {e}')
        return []

def get_pending_station_items(location):
    """Get pending items for station manager"""
    # FIX: Local imports
    from models.employee import Employee
    from models.leave import LeaveRequest
    from models.attendance import AttendanceRecord
    
    try:
        # Pending leave requests for location employees
        location_employees = [emp.id for emp in Employee.query.filter_by(location=location, is_active=True).all()]
        pending_leaves = LeaveRequest.query.filter(
            LeaveRequest.employee_id.in_(location_employees),
            LeaveRequest.status == 'pending'
        ).count()
        
        # Employees with incomplete attendance today
        today = date.today()
        total_employees = len(location_employees)
        marked_attendance = AttendanceRecord.query.filter(
            AttendanceRecord.date == today,
            AttendanceRecord.employee_id.in_(location_employees)
        ).count()
        
        unmarked_attendance = total_employees - marked_attendance
        
        return {
            'pending_leaves': pending_leaves,
            'unmarked_attendance': unmarked_attendance,
            'total_pending': pending_leaves + unmarked_attendance
        }
        
    except Exception as e:
        current_app.logger.error(f'Error in get_pending_station_items: {e}')
        return {'pending_leaves': 0, 'unmarked_attendance': 0, 'total_pending': 0}

def get_location_performance_detailed(location):
    """Get detailed performance metrics for a location"""
    # FIX: Local imports
    from models.employee import Employee
    from models.attendance import AttendanceRecord
    
    try:
        thirty_days_ago = date.today() - timedelta(days=30)
        
        # Get attendance data for last 30 days
        attendance_data = db.session.query(
            AttendanceRecord.date,
            func.count(AttendanceRecord.id).label('total'),
            func.sum(case((AttendanceRecord.status == 'present', 1), else_=0)).label('present'),
            func.sum(case((AttendanceRecord.status == 'late', 1), else_=0)).label('late')
        ).join(Employee).filter(
            AttendanceRecord.date >= thirty_days_ago,
            Employee.location == location,
            Employee.is_active == True
        ).group_by(AttendanceRecord.date).order_by(AttendanceRecord.date).all()
        
        # Calculate metrics
        total_records = sum(data.total for data in attendance_data)
        total_present = sum(data.present or 0 for data in attendance_data)
        total_late = sum(data.late or 0 for data in attendance_data)
        
        return {
            'attendance_rate': round((total_present + total_late) / total_records * 100, 1) if total_records > 0 else 0,
            'punctuality_rate': round(total_present / (total_present + total_late) * 100, 1) if (total_present + total_late) > 0 else 0,
            'total_working_days': len(attendance_data),
            'daily_data': [
                {
                    'date': data.date.strftime('%Y-%m-%d'),
                    'rate': round((data.present + data.late) / data.total * 100, 1) if data.total > 0 else 0
                }
                for data in attendance_data
            ]
        }
        
    except Exception as e:
        current_app.logger.error(f'Error in get_location_performance_detailed: {e}')
        return {'attendance_rate': 0, 'punctuality_rate': 0, 'total_working_days': 0, 'daily_data': []}

def get_staff_on_duty_breakdown(location):
    """Get breakdown of staff on duty"""
    # FIX: Local imports
    from models.employee import Employee
    from models.attendance import AttendanceRecord
    
    try:
        today = date.today()
        
        # Get current shift information
        current_hour = datetime.now().hour
        current_shift = 'day' if 6 <= current_hour < 18 else 'night'
        
        # Get employees by shift
        staff_breakdown = db.session.query(
            Employee.shift,
            Employee.department,
            func.count(Employee.id).label('total'),
            func.sum(case((AttendanceRecord.status.in_(['present', 'late']), 1), else_=0)).label('on_duty')
        ).outerjoin(
            AttendanceRecord,
            and_(AttendanceRecord.employee_id == Employee.id, AttendanceRecord.date == today)
        ).filter(
            Employee.location == location,
            Employee.is_active == True
        ).group_by(Employee.shift, Employee.department).all()
        
        breakdown = defaultdict(lambda: defaultdict(dict))
        for staff in staff_breakdown:
            shift = staff.shift or 'day'
            dept = staff.department or 'operations'
            breakdown[shift][dept] = {
                'total': staff.total,
                'on_duty': staff.on_duty or 0,
                'off_duty': staff.total - (staff.on_duty or 0)
            }
        
        return {
            'current_shift': current_shift,
            'breakdown': dict(breakdown)
        }
        
    except Exception as e:
        current_app.logger.error(f'Error in get_staff_on_duty_breakdown: {e}')
        return {'current_shift': 'day', 'breakdown': {}}

def get_weekly_attendance_trends(location):
    """Get weekly attendance trends for location"""
    # FIX: Local imports
    from models.employee import Employee
    from models.attendance import AttendanceRecord
    
    try:
        seven_days_ago = date.today() - timedelta(days=7)
        
        daily_trends = db.session.query(
            AttendanceRecord.date,
            func.count(AttendanceRecord.id).label('total'),
            func.sum(case((AttendanceRecord.status.in_(['present', 'late']), 1), else_=0)).label('attended')
        ).join(Employee).filter(
            AttendanceRecord.date >= seven_days_ago,
            Employee.location == location,
            Employee.is_active == True
        ).group_by(AttendanceRecord.date).order_by(AttendanceRecord.date).all()
        
        return [
            {
                'date': trend.date.strftime('%A, %b %d'),
                'rate': round(trend.attended / trend.total * 100, 1) if trend.total > 0 else 0,
                'total': trend.total,
                'attended': trend.attended
            }
            for trend in daily_trends
        ]
        
    except Exception as e:
        current_app.logger.error(f'Error in get_weekly_attendance_trends: {e}')
        return []

def get_location_alerts(location):
    """Get location-specific alerts"""
    try:
        alerts = []
        
        # Check attendance rate
        location_stats = get_location_statistics(location)
        if location_stats['attendance_rate'] < 80:
            alerts.append({
                'type': 'warning',
                'message': f'Low attendance rate today: {location_stats["attendance_rate"]}%'
            })
        
        # Check unmarked attendance
        pending_items = get_pending_station_items(location)
        if pending_items['unmarked_attendance'] > 0:
            alerts.append({
                'type': 'info',
                'message': f'{pending_items["unmarked_attendance"]} employees have not marked attendance today'
            })
        
        return alerts
        
    except Exception as e:
        current_app.logger.error(f'Error in get_location_alerts: {e}')
        return []

def get_inventory_status(location):
    """Get fuel/inventory status for gas stations"""
    # FIX: Local imports
    from config import Config
    
    try:
        # This would typically integrate with inventory management system
        # For now, return placeholder data
        if location == 'head_office':
            return None
        
        # FIX: Using Config to get location details
        location_config = current_app.config.get('COMPANY_LOCATIONS', {}).get(location, {})
        
        return {
            'fuel_levels': {
                'petrol': {'current': 75, 'capacity': 100, 'status': 'good'},
                'diesel': {'current': 60, 'capacity': 100, 'status': 'good'},
                'lpg': {'current': 40, 'capacity': 100, 'status': 'low'}
            },
            'tank_capacity': location_config.get('tank_capacity', {}), # FIX: Added tank capacity info
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M')
        }
        
    except Exception as e:
        current_app.logger.error(f'Error in get_inventory_status: {e}')
        return None

def get_customer_service_metrics(location):
    """Get customer service metrics for location"""
    try:
        # This would typically integrate with customer feedback system
        # For now, return placeholder data
        return {
            'daily_customers': 150,
            'customer_satisfaction': 4.2,
            'complaints': 2,
            'compliments': 8
        }
        
    except Exception as e:
        current_app.logger.error(f'Error in get_customer_service_metrics: {e}')
        return {
            'daily_customers': 0,
            'customer_satisfaction': 0,
            'complaints': 0,
            'compliments': 0
        }

# Error handlers
@dashboard_bp.errorhandler(404)
def dashboard_not_found(error):
    """Handle 404 errors in dashboard"""
    return render_template('errors/404.html'), 404

@dashboard_bp.errorhandler(500)
def dashboard_server_error(error):
    """Handle 500 errors in dashboard"""
    db.session.rollback()
    current_app.logger.error(f'Dashboard error: {error}')
    return render_template('errors/500.html'), 500