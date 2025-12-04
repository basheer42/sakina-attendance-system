"""
Sakina Gas Company - Reports and Analytics Routes
Built from scratch with comprehensive reporting system
Version 3.0 - Enterprise grade with full complexity
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app, make_response
from flask_login import login_required, current_user
from datetime import datetime, date, timedelta
from sqlalchemy import func, and_, or_, extract, case, desc # FIX: Added desc
from decimal import Decimal
import json
import csv
import io
import calendar # FIX: Added calendar import

# FIX: Removed global model imports to prevent early model registration
from database import db
from config import Config

# Create blueprint
reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/dashboard')
@login_required
def reports_dashboard():
    """Reports dashboard with overview of available reports"""
    # FIX: Local imports
    from models.employee import Employee
    from models.attendance import AttendanceRecord
    from models.leave import LeaveRequest
    from models.audit import AuditLog
    
    if current_user.role not in ['hr_manager', 'admin', 'station_manager']:
        flash('You do not have permission to access reports.', 'error')
        return redirect(url_for('dashboard.main'))
    
    # Get quick statistics for dashboard
    today = date.today()
    current_month_start = date(today.year, today.month, 1)
    
    # Build base queries based on user permissions
    if current_user.role in ['hr_manager', 'admin']:
        employee_query = Employee.query.filter(Employee.is_active == True)
        attendance_query = AttendanceRecord.query
        leave_query = LeaveRequest.query
    else:
        # Station managers see only their location
        employee_query = Employee.query.filter(
            Employee.is_active == True,
            Employee.location == current_user.location
        )
        attendance_query = AttendanceRecord.query.join(Employee).filter(
            Employee.location == current_user.location
        )
        leave_query = LeaveRequest.query.join(Employee).filter(
            Employee.location == current_user.location
        )
    
    # Calculate statistics
    total_employees = employee_query.count()
    
    # Today's attendance
    today_attendance = attendance_query.filter(AttendanceRecord.date == today).count()
    today_present = attendance_query.filter(
        AttendanceRecord.date == today,
        AttendanceRecord.status.in_(['present', 'late'])
    ).count()
    
    # Current month statistics
    month_attendance = attendance_query.filter(
        AttendanceRecord.date >= current_month_start
    ).count()
    
    # Leave statistics
    pending_leaves = leave_query.filter(LeaveRequest.status == 'pending').count()
    current_leaves = leave_query.filter(
        LeaveRequest.status == 'approved',
        LeaveRequest.start_date <= today,
        LeaveRequest.end_date >= today
    ).count()
    
    # Recent reports accessed
    recent_reports = AuditLog.query.filter(
        AuditLog.user_id == current_user.id,
        AuditLog.event_type.like('report_%'), # FIX: Use event_type
        AuditLog.timestamp >= datetime.utcnow() - timedelta(days=30)
    ).order_by(AuditLog.timestamp.desc()).limit(5).all()
    
    return render_template('reports/dashboard.html',
        total_employees=total_employees,
        today_attendance=today_attendance,
        today_present=today_present,
        attendance_rate=round((today_present / total_employees * 100) if total_employees > 0 else 0, 1), # FIX: Use total_employees in calculation
        month_attendance=month_attendance,
        pending_leaves=pending_leaves,
        current_leaves=current_leaves,
        recent_reports=recent_reports
    )

@reports_bp.route('/attendance')
@login_required
def attendance_reports():
    """Comprehensive attendance reports with filtering"""
    if current_user.role not in ['hr_manager', 'admin', 'station_manager']:
        flash('You do not have permission to access attendance reports.', 'error')
        return redirect(url_for('reports.reports_dashboard'))
    
    # FIX: Local imports
    from models.employee import Employee
    from models.attendance import AttendanceRecord
    from models.performance import PerformanceReview
    from models.audit import AuditLog
    
    # Get filter parameters
    start_date_str = request.args.get('start_date', '')
    end_date_str = request.args.get('end_date', '')
    location_filter = request.args.get('location', '')
    department_filter = request.args.get('department', '')
    employee_filter = request.args.get('employee', '')
    report_type = request.args.get('type', 'summary')
    
    # Set default date range (current month)
    if not start_date_str:
        start_date = date(date.today().year, date.today().month, 1)
    else:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
    
    if not end_date_str:
        end_date = date.today()
    else:
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    
    # Validate date range
    if start_date > end_date:
        flash('Start date cannot be after end date.', 'error')
        start_date, end_date = end_date, start_date
    
    # Build base query with user permissions
    if current_user.role in ['hr_manager', 'admin']:
        query = AttendanceRecord.query.join(Employee)
        employee_options = Employee.query.filter(Employee.is_active == True)
        available_locations = current_app.config['COMPANY_LOCATIONS'].keys()
        available_departments = current_app.config['DEPARTMENTS'].keys()
    else:
        query = AttendanceRecord.query.join(Employee).filter(
            Employee.location == current_user.location
        )
        employee_options = Employee.query.filter(
            Employee.is_active == True,
            Employee.location == current_user.location
        )
        available_locations = [current_user.location]
        available_departments = current_app.config['DEPARTMENTS'].keys()
    
    # Apply date filter
    query = query.filter(AttendanceRecord.date.between(start_date, end_date))
    
    # Apply additional filters
    if location_filter:
        query = query.filter(Employee.location == location_filter)
    
    if department_filter:
        query = query.filter(Employee.department == department_filter)
    
    if employee_filter:
        query = query.filter(Employee.id == employee_filter)
    
    # Generate report based on type
    if report_type == 'summary':
        # Summary report with aggregated data
        summary_data = generate_attendance_summary(query, start_date, end_date)
        
    elif report_type == 'detailed':
        # Detailed daily records
        page = request.args.get('page', 1, type=int)
        per_page = 50
        
        records = query.order_by(
            AttendanceRecord.date.desc(),
            Employee.last_name,
            Employee.first_name
        ).paginate(page=page, per_page=per_page, error_out=False)
        
    elif report_type == 'monthly':
        # Monthly attendance trends
        monthly_data = generate_monthly_attendance_trends(query, start_date, end_date)
        
    elif report_type == 'employee':
        # Individual employee analysis
        if not employee_filter:
            flash('Please select an employee for individual analysis.', 'warning')
            employee_data = None
        else:
            employee_data = generate_employee_attendance_analysis(employee_filter, start_date, end_date)
    
    # Log report access
    AuditLog.log_event(
        event_type='report_attendance_accessed',
        description=f'Attendance report accessed: {report_type} from {start_date} to {end_date}',
        user_id=current_user.id,
        event_category='reports',
        details={
            'report_type': report_type,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'filters': {
                'location': location_filter,
                'department': department_filter,
                'employee': employee_filter
            }
        }
    )
    
    template_data = {
        'start_date': start_date,
        'end_date': end_date,
        'location_filter': location_filter,
        'department_filter': department_filter,
        'employee_filter': employee_filter,
        'report_type': report_type,
        'available_locations': available_locations,
        'available_departments': available_departments,
        'employee_options': employee_options.all()
    }
    
    # Add report-specific data
    if report_type == 'summary':
        template_data['summary_data'] = summary_data
    elif report_type == 'detailed':
        template_data['records'] = records
    elif report_type == 'monthly':
        template_data['monthly_data'] = monthly_data
    elif report_type == 'employee' and 'employee_data' in locals():
        template_data['employee_data'] = employee_data
    
    return render_template('reports/attendance.html', **template_data)

@reports_bp.route('/leave')
@login_required
def leave_reports():
    """Comprehensive leave reports and analytics"""
    if current_user.role not in ['hr_manager', 'admin', 'station_manager']:
        flash('You do not have permission to access leave reports.', 'error')
        return redirect(url_for('reports.reports_dashboard'))
    
    # FIX: Local imports
    from models.leave import LeaveRequest
    from models.employee import Employee
    from models.audit import AuditLog
    
    # Get filter parameters
    year = request.args.get('year', date.today().year, type=int)
    location_filter = request.args.get('location', '')
    department_filter = request.args.get('department', '')
    leave_type_filter = request.args.get('leave_type', '')
    status_filter = request.args.get('status', '')
    report_type = request.args.get('type', 'summary')
    
    # Build base query with user permissions
    if current_user.role in ['hr_manager', 'admin']:
        query = LeaveRequest.query.join(Employee)
        available_locations = current_app.config['COMPANY_LOCATIONS'].keys()
        available_departments = current_app.config['DEPARTMENTS'].keys()
    else:
        query = LeaveRequest.query.join(Employee).filter(
            Employee.location == current_user.location
        )
        available_locations = [current_user.location]
        available_departments = current_app.config['DEPARTMENTS'].keys()
    
    # Apply year filter
    year_start = date(year, 1, 1)
    year_end = date(year, 12, 31)
    query = query.filter(LeaveRequest.start_date.between(year_start, year_end))
    
    # Apply additional filters
    if location_filter:
        query = query.filter(Employee.location == location_filter)
    
    if department_filter:
        query = query.filter(Employee.department == department_filter)
    
    if leave_type_filter:
        query = query.filter(LeaveRequest.leave_type == leave_type_filter)
    
    if status_filter:
        query = query.filter(LeaveRequest.status == status_filter)
    
    # Generate report based on type
    if report_type == 'summary':
        summary_data = generate_leave_summary(query, year)
        
    elif report_type == 'balance':
        balance_data = generate_leave_balance_report(year, location_filter, department_filter)
        
    elif report_type == 'trends':
        trends_data = generate_leave_trends_report(query, year)
        
    elif report_type == 'compliance':
        compliance_data = generate_leave_compliance_report(query, year)
    
    # Leave type options
    leave_types = [
        ('annual_leave', 'Annual Leave'),
        ('sick_leave', 'Sick Leave'),
        ('maternity_leave', 'Maternity Leave'),
        ('paternity_leave', 'Paternity Leave'),
        ('compassionate_leave', 'Compassionate Leave'),
        ('study_leave', 'Study Leave')
    ]
    
    # Status options
    status_options = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled')
    ]
    
    # Log report access
    AuditLog.log_event(
        event_type='report_leave_accessed',
        description=f'Leave report accessed: {report_type} for year {year}',
        user_id=current_user.id,
        event_category='reports',
        details={
            'report_type': report_type,
            'year': year,
            'filters': {
                'location': location_filter,
                'department': department_filter,
                'leave_type': leave_type_filter,
                'status': status_filter
            }
        }
    )
    
    template_data = {
        'year': year,
        'location_filter': location_filter,
        'department_filter': department_filter,
        'leave_type_filter': leave_type_filter,
        'status_filter': status_filter,
        'report_type': report_type,
        'available_locations': available_locations,
        'available_departments': available_departments,
        'leave_types': leave_types,
        'status_options': status_options,
        'year_options': list(range(year - 5, year + 2))
    }
    
    # Add report-specific data
    if report_type == 'summary':
        template_data['summary_data'] = summary_data
    elif report_type == 'balance':
        template_data['balance_data'] = balance_data
    elif report_type == 'trends':
        template_data['trends_data'] = trends_data
    elif report_type == 'compliance':
        template_data['compliance_data'] = compliance_data
    
    return render_template('reports/leave.html', **template_data)

@reports_bp.route('/performance')
@login_required
def performance_reports():
    """Performance management reports and analytics"""
    if current_user.role not in ['hr_manager', 'admin']:
        flash('You do not have permission to access performance reports.', 'error')
        return redirect(url_for('reports.reports_dashboard'))
    
    # FIX: Local imports
    from models.performance import PerformanceReview
    from models.employee import Employee
    from models.audit import AuditLog
    
    # Get filter parameters
    year = request.args.get('year', date.today().year, type=int)
    review_type_filter = request.args.get('review_type', '')
    location_filter = request.args.get('location', '')
    department_filter = request.args.get('department', '')
    rating_filter = request.args.get('rating', '')
    report_type = request.args.get('type', 'summary')
    
    # Build base query
    query = PerformanceReview.query.join(Employee)
    
    # Apply year filter
    year_start = date(year, 1, 1)
    year_end = date(year, 12, 31)
    query = query.filter(PerformanceReview.review_date.between(year_start, year_end))
    
    # Apply additional filters
    if review_type_filter:
        query = query.filter(PerformanceReview.review_type == review_type_filter)
    
    if location_filter:
        query = query.filter(Employee.location == location_filter)
    
    if department_filter:
        query = query.filter(Employee.department == department_filter)
    
    if rating_filter:
        if rating_filter == 'excellent':
            query = query.filter(PerformanceReview.overall_rating >= 4.5)
        elif rating_filter == 'good':
            query = query.filter(
                PerformanceReview.overall_rating >= 3.5,
                PerformanceReview.overall_rating < 4.5
            )
        elif rating_filter == 'average':
            query = query.filter(
                PerformanceReview.overall_rating >= 2.5,
                PerformanceReview.overall_rating < 3.5
            )
        elif rating_filter == 'poor':
            query = query.filter(PerformanceReview.overall_rating < 2.5)
    
    # Generate report based on type
    if report_type == 'summary':
        summary_data = generate_performance_summary(query, year)
        
    elif report_type == 'ratings':
        ratings_data = generate_performance_ratings_analysis(query, year)
        
    elif report_type == 'goals':
        goals_data = generate_goals_achievement_report(query, year)
        
    elif report_type == 'development':
        development_data = generate_development_needs_report(query, year)
    
    # Filter options
    review_types = [
        ('annual', 'Annual Review'),
        ('probation', 'Probation Review'),
        ('mid_year', 'Mid-Year Review'),
        ('quarterly', 'Quarterly Review')
    ]
    
    rating_options = [
        ('excellent', 'Excellent (4.5+)'),
        ('good', 'Good (3.5-4.4)'),
        ('average', 'Average (2.5-3.4)'),
        ('poor', 'Poor (<2.5)')
    ]
    
    # Log report access
    AuditLog.log_event(
        event_type='report_performance_accessed',
        description=f'Performance report accessed: {report_type} for year {year}',
        user_id=current_user.id,
        event_category='reports',
        details={
            'report_type': report_type,
            'year': year,
            'filters': {
                'review_type': review_type_filter,
                'location': location_filter,
                'department': department_filter,
                'rating': rating_filter
            }
        }
    )
    
    template_data = {
        'year': year,
        'review_type_filter': review_type_filter,
        'location_filter': location_filter,
        'department_filter': department_filter,
        'rating_filter': rating_filter,
        'report_type': report_type,
        'available_locations': current_app.config['COMPANY_LOCATIONS'].keys(),
        'available_departments': current_app.config['DEPARTMENTS'].keys(),
        'review_types': review_types,
        'rating_options': rating_options,
        'year_options': list(range(year - 5, year + 2))
    }
    
    # Add report-specific data
    if report_type == 'summary':
        template_data['summary_data'] = summary_data
    elif report_type == 'ratings':
        template_data['ratings_data'] = ratings_data
    elif report_type == 'goals':
        template_data['goals_data'] = goals_data
    elif report_type == 'development':
        template_data['development_data'] = development_data
    
    return render_template('reports/performance.html', **template_data)

@reports_bp.route('/hr-analytics')
@login_required
def hr_analytics():
    """Comprehensive HR analytics dashboard"""
    if current_user.role not in ['hr_manager', 'admin']:
        flash('You do not have permission to access HR analytics.', 'error')
        return redirect(url_for('reports.reports_dashboard'))
    
    # FIX: Local imports
    from models.employee import Employee
    from models.attendance import AttendanceRecord
    from models.leave import LeaveRequest
    from models.performance import PerformanceReview
    from models.audit import AuditLog
    
    # Time range for analytics
    end_date = date.today()
    start_date = end_date - timedelta(days=365)  # Last 12 months
    
    # Employee statistics
    employee_stats = generate_employee_analytics()
    
    # Attendance analytics
    attendance_analytics = generate_attendance_analytics(start_date, end_date)
    
    # Leave analytics
    leave_analytics = generate_leave_analytics(start_date, end_date)
    
    # Performance analytics
    performance_analytics = generate_performance_analytics()
    
    # Turnover analytics
    turnover_analytics = generate_turnover_analytics(start_date, end_date)
    
    # Compliance metrics
    compliance_metrics = generate_compliance_metrics()
    
    # Log analytics access
    AuditLog.log_event(
        event_type='hr_analytics_accessed',
        description='HR analytics dashboard accessed',
        user_id=current_user.id,
        event_category='reports',
        details={'date_range': f'{start_date} to {end_date}'}
    )
    
    return render_template('reports/hr_analytics.html',
        employee_stats=employee_stats,
        attendance_analytics=attendance_analytics,
        leave_analytics=leave_analytics,
        performance_analytics=performance_analytics,
        turnover_analytics=turnover_analytics,
        compliance_metrics=compliance_metrics,
        start_date=start_date,
        end_date=end_date
    )

# Export functionality

@reports_bp.route('/export/attendance')
@login_required
def export_attendance():
    """Export attendance data to CSV"""
    if current_user.role not in ['hr_manager', 'admin', 'station_manager']:
        return jsonify({'error': 'Insufficient permissions'}), 403
    
    # FIX: Local imports
    from models.employee import Employee
    from models.attendance import AttendanceRecord
    from models.audit import AuditLog
    
    # Get parameters
    start_date_str = request.args.get('start_date', '')
    end_date_str = request.args.get('end_date', '')
    location_filter = request.args.get('location', '')
    format_type = request.args.get('format', 'csv')
    
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400
    
    # Build query with user permissions
    if current_user.role in ['hr_manager', 'admin']:
        query = AttendanceRecord.query.join(Employee)
    else:
        query = AttendanceRecord.query.join(Employee).filter(
            Employee.location == current_user.location
        )
    
    query = query.filter(AttendanceRecord.date.between(start_date, end_date))
    
    if location_filter:
        query = query.filter(Employee.location == location_filter)
    
    records = query.order_by(
        AttendanceRecord.date.desc(),
        Employee.last_name,
        Employee.first_name
    ).all()
    
    if format_type == 'csv':
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'Date', 'Employee ID', 'Employee Name', 'Department', 'Location',
            'Clock In', 'Clock Out', 'Break Time (min)', 'Total Hours',
            'Regular Hours', 'Overtime Hours', 'Status', 'Late Minutes'
        ])
        
        # Write data
        for record in records:
            writer.writerow([
                record.date.isoformat(),
                record.employee.employee_id,
                record.employee.get_full_name(),
                record.employee.department,
                record.employee.location,
                record.clock_in_time.strftime('%H:%M') if record.clock_in_time else '', # FIX: Use clock_in_time
                record.clock_out_time.strftime('%H:%M') if record.clock_out_time else '', # FIX: Use clock_out_time
                record.total_break_minutes, # FIX: Use total_break_minutes
                record.get_formatted_work_hours(),
                f"{float(record.regular_hours):.2f}" if record.regular_hours else "0.00",
                f"{float(record.overtime_hours):.2f}" if record.overtime_hours else "0.00",
                record.get_status_display(),
                record.minutes_late # FIX: Use minutes_late
            ])
        
        output.seek(0)
        
        # Create response
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename=attendance_{start_date}_{end_date}.csv'
        
        # Log export
        AuditLog.log_event(
            event_type='report_attendance_exported',
            description=f'Attendance report exported ({len(records)} records)',
            user_id=current_user.id,
            event_category='reports',
            details={
                'format': format_type,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'record_count': len(records)
            }
        )
        
        return response
    
    return jsonify({'error': 'Unsupported format'}), 400

@reports_bp.route('/export/leave')
@login_required
def export_leave():
    """Export leave data to CSV"""
    if current_user.role not in ['hr_manager', 'admin', 'station_manager']:
        return jsonify({'error': 'Insufficient permissions'}), 403
    
    # FIX: Local imports
    from models.employee import Employee
    from models.leave import LeaveRequest
    from models.audit import AuditLog
    
    # Get parameters
    year = request.args.get('year', date.today().year, type=int)
    status_filter = request.args.get('status', '')
    format_type = request.args.get('format', 'csv')
    
    # Build query with user permissions
    if current_user.role in ['hr_manager', 'admin']:
        query = LeaveRequest.query.join(Employee)
    else:
        query = LeaveRequest.query.join(Employee).filter(
            Employee.location == current_user.location
        )
    
    # Apply filters
    year_start = date(year, 1, 1)
    year_end = date(year, 12, 31)
    query = query.filter(LeaveRequest.start_date.between(year_start, year_end))
    
    if status_filter:
        query = query.filter(LeaveRequest.status == status_filter)
    
    requests = query.order_by(
        LeaveRequest.requested_date.desc() # FIX: Use requested_date
    ).all()
    
    if format_type == 'csv':
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'Request Number', 'Employee ID', 'Employee Name', 'Department',
            'Leave Type', 'Start Date', 'End Date', 'Total Days', 'Status',
            'Requested Date', 'Approved Date', 'Reason'
        ])
        
        # Write data
        for req in requests:
            writer.writerow([
                req.request_number,
                req.employee.employee_id,
                req.employee.get_full_name(),
                req.employee.department,
                req.get_leave_type_display(),
                req.start_date.isoformat(),
                req.end_date.isoformat(),
                f"{float(req.total_days):.1f}",
                req.get_status_display(),
                req.requested_date.strftime('%Y-%m-%d %H:%M'),
                req.hr_approval_date.strftime('%Y-%m-%d %H:%M') if req.hr_approval_date else '', # FIX: Use hr_approval_date
                req.reason[:100] + '...' if len(req.reason) > 100 else req.reason
            ])
        
        output.seek(0)
        
        # Create response
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename=leave_requests_{year}.csv'
        
        # Log export
        AuditLog.log_event(
            event_type='report_leave_exported',
            description=f'Leave report exported ({len(requests)} records)',
            user_id=current_user.id,
            event_category='reports',
            details={
                'format': format_type,
                'year': year,
                'record_count': len(requests)
            }
        )
        
        return response
    
    return jsonify({'error': 'Unsupported format'}), 400

# Helper functions for report generation

def generate_attendance_summary(query, start_date, end_date):
    """Generate attendance summary statistics"""
    # FIX: Local imports
    from models.employee import Employee
    from models.attendance import AttendanceRecord
    
    total_records = query.count()
    
    # Status breakdown
    status_counts = db.session.query(
        AttendanceRecord.status,
        func.count(AttendanceRecord.id).label('count')
    ).join(Employee).filter(
        AttendanceRecord.date.between(start_date, end_date)
    ).group_by(AttendanceRecord.status).all()
    
    status_breakdown = {status: count for status, count in status_counts}
    
    # Calculate rates
    present_count = status_breakdown.get('present', 0) + status_breakdown.get('late', 0)
    attendance_rate = (present_count / total_records * 100) if total_records > 0 else 0
    punctuality_rate = (status_breakdown.get('present', 0) / present_count * 100) if present_count > 0 else 0
    
    # Department breakdown (if user has access)
    dept_query = query.with_entities(
        Employee.department,
        func.count(AttendanceRecord.id).label('total'),
        func.sum(case((AttendanceRecord.status.in_(['present', 'late']), 1), else_=0)).label('present')
    ).group_by(Employee.department)
    
    department_stats = []
    for dept, total, present in dept_query.all():
        rate = (present / total * 100) if total > 0 else 0
        department_stats.append({
            'department': dept,
            'total_records': total,
            'present_records': present,
            'attendance_rate': round(rate, 1)
        })
    
    return {
        'total_records': total_records,
        'status_breakdown': status_breakdown,
        'attendance_rate': round(attendance_rate, 1),
        'punctuality_rate': round(punctuality_rate, 1),
        'department_stats': department_stats,
        'date_range': f"{start_date} to {end_date}"
    }

def generate_leave_summary(query, year):
    """Generate leave summary statistics"""
    # FIX: Local imports
    from models.leave import LeaveRequest
    
    total_requests = query.count()
    
    # Status breakdown
    status_counts = query.with_entities(
        LeaveRequest.status,
        func.count(LeaveRequest.id).label('count')
    ).group_by(LeaveRequest.status).all()
    
    status_breakdown = {status: count for status, count in status_counts}
    
    # Leave type breakdown
    type_counts = query.with_entities(
        LeaveRequest.leave_type,
        func.count(LeaveRequest.id).label('count'),
        func.sum(LeaveRequest.total_days).label('total_days')
    ).group_by(LeaveRequest.leave_type).all()
    
    type_breakdown = []
    for leave_type, count, total_days in type_counts:
        type_breakdown.append({
            'leave_type': leave_type.replace('_', ' ').title(),
            'request_count': count,
            'total_days': float(total_days) if total_days else 0
        })
    
    # Monthly trends
    monthly_trends = query.with_entities(
        extract('month', LeaveRequest.start_date).label('month'),
        func.count(LeaveRequest.id).label('count')
    ).group_by(extract('month', LeaveRequest.start_date)).all()
    
    monthly_data = {month: 0 for month in range(1, 13)}
    for month, count in monthly_trends:
        monthly_data[int(month)] = count
    
    return {
        'total_requests': total_requests,
        'status_breakdown': status_breakdown,
        'type_breakdown': type_breakdown,
        'monthly_trends': monthly_data,
        'year': year
    }

def generate_employee_analytics():
    """Generate comprehensive employee analytics"""
    # FIX: Local imports
    from models.employee import Employee
    
    total_employees = Employee.query.count()
    active_employees = Employee.query.filter(Employee.is_active == True).count()
    
    # Department distribution
    dept_counts = db.session.query(
        Employee.department,
        func.count(Employee.id).label('count')
    ).filter(Employee.is_active == True).group_by(Employee.department).all()
    
    department_distribution = {dept: count for dept, count in dept_counts}
    
    # Location distribution
    location_counts = db.session.query(
        Employee.location,
        func.count(Employee.id).label('count')
    ).filter(Employee.is_active == True).group_by(Employee.location).all()
    
    location_distribution = {location: count for location, count in location_counts}
    
    # Employment type distribution
    type_counts = db.session.query(
        Employee.employment_type,
        func.count(Employee.id).label('count')
    ).filter(Employee.is_active == True).group_by(Employee.employment_type).all()
    
    employment_type_distribution = {emp_type: count for emp_type, count in type_counts}
    
    return {
        'total_employees': total_employees,
        'active_employees': active_employees,
        'inactive_employees': total_employees - active_employees,
        'department_distribution': department_distribution,
        'location_distribution': location_distribution,
        'employment_type_distribution': employment_type_distribution
    }

def generate_attendance_analytics(start_date, end_date):
    """Generate attendance analytics for time period"""
    # FIX: Local imports
    from models.attendance import AttendanceRecord
    
    # Overall attendance rate
    total_records = AttendanceRecord.query.filter(
        AttendanceRecord.date.between(start_date, end_date)
    ).count()
    
    present_records = AttendanceRecord.query.filter(
        AttendanceRecord.date.between(start_date, end_date),
        AttendanceRecord.status.in_(['present', 'late'])
    ).count()
    
    overall_rate = (present_records / total_records * 100) if total_records > 0 else 0
    
    # Monthly trends
    monthly_data = db.session.query(
        func.date_trunc('month', AttendanceRecord.date).label('month'),
        func.count(AttendanceRecord.id).label('total'),
        func.sum(case((AttendanceRecord.status.in_(['present', 'late']), 1), else_=0)).label('present')
    ).filter(
        AttendanceRecord.date.between(start_date, end_date)
    ).group_by(func.date_trunc('month', AttendanceRecord.date)).all()
    
    monthly_trends = []
    for month, total, present in monthly_data:
        rate = (present / total * 100) if total > 0 else 0
        monthly_trends.append({
            'month': month.strftime('%Y-%m'),
            'attendance_rate': round(rate, 1)
        })
    
    return {
        'overall_attendance_rate': round(overall_rate, 1),
        'total_records': total_records,
        'present_records': present_records,
        'monthly_trends': monthly_trends
    }

def generate_leave_analytics(start_date, end_date):
    """Generate leave analytics for time period"""
    # FIX: Local imports
    from models.leave import LeaveRequest
    from models.employee import Employee
    
    # Leave requests by type
    leave_by_type = db.session.query(
        LeaveRequest.leave_type,
        func.count(LeaveRequest.id).label('count'),
        func.sum(LeaveRequest.total_days).label('total_days')
    ).filter(
        LeaveRequest.start_date.between(start_date, end_date)
    ).group_by(LeaveRequest.leave_type).all()
    
    leave_trends = []
    for leave_type, count, total_days in leave_by_type:
        leave_trends.append({
            'leave_type': leave_type.replace('_', ' ').title(),
            'count': count,
            'total_days': float(total_days) if total_days else 0
        })
    
    return {
        'leave_by_type': leave_trends,
        'total_requests': sum(item['count'] for item in leave_trends)
    }

def generate_performance_analytics():
    """Generate performance analytics"""
    # FIX: Local imports
    from models.performance import PerformanceReview
    
    # Average rating by location
    avg_rating_by_location = db.session.query(
        Employee.location,
        func.avg(PerformanceReview.overall_rating).label('average_rating')
    ).join(PerformanceReview).group_by(Employee.location).all()
    
    location_ratings = {
        location: round(float(avg_rating), 2)
        for location, avg_rating in avg_rating_by_location
    }
    
    return {
        'average_rating_by_location': location_ratings,
        'total_reviews': PerformanceReview.query.count()
    }

def generate_turnover_analytics(start_date, end_date):
    """Generate turnover analytics"""
    # FIX: Local imports
    from models.employee import Employee
    
    # Active employees at start of period
    start_employees = Employee.query.filter(
        Employee.hire_date <= start_date,
        or_(Employee.termination_date.is_(None), Employee.termination_date > start_date)
    ).count()
    
    # Employees terminated during period
    terminated_employees = Employee.query.filter(
        Employee.termination_date >= start_date,
        Employee.termination_date <= end_date
    ).count()
    
    # Annualized turnover rate (simplified)
    avg_employees = start_employees # Simplified denominator
    turnover_rate = (terminated_employees / avg_employees * 100) if avg_employees > 0 else 0
    
    return {
        'start_employees': start_employees,
        'terminated_employees': terminated_employees,
        'annualized_turnover_rate': round(turnover_rate, 2)
    }

def generate_compliance_metrics():
    """Generate compliance-related metrics"""
    # FIX: Local imports
    from models.performance import PerformanceReview
    from models.leave import LeaveRequest
    from models.employee import Employee
    
    today = date.today()
    
    # Overdue performance reviews
    overdue_reviews = PerformanceReview.query.filter(
        PerformanceReview.due_date < today,
        PerformanceReview.status.in_(['draft', 'in_progress'])
    ).count()
    
    # Pending leave approvals (>3 days old)
    old_pending_leaves = LeaveRequest.query.filter(
        LeaveRequest.status == 'pending',
        LeaveRequest.requested_date < datetime.utcnow() - timedelta(days=3)
    ).count()
    
    # Employees without recent performance reviews
    one_year_ago = today - timedelta(days=365)
    employees_needing_review = Employee.query.filter(
        Employee.is_active == True,
        ~Employee.id.in_(
            db.session.query(PerformanceReview.employee_id).filter(
                PerformanceReview.review_date > one_year_ago
            )
        )
    ).count()
    
    return {
        'overdue_reviews': overdue_reviews,
        'old_pending_leaves': old_pending_leaves,
        'employees_needing_review': employees_needing_review,
        'last_calculated': datetime.utcnow().isoformat()
    }

# API endpoints for chart data

@reports_bp.route('/api/attendance-chart')
@login_required
def api_attendance_chart():
    """API endpoint for attendance chart data"""
    # FIX: Local imports
    from models.employee import Employee
    from models.attendance import AttendanceRecord
    
    days = request.args.get('days', 30, type=int)
    
    end_date = date.today()
    start_date = end_date - timedelta(days=days-1)
    
    # Build query based on permissions
    if current_user.role in ['hr_manager', 'admin']:
        base_query = AttendanceRecord.query
    else:
        base_query = AttendanceRecord.query.join(Employee).filter(
            Employee.location == current_user.location
        )
    
    # Get daily attendance data
    daily_data = db.session.query(
        AttendanceRecord.date,
        func.count(AttendanceRecord.id).label('total'),
        func.sum(case((AttendanceRecord.status == 'present', 1), else_=0)).label('present'),
        func.sum(case((AttendanceRecord.status == 'late', 1), else_=0)).label('late'),
        func.sum(case((AttendanceRecord.status == 'absent', 1), else_=0)).label('absent')
    ).filter(
        AttendanceRecord.date.between(start_date, end_date)
    ).group_by(AttendanceRecord.date).all()
    
    chart_data = {
        'labels': [],
        'datasets': [
            {'label': 'Present', 'data': [], 'backgroundColor': '#28A745'},
            {'label': 'Late', 'data': [], 'backgroundColor': '#FFC107'},
            {'label': 'Absent', 'data': [], 'backgroundColor': '#DC3545'}
        ]
    }
    
    # Fill in data for each day
    current_date = start_date
    daily_dict = {item.date: item for item in daily_data}
    
    while current_date <= end_date:
        chart_data['labels'].append(current_date.strftime('%Y-%m-%d'))
        
        if current_date in daily_dict:
            data = daily_dict[current_date]
            chart_data['datasets'][0]['data'].append(data.present)
            chart_data['datasets'][1]['data'].append(data.late)
            chart_data['datasets'][2]['data'].append(data.absent)
        else:
            chart_data['datasets'][0]['data'].append(0)
            chart_data['datasets'][1]['data'].append(0)
            chart_data['datasets'][2]['data'].append(0)
        
        current_date += timedelta(days=1)
    
    return jsonify(chart_data)

# Error handlers for reports blueprint

@reports_bp.errorhandler(403)
def reports_forbidden(error):
    """Handle forbidden access to reports"""
    flash('You do not have permission to access this report.', 'error')
    return redirect(url_for('reports.reports_dashboard'))

@reports_bp.errorhandler(500)
def reports_server_error(error):
    """Handle server errors in reports"""
    db.session.rollback()
    current_app.logger.error(f'Reports error: {error}')
    flash('A system error occurred while generating the report. Please try again.', 'error')
    return redirect(url_for('reports.reports_dashboard'))