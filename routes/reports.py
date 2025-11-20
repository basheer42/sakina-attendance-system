"""
Enhanced Reports Routes for Sakina Gas Attendance System
Comprehensive reporting and analytics dashboard
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, make_response
from flask_login import login_required, current_user
from models import db, Employee, AttendanceRecord, LeaveRequest, Holiday, AuditLog, PerformanceReview
from datetime import date, datetime, timedelta
from sqlalchemy import func, and_, or_, desc, extract
from config import Config
import json
import csv
import io

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/')
@login_required
def dashboard():
    """Reports dashboard with overview of all available reports"""
    if current_user.role == 'station_manager':
        flash('Access denied. HR Manager privileges required for comprehensive reports.', 'danger')
        return redirect(url_for('dashboard.station_overview'))
    
    # Get quick statistics for dashboard
    quick_stats = get_quick_report_stats()
    
    # Get recent report activities
    recent_reports = AuditLog.query.filter(
        AuditLog.action.like('%report%')
    ).order_by(desc(AuditLog.timestamp)).limit(10).all()
    
    return render_template('reports/dashboard.html',
                         quick_stats=quick_stats,
                         recent_reports=recent_reports)

@reports_bp.route('/attendance')
@login_required
def attendance_reports():
    """Comprehensive attendance reporting"""
    if current_user.role == 'station_manager':
        flash('Access denied. HR Manager privileges required.', 'danger')
        return redirect(url_for('dashboard.station_overview'))
    
    # Get parameters
    report_type = request.args.get('type', 'summary')
    start_date_str = request.args.get('start_date', date.today().replace(day=1).isoformat())
    end_date_str = request.args.get('end_date', date.today().isoformat())
    location_filter = request.args.get('location', 'all')
    department_filter = request.args.get('department', 'all')
    
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    except ValueError:
        start_date = date.today().replace(day=1)
        end_date = date.today()
    
    # Generate report data
    if report_type == 'summary':
        report_data = generate_attendance_summary_report(start_date, end_date, location_filter, department_filter)
    elif report_type == 'detailed':
        report_data = generate_detailed_attendance_report(start_date, end_date, location_filter, department_filter)
    elif report_type == 'trends':
        report_data = generate_attendance_trends_report(start_date, end_date, location_filter, department_filter)
    elif report_type == 'compliance':
        report_data = generate_attendance_compliance_report(start_date, end_date, location_filter, department_filter)
    else:
        report_data = generate_attendance_summary_report(start_date, end_date, location_filter, department_filter)
    
    # Get filter options
    filter_options = {
        'locations': ['all'] + list(Config.COMPANY_LOCATIONS.keys()),
        'departments': ['all'] + list(Config.DEPARTMENTS.keys())
    }
    
    return render_template('reports/attendance.html',
                         report_data=report_data,
                         report_type=report_type,
                         start_date=start_date,
                         end_date=end_date,
                         location_filter=location_filter,
                         department_filter=department_filter,
                         filter_options=filter_options)

@reports_bp.route('/export/<report_type>')
@login_required
def export_report(report_type):
    """Export reports to CSV format"""
    if current_user.role == 'station_manager':
        return jsonify({'error': 'Access denied'}), 403
    
    # Get parameters from request
    start_date_str = request.args.get('start_date', date.today().replace(day=1).isoformat())
    end_date_str = request.args.get('end_date', date.today().isoformat())
    location_filter = request.args.get('location', 'all')
    department_filter = request.args.get('department', 'all')
    
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    except ValueError:
        start_date = date.today().replace(day=1)
        end_date = date.today()
    
    # Generate CSV data based on report type
    if report_type == 'attendance_summary':
        csv_data = export_attendance_summary_csv(start_date, end_date, location_filter, department_filter)
        filename = f'attendance_summary_{start_date}_to_{end_date}.csv'
    elif report_type == 'leave_balance':
        csv_data = export_leave_balance_csv(location_filter, department_filter)
        filename = f'leave_balance_{date.today().isoformat()}.csv'
    elif report_type == 'employee_list':
        csv_data = export_employee_list_csv(location_filter, department_filter)
        filename = f'employee_list_{date.today().isoformat()}.csv'
    else:
        return jsonify({'error': 'Invalid report type'}), 400
    
    # Create CSV response
    output = io.StringIO()
    output.write(csv_data)
    output.seek(0)
    
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'
    
    # Log the export
    AuditLog.log_action(
        user_id=current_user.id,
        action='report_exported',
        target_type='report',
        details=f'Exported {report_type} report',
        ip_address=request.remote_addr
    )
    
    return response

# Helper Functions

def get_quick_report_stats():
    """Get quick statistics for reports dashboard"""
    today = date.today()
    this_month = today.replace(day=1)
    
    stats = {
        'total_employees': Employee.query.filter(Employee.is_active == True).count(),
        'today_present': db.session.query(AttendanceRecord).join(Employee).filter(
            AttendanceRecord.date == today,
            Employee.is_active == True,
            AttendanceRecord.status.in_(['present', 'late'])
        ).count(),
        'pending_leaves': LeaveRequest.query.filter(
            LeaveRequest.status == 'pending'
        ).count(),
        'this_month_leaves': LeaveRequest.query.filter(
            LeaveRequest.start_date >= this_month,
            LeaveRequest.status == 'approved'
        ).count()
    }
    
    return stats

def generate_attendance_summary_report(start_date, end_date, location_filter, department_filter):
    """Generate attendance summary report"""
    # Base query
    query = db.session.query(
        Employee.id,
        Employee.employee_id,
        Employee.first_name,
        Employee.last_name,
        Employee.location,
        Employee.department,
        func.count(AttendanceRecord.id).label('total_days'),
        func.sum(func.case([(AttendanceRecord.status.in_(['present', 'late']), 1)], else_=0)).label('present_days'),
        func.sum(func.case([(AttendanceRecord.status == 'absent', 1)], else_=0)).label('absent_days'),
        func.sum(func.case([(AttendanceRecord.status == 'late', 1)], else_=0)).label('late_days'),
        func.sum(AttendanceRecord.hours_worked).label('total_hours'),
        func.sum(AttendanceRecord.overtime_hours).label('overtime_hours')
    ).join(AttendanceRecord).filter(
        Employee.is_active == True,
        AttendanceRecord.date >= start_date,
        AttendanceRecord.date <= end_date
    )
    
    # Apply filters
    if location_filter != 'all':
        query = query.filter(Employee.location == location_filter)
    
    if department_filter != 'all':
        query = query.filter(Employee.department == department_filter)
    
    # Group by employee
    results = query.group_by(Employee.id).all()
    
    # Calculate summary statistics
    summary = {
        'total_employees': len(results),
        'total_days_recorded': sum(r.total_days for r in results),
        'total_present_days': sum(r.present_days or 0 for r in results),
        'total_absent_days': sum(r.absent_days or 0 for r in results),
        'total_hours_worked': sum(float(r.total_hours or 0) for r in results),
        'total_overtime_hours': sum(float(r.overtime_hours or 0) for r in results),
        'average_attendance_rate': 0
    }
    
    if summary['total_days_recorded'] > 0:
        summary['average_attendance_rate'] = round(
            (summary['total_present_days'] / summary['total_days_recorded']) * 100, 2
        )
    
    return {
        'type': 'attendance_summary',
        'period': f"{start_date} to {end_date}",
        'employee_data': results,
        'summary': summary,
        'location_filter': location_filter,
        'department_filter': department_filter
    }

def generate_detailed_attendance_report(start_date, end_date, location_filter, department_filter):
    """Generate detailed daily attendance report"""
    # Get all attendance records in date range
    query = db.session.query(AttendanceRecord, Employee).join(Employee).filter(
        Employee.is_active == True,
        AttendanceRecord.date >= start_date,
        AttendanceRecord.date <= end_date
    )
    
    # Apply filters
    if location_filter != 'all':
        query = query.filter(Employee.location == location_filter)
    
    if department_filter != 'all':
        query = query.filter(Employee.department == department_filter)
    
    # Order by date and employee
    results = query.order_by(desc(AttendanceRecord.date), Employee.first_name).all()
    
    # Group by date
    daily_data = {}
    for attendance, employee in results:
        date_key = attendance.date.isoformat()
        if date_key not in daily_data:
            daily_data[date_key] = {
                'date': attendance.date,
                'records': [],
                'summary': {'present': 0, 'absent': 0, 'late': 0, 'total': 0}
            }
        
        daily_data[date_key]['records'].append({
            'attendance': attendance,
            'employee': employee
        })
        
        # Update daily summary
        daily_data[date_key]['summary']['total'] += 1
        if attendance.status in ['present', 'late']:
            daily_data[date_key]['summary']['present'] += 1
        if attendance.status == 'late':
            daily_data[date_key]['summary']['late'] += 1
        if attendance.status == 'absent':
            daily_data[date_key]['summary']['absent'] += 1
    
    return {
        'type': 'detailed_attendance',
        'period': f"{start_date} to {end_date}",
        'daily_data': daily_data,
        'total_days': len(daily_data)
    }

def generate_attendance_trends_report(start_date, end_date, location_filter, department_filter):
    """Generate attendance trends analysis"""
    # Daily attendance rates
    daily_trends = []
    current_date = start_date
    
    while current_date <= end_date:
        if current_date.weekday() < 5:  # Weekdays only
            # Get day's statistics
            query = db.session.query(AttendanceRecord).join(Employee).filter(
                Employee.is_active == True,
                AttendanceRecord.date == current_date
            )
            
            # Apply filters
            if location_filter != 'all':
                query = query.filter(Employee.location == location_filter)
            
            if department_filter != 'all':
                query = query.filter(Employee.department == department_filter)
            
            total = query.count()
            present = query.filter(AttendanceRecord.status.in_(['present', 'late'])).count()
            late = query.filter(AttendanceRecord.status == 'late').count()
            
            daily_trends.append({
                'date': current_date,
                'total': total,
                'present': present,
                'late': late,
                'attendance_rate': round((present / total * 100), 1) if total > 0 else 0
            })
        
        current_date += timedelta(days=1)
    
    return {
        'type': 'attendance_trends',
        'period': f"{start_date} to {end_date}",
        'daily_trends': daily_trends
    }

def generate_attendance_compliance_report(start_date, end_date, location_filter, department_filter):
    """Generate attendance compliance report"""
    # Employees with excessive absences
    excessive_absences = db.session.query(
        Employee.id,
        Employee.employee_id,
        Employee.first_name,
        Employee.last_name,
        Employee.location,
        Employee.department,
        func.count(AttendanceRecord.id).label('absent_days')
    ).join(AttendanceRecord).filter(
        Employee.is_active == True,
        AttendanceRecord.date >= start_date,
        AttendanceRecord.date <= end_date,
        AttendanceRecord.status == 'absent'
    )
    
    # Apply filters
    if location_filter != 'all':
        excessive_absences = excessive_absences.filter(Employee.location == location_filter)
    
    if department_filter != 'all':
        excessive_absences = excessive_absences.filter(Employee.department == department_filter)
    
    excessive_absences = excessive_absences.group_by(Employee.id).having(
        func.count(AttendanceRecord.id) > 5  # More than 5 absences
    ).all()
    
    return {
        'type': 'attendance_compliance',
        'period': f"{start_date} to {end_date}",
        'excessive_absences': excessive_absences,
        'total_compliance_issues': len(excessive_absences)
    }

def export_attendance_summary_csv(start_date, end_date, location_filter, department_filter):
    """Export attendance summary to CSV"""
    report_data = generate_attendance_summary_report(start_date, end_date, location_filter, department_filter)
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow([
        'Employee ID', 'Full Name', 'Location', 'Department',
        'Total Days', 'Present Days', 'Absent Days', 'Late Days',
        'Total Hours', 'Overtime Hours', 'Attendance Rate'
    ])
    
    # Data
    for record in report_data['employee_data']:
        attendance_rate = round((record.present_days / record.total_days * 100), 1) if record.total_days > 0 else 0
        writer.writerow([
            record.employee_id,
            f"{record.first_name} {record.last_name}",
            record.location,
            record.department,
            record.total_days,
            record.present_days or 0,
            record.absent_days or 0,
            record.late_days or 0,
            round(float(record.total_hours or 0), 2),
            round(float(record.overtime_hours or 0), 2),
            attendance_rate
        ])
    
    return output.getvalue()

def export_leave_balance_csv(location_filter, department_filter):
    """Export leave balance to CSV"""
    query = Employee.query.filter(Employee.is_active == True)
    
    if location_filter != 'all':
        query = query.filter(Employee.location == location_filter)
    
    if department_filter != 'all':
        query = query.filter(Employee.department == department_filter)
    
    employees = query.order_by(Employee.first_name, Employee.last_name).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    header = ['Employee ID', 'Full Name', 'Location', 'Department', 'Years of Service']
    for leave_type in Config.KENYAN_LABOR_LAWS.keys():
        header.extend([f'{leave_type.title()} Entitlement', f'{leave_type.title()} Available'])
    
    writer.writerow(header)
    
    # Data
    current_year = date.today().year
    for employee in employees:
        row = [
            employee.employee_id,
            employee.full_name,
            employee.location,
            employee.department,
            round(employee.years_of_service, 1)
        ]
        
        for leave_type in Config.KENYAN_LABOR_LAWS.keys():
            balance = employee.get_leave_balance(leave_type, current_year)
            row.extend([balance, balance])  # Simplified - would need actual balance calculation
        
        writer.writerow(row)
    
    return output.getvalue()

def export_employee_list_csv(location_filter, department_filter):
    """Export employee list to CSV"""
    query = Employee.query.filter(Employee.is_active == True)
    
    if location_filter != 'all':
        query = query.filter(Employee.location == location_filter)
    
    if department_filter != 'all':
        query = query.filter(Employee.department == department_filter)
    
    employees = query.order_by(Employee.first_name, Employee.last_name).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow([
        'Employee ID', 'Full Name', 'Email', 'Phone', 'Location',
        'Department', 'Position', 'Hire Date', 'Employment Type',
        'Employment Status', 'Basic Salary'
    ])
    
    # Data
    for employee in employees:
        writer.writerow([
            employee.employee_id,
            employee.full_name,
            employee.email or '',
            employee.phone or '',
            employee.location,
            employee.department,
            employee.position,
            employee.hire_date.isoformat(),
            employee.employment_type or '',
            employee.employment_status or '',
            float(employee.basic_salary or 0)
        ])
    
    return output.getvalue()