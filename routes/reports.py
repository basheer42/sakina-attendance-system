"""
Sakina Gas Company - Reports and Analytics Routes
Built from scratch with comprehensive reporting system
Version 3.0 - Enterprise grade with full complexity
FIXED: Models imported inside functions to prevent mapper conflicts
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app, make_response
from flask_login import login_required, current_user
from datetime import datetime, date, timedelta
from sqlalchemy import func, and_, or_, extract, case, desc
from decimal import Decimal
import json
import csv
import io
import calendar

# FIXED: Removed global model imports to prevent early model registration
from database import db

# Create blueprint
reports_bp = Blueprint('reports', __name__)

def check_reports_permission(report_type='basic'):
    """Check if user has permission to access reports"""
    if current_user.role == 'hr_manager':
        return True
    elif current_user.role == 'station_manager' and report_type in ['basic', 'location']:
        return True
    elif current_user.role == 'admin':
        return True
    return False

@reports_bp.route('/dashboard')
@login_required
def reports_dashboard():
    """Reports dashboard with overview of available reports"""
    # FIXED: Local imports
    from models.employee import Employee
    from models.attendance import AttendanceRecord
    from models.leave import LeaveRequest
    from models.audit import AuditLog
    
    if not check_reports_permission():
        flash('You do not have permission to access reports.', 'error')
        return redirect(url_for('dashboard.main'))
    
    # Get quick statistics for dashboard
    today = date.today()
    current_month_start = date(today.year, today.month, 1)
    
    try:
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
            AuditLog.event_action.like('report_%'),
            AuditLog.timestamp >= datetime.utcnow() - timedelta(days=30)
        ).order_by(AuditLog.timestamp.desc()).limit(5).all()
        
        return render_template('reports/dashboard.html',
            total_employees=total_employees,
            today_attendance=today_attendance,
            today_present=today_present,
            attendance_rate=round((today_present / total_employees * 100) if total_employees > 0 else 0, 1),
            month_attendance=month_attendance,
            pending_leaves=pending_leaves,
            current_leaves=current_leaves,
            recent_reports=recent_reports
        )
        
    except Exception as e:
        current_app.logger.error(f"Error in reports dashboard: {e}")
        flash('Error loading reports dashboard. Please try again.', 'error')
        return redirect(url_for('dashboard.main'))

@reports_bp.route('/attendance')
@login_required
def attendance_reports():
    """Comprehensive attendance reports with filtering"""
    # FIXED: Local imports
    from models.employee import Employee
    from models.attendance import AttendanceRecord
    from models.audit import AuditLog
    
    if not check_reports_permission('basic'):
        flash('You do not have permission to access attendance reports.', 'error')
        return redirect(url_for('dashboard.main'))
    
    # Get filter parameters
    start_date_str = request.args.get('start_date', (date.today() - timedelta(days=30)).isoformat())
    end_date_str = request.args.get('end_date', date.today().isoformat())
    location_filter = request.args.get('location', '')
    department_filter = request.args.get('department', '')
    employee_filter = request.args.get('employee', '')
    report_type = request.args.get('type', 'summary')
    
    try:
        # Parse dates
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    except ValueError:
        flash('Invalid date format. Please use YYYY-MM-DD.', 'error')
        start_date = date.today() - timedelta(days=30)
        end_date = date.today()
    
    # Validate date range
    if start_date > end_date:
        flash('Start date must be before end date.', 'error')
        start_date, end_date = end_date, start_date
    
    try:
        # Build base query with user permissions
        if current_user.role in ['hr_manager', 'admin']:
            query = AttendanceRecord.query.join(Employee)
            employee_options = Employee.query.filter(Employee.is_active == True)
            available_locations = list(current_app.config.get('COMPANY_LOCATIONS', {}).keys())
            available_departments = list(current_app.config.get('DEPARTMENTS', {}).keys())
        else:
            query = AttendanceRecord.query.join(Employee).filter(
                Employee.location == current_user.location
            )
            employee_options = Employee.query.filter(
                Employee.is_active == True,
                Employee.location == current_user.location
            )
            available_locations = [current_user.location]
            available_departments = list(current_app.config.get('DEPARTMENTS', {}).keys())
        
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
        
        if report_type == 'summary':
            # Summary report with aggregated data
            template_data['summary_data'] = generate_attendance_summary(query, start_date, end_date)
            
        elif report_type == 'detailed':
            # Detailed daily records
            page = request.args.get('page', 1, type=int)
            per_page = 50
            
            records = query.order_by(
                AttendanceRecord.date.desc(),
                Employee.last_name,
                Employee.first_name
            ).paginate(page=page, per_page=per_page, error_out=False)
            
            template_data['records'] = records
            
        elif report_type == 'monthly':
            # Monthly attendance trends
            template_data['monthly_data'] = generate_monthly_attendance_trends(query, start_date, end_date)
            
        elif report_type == 'employee':
            # Individual employee analysis
            if not employee_filter:
                flash('Please select an employee for individual analysis.', 'warning')
                employee_data = None
            else:
                employee_data = generate_employee_attendance_analysis(employee_filter, start_date, end_date)
            template_data['employee_data'] = employee_data
        
        # Log report access
        AuditLog.log_event(
            event_type='report_attendance_accessed',
            user_id=current_user.id,
            description=f'Attendance report accessed: {report_type} from {start_date} to {end_date}',
            ip_address=request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR'))
        )
        
        return render_template('reports/attendance.html', **template_data)
        
    except Exception as e:
        current_app.logger.error(f"Error in attendance reports: {e}")
        flash('Error generating attendance report. Please try again.', 'error')
@reports_bp.route('/leave')
@login_required
def leave_reports():
    """Comprehensive leave reports and analytics"""
    # FIXED: Local imports
    from models.leave import LeaveRequest
    from models.employee import Employee
    from models.audit import AuditLog
    
    if not check_reports_permission('basic'):
        flash('You do not have permission to access leave reports.', 'error')
        return redirect(url_for('reports.reports_dashboard'))
    
    # Get filter parameters
    year = request.args.get('year', date.today().year, type=int)
    location_filter = request.args.get('location', '')
    department_filter = request.args.get('department', '')
    leave_type_filter = request.args.get('leave_type', '')
    status_filter = request.args.get('status', '')
    report_type = request.args.get('type', 'summary')
    
    try:
        # Build base query with user permissions
        if current_user.role in ['hr_manager', 'admin']:
            query = LeaveRequest.query.join(Employee)
            available_locations = list(current_app.config.get('COMPANY_LOCATIONS', {}).keys())
            available_departments = list(current_app.config.get('DEPARTMENTS', {}).keys())
        else:
            query = LeaveRequest.query.join(Employee).filter(
                Employee.location == current_user.location
            )
            available_locations = [current_user.location]
            available_departments = list(current_app.config.get('DEPARTMENTS', {}).keys())
        
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
        
        # Generate report data
        leave_data = {
            'total_requests': query.count(),
            'approved_requests': query.filter(LeaveRequest.status == 'approved').count(),
            'pending_requests': query.filter(LeaveRequest.status == 'pending').count(),
            'rejected_requests': query.filter(LeaveRequest.status == 'rejected').count()
        }
        
        # Get leave trends by month
        monthly_trends = generate_leave_monthly_trends(query, year)
        
        # Get leave type breakdown
        leave_type_breakdown = generate_leave_type_breakdown(query)
        
        # Log report access
        AuditLog.log_event(
            event_type='report_leave_accessed',
            user_id=current_user.id,
            description=f'Leave report accessed for year {year}',
            ip_address=request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR'))
        )
        
        return render_template('reports/leave.html',
                             year=year,
                             location_filter=location_filter,
                             department_filter=department_filter,
                             leave_type_filter=leave_type_filter,
                             status_filter=status_filter,
                             report_type=report_type,
                             available_locations=available_locations,
                             available_departments=available_departments,
                             leave_data=leave_data,
                             monthly_trends=monthly_trends,
                             leave_type_breakdown=leave_type_breakdown,
                             available_leave_types=get_available_leave_types())
                             
    except Exception as e:
        current_app.logger.error(f"Error in leave reports: {e}")
        flash('Error generating leave report. Please try again.', 'error')
        return redirect(url_for('reports.reports_dashboard'))

@reports_bp.route('/employee')
@login_required
def employee_reports():
    """Employee reports and analytics"""
    # FIXED: Local imports
    from models.employee import Employee
    from models.audit import AuditLog
    
    if not check_reports_permission('basic'):
        flash('You do not have permission to access employee reports.', 'error')
        return redirect(url_for('reports.reports_dashboard'))
    
    try:
        # Get employee statistics
        if current_user.role in ['hr_manager', 'admin']:
            base_query = Employee.query
            available_locations = list(current_app.config.get('COMPANY_LOCATIONS', {}).keys())
        else:
            base_query = Employee.query.filter(Employee.location == current_user.location)
            available_locations = [current_user.location]
        
        # Calculate employee metrics
        employee_metrics = {
            'total_employees': base_query.count(),
            'active_employees': base_query.filter(Employee.is_active == True).count(),
            'inactive_employees': base_query.filter(Employee.is_active == False).count(),
            'by_department': get_department_breakdown(base_query),
            'by_location': get_location_breakdown(base_query),
            'by_employment_type': get_employment_type_breakdown(base_query)
        }
        
        # Log report access
        AuditLog.log_event(
            event_type='report_employee_accessed',
            user_id=current_user.id,
            description='Employee report accessed',
            ip_address=request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR'))
        )
        
        return render_template('reports/employee.html',
                             employee_metrics=employee_metrics,
                             available_locations=available_locations,
                             available_departments=list(current_app.config.get('DEPARTMENTS', {}).keys()))
                             
    except Exception as e:
        current_app.logger.error(f"Error in employee reports: {e}")
        flash('Error generating employee report. Please try again.', 'error')
        return redirect(url_for('reports.reports_dashboard'))

@reports_bp.route('/compliance')
@login_required
def compliance_reports():
    """Compliance and audit reports"""
    # FIXED: Local imports
    from models.leave import LeaveRequest
    from models.employee import Employee
    from models.audit import AuditLog
    
    if current_user.role not in ['hr_manager', 'admin']:
        flash('You do not have permission to access compliance reports.', 'error')
        return redirect(url_for('reports.reports_dashboard'))
    
    try:
        # Get compliance metrics for current year
        current_year = date.today().year
        year_start = date(current_year, 1, 1)
        year_end = date(current_year, 12, 31)
        
        # Leave compliance issues
        compliance_issues = []
        
        # Check for employees exceeding leave entitlements
        leave_entitlements = current_app.config.get('KENYAN_LABOR_LAWS', {}).get('leave_entitlements', {})
        
        for leave_type, details in leave_entitlements.items():
            annual_entitlement = details.get('annual_entitlement', 0)
            if annual_entitlement > 0:
                # Find employees who have exceeded their entitlement
                exceeded_employees = db.session.query(
                    Employee.id,
                    Employee.first_name,
                    Employee.last_name,
                    Employee.employee_id,
                    func.sum(LeaveRequest.total_days).label('total_used')
                ).join(LeaveRequest).filter(
                    LeaveRequest.leave_type == leave_type,
                    LeaveRequest.status == 'approved',
                    func.extract('year', LeaveRequest.start_date) == current_year
                ).group_by(
                    Employee.id,
                    Employee.first_name,
                    Employee.last_name,
                    Employee.employee_id
                ).having(
                    func.sum(LeaveRequest.total_days) > annual_entitlement
                ).all()
                
                for emp in exceeded_employees:
                    compliance_issues.append({
                        'type': 'leave_exceeded',
                        'severity': 'high',
                        'employee_id': emp.employee_id,
                        'employee_name': f"{emp.first_name} {emp.last_name}",
                        'leave_type': leave_type,
                        'entitled': annual_entitlement,
                        'used': int(emp.total_used),
                        'excess': int(emp.total_used) - annual_entitlement
                    })
        
        # Check for pending leave approvals older than 7 days
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        old_pending_leaves = LeaveRequest.query.filter(
            LeaveRequest.status == 'pending',
            LeaveRequest.created_date < seven_days_ago
        ).all()
        
        for leave in old_pending_leaves:
            compliance_issues.append({
                'type': 'pending_approval',
                'severity': 'medium',
                'employee_id': leave.employee.employee_id,
                'employee_name': leave.employee.get_full_name(),
                'leave_type': leave.leave_type,
                'request_date': leave.created_date.date(),
                'days_pending': (datetime.utcnow() - leave.created_date).days
            })
        
        # Recent audit activities
        recent_audits = AuditLog.query.filter(
            AuditLog.timestamp >= datetime.utcnow() - timedelta(days=30)
        ).order_by(desc(AuditLog.timestamp)).limit(50).all()
        
        # Summary statistics
        compliance_summary = {
            'total_issues': len(compliance_issues),
            'high_priority': len([i for i in compliance_issues if i['severity'] == 'high']),
            'medium_priority': len([i for i in compliance_issues if i['severity'] == 'medium']),
            'recent_audits': len(recent_audits),
            'last_audit_date': recent_audits[0].timestamp.date() if recent_audits else None
        }
        
        return render_template('reports/compliance.html',
                             compliance_issues=compliance_issues,
                             compliance_summary=compliance_summary,
                             recent_audits=recent_audits,
                             current_year=current_year)
                             
    except Exception as e:
        current_app.logger.error(f"Error in compliance reports: {e}")
        flash('Error generating compliance report. Please try again.', 'error')
        return redirect(url_for('reports.reports_dashboard'))

@reports_bp.route('/analytics')
@login_required
def analytics_dashboard():
    """Advanced analytics dashboard"""
    if not check_reports_permission('advanced'):
        flash('You do not have permission to access advanced analytics.', 'error')
        return redirect(url_for('reports.reports_dashboard'))
    
    try:
        # This would contain advanced analytics features
        # For now, redirect to main reports dashboard
        flash('Advanced analytics dashboard is under development.', 'info')
        return redirect(url_for('reports.reports_dashboard'))
        
    except Exception as e:
        current_app.logger.error(f"Error in analytics dashboard: {e}")
        flash('Error loading analytics dashboard.', 'error')
        return redirect(url_for('reports.reports_dashboard'))

@reports_bp.route('/payroll')
@login_required
def payroll_reports():
    """Payroll reports and analytics (Placeholder for future payroll integration)"""
    if not check_reports_permission('basic'):
        flash('You do not have permission to access payroll reports.', 'error')
        return redirect(url_for('reports.reports_dashboard'))
    
    flash('Payroll reports feature is under development and will be available in the next version.', 'info')
    return redirect(url_for('reports.reports_dashboard'))

@reports_bp.route('/export/attendance')
@login_required
def export_attendance():
    """Export attendance data to CSV"""
    # FIXED: Local imports
    from models.employee import Employee
    from models.attendance import AttendanceRecord
    
    if not check_reports_permission('basic'):
        return jsonify({'error': 'Permission denied'}), 403
    
    # Get filter parameters
    start_date_str = request.args.get('start_date', (date.today() - timedelta(days=30)).isoformat())
    end_date_str = request.args.get('end_date', date.today().isoformat())
    location_filter = request.args.get('location', '')
    
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        
        # Build query
        if current_user.role in ['hr_manager', 'admin']:
            query = AttendanceRecord.query.join(Employee)
        else:
            query = AttendanceRecord.query.join(Employee).filter(
                Employee.location == current_user.location
            )
        
        query = query.filter(AttendanceRecord.date.between(start_date, end_date))
        
        if location_filter:
            query = query.filter(Employee.location == location_filter)
        
        records = query.order_by(AttendanceRecord.date.desc()).all()
        
        # Create CSV
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Headers
        writer.writerow([
            'Date', 'Employee ID', 'Employee Name', 'Department', 'Location',
            'Status', 'Clock In', 'Clock Out', 'Hours Worked', 'Notes'
        ])
        
        # Data
        for record in records:
            writer.writerow([
                record.date.isoformat(),
                record.employee.employee_id,
                record.employee.get_full_name(),
                record.employee.department,
                record.employee.location,
                record.status,
                record.clock_in_time.strftime('%H:%M') if record.clock_in_time else '',
                record.clock_out_time.strftime('%H:%M') if record.clock_out_time else '',
                f"{record.work_hours:.2f}" if record.work_hours else '0.00',
                record.notes or ''
            ])
        
        output.seek(0)
        
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename=attendance_report_{start_date}_{end_date}.csv'
        
        return response
        
    except Exception as e:
        current_app.logger.error(f"Error exporting attendance: {e}")
        flash('Error exporting attendance data.', 'error')
        return redirect(url_for('reports.attendance_reports'))

@reports_bp.route('/export/leave')
@login_required
def export_leave():
    """Export leave data to CSV"""
    # FIXED: Local imports
    from models.leave import LeaveRequest
    from models.employee import Employee
    
    if not check_reports_permission('basic'):
        return jsonify({'error': 'Permission denied'}), 403
    
    # Get filter parameters
    year = request.args.get('year', date.today().year, type=int)
    location_filter = request.args.get('location', '')
    
    try:
        # Build query
        if current_user.role in ['hr_manager', 'admin']:
            query = LeaveRequest.query.join(Employee)
        else:
            query = LeaveRequest.query.join(Employee).filter(
                Employee.location == current_user.location
            )
        
        # Apply year filter
        year_start = date(year, 1, 1)
        year_end = date(year, 12, 31)
        query = query.filter(LeaveRequest.start_date.between(year_start, year_end))
        
        if location_filter:
            query = query.filter(Employee.location == location_filter)
        
        leave_requests = query.order_by(LeaveRequest.start_date.desc()).all()
        
        # Create CSV
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Headers
        writer.writerow([
            'Leave ID', 'Employee ID', 'Employee Name', 'Department', 'Location',
            'Leave Type', 'Start Date', 'End Date', 'Total Days', 'Status',
            'Request Date', 'Approved Date', 'Reason', 'Comments'
        ])
        
        # Data
        for leave in leave_requests:
            writer.writerow([
                leave.id,
                leave.employee.employee_id,
                leave.employee.get_full_name(),
                leave.employee.department,
                leave.employee.location,
                leave.leave_type,
                leave.start_date.isoformat(),
                leave.end_date.isoformat(),
                leave.total_days,
                leave.status,
                leave.created_date.isoformat(),
                leave.approved_date.isoformat() if leave.approved_date else '',
                leave.reason,
                leave.approval_comments or ''
            ])
        
        output.seek(0)
        
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename=leave_report_{year}_{location_filter or "all"}.csv'
        
        return response
        
    except Exception as e:
        current_app.logger.error(f"Error exporting leave data: {e}")
        flash('Error exporting leave data.', 'error')
        return redirect(url_for('reports.leave_reports'))

@reports_bp.route('/export/employee')
@login_required
def export_employee():
    """Export employee data to CSV"""
    # FIXED: Local imports
    from models.employee import Employee
    
    if not check_reports_permission('basic'):
        return jsonify({'error': 'Permission denied'}), 403
    
    try:
        # Build query
        if current_user.role in ['hr_manager', 'admin']:
            query = Employee.query
        else:
            query = Employee.query.filter(Employee.location == current_user.location)
        
        status_filter = request.args.get('status', 'all')
        if status_filter == 'active':
            query = query.filter(Employee.is_active == True)
        elif status_filter == 'inactive':
            query = query.filter(Employee.is_active == False)
        
        employees = query.order_by(Employee.last_name, Employee.first_name).all()
        
        # Create CSV
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Headers
        writer.writerow([
            'Employee ID', 'First Name', 'Last Name', 'Email', 'Phone',
            'Department', 'Position', 'Location', 'Employment Type',
            'Hire Date', 'Basic Salary', 'Status'
        ])
        
        # Data
        for employee in employees:
            writer.writerow([
                employee.employee_id,
                employee.first_name,
                employee.last_name,
                employee.email,
                employee.phone_number or '',
                employee.department,
                employee.position,
                employee.location,
                employee.employment_type,
                employee.hire_date.isoformat() if employee.hire_date else '',
                float(employee.basic_salary) if employee.basic_salary else 0,
                'Active' if employee.is_active else 'Inactive'
            ])
        
        output.seek(0)
        
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename=employee_report_{status_filter}_{date.today().isoformat()}.csv'
        
        return response
        
    except Exception as e:
        current_app.logger.error(f"Error exporting employee data: {e}")
        flash('Error exporting employee data.', 'error')
        return redirect(url_for('reports.employee_reports'))

@reports_bp.route('/api/attendance-chart')
@login_required
def api_attendance_chart():
    """API endpoint for attendance chart data"""
    # FIXED: Local imports
    from models.employee import Employee
    from models.attendance import AttendanceRecord
    
    if not check_reports_permission('basic'):
        return jsonify({'error': 'Permission denied'}), 403
    
    try:
        days = request.args.get('days', 30, type=int)
        start_date = date.today() - timedelta(days=days)
        
        # Build query based on user role
        if current_user.role in ['hr_manager', 'admin']:
            query = AttendanceRecord.query.join(Employee)
        else:
            query = AttendanceRecord.query.join(Employee).filter(
                Employee.location == current_user.location
            )
        
        # Get daily attendance data
        daily_data = []
        for i in range(days + 1):
            target_date = start_date + timedelta(days=i)
            
            day_records = query.filter(AttendanceRecord.date == target_date).all()
            
            present_count = len([r for r in day_records if r.status in ['present', 'late']])
            absent_count = len([r for r in day_records if r.status == 'absent'])
            
            daily_data.append({
                'date': target_date.isoformat(),
                'present': present_count,
                'absent': absent_count,
                'total': present_count + absent_count
            })
        
        return jsonify({
            'success': True,
            'data': daily_data
        })
        
    except Exception as e:
        current_app.logger.error(f"Error generating attendance chart data: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@reports_bp.route('/api/leave-trends')
@login_required
def api_leave_trends():
    """API endpoint for leave trends chart data"""
    # FIXED: Local imports
    from models.leave import LeaveRequest
    from models.employee import Employee
    
    if not check_reports_permission('basic'):
        return jsonify({'error': 'Permission denied'}), 403
    
    try:
        year = request.args.get('year', date.today().year, type=int)
        
        # Build query based on user role
        if current_user.role in ['hr_manager', 'admin']:
            query = LeaveRequest.query.join(Employee)
        else:
            query = LeaveRequest.query.join(Employee).filter(
                Employee.location == current_user.location
            )
        
        # Filter by year
        year_start = date(year, 1, 1)
        year_end = date(year, 12, 31)
        query = query.filter(LeaveRequest.start_date.between(year_start, year_end))
        
        # Get monthly data
        monthly_data = []
        for month in range(1, 13):
            month_start = date(year, month, 1)
            if month == 12:
                month_end = date(year + 1, 1, 1) - timedelta(days=1)
            else:
                month_end = date(year, month + 1, 1) - timedelta(days=1)
            
            month_leaves = query.filter(
                LeaveRequest.start_date.between(month_start, month_end)
            ).all()
            
            monthly_data.append({
                'month': calendar.month_abbr[month],
                'total': len(month_leaves),
                'approved': len([l for l in month_leaves if l.status == 'approved']),
                'pending': len([l for l in month_leaves if l.status == 'pending']),
                'rejected': len([l for l in month_leaves if l.status == 'rejected'])
            })
        
        return jsonify({
            'success': True,
            'data': monthly_data
        })
        
    except Exception as e:
        current_app.logger.error(f"Error generating leave trends data: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@reports_bp.route('/api/department-stats')
@login_required
def api_department_stats():
    """API endpoint for department statistics"""
    # FIXED: Local imports
    from models.employee import Employee
    
    if not check_reports_permission('basic'):
        return jsonify({'error': 'Permission denied'}), 403
    
    try:
        # Build query based on user role
        if current_user.role in ['hr_manager', 'admin']:
            query = Employee.query
        else:
            query = Employee.query.filter(Employee.location == current_user.location)
        
        # Get department statistics
        dept_stats = []
        departments = current_app.config.get('DEPARTMENTS', {})
        
        for dept_key, dept_info in departments.items():
            dept_employees = query.filter(Employee.department == dept_key).all()
            active_count = len([e for e in dept_employees if e.is_active])
            inactive_count = len([e for e in dept_employees if not e.is_active])
            
            dept_stats.append({
                'department': dept_info.get('name', dept_key.replace('_', ' ').title()),
                'code': dept_key,
                'active': active_count,
                'inactive': inactive_count,
                'total': active_count + inactive_count
            })
        
        return jsonify({
            'success': True,
            'data': dept_stats
        })
        
    except Exception as e:
        current_app.logger.error(f"Error generating department stats: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500
# Helper Functions

def generate_attendance_summary(query, start_date, end_date):
    """Generate attendance summary data"""
    records = query.all()
    
    total_records = len(records)
    present_count = len([r for r in records if r.status in ['present', 'late']])
    absent_count = len([r for r in records if r.status == 'absent'])
    late_count = len([r for r in records if r.status == 'late'])
    
    total_hours = sum(float(r.work_hours or 0) for r in records)
    total_overtime = sum(float(r.overtime_hours or 0) for r in records)
    
    return {
        'total_records': total_records,
        'present_count': present_count,
        'absent_count': absent_count,
        'late_count': late_count,
        'attendance_rate': round((present_count / total_records * 100) if total_records > 0 else 0, 1),
        'total_hours': round(total_hours, 2),
        'total_overtime': round(total_overtime, 2),
        'average_daily_hours': round(total_hours / total_records, 2) if total_records > 0 else 0
    }

def generate_monthly_attendance_trends(query, start_date, end_date):
    """Generate monthly attendance trend data"""
    monthly_data = []
    
    current_date = start_date.replace(day=1)
    while current_date <= end_date:
        # Get last day of the month
        if current_date.month == 12:
            next_month = current_date.replace(year=current_date.year + 1, month=1)
        else:
            next_month = current_date.replace(month=current_date.month + 1)
        
        month_end = next_month - timedelta(days=1)
        
        # Filter records for this month
        month_records = [r for r in query.all() if current_date <= r.date <= month_end]
        
        present_count = len([r for r in month_records if r.status in ['present', 'late']])
        absent_count = len([r for r in month_records if r.status == 'absent'])
        
        monthly_data.append({
            'month': current_date.strftime('%Y-%m'),
            'month_name': current_date.strftime('%B %Y'),
            'present': present_count,
            'absent': absent_count,
            'total': present_count + absent_count,
            'attendance_rate': round((present_count / (present_count + absent_count) * 100) if (present_count + absent_count) > 0 else 0, 1)
        })
        
        current_date = next_month
        
    return monthly_data

def generate_employee_attendance_analysis(employee_id, start_date, end_date):
    """Generate individual employee attendance analysis"""
    # FIXED: Local imports
    from models.employee import Employee
    from models.attendance import AttendanceRecord
    
    employee = Employee.query.get(employee_id)
    if not employee:
        return None
    
    records = AttendanceRecord.query.filter(
        AttendanceRecord.employee_id == employee_id,
        AttendanceRecord.date.between(start_date, end_date)
    ).all()
    
    present_count = len([r for r in records if r.status in ['present', 'late']])
    absent_count = len([r for r in records if r.status == 'absent'])
    late_count = len([r for r in records if r.status == 'late'])
    
    total_hours = sum(float(r.work_hours or 0) for r in records)
    
    return {
        'employee': employee,
        'total_days': len(records),
        'present_days': present_count,
        'absent_days': absent_count,
        'late_days': late_count,
        'attendance_rate': round((present_count / len(records) * 100) if records else 0, 1),
        'punctuality_rate': round(((present_count - late_count) / len(records) * 100) if records else 0, 1),
        'total_hours': round(total_hours, 2),
        'average_hours_per_day': round(total_hours / len(records), 2) if records else 0
    }

def generate_leave_monthly_trends(query, year):
    """Generate leave monthly trends"""
    monthly_trends = []
    
    for month in range(1, 13):
        month_start = date(year, month, 1)
        if month == 12:
            month_end = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            month_end = date(year, month + 1, 1) - timedelta(days=1)
        
        month_leaves = query.filter(
            LeaveRequest.start_date.between(month_start, month_end)
        ).all()
        
        monthly_trends.append({
            'month': month,
            'month_name': calendar.month_name[month],
            'total_requests': len(month_leaves),
            'approved': len([l for l in month_leaves if l.status == 'approved']),
            'pending': len([l for l in month_leaves if l.status == 'pending']),
            'rejected': len([l for l in month_leaves if l.status == 'rejected'])
        })
    
    return monthly_trends

def generate_leave_type_breakdown(query):
    """Generate leave type breakdown"""
    leave_types = {}
    
    for leave_request in query.all():
        leave_type = leave_request.leave_type
        if leave_type not in leave_types:
            leave_types[leave_type] = {
                'total': 0,
                'approved': 0,
                'pending': 0,
                'rejected': 0,
                'total_days': 0
            }
        
        leave_types[leave_type]['total'] += 1
        leave_types[leave_type][leave_request.status] += 1
        if leave_request.status == 'approved':
            leave_types[leave_type]['total_days'] += leave_request.total_days or 0
    
    return leave_types

def get_available_leave_types():
    """Get available leave types from configuration"""
    labor_laws = current_app.config.get('KENYAN_LABOR_LAWS', {})
    leave_entitlements = labor_laws.get('leave_entitlements', {})
    
    return [(k, v.get('display_name', k.replace('_', ' ').title())) 
            for k, v in leave_entitlements.items()]

def get_department_breakdown(base_query):
    """Get employee breakdown by department"""
    # FIXED: Local imports
    from models.employee import Employee
    
    breakdown = {}
    
    departments = current_app.config.get('DEPARTMENTS', {})
    
    for dept_key in departments.keys():
        count = base_query.filter(Employee.department == dept_key).count()
        breakdown[dept_key] = count
    
    return breakdown

def get_location_breakdown(base_query):
    """Get employee breakdown by location"""
    # FIXED: Local imports  
    from models.employee import Employee
    
    breakdown = {}
    
    locations = current_app.config.get('COMPANY_LOCATIONS', {})
    
    for location_key in locations.keys():
        count = base_query.filter(Employee.location == location_key).count()
        breakdown[location_key] = count
    
    return breakdown

def get_employment_type_breakdown(base_query):
    """Get employee breakdown by employment type"""
    # FIXED: Local imports
    from models.employee import Employee
    
    breakdown = {}
    
    employment_types = ['permanent', 'contract', 'casual', 'intern']
    
    for emp_type in employment_types:
        count = base_query.filter(Employee.employment_type == emp_type).count()
        breakdown[emp_type] = count
    
    return breakdown

def generate_turnover_analytics(start_date, end_date):
    """Generate turnover analytics"""
    # FIXED: Local imports
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
    # FIXED: Local imports
    from models.performance import PerformanceReview
    from models.leave import LeaveRequest
    from models.employee import Employee
    
    today = date.today()
    
    # Overdue performance reviews
    try:
        overdue_reviews = PerformanceReview.query.filter(
            PerformanceReview.due_date < today,
            PerformanceReview.status.in_(['draft', 'in_progress'])
        ).count()
    except:
        overdue_reviews = 0
    
    # Pending leave approvals (>3 days old)
    old_pending_leaves = LeaveRequest.query.filter(
        LeaveRequest.status == 'pending',
        LeaveRequest.requested_date < datetime.utcnow() - timedelta(days=3)
    ).count()
    
    # Employees without recent performance reviews
    one_year_ago = today - timedelta(days=365)
    try:
        employees_needing_review = Employee.query.filter(
            Employee.is_active == True,
            ~Employee.id.in_(
                db.session.query(PerformanceReview.employee_id).filter(
                    PerformanceReview.review_date > one_year_ago
                )
            )
        ).count()
    except:
        employees_needing_review = 0
    
    return {
        'overdue_reviews': overdue_reviews,
        'old_pending_leaves': old_pending_leaves,
        'employees_needing_review': employees_needing_review,
        'last_calculated': datetime.utcnow().isoformat()
    }

def calculate_advanced_metrics():
    """Calculate advanced HR metrics"""
    # FIXED: Local imports
    from models.employee import Employee
    from models.attendance import AttendanceRecord
    from models.leave import LeaveRequest
    
    try:
        today = date.today()
        thirty_days_ago = today - timedelta(days=30)
        
        # Average tenure
        active_employees = Employee.query.filter(Employee.is_active == True).all()
        total_tenure_days = sum(
            (today - emp.hire_date).days for emp in active_employees if emp.hire_date
        )
        avg_tenure_years = round(
            (total_tenure_days / len(active_employees) / 365.25), 1
        ) if active_employees else 0
        
        # Attendance rate (last 30 days)
        attendance_records = AttendanceRecord.query.filter(
            AttendanceRecord.date >= thirty_days_ago
        ).all()
        
        present_records = [r for r in attendance_records if r.status in ['present', 'late']]
        attendance_rate = round(
            (len(present_records) / len(attendance_records) * 100), 1
        ) if attendance_records else 0
        
        # Leave utilization rate
        current_year = today.year
        approved_leaves = LeaveRequest.query.filter(
            LeaveRequest.status == 'approved',
            func.extract('year', LeaveRequest.start_date) == current_year
        ).all()
        
        total_leave_days = sum(leave.total_days or 0 for leave in approved_leaves)
        total_entitled_days = len(active_employees) * 21  # 21 days annual leave
        leave_utilization = round(
            (total_leave_days / total_entitled_days * 100), 1
        ) if total_entitled_days > 0 else 0
        
        return {
            'average_tenure_years': avg_tenure_years,
            'attendance_rate_30_days': attendance_rate,
            'leave_utilization_rate': leave_utilization,
            'total_active_employees': len(active_employees)
        }
        
    except Exception as e:
        current_app.logger.error(f"Error calculating advanced metrics: {e}")
        return {
            'average_tenure_years': 0,
            'attendance_rate_30_days': 0,
            'leave_utilization_rate': 0,
            'total_active_employees': 0
        }

def get_performance_indicators():
    """Get key performance indicators for dashboard"""
    try:
        basic_metrics = calculate_advanced_metrics()
        compliance_metrics = generate_compliance_metrics()
        
        # Calculate overall health score
        health_factors = []
        
        if basic_metrics['attendance_rate_30_days'] >= 90:
            health_factors.append(25)
        elif basic_metrics['attendance_rate_30_days'] >= 80:
            health_factors.append(15)
        else:
            health_factors.append(0)
        
        if compliance_metrics['old_pending_leaves'] == 0:
            health_factors.append(25)
        elif compliance_metrics['old_pending_leaves'] <= 5:
            health_factors.append(15)
        else:
            health_factors.append(0)
        
        if compliance_metrics['overdue_reviews'] == 0:
            health_factors.append(25)
        elif compliance_metrics['overdue_reviews'] <= 10:
            health_factors.append(15)
        else:
            health_factors.append(0)
        
        if basic_metrics['leave_utilization_rate'] >= 60 and basic_metrics['leave_utilization_rate'] <= 80:
            health_factors.append(25)
        else:
            health_factors.append(10)
        
        overall_health = sum(health_factors)
        
        return {
            'basic_metrics': basic_metrics,
            'compliance_metrics': compliance_metrics,
            'overall_health_score': overall_health,
            'health_status': 'Excellent' if overall_health >= 80 else 'Good' if overall_health >= 60 else 'Needs Attention'
        }
        
    except Exception as e:
        current_app.logger.error(f"Error getting performance indicators: {e}")
        return {
            'basic_metrics': calculate_advanced_metrics(),
            'compliance_metrics': generate_compliance_metrics(),
            'overall_health_score': 0,
            'health_status': 'Unknown'
        }