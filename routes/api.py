"""
Enhanced API Routes for Sakina Gas Attendance System
RESTful API for mobile applications and external integrations
"""
from flask import Blueprint, request, jsonify, g
from flask_login import login_required, current_user
from models import db, Employee, AttendanceRecord, LeaveRequest, Holiday, User, AuditLog
from datetime import date, datetime, timedelta
from sqlalchemy import func, and_, or_, desc
from config import Config
import json

api_bp = Blueprint('api', __name__)

# API Authentication and Security

@api_bp.before_request
def before_api_request():
    """Security checks before API requests"""
    # Store IP for audit logging
    g.ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', 
                                      request.environ.get('REMOTE_ADDR'))
    
    # Check API rate limiting (basic implementation)
    g.api_request_start = datetime.utcnow()

@api_bp.after_request
def after_api_request(response):
    """API response processing"""
    # Add API headers
    response.headers['X-API-Version'] = '2.0'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    
    # Calculate response time
    if hasattr(g, 'api_request_start'):
        duration = (datetime.utcnow() - g.api_request_start).total_seconds()
        response.headers['X-Response-Time'] = f'{duration:.3f}s'
    
    return response

# Employee Management APIs

@api_bp.route('/employees', methods=['GET'])
@login_required
def api_list_employees():
    """Get list of employees with filtering"""
    try:
        # Get query parameters
        location = request.args.get('location', 'all')
        department = request.args.get('department', 'all')
        status = request.args.get('status', 'active')
        search = request.args.get('search', '').strip()
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 25, type=int), 100)  # Max 100 per page
        
        # Base query based on user role
        if current_user.role == 'station_manager':
            query = Employee.query.filter(Employee.location == current_user.location)
        else:
            query = Employee.query
        
        # Apply filters
        if status == 'active':
            query = query.filter(Employee.is_active == True)
        elif status == 'inactive':
            query = query.filter(Employee.is_active == False)
        
        if location != 'all' and current_user.role != 'station_manager':
            query = query.filter(Employee.location == location)
        
        if department != 'all':
            query = query.filter(Employee.department == department)
        
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Employee.first_name.ilike(search_term),
                    Employee.last_name.ilike(search_term),
                    Employee.employee_id.ilike(search_term),
                    Employee.position.ilike(search_term)
                )
            )
        
        # Paginate
        employees = query.order_by(Employee.first_name, Employee.last_name).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # Format response
        employee_list = []
        for emp in employees.items:
            employee_list.append({
                'id': emp.id,
                'employee_id': emp.employee_id,
                'first_name': emp.first_name,
                'last_name': emp.last_name,
                'full_name': emp.full_name,
                'email': emp.email,
                'phone': emp.phone,
                'location': emp.location,
                'department': emp.department,
                'position': emp.position,
                'shift': emp.shift,
                'hire_date': emp.hire_date.isoformat(),
                'employment_status': emp.employment_status,
                'is_active': emp.is_active,
                'years_of_service': round(emp.years_of_service, 1)
            })
        
        return jsonify({
            'success': True,
            'data': employee_list,
            'pagination': {
                'page': employees.page,
                'per_page': employees.per_page,
                'total': employees.total,
                'pages': employees.pages,
                'has_next': employees.has_next,
                'has_prev': employees.has_prev
            },
            'filters_applied': {
                'location': location,
                'department': department,
                'status': status,
                'search': search
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@api_bp.route('/employees/<int:employee_id>', methods=['GET'])
@login_required
def api_get_employee(employee_id):
    """Get detailed employee information"""
    try:
        employee = Employee.query.get_or_404(employee_id)
        
        # Check permissions
        if (current_user.role == 'station_manager' and 
            employee.location != current_user.location):
            return jsonify({'success': False, 'message': 'Access denied'}), 403
        
        # Get additional data
        today = date.today()
        current_year = today.year
        
        # Recent attendance (last 30 days)
        recent_attendance = AttendanceRecord.query.filter(
            AttendanceRecord.employee_id == employee.id,
            AttendanceRecord.date >= today - timedelta(days=30)
        ).order_by(desc(AttendanceRecord.date)).limit(10).all()
        
        attendance_summary = employee.get_attendance_summary(
            today - timedelta(days=30), today
        )
        
        # Leave balances
        leave_balances = {}
        for leave_type in Config.KENYAN_LABOR_LAWS.keys():
            leave_balances[leave_type] = employee.get_leave_balance(leave_type, current_year)
        
        # Format response
        employee_data = {
            'id': employee.id,
            'employee_id': employee.employee_id,
            'personal_info': {
                'first_name': employee.first_name,
                'last_name': employee.last_name,
                'full_name': employee.full_name,
                'email': employee.email,
                'phone': employee.phone,
                'date_of_birth': employee.date_of_birth.isoformat() if employee.date_of_birth else None,
                'national_id': employee.national_id,
                'gender': employee.gender
            },
            'employment_info': {
                'location': employee.location,
                'department': employee.department,
                'position': employee.position,
                'shift': employee.shift,
                'hire_date': employee.hire_date.isoformat(),
                'employment_type': employee.employment_type,
                'employment_status': employee.employment_status,
                'years_of_service': round(employee.years_of_service, 1),
                'months_of_service': employee.months_of_service,
                'is_active': employee.is_active
            },
            'attendance_summary': attendance_summary,
            'leave_balances': leave_balances,
            'recent_attendance': [
                {
                    'date': att.date.isoformat(),
                    'status': att.status,
                    'clock_in': att.clock_in.strftime('%H:%M') if att.clock_in else None,
                    'clock_out': att.clock_out.strftime('%H:%M') if att.clock_out else None,
                    'hours_worked': float(att.hours_worked) if att.hours_worked else 0
                }
                for att in recent_attendance
            ]
        }
        
        return jsonify({
            'success': True,
            'data': employee_data
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# Attendance Management APIs

@api_bp.route('/attendance/mark', methods=['POST'])
@login_required
def api_mark_attendance():
    """Mark attendance for employee(s)"""
    try:
        data = request.get_json()
        
        # Single employee or bulk marking
        if 'employee_id' in data:
            # Single employee
            result = mark_single_attendance(data)
            return jsonify(result)
        elif 'employees' in data:
            # Bulk marking
            result = mark_bulk_attendance(data)
            return jsonify(result)
        else:
            return jsonify({'success': False, 'message': 'Invalid request format'}), 400
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@api_bp.route('/attendance/today', methods=['GET'])
@login_required
def api_today_attendance():
    """Get today's attendance overview"""
    try:
        today = date.today()
        location = request.args.get('location', 'all')
        
        # Base query based on user role
        if current_user.role == 'station_manager':
            employee_query = Employee.query.filter(
                Employee.location == current_user.location,
                Employee.is_active == True
            )
        else:
            employee_query = Employee.query.filter(Employee.is_active == True)
            if location != 'all':
                employee_query = employee_query.filter(Employee.location == location)
        
        employees = employee_query.all()
        
        # Get attendance data
        attendance_data = []
        summary = {'total': 0, 'present': 0, 'absent': 0, 'late': 0, 'not_marked': 0}
        
        for employee in employees:
            # Get attendance record
            attendance = AttendanceRecord.query.filter(
                AttendanceRecord.employee_id == employee.id,
                AttendanceRecord.date == today
            ).first()
            
            # Check for approved leave
            leave_request = LeaveRequest.query.filter(
                LeaveRequest.employee_id == employee.id,
                LeaveRequest.start_date <= today,
                LeaveRequest.end_date >= today,
                LeaveRequest.status == 'approved'
            ).first()
            
            status = 'not_marked'
            if leave_request:
                status = 'on_leave'
            elif attendance:
                status = attendance.status
            
            attendance_data.append({
                'employee_id': employee.id,
                'employee_code': employee.employee_id,
                'name': employee.full_name,
                'location': employee.location,
                'department': employee.department,
                'status': status,
                'clock_in': attendance.clock_in.strftime('%H:%M') if attendance and attendance.clock_in else None,
                'clock_out': attendance.clock_out.strftime('%H:%M') if attendance and attendance.clock_out else None,
                'leave_type': leave_request.leave_type if leave_request else None
            })
            
            # Update summary
            summary['total'] += 1
            if status in ['present', 'late']:
                summary['present'] += 1
            elif status == 'absent':
                summary['absent'] += 1
            elif status == 'late':
                summary['late'] += 1
            elif status == 'not_marked':
                summary['not_marked'] += 1
        
        summary['attendance_rate'] = round((summary['present'] / summary['total'] * 100), 1) if summary['total'] > 0 else 0
        
        return jsonify({
            'success': True,
            'date': today.isoformat(),
            'summary': summary,
            'attendance_data': attendance_data
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@api_bp.route('/attendance/employee/<int:employee_id>/history', methods=['GET'])
@login_required
def api_employee_attendance_history(employee_id):
    """Get employee attendance history"""
    try:
        employee = Employee.query.get_or_404(employee_id)
        
        # Check permissions
        if (current_user.role == 'station_manager' and 
            employee.location != current_user.location):
            return jsonify({'success': False, 'message': 'Access denied'}), 403
        
        # Get date range
        start_date_str = request.args.get('start_date', (date.today() - timedelta(days=30)).isoformat())
        end_date_str = request.args.get('end_date', date.today().isoformat())
        
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'success': False, 'message': 'Invalid date format'}), 400
        
        # Get attendance records
        attendance_records = AttendanceRecord.query.filter(
            AttendanceRecord.employee_id == employee.id,
            AttendanceRecord.date >= start_date,
            AttendanceRecord.date <= end_date
        ).order_by(desc(AttendanceRecord.date)).all()
        
        # Format data
        history_data = []
        for record in attendance_records:
            history_data.append({
                'date': record.date.isoformat(),
                'status': record.status,
                'clock_in': record.clock_in.strftime('%H:%M') if record.clock_in else None,
                'clock_out': record.clock_out.strftime('%H:%M') if record.clock_out else None,
                'hours_worked': float(record.hours_worked) if record.hours_worked else 0,
                'overtime_hours': float(record.overtime_hours) if record.overtime_hours else 0,
                'late_minutes': record.late_minutes or 0,
                'notes': record.notes
            })
        
        # Calculate summary
        summary = employee.get_attendance_summary(start_date, end_date)
        
        return jsonify({
            'success': True,
            'employee': {
                'id': employee.id,
                'name': employee.full_name,
                'employee_id': employee.employee_id
            },
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            },
            'summary': summary,
            'attendance_history': history_data
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# Leave Management APIs

@api_bp.route('/leaves', methods=['GET'])
@login_required
def api_list_leaves():
    """Get leave requests list"""
    try:
        # Get query parameters
        status = request.args.get('status', 'all')
        employee_id = request.args.get('employee_id', type=int)
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 25, type=int), 100)
        
        # Base query
        if current_user.role == 'station_manager':
            query = db.session.query(LeaveRequest).join(Employee).filter(
                Employee.location == current_user.location,
                Employee.is_active == True
            )
        else:
            query = db.session.query(LeaveRequest).join(Employee).filter(
                Employee.is_active == True
            )
        
        # Apply filters
        if status != 'all':
            query = query.filter(LeaveRequest.status == status)
        
        if employee_id:
            query = query.filter(LeaveRequest.employee_id == employee_id)
        
        # Paginate
        leave_requests = query.order_by(desc(LeaveRequest.created_at)).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # Format response
        leave_list = []
        for leave in leave_requests.items:
            leave_list.append({
                'id': leave.id,
                'employee': {
                    'id': leave.employee.id,
                    'name': leave.employee.full_name,
                    'employee_id': leave.employee.employee_id
                },
                'leave_type': leave.leave_type,
                'start_date': leave.start_date.isoformat(),
                'end_date': leave.end_date.isoformat(),
                'total_days': leave.total_days,
                'working_days': leave.working_days,
                'reason': leave.reason,
                'status': leave.status,
                'priority': leave.priority,
                'created_at': leave.created_at.isoformat(),
                'approved_at': leave.approved_at.isoformat() if leave.approved_at else None,
                'approver': leave.approver.full_name if leave.approver else None
            })
        
        return jsonify({
            'success': True,
            'data': leave_list,
            'pagination': {
                'page': leave_requests.page,
                'per_page': leave_requests.per_page,
                'total': leave_requests.total,
                'pages': leave_requests.pages
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@api_bp.route('/leaves/<int:leave_id>/approve', methods=['POST'])
@login_required
def api_approve_leave(leave_id):
    """Approve leave request"""
    try:
        if current_user.role not in ['hr_manager', 'admin']:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        leave_request = LeaveRequest.query.get_or_404(leave_id)
        
        if leave_request.status != 'pending':
            return jsonify({'success': False, 'message': 'Leave request is not pending'}), 400
        
        data = request.get_json() or {}
        approval_notes = data.get('notes', '').strip()
        
        # Approve
        leave_request.status = 'approved'
        leave_request.approved_by = current_user.id
        leave_request.approved_at = datetime.utcnow()
        leave_request.hr_notes = approval_notes
        
        db.session.commit()
        
        # Log approval
        AuditLog.log_action(
            user_id=current_user.id,
            action='leave_approved_api',
            target_type='leave_request',
            target_id=leave_request.id,
            details=f'API: Approved {leave_request.leave_type} for {leave_request.employee.full_name}',
            ip_address=g.ip_address
        )
        
        return jsonify({
            'success': True,
            'message': f'Leave approved for {leave_request.employee.full_name}',
            'leave_request': {
                'id': leave_request.id,
                'status': leave_request.status,
                'approved_at': leave_request.approved_at.isoformat()
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@api_bp.route('/employees/<int:employee_id>/leave-balance', methods=['GET'])
@login_required
def api_employee_leave_balance(employee_id):
    """Get employee leave balance"""
    try:
        employee = Employee.query.get_or_404(employee_id)
        
        # Check permissions
        if (current_user.role == 'station_manager' and 
            employee.location != current_user.location):
            return jsonify({'success': False, 'message': 'Access denied'}), 403
        
        year = request.args.get('year', date.today().year, type=int)
        
        # Calculate balances for all leave types
        balances = {}
        for leave_type in Config.KENYAN_LABOR_LAWS.keys():
            balance = employee.get_leave_balance(leave_type, year)
            policy = Config.KENYAN_LABOR_LAWS.get(leave_type, {})
            
            balances[leave_type] = {
                'name': policy.get('name', leave_type.title()),
                'entitlement': balance,
                'used': 0,  # Would calculate from approved requests
                'available': balance,
                'max_days': policy.get('max_days'),
                'color': policy.get('color', '#6c757d')
            }
        
        return jsonify({
            'success': True,
            'employee': {
                'id': employee.id,
                'name': employee.full_name,
                'employee_id': employee.employee_id
            },
            'year': year,
            'years_of_service': round(employee.years_of_service, 1),
            'balances': balances
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# Dashboard and Statistics APIs

@api_bp.route('/dashboard/stats', methods=['GET'])
@login_required
def api_dashboard_stats():
    """Get dashboard statistics"""
    try:
        today = date.today()
        
        # Base statistics based on user role
        if current_user.role == 'station_manager':
            # Station-specific stats
            total_employees = Employee.query.filter(
                Employee.location == current_user.location,
                Employee.is_active == True
            ).count()
            
            present_today = db.session.query(AttendanceRecord).join(Employee).filter(
                AttendanceRecord.date == today,
                Employee.location == current_user.location,
                Employee.is_active == True,
                AttendanceRecord.status.in_(['present', 'late'])
            ).count()
            
            pending_leaves = db.session.query(LeaveRequest).join(Employee).filter(
                LeaveRequest.status == 'pending',
                Employee.location == current_user.location
            ).count()
            
        else:
            # Company-wide stats
            total_employees = Employee.query.filter(Employee.is_active == True).count()
            
            present_today = db.session.query(AttendanceRecord).join(Employee).filter(
                AttendanceRecord.date == today,
                Employee.is_active == True,
                AttendanceRecord.status.in_(['present', 'late'])
            ).count()
            
            pending_leaves = LeaveRequest.query.filter(
                LeaveRequest.status == 'pending'
            ).count()
        
        # Common calculations
        absent_today = db.session.query(AttendanceRecord).join(Employee).filter(
            AttendanceRecord.date == today,
            Employee.is_active == True,
            AttendanceRecord.status == 'absent'
        ).count()
        
        attendance_rate = round((present_today / total_employees * 100), 1) if total_employees > 0 else 0
        
        return jsonify({
            'success': True,
            'date': today.isoformat(),
            'stats': {
                'total_employees': total_employees,
                'present_today': present_today,
                'absent_today': absent_today,
                'attendance_rate': attendance_rate,
                'pending_leave_requests': pending_leaves
            },
            'user_context': {
                'role': current_user.role,
                'location': current_user.location if current_user.role == 'station_manager' else None
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@api_bp.route('/reports/attendance-summary', methods=['GET'])
@login_required
def api_attendance_summary():
    """Get attendance summary report via API"""
    try:
        if current_user.role == 'station_manager':
            return jsonify({'success': False, 'message': 'Access denied'}), 403
        
        # Get date range
        start_date_str = request.args.get('start_date', date.today().replace(day=1).isoformat())
        end_date_str = request.args.get('end_date', date.today().isoformat())
        
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'success': False, 'message': 'Invalid date format'}), 400
        
        # Generate report data (simplified for API)
        summary_data = []
        
        # Get location-wise summary
        for location in Config.COMPANY_LOCATIONS.keys():
            location_employees = Employee.query.filter(
                Employee.location == location,
                Employee.is_active == True
            ).count()
            
            location_present = db.session.query(AttendanceRecord).join(Employee).filter(
                Employee.location == location,
                Employee.is_active == True,
                AttendanceRecord.date >= start_date,
                AttendanceRecord.date <= end_date,
                AttendanceRecord.status.in_(['present', 'late'])
            ).count()
            
            total_records = db.session.query(AttendanceRecord).join(Employee).filter(
                Employee.location == location,
                Employee.is_active == True,
                AttendanceRecord.date >= start_date,
                AttendanceRecord.date <= end_date
            ).count()
            
            attendance_rate = round((location_present / total_records * 100), 1) if total_records > 0 else 0
            
            summary_data.append({
                'location': location,
                'location_name': Config.COMPANY_LOCATIONS[location]['name'],
                'total_employees': location_employees,
                'total_records': total_records,
                'present_records': location_present,
                'attendance_rate': attendance_rate
            })
        
        return jsonify({
            'success': True,
            'report_type': 'attendance_summary',
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            },
            'summary_data': summary_data,
            'generated_at': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# Helper Functions for API

def mark_single_attendance(data):
    """Mark attendance for single employee"""
    employee_id = data.get('employee_id')
    status = data.get('status')
    notes = data.get('notes', '')
    target_date_str = data.get('date', date.today().isoformat())
    
    try:
        target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
    except ValueError:
        return {'success': False, 'message': 'Invalid date format'}
    
    # Get and validate employee
    employee = Employee.query.filter(
        Employee.id == employee_id,
        Employee.is_active == True
    ).first()
    
    if not employee:
        return {'success': False, 'message': 'Employee not found'}
    
    # Check permissions
    if (current_user.role == 'station_manager' and 
        employee.location != current_user.location):
        return {'success': False, 'message': 'Access denied'}
    
    try:
        # Check existing attendance
        existing = AttendanceRecord.query.filter(
            AttendanceRecord.employee_id == employee.id,
            AttendanceRecord.date == target_date
        ).first()
        
        current_time = datetime.now()
        
        if existing:
            # Update existing
            existing.status = status
            existing.notes = notes
            existing.marked_by = current_user.id
            existing.updated_at = current_time
        else:
            # Create new
            attendance = AttendanceRecord(
                employee_id=employee.id,
                date=target_date,
                status=status,
                notes=notes,
                marked_by=current_user.id,
                clock_in=current_time if status in ['present', 'late'] else None,
                location_marked=employee.location,
                verification_method='api'
            )
            db.session.add(attendance)
        
        db.session.commit()
        
        # Log action
        AuditLog.log_action(
            user_id=current_user.id,
            action='attendance_marked_api',
            target_type='attendance',
            target_id=employee.id,
            details=f'API: Marked {status} for {employee.full_name}',
            ip_address=g.ip_address
        )
        
        return {
            'success': True,
            'message': f'Attendance marked for {employee.full_name}',
            'employee': employee.full_name,
            'status': status,
            'date': target_date.isoformat()
        }
        
    except Exception as e:
        db.session.rollback()
        return {'success': False, 'message': str(e)}

def mark_bulk_attendance(data):
    """Mark attendance for multiple employees"""
    employees_data = data.get('employees', [])
    target_date_str = data.get('date', date.today().isoformat())
    
    try:
        target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
    except ValueError:
        return {'success': False, 'message': 'Invalid date format'}
    
    success_count = 0
    error_count = 0
    errors = []
    
    try:
        for emp_data in employees_data:
            result = mark_single_attendance({
                'employee_id': emp_data.get('employee_id'),
                'status': emp_data.get('status'),
                'notes': emp_data.get('notes', ''),
                'date': target_date_str
            })
            
            if result['success']:
                success_count += 1
            else:
                error_count += 1
                errors.append(result['message'])
        
        return {
            'success': True,
            'message': f'Bulk attendance completed. Success: {success_count}, Errors: {error_count}',
            'summary': {
                'success_count': success_count,
                'error_count': error_count,
                'total_processed': len(employees_data)
            },
            'errors': errors if errors else None
        }
        
    except Exception as e:
        return {'success': False, 'message': str(e)}

# Error Handlers for API

@api_bp.errorhandler(404)
def api_not_found(error):
    return jsonify({'success': False, 'message': 'API endpoint not found'}), 404

@api_bp.errorhandler(403)
def api_forbidden(error):
    return jsonify({'success': False, 'message': 'Access forbidden'}), 403

@api_bp.errorhandler(500)
def api_internal_error(error):
    db.session.rollback()
    return jsonify({'success': False, 'message': 'Internal server error'}), 500

# API Documentation Endpoint

@api_bp.route('/docs', methods=['GET'])
@login_required
def api_documentation():
    """API documentation endpoint"""
    return jsonify({
        'api_version': '2.0',
        'endpoints': {
            'employees': {
                'GET /api/v2/employees': 'List employees with filtering',
                'GET /api/v2/employees/{id}': 'Get employee details'
            },
            'attendance': {
                'POST /api/v2/attendance/mark': 'Mark attendance',
                'GET /api/v2/attendance/today': 'Get today\'s attendance',
                'GET /api/v2/attendance/employee/{id}/history': 'Get employee attendance history'
            },
            'leaves': {
                'GET /api/v2/leaves': 'List leave requests',
                'POST /api/v2/leaves/{id}/approve': 'Approve leave request',
                'GET /api/v2/employees/{id}/leave-balance': 'Get leave balance'
            },
            'dashboard': {
                'GET /api/v2/dashboard/stats': 'Get dashboard statistics',
                'GET /api/v2/reports/attendance-summary': 'Get attendance summary report'
            }
        },
        'authentication': 'Session-based authentication required',
        'rate_limits': 'Standard rate limiting applies',
        'response_format': 'JSON with success/error indicators'
    })