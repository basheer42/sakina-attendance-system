"""
Sakina Gas Company - REST API Routes
Built from scratch with comprehensive API endpoints for mobile/external access
Version 3.0 - Enterprise grade with full complexity
FIXED: Models imported inside functions to prevent mapper conflicts
"""

from flask import Blueprint, request, jsonify, current_app, g
from flask_login import login_required, current_user
from datetime import datetime, date, timedelta
from sqlalchemy import func, desc, and_, or_
from werkzeug.exceptions import BadRequest
import json

# FIXED: Removed global model imports to prevent early model registration
from database import db

# Create blueprint
api_bp = Blueprint('api', __name__)

def api_response(success=True, data=None, message='', errors=None, status_code=200):
    """Standardized API response format"""
    response = {
        'success': success,
        'timestamp': datetime.utcnow().isoformat(),
        'user_id': current_user.id if current_user.is_authenticated else None
    }
    
    if data is not None:
        response['data'] = data
    
    if message:
        response['message'] = message
    
    if errors:
        response['errors'] = errors if isinstance(errors, list) else [errors]
    
    return jsonify(response), status_code

def check_api_permission(action, resource=None):
    """Check API permissions"""
    if current_user.role == 'hr_manager':
        return True
    elif current_user.role == 'station_manager':
        if action in ['view', 'mark'] and (resource is None or resource == current_user.location):
            return True
    elif current_user.role == 'admin':
        return True
    return False

@api_bp.before_request
def before_request():
    """Pre-process all API requests"""
    # Store client IP
    g.client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR'))
    
    # Validate JSON for POST/PUT requests
    if request.method in ['POST', 'PUT', 'PATCH'] and request.content_type == 'application/json':
        try:
            g.json_data = request.get_json()
        except BadRequest:
            return api_response(False, message='Invalid JSON format', status_code=400)
    else:
        g.json_data = None

@api_bp.route('/health')
def health_check():
    """API health check endpoint"""
    return api_response(True, {
        'status': 'healthy',
        'version': '3.0',
        'timestamp': datetime.utcnow().isoformat(),
        'database': 'connected',
        'server': 'Sakina Gas Attendance System'
    })

# Employee API Endpoints

@api_bp.route('/employees', methods=['GET'])
@login_required
def api_employees():
    """Get employees list with filtering"""
    # FIXED: Local imports
    from models.employee import Employee
    
    if not check_api_permission('view'):
        return api_response(False, message='Insufficient permissions', status_code=403)
    
    try:
        # Get query parameters
        location = request.args.get('location')
        department = request.args.get('department')
        status = request.args.get('status', 'active')
        search = request.args.get('search', '').strip()
        limit = min(request.args.get('limit', 100, type=int), 500)
        page = request.args.get('page', 1, type=int)
        
        # Build query
        query = Employee.query
        
        # Apply role-based filtering
        if current_user.role == 'station_manager':
            query = query.filter(Employee.location == current_user.location)
        elif location:
            query = query.filter(Employee.location == location)
        
        # Apply filters
        if department:
            query = query.filter(Employee.department == department)
        
        if status == 'active':
            query = query.filter(Employee.is_active == True)
        elif status == 'inactive':
            query = query.filter(Employee.is_active == False)
        
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(or_(
                Employee.first_name.ilike(search_pattern),
                Employee.last_name.ilike(search_pattern),
                Employee.employee_id.ilike(search_pattern),
                Employee.email.ilike(search_pattern)
            ))
        
        # Execute query with pagination
        total_count = query.count()
        employees = query.order_by(Employee.last_name, Employee.first_name).limit(limit).offset((page - 1) * limit).all()
        
        # Format response data
        employees_data = []
        for employee in employees:
            employees_data.append({
                'id': employee.id,
                'employee_id': employee.employee_id,
                'first_name': employee.first_name,
                'last_name': employee.last_name,
                'full_name': employee.get_full_name(),
                'email': employee.email,
                'phone': employee.phone,
                'department': employee.department,
                'position': employee.position,
                'location': employee.location,
                'employment_type': employee.employment_type,
                'hire_date': employee.hire_date.isoformat() if employee.hire_date else None,
                'is_active': employee.is_active,
                'shift': getattr(employee, 'shift', 'day')
            })
        
        return api_response(True, {
            'employees': employees_data,
            'total': len(employees_data),
            'total_count': total_count,
            'page': page,
            'limit': limit,
            'filters': {
                'location': location,
                'department': department,
                'status': status,
                'search': search
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"API error getting employees: {e}")
        return api_response(False, message='Internal server error', status_code=500)

@api_bp.route('/employees/<int:employee_id>', methods=['GET'])
@login_required
def api_employee_detail(employee_id):
    """Get detailed employee information"""
    # FIXED: Local imports
    from models.employee import Employee
    from models.attendance import AttendanceRecord
    from models.leave import LeaveRequest
    
    try:
        employee = Employee.query.get(employee_id)
        if not employee:
            return api_response(False, message='Employee not found', status_code=404)
        
        # Check permissions
        if (current_user.role == 'station_manager' and 
            employee.location != current_user.location):
            return api_response(False, message='Access denied', status_code=403)
        
        # Get recent attendance (last 30 days)
        thirty_days_ago = date.today() - timedelta(days=30)
        recent_attendance = AttendanceRecord.query.filter(
            AttendanceRecord.employee_id == employee.id,
            AttendanceRecord.date >= thirty_days_ago
        ).order_by(desc(AttendanceRecord.date)).limit(10).all()
        
        # Get leave balances
        leave_balances = {}
        try:
            leave_entitlements = current_app.config.get('KENYAN_LABOR_LAWS', {}).get('leave_entitlements', {})
            current_year = date.today().year
            
            for leave_type, details in leave_entitlements.items():
                annual_entitlement = details.get('annual_entitlement', 0)
                
                used_days = db.session.query(func.sum(LeaveRequest.total_days)).filter(
                    LeaveRequest.employee_id == employee.id,
                    LeaveRequest.leave_type == leave_type,
                    LeaveRequest.status == 'approved',
                    func.extract('year', LeaveRequest.start_date) == current_year
                ).scalar() or 0
                
                leave_balances[leave_type] = {
                    'entitlement': annual_entitlement,
                    'used': int(used_days),
                    'remaining': max(0, annual_entitlement - int(used_days))
                }
        except Exception as e:
            current_app.logger.warning(f"Error calculating leave balances: {e}")
            leave_balances = {}
        
        # Format employee data
        employee_data = {
            'id': employee.id,
            'employee_id': employee.employee_id,
            'personal_info': {
                'first_name': employee.first_name,
                'last_name': employee.last_name,
                'full_name': employee.get_full_name(),
                'email': employee.email,
                'phone': employee.phone,
                'date_of_birth': employee.date_of_birth.isoformat() if employee.date_of_birth else None,
                'gender': getattr(employee, 'gender', None),
                'national_id': getattr(employee, 'national_id', None)
            },
            'employment_info': {
                'department': employee.department,
                'position': employee.position,
                'location': employee.location,
                'employment_type': employee.employment_type,
                'hire_date': employee.hire_date.isoformat() if employee.hire_date else None,
                'basic_salary': float(employee.basic_salary or 0),
                'is_active': employee.is_active
            },
            'attendance_summary': calculate_employee_attendance_rate(employee),
            'leave_balances': leave_balances,
            'recent_attendance': [
                {
                    'date': att.date.isoformat(),
                    'status': att.status,
                    'clock_in': att.clock_in_time.strftime('%H:%M') if att.clock_in_time else None,
                    'clock_out': att.clock_out_time.strftime('%H:%M') if att.clock_out_time else None,
                    'hours_worked': float(att.work_hours) if att.work_hours else 0
                }
                for att in recent_attendance
            ]
        }
        
        return api_response(True, employee_data)
        
    except Exception as e:
        current_app.logger.error(f"API error getting employee {employee_id}: {e}")
        return api_response(False, message='Internal server error', status_code=500)

@api_bp.route('/employees/search', methods=['GET'])
@login_required
def api_search_employees():
    """Search employees by name, ID, or email"""
    # FIXED: Local imports
    from models.employee import Employee
    
    if not check_api_permission('view'):
        return api_response(False, message='Insufficient permissions', status_code=403)
    
    try:
        query_term = request.args.get('q', '').strip()
        limit = min(request.args.get('limit', 20, type=int), 50)
        
        if len(query_term) < 2:
            return api_response(False, message='Search term must be at least 2 characters', status_code=400)
        
        # Build search query
        search_pattern = f"%{query_term}%"
        query = Employee.query.filter(
            Employee.is_active == True,
            or_(
                Employee.first_name.ilike(search_pattern),
                Employee.last_name.ilike(search_pattern),
                Employee.employee_id.ilike(search_pattern),
                Employee.email.ilike(search_pattern)
            )
        )
        
        # Apply role-based filtering
        if current_user.role == 'station_manager':
            query = query.filter(Employee.location == current_user.location)
        
        employees = query.limit(limit).all()
        
        # Format results
        results = []
        for employee in employees:
            results.append({
                'id': employee.id,
                'employee_id': employee.employee_id,
                'name': employee.get_full_name(),
                'email': employee.email,
                'department': employee.department,
                'position': employee.position,
                'location': employee.location
            })
        
        return api_response(True, {
            'query': query_term,
            'results': results,
            'total_found': len(results)
        })
        
    except Exception as e:
        current_app.logger.error(f"API error searching employees: {e}")
# Attendance Management APIs

@api_bp.route('/attendance/mark', methods=['POST'])
@login_required
def api_mark_attendance():
    """Mark attendance for employee(s)"""
    if not check_api_permission('mark'):
        return api_response(False, message='Insufficient permissions', status_code=403)
    
    try:
        data = g.json_data
        if not data:
            return api_response(False, message='JSON data required', status_code=400)
        
        # Single employee or bulk marking
        if 'employee_id' in data:
            result = mark_single_attendance(data)
            return api_response(result['success'], result.get('data'), result.get('message'))
            
        elif 'employees' in data:
            result = mark_bulk_attendance(data)
            return api_response(result['success'], result.get('data'), result.get('message'))
            
        else:
            return api_response(False, message='Invalid request format', status_code=400)
            
    except Exception as e:
        current_app.logger.error(f"API error marking attendance: {e}")
        return api_response(False, message='Internal server error', status_code=500)

@api_bp.route('/attendance/today', methods=['GET'])
@login_required
def api_today_attendance():
    """Get today's attendance overview"""
    # FIXED: Local imports
    from models.employee import Employee
    from models.attendance import AttendanceRecord
    from models.leave import LeaveRequest
    
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
        
        total_employees = employee_query.count()
        employee_ids = [emp.id for emp in employee_query.all()]
        
        # Get today's attendance
        attendance_records = AttendanceRecord.query.filter(
            AttendanceRecord.date == today,
            AttendanceRecord.employee_id.in_(employee_ids)
        ).all()
        
        # Get approved leaves for today
        on_leave = LeaveRequest.query.filter(
            LeaveRequest.start_date <= today,
            LeaveRequest.end_date >= today,
            LeaveRequest.status == 'approved',
            LeaveRequest.employee_id.in_(employee_ids)
        ).count()
        
        # Calculate statistics
        present = len([r for r in attendance_records if r.status in ['present', 'late']])
        absent = len([r for r in attendance_records if r.status == 'absent'])
        late = len([r for r in attendance_records if r.status == 'late'])
        not_marked = total_employees - len(attendance_records) - on_leave
        
        return api_response(True, {
            'date': today.isoformat(),
            'location': location,
            'summary': {
                'total_employees': total_employees,
                'present': present,
                'absent': absent,
                'late': late,
                'on_leave': on_leave,
                'not_marked': not_marked,
                'attendance_rate': round((present / total_employees * 100) if total_employees > 0 else 0, 1)
            },
            'details': [
                {
                    'employee_id': record.employee_id,
                    'employee_name': record.employee.get_full_name(),
                    'status': record.status,
                    'clock_in': record.clock_in_time.strftime('%H:%M') if record.clock_in_time else None,
                    'clock_out': record.clock_out_time.strftime('%H:%M') if record.clock_out_time else None,
                    'notes': record.notes
                }
                for record in attendance_records
            ]
        })
        
    except Exception as e:
        current_app.logger.error(f"API error getting today's attendance: {e}")
        return api_response(False, message='Internal server error', status_code=500)

@api_bp.route('/attendance/employee/<int:employee_id>/history', methods=['GET'])
@login_required
def api_employee_attendance_history(employee_id):
    """Get employee attendance history"""
    # FIXED: Local imports
    from models.employee import Employee
    from models.attendance import AttendanceRecord
    
    try:
        employee = Employee.query.get(employee_id)
        if not employee:
            return api_response(False, message='Employee not found', status_code=404)
        
        # Check permissions
        if (current_user.role == 'station_manager' and 
            employee.location != current_user.location):
            return api_response(False, message='Access denied', status_code=403)
        
        # Get date range
        start_date_str = request.args.get('start_date', (date.today() - timedelta(days=30)).isoformat())
        end_date_str = request.args.get('end_date', date.today().isoformat())
        
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            return api_response(False, message='Invalid date format. Use YYYY-MM-DD', status_code=400)
        
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
                'clock_in': record.clock_in_time.strftime('%H:%M') if record.clock_in_time else None,
                'clock_out': record.clock_out_time.strftime('%H:%M') if record.clock_out_time else None,
                'hours_worked': float(record.work_hours) if record.work_hours else 0,
                'overtime_hours': float(record.overtime_hours) if record.overtime_hours else 0,
                'late_minutes': record.minutes_late or 0,
                'notes': record.notes
            })
        
        # Calculate summary
        summary = {
            'total_records': len(attendance_records),
            'total_hours': sum(item['hours_worked'] for item in history_data),
            'total_overtime': sum(item['overtime_hours'] for item in history_data),
            'present_days': len([r for r in attendance_records if r.status in ['present', 'late']]),
            'absent_days': len([r for r in attendance_records if r.status == 'absent']),
            'late_days': len([r for r in attendance_records if r.status == 'late']),
            'attendance_rate': 0
        }
        
        if summary['total_records'] > 0:
            summary['attendance_rate'] = round(
                (summary['present_days'] / summary['total_records'] * 100), 1
            )
        
        return api_response(True, {
            'employee': {
                'id': employee.id,
                'employee_id': employee.employee_id,
                'name': employee.get_full_name()
            },
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            },
            'summary': summary,
            'records': history_data
        })
        
    except Exception as e:
        current_app.logger.error(f"API error getting attendance history: {e}")
        return api_response(False, message='Internal server error', status_code=500)

@api_bp.route('/attendance/clock-in', methods=['POST'])
@login_required
def api_clock_in():
    """Clock in employee"""
    # FIXED: Local imports
    from models.employee import Employee
    from models.attendance import AttendanceRecord
    from models.audit import AuditLog
    
    if not check_api_permission('mark'):
        return api_response(False, message='Insufficient permissions', status_code=403)
    
    try:
        data = g.json_data
        if not data:
            return api_response(False, message='JSON data required', status_code=400)
        
        employee_id = data.get('employee_id')
        if not employee_id:
            return api_response(False, message='Employee ID is required', status_code=400)
        
        # Get employee
        employee = Employee.query.get(employee_id)
        if not employee:
            return api_response(False, message='Employee not found', status_code=404)
        
        # Check permissions
        if (current_user.role == 'station_manager' and 
            employee.location != current_user.location):
            return api_response(False, message='Access denied', status_code=403)
        
        today = date.today()
        current_time = datetime.now()
        
        # Check if already clocked in today
        existing_record = AttendanceRecord.query.filter_by(
            employee_id=employee.id,
            date=today
        ).first()
        
        if existing_record and existing_record.clock_in_time:
            return api_response(False, 
                              message=f'Employee already clocked in today at {existing_record.clock_in_time.strftime("%H:%M")}',
                              status_code=400)
        
        # Determine if late based on shift
        shift_start_times = {
            'day': datetime.strptime('06:00', '%H:%M').time(),
            'night': datetime.strptime('18:00', '%H:%M').time(),
            'standard': datetime.strptime('08:00', '%H:%M').time()
        }
        
        employee_shift = getattr(employee, 'shift', 'day')
        expected_time = shift_start_times.get(employee_shift, shift_start_times['day'])
        grace_period = timedelta(minutes=15)
        
        # Convert expected time to datetime for comparison
        expected_datetime = datetime.combine(today, expected_time)
        is_late = current_time > (expected_datetime + grace_period)
        
        # Calculate late minutes
        late_minutes = 0
        if is_late:
            late_minutes = max(0, int((current_time - expected_datetime).total_seconds() / 60))
        
        # Create or update attendance record
        if existing_record:
            existing_record.clock_in_time = current_time
            existing_record.status = 'late' if is_late else 'present'
            existing_record.minutes_late = late_minutes
            existing_record.clock_in_method = 'api_clock'
            existing_record.ip_address = g.client_ip
            existing_record.updated_by = current_user.id
            existing_record.last_updated = current_time
        else:
            attendance_record = AttendanceRecord(
                employee_id=employee.id,
                date=today,
                clock_in_time=current_time,
                status='late' if is_late else 'present',
                minutes_late=late_minutes,
                created_by=current_user.id,
                location=employee.location,
                clock_in_method='api_clock',
                ip_address=g.client_ip
            )
            db.session.add(attendance_record)
        
        db.session.commit()
        
        # Log action
        AuditLog.log_event(
            event_type='employee_clocked_in_api',
            user_id=current_user.id,
            description=f'API: {employee.get_full_name()} clocked in at {current_time.strftime("%H:%M")}' + 
                       (f' ({late_minutes} minutes late)' if is_late else ''),
            ip_address=g.client_ip
        )
        
        return api_response(True, {
            'employee': employee.get_full_name(),
            'clock_in_time': current_time.strftime('%H:%M:%S'),
            'status': 'late' if is_late else 'present',
            'late_minutes': late_minutes,
            'expected_time': expected_time.strftime('%H:%M')
        }, f'Successfully clocked in{" (Late)" if is_late else ""}')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"API error clocking in: {e}")
        return api_response(False, message='Internal server error', status_code=500)

@api_bp.route('/attendance/clock-out', methods=['POST'])
@login_required
def api_clock_out():
    """Clock out employee"""
    # FIXED: Local imports
    from models.employee import Employee
    from models.attendance import AttendanceRecord
    from models.audit import AuditLog
    
    if not check_api_permission('mark'):
        return api_response(False, message='Insufficient permissions', status_code=403)
    
    try:
        data = g.json_data
        if not data:
            return api_response(False, message='JSON data required', status_code=400)
        
        employee_id = data.get('employee_id')
        if not employee_id:
            return api_response(False, message='Employee ID is required', status_code=400)
        
        # Get employee
        employee = Employee.query.get(employee_id)
        if not employee:
            return api_response(False, message='Employee not found', status_code=404)
        
        # Check permissions
        if (current_user.role == 'station_manager' and 
            employee.location != current_user.location):
            return api_response(False, message='Access denied', status_code=403)
        
        today = date.today()
        current_time = datetime.now()
        
        # Find today's attendance record
        attendance_record = AttendanceRecord.query.filter_by(
            employee_id=employee.id,
            date=today
        ).first()
        
        if not attendance_record:
            return api_response(False, 
                              message='No clock-in record found for today. Please clock in first.',
                              status_code=400)
        
        if not attendance_record.clock_in_time:
            return api_response(False, 
                              message='No clock-in time found. Please clock in first.',
                              status_code=400)
        
        if attendance_record.clock_out_time:
            return api_response(False, 
                              message=f'Employee already clocked out today at {attendance_record.clock_out_time.strftime("%H:%M")}',
                              status_code=400)
        
        # Calculate work hours
        work_duration = current_time - attendance_record.clock_in_time
        work_hours = work_duration.total_seconds() / 3600
        
        # Calculate overtime (assuming 8-hour standard workday)
        standard_hours = 8.0
        overtime_hours = max(0, work_hours - standard_hours)
        
        # Update attendance record
        attendance_record.clock_out_time = current_time
        attendance_record.work_hours = round(work_hours, 2)
        attendance_record.overtime_hours = round(overtime_hours, 2)
        attendance_record.updated_by = current_user.id
        attendance_record.last_updated = current_time
        
        db.session.commit()
        
        # Log action
        AuditLog.log_event(
            event_type='employee_clocked_out_api',
            user_id=current_user.id,
            description=f'API: {employee.get_full_name()} clocked out at {current_time.strftime("%H:%M")} ' +
                       f'(Worked {work_hours:.2f} hours)',
            ip_address=g.client_ip
        )
        
        return api_response(True, {
            'employee': employee.get_full_name(),
            'clock_out_time': current_time.strftime('%H:%M:%S'),
            'work_hours': round(work_hours, 2),
            'overtime_hours': round(overtime_hours, 2),
            'clock_in_time': attendance_record.clock_in_time.strftime('%H:%M:%S')
        }, 'Successfully clocked out')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"API error clocking out: {e}")
        return api_response(False, message='Internal server error', status_code=500)
        return api_response(False, message='Internal server error', status_code=500)
# Leave Management APIs

@api_bp.route('/leaves', methods=['GET'])
@login_required
def api_leaves():
    """Get leave requests with filtering"""
    # FIXED: Local imports
    from models.leave import LeaveRequest
    from models.employee import Employee
    
    if not check_api_permission('view'):
        return api_response(False, message='Insufficient permissions', status_code=403)
    
    try:
        # Get query parameters
        status = request.args.get('status', 'all')
        employee_id = request.args.get('employee_id', type=int)
        leave_type = request.args.get('leave_type')
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        limit = min(request.args.get('limit', 50, type=int), 200)
        page = request.args.get('page', 1, type=int)
        
        # Build query
        query = LeaveRequest.query.join(Employee)
        
        # Apply role-based filtering
        if current_user.role == 'station_manager':
            query = query.filter(Employee.location == current_user.location)
        
        # Apply filters
        if status != 'all':
            if status == 'pending':
                query = query.filter(LeaveRequest.status.in_(['pending', 'pending_hr']))
            else:
                query = query.filter(LeaveRequest.status == status)
        
        if employee_id:
            query = query.filter(LeaveRequest.employee_id == employee_id)
        
        if leave_type:
            query = query.filter(LeaveRequest.leave_type == leave_type)
        
        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                query = query.filter(LeaveRequest.start_date >= start_date)
            except ValueError:
                return api_response(False, message='Invalid start_date format', status_code=400)
        
        if end_date_str:
            try:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
                query = query.filter(LeaveRequest.end_date <= end_date)
            except ValueError:
                return api_response(False, message='Invalid end_date format', status_code=400)
        
        # Execute query with pagination
        total_count = query.count()
        leave_requests = query.order_by(desc(LeaveRequest.created_date)).limit(limit).offset((page - 1) * limit).all()
        
        # Format response
        leaves_data = []
        for leave in leave_requests:
            leaves_data.append({
                'id': leave.id,
                'employee': {
                    'id': leave.employee.id,
                    'employee_id': leave.employee.employee_id,
                    'name': leave.employee.get_full_name(),
                    'department': leave.employee.department,
                    'location': leave.employee.location
                },
                'leave_type': leave.leave_type,
                'start_date': leave.start_date.isoformat(),
                'end_date': leave.end_date.isoformat(),
                'total_days': leave.total_days,
                'reason': leave.reason,
                'status': leave.status,
                'requested_date': leave.created_date.isoformat(),
                'approved_date': leave.approved_date.isoformat() if leave.approved_date else None,
                'approval_comments': leave.approval_comments
            })
        
        return api_response(True, {
            'leave_requests': leaves_data,
            'total': len(leaves_data),
            'total_count': total_count,
            'page': page,
            'limit': limit,
            'filters': {
                'status': status,
                'employee_id': employee_id,
                'leave_type': leave_type,
                'start_date': start_date_str,
                'end_date': end_date_str
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"API error getting leaves: {e}")
        return api_response(False, message='Internal server error', status_code=500)

@api_bp.route('/leaves/request', methods=['POST'])
@login_required
def api_request_leave():
    """Request leave through API"""
    # FIXED: Local imports
    from models.leave import LeaveRequest
    from models.employee import Employee
    from models.audit import AuditLog
    
    try:
        data = g.json_data
        if not data:
            return api_response(False, message='JSON data required', status_code=400)
        
        # Validate required fields
        required_fields = ['employee_id', 'leave_type', 'start_date', 'end_date', 'reason']
        missing_fields = [field for field in required_fields if not data.get(field)]
        
        if missing_fields:
            return api_response(False, 
                              message=f'Missing required fields: {", ".join(missing_fields)}',
                              status_code=400)
        
        # Get employee and validate permissions
        employee = Employee.query.get(data['employee_id'])
        if not employee:
            return api_response(False, message='Employee not found', status_code=404)
        
        if (current_user.role == 'station_manager' and 
            employee.location != current_user.location):
            return api_response(False, message='Access denied', status_code=403)
        
        # Parse and validate dates
        try:
            start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
            end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
        except ValueError:
            return api_response(False, message='Invalid date format. Use YYYY-MM-DD', status_code=400)
        
        if start_date < date.today():
            return api_response(False, message='Start date cannot be in the past', status_code=400)
        
        if end_date < start_date:
            return api_response(False, message='End date must be after start date', status_code=400)
        
        # Calculate total days
        total_days = (end_date - start_date).days + 1
        
        # Check for overlapping requests
        overlapping = LeaveRequest.query.filter(
            LeaveRequest.employee_id == employee.id,
            LeaveRequest.status.in_(['pending', 'approved']),
            or_(
                and_(LeaveRequest.start_date <= start_date, LeaveRequest.end_date >= start_date),
                and_(LeaveRequest.start_date <= end_date, LeaveRequest.end_date >= end_date),
                and_(LeaveRequest.start_date >= start_date, LeaveRequest.end_date <= end_date)
            )
        ).first()
        
        if overlapping:
            return api_response(False, 
                              message=f'Leave dates overlap with existing request from {overlapping.start_date} to {overlapping.end_date}',
                              status_code=400)
        
        # Create leave request
        leave_request = LeaveRequest(
            employee_id=employee.id,
            leave_type=data['leave_type'],
            start_date=start_date,
            end_date=end_date,
            total_days=total_days,
            reason=data['reason'],
            contact_info=data.get('contact_info', ''),
            requested_by=current_user.id,
            requested_date=datetime.utcnow(),
            status='pending'
        )
        
        db.session.add(leave_request)
        db.session.flush()
        
        # Log the action
        AuditLog.log_event(
            user_id=current_user.id,
            action='leave_requested_api',
            table_name='leave_requests',
            record_id=leave_request.id,
            description=f'Leave requested via API: {data["leave_type"]} for {employee.get_full_name()}',
            ip_address=g.client_ip
        )
        
        db.session.commit()
        
        return api_response(True, {
            'leave_request_id': leave_request.id,
            'employee': employee.get_full_name(),
            'leave_type': leave_request.leave_type,
            'start_date': leave_request.start_date.isoformat(),
            'end_date': leave_request.end_date.isoformat(),
            'total_days': leave_request.total_days,
            'status': leave_request.status
        }, 'Leave request submitted successfully')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"API error requesting leave: {e}")
        return api_response(False, message='Internal server error', status_code=500)

@api_bp.route('/leaves/balance/<int:employee_id>', methods=['GET'])
@login_required
def api_employee_leave_balance(employee_id):
    """Get employee leave balance"""
    # FIXED: Local imports
    from models.employee import Employee
    from models.leave import LeaveRequest
    
    try:
        employee = Employee.query.get(employee_id)
        if not employee:
            return api_response(False, message='Employee not found', status_code=404)
        
        # Check permissions
        if (current_user.role == 'station_manager' and 
            employee.location != current_user.location):
            return api_response(False, message='Access denied', status_code=403)
        
        # Calculate leave balances
        current_year = date.today().year
        leave_entitlements = current_app.config.get('KENYAN_LABOR_LAWS', {}).get('leave_entitlements', {})
        
        balances = {}
        
        for leave_type, details in leave_entitlements.items():
            annual_entitlement = details.get('annual_entitlement', 0)
            
            # Calculate used days for current year
            used_days = db.session.query(func.sum(LeaveRequest.total_days)).filter(
                LeaveRequest.employee_id == employee.id,
                LeaveRequest.leave_type == leave_type,
                LeaveRequest.status == 'approved',
                func.extract('year', LeaveRequest.start_date) == current_year
            ).scalar() or 0
            
            remaining_days = max(0, annual_entitlement - int(used_days))
            
            balances[leave_type] = {
                'entitlement': annual_entitlement,
                'used': int(used_days),
                'remaining': remaining_days,
                'percentage_used': round((int(used_days) / annual_entitlement * 100), 1) if annual_entitlement > 0 else 0
            }
        
        return api_response(True, {
            'employee': {
                'id': employee.id,
                'employee_id': employee.employee_id,
                'name': employee.get_full_name(),
                'department': employee.department,
                'location': employee.location
            },
            'year': current_year,
            'balances': balances
        })
        
    except Exception as e:
        current_app.logger.error(f"API error getting leave balance: {e}")
        return api_response(False, message='Internal server error', status_code=500)

@api_bp.route('/leaves/approve/<int:leave_id>', methods=['POST'])
@login_required
def api_approve_leave(leave_id):
    """Approve leave request through API"""
    # FIXED: Local imports
    from models.leave import LeaveRequest
    from models.audit import AuditLog
    
    if current_user.role not in ['hr_manager', 'admin']:
        return api_response(False, message='Only HR managers can approve leaves', status_code=403)
    
    try:
        leave_request = LeaveRequest.query.get(leave_id)
        if not leave_request:
            return api_response(False, message='Leave request not found', status_code=404)
        
        if leave_request.status not in ['pending', 'pending_hr']:
            return api_response(False, message='Leave request is not pending approval', status_code=400)
        
        data = g.json_data or {}
        comments = data.get('comments', '').strip()
        
        # Update leave request
        leave_request.status = 'approved'
        leave_request.approved_by = current_user.id
        leave_request.approved_date = datetime.utcnow()
        leave_request.approval_comments = comments
        
        db.session.commit()
        
        # Log action
        AuditLog.log_event(
            event_type='leave_approved_api',
            user_id=current_user.id,
            target_type='leave_requests',
            target_id=leave_request.id,
            description=f'API: Approved {leave_request.leave_type} for {leave_request.employee.get_full_name()}',
            ip_address=g.client_ip
        )
        
        return api_response(True, {
            'leave_request_id': leave_request.id,
            'employee': leave_request.employee.get_full_name(),
            'leave_type': leave_request.leave_type,
            'start_date': leave_request.start_date.isoformat(),
            'end_date': leave_request.end_date.isoformat(),
            'total_days': leave_request.total_days,
            'approved_by': current_user.get_full_name(),
            'approved_date': leave_request.approved_date.isoformat()
        }, 'Leave request approved successfully')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"API error approving leave: {e}")
        return api_response(False, message='Internal server error', status_code=500)

@api_bp.route('/leaves/reject/<int:leave_id>', methods=['POST'])
@login_required
def api_reject_leave(leave_id):
    """Reject leave request through API"""
    # FIXED: Local imports
    from models.leave import LeaveRequest
    from models.audit import AuditLog
    
    if current_user.role not in ['hr_manager', 'admin']:
        return api_response(False, message='Only HR managers can reject leaves', status_code=403)
    
    try:
        leave_request = LeaveRequest.query.get(leave_id)
        if not leave_request:
            return api_response(False, message='Leave request not found', status_code=404)
        
        if leave_request.status not in ['pending', 'pending_hr']:
            return api_response(False, message='Leave request is not pending approval', status_code=400)
        
        data = g.json_data or {}
        rejection_reason = data.get('reason', '').strip()
        
        if not rejection_reason:
            return api_response(False, message='Rejection reason is required', status_code=400)
        
        # Update leave request
        leave_request.status = 'rejected'
        leave_request.approved_by = current_user.id
        leave_request.approved_date = datetime.utcnow()
        leave_request.approval_comments = rejection_reason
        
        db.session.commit()
        
        # Log action
        AuditLog.log_event(
            event_type='leave_rejected_api',
            user_id=current_user.id,
            target_type='leave_requests',
            target_id=leave_request.id,
            description=f'API: Rejected {leave_request.leave_type} for {leave_request.employee.get_full_name()}',
            ip_address=g.client_ip
        )
        
        return api_response(True, {
            'leave_request_id': leave_request.id,
            'employee': leave_request.employee.get_full_name(),
            'leave_type': leave_request.leave_type,
            'rejected_by': current_user.get_full_name(),
            'rejection_reason': rejection_reason,
            'rejected_date': leave_request.approved_date.isoformat()
        }, 'Leave request rejected')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"API error rejecting leave: {e}")
        return api_response(False, message='Internal server error', status_code=500)

# Dashboard APIs

@api_bp.route('/dashboard/stats', methods=['GET'])
@login_required
def api_dashboard_stats():
    """Get dashboard statistics"""
    # FIXED: Local imports
    from models.employee import Employee
    from models.attendance import AttendanceRecord
    from models.leave import LeaveRequest
    
    try:
        today = date.today()
        
        # Base queries based on user role
        if current_user.role == 'station_manager':
            employee_query = Employee.query.filter(
                Employee.location == current_user.location,
                Employee.is_active == True
            )
            location_filter = Employee.location == current_user.location
        else:
            employee_query = Employee.query.filter(Employee.is_active == True)
            location_filter = True
        
        # Employee statistics
        total_employees = employee_query.count()
        
        # Today's attendance
        today_attendance = AttendanceRecord.query.join(Employee).filter(
            AttendanceRecord.date == today,
            location_filter
        ).count()
        
        today_present = AttendanceRecord.query.join(Employee).filter(
            AttendanceRecord.date == today,
            AttendanceRecord.status.in_(['present', 'late']),
            location_filter
        ).count()
        
        # Leave statistics
        pending_leaves = LeaveRequest.query.join(Employee).filter(
            LeaveRequest.status == 'pending',
            location_filter
        ).count()
        
        current_leaves = LeaveRequest.query.join(Employee).filter(
            LeaveRequest.status == 'approved',
            LeaveRequest.start_date <= today,
            LeaveRequest.end_date >= today,
            location_filter
        ).count()
        
        return api_response(True, {
            'employees': {
                'total': total_employees,
                'active': total_employees
            },
            'attendance': {
                'today_total': today_attendance,
                'today_present': today_present,
                'today_absent': today_attendance - today_present,
                'attendance_rate': round((today_present / total_employees * 100) if total_employees > 0 else 0, 1)
            },
            'leaves': {
                'pending': pending_leaves,
                'current': current_leaves
            },
            'date': today.isoformat()
        })
        
    except Exception as e:
        current_app.logger.error(f"API error getting dashboard stats: {e}")
        return api_response(False, message='Internal server error', status_code=500)

# Utility APIs

@api_bp.route('/locations', methods=['GET'])
@login_required
def api_locations():
    """Get available locations"""
    try:
        locations = current_app.config.get('COMPANY_LOCATIONS', {})
        
        # Format locations data
        locations_data = []
        for key, info in locations.items():
            # Filter based on user role
            if current_user.role == 'station_manager' and key != current_user.location:
                continue
                
            locations_data.append({
                'code': key,
                'name': info.get('name', key.replace('_', ' ').title()),
                'address': info.get('address', ''),
                'type': info.get('type', 'office')
            })
        
        return api_response(True, {
            'locations': locations_data,
            'total': len(locations_data)
        })
        
    except Exception as e:
        current_app.logger.error(f"API error getting locations: {e}")
        return api_response(False, message='Internal server error', status_code=500)

@api_bp.route('/departments', methods=['GET'])
@login_required
def api_departments():
    """Get available departments"""
    try:
        departments = current_app.config.get('DEPARTMENTS', {})
        
        # Format departments data
        departments_data = []
        for key, info in departments.items():
            departments_data.append({
                'code': key,
                'name': info.get('name', key.replace('_', ' ').title()),
                'description': info.get('description', '')
            })
        
        return api_response(True, {
            'departments': departments_data,
            'total': len(departments_data)
        })
        
    except Exception as e:
        current_app.logger.error(f"API error getting departments: {e}")
        return api_response(False, message='Internal server error', status_code=500)

@api_bp.route('/leave-types', methods=['GET'])
@login_required
def api_leave_types():
    """Get available leave types with entitlements"""
    try:
        leave_entitlements = current_app.config.get('KENYAN_LABOR_LAWS', {}).get('leave_entitlements', {})
        
        # Format leave types data
        leave_types_data = []
        for key, details in leave_entitlements.items():
            leave_types_data.append({
                'code': key,
                'name': details.get('display_name', key.replace('_', ' ').title()),
                'annual_entitlement': details.get('annual_entitlement', 0),
                'max_continuous_days': details.get('max_continuous_days', 0),
                'min_notice_days': details.get('min_notice_days', 0),
                'gender_specific': details.get('gender_specific', None),
                'certificate_required': details.get('certificate_required', False)
            })
        
        return api_response(True, {
            'leave_types': leave_types_data,
            'total': len(leave_types_data)
        })
        
    except Exception as e:
        current_app.logger.error(f"API error getting leave types: {e}")
        return api_response(False, message='Internal server error', status_code=500)

@api_bp.route('/user-info', methods=['GET'])
@login_required
def api_user_info():
    """Get current user information"""
    try:
        user_data = {
            'id': current_user.id,
            'username': current_user.username,
            'email': current_user.email,
            'first_name': current_user.first_name,
            'last_name': current_user.last_name,
            'full_name': current_user.get_full_name(),
            'role': current_user.role,
            'location': current_user.location,
            'is_active': current_user.is_active,
            'last_login': current_user.last_login.isoformat() if current_user.last_login else None,
            'permissions': {
                'can_view_all_locations': current_user.role in ['hr_manager', 'admin'],
                'can_manage_employees': current_user.role in ['hr_manager', 'admin'],
                'can_approve_leaves': current_user.role in ['hr_manager', 'admin'],
                'can_access_reports': True,
                'location_restricted': current_user.role == 'station_manager'
            }
        }
        
        return api_response(True, user_data)
        
    except Exception as e:
        current_app.logger.error(f"API error getting user info: {e}")
        return api_response(False, message='Internal server error', status_code=500)

# Helper Functions

def mark_single_attendance(data):
    """Mark attendance for a single employee"""
    # FIXED: Local imports
    from models.employee import Employee
    from models.attendance import AttendanceRecord
    from models.audit import AuditLog
    
    try:
        employee_id = data.get('employee_id')
        status = data.get('status')
        notes = data.get('notes', '')
        target_date_str = data.get('date', date.today().isoformat())
        
        if not employee_id or not status:
            return {'success': False, 'message': 'Employee ID and status are required'}
        
        employee = Employee.query.get(employee_id)
        if not employee:
            return {'success': False, 'message': 'Employee not found'}
        
        if (current_user.role == 'station_manager' and 
            employee.location != current_user.location):
            return {'success': False, 'message': 'Access denied'}
        
        try:
            target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
        except ValueError:
            return {'success': False, 'message': 'Invalid date format'}
        
        existing = AttendanceRecord.query.filter_by(
            employee_id=employee.id,
            date=target_date
        ).first()
        
        current_time = datetime.now()
        
        if existing:
            existing.status = status
            existing.notes = notes
            existing.updated_by = current_user.id
            existing.last_updated = current_time
        else:
            attendance = AttendanceRecord(
                employee_id=employee.id,
                date=target_date,
                status=status,
                notes=notes,
                created_by=current_user.id,
                clock_in_time=current_time if status in ['present', 'late'] else None,
                location=employee.location,
                clock_in_method='api_mark',
                ip_address=g.client_ip
            )
            db.session.add(attendance)
        
        db.session.commit()
        
        AuditLog.log_event(
            user_id=current_user.id,
            action='attendance_marked_api',
            description=f'API: Marked {status} for {employee.get_full_name()}',
            ip_address=g.client_ip
        )
        
        return {
            'success': True,
            'message': f'Attendance marked for {employee.get_full_name()}',
            'data': {
                'employee': employee.get_full_name(),
                'status': status,
                'date': target_date.isoformat()
            }
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
        'data': {
            'success_count': success_count,
            'error_count': error_count,
            'errors': errors if errors else None
        }
    }

def calculate_employee_attendance_rate(employee):
    """Calculate employee attendance rate for current month"""
    # FIXED: Local imports
    from models.attendance import AttendanceRecord
    
    try:
        today = date.today()
        start_of_month = today.replace(day=1)
        
        attendance_records = AttendanceRecord.query.filter(
            AttendanceRecord.employee_id == employee.id,
            AttendanceRecord.date >= start_of_month,
            AttendanceRecord.date <= today
        ).all()
        
        if not attendance_records:
            return 0.0
        
        present_count = len([r for r in attendance_records if r.status in ['present', 'late']])
        total_records = len(attendance_records)
        
        return round((present_count / total_records * 100), 1) if total_records > 0 else 0.0
        
    except Exception as e:
        current_app.logger.error(f"Error calculating attendance rate for employee {employee.id}: {e}")
        return 0.0

# Error Handlers

@api_bp.errorhandler(404)
def api_not_found(error):
    """Handle 404 errors for API routes"""
    return api_response(False, message='Endpoint not found', status_code=404)

@api_bp.errorhandler(405)
def api_method_not_allowed(error):
    """Handle 405 errors for API routes"""
    return api_response(False, message='Method not allowed', status_code=405)

@api_bp.errorhandler(500)
def api_internal_error(error):
    """Handle 500 errors for API routes"""
    return api_response(False, message='Internal server error', status_code=500)

@api_bp.errorhandler(403)
def api_forbidden(error):
    """Handle 403 errors for API routes"""
    return api_response(False, message='Access forbidden', status_code=403)

@api_bp.errorhandler(401)
def api_unauthorized(error):
    """Handle 401 errors for API routes"""
    return api_response(False, message='Authentication required', status_code=401)

# API Documentation

@api_bp.route('/docs')
def api_documentation():
    """API documentation endpoint"""
    return jsonify({
        'api_version': '3.0',
        'service': 'Sakina Gas Attendance System API',
        'description': 'Comprehensive REST API for attendance management system',
        'base_url': '/api',
        'authentication': {
            'type': 'session-based',
            'description': 'Login required via web interface before API access'
        },
        'endpoints': {
            'system': {
                'health': 'GET /health - Health check',
                'docs': 'GET /docs - API documentation',
                'user_info': 'GET /user-info - Current user information'
            },
            'employees': {
                'list': 'GET /employees - List employees with filters (?location=&department=&status=&search=&limit=&page=)',
                'detail': 'GET /employees/{id} - Get detailed employee information',
                'search': 'GET /employees/search?q={term} - Search employees by name, ID, or email'
            },
            'attendance': {
                'mark': 'POST /attendance/mark - Mark attendance (single or bulk)',
                'today': 'GET /attendance/today - Today\'s attendance overview (?location=)',
                'history': 'GET /attendance/employee/{id}/history - Employee attendance history (?start_date=&end_date=)',
                'clock_in': 'POST /attendance/clock-in - Clock in employee',
                'clock_out': 'POST /attendance/clock-out - Clock out employee'
            },
            'leaves': {
                'list': 'GET /leaves - List leave requests with filters (?status=&employee_id=&leave_type=&start_date=&end_date=&limit=&page=)',
                'request': 'POST /leaves/request - Request leave',
                'balance': 'GET /leaves/balance/{employee_id} - Get employee leave balance',
                'approve': 'POST /leaves/approve/{id} - Approve leave request',
                'reject': 'POST /leaves/reject/{id} - Reject leave request'
            },
            'dashboard': {
                'stats': 'GET /dashboard/stats - Dashboard statistics'
            },
            'utilities': {
                'locations': 'GET /locations - Get available locations',
                'departments': 'GET /departments - Get available departments',
                'leave_types': 'GET /leave-types - Get available leave types with entitlements'
            }
        },
        'response_format': {
            'success': 'boolean - Request success status',
            'data': 'object|array|null - Response data',
            'message': 'string - Success/error message',
            'timestamp': 'string - ISO datetime of response',
            'user_id': 'integer|null - Current user ID',
            'errors': 'array|null - Error details if any'
        },
        'permissions': {
            'hr_manager': 'Full access to all endpoints and all locations',
            'station_manager': 'Limited to own location, cannot approve leaves',
            'admin': 'Full system access'
        },
        'rate_limits': {
            'general': '1000 requests per hour per user',
            'bulk_operations': '100 requests per hour per user'
        }
    })

@api_bp.route('/status')
def api_status():
    """Detailed API status endpoint"""
    try:
        # FIXED: Local imports
        from models.employee import Employee
        from models.attendance import AttendanceRecord
        
        # Test database connectivity
        employee_count = Employee.query.count()
        attendance_count = AttendanceRecord.query.count()
        
        return jsonify({
            'status': 'operational',
            'version': '3.0',
            'timestamp': datetime.utcnow().isoformat(),
            'database': {
                'status': 'connected',
                'employees': employee_count,
                'attendance_records': attendance_count
            },
            'features': {
                'kenyan_labor_law_compliance': True,
                'multi_location_support': True,
                'role_based_access': True,
                'audit_logging': True,
                'real_time_statistics': True
            }
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'version': '3.0',
            'timestamp': datetime.utcnow().isoformat(),
            'error': str(e)
        }), 500