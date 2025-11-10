"""
Attendance management routes for Sakina Gas Attendance System
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from models import db, Employee, AttendanceRecord
from datetime import date, datetime

attendance_bp = Blueprint('attendance', __name__)

@attendance_bp.route('/mark', methods=['GET', 'POST'])
@login_required
def mark_attendance():
    """Mark attendance for employees"""
    if request.method == 'POST':
        employee_id = request.form['employee_id']
        status = request.form['status']
        notes = request.form.get('notes', '')
        
        employee = Employee.query.filter_by(employee_id=employee_id, is_active=True).first()
        if not employee:
            flash('Employee not found', 'error')
            return redirect(request.url)
        
        # Check if attendance already marked for today
        today = date.today()
        existing_record = AttendanceRecord.query.filter_by(
            employee_id=employee.id,
            date=today
        ).first()
        
        if existing_record:
            # Update existing record
            existing_record.status = status
            existing_record.notes = notes
            existing_record.marked_by = current_user.id
            existing_record.updated_at = datetime.utcnow()
        else:
            # Create new record
            attendance = AttendanceRecord(
                employee_id=employee.id,
                date=today,
                status=status,
                shift=employee.shift,
                notes=notes,
                marked_by=current_user.id
            )
            db.session.add(attendance)
        
        # Set clock in/out times if present
        if status == 'present':
            if existing_record:
                if not existing_record.clock_in:
                    existing_record.clock_in = datetime.utcnow()
            else:
                attendance.clock_in = datetime.utcnow()
        
        db.session.commit()
        flash(f'Attendance marked for {employee.full_name}', 'success')
        
    return render_template('attendance/mark.html')

@attendance_bp.route('/clock/<action>/<employee_id>')
@login_required
def clock_action(action, employee_id):
    """Handle clock in/out actions"""
    employee = Employee.query.filter_by(employee_id=employee_id, is_active=True).first()
    if not employee:
        return jsonify({'success': False, 'message': 'Employee not found'})
    
    today = date.today()
    attendance = AttendanceRecord.query.filter_by(
        employee_id=employee.id,
        date=today
    ).first()
    
    if not attendance:
        attendance = AttendanceRecord(
            employee_id=employee.id,
            date=today,
            shift=employee.shift,
            status='present',
            marked_by=current_user.id
        )
        db.session.add(attendance)
    
    now = datetime.utcnow()
    
    if action == 'in':
        if attendance.clock_in:
            return jsonify({'success': False, 'message': 'Already clocked in'})
        attendance.clock_in = now
        attendance.status = 'present'
        message = f'{employee.full_name} clocked in at {now.strftime("%H:%M")}'
    elif action == 'out':
        if not attendance.clock_in:
            return jsonify({'success': False, 'message': 'Must clock in first'})
        if attendance.clock_out:
            return jsonify({'success': False, 'message': 'Already clocked out'})
        attendance.clock_out = now
        message = f'{employee.full_name} clocked out at {now.strftime("%H:%M")}'
    else:
        return jsonify({'success': False, 'message': 'Invalid action'})
    
    attendance.updated_at = now
    db.session.commit()
    
    return jsonify({'success': True, 'message': message})
