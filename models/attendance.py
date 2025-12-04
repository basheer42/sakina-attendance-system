"""
Sakina Gas Company - Attendance Model
Built from scratch with comprehensive attendance tracking and analytics
Version 3.0 - Enterprise grade with full complexity
"""

from database import db
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON, Date, Time, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, date, time, timedelta
from decimal import Decimal
import json

class AttendanceRecord(db.Model):
    """
    Comprehensive Attendance model with advanced tracking and analytics
    """
    __tablename__ = 'attendance_records'
    
    # Primary identification
    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey('employees.id'), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    
    # Time tracking
    clock_in_time = Column(DateTime, nullable=True)
    clock_out_time = Column(DateTime, nullable=True)
    scheduled_in_time = Column(Time, nullable=True)  # Expected clock-in time
    scheduled_out_time = Column(Time, nullable=True)  # Expected clock-out time
    
    # Break times
    break_start_time = Column(DateTime, nullable=True)
    break_end_time = Column(DateTime, nullable=True)
    total_break_minutes = Column(Integer, nullable=False, default=0)
    
    # Status and calculations
    status = Column(String(30), nullable=False, index=True)  # present, late, absent, on_leave, etc.
    work_hours = Column(Numeric(5, 2), nullable=False, default=0.00)  # Total hours worked
    regular_hours = Column(Numeric(5, 2), nullable=False, default=0.00)  # Regular work hours
    overtime_hours = Column(Numeric(5, 2), nullable=False, default=0.00)  # Overtime hours
    
    # Late and early departure tracking
    minutes_late = Column(Integer, nullable=False, default=0)
    minutes_early_departure = Column(Integer, nullable=False, default=0)
    
    # Location and method tracking
    location = Column(String(50), nullable=True, index=True)
    clock_in_method = Column(String(20), nullable=False, default='manual')  # manual, biometric, mobile, web
    clock_out_method = Column(String(20), nullable=True)
    
    # GPS and verification
    clock_in_location = Column(JSON, nullable=True)  # GPS coordinates, address
    clock_out_location = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)  # IPv4 or IPv6
    user_agent = Column(Text, nullable=True)
    
    # Approval and verification
    is_verified = Column(Boolean, nullable=False, default=False)
    verified_by = Column(Integer, nullable=True)  # User ID who verified
    verified_date = Column(DateTime, nullable=True)
    
    # Manager override
    is_manual_entry = Column(Boolean, nullable=False, default=False)
    manual_entry_reason = Column(Text, nullable=True)
    entered_by = Column(Integer, nullable=True)  # User ID who made manual entry
    
    # Shift information
    shift_type = Column(String(20), nullable=False, default='day')  # day, night, custom
    shift_pattern = Column(String(50), nullable=True)  # 9-to-5, 24hr, rotating, etc.
    
    # Additional tracking
    productivity_score = Column(Numeric(5, 2), nullable=True)  # Performance metric
    tasks_completed = Column(Integer, nullable=True)
    meetings_attended = Column(Integer, nullable=True)
    
    # Notes and comments
    notes = Column(Text, nullable=True)  # Employee notes
    manager_notes = Column(Text, nullable=True)  # Manager/HR notes
    system_notes = Column(Text, nullable=True)  # Automated system notes
    
    # Absence details (if applicable)
    absence_type = Column(String(30), nullable=True)  # sick, personal, vacation, etc.
    absence_reason = Column(Text, nullable=True)
    doctor_note_required = Column(Boolean, nullable=False, default=False)
    doctor_note_provided = Column(Boolean, nullable=False, default=False)
    
    # Leave integration
    leave_request_id = Column(Integer, ForeignKey('leave_requests.id'), nullable=True)
    
    # Weather and external factors
    weather_conditions = Column(String(50), nullable=True)
    transport_issues = Column(Boolean, nullable=False, default=False)
    
    # System metadata
    created_date = Column(DateTime, nullable=False, default=func.current_timestamp())
    created_by = Column(Integer, nullable=True)  # User ID who created record
    last_updated = Column(DateTime, nullable=False, default=func.current_timestamp(), onupdate=func.current_timestamp())
    updated_by = Column(Integer, nullable=True)  # User ID who last updated
    
    # Flexible metadata storage
    attendance_metadata = Column(JSON, nullable=True) # FIX: Renamed from 'metadata'
    
    # Device and technology tracking
    device_info = Column(JSON, nullable=True)  # Device used for clock-in/out
    app_version = Column(String(20), nullable=True)  # Mobile app version
    
    # Compliance and audit
    is_compliant = Column(Boolean, nullable=False, default=True)
    compliance_notes = Column(Text, nullable=True)
    audit_trail = Column(JSON, nullable=True)  # Changes history
    
    # Performance indicators
    efficiency_rating = Column(String(20), nullable=True)  # excellent, good, average, poor
    punctuality_score = Column(Numeric(5, 2), nullable=True)  # 0-100 score
    
    # Relationships
    # FIX: Use string literal for relationship to break circular dependency
    leave_request = relationship('LeaveRequest', backref='attendance_records')
    employee = relationship('Employee', backref='employee_attendance_records') 
    
    # Indexes
    __table_args__ = (
        db.Index('idx_employee_date', 'employee_id', 'date'),
        db.Index('idx_date_status', 'date', 'status'),
        db.Index('idx_location_date', 'location', 'date'),
    )
    
    def __init__(self, **kwargs):
        """Initialize attendance record with default values"""
        super(AttendanceRecord, self).__init__()
        
        # Set default metadata
        self.attendance_metadata = {} # FIX: Renamed from self.metadata
        self.audit_trail = []
        self.device_info = {}
        
        # Set creation timestamp
        self.created_date = datetime.utcnow()
        
        # Apply any provided kwargs
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def clock_in(self, clock_in_time=None, location=None, method='manual', 
                ip_address=None, user_agent=None, gps_location=None):
        """Record clock-in time and calculate status"""
        # Use current time if not provided
        if clock_in_time is None:
            clock_in_time = datetime.now()
        
        self.clock_in_time = clock_in_time
        self.clock_in_method = method
        self.location = location
        self.ip_address = ip_address
        self.user_agent = user_agent
        
        if gps_location:
            self.clock_in_location = gps_location
        
        # Calculate status based on scheduled time
        self._calculate_clock_in_status()
        
        # Add to audit trail
        self._add_to_audit_trail('clock_in', {
            'time': clock_in_time.isoformat(),
            'method': method,
            'location': location
        })
    
    def clock_out(self, clock_out_time=None, method='manual', gps_location=None):
        """Record clock-out time and calculate work hours"""
        # Use current time if not provided
        if clock_out_time is None:
            clock_out_time = datetime.now()
        
        self.clock_out_time = clock_out_time
        self.clock_out_method = method
        
        if gps_location:
            self.clock_out_location = gps_location
        
        # Calculate work hours and overtime
        self._calculate_work_hours()
        
        # Calculate early departure
        self._calculate_early_departure()
        
        # Add to audit trail
        self._add_to_audit_trail('clock_out', {
            'time': clock_out_time.isoformat(),
            'method': method,
            'work_hours': float(self.work_hours) if self.work_hours else 0,
            'overtime_hours': float(self.overtime_hours) if self.overtime_hours else 0
        })
    
    def start_break(self, break_time=None):
        """Record break start time"""
        if break_time is None:
            break_time = datetime.now()
        
        self.break_start_time = break_time
        
        self._add_to_audit_trail('break_start', {
            'time': break_time.isoformat()
        })
    
    def end_break(self, break_time=None):
        """Record break end time and calculate break duration"""
        if break_time is None:
            break_time = datetime.now()
        
        self.break_end_time = break_time
        
        # Calculate break duration
        if self.break_start_time:
            break_duration = break_time - self.break_start_time
            self.total_break_minutes += int(break_duration.total_seconds() / 60)
        
        # Recalculate work hours if clock-out is already recorded
        if self.clock_out_time:
            self._calculate_work_hours()
        
        self._add_to_audit_trail('break_end', {
            'time': break_time.isoformat(),
            'duration_minutes': self.total_break_minutes
        })
    
    def _calculate_clock_in_status(self):
        """Calculate attendance status based on clock-in time"""
        from flask import current_app # Local import
        
        # Check if scheduled time is available
        if not self.clock_in_time or not self.scheduled_in_time:
            self.status = 'present'
            return
        
        # Convert scheduled time to datetime for comparison
        scheduled_datetime = datetime.combine(self.date, self.scheduled_in_time)
        
        # Calculate how late the employee is
        if self.clock_in_time > scheduled_datetime:
            late_delta = self.clock_in_time - scheduled_datetime
            self.minutes_late = int(late_delta.total_seconds() / 60)
            
            # Determine if it's considered "late" based on company policy
            late_threshold = current_app.config.get('VALIDATION_RULES', {}).get(
                'attendance_rules', {}).get('late_threshold_minutes', 15)
            
            if self.minutes_late > late_threshold:
                self.status = 'late'
            else:
                self.status = 'present'
        else:
            self.status = 'present'
            self.minutes_late = 0
    
    def _calculate_work_hours(self):
        """Calculate total work hours and overtime"""
        from flask import current_app # Local import
        
        if not self.clock_in_time or not self.clock_out_time:
            self.work_hours = Decimal('0.00')
            self.regular_hours = Decimal('0.00')
            self.overtime_hours = Decimal('0.00')
            return
        
        # Calculate total time
        total_time = self.clock_out_time - self.clock_in_time
        total_minutes = int(total_time.total_seconds() / 60)
        
        # Subtract break time
        work_minutes = total_minutes - self.total_break_minutes
        work_hours = work_minutes / 60
        
        # Get standard work hours from config
        standard_hours = current_app.config.get('KENYAN_LABOR_LAWS', {}).get(
            'working_hours', {}).get('normal_hours_per_day', 8)
        
        # Calculate regular and overtime hours
        if work_hours <= standard_hours:
            self.regular_hours = Decimal(str(round(work_hours, 2)))
            self.overtime_hours = Decimal('0.00')
        else:
            self.regular_hours = Decimal(str(standard_hours))
            self.overtime_hours = Decimal(str(round(work_hours - standard_hours, 2)))
        
        self.work_hours = Decimal(str(round(work_hours, 2)))
    
    def _calculate_early_departure(self):
        """Calculate early departure minutes"""
        if not self.clock_out_time or not self.scheduled_out_time:
            return
        
        # Convert scheduled out time to datetime
        scheduled_out_datetime = datetime.combine(self.date, self.scheduled_out_time)
        
        # If leaving before scheduled time
        if self.clock_out_time < scheduled_out_datetime:
            early_delta = scheduled_out_datetime - self.clock_out_time
            self.minutes_early_departure = int(early_delta.total_seconds() / 60)
        else:
            self.minutes_early_departure = 0
    
    def _add_to_audit_trail(self, action, data):
        """Add entry to audit trail"""
        if self.audit_trail is None:
            self.audit_trail = []
        
        entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'action': action,
            'data': data
        }
        
        self.audit_trail.append(entry)
    
    def mark_absent(self, reason=None, absence_type='unexcused'):
        """Mark employee as absent"""
        self.status = 'absent'
        self.absence_type = absence_type
        self.absence_reason = reason
        self.work_hours = Decimal('0.00')
        self.regular_hours = Decimal('0.00')
        self.overtime_hours = Decimal('0.00')
        
        self._add_to_audit_trail('marked_absent', {
            'reason': reason,
            'type': absence_type
        })
    
    def mark_on_leave(self, leave_type, leave_request_id=None):
        """Mark employee as on leave"""
        leave_status_map = {
            'annual_leave': 'annual_leave',
            'sick_leave': 'sick_leave',
            'maternity_leave': 'maternity_leave',
            'paternity_leave': 'paternity_leave',
            'compassionate_leave': 'compassionate_leave',
            'study_leave': 'study_leave'
        }
        
        self.status = leave_status_map.get(leave_type, 'on_leave')
        self.leave_request_id = leave_request_id
        self.work_hours = Decimal('0.00')
        self.regular_hours = Decimal('0.00')
        self.overtime_hours = Decimal('0.00')
        
        self._add_to_audit_trail('marked_on_leave', {
            'leave_type': leave_type,
            'leave_request_id': leave_request_id
        })
    
    def calculate_punctuality_score(self):
        """Calculate punctuality score (0-100)"""
        if self.status == 'absent':
            return 0.0
        
        if self.minutes_late == 0:
            return 100.0
        
        # Score decreases with lateness
        # 15 minutes late = 50 points, 30+ minutes = 0 points
        if self.minutes_late <= 15:
            score = 100 - (self.minutes_late * 3.33)  # 3.33 points per minute
        elif self.minutes_late <= 30:
            score = 50 - ((self.minutes_late - 15) * 3.33)
        else:
            score = 0
        
        return max(0.0, min(100.0, round(score, 2)))
    
    def calculate_efficiency_rating(self):
        """Calculate efficiency rating based on various factors"""
        score = 0
        
        # Base score from punctuality
        score += self.calculate_punctuality_score() * 0.4
        
        # Work hours completion (if overtime is positive, bonus points)
        if self.regular_hours is not None and float(self.regular_hours) >= 8:
            score += 30
        elif self.regular_hours is not None and float(self.regular_hours) >= 6:
            score += 20
        elif self.regular_hours is not None and float(self.regular_hours) >= 4:
            score += 10
        
        # Overtime bonus (but cap it)
        if self.overtime_hours is not None and float(self.overtime_hours) > 0:
            overtime_bonus = min(float(self.overtime_hours) * 5, 20)
            score += overtime_bonus
        
        # Break time penalty (if excessive breaks)
        if self.total_break_minutes > 90:  # More than 1.5 hours
            score -= 10
        
        # Determine rating
        if score >= 90:
            return 'excellent'
        elif score >= 75:
            return 'good'
        elif score >= 60:
            return 'average'
        else:
            return 'poor'
    
    def get_formatted_work_hours(self):
        """Get formatted work hours as HH:MM"""
        if self.work_hours is None or self.work_hours == 0:
            return "00:00"
        
        hours = int(self.work_hours)
        minutes = int((self.work_hours - hours) * 60)
        return f"{hours:02d}:{minutes:02d}"
    
    def get_status_display(self):
        """Get human-readable status"""
        status_map = {
            'present': 'Present',
            'late': 'Late',
            'absent': 'Absent',
            'annual_leave': 'Annual Leave',
            'sick_leave': 'Sick Leave',
            'maternity_leave': 'Maternity Leave',
            'paternity_leave': 'Paternity Leave',
            'compassionate_leave': 'Compassionate Leave',
            'study_leave': 'Study Leave',
            'on_leave': 'On Leave'
        }
        return status_map.get(self.status, self.status.replace('_', ' ').title())
    
    def get_clock_in_display(self):
        """Get formatted clock-in time"""
        if self.clock_in_time:
            return self.clock_in_time.strftime('%H:%M')
        return '-'
    
    def get_clock_out_display(self):
        """Get formatted clock-out time"""
        if self.clock_out_time:
            return self.clock_out_time.strftime('%H:%M')
        return '-'
    
    def is_overtime_applicable(self):
        """Check if overtime rules apply"""
        return self.overtime_hours is not None and self.overtime_hours > 0 and self.status in ['present', 'late']
    
    def get_overtime_rate(self):
        """Get overtime rate multiplier"""
        from config import get_overtime_rate # Local import
        from models.holiday import Holiday # Local import
        
        # Check if it's a holiday
        is_holiday = Holiday.is_holiday(self.date)
        
        # Check if it's night shift
        is_night_shift = self.shift_type == 'night'
        
        # FIX: Ensure work_hours is treated as a float/Decimal for the function call
        return get_overtime_rate(float(self.work_hours) if self.work_hours else 0, is_holiday, is_night_shift)
    
    def verify_attendance(self, verified_by_user_id, notes=None):
        """Verify attendance record"""
        self.is_verified = True
        self.verified_by = verified_by_user_id
        self.verified_date = datetime.utcnow()
        
        if notes:
            if not self.manager_notes:
                self.manager_notes = ""
            self.manager_notes += f"\n\nVerified: {notes}"
        
        self._add_to_audit_trail('verified', {
            'verified_by': verified_by_user_id,
            'notes': notes
        })
    
    def add_manual_entry(self, entered_by_user_id, reason, clock_in=None, 
                        clock_out=None, work_hours=None):
        """Add manual attendance entry"""
        self.is_manual_entry = True
        self.entered_by = entered_by_user_id
        self.manual_entry_reason = reason
        
        if clock_in:
            self.clock_in_time = clock_in
            self.clock_in_method = 'manual'
        
        if clock_out:
            self.clock_out_time = clock_out
            self.clock_out_method = 'manual'
        
        if work_hours is not None:
            self.work_hours = Decimal(str(work_hours))
        elif self.clock_in_time and self.clock_out_time:
            self._calculate_work_hours()
        
        # Update status
        if self.clock_in_time:
            self._calculate_clock_in_status()
        
        self._add_to_audit_trail('manual_entry', {
            'entered_by': entered_by_user_id,
            'reason': reason,
            'clock_in': clock_in.isoformat() if clock_in else None,
            'clock_out': clock_out.isoformat() if clock_out else None
        })
    
    def to_dict(self, include_sensitive=False):
        """Convert attendance record to dictionary"""
        data = {
            'id': self.id,
            'employee_id': self.employee_id,
            'date': self.date.isoformat(),
            'status': self.status,
            'status_display': self.get_status_display(),
            'clock_in_time': self.clock_in_time.isoformat() if self.clock_in_time else None,
            'clock_out_time': self.clock_out_time.isoformat() if self.clock_out_time else None,
            'clock_in_display': self.get_clock_in_display(),
            'clock_out_display': self.get_clock_out_display(),
            'work_hours': float(self.work_hours) if self.work_hours else 0,
            'work_hours_display': self.get_formatted_work_hours(),
            'overtime_hours': float(self.overtime_hours) if self.overtime_hours else 0,
            'minutes_late': self.minutes_late,
            'is_verified': self.is_verified,
            'is_manual_entry': self.is_manual_entry,
            'location': self.location
        }
        
        if include_sensitive:
            data.update({
                'regular_hours': float(self.regular_hours) if self.regular_hours else 0,
                'total_break_minutes': self.total_break_minutes,
                'minutes_early_departure': self.minutes_early_departure,
                'punctuality_score': self.calculate_punctuality_score(),
                'efficiency_rating': self.calculate_efficiency_rating(),
                'overtime_rate': self.get_overtime_rate() if self.is_overtime_applicable() else 1.0,
                'notes': self.notes,
                'manager_notes': self.manager_notes,
                'ip_address': self.ip_address,
                'audit_trail': self.audit_trail
            })
        
        return data
    
    @classmethod
    def get_attendance_for_date(cls, target_date, location=None, department=None):
        """Get attendance records for a specific date"""
        from models.employee import Employee # Local import
        
        query = cls.query.join(Employee).filter(cls.date == target_date)
        
        if location:
            query = query.filter(Employee.location == location)
        
        if department:
            query = query.filter(Employee.department == department)
        
        return query.all()
    
    @classmethod
    def get_employee_attendance_range(cls, employee_id, start_date, end_date):
        """Get attendance records for employee within date range"""
        return cls.query.filter(
            cls.employee_id == employee_id,
            cls.date.between(start_date, end_date)
        ).order_by(cls.date).all()
    
    @classmethod
    def get_attendance_summary(cls, start_date, end_date, location=None):
        """Get attendance summary for date range"""
        from models.employee import Employee # Local import
        
        query = db.session.query(
            cls.status,
            func.count(cls.id).label('count')
        ).join(Employee).filter(
            cls.date.between(start_date, end_date),
            Employee.is_active == True
        )
        
        if location:
            query = query.filter(Employee.location == location)
        
        query = query.group_by(cls.status)
        
        results = query.all()
        summary = {result.status: result.count for result in results}
        
        return summary
    
    @classmethod
    def create_attendance_record(cls, employee_id, date, **kwargs):
        """Create new attendance record"""
        # Check if record already exists
        existing = cls.query.filter_by(employee_id=employee_id, date=date).first()
        if existing:
            # FIX: Return existing instead of raising if update is possible/intended
            return existing 
        
        record = cls(employee_id=employee_id, date=date, **kwargs)
        return record
    
    def __repr__(self):
        # FIX: Ensure safe access to employee.get_full_name()
        employee_name = self.employee.get_full_name() if self.employee and hasattr(self.employee, 'get_full_name') else str(self.employee_id)
        return f'<AttendanceRecord {employee_name}: {self.date} - {self.status}>'