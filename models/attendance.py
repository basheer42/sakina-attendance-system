"""
Attendance Model - Daily Attendance Tracking
This file contains only the AttendanceRecord model
"""

from database import db
from datetime import datetime, date, time

class AttendanceRecord(db.Model):
    """Attendance record model for daily tracking"""
    
    __tablename__ = 'attendance_records'
    
    # Primary fields
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False, index=True)
    date = db.Column(db.Date, nullable=False, index=True)
    
    # Attendance status
    status = db.Column(db.String(20), nullable=False)  # present, absent, late, half_day, on_leave
    
    # Time tracking
    clock_in = db.Column(db.DateTime, nullable=True)
    clock_out = db.Column(db.DateTime, nullable=True)
    break_start = db.Column(db.DateTime, nullable=True)
    break_end = db.Column(db.DateTime, nullable=True)
    
    # Shift information
    shift = db.Column(db.String(20), nullable=True)  # day, night
    scheduled_start = db.Column(db.Time, nullable=True)
    scheduled_end = db.Column(db.Time, nullable=True)
    
    # Late tracking
    late_minutes = db.Column(db.Integer, default=0, nullable=False)
    is_late = db.Column(db.Boolean, default=False, nullable=False)
    
    # Work hours
    total_hours = db.Column(db.Numeric(5, 2), nullable=True)
    regular_hours = db.Column(db.Numeric(5, 2), nullable=True)
    overtime_hours = db.Column(db.Numeric(5, 2), nullable=True)
    
    # Additional information
    notes = db.Column(db.Text, nullable=True)
    location_marked = db.Column(db.String(100), nullable=True)
    
    # System tracking
    marked_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Technical fields
    ip_address = db.Column(db.String(45), nullable=True)  # IPv6 support
    user_agent = db.Column(db.String(500), nullable=True)
    verification_method = db.Column(db.String(50), default='manual')  # manual, biometric, rfid
    
    # Unique constraint to prevent duplicate records
    __table_args__ = (
        db.UniqueConstraint('employee_id', 'date', name='unique_employee_date_attendance'),
        db.Index('idx_attendance_date_status', 'date', 'status'),
        db.Index('idx_attendance_employee_date', 'employee_id', 'date'),
    )
    
    @property
    def duration(self):
        """Calculate work duration in hours"""
        if self.clock_in and self.clock_out:
            duration = self.clock_out - self.clock_in
            
            # Subtract break time if recorded
            if self.break_start and self.break_end:
                break_duration = self.break_end - self.break_start
                duration -= break_duration
            
            return round(duration.total_seconds() / 3600, 2)
        return 0
    
    @property
    def is_overtime(self):
        """Check if this record has overtime"""
        return self.overtime_hours and self.overtime_hours > 0
    
    @property
    def is_present(self):
        """Check if employee is marked as present"""
        return self.status in ['present', 'late', 'half_day']
    
    @property
    def is_absent(self):
        """Check if employee is marked as absent"""
        return self.status in ['absent', 'on_leave']
    
    @property
    def status_display(self):
        """Get display-friendly status"""
        status_map = {
            'present': 'Present',
            'absent': 'Absent',
            'late': 'Late',
            'half_day': 'Half Day',
            'on_leave': 'On Leave'
        }
        return status_map.get(self.status, self.status.title())
    
    @property
    def status_color(self):
        """Get color class for status display"""
        color_map = {
            'present': 'success',
            'late': 'warning',
            'half_day': 'info',
            'absent': 'danger',
            'on_leave': 'secondary'
        }
        return color_map.get(self.status, 'secondary')
    
    def calculate_overtime(self):
        """Calculate overtime hours based on shift schedule"""
        if not self.total_hours:
            return 0
        
        # Standard work hours (8 hours per day)
        standard_hours = 8
        
        if self.total_hours > standard_hours:
            return round(self.total_hours - standard_hours, 2)
        
        return 0
    
    def is_on_time(self):
        """Check if employee clocked in on time"""
        if not self.clock_in or not self.scheduled_start:
            return True
        
        clock_in_time = self.clock_in.time()
        grace_period = 15  # 15 minutes grace period
        
        # Calculate grace time
        scheduled_datetime = datetime.combine(self.date, self.scheduled_start)
        grace_datetime = scheduled_datetime + datetime.timedelta(minutes=grace_period)
        grace_time = grace_datetime.time()
        
        return clock_in_time <= grace_time
    
    def update_calculated_fields(self):
        """Update calculated fields like total hours, overtime, etc."""
        # Calculate total hours
        if self.clock_in and self.clock_out:
            self.total_hours = self.duration
        
        # Calculate late status
        if not self.is_on_time():
            self.is_late = True
            if self.clock_in and self.scheduled_start:
                scheduled_datetime = datetime.combine(self.date, self.scheduled_start)
                late_delta = self.clock_in - scheduled_datetime
                self.late_minutes = int(late_delta.total_seconds() / 60)
        
        # Calculate overtime
        self.overtime_hours = self.calculate_overtime()
        self.regular_hours = min(self.total_hours or 0, 8)
    
    @classmethod
    def get_today_attendance(cls, location=None):
        """Get today's attendance summary"""
        today = date.today()
        query = cls.query.filter_by(date=today)
        
        if location:
            from models.employee import Employee
            query = query.join(Employee).filter(Employee.location == location)
        
        return query.all()
    
    @classmethod
    def get_attendance_summary(cls, start_date, end_date, location=None):
        """Get attendance summary for date range"""
        query = cls.query.filter(
            cls.date >= start_date,
            cls.date <= end_date
        )
        
        if location:
            from models.employee import Employee
            query = query.join(Employee).filter(Employee.location == location)
        
        # Count by status
        summary = {}
        records = query.all()
        
        for record in records:
            status = record.status
            if status not in summary:
                summary[status] = 0
            summary[status] += 1
        
        return summary
    
    def __repr__(self):
        return f'<AttendanceRecord {self.employee_id}: {self.date} - {self.status}>'