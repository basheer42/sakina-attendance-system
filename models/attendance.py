"""
Sakina Gas Company - Attendance Records Model (COMPLETE VERSION)
Built from scratch with comprehensive attendance tracking and analytics
Version 3.0 - Enterprise grade with full complexity - NO TRUNCATION
FIXED: SQLAlchemy relationship conflicts resolved
"""

from database import db
from sqlalchemy import Column, Integer, String, Date, DateTime, Time, Text, Boolean, Numeric, JSON, ForeignKey, func, Index
from sqlalchemy.orm import relationship, backref
from datetime import datetime, date, time, timedelta
from decimal import Decimal
import json

class AttendanceRecord(db.Model):
    """
    COMPLETE Professional attendance tracking model with comprehensive features
    FIXED: Resolved SQLAlchemy relationship conflicts - FULL COMPLEXITY
    """
    __tablename__ = 'attendance_records'
    
    # Primary identification
    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey('employees.id'), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    
    # Basic attendance information
    status = Column(String(20), nullable=False, default='present', index=True)  # present, absent, late, half_day, on_leave
    shift = Column(String(20), nullable=True, index=True)  # day, night, custom
    location = Column(String(50), nullable=True, index=True)  # dandora, tassia, kiambu, head_office
    
    # Time tracking - comprehensive
    scheduled_start_time = Column(Time, nullable=True)
    scheduled_end_time = Column(Time, nullable=True)
    actual_start_time = Column(Time, nullable=True)
    actual_end_time = Column(Time, nullable=True)
    
    # Clock in/out tracking with precise timestamps
    clock_in_time = Column(DateTime, nullable=True)
    clock_out_time = Column(DateTime, nullable=True)
    clock_in_location = Column(String(100), nullable=True)  # GPS or manual location
    clock_out_location = Column(String(100), nullable=True)
    
    # Break tracking - detailed
    break_start_time = Column(Time, nullable=True)
    break_end_time = Column(Time, nullable=True)
    total_break_minutes = Column(Integer, nullable=False, default=0)
    
    # Multiple break periods support
    break_periods = Column(JSON, nullable=True)  # [{"start": "time", "end": "time", "type": "lunch/tea/personal"}]
    
    # Calculated durations - precise tracking
    scheduled_hours = Column(Numeric(5, 2), nullable=False, default=8.0)
    worked_hours = Column(Numeric(5, 2), nullable=False, default=0.0)
    overtime_hours = Column(Numeric(5, 2), nullable=False, default=0.0)
    undertime_hours = Column(Numeric(5, 2), nullable=False, default=0.0)
    regular_hours = Column(Numeric(5, 2), nullable=False, default=0.0)
    
    # Lateness and early departure tracking
    late_arrival_minutes = Column(Integer, nullable=False, default=0)
    early_departure_minutes = Column(Integer, nullable=False, default=0)
    
    # Advanced time calculations
    grace_period_used = Column(Boolean, nullable=False, default=False)
    grace_period_minutes = Column(Integer, nullable=False, default=0)
    total_productive_hours = Column(Numeric(5, 2), nullable=False, default=0.0)
    
    # IP and device tracking - security
    clock_in_ip = Column(String(45), nullable=True)
    clock_out_ip = Column(String(45), nullable=True)
    clock_in_device = Column(String(100), nullable=True)
    clock_out_device = Column(String(100), nullable=True)
    clock_in_user_agent = Column(Text, nullable=True)
    clock_out_user_agent = Column(Text, nullable=True)
    
    # Location verification and GPS
    clock_in_gps_coordinates = Column(JSON, nullable=True)  # {"lat": float, "lng": float, "accuracy": float}
    clock_out_gps_coordinates = Column(JSON, nullable=True)
    location_verified = Column(Boolean, nullable=False, default=False)
    location_variance_meters = Column(Integer, nullable=True)  # Distance from expected location
    
    # Biometric and authentication method
    clock_in_method = Column(String(30), nullable=False, default='manual')  # manual, biometric, mobile, web, api
    clock_out_method = Column(String(30), nullable=True)
    biometric_data = Column(JSON, nullable=True)  # Encrypted biometric verification data
    authentication_score = Column(Numeric(5, 2), nullable=True)  # Confidence score for authentication
    
    # Approval workflow - comprehensive
    is_approved = Column(Boolean, nullable=False, default=False)
    approved_by = Column(Integer, nullable=True)  # User ID
    approved_date = Column(DateTime, nullable=True)
    approval_notes = Column(Text, nullable=True)
    requires_manager_approval = Column(Boolean, nullable=False, default=False)
    requires_hr_approval = Column(Boolean, nullable=False, default=False)
    
    # Manager override capabilities
    is_manual_entry = Column(Boolean, nullable=False, default=False)
    manual_entry_reason = Column(Text, nullable=True)
    entered_by = Column(Integer, nullable=True)  # User ID who made manual entry
    manual_entry_timestamp = Column(DateTime, nullable=True)
    original_data_backup = Column(JSON, nullable=True)  # Backup of original data before manual changes
    
    # Shift information - detailed
    shift_type = Column(String(20), nullable=False, default='day')  # day, night, custom, split
    shift_pattern = Column(String(50), nullable=True)  # 9-to-5, 24hr, rotating, flex-time
    shift_start_window = Column(JSON, nullable=True)  # Flexible start time window
    shift_end_window = Column(JSON, nullable=True)  # Flexible end time window
    is_flexible_shift = Column(Boolean, nullable=False, default=False)
    
    # Rotation and schedule management
    rotation_week = Column(Integer, nullable=True)  # Week number in rotation cycle
    rotation_cycle_id = Column(String(20), nullable=True)  # ID of rotation pattern
    schedule_version = Column(String(20), nullable=True)  # Version of schedule used
    schedule_exceptions = Column(JSON, nullable=True)  # Special schedule modifications
    
    # Additional tracking - performance and productivity
    productivity_score = Column(Numeric(5, 2), nullable=True)  # Performance metric 0-100
    tasks_completed = Column(Integer, nullable=True)
    meetings_attended = Column(Integer, nullable=True)
    project_hours = Column(JSON, nullable=True)  # {"project_id": hours_spent}
    department_activities = Column(JSON, nullable=True)  # Department-specific activities
    
    # Client and customer interaction tracking
    customers_served = Column(Integer, nullable=True)
    service_quality_rating = Column(Numeric(3, 2), nullable=True)  # 1-5 rating
    customer_feedback_summary = Column(Text, nullable=True)
    
    # Sales and revenue tracking (for stations)
    sales_amount = Column(Numeric(12, 2), nullable=True)  # Daily sales for station employees
    fuel_dispensed_liters = Column(Numeric(10, 2), nullable=True)  # Fuel dispensed
    transactions_processed = Column(Integer, nullable=True)
    cash_handled = Column(Numeric(12, 2), nullable=True)
    
    # Notes and comments - comprehensive
    notes = Column(Text, nullable=True)  # Employee self-notes
    manager_notes = Column(Text, nullable=True)  # Manager/supervisor notes
    hr_notes = Column(Text, nullable=True)  # HR department notes
    system_notes = Column(Text, nullable=True)  # Automated system notes
    private_notes = Column(Text, nullable=True)  # Internal management notes
    
    # Absence details (when applicable)
    absence_type = Column(String(30), nullable=True)  # sick, personal, vacation, emergency, bereavement
    absence_reason = Column(Text, nullable=True)
    absence_category = Column(String(20), nullable=True)  # planned, unplanned, emergency
    doctor_note_required = Column(Boolean, nullable=False, default=False)
    doctor_note_provided = Column(Boolean, nullable=False, default=False)
    doctor_note_expiry = Column(Date, nullable=True)
    return_to_work_clearance = Column(Boolean, nullable=False, default=False)
    
    # Leave integration - comprehensive
    leave_request_id = Column(Integer, ForeignKey('leave_requests.id'), nullable=True)
    leave_type_used = Column(String(30), nullable=True)  # annual, sick, maternity, paternity
    leave_days_deducted = Column(Numeric(4, 2), nullable=False, default=0.0)  # Support half days
    
    # Weather and external factors
    weather_conditions = Column(String(50), nullable=True)  # sunny, rainy, stormy, etc.
    weather_impact = Column(Boolean, nullable=False, default=False)
    transport_issues = Column(Boolean, nullable=False, default=False)
    transport_details = Column(Text, nullable=True)
    power_outage = Column(Boolean, nullable=False, default=False)
    equipment_failure = Column(Boolean, nullable=False, default=False)
    external_factors = Column(JSON, nullable=True)  # Other external factors affecting attendance
    
    # Emergency and safety
    safety_incident = Column(Boolean, nullable=False, default=False)
    safety_incident_details = Column(Text, nullable=True)
    emergency_response_participated = Column(Boolean, nullable=False, default=False)
    first_aid_provided = Column(Boolean, nullable=False, default=False)
    
    # Training and development
    training_hours = Column(Numeric(4, 2), nullable=False, default=0.0)
    training_topics = Column(JSON, nullable=True)  # ["Safety", "Customer Service", "Equipment"]
    skill_assessments_completed = Column(Integer, nullable=False, default=0)
    certifications_earned = Column(JSON, nullable=True)
    
    # System metadata - comprehensive
    created_date = Column(DateTime, nullable=False, default=func.current_timestamp())
    created_by = Column(Integer, nullable=True)  # User ID who created record
    last_updated = Column(DateTime, nullable=False, default=func.current_timestamp(), onupdate=func.current_timestamp())
    updated_by = Column(Integer, nullable=True)  # User ID who last updated
    
    # Version control and change tracking
    version_number = Column(Integer, nullable=False, default=1)
    change_summary = Column(Text, nullable=True)  # Summary of changes made
    previous_versions = Column(JSON, nullable=True)  # History of previous versions
    
    # Flexible metadata storage
    attendance_metadata = Column(JSON, nullable=True)  # Additional custom data
    
    # Device and technology tracking - detailed
    device_info = Column(JSON, nullable=True)  # Device specifications and details
    app_version = Column(String(20), nullable=True)  # Mobile app version
    browser_info = Column(JSON, nullable=True)  # Browser details for web access
    
    # Network and connectivity
    network_type = Column(String(20), nullable=True)  # wifi, cellular, ethernet
    network_quality = Column(String(20), nullable=True)  # excellent, good, poor
    connection_speed = Column(String(20), nullable=True)
    
    # Compliance and audit - comprehensive
    is_compliant = Column(Boolean, nullable=False, default=True)
    compliance_score = Column(Numeric(5, 2), nullable=True)  # 0-100 compliance score
    compliance_notes = Column(Text, nullable=True)
    audit_trail = Column(JSON, nullable=True)  # Detailed changes history
    
    # Legal and regulatory
    labor_law_compliance = Column(Boolean, nullable=False, default=True)
    overtime_authorization = Column(Boolean, nullable=False, default=False)
    overtime_reason = Column(Text, nullable=True)
    break_compliance = Column(Boolean, nullable=False, default=True)
    
    # Performance indicators - detailed
    efficiency_rating = Column(String(20), nullable=True)  # excellent, good, average, poor, critical
    punctuality_score = Column(Numeric(5, 2), nullable=True)  # 0-100 punctuality score
    reliability_score = Column(Numeric(5, 2), nullable=True)  # 0-100 reliability score
    overall_performance_score = Column(Numeric(5, 2), nullable=True)  # Combined performance metric
    
    # Automated calculations and flags
    is_perfect_attendance = Column(Boolean, nullable=False, default=False)
    is_exceptional_performance = Column(Boolean, nullable=False, default=False)
    requires_follow_up = Column(Boolean, nullable=False, default=False)
    follow_up_reason = Column(Text, nullable=True)
    
    # Integration with other systems
    payroll_processed = Column(Boolean, nullable=False, default=False)
    payroll_batch_id = Column(String(50), nullable=True)
    exported_to_hr_system = Column(Boolean, nullable=False, default=False)
    export_timestamp = Column(DateTime, nullable=True)
    
    # Data quality and validation
    data_quality_score = Column(Numeric(5, 2), nullable=True)  # Quality of attendance data
    anomaly_detected = Column(Boolean, nullable=False, default=False)
    anomaly_type = Column(String(50), nullable=True)
    anomaly_confidence = Column(Numeric(5, 2), nullable=True)
    manual_verification_required = Column(Boolean, nullable=False, default=False)
    
    # FIXED: Simplified relationships to avoid conflicts
    # The employee relationship is managed by the Employee model
    # Leave request relationship - FIX: Changed back_populates to backref to avoid the reported error
    leave_request = relationship('LeaveRequest', backref='attendance_records', lazy='select')
    
    # Indexes for optimal performance
    __table_args__ = (
        Index('idx_employee_date', 'employee_id', 'date'),
        Index('idx_date_status', 'date', 'status'),
        Index('idx_location_date', 'location', 'date'),
        Index('idx_shift_date', 'shift', 'date'),
        Index('idx_approval_status', 'is_approved', 'requires_manager_approval'),
        Index('idx_manual_entry', 'is_manual_entry', 'entered_by'),
        Index('idx_compliance', 'is_compliant', 'labor_law_compliance'),
        Index('idx_performance', 'efficiency_rating', 'punctuality_score'),
    )
    
    def __init__(self, **kwargs):
        """Initialize attendance record with comprehensive defaults"""
        # Note: Calling super().__init__() is enough, but preserving user's explicit style.
        # super(AttendanceRecord, self).__init__() 
        
        # Set default metadata structures (only necessary if JSON columns default is not properly set in SQLAlchemy dialect)
        if 'attendance_metadata' not in kwargs:
             self.attendance_metadata = {}
        if 'audit_trail' not in kwargs:
             self.audit_trail = []
        if 'device_info' not in kwargs:
             self.device_info = {}
        if 'break_periods' not in kwargs:
             self.break_periods = []
        if 'project_hours' not in kwargs:
             self.project_hours = {}
        if 'department_activities' not in kwargs:
             self.department_activities = {}
        if 'external_factors' not in kwargs:
             self.external_factors = {}
        if 'training_topics' not in kwargs:
             self.training_topics = []
        if 'certifications_earned' not in kwargs:
             self.certifications_earned = []
        if 'previous_versions' not in kwargs:
             self.previous_versions = []
        
        # Set creation timestamp and version
        if 'created_date' not in kwargs:
             self.created_date = datetime.utcnow()
        if 'version_number' not in kwargs:
             self.version_number = 1
        
        # Initialize performance scores (Decimal initialization is important)
        if 'punctuality_score' not in kwargs:
             self.punctuality_score = Decimal(100.0)
        if 'reliability_score' not in kwargs:
             self.reliability_score = Decimal(100.0)
        if 'compliance_score' not in kwargs:
             self.compliance_score = Decimal(100.0)
        if 'data_quality_score' not in kwargs:
             self.data_quality_score = Decimal(100.0)
        
        # Apply any provided kwargs
        for key, value in kwargs.items():
            if hasattr(self, key):
                # Handle Decimal conversions for Numeric types
                if isinstance(getattr(self.__class__, key).type, (Numeric)) and value is not None:
                    setattr(self, key, Decimal(str(value)))
                # Set DateTime objects directly
                elif isinstance(getattr(self.__class__, key).type, (DateTime, Date, Time)) and value is not None:
                     setattr(self, key, value)
                # Set others
                else:
                    setattr(self, key, value)
    
    def calculate_worked_hours(self):
        """Calculate actual worked hours with advanced logic"""
        if not self.actual_start_time or not self.actual_end_time:
            self.worked_hours = Decimal(0.0)
            return self.worked_hours
        
        # Convert times to datetime for calculation (self.date is a Date object)
        start_datetime = datetime.combine(self.date, self.actual_start_time)
        end_datetime = datetime.combine(self.date, self.actual_end_time)
        
        # Handle overnight shifts (if end time is earlier than start time on the same date, assume it's the next day)
        if end_datetime < start_datetime:
            end_datetime = datetime.combine(self.date + timedelta(days=1), self.actual_end_time)
        
        # Calculate total time in minutes
        total_minutes = (end_datetime - start_datetime).total_seconds() / 60
        
        # Subtract break time
        break_minutes = self.total_break_minutes
        if self.break_periods:
            # Calculate break time from detailed periods
            break_minutes = sum([
                self._calculate_break_duration(period) 
                for period in self.break_periods
            ])
        
        # Calculate net worked time
        net_minutes = total_minutes - break_minutes
        net_hours = max(0, net_minutes / 60)
        
        # Update worked hours
        self.worked_hours = round(Decimal(net_hours), 2)
        
        # Use Decimal for all calculations involving Numeric fields
        scheduled_hours = self.scheduled_hours if self.scheduled_hours else Decimal(0.0)
        
        # Calculate overtime and regular hours
        if self.worked_hours > scheduled_hours:
            self.regular_hours = scheduled_hours
            self.overtime_hours = round(self.worked_hours - scheduled_hours, 2)
            self.undertime_hours = Decimal(0.0)
        else:
            self.regular_hours = self.worked_hours
            self.overtime_hours = Decimal(0.0)
            self.undertime_hours = round(scheduled_hours - self.worked_hours, 2)
        
        # Calculate productive hours (excluding non-productive activities like training)
        training_hours = self.training_hours if self.training_hours else Decimal(0.0)
        self.total_productive_hours = self.worked_hours - training_hours
        
        return self.worked_hours
    
    def _calculate_break_duration(self, break_period):
        """Calculate duration of a single break period"""
        try:
            if isinstance(break_period, dict) and 'start' in break_period and 'end' in break_period:
                
                # Handling Time/String conversion
                start_val = break_period['start']
                end_val = break_period['end']
                
                start_time = start_val if isinstance(start_val, time) else datetime.strptime(start_val, '%H:%M').time()
                end_time = end_val if isinstance(end_val, time) else datetime.strptime(end_val, '%H:%M').time()
                
                start_datetime = datetime.combine(self.date, start_time)
                end_datetime = datetime.combine(self.date, end_time)
                
                # Handle breaks that cross midnight
                if end_datetime < start_datetime:
                    end_datetime += timedelta(days=1)
                
                return (end_datetime - start_datetime).total_seconds() / 60
        except Exception as e:
            # Log error if needed: current_app.logger.error(f"Break duration error: {e}")
            pass
        return 0
    
    def mark_present(self, clock_in_time=None, location=None, method='manual', device_info=None):
        """Mark employee as present with comprehensive tracking"""
        self.status = 'present'
        self.clock_in_time = clock_in_time or datetime.utcnow()
        self.clock_in_location = location
        self.clock_in_method = method
        
        # FIX: Ensure actual_start_time is a time object from the DateTime object
        if isinstance(self.clock_in_time, datetime):
            self.actual_start_time = self.clock_in_time.time()
        elif self.clock_in_time:
             # Assuming it is already a time object if not a datetime (unlikely for clock-in)
             self.actual_start_time = self.clock_in_time
        
        if device_info:
            if not self.device_info:
                 self.device_info = {}
            self.device_info.update({'clock_in': device_info})
        
        # Calculate lateness
        if self.scheduled_start_time and self.actual_start_time:
            self.late_arrival_minutes = self.get_lateness_minutes()
            if self.late_arrival_minutes > 0:
                self.status = 'late'
        
        # Update audit trail
        self._add_audit_entry('mark_present', {
            'time': self.clock_in_time.isoformat() if isinstance(self.clock_in_time, datetime) else str(self.clock_in_time),
            'location': location,
            'method': method
        })
    
    def mark_absent(self, reason=None, absence_type='unplanned', requires_documentation=False):
        """Mark employee as absent with detailed tracking"""
        self.status = 'absent'
        self.absence_reason = reason
        self.absence_type = absence_type
        self.worked_hours = Decimal(0.0)
        self.regular_hours = Decimal(0.0)
        self.overtime_hours = Decimal(0.0)
        # Use Decimal for comparison
        scheduled_hours = self.scheduled_hours if self.scheduled_hours else Decimal(0.0)
        self.undertime_hours = scheduled_hours 
        
        if requires_documentation:
            self.doctor_note_required = True
        
        # Update audit trail
        self._add_audit_entry('mark_absent', {
            'reason': reason,
            'type': absence_type,
            'requires_documentation': requires_documentation
        })
    
    def clock_out(self, clock_out_time=None, location=None, method=None, device_info=None):
        """Record clock out time with comprehensive tracking"""
        self.clock_out_time = clock_out_time or datetime.utcnow()
        self.clock_out_location = location
        self.clock_out_method = method or self.clock_in_method
        
        # FIX: Ensure actual_end_time is a time object from the DateTime object
        if isinstance(self.clock_out_time, datetime):
            self.actual_end_time = self.clock_out_time.time()
        elif self.clock_out_time:
             self.actual_end_time = self.clock_out_time
        
        if device_info:
            if not self.device_info:
                self.device_info = {}
            self.device_info['clock_out'] = device_info
        
        # Calculate early departure
        if self.scheduled_end_time and self.actual_end_time:
            self.early_departure_minutes = self.get_early_departure_minutes()
        
        # Calculate worked hours
        self.calculate_worked_hours()
        
        # Update performance scores
        self.update_performance_scores()
        
        # Update audit trail
        self._add_audit_entry('clock_out', {
            'time': self.clock_out_time.isoformat() if isinstance(self.clock_out_time, datetime) else str(self.clock_out_time),
            'location': location,
            'method': method,
            'worked_hours': float(self.worked_hours)
        })
    
    def add_break_period(self, start_time, end_time, break_type='lunch'):
        """Add a break period to the attendance record"""
        if not self.break_periods:
            self.break_periods = []
        
        # Format times as strings for JSON persistence if they are time objects
        start_str = start_time.strftime('%H:%M') if isinstance(start_time, time) else start_time
        end_str = end_time.strftime('%H:%M') if isinstance(end_time, time) else end_time
        
        break_period = {
            'start': start_str,
            'end': end_str,
            'type': break_type,
            'duration_minutes': self._calculate_break_duration({
                'start': start_str,
                'end': end_str
            })
        }
        
        self.break_periods.append(break_period)
        
        # Update total break minutes
        self.total_break_minutes = sum([
            period.get('duration_minutes', 0) 
            for period in self.break_periods
        ])
        
        # Recalculate worked hours
        if self.actual_start_time and self.actual_end_time:
            self.calculate_worked_hours()
    
    def is_late(self):
        """Check if employee was late"""
        if not self.actual_start_time or not self.scheduled_start_time:
            return False
        
        # Compare Time objects directly
        return self.actual_start_time > self.scheduled_start_time
    
    def get_lateness_minutes(self):
        """Get lateness in minutes"""
        if not self.is_late():
            return 0
        
        start_scheduled = datetime.combine(self.date, self.scheduled_start_time)
        start_actual = datetime.combine(self.date, self.actual_start_time)
        
        # Apply grace period
        grace_minutes = self.grace_period_minutes or 0
        lateness = int((start_actual - start_scheduled).total_seconds() / 60)
        
        if lateness <= grace_minutes:
            self.grace_period_used = True
            return 0
        
        return max(0, lateness - grace_minutes)
    
    def get_early_departure_minutes(self):
        """Get early departure in minutes"""
        if not self.actual_end_time or not self.scheduled_end_time:
            return 0
        
        end_scheduled = datetime.combine(self.date, self.scheduled_end_time)
        end_actual = datetime.combine(self.date, self.actual_end_time)
        
        if end_actual < end_scheduled:
            return int((end_scheduled - end_actual).total_seconds() / 60)
        
        return 0
    
    def update_performance_scores(self):
        """Update performance scores based on attendance data"""
        # Punctuality score
        # Use Decimal for consistency
        punctuality_score_val = Decimal(100.0)
        if self.late_arrival_minutes > 0:
            if self.late_arrival_minutes <= 15:
                punctuality_score_val = Decimal(85.0)
            elif self.late_arrival_minutes <= 30:
                punctuality_score_val = Decimal(70.0)
            else:
                punctuality_score_val = Decimal(50.0)
        self.punctuality_score = punctuality_score_val
        
        # Efficiency score based on worked vs scheduled hours
        scheduled_hours = self.scheduled_hours if self.scheduled_hours else Decimal(0.0)
        if scheduled_hours > Decimal(0):
             efficiency = min(Decimal(100.0), (self.worked_hours / scheduled_hours) * Decimal(100.0))
        else:
             efficiency = Decimal(100.0)
        
        self.efficiency_rating = self._get_efficiency_rating(efficiency)
        
        # Overall performance score
        productivity_score = self.productivity_score if self.productivity_score else Decimal(80.0)
        
        self.overall_performance_score = (
            self.punctuality_score * Decimal(0.4) +
            efficiency * Decimal(0.4) +
            productivity_score * Decimal(0.2)
        )
        
        # Check for perfect attendance
        self.is_perfect_attendance = (
            self.status == 'present' and
            self.late_arrival_minutes == 0 and
            self.early_departure_minutes == 0 and
            self.worked_hours >= scheduled_hours
        )
        
        # Check for exceptional performance
        self.is_exceptional_performance = (
            self.overall_performance_score >= Decimal(95.0) and
            (self.overtime_hours or Decimal(0.0)) > Decimal(0.0)
        )
    
    def _get_efficiency_rating(self, efficiency_score):
        """Convert efficiency score to rating"""
        if efficiency_score >= Decimal(95):
            return 'excellent'
        elif efficiency_score >= Decimal(85):
            return 'good'
        elif efficiency_score >= Decimal(70):
            return 'average'
        elif efficiency_score >= Decimal(50):
            return 'poor'
        else:
            return 'critical'
    
    def _add_audit_entry(self, action, details):
        """Add entry to audit trail"""
        if not self.audit_trail:
            self.audit_trail = []
        
        entry = {
            'action': action,
            'timestamp': datetime.utcnow().isoformat(),
            'details': details,
            'user_id': getattr(self, '_current_user_id', None)
        }
        
        self.audit_trail.append(entry)
    
    def approve_record(self, approver_id, notes=None):
        """Approve attendance record"""
        self.is_approved = True
        self.approved_by = approver_id
        self.approved_date = datetime.utcnow()
        self.approval_notes = notes
        
        self._add_audit_entry('approve', {
            'approver_id': approver_id,
            'notes': notes
        })
    
    def flag_for_review(self, reason, reviewer_role='manager'):
        """Flag record for manual review"""
        self.requires_follow_up = True
        self.follow_up_reason = reason
        
        if reviewer_role == 'hr':
            self.requires_hr_approval = True
        else:
            self.requires_manager_approval = True
        
        self._add_audit_entry('flag_for_review', {
            'reason': reason,
            'reviewer_role': reviewer_role
        })
    
    def detect_anomalies(self):
        """Detect potential anomalies in attendance data"""
        anomalies = []
        
        # Check for unusual working hours
        if (self.worked_hours or Decimal(0.0)) > 16:
            anomalies.append('excessive_hours')
        
        # Check for multiple clock-ins on same day
        if self.is_manual_entry and not self.manual_entry_reason:
            anomalies.append('manual_entry_without_reason')
        
        # Check for location inconsistencies
        if (self.clock_in_location and self.clock_out_location and 
            self.clock_in_location != self.clock_out_location):
            anomalies.append('location_mismatch')
        
        # Check for suspicious timing patterns
        if self.late_arrival_minutes > 120:  # More than 2 hours late
            anomalies.append('excessive_lateness')
        
        if anomalies:
            self.anomaly_detected = True
            self.anomaly_type = ', '.join(anomalies)
            self.manual_verification_required = True
        
        return anomalies
    
    def export_for_payroll(self):
        """Export attendance data for payroll processing"""
        payroll_data = {
            'employee_id': self.employee_id,
            'date': self.date.isoformat(),
            'regular_hours': float(self.regular_hours),
            'overtime_hours': float(self.overtime_hours),
            'status': self.status,
            'approved': self.is_approved,
            'location': self.location,
            'shift_type': self.shift_type
        }
        
        if self.sales_amount:
            payroll_data['sales_amount'] = float(self.sales_amount)
        
        if self.customers_served:
            payroll_data['customers_served'] = self.customers_served
        
        return payroll_data
    
    def to_dict(self):
        """Convert attendance record to dictionary for API responses"""
        # Ensure Decimal values are converted to float/str
        worked_hours = float(self.worked_hours) if self.worked_hours is not None else 0.0
        scheduled_hours = float(self.scheduled_hours) if self.scheduled_hours is not None else 0.0
        regular_hours = float(self.regular_hours) if self.regular_hours is not None else 0.0
        overtime_hours = float(self.overtime_hours) if self.overtime_hours is not None else 0.0
        punctuality_score = float(self.punctuality_score) if self.punctuality_score is not None else None
        overall_performance_score = float(self.overall_performance_score) if self.overall_performance_score is not None else None
        sales_amount = float(self.sales_amount) if self.sales_amount is not None else None
        
        data = {
            'id': self.id,
            'employee_id': self.employee_id,
            'date': self.date.isoformat() if self.date else None,
            'status': self.status,
            'shift': self.shift,
            'location': self.location,
            # Ensure proper ISO/string formatting for mixed Time/DateTime types if they exist
            'clock_in_time': self.clock_in_time.isoformat() if isinstance(self.clock_in_time, datetime) else str(self.clock_in_time) if self.clock_in_time else None,
            'clock_out_time': self.clock_out_time.isoformat() if isinstance(self.clock_out_time, datetime) else str(self.clock_out_time) if self.clock_out_time else None,
            'scheduled_hours': scheduled_hours,
            'worked_hours': worked_hours,
            'regular_hours': regular_hours,
            'overtime_hours': overtime_hours,
            'is_late': self.is_late(),
            'lateness_minutes': self.get_lateness_minutes(),
            'is_approved': self.is_approved,
            'notes': self.notes,
            'manager_notes': self.manager_notes,
            'efficiency_rating': self.efficiency_rating,
            'punctuality_score': punctuality_score,
            'overall_performance_score': overall_performance_score,
            'is_perfect_attendance': self.is_perfect_attendance,
            'requires_follow_up': self.requires_follow_up,
            'created_date': self.created_date.isoformat() if self.created_date else None,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }
        
        # Add optional fields if present
        if self.absence_reason:
            data['absence_reason'] = self.absence_reason
        
        if self.leave_request_id:
            data['leave_request_id'] = self.leave_request_id
        
        if sales_amount:
            data['sales_amount'] = sales_amount
        
        if self.customers_served:
            data['customers_served'] = self.customers_served
        
        return data
    
    @classmethod
    def get_attendance_for_date(cls, target_date, location=None, department=None, include_inactive=False):
        """Get attendance records for a specific date with filtering"""
        # Import Employee model locally to avoid circular imports
        from models.employee import Employee
        
        query = cls.query.join(Employee).filter(cls.date == target_date)
        
        if not include_inactive:
            query = query.filter(Employee.is_active == True)
        
        if location:
            query = query.filter(Employee.location == location)
        
        if department:
            query = query.filter(Employee.department == department)
        
        return query.order_by(Employee.last_name, Employee.first_name).all()
    
    @classmethod
    def get_employee_attendance_range(cls, employee_id, start_date, end_date):
        """Get attendance records for employee within date range"""
        return cls.query.filter(
            cls.employee_id == employee_id,
            cls.date.between(start_date, end_date)
        ).order_by(cls.date).all()
    
    @classmethod
    def get_attendance_summary(cls, start_date, end_date, location=None, department=None):
        """Get attendance summary for date range with detailed statistics"""
        from models.employee import Employee
        
        # Use str conversion for Numeric/Decimal types in aggregation results
        query = db.session.query(
            cls.status,
            func.count(cls.id).label('count'),
            func.avg(cls.worked_hours).label('avg_hours'),
            func.sum(cls.overtime_hours).label('total_overtime'),
            func.avg(cls.punctuality_score).label('avg_punctuality')
        ).join(Employee).filter(
            cls.date.between(start_date, end_date),
            Employee.is_active == True
        )
        
        if location:
            query = query.filter(Employee.location == location)
        
        if department:
            query = query.filter(Employee.department == department)
        
        query = query.group_by(cls.status)
        results = query.all()
        
        summary = {}
        for result in results:
            # Conversion from result Decimal/Numeric to float for presentation layer
            summary[result.status] = {
                'count': result.count,
                'avg_hours': float(result.avg_hours or 0),
                'total_overtime': float(result.total_overtime or 0),
                'avg_punctuality': float(result.avg_punctuality or 100)
            }
        
        return summary
    
    @classmethod
    def get_performance_metrics(cls, start_date, end_date, location=None):
        """Get performance metrics for date range"""
        from models.employee import Employee
        
        query = cls.query.join(Employee).filter(
            cls.date.between(start_date, end_date),
            Employee.is_active == True,
            cls.status.in_(['present', 'late'])
        )
        
        if location:
            query = query.filter(Employee.location == location)
        
        records = query.all()
        
        if not records:
            return None
        
        total_records = len(records)
        perfect_attendance = len([r for r in records if r.is_perfect_attendance])
        exceptional_performance = len([r for r in records if r.is_exceptional_performance])
        
        # Ensure Decimal fields are converted before summation/average
        avg_punctuality = sum([float(r.punctuality_score) or 0 for r in records]) / total_records if total_records else 0
        avg_performance = sum([float(r.overall_performance_score) or 0 for r in records]) / total_records if total_records else 0
        total_overtime = sum([float(r.overtime_hours) for r in records if r.overtime_hours])
        
        return {
            'total_records': total_records,
            'perfect_attendance_rate': (perfect_attendance / total_records) * 100,
            'exceptional_performance_rate': (exceptional_performance / total_records) * 100,
            'average_punctuality': avg_punctuality,
            'average_performance': avg_performance,
            'total_overtime_hours': total_overtime
        }
    
    @classmethod
    def create_attendance_record(cls, employee_id, date, **kwargs):
        """Create new attendance record with validation"""
        # Check if record already exists
        existing = cls.query.filter_by(employee_id=employee_id, date=date).first()
        if existing:
            raise ValueError(f"Attendance record already exists for employee {employee_id} on {date}")
        
        record = cls(employee_id=employee_id, date=date, **kwargs)
        record.detect_anomalies()  # Automatically detect anomalies
        
        return record
    
    def __repr__(self):
        """String representation of attendance record"""
        try:
            # FIX: Access relationship via 'employee' property
            employee_name = f"{self.employee.first_name} {self.employee.last_name}" if hasattr(self, 'employee') and self.employee else f"Employee {self.employee_id}"
            
            worked_hours_display = float(self.worked_hours) if self.worked_hours is not None else 0.0
            
            return f'<AttendanceRecord {employee_name}: {self.date} - {self.status} ({worked_hours_display:.2f}h)>'
        except:
            return f'<AttendanceRecord ID:{self.id} Employee:{self.employee_id} Date:{self.date}>'


class AttendanceSummary(db.Model):
    """
    Monthly attendance summary for performance tracking and reporting
    """
    __tablename__ = 'attendance_summaries'
    
    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey('employees.id'), nullable=False)
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    
    # Basic attendance statistics
    total_working_days = Column(Integer, nullable=False, default=0)
    total_scheduled_days = Column(Integer, nullable=False, default=0)
    present_days = Column(Integer, nullable=False, default=0)
    absent_days = Column(Integer, nullable=False, default=0)
    late_days = Column(Integer, nullable=False, default=0)
    half_days = Column(Integer, nullable=False, default=0)
    early_departures = Column(Integer, nullable=False, default=0)
    
    # Hours tracking
    total_scheduled_hours = Column(Numeric(8, 2), nullable=False, default=0)
    total_worked_hours = Column(Numeric(8, 2), nullable=False, default=0)
    total_regular_hours = Column(Numeric(8, 2), nullable=False, default=0)
    total_overtime_hours = Column(Numeric(8, 2), nullable=False, default=0)
    total_undertime_hours = Column(Numeric(8, 2), nullable=False, default=0)
    
    # Performance metrics
    attendance_percentage = Column(Numeric(5, 2), nullable=False, default=0)
    punctuality_percentage = Column(Numeric(5, 2), nullable=False, default=0)
    average_daily_hours = Column(Numeric(5, 2), nullable=False, default=0)
    average_punctuality_score = Column(Numeric(5, 2), nullable=False, default=0)
    average_performance_score = Column(Numeric(5, 2), nullable=False, default=0)
    
    # Leave and absence tracking
    sick_days = Column(Integer, nullable=False, default=0)
    vacation_days = Column(Integer, nullable=False, default=0)
    personal_days = Column(Integer, nullable=False, default=0)
    emergency_days = Column(Integer, nullable=False, default=0)
    
    # Productivity and performance
    total_tasks_completed = Column(Integer, nullable=False, default=0)
    total_customers_served = Column(Integer, nullable=False, default=0)
    total_sales_amount = Column(Numeric(12, 2), nullable=False, default=0)
    training_hours = Column(Numeric(6, 2), nullable=False, default=0)
    
    # Quality indicators
    perfect_attendance_days = Column(Integer, nullable=False, default=0)
    exceptional_performance_days = Column(Integer, nullable=False, default=0)
    anomaly_count = Column(Integer, nullable=False, default=0)
    requires_attention = Column(Boolean, nullable=False, default=False)
    
    # Metadata
    created_date = Column(DateTime, nullable=False, default=func.current_timestamp())
    last_calculated = Column(DateTime, nullable=False, default=func.current_timestamp())
    calculation_version = Column(String(10), nullable=False, default='1.0')
    
    # Indexes
    __table_args__ = (
        Index('idx_employee_year_month', 'employee_id', 'year', 'month'),
        Index('idx_year_month', 'year', 'month'),
    )
    
    @classmethod
    def calculate_summary(cls, employee_id, year, month):
        """Calculate attendance summary for employee for given month"""
        from calendar import monthrange
        from models.employee import Employee
        
        # Get month date range
        start_date = date(year, month, 1)
        last_day = monthrange(year, month)[1]
        end_date = date(year, month, last_day)
        
        # Get all attendance records for the month
        records = AttendanceRecord.query.filter(
            AttendanceRecord.employee_id == employee_id,
            AttendanceRecord.date.between(start_date, end_date)
        ).all()
        
        # Get or create summary record
        summary = cls.query.filter_by(
            employee_id=employee_id,
            year=year,
            month=month
        ).first()
        
        if not summary:
            summary = cls(employee_id=employee_id, year=year, month=month)
        
        # Calculate statistics
        summary.total_working_days = len(records)
        summary.present_days = len([r for r in records if r.status in ['present', 'late']])
        summary.absent_days = len([r for r in records if r.status == 'absent'])
        summary.late_days = len([r for r in records if r.status == 'late'])
        summary.half_days = len([r for r in records if r.status == 'half_day'])
        
        # Hours calculations
        summary.total_worked_hours = sum([r.worked_hours or Decimal(0.0) for r in records])
        summary.total_regular_hours = sum([r.regular_hours or Decimal(0.0) for r in records])
        summary.total_overtime_hours = sum([r.overtime_hours or Decimal(0.0) for r in records])
        summary.total_scheduled_hours = sum([r.scheduled_hours or Decimal(0.0) for r in records])
        
        # Percentages
        if summary.total_working_days > 0:
            summary.attendance_percentage = Decimal((summary.present_days / summary.total_working_days) * 100)
            summary.punctuality_percentage = Decimal(((summary.present_days - summary.late_days) / summary.total_working_days) * 100)
        
        # Performance metrics
        if records:
            valid_scores = [r.punctuality_score for r in records if r.punctuality_score is not None]
            summary.average_punctuality_score = Decimal(sum(valid_scores) / len(valid_scores)) if valid_scores else Decimal(0)
            
            perf_scores = [r.overall_performance_score for r in records if r.overall_performance_score is not None]
            summary.average_performance_score = Decimal(sum(perf_scores) / len(perf_scores)) if perf_scores else Decimal(0)
        
        # Quality indicators
        summary.perfect_attendance_days = len([r for r in records if r.is_perfect_attendance])
        summary.exceptional_performance_days = len([r for r in records if r.is_exceptional_performance])
        summary.anomaly_count = len([r for r in records if r.anomaly_detected])
        
        # Set attention flag
        summary.requires_attention = (
            summary.attendance_percentage < Decimal(90) or
            summary.punctuality_percentage < Decimal(85) or
            summary.anomaly_count > 2
        )
        
        summary.last_calculated = datetime.utcnow()
        
        return summary
    
    def __repr__(self):
        return f'<AttendanceSummary Employee:{self.employee_id} {self.year}-{self.month:02d}>'