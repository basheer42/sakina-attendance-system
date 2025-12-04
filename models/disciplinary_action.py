"""
Sakina Gas Company - Disciplinary Action Model
Built from scratch with comprehensive disciplinary management system
Version 3.0 - Enterprise grade with full complexity and legal compliance
"""

from database import db
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON, Date, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, date, timedelta

class DisciplinaryAction(db.Model):
    """
    Comprehensive Disciplinary Action model with legal compliance and progressive discipline
    """
    __tablename__ = 'disciplinary_actions'
    
    # Primary identification
    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey('employees.id'), nullable=False, index=True)
    case_number = Column(String(20), unique=True, nullable=False, index=True)
    
    # Incident details
    incident_date = Column(DateTime, nullable=False, index=True)
    incident_location = Column(String(100), nullable=True)
    incident_description = Column(Text, nullable=False)
    incident_category = Column(String(50), nullable=False, index=True)  # misconduct, performance, attendance, policy_violation, etc.
    
    # Action classification
    action_type = Column(String(30), nullable=False, index=True)  # verbal_warning, written_warning, final_warning, suspension, termination
    severity_level = Column(String(20), nullable=False, index=True)  # minor, moderate, severe, critical
    
    # Progressive discipline tracking
    is_first_offense = Column(Boolean, nullable=False, default=True)
    previous_action_id = Column(Integer, ForeignKey('disciplinary_actions.id'), nullable=True)
    escalation_level = Column(Integer, nullable=False, default=1)  # 1st, 2nd, 3rd offense level
    
    # Action details
    action_description = Column(Text, nullable=False)
    action_reason = Column(Text, nullable=False)
    corrective_measures = Column(Text, nullable=True)
    expected_behavior_change = Column(Text, nullable=True)
    
    # Timing and duration
    action_date = Column(DateTime, nullable=False, default=func.current_timestamp())
    effective_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)  # For suspensions or probation periods
    review_date = Column(Date, nullable=True)  # When to review progress
    
    # Status tracking
    status = Column(String(20), nullable=False, default='active', index=True)  # active, completed, appealed, overturned, expired
    
    # Investigation details
    investigation_required = Column(Boolean, nullable=False, default=False)
    investigation_completed = Column(Boolean, nullable=False, default=False)
    investigation_start_date = Column(Date, nullable=True)
    investigation_end_date = Column(Date, nullable=True)
    investigation_summary = Column(Text, nullable=True)
    
    # Witnesses and evidence
    witnesses = Column(JSON, nullable=True)  # List of witness information
    evidence_collected = Column(JSON, nullable=True)  # Evidence documentation
    evidence_files = Column(Text, nullable=True)  # File paths/references
    
    # People involved
    reported_by = Column(Integer, ForeignKey('users.id'), nullable=True)  # Who reported the incident
    investigated_by = Column(Integer, ForeignKey('users.id'), nullable=True)  # Investigator
    action_taken_by = Column(Integer, ForeignKey('users.id'), nullable=False)  # Manager/HR who took action
    hr_approved_by = Column(Integer, ForeignKey('users.id'), nullable=True)  # HR approval
    
    # Employee response and acknowledgment
    employee_statement = Column(Text, nullable=True)
    employee_acknowledged = Column(Boolean, nullable=False, default=False)
    employee_acknowledgment_date = Column(DateTime, nullable=True)
    employee_signature = Column(Text, nullable=True)  # Digital signature
    
    # Union and representation
    union_representative_present = Column(Boolean, nullable=False, default=False)
    union_representative_name = Column(String(100), nullable=True)
    employee_represented = Column(Boolean, nullable=False, default=False)
    representative_name = Column(String(100), nullable=True)
    
    # Appeal process
    appeal_allowed = Column(Boolean, nullable=False, default=True)
    appeal_filed = Column(Boolean, nullable=False, default=False)
    appeal_date = Column(DateTime, nullable=True)
    appeal_reason = Column(Text, nullable=True)
    appeal_outcome = Column(String(30), nullable=True)  # upheld, overturned, modified
    appeal_decision_date = Column(DateTime, nullable=True)
    appeal_decided_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    
    # Financial impact
    has_financial_penalty = Column(Boolean, nullable=False, default=False)
    penalty_amount = Column(Numeric(10, 2), nullable=True)
    penalty_currency = Column(String(5), nullable=False, default='KES')
    pay_deduction_authorized = Column(Boolean, nullable=False, default=False)
    
    # Suspension details (if applicable)
    is_suspension = Column(Boolean, nullable=False, default=False)
    suspension_days = Column(Integer, nullable=True)
    is_paid_suspension = Column(Boolean, nullable=False, default=False)
    return_to_work_conditions = Column(Text, nullable=True)
    
    # Training and development requirements
    training_required = Column(Boolean, nullable=False, default=False)
    required_training = Column(JSON, nullable=True)  # List of required training programs
    training_deadline = Column(Date, nullable=True)
    training_completed = Column(Boolean, nullable=False, default=False)
    training_completion_date = Column(Date, nullable=True)
    
    # Performance monitoring
    monitoring_period_months = Column(Integer, nullable=True)  # Period for enhanced monitoring
    monitoring_requirements = Column(Text, nullable=True)
    monitoring_completed = Column(Boolean, nullable=False, default=False)
    performance_improved = Column(Boolean, nullable=True)
    
    # Follow-up actions
    follow_up_required = Column(Boolean, nullable=False, default=False)
    follow_up_date = Column(Date, nullable=True)
    follow_up_completed = Column(Boolean, nullable=False, default=False)
    follow_up_notes = Column(Text, nullable=True)
    
    # Legal and compliance
    legal_review_required = Column(Boolean, nullable=False, default=False)
    legal_review_completed = Column(Boolean, nullable=False, default=False)
    legal_advisor = Column(String(100), nullable=True)
    legal_opinion = Column(Text, nullable=True)
    
    # Documentation and communication
    documentation_complete = Column(Boolean, nullable=False, default=False)
    employee_notified = Column(Boolean, nullable=False, default=False)
    notification_date = Column(DateTime, nullable=True)
    notification_method = Column(String(30), nullable=True)  # email, letter, verbal, meeting
    
    # Policy references
    policy_violated = Column(JSON, nullable=True)  # List of violated policies
    policy_sections = Column(JSON, nullable=True)  # Specific policy section references
    legal_violations = Column(JSON, nullable=True)  # Any legal violations
    
    # Impact assessment
    business_impact = Column(Text, nullable=True)
    safety_implications = Column(Text, nullable=True)
    customer_impact = Column(Text, nullable=True)
    team_impact = Column(Text, nullable=True)
    
    # System metadata
    created_date = Column(DateTime, nullable=False, default=func.current_timestamp())
    created_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    last_updated = Column(DateTime, nullable=False, default=func.current_timestamp(), onupdate=func.current_timestamp())
    updated_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    
    # Data retention and confidentiality
    is_confidential = Column(Boolean, nullable=False, default=True)
    retention_period_years = Column(Integer, nullable=False, default=7)  # Legal retention requirement
    can_affect_references = Column(Boolean, nullable=False, default=True)
    
    # Flexible data storage
    action_metadata = Column(JSON, nullable=True) # FIX: Renamed from 'metadata'
    custom_fields = Column(JSON, nullable=True)  # Additional company-specific fields
    
    # Relationships
    # FIX: Use string literal for self-referential relationship
    previous_action = relationship('DisciplinaryAction', remote_side=[id], backref='subsequent_actions')
    # All relationships use string literals - safe from direct circular imports
    reporter = relationship('User', foreign_keys=[reported_by], backref='reported_incidents')
    investigator = relationship('User', foreign_keys=[investigated_by], backref='investigated_cases')
    action_taker = relationship('User', foreign_keys=[action_taken_by], backref='disciplinary_actions_taken')
    hr_approver = relationship('User', foreign_keys=[hr_approved_by])
    appeal_decider = relationship('User', foreign_keys=[appeal_decided_by])
    creator = relationship('User', foreign_keys=[created_by])
    updater = relationship('User', foreign_keys=[updated_by])
    
    # Indexes
    __table_args__ = (
        db.Index('idx_employee_incident_date', 'employee_id', 'incident_date'),
        db.Index('idx_action_type_date', 'action_type', 'action_date'),
        db.Index('idx_severity_status', 'severity_level', 'status'),
        db.Index('idx_case_number', 'case_number'),
    )
    
    def __init__(self, **kwargs):
        """Initialize disciplinary action with defaults"""
        super(DisciplinaryAction, self).__init__()
        
        # Set default structures
        self.witnesses = []
        self.evidence_collected = []
        self.policy_violated = []
        self.policy_sections = []
        self.legal_violations = []
        self.required_training = []
        self.action_metadata = {} # FIX: Renamed from self.metadata
        self.custom_fields = {}
        
        # Set creation timestamp
        self.created_date = datetime.utcnow()
        
        # Apply any provided kwargs
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        
        # Generate case number if not provided
        if not self.case_number:
            self.case_number = self.generate_case_number()
        
        # Set automatic fields based on action type
        self._set_action_defaults()
    
    def generate_case_number(self):
        """Generate unique case number"""
        year = datetime.now().year
        
        # Count existing cases this year
        year_start = datetime(year, 1, 1)
        year_end = datetime(year, 12, 31, 23, 59, 59)
        
        # FIX: Use direct query on the model
        count = DisciplinaryAction.query.filter(
            DisciplinaryAction.created_date.between(year_start, year_end)
        ).count()
        
        return f"DA{year}{count + 1:04d}"
    
    def _set_action_defaults(self):
        """Set default values based on action type"""
        if self.action_type == 'suspension':
            self.is_suspension = True
        
        # Set default review dates
        if self.action_type == 'written_warning' or self.action_type == 'final_warning':
            self.review_date = date.today() + timedelta(days=90)
        elif self.action_type == 'verbal_warning':
            self.review_date = date.today() + timedelta(days=30)
        
        # Set monitoring periods
        if self.action_type == 'final_warning':
            self.monitoring_period_months = 6
            self.follow_up_required = True
            self.follow_up_date = date.today() + timedelta(days=30)
    
    @classmethod
    def determine_progressive_discipline_level(cls, employee_id, severity_level='moderate'):
        """Determine appropriate discipline level based on history"""
        from models.employee import Employee
        
        # Get previous disciplinary actions for this employee
        previous_actions = cls.query.filter(
            cls.employee_id == employee_id,
            cls.status.in_(['active', 'completed']), # Include completed actions for history
        ).order_by(cls.action_date.desc()).all()
        
        if not previous_actions:
            return 'verbal_warning'
        
        # Get the most recent action
        last_action = previous_actions[0]
        escalation_level = len(previous_actions) + 1 # Simple level count
        
        # Progressive discipline matrix (Simplified)
        if severity_level == 'critical':
            return 'termination'
        elif severity_level == 'severe':
            if escalation_level >= 3 or last_action.action_type in ['final_warning', 'suspension']:
                return 'termination'
            else:
                return 'final_warning'
        elif severity_level == 'moderate':
            if escalation_level == 1:
                return 'verbal_warning'
            elif escalation_level == 2:
                return 'written_warning'
            else:
                return 'final_warning'
        else:  # minor
            if escalation_level <= 2:
                return 'verbal_warning'
            else:
                return 'written_warning'
    
    def add_witness(self, name, contact, statement, role=None):
        """Add witness information"""
        if self.witnesses is None:
            self.witnesses = []
        
        witness = {
            'name': name,
            'contact': contact,
            'statement': statement,
            'role': role,
            'date_interviewed': datetime.utcnow().isoformat()
        }
        
        self.witnesses.append(witness)
    
    def add_evidence(self, evidence_type, description, file_path=None, collected_by=None):
        """Add evidence to the case"""
        if self.evidence_collected is None:
            self.evidence_collected = []
        
        evidence = {
            'type': evidence_type,  # document, photo, video, audio, physical
            'description': description,
            'file_path': file_path,
            'collected_by': collected_by,
            'collection_date': datetime.utcnow().isoformat()
        }
        
        self.evidence_collected.append(evidence)
    
    def add_policy_violation(self, policy_name, section, description):
        """Add violated policy reference"""
        if self.policy_violated is None:
            self.policy_violated = []
        
        violation = {
            'policy_name': policy_name,
            'section': section,
            'description': description
        }
        
        self.policy_violated.append(violation)
    
    def require_training(self, training_name, provider, deadline_days=30, is_mandatory=True):
        """Add required training"""
        if self.required_training is None:
            self.required_training = []
        
        training = {
            'training_name': training_name,
            'provider': provider,
            'deadline': (date.today() + timedelta(days=deadline_days)).isoformat(),
            'is_mandatory': is_mandatory,
            'assigned_date': date.today().isoformat(),
            'status': 'assigned'
        }
        
        self.required_training.append(training)
        self.training_required = True
        self.training_deadline = date.today() + timedelta(days=deadline_days)
    
    def complete_investigation(self, investigator_id, summary, evidence_sufficient=True):
        """Complete the investigation process"""
        self.investigation_completed = True
        self.investigation_end_date = date.today()
        self.investigated_by = investigator_id
        self.investigation_summary = summary
        
        if evidence_sufficient:
            self.status = 'active'
        else:
            self.status = 'insufficient_evidence'
    
    def acknowledge_by_employee(self, statement=None, signature=None):
        """Employee acknowledges the disciplinary action"""
        self.employee_acknowledged = True
        self.employee_acknowledgment_date = datetime.utcnow()
        
        if statement:
            self.employee_statement = statement
        
        if signature:
            self.employee_signature = signature
    
    def file_appeal(self, reason, supporting_evidence=None):
        """File an appeal for this disciplinary action"""
        if not self.can_be_appealed():
            raise ValueError("This action cannot be appealed")
        
        self.appeal_filed = True
        self.appeal_date = datetime.utcnow()
        self.appeal_reason = reason
        
        if supporting_evidence:
            if self.evidence_collected is None:
                self.evidence_collected = []
            
            appeal_evidence = {
                'type': 'appeal_evidence',
                'description': supporting_evidence,
                'submitted_by': 'employee',
                'submission_date': datetime.utcnow().isoformat()
            }
            
            self.evidence_collected.append(appeal_evidence)
        
        # Change status to under appeal review
        self.status = 'under_appeal'
    
    def decide_appeal(self, decision, decided_by_user_id, decision_reason=None):
        """Decide on an appeal"""
        if not self.appeal_filed:
            raise ValueError("No appeal has been filed")
        
        valid_decisions = ['upheld', 'overturned', 'modified']
        if decision not in valid_decisions:
            raise ValueError(f"Invalid decision. Must be one of: {valid_decisions}")
        
        self.appeal_outcome = decision
        self.appeal_decision_date = datetime.utcnow()
        self.appeal_decided_by = decided_by_user_id
        
        if decision_reason:
            if not self.appeal_reason:
                self.appeal_reason = ""
            self.appeal_reason += f"\n\nAppeal Decision: {decision_reason}"
        
        # Update status based on decision
        if decision == 'overturned':
            self.status = 'overturned'
        elif decision == 'modified':
            self.status = 'modified'
        else:  # upheld
            self.status = 'active'
    
    def complete_training_requirement(self, training_name, completion_date=None):
        """Mark required training as completed"""
        if self.required_training:
            for training in self.required_training:
                if training.get('training_name') == training_name:
                    training['status'] = 'completed'
                    training['completion_date'] = (completion_date or date.today()).isoformat()
                    break
        
        # Check if all training is completed
        if self.required_training:
            all_completed = all(
                training.get('status') == 'completed' 
                for training in self.required_training
            )
            if all_completed:
                self.training_completed = True
                self.training_completion_date = completion_date or date.today()
    
    def schedule_follow_up(self, follow_up_date, requirements=None):
        """Schedule follow-up review"""
        self.follow_up_required = True
        self.follow_up_date = follow_up_date
        
        if requirements:
            self.monitoring_requirements = requirements
    
    def complete_follow_up(self, outcome, notes, performance_improved=None):
        """Complete follow-up review"""
        self.follow_up_completed = True
        self.follow_up_notes = notes
        
        if performance_improved is not None:
            self.performance_improved = performance_improved
            
            # If performance improved and monitoring period is over, mark as completed
            if performance_improved and self.is_monitoring_period_over():
                self.status = 'completed'
    
    def is_monitoring_period_over(self):
        """Check if monitoring period has ended"""
        if not self.monitoring_period_months:
            return True
        
        monitoring_end = self.action_date.date() + timedelta(days=self.monitoring_period_months * 30)
        return date.today() > monitoring_end
    
    def can_be_appealed(self):
        """Check if this action can be appealed"""
        # Can't appeal if already appealed
        if self.appeal_filed:
            return False
        
        # Can't appeal verbal warnings typically
        if self.action_type == 'verbal_warning':
            return False
        
        # Must be within appeal period (usually 7-14 days)
        appeal_deadline = self.action_date + timedelta(days=14)
        if datetime.utcnow() > appeal_deadline:
            return False
        
        return self.appeal_allowed
    
    @property
    def is_active(self):
        """Check if disciplinary action is currently active"""
        if self.status != 'active':
            return False
        
        if self.end_date:
            return datetime.now().date() <= self.end_date
        
        return True
    
    @property
    def days_remaining(self):
        """Get days remaining for time-bound actions"""
        if self.end_date and self.is_active:
            remaining = (self.end_date - datetime.now().date()).days
            return max(0, remaining)
        return 0
    
    def get_action_type_display(self):
        """Get human-readable action type"""
        type_map = {
            'verbal_warning': 'Verbal Warning',
            'written_warning': 'Written Warning',
            'final_warning': 'Final Written Warning',
            'suspension': 'Suspension',
            'demotion': 'Demotion',
            'termination': 'Termination',
            'counseling': 'Counseling Session',
            'training_requirement': 'Mandatory Training'
        }
        return type_map.get(self.action_type, self.action_type.replace('_', ' ').title())
    
    def get_severity_display(self):
        """Get human-readable severity level"""
        severity_map = {
            'minor': 'Minor',
            'moderate': 'Moderate',
            'severe': 'Severe',
            'critical': 'Critical'
        }
        return severity_map.get(self.severity_level, self.severity_level.title())
    
    def get_status_display(self):
        """Get human-readable status"""
        status_map = {
            'active': 'Active',
            'completed': 'Completed',
            'appealed': 'Under Appeal',
            'overturned': 'Overturned',
            'expired': 'Expired',
            'under_appeal': 'Under Appeal Review',
            'insufficient_evidence': 'Insufficient Evidence',
            'modified': 'Modified'
        }
        return status_map.get(self.status, self.status.replace('_', ' ').title())
    
    def get_severity_color(self):
        """Get color code for severity level"""
        color_map = {
            'minor': '#FFC107',      # Yellow
            'moderate': '#17A2B8',   # Cyan
            'severe': '#FD7E14',     # Orange
            'critical': '#DC3545'    # Red
        }
        return color_map.get(self.severity_level, '#6C757D')
    
    def to_dict(self, include_sensitive=False):
        """Convert disciplinary action to dictionary"""
        data = {
            'id': self.id,
            'employee_id': self.employee_id,
            'case_number': self.case_number,
            'incident_date': self.incident_date.isoformat() if self.incident_date else None,
            'action_type': self.action_type,
            'action_type_display': self.get_action_type_display(),
            'severity_level': self.severity_level,
            'severity_display': self.get_severity_display(),
            'severity_color': self.get_severity_color(),
            'status': self.status,
            'status_display': self.get_status_display(),
            'escalation_level': self.escalation_level,
            'is_first_offense': self.is_first_offense,
            'is_active': self.is_active,
            'days_remaining': self.days_remaining
        }
        
        if include_sensitive:
            data.update({
                'incident_description': self.incident_description,
                'action_description': self.action_description,
                'action_reason': self.action_reason,
                'employee_statement': self.employee_statement,
                'investigation_summary': self.investigation_summary,
                'witnesses': self.witnesses,
                'evidence_collected': self.evidence_collected,
                'policy_violated': self.policy_violated,
                'required_training': self.required_training,
                'appeal_filed': self.appeal_filed,
                'appeal_reason': self.appeal_reason,
                'appeal_outcome': self.appeal_outcome,
                'follow_up_notes': self.follow_up_notes
            })
        
        return data
    
    @classmethod
    def get_employee_disciplinary_history(cls, employee_id):
        """Get disciplinary history for an employee"""
        return cls.query.filter(
            cls.employee_id == employee_id
        ).order_by(cls.action_date.desc()).all()
    
    @classmethod
    def get_pending_investigations(cls):
        """Get cases requiring investigation"""
        return cls.query.filter(
            cls.investigation_required == True,
            cls.investigation_completed == False
        ).all()
    
    @classmethod
    def get_pending_appeals(cls):
        """Get cases with pending appeals"""
        return cls.query.filter(
            cls.appeal_filed == True,
            cls.appeal_outcome.is_(None)
        ).all()
    
    @classmethod
    def create_disciplinary_action(cls, employee_id, incident_description, 
                                  incident_category, action_taken_by, **kwargs):
        """Create new disciplinary action"""
        action = cls(
            employee_id=employee_id,
            incident_date=datetime.utcnow(),
            incident_description=incident_description,
            incident_category=incident_category,
            action_taken_by=action_taken_by,
            **kwargs
        )
        
        # Auto-determine progressive discipline if not specified
        if 'action_type' not in kwargs:
            # NOTE: determine_progressive_discipline_level uses the instance, so we must set action_type back
            suggested_action = cls.determine_progressive_discipline_level(employee_id, action.severity_level) # FIX: Use employee_id for class method
            action.action_type = suggested_action
        
        return action
    
    def __repr__(self):
        # FIX: Ensure safe access to employee.get_full_name()
        employee_name = self.employee.get_full_name() if self.employee and hasattr(self.employee, 'get_full_name') else str(self.employee_id)
        return f'<DisciplinaryAction {self.case_number}: {employee_name} - {self.action_type}>'