"""
Sakina Gas Company - Performance Review Model
Built from scratch with comprehensive performance management system
Version 3.0 - Enterprise grade with full complexity
"""

from database import db
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON, Date, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, date, timedelta
from decimal import Decimal

class PerformanceReview(db.Model):
    """
    Comprehensive Performance Review model with advanced evaluation features
    """
    __tablename__ = 'performance_reviews'
    
    # Primary identification
    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey('employees.id'), nullable=False, index=True)
    review_number = Column(String(20), unique=True, nullable=False, index=True)
    
    # Review period and timing
    review_type = Column(String(30), nullable=False, index=True)  # annual, probation, mid_year, quarterly, project_based
    review_period_start = Column(Date, nullable=False)
    review_period_end = Column(Date, nullable=False)
    review_date = Column(Date, nullable=False, index=True)
    due_date = Column(Date, nullable=True)
    
    # Review status and workflow
    status = Column(String(20), nullable=False, default='draft', index=True)  # draft, in_progress, completed, approved, rejected
    completion_percentage = Column(Integer, nullable=False, default=0)  # 0-100
    
    # Reviewers and participants
    reviewer_id = Column(Integer, ForeignKey('users.id'), nullable=False)  # Primary reviewer (usually manager)
    secondary_reviewer_id = Column(Integer, ForeignKey('users.id'), nullable=True)  # Secondary reviewer
    hr_reviewer_id = Column(Integer, ForeignKey('users.id'), nullable=True)  # HR reviewer
    self_review_completed = Column(Boolean, nullable=False, default=False)
    
    # Overall ratings
    overall_rating = Column(Numeric(3, 2), nullable=True)  # 1.00 to 5.00
    overall_rating_scale = Column(String(20), nullable=False, default='1-5')  # 1-5, 1-10, percentage
    previous_rating = Column(Numeric(3, 2), nullable=True)  # For comparison
    
    # Core competency ratings (stored as JSON)
    core_competencies = Column(JSON, nullable=True)  # Array of competency assessments
    technical_skills = Column(JSON, nullable=True)  # Technical skill assessments
    soft_skills = Column(JSON, nullable=True)  # Soft skill assessments
    leadership_skills = Column(JSON, nullable=True)  # Leadership assessments (if applicable)
    
    # Goal setting and achievement
    previous_goals = Column(JSON, nullable=True)  # Goals from previous review
    goal_achievement_score = Column(Numeric(5, 2), nullable=True)  # Percentage of goals achieved
    new_goals = Column(JSON, nullable=True)  # Goals for next period
    
    # Key Performance Indicators (KPIs)
    kpi_scores = Column(JSON, nullable=True)  # Individual KPI assessments
    kpi_overall_score = Column(Numeric(5, 2), nullable=True)  # Overall KPI performance
    
    # Attendance and punctuality metrics
    attendance_score = Column(Numeric(5, 2), nullable=True)  # Based on attendance data
    punctuality_score = Column(Numeric(5, 2), nullable=True)  # Based on punctuality data
    
    # Qualitative assessments
    strengths = Column(Text, nullable=True)
    areas_for_improvement = Column(Text, nullable=True)
    achievements = Column(Text, nullable=True)
    challenges_faced = Column(Text, nullable=True)
    
    # Development and career planning
    development_needs = Column(JSON, nullable=True)  # Training/development requirements
    career_aspirations = Column(Text, nullable=True)
    recommended_training = Column(JSON, nullable=True)  # Training recommendations
    mentoring_needs = Column(Text, nullable=True)
    
    # Manager feedback and employee response
    manager_comments = Column(Text, nullable=True)
    employee_comments = Column(Text, nullable=True)  # Employee's response/self-assessment
    hr_comments = Column(Text, nullable=True)
    
    # Performance improvement plan
    requires_pip = Column(Boolean, nullable=False, default=False)  # Performance Improvement Plan
    pip_details = Column(JSON, nullable=True)  # PIP specifics if required
    pip_start_date = Column(Date, nullable=True)
    pip_end_date = Column(Date, nullable=True)
    
    # Recognition and rewards
    recognition_received = Column(JSON, nullable=True)  # Recognition during review period
    recommended_for_promotion = Column(Boolean, nullable=False, default=False)
    recommended_for_raise = Column(Boolean, nullable=False, default=False)
    recommended_salary_increase = Column(Numeric(5, 2), nullable=True)  # Percentage increase
    
    # Meeting and discussion details
    review_meetings = Column(JSON, nullable=True)  # Meeting history and notes
    total_review_time_hours = Column(Numeric(4, 2), nullable=True)  # Time spent on review
    
    # Signatures and approvals
    employee_acknowledged = Column(Boolean, nullable=False, default=False)
    employee_acknowledgment_date = Column(DateTime, nullable=True)
    manager_approved = Column(Boolean, nullable=False, default=False)
    manager_approval_date = Column(DateTime, nullable=True)
    hr_approved = Column(Boolean, nullable=False, default=False)
    hr_approval_date = Column(DateTime, nullable=True)
    
    # Digital signatures
    employee_signature = Column(Text, nullable=True)  # Digital signature or acknowledgment
    manager_signature = Column(Text, nullable=True)
    hr_signature = Column(Text, nullable=True)
    
    # Follow-up and monitoring
    follow_up_required = Column(Boolean, nullable=False, default=False)
    follow_up_date = Column(Date, nullable=True)
    follow_up_completed = Column(Boolean, nullable=False, default=False)
    next_review_date = Column(Date, nullable=True)
    
    # System metadata
    created_date = Column(DateTime, nullable=False, default=func.current_timestamp())
    created_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    last_updated = Column(DateTime, nullable=False, default=func.current_timestamp(), onupdate=func.current_timestamp())
    updated_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    
    # Flexible data storage
    review_metadata = Column(JSON, nullable=True) # FIX: Renamed from 'metadata'
    attachments = Column(JSON, nullable=True)  # Supporting documents
    
    # Data retention and compliance
    is_confidential = Column(Boolean, nullable=False, default=True)
    retention_period_years = Column(Integer, nullable=False, default=7)  # Legal retention
    can_be_shared_with_employee = Column(Boolean, nullable=False, default=True)
    
    # Performance metrics calculation
    calculated_metrics = Column(JSON, nullable=True)  # Auto-calculated performance data
    metrics_last_calculated = Column(DateTime, nullable=True)
    
    # Relationships
    # All relationships use string literals - safe from direct circular imports
    reviewer = relationship('User', foreign_keys=[reviewer_id], backref='reviews_conducted')
    secondary_reviewer = relationship('User', foreign_keys=[secondary_reviewer_id])
    hr_reviewer = relationship('User', foreign_keys=[hr_reviewer_id])
    creator = relationship('User', foreign_keys=[created_by])
    updater = relationship('User', foreign_keys=[updated_by])
    
    # Indexes
    __table_args__ = (
        db.Index('idx_employee_review_date', 'employee_id', 'review_date'),
        db.Index('idx_review_type_status', 'review_type', 'status'),
        db.Index('idx_reviewer_date', 'reviewer_id', 'review_date'),
    )
    
    def __init__(self, **kwargs):
        """Initialize performance review with defaults"""
        super(PerformanceReview, self).__init__()
        
        # Set default structures
        self.core_competencies = []
        self.technical_skills = []
        self.soft_skills = []
        self.leadership_skills = []
        self.previous_goals = []
        self.new_goals = []
        self.kpi_scores = []
        self.development_needs = []
        self.recommended_training = []
        self.recognition_received = []
        self.review_meetings = []
        self.review_metadata = {} # FIX: Renamed from self.metadata
        self.attachments = []
        self.pip_details = {}
        self.calculated_metrics = {}
        
        # Set creation timestamp
        self.created_date = datetime.utcnow()
        
        # Apply any provided kwargs
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        
        # Generate review number if not provided
        if not self.review_number:
            self.review_number = self.generate_review_number()
        
        # Set next review date if not provided
        if not self.next_review_date and self.review_type == 'annual' and self.review_date: # FIX: Check self.review_date
            self.next_review_date = self.review_date + timedelta(days=365)
        elif not self.next_review_date and self.review_type == 'probation' and self.review_date: # FIX: Check self.review_date
            self.next_review_date = self.review_date + timedelta(days=30)
    
    def generate_review_number(self):
        """Generate unique review number"""
        year = datetime.now().year
        
        # Count existing reviews this year for this employee
        year_start = date(year, 1, 1)
        year_end = date(year, 12, 31)
        
        # NOTE: Using PerformanceReview.query is safe within the class body
        count = PerformanceReview.query.filter(
            PerformanceReview.employee_id == self.employee_id,
            PerformanceReview.review_date.between(year_start, year_end)
        ).count()
        
        # NOTE: self.employee_id is foreign key to employees.id, but the review number uses it as part of the ID, we assume it's the external ID
        # As self.employee_id is a Column(Integer), we must ensure self.employee_id is the integer ID here.
        # However, to preserve the logic, we assume the integer ID is the one used in the review number generation.
        return f"PR{year}{self.employee_id:04d}{count + 1:02d}"
    
    def calculate_overall_rating(self):
        """Calculate overall rating from component scores"""
        total_score = 0
        total_weight = 0
        
        # Core competencies (30% weight)
        if self.core_competencies:
            comp_avg = sum(comp.get('score', 0) for comp in self.core_competencies) / len(self.core_competencies)
            total_score += comp_avg * 0.3
            total_weight += 0.3
        
        # Technical skills (25% weight)
        if self.technical_skills:
            tech_avg = sum(skill.get('score', 0) for skill in self.technical_skills) / len(self.technical_skills)
            total_score += tech_avg * 0.25
            total_weight += 0.25
        
        # KPI performance (25% weight)
        if self.kpi_overall_score:
            total_score += float(self.kpi_overall_score) * 0.25
            total_weight += 0.25
        
        # Goal achievement (20% weight)
        if self.goal_achievement_score:
            total_score += float(self.goal_achievement_score) / 100 * 5 * 0.2  # Convert percentage to 1-5 scale
            total_weight += 0.2
        
        if total_weight > 0:
            # Scale result back to 1-5 if components are rated 1-5
            final_rating = total_score / total_weight
            self.overall_rating = Decimal(str(round(final_rating, 2)))
        
        return self.overall_rating
    
    def calculate_performance_metrics(self):
        """Calculate comprehensive performance metrics"""
        from models.attendance import AttendanceRecord # Local import
        
        metrics = {}
        
        # Get attendance data for review period
        attendance_records = AttendanceRecord.query.filter(
            AttendanceRecord.employee_id == self.employee_id,
            AttendanceRecord.date.between(self.review_period_start, self.review_period_end)
        ).all()
        
        if attendance_records:
            # Attendance metrics
            total_days = len(attendance_records)
            present_days = sum(1 for r in attendance_records if r.status in ['present', 'late'])
            late_days = sum(1 for r in attendance_records if r.status == 'late')
            
            attendance_rate = (present_days / total_days * 100) if total_days > 0 else 0
            # Punctuality rate is on-time arrivals / (on-time + late)
            punctuality_rate = ((present_days - late_days) / present_days * 100) if present_days > 0 else 0
            
            self.attendance_score = Decimal(str(round(attendance_rate, 2)))
            self.punctuality_score = Decimal(str(round(punctuality_rate, 2)))
            
            metrics['attendance'] = {
                'total_days': total_days,
                'present_days': present_days,
                'late_days': late_days,
                'attendance_rate': attendance_rate,
                'punctuality_rate': punctuality_rate
            }
        
        # Goal achievement calculation
        if self.previous_goals:
            achieved_goals = sum(1 for goal in self.previous_goals if goal.get('status') == 'achieved')
            total_goals = len(self.previous_goals)
            achievement_percentage = (achieved_goals / total_goals * 100) if total_goals > 0 else 0
            self.goal_achievement_score = Decimal(str(round(achievement_percentage, 2)))
            
            metrics['goals'] = {
                'total_goals': total_goals,
                'achieved_goals': achieved_goals,
                'achievement_percentage': achievement_percentage
            }
        
        self.calculated_metrics = metrics
        self.metrics_last_calculated = datetime.utcnow()
        
        return metrics
    
    def add_competency_assessment(self, competency_name, score, comments=None, weight=1.0):
        """Add a core competency assessment"""
        if self.core_competencies is None:
            self.core_competencies = []
        
        assessment = {
            'competency': competency_name,
            'score': score,
            'comments': comments,
            'weight': weight,
            'assessed_date': datetime.utcnow().isoformat()
        }
        
        # Update existing or add new
        for i, comp in enumerate(self.core_competencies):
            if comp.get('competency') == competency_name:
                self.core_competencies[i] = assessment
                return
        
        self.core_competencies.append(assessment)
    
    def add_goal(self, goal_title, description, target_date, weight=1.0, category='performance'):
        """Add a goal for the next review period"""
        if self.new_goals is None:
            self.new_goals = []
        
        goal = {
            'title': goal_title,
            'description': description,
            'target_date': target_date.isoformat() if isinstance(target_date, date) else target_date,
            'weight': weight,
            'category': category,
            'status': 'pending',
            'created_date': datetime.utcnow().isoformat()
        }
        
        self.new_goals.append(goal)
    
    def update_goal_status(self, goal_title, status, achievement_percentage=None, notes=None):
        """Update status of an existing goal"""
        if self.previous_goals:
            for goal in self.previous_goals:
                if goal.get('title') == goal_title:
                    goal['status'] = status
                    if achievement_percentage is not None:
                        goal['achievement_percentage'] = achievement_percentage
                    if notes:
                        goal['notes'] = notes
                    goal['updated_date'] = datetime.utcnow().isoformat()
                    break
    
    def add_kpi_score(self, kpi_name, target_value, actual_value, score, unit=None):
        """Add KPI performance score"""
        if self.kpi_scores is None:
            self.kpi_scores = []
        
        kpi = {
            'kpi_name': kpi_name,
            'target_value': target_value,
            'actual_value': actual_value,
            'score': score,
            'unit': unit,
            'achievement_percentage': (actual_value / target_value * 100) if target_value > 0 else 0,
            'assessed_date': datetime.utcnow().isoformat()
        }
        
        # Update existing or add new
        for i, existing_kpi in enumerate(self.kpi_scores):
            if existing_kpi.get('kpi_name') == kpi_name:
                self.kpi_scores[i] = kpi
                return
        
        self.kpi_scores.append(kpi)
        
        # Recalculate overall KPI score
        if self.kpi_scores:
            avg_score = sum(k.get('score', 0) for k in self.kpi_scores) / len(self.kpi_scores)
            self.kpi_overall_score = Decimal(str(round(avg_score, 2)))
    
    def add_development_need(self, area, priority, suggested_action, timeline=None):
        """Add development need or training requirement"""
        if self.development_needs is None:
            self.development_needs = []
        
        need = {
            'area': area,
            'priority': priority,  # high, medium, low
            'suggested_action': suggested_action,
            'timeline': timeline,
            'identified_date': datetime.utcnow().isoformat()
        }
        
        self.development_needs.append(need)
    
    def add_training_recommendation(self, training_name, provider, duration, cost=None, priority='medium'):
        """Add training recommendation"""
        if self.recommended_training is None:
            self.recommended_training = []
        
        training = {
            'training_name': training_name,
            'provider': provider,
            'duration': duration,
            'cost': cost,
            'priority': priority,
            'recommended_date': datetime.utcnow().isoformat()
        }
        
        self.recommended_training.append(training)
    
    def create_performance_improvement_plan(self, areas_for_improvement, specific_goals, timeline_days=90):
        """Create a Performance Improvement Plan"""
        self.requires_pip = True
        self.pip_start_date = date.today()
        self.pip_end_date = date.today() + timedelta(days=timeline_days)
        
        self.pip_details = {
            'areas_for_improvement': areas_for_improvement,
            'specific_goals': specific_goals,
            'timeline_days': timeline_days,
            'review_checkpoints': [
                (self.pip_start_date + timedelta(days=30)).isoformat(),
                (self.pip_start_date + timedelta(days=60)).isoformat(),
                self.pip_end_date.isoformat()
            ],
            'created_date': datetime.utcnow().isoformat(),
            'status': 'active'
        }
    
    def acknowledge_by_employee(self, employee_comments=None, signature=None):
        """Employee acknowledges the review"""
        self.employee_acknowledged = True
        self.employee_acknowledgment_date = datetime.utcnow()
        
        if employee_comments:
            self.employee_comments = employee_comments
        
        if signature:
            self.employee_signature = signature
    
    def approve_by_manager(self, manager_comments=None, signature=None):
        """Manager approves the review"""
        self.manager_approved = True
        self.manager_approval_date = datetime.utcnow()
        
        if manager_comments:
            self.manager_comments = manager_comments
        
        if signature:
            self.manager_signature = signature
        
        # Check if ready for completion
        if self.employee_acknowledged and not self.hr_approved:
            self.status = 'pending_hr_approval'
        elif self.employee_acknowledged and self.hr_approved:
            self.status = 'completed'
    
    def approve_by_hr(self, hr_comments=None, signature=None):
        """HR approves the review"""
        self.hr_approved = True
        self.hr_approval_date = datetime.utcnow()
        
        if hr_comments:
            self.hr_comments = hr_comments
        
        if signature:
            self.hr_signature = signature
        
        # Check if ready for completion
        if self.employee_acknowledged and self.manager_approved:
            self.status = 'completed'
    
    def get_review_type_display(self):
        """Get human-readable review type"""
        type_map = {
            'annual': 'Annual Review',
            'probation': 'Probation Review',
            'mid_year': 'Mid-Year Review',
            'quarterly': 'Quarterly Review',
            'project_based': 'Project-Based Review',
            'promotion': 'Promotion Review',
            'pip': 'Performance Improvement Review'
        }
        return type_map.get(self.review_type, self.review_type.replace('_', ' ').title())
    
    def get_status_display(self):
        """Get human-readable status"""
        status_map = {
            'draft': 'Draft',
            'in_progress': 'In Progress',
            'completed': 'Completed',
            'approved': 'Approved',
            'rejected': 'Rejected',
            'pending_hr_approval': 'Pending HR Approval'
        }
        return status_map.get(self.status, self.status.replace('_', ' ').title())
    
    def get_overall_rating_display(self):
        """Get formatted overall rating"""
        if self.overall_rating:
            return f"{float(self.overall_rating):.2f} / 5.00"
        return "Not Rated"
    
    def get_performance_level(self):
        """Get performance level based on overall rating"""
        if not self.overall_rating:
            return 'Not Rated'
        
        rating = float(self.overall_rating)
        if rating >= 4.5:
            return 'Exceptional'
        elif rating >= 3.5:
            return 'Exceeds Expectations'
        elif rating >= 2.5:
            return 'Meets Expectations'
        elif rating >= 1.5:
            return 'Below Expectations'
        else:
            return 'Unsatisfactory'
    
    def get_performance_color(self):
        """Get color code for performance level"""
        level = self.get_performance_level()
        color_map = {
            'Exceptional': '#28A745',      # Green
            'Exceeds Expectations': '#20C997', # Teal
            'Meets Expectations': '#007BFF',   # Blue
            'Below Expectations': '#FFC107',   # Yellow
            'Unsatisfactory': '#DC3545',      # Red
            'Not Rated': '#6C757D'            # Gray
        }
        return color_map.get(level, '#6C757D')
    
    def is_overdue(self):
        """Check if review is overdue"""
        return self.due_date and date.today() > self.due_date and self.status not in ['completed', 'approved', 'rejected']
    
    def days_until_due(self):
        """Get days until review is due"""
        if self.due_date:
            delta = self.due_date - date.today()
            return delta.days
        return None
    
    def calculate_completion_percentage(self):
        """Calculate review completion percentage"""
        total_sections = 8  # Adjust based on required sections
        completed_sections = 0
        
        # Check completed sections
        if self.overall_rating:
            completed_sections += 1
        if self.core_competencies and len(self.core_competencies) > 0: # FIX: Check list length
            completed_sections += 1
        if self.achievements:
            completed_sections += 1
        if self.areas_for_improvement:
            completed_sections += 1
        if self.new_goals and len(self.new_goals) > 0: # FIX: Check list length
            completed_sections += 1
        if self.manager_comments:
            completed_sections += 1
        if self.employee_acknowledged:
            completed_sections += 1
        if self.manager_approved:
            completed_sections += 1
        
        self.completion_percentage = int((completed_sections / total_sections) * 100)
        return self.completion_percentage
    
    def to_dict(self, include_sensitive=False):
        """Convert performance review to dictionary"""
        data = {
            'id': self.id,
            'employee_id': self.employee_id,
            'review_number': self.review_number,
            'review_type': self.review_type,
            'review_type_display': self.get_review_type_display(),
            'review_date': self.review_date.isoformat(),
            'status': self.status,
            'status_display': self.get_status_display(),
            'overall_rating': float(self.overall_rating) if self.overall_rating else None,
            'overall_rating_display': self.get_overall_rating_display(),
            'performance_level': self.get_performance_level(),
            'performance_color': self.get_performance_color(),
            'completion_percentage': self.calculate_completion_percentage(), # FIX: Call method to update
            'is_overdue': self.is_overdue(),
            'days_until_due': self.days_until_due()
        }
        
        if include_sensitive:
            data.update({
                'strengths': self.strengths,
                'areas_for_improvement': self.areas_for_improvement,
                'achievements': self.achievements,
                'manager_comments': self.manager_comments,
                'employee_comments': self.employee_comments,
                'core_competencies': self.core_competencies,
                'technical_skills': self.technical_skills,
                'new_goals': self.new_goals,
                'kpi_scores': self.kpi_scores,
                'development_needs': self.development_needs,
                'requires_pip': self.requires_pip,
                'pip_details': self.pip_details,
                'calculated_metrics': self.calculated_metrics
            })
        
        return data
    
    @classmethod
    def create_annual_review(cls, employee_id, reviewer_id, review_year=None):
        """Create annual performance review"""
        if review_year is None:
            review_year = date.today().year
        
        review = cls(
            employee_id=employee_id,
            reviewer_id=reviewer_id,
            review_type='annual',
            review_period_start=date(review_year - 1, 1, 1),
            review_period_end=date(review_year - 1, 12, 31),
            review_date=date.today(),
            due_date=date.today() + timedelta(days=30),
            status='draft'
        )
        
        return review
    
    @classmethod
    def create_probation_review(cls, employee_id, reviewer_id, probation_end_date):
        """Create probation review"""
        review = cls(
            employee_id=employee_id,
            reviewer_id=reviewer_id,
            review_type='probation',
            review_period_start=probation_end_date - timedelta(days=90),
            review_period_end=probation_end_date,
            review_date=date.today(),
            due_date=probation_end_date - timedelta(days=7),  # Review 1 week before probation ends
            status='draft'
        )
        
        return review
    
    @classmethod
    def get_overdue_reviews(cls):
        """Get all overdue performance reviews"""
        return cls.query.filter(
            cls.due_date < date.today(),
            cls.status.in_(['draft', 'in_progress'])
        ).all()
    
    @classmethod
    def get_upcoming_reviews(cls, days_ahead=30):
        """Get reviews due within specified days"""
        cutoff_date = date.today() + timedelta(days=days_ahead)
        return cls.query.filter(
            cls.due_date <= cutoff_date,
            cls.status.in_(['draft', 'in_progress'])
        ).order_by(cls.due_date).all()
    
    @classmethod
    def get_employee_reviews(cls, employee_id, limit=10):
        """Get performance reviews for an employee"""
        return cls.query.filter(
            cls.employee_id == employee_id
        ).order_by(cls.review_date.desc()).limit(limit).all()
    
    def __repr__(self):
        # FIX: Ensure safe access to employee.get_full_name()
        employee_name = self.employee.get_full_name() if self.employee and hasattr(self.employee, 'get_full_name') else str(self.employee_id)
        return f'<PerformanceReview {self.review_number}: {employee_name} - {self.review_type}>'