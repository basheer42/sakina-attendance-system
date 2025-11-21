"""
Performance Review Model - Employee Performance Tracking
This file contains only the PerformanceReview model
"""

from database import db
from datetime import datetime, date

class PerformanceReview(db.Model):
    """Performance review model for tracking employee performance"""
    
    __tablename__ = 'performance_reviews'
    
    # Primary fields
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False, index=True)
    
    # Review period
    review_period_start = db.Column(db.Date, nullable=False)
    review_period_end = db.Column(db.Date, nullable=False)
    review_type = db.Column(db.String(50), default='annual')  # annual, probation, quarterly
    
    # Performance scores (1-5 scale)
    punctuality_score = db.Column(db.Integer, nullable=True)  # Based on attendance
    productivity_score = db.Column(db.Integer, nullable=True)
    teamwork_score = db.Column(db.Integer, nullable=True)
    communication_score = db.Column(db.Integer, nullable=True)
    initiative_score = db.Column(db.Integer, nullable=True)
    overall_score = db.Column(db.Numeric(3, 2), nullable=True)  # Average score
    
    # Review details
    strengths = db.Column(db.Text, nullable=True)
    areas_for_improvement = db.Column(db.Text, nullable=True)
    goals_achievements = db.Column(db.Text, nullable=True)
    future_goals = db.Column(db.Text, nullable=True)
    training_needs = db.Column(db.Text, nullable=True)
    
    # Reviewer information
    reviewed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    review_date = db.Column(db.Date, default=date.today, nullable=False)
    
    # Employee feedback
    employee_comments = db.Column(db.Text, nullable=True)
    employee_acknowledged = db.Column(db.Boolean, default=False)
    acknowledgment_date = db.Column(db.Date, nullable=True)
    
    # Performance rating
    performance_rating = db.Column(db.String(20), nullable=True)  # excellent, good, satisfactory, needs_improvement, unsatisfactory
    
    # Recommendations
    salary_increase_recommended = db.Column(db.Boolean, default=False)
    promotion_recommended = db.Column(db.Boolean, default=False)
    training_recommended = db.Column(db.Boolean, default=False)
    disciplinary_action_needed = db.Column(db.Boolean, default=False)
    
    # Additional notes
    reviewer_notes = db.Column(db.Text, nullable=True)
    hr_notes = db.Column(db.Text, nullable=True)
    
    # System fields
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Attendance metrics (calculated from attendance records)
    attendance_percentage = db.Column(db.Numeric(5, 2), nullable=True)
    late_incidents = db.Column(db.Integer, default=0)
    absent_days = db.Column(db.Integer, default=0)
    
    # Indexes for better performance
    __table_args__ = (
        db.Index('idx_review_employee_period', 'employee_id', 'review_period_start'),
        db.Index('idx_review_type_date', 'review_type', 'review_date'),
    )
    
    @property
    def review_period_display(self):
        """Get formatted review period"""
        return f"{self.review_period_start.strftime('%b %Y')} - {self.review_period_end.strftime('%b %Y')}"
    
    @property
    def performance_rating_display(self):
        """Get display-friendly performance rating"""
        rating_map = {
            'excellent': 'Excellent',
            'good': 'Good', 
            'satisfactory': 'Satisfactory',
            'needs_improvement': 'Needs Improvement',
            'unsatisfactory': 'Unsatisfactory'
        }
        return rating_map.get(self.performance_rating, self.performance_rating)
    
    @property
    def performance_color(self):
        """Get color class for performance rating"""
        color_map = {
            'excellent': 'success',
            'good': 'primary',
            'satisfactory': 'info',
            'needs_improvement': 'warning',
            'unsatisfactory': 'danger'
        }
        return color_map.get(self.performance_rating, 'secondary')
    
    @property
    def review_type_display(self):
        """Get display-friendly review type"""
        type_map = {
            'annual': 'Annual Review',
            'probation': 'Probation Review',
            'quarterly': 'Quarterly Review',
            'mid_year': 'Mid-Year Review'
        }
        return type_map.get(self.review_type, self.review_type.replace('_', ' ').title())
    
    @property
    def is_overdue_acknowledgment(self):
        """Check if employee acknowledgment is overdue"""
        if self.employee_acknowledged:
            return False
        
        # Consider overdue if more than 7 days since review date
        from datetime import timedelta
        overdue_date = self.review_date + timedelta(days=7)
        return date.today() > overdue_date
    
    def calculate_overall_score(self):
        """Calculate overall score from individual scores"""
        scores = [
            self.punctuality_score,
            self.productivity_score,
            self.teamwork_score,
            self.communication_score,
            self.initiative_score
        ]
        
        valid_scores = [score for score in scores if score is not None]
        
        if valid_scores:
            self.overall_score = round(sum(valid_scores) / len(valid_scores), 2)
        else:
            self.overall_score = None
        
        # Determine performance rating based on overall score
        if self.overall_score:
            if self.overall_score >= 4.5:
                self.performance_rating = 'excellent'
            elif self.overall_score >= 3.5:
                self.performance_rating = 'good'
            elif self.overall_score >= 2.5:
                self.performance_rating = 'satisfactory'
            elif self.overall_score >= 1.5:
                self.performance_rating = 'needs_improvement'
            else:
                self.performance_rating = 'unsatisfactory'
    
    def calculate_attendance_metrics(self):
        """Calculate attendance metrics for the review period"""
        from models.attendance import AttendanceRecord
        
        # Get attendance records for review period
        attendance_records = AttendanceRecord.query.filter(
            AttendanceRecord.employee_id == self.employee_id,
            AttendanceRecord.date >= self.review_period_start,
            AttendanceRecord.date <= self.review_period_end
        ).all()
        
        total_work_days = len(attendance_records)
        
        if total_work_days > 0:
            present_days = len([r for r in attendance_records if r.is_present])
            late_days = len([r for r in attendance_records if r.status == 'late'])
            absent_days = len([r for r in attendance_records if r.status == 'absent'])
            
            self.attendance_percentage = round((present_days / total_work_days) * 100, 2)
            self.late_incidents = late_days
            self.absent_days = absent_days
            
            # Set punctuality score based on attendance
            if self.attendance_percentage >= 98:
                self.punctuality_score = 5
            elif self.attendance_percentage >= 95:
                self.punctuality_score = 4
            elif self.attendance_percentage >= 90:
                self.punctuality_score = 3
            elif self.attendance_percentage >= 80:
                self.punctuality_score = 2
            else:
                self.punctuality_score = 1
    
    def acknowledge_by_employee(self, comments=None):
        """Mark as acknowledged by employee"""
        self.employee_acknowledged = True
        self.acknowledgment_date = date.today()
        if comments:
            self.employee_comments = comments
    
    @classmethod
    def get_due_reviews(cls, days_ahead=30):
        """Get employees who are due for review"""
        from datetime import timedelta
        from models.employee import Employee
        
        # This would need business logic to determine who is due for review
        # For example, annual reviews 12 months after hire date or last review
        cutoff_date = date.today() + timedelta(days=days_ahead)
        
        # Get employees who haven't had a review in the last 12 months
        # This is a simplified example - real logic would be more complex
        return Employee.query.filter(Employee.is_active == True).all()
    
    @classmethod
    def get_employee_reviews(cls, employee_id):
        """Get all reviews for an employee"""
        return cls.query.filter_by(employee_id=employee_id)\
                      .order_by(cls.review_date.desc()).all()
    
    @classmethod
    def get_pending_acknowledgments(cls):
        """Get reviews pending employee acknowledgment"""
        return cls.query.filter_by(employee_acknowledged=False)\
                      .order_by(cls.review_date).all()
    
    def __repr__(self):
        return f'<PerformanceReview {self.employee_id}: {self.review_type} ({self.review_date})>'