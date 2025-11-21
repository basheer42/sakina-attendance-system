"""
Audit Log Model - System Activity Tracking
This file contains only the AuditLog model
"""

from database import db
from datetime import datetime
import json

class AuditLog(db.Model):
    """Audit log model for tracking system activities"""
    
    __tablename__ = 'audit_logs'
    
    # Primary fields
    id = db.Column(db.Integer, primary_key=True)
    
    # User and action information
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    action = db.Column(db.String(100), nullable=False, index=True)
    
    # Target information
    target_type = db.Column(db.String(50), nullable=True)  # employee, leave_request, attendance, etc.
    target_id = db.Column(db.Integer, nullable=True)
    
    # Action details
    details = db.Column(db.Text, nullable=True)
    old_values = db.Column(db.Text, nullable=True)  # JSON string of old values
    new_values = db.Column(db.Text, nullable=True)  # JSON string of new values
    
    # Request information
    ip_address = db.Column(db.String(45), nullable=True)  # IPv6 support
    user_agent = db.Column(db.String(500), nullable=True)
    
    # Timestamp
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Additional metadata
    session_id = db.Column(db.String(100), nullable=True)
    request_id = db.Column(db.String(100), nullable=True)
    
    # Indexes for better performance
    __table_args__ = (
        db.Index('idx_audit_user_action', 'user_id', 'action'),
        db.Index('idx_audit_target', 'target_type', 'target_id'),
        db.Index('idx_audit_timestamp', 'timestamp'),
    )
    
    @property
    def user_display(self):
        """Get user display name"""
        if self.user_id and hasattr(self, 'user'):
            return self.user.full_name
        return 'System'
    
    @property
    def action_display(self):
        """Get display-friendly action name"""
        action_map = {
            'login': 'User Login',
            'logout': 'User Logout',
            'attendance_marked': 'Attendance Marked',
            'attendance_updated': 'Attendance Updated',
            'leave_requested': 'Leave Requested',
            'leave_approved': 'Leave Approved',
            'leave_rejected': 'Leave Rejected',
            'employee_added': 'Employee Added',
            'employee_updated': 'Employee Updated',
            'employee_deactivated': 'Employee Deactivated',
            'password_changed': 'Password Changed',
            'profile_updated': 'Profile Updated'
        }
        return action_map.get(self.action, self.action.replace('_', ' ').title())
    
    @property
    def severity_level(self):
        """Get severity level of the action"""
        high_severity = ['employee_deactivated', 'leave_approved', 'attendance_updated']
        medium_severity = ['leave_requested', 'attendance_marked', 'employee_added']
        
        if self.action in high_severity:
            return 'high'
        elif self.action in medium_severity:
            return 'medium'
        return 'low'
    
    @property
    def severity_color(self):
        """Get color class for severity level"""
        colors = {
            'high': 'danger',
            'medium': 'warning',
            'low': 'info'
        }
        return colors.get(self.severity_level, 'secondary')
    
    def get_old_values_dict(self):
        """Get old values as dictionary"""
        if self.old_values:
            try:
                return json.loads(self.old_values)
            except json.JSONDecodeError:
                return {}
        return {}
    
    def get_new_values_dict(self):
        """Get new values as dictionary"""
        if self.new_values:
            try:
                return json.loads(self.new_values)
            except json.JSONDecodeError:
                return {}
        return {}
    
    def get_changes(self):
        """Get list of changes made"""
        old_vals = self.get_old_values_dict()
        new_vals = self.get_new_values_dict()
        
        changes = []
        
        # Find changed fields
        all_fields = set(old_vals.keys()) | set(new_vals.keys())
        
        for field in all_fields:
            old_value = old_vals.get(field)
            new_value = new_vals.get(field)
            
            if old_value != new_value:
                changes.append({
                    'field': field,
                    'old_value': old_value,
                    'new_value': new_value
                })
        
        return changes
    
    @classmethod
    def log_action(cls, user_id, action, target_type=None, target_id=None, 
                   details=None, old_values=None, new_values=None, 
                   ip_address=None, user_agent=None):
        """Log an action to the audit trail"""
        
        # Convert dictionaries to JSON strings
        old_values_json = json.dumps(old_values) if old_values else None
        new_values_json = json.dumps(new_values) if new_values else None
        
        audit_log = cls(
            user_id=user_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            details=details,
            old_values=old_values_json,
            new_values=new_values_json,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        db.session.add(audit_log)
        # Note: Commit should be handled by the calling function
        
        return audit_log
    
    @classmethod
    def get_user_activity(cls, user_id, limit=50):
        """Get recent activity for a specific user"""
        return cls.query.filter_by(user_id=user_id)\
                      .order_by(cls.timestamp.desc())\
                      .limit(limit).all()
    
    @classmethod
    def get_target_history(cls, target_type, target_id, limit=20):
        """Get history for a specific target (employee, leave request, etc.)"""
        return cls.query.filter_by(target_type=target_type, target_id=target_id)\
                      .order_by(cls.timestamp.desc())\
                      .limit(limit).all()
    
    @classmethod
    def get_recent_activity(cls, limit=100, action_filter=None):
        """Get recent system activity"""
        query = cls.query
        
        if action_filter:
            if isinstance(action_filter, list):
                query = query.filter(cls.action.in_(action_filter))
            else:
                query = query.filter_by(action=action_filter)
        
        return query.order_by(cls.timestamp.desc()).limit(limit).all()
    
    @classmethod
    def cleanup_old_logs(cls, days_to_keep=365):
        """Clean up old audit logs to prevent database bloat"""
        from datetime import timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        deleted_count = cls.query.filter(cls.timestamp < cutoff_date).delete()
        db.session.commit()
        
        return deleted_count
    
    def __repr__(self):
        return f'<AuditLog {self.action}: {self.user_display} at {self.timestamp}>'