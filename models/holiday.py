"""
Holiday Model - Public Holidays Management
This file contains only the Holiday model
"""

from database import db
from datetime import datetime, date

class Holiday(db.Model):
    """Holiday model for managing public holidays"""
    
    __tablename__ = 'holidays'
    
    # Primary fields
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    date = db.Column(db.Date, nullable=False, index=True)
    year = db.Column(db.Integer, nullable=False, index=True)
    
    # Holiday details
    description = db.Column(db.Text, nullable=True)
    is_public_holiday = db.Column(db.Boolean, default=True, nullable=False)
    is_company_holiday = db.Column(db.Boolean, default=False, nullable=False)
    
    # Location specific (if holiday applies to specific locations)
    locations = db.Column(db.Text, nullable=True)  # JSON array of locations
    
    # Holiday type
    holiday_type = db.Column(db.String(50), default='public')  # public, religious, company
    
    # System fields
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Unique constraint to prevent duplicate holidays on same date
    __table_args__ = (
        db.UniqueConstraint('name', 'date', name='unique_holiday_date'),
        db.Index('idx_holiday_year_date', 'year', 'date'),
    )
    
    @property
    def is_weekend(self):
        """Check if holiday falls on weekend"""
        return self.date.weekday() >= 5  # Saturday=5, Sunday=6
    
    @property
    def weekday_name(self):
        """Get weekday name"""
        weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        return weekdays[self.date.weekday()]
    
    @property
    def is_past(self):
        """Check if holiday is in the past"""
        return self.date < date.today()
    
    @property
    def is_today(self):
        """Check if holiday is today"""
        return self.date == date.today()
    
    @property
    def is_upcoming(self):
        """Check if holiday is upcoming"""
        return self.date > date.today()
    
    @property
    def holiday_type_display(self):
        """Get display-friendly holiday type"""
        type_map = {
            'public': 'Public Holiday',
            'religious': 'Religious Holiday',
            'company': 'Company Holiday'
        }
        return type_map.get(self.holiday_type, self.holiday_type.title())
    
    def applies_to_location(self, location):
        """Check if holiday applies to specific location"""
        if not self.locations:
            return True  # Applies to all locations
        
        import json
        try:
            location_list = json.loads(self.locations)
            return location in location_list
        except (json.JSONDecodeError, TypeError):
            return True
    
    @classmethod
    def get_holidays_for_year(cls, year):
        """Get all holidays for a specific year"""
        return cls.query.filter_by(year=year).order_by(cls.date).all()
    
    @classmethod
    def get_upcoming_holidays(cls, days=30):
        """Get upcoming holidays within specified days"""
        from datetime import timedelta
        end_date = date.today() + timedelta(days=days)
        
        return cls.query.filter(
            cls.date >= date.today(),
            cls.date <= end_date
        ).order_by(cls.date).all()
    
    @classmethod
    def is_holiday(cls, check_date, location=None):
        """Check if a specific date is a holiday"""
        query = cls.query.filter_by(date=check_date)
        holidays = query.all()
        
        if not holidays:
            return False
        
        if location:
            # Check if any holiday applies to the location
            for holiday in holidays:
                if holiday.applies_to_location(location):
                    return True
            return False
        
        return True
    
    @classmethod
    def get_holiday_on_date(cls, check_date, location=None):
        """Get holiday information for a specific date"""
        query = cls.query.filter_by(date=check_date)
        holidays = query.all()
        
        if location:
            applicable_holidays = [h for h in holidays if h.applies_to_location(location)]
            return applicable_holidays[0] if applicable_holidays else None
        
        return holidays[0] if holidays else None
    
    @classmethod
    def create_kenyan_holidays(cls, year):
        """Create default Kenyan public holidays for a year"""
        kenyan_holidays = [
            {'name': 'New Year\'s Day', 'month': 1, 'day': 1},
            {'name': 'Labour Day', 'month': 5, 'day': 1},
            {'name': 'Madaraka Day', 'month': 6, 'day': 1},
            {'name': 'Mashujaa Day', 'month': 10, 'day': 20},
            {'name': 'Jamhuri Day', 'month': 12, 'day': 12},
            {'name': 'Christmas Day', 'month': 12, 'day': 25},
            {'name': 'Boxing Day', 'month': 12, 'day': 26},
        ]
        
        created_holidays = []
        
        for holiday_data in kenyan_holidays:
            holiday_date = date(year, holiday_data['month'], holiday_data['day'])
            
            # Check if holiday already exists
            existing = cls.query.filter_by(name=holiday_data['name'], date=holiday_date).first()
            if not existing:
                holiday = cls(
                    name=holiday_data['name'],
                    date=holiday_date,
                    year=year,
                    description=f"Kenyan public holiday - {holiday_data['name']}",
                    is_public_holiday=True,
                    holiday_type='public'
                )
                db.session.add(holiday)
                created_holidays.append(holiday)
        
        if created_holidays:
            db.session.commit()
        
        return created_holidays
    
    def __repr__(self):
        return f'<Holiday {self.name}: {self.date}>'