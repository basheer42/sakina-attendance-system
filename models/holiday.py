"""
Sakina Gas Company - Holiday Model
Built from scratch with comprehensive holiday management
Version 3.0 - Enterprise grade with Kenyan holidays
"""

from database import db # FIX: Added missing import for db.or_
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON, Date
from sqlalchemy.sql import func
from datetime import datetime, date, timedelta

class Holiday(db.Model):
    """
    Comprehensive Holiday model for managing public and company holidays
    """
    __tablename__ = 'holidays'
    
    # Primary identification
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    date = Column(Date, nullable=False, index=True)
    year = Column(Integer, nullable=False, index=True)
    
    # Holiday classification
    holiday_type = Column(String(20), nullable=False, default='public', index=True)  # public, company, religious, cultural
    category = Column(String(30), nullable=True)  # national, christian, islamic, hindu, etc.
    
    # Holiday details
    description = Column(Text, nullable=True)
    significance = Column(Text, nullable=True)
    traditions = Column(Text, nullable=True)
    
    # Applicability
    is_mandatory = Column(Boolean, nullable=False, default=True)
    applies_to_all_locations = Column(Boolean, nullable=False, default=True)
    applicable_locations = Column(JSON, nullable=True)  # List of locations if not all
    applies_to_all_departments = Column(Boolean, nullable=False, default=True)
    applicable_departments = Column(JSON, nullable=True)  # List of departments if not all
    
    # Work arrangements
    is_working_day = Column(Boolean, nullable=False, default=False)  # Some holidays might be working days
    overtime_rate_multiplier = Column(Integer, nullable=False, default=2)  # 2x for holidays
    
    # Date handling
    is_recurring_annually = Column(Boolean, nullable=False, default=True)
    is_observed = Column(Boolean, nullable=False, default=True)  # Actually observed by company
    observed_date = Column(Date, nullable=True)  # If different from actual date
    
    # Replacement/compensation
    is_replaced_if_weekend = Column(Boolean, nullable=False, default=True)
    replacement_date = Column(Date, nullable=True)  # Monday if falls on weekend
    replacement_rule = Column(String(50), nullable=True)  # next_monday, previous_friday, etc.
    
    # Legal and compliance
    legal_reference = Column(String(200), nullable=True)
    government_gazette_reference = Column(String(100), nullable=True)
    is_gazetted = Column(Boolean, nullable=False, default=True)
    
    # Cultural and religious details
    lunar_calendar_based = Column(Boolean, nullable=False, default=False)
    estimated_date = Column(Boolean, nullable=False, default=False)  # For lunar-based holidays
    
    # Administrative
    created_date = Column(DateTime, nullable=False, default=func.current_timestamp())
    created_by = Column(Integer, nullable=True)
    last_updated = Column(DateTime, nullable=False, default=func.current_timestamp(), onupdate=func.current_timestamp())
    updated_by = Column(Integer, nullable=True)
    
    # Metadata
    holiday_metadata = Column(JSON, nullable=True) # FIX: Renamed from 'metadata'
    
    # Indexes
    __table_args__ = (
        db.Index('idx_date_type', 'date', 'holiday_type'),
        db.Index('idx_year_type', 'year', 'holiday_type'),
    )
    
    def __init__(self, **kwargs):
        """Initialize holiday with defaults"""
        super(Holiday, self).__init__()
        
        # Set default metadata
        self.holiday_metadata = {} # FIX: Renamed from self.metadata
        self.applicable_locations = []
        self.applicable_departments = []
        
        # Set creation timestamp
        self.created_date = datetime.utcnow()
        
        # Apply any provided kwargs
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        
        # Set year from date if not provided
        if self.date and not self.year:
            self.year = self.date.year
        
        # Handle weekend replacement
        if self.is_replaced_if_weekend and self.date:
            self._calculate_observed_date()
    
    def _calculate_observed_date(self):
        """Calculate observed date if holiday falls on weekend"""
        if not self.date:
            return
        
        weekday = self.date.weekday()  # Monday=0, Sunday=6
        
        # If falls on Saturday (5) or Sunday (6)
        if weekday == 5:  # Saturday
            if self.replacement_rule == 'previous_friday':
                self.observed_date = self.date - timedelta(days=1)
            else:  # Default to next Monday
                self.observed_date = self.date + timedelta(days=2)
        elif weekday == 6:  # Sunday
            self.observed_date = self.date + timedelta(days=1)  # Monday
        else:
            self.observed_date = self.date  # Same day if weekday
    
    def get_effective_date(self):
        """Get the effective holiday date (observed date if different)"""
        return self.observed_date or self.date
    
    def is_applicable_to_location(self, location):
        """Check if holiday applies to specific location"""
        if self.applies_to_all_locations:
            return True
        
        if self.applicable_locations:
            return location in self.applicable_locations
        
        return False
    
    def is_applicable_to_department(self, department):
        """Check if holiday applies to specific department"""
        if self.applies_to_all_departments:
            return True
        
        if self.applicable_departments:
            return department in self.applicable_departments
        
        return False
    
    def is_applicable_to_employee(self, employee):
        """Check if holiday applies to specific employee"""
        location_applies = self.is_applicable_to_location(employee.location)
        department_applies = self.is_applicable_to_department(employee.department)
        
        return location_applies and department_applies
    
    def get_holiday_type_display(self):
        """Get human-readable holiday type"""
        type_map = {
            'public': 'Public Holiday',
            'company': 'Company Holiday',
            'religious': 'Religious Holiday',
            'cultural': 'Cultural Holiday',
            'memorial': 'Memorial Day',
            'national': 'National Holiday'
        }
        return type_map.get(self.holiday_type, self.holiday_type.title())
    
    def get_overtime_multiplier(self):
        """Get overtime rate multiplier for this holiday"""
        if not self.is_working_day:
            return self.overtime_rate_multiplier
        return 1  # Normal rate if it's a working holiday
    
    def falls_on_weekend(self):
        """Check if holiday falls on weekend"""
        if not self.date:
            return False
        return self.date.weekday() >= 5  # Saturday or Sunday
    
    def is_long_weekend(self):
        """Check if holiday creates a long weekend"""
        if not self.date:
            return False
        
        weekday = self.date.weekday()
        # Friday or Monday holidays create long weekends
        return weekday in [0, 4]  # Monday or Friday
    
    def days_until_holiday(self):
        """Calculate days until this holiday"""
        today = date.today()
        holiday_date = self.get_effective_date()
        
        if holiday_date < today:
            return 0  # Holiday has passed
        
        return (holiday_date - today).days
    
    def to_dict(self, include_sensitive=False):
        """Convert holiday to dictionary"""
        data = {
            'id': self.id,
            'name': self.name,
            'date': self.date.isoformat(),
            'year': self.year,
            'holiday_type': self.holiday_type,
            'holiday_type_display': self.get_holiday_type_display(),
            'description': self.description,
            'is_mandatory': self.is_mandatory,
            'is_working_day': self.is_working_day,
            'is_observed': self.is_observed,
            'observed_date': self.observed_date.isoformat() if self.observed_date else None,
            'effective_date': self.get_effective_date().isoformat(),
            'falls_on_weekend': self.falls_on_weekend(),
            'is_long_weekend': self.is_long_weekend(),
            'days_until_holiday': self.days_until_holiday()
        }
        
        if include_sensitive:
            data.update({
                'significance': self.significance,
                'traditions': self.traditions,
                'applicable_locations': self.applicable_locations,
                'applicable_departments': self.applicable_departments,
                'overtime_rate_multiplier': self.overtime_rate_multiplier,
                'legal_reference': self.legal_reference,
                'government_gazette_reference': self.government_gazette_reference,
                'metadata': self.holiday_metadata # FIX: Renamed
            })
        
        return data
    
    @classmethod
    def is_holiday(cls, check_date):
        """Check if a specific date is a holiday"""
        # FIX: Added filtering for is_observed=True
        holiday = cls.query.filter(
            db.or_(
                cls.date == check_date,
                cls.observed_date == check_date
            ),
            cls.is_observed == True
        ).first()
        
        return holiday is not None
    
    @classmethod
    def get_holiday_for_date(cls, check_date):
        """Get holiday for a specific date"""
        return cls.query.filter(
            db.or_(
                cls.date == check_date,
                cls.observed_date == check_date
            ),
            cls.is_observed == True
        ).first()
    
    @classmethod
    def get_holidays_for_year(cls, year):
        """Get all holidays for a specific year"""
        return cls.query.filter(
            cls.year == year,
            cls.is_observed == True
        ).order_by(cls.date).all()
    
    @classmethod
    def get_holidays_for_month(cls, year, month):
        """Get holidays for a specific month"""
        start_date = date(year, month, 1)
        
        # Get last day of month
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)
        
        return cls.query.filter(
            cls.date.between(start_date, end_date),
            cls.is_observed == True
        ).order_by(cls.date).all()
    
    @classmethod
    def get_upcoming_holidays(cls, days_ahead=90):
        """Get upcoming holidays within specified days"""
        start_date = date.today()
        end_date = start_date + timedelta(days=days_ahead)
        
        return cls.query.filter(
            db.or_(cls.date, cls.observed_date).between(start_date, end_date),
            cls.is_observed == True
        ).order_by(cls.date).all()
    
    @classmethod
    def get_holidays_by_type(cls, holiday_type, year=None):
        """Get holidays by type"""
        query = cls.query.filter(
            cls.holiday_type == holiday_type,
            cls.is_observed == True
        )
        
        if year:
            query = query.filter(cls.year == year)
        
        return query.order_by(cls.date).all()
    
    @classmethod
    def create_kenyan_holidays_2024_2025(cls):
        """Create Kenyan public holidays for 2024-2025"""
        holidays_data = [
            # 2024 Holidays
            {
                'name': 'New Year Day',
                'date': date(2024, 1, 1),
                'year': 2024,
                'holiday_type': 'public',
                'category': 'national',
                'description': 'New Year celebration',
                'significance': 'Beginning of the Gregorian calendar year',
                'legal_reference': 'Public Holidays Act (Cap. 110)',
                'is_gazetted': True
            },
            {
                'name': 'Good Friday',
                'date': date(2024, 3, 29),
                'year': 2024,
                'holiday_type': 'public',
                'category': 'christian',
                'description': 'Christian holy day commemorating crucifixion of Jesus Christ',
                'significance': 'Most solemn day in Christian calendar',
                'legal_reference': 'Public Holidays Act (Cap. 110)',
                'is_gazetted': True
            },
            {
                'name': 'Easter Monday',
                'date': date(2024, 4, 1),
                'year': 2024,
                'holiday_type': 'public',
                'category': 'christian',
                'description': 'Christian holy day following Easter Sunday',
                'significance': 'Celebration of Jesus Christ\'s resurrection',
                'legal_reference': 'Public Holidays Act (Cap. 110)',
                'is_gazetted': True
            },
            {
                'name': 'Labour Day',
                'date': date(2024, 5, 1),
                'year': 2024,
                'holiday_type': 'public',
                'category': 'national',
                'description': 'International Workers\' Day',
                'significance': 'Celebration of workers and labor movement',
                'legal_reference': 'Public Holidays Act (Cap. 110)',
                'is_gazetted': True
            },
            {
                'name': 'Madaraka Day',
                'date': date(2024, 6, 1),
                'year': 2024,
                'holiday_type': 'public',
                'category': 'national',
                'description': 'Self-governance day',
                'significance': 'Commemorates attainment of self-rule in 1963',
                'legal_reference': 'Public Holidays Act (Cap. 110)',
                'is_gazetted': True
            },
            {
                'name': 'Eid al-Adha',
                'date': date(2024, 6, 17),
                'year': 2024,
                'holiday_type': 'public',
                'category': 'islamic',
                'description': 'Islamic festival of sacrifice',
                'significance': 'Commemorates Abraham\'s willingness to sacrifice his son',
                'legal_reference': 'Public Holidays Act (Cap. 110)',
                'is_gazetted': True,
                'lunar_calendar_based': True
            },
            {
                'name': 'Huduma Day',
                'date': date(2024, 10, 10),
                'year': 2024,
                'holiday_type': 'public',
                'category': 'national',
                'description': 'Public service day',
                'significance': 'Honors public service and government workers',
                'legal_reference': 'Public Holidays Act (Cap. 110)',
                'is_gazetted': True
            },
            {
                'name': 'Mashujaa Day',
                'date': date(2024, 10, 20),
                'year': 2024,
                'holiday_type': 'public',
                'category': 'national',
                'description': 'Heroes\' day',
                'significance': 'Honors all those who contributed to independence',
                'legal_reference': 'Public Holidays Act (Cap. 110)',
                'is_gazetted': True
            },
            {
                'name': 'Independence Day',
                'date': date(2024, 12, 12),
                'year': 2024,
                'holiday_type': 'public',
                'category': 'national',
                'description': 'Independence from Britain',
                'significance': 'Commemorates independence from British colonial rule in 1963',
                'legal_reference': 'Public Holidays Act (Cap. 110)',
                'is_gazetted': True
            },
            {
                'name': 'Christmas Day',
                'date': date(2024, 12, 25),
                'year': 2024,
                'holiday_type': 'public',
                'category': 'christian',
                'description': 'Christian celebration of birth of Jesus Christ',
                'significance': 'Most important Christian holiday',
                'legal_reference': 'Public Holidays Act (Cap. 110)',
                'is_gazetted': True
            },
            {
                'name': 'Boxing Day',
                'date': date(2024, 12, 26),
                'year': 2024,
                'holiday_type': 'public',
                'category': 'national',
                'description': 'Post-Christmas holiday',
                'significance': 'Traditional day of giving to the poor',
                'legal_reference': 'Public Holidays Act (Cap. 110)',
                'is_gazetted': True
            },
            
            # 2025 Holidays
            {
                'name': 'New Year Day',
                'date': date(2025, 1, 1),
                'year': 2025,
                'holiday_type': 'public',
                'category': 'national',
                'description': 'New Year celebration',
                'significance': 'Beginning of the Gregorian calendar year',
                'legal_reference': 'Public Holidays Act (Cap. 110)',
                'is_gazetted': True
            },
            {
                'name': 'Good Friday',
                'date': date(2025, 4, 18),
                'year': 2025,
                'holiday_type': 'public',
                'category': 'christian',
                'description': 'Christian holy day commemorating crucifixion of Jesus Christ',
                'significance': 'Most solemn day in Christian calendar',
                'legal_reference': 'Public Holidays Act (Cap. 110)',
                'is_gazetted': True
            },
            {
                'name': 'Easter Monday',
                'date': date(2025, 4, 21),
                'year': 2025,
                'holiday_type': 'public',
                'category': 'christian',
                'description': 'Christian holy day following Easter Sunday',
                'significance': 'Celebration of Jesus Christ\'s resurrection',
                'legal_reference': 'Public Holidays Act (Cap. 110)',
                'is_gazetted': True
            },
            {
                'name': 'Labour Day',
                'date': date(2025, 5, 1),
                'year': 2025,
                'holiday_type': 'public',
                'category': 'national',
                'description': 'International Workers\' Day',
                'significance': 'Celebration of workers and labor movement',
                'legal_reference': 'Public Holidays Act (Cap. 110)',
                'is_gazetted': True
            },
            {
                'name': 'Madaraka Day',
                'date': date(2025, 6, 1),
                'year': 2025,
                'holiday_type': 'public',
                'category': 'national',
                'description': 'Self-governance day',
                'significance': 'Commemorates attainment of self-rule in 1963',
                'legal_reference': 'Public Holidays Act (Cap. 110)',
                'is_gazetted': True
            },
            {
                'name': 'Huduma Day',
                'date': date(2025, 10, 10),
                'year': 2025,
                'holiday_type': 'public',
                'category': 'national',
                'description': 'Public service day',
                'significance': 'Honors public service and government workers',
                'legal_reference': 'Public Holidays Act (Cap. 110)',
                'is_gazetted': True
            },
            {
                'name': 'Mashujaa Day',
                'date': date(2025, 10, 20),
                'year': 2025,
                'holiday_type': 'public',
                'category': 'national',
                'description': 'Heroes\' day',
                'significance': 'Honors all those who contributed to independence',
                'legal_reference': 'Public Holidays Act (Cap. 110)',
                'is_gazetted': True
            },
            {
                'name': 'Independence Day',
                'date': date(2025, 12, 12),
                'year': 2025,
                'holiday_type': 'public',
                'category': 'national',
                'description': 'Independence from Britain',
                'significance': 'Commemorates independence from British colonial rule in 1963',
                'legal_reference': 'Public Holidays Act (Cap. 110)',
                'is_gazetted': True
            },
            {
                'name': 'Christmas Day',
                'date': date(2025, 12, 25),
                'year': 2025,
                'holiday_type': 'public',
                'category': 'christian',
                'description': 'Christian celebration of birth of Jesus Christ',
                'significance': 'Most important Christian holiday',
                'legal_reference': 'Public Holidays Act (Cap. 110)',
                'is_gazetted': True
            },
            {
                'name': 'Boxing Day',
                'date': date(2025, 12, 26),
                'year': 2025,
                'holiday_type': 'public',
                'category': 'national',
                'description': 'Post-Christmas holiday',
                'significance': 'Traditional day of giving to the poor',
                'legal_reference': 'Public Holidays Act (Cap. 110)',
                'is_gazetted': True
            },
            
            # Company holidays
            {
                'name': 'Sakina Gas Founders Day',
                'date': date(2024, 9, 15),
                'year': 2024,
                'holiday_type': 'company',
                'category': 'company',
                'description': 'Company founding anniversary',
                'significance': 'Celebrates the establishment of Sakina Gas Company',
                'is_mandatory': False,
                'is_working_day': True,
                'overtime_rate_multiplier': 1
            },
            {
                'name': 'Sakina Gas Founders Day',
                'date': date(2025, 9, 15),
                'year': 2025,
                'holiday_type': 'company',
                'category': 'company',
                'description': 'Company founding anniversary',
                'significance': 'Celebrates the establishment of Sakina Gas Company',
                'is_mandatory': False,
                'is_working_day': True,
                'overtime_rate_multiplier': 1
            }
        ]
        
        holidays = []
        for holiday_data in holidays_data:
            # Check if holiday already exists
            existing = cls.query.filter_by(
                name=holiday_data['name'],
                date=holiday_data['date']
            ).first()
            
            if not existing:
                holiday = cls(**holiday_data)
                holidays.append(holiday)
        
        return holidays
    
    def __repr__(self):
        return f'<Holiday {self.name}: {self.date} ({self.holiday_type})>'