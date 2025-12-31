#!/usr/bin/env python3
"""
Sakina Gas Company - User Setup Script
Creates default users and initializes the database with sample data.

This script should be run once during initial setup.

Usage:
    python setup_users.py
    
Default Credentials (after running):
    HR Manager: hr_manager / Manager123!
    Dandora Manager: dandora_manager / Manager123!
    Tassia Manager: tassia_manager / Manager123!
    Kiambu Manager: kiambu_manager / Manager123!

IMPORTANT: Change these passwords after first login!

Version: 3.0.0
"""

import os
import sys
import sqlite3
from datetime import datetime, date, timedelta
from pathlib import Path

# Add project root to path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)


# =============================================================================
# Configuration
# =============================================================================

# STANDARDIZED PASSWORD - matches README.md and app_secrets.py
SECURE_DEFAULT_PASSWORD = 'Manager123!'

# Database path
DB_FILENAME = 'sakina_attendance.db'
DB_PATH = os.path.join(project_dir, 'instance', DB_FILENAME)

# Default users configuration
DEFAULT_USERS = [
    {
        'username': 'hr_manager',
        'email': 'hr@sakinagas.com',
        'first_name': 'HR',
        'last_name': 'Manager',
        'role': 'hr_manager',
        'department': 'hr',
        'location': 'head_office',
        'is_active': True,
        'is_admin': True
    },
    {
        'username': 'dandora_manager',
        'email': 'dandora@sakinagas.com',
        'first_name': 'Dandora',
        'last_name': 'Manager',
        'role': 'station_manager',
        'department': 'operations',
        'location': 'dandora',
        'is_active': True,
        'is_admin': False
    },
    {
        'username': 'tassia_manager',
        'email': 'tassia@sakinagas.com',
        'first_name': 'Tassia',
        'last_name': 'Manager',
        'role': 'station_manager',
        'department': 'operations',
        'location': 'tassia',
        'is_active': True,
        'is_admin': False
    },
    {
        'username': 'kiambu_manager',
        'email': 'kiambu@sakinagas.com',
        'first_name': 'Kiambu',
        'last_name': 'Manager',
        'role': 'station_manager',
        'department': 'operations',
        'location': 'kiambu',
        'is_active': True,
        'is_admin': False
    }
]

# Default employees (sample data)
DEFAULT_EMPLOYEES = [
    {
        'employee_id': 'EMP001',
        'first_name': 'John',
        'last_name': 'Kamau',
        'email': 'john.kamau@sakinagas.com',
        'department': 'operations',
        'position': 'Station Attendant',
        'location': 'dandora',
        'shift': 'day',
        'employment_type': 'permanent'
    },
    {
        'employee_id': 'EMP002',
        'first_name': 'Mary',
        'last_name': 'Wanjiku',
        'email': 'mary.wanjiku@sakinagas.com',
        'department': 'operations',
        'position': 'Station Attendant',
        'location': 'tassia',
        'shift': 'day',
        'employment_type': 'permanent'
    },
    {
        'employee_id': 'EMP003',
        'first_name': 'Peter',
        'last_name': 'Ochieng',
        'email': 'peter.ochieng@sakinagas.com',
        'department': 'operations',
        'position': 'Station Attendant',
        'location': 'kiambu',
        'shift': 'night',
        'employment_type': 'permanent'
    },
    {
        'employee_id': 'EMP004',
        'first_name': 'Grace',
        'last_name': 'Muthoni',
        'email': 'grace.muthoni@sakinagas.com',
        'department': 'hr',
        'position': 'HR Assistant',
        'location': 'head_office',
        'shift': 'day',
        'employment_type': 'permanent'
    },
    {
        'employee_id': 'EMP005',
        'first_name': 'David',
        'last_name': 'Njoroge',
        'email': 'david.njoroge@sakinagas.com',
        'department': 'finance',
        'position': 'Accountant',
        'location': 'head_office',
        'shift': 'day',
        'employment_type': 'permanent'
    }
]


# =============================================================================
# Utility Functions
# =============================================================================

def hash_password(password):
    """
    Hash a password using bcrypt.
    Falls back to werkzeug if bcrypt is not available.
    """
    try:
        import bcrypt
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    except ImportError:
        try:
            from werkzeug.security import generate_password_hash
            return generate_password_hash(password)
        except ImportError:
            # Last resort - use hashlib (not recommended for production)
            import hashlib
            return hashlib.sha256(password.encode()).hexdigest()


def test_database_permissions():
    """Test if we can create files in the instance directory"""
    instance_dir = os.path.join(project_dir, 'instance')
    test_file = os.path.join(instance_dir, 'test_permissions.tmp')
    
    try:
        # Ensure instance directory exists
        os.makedirs(instance_dir, exist_ok=True)
        
        # Try to create a test file
        with open(test_file, 'w') as f:
            f.write('test')
        
        # Try to read it back
        with open(test_file, 'r') as f:
            content = f.read()
        
        # Clean up
        os.remove(test_file)
        
        print(f"✅ Directory permissions OK: {instance_dir}")
        return True
        
    except Exception as e:
        print(f"❌ Directory permission error: {e}")
        print(f"   Directory: {instance_dir}")
        print(f"   Current user may not have write permissions")
        return False


def create_database_tables(conn):
    """Create all required database tables"""
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username VARCHAR(64) UNIQUE NOT NULL,
            email VARCHAR(120) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            first_name VARCHAR(50),
            last_name VARCHAR(50),
            role VARCHAR(30) DEFAULT 'employee',
            department VARCHAR(50),
            location VARCHAR(50),
            is_active BOOLEAN DEFAULT 1,
            is_admin BOOLEAN DEFAULT 0,
            is_verified BOOLEAN DEFAULT 0,
            created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_login DATETIME,
            failed_login_attempts INTEGER DEFAULT 0,
            account_locked_until DATETIME,
            force_password_change BOOLEAN DEFAULT 0
        )
    ''')
    
    # Employees table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id VARCHAR(20) UNIQUE NOT NULL,
            first_name VARCHAR(50) NOT NULL,
            last_name VARCHAR(50) NOT NULL,
            middle_name VARCHAR(50),
            email VARCHAR(120),
            phone_number VARCHAR(20),
            national_id VARCHAR(20),
            date_of_birth DATE,
            gender VARCHAR(10),
            marital_status VARCHAR(20),
            address TEXT,
            department VARCHAR(50),
            position VARCHAR(100),
            location VARCHAR(50),
            shift VARCHAR(20) DEFAULT 'day',
            employment_type VARCHAR(30) DEFAULT 'permanent',
            hire_date DATE,
            termination_date DATE,
            basic_salary DECIMAL(12, 2),
            is_active BOOLEAN DEFAULT 1,
            created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            annual_leave_balance DECIMAL(5, 2) DEFAULT 21,
            sick_leave_balance DECIMAL(5, 2) DEFAULT 30
        )
    ''')
    
    # Attendance records table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS attendance_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            date DATE NOT NULL,
            status VARCHAR(20) DEFAULT 'present',
            shift VARCHAR(20),
            location VARCHAR(50),
            clock_in_time DATETIME,
            clock_out_time DATETIME,
            worked_hours DECIMAL(5, 2),
            notes TEXT,
            is_approved BOOLEAN DEFAULT 0,
            approved_by INTEGER,
            created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (employee_id) REFERENCES employees(id)
        )
    ''')
    
    # Leave requests table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS leave_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            leave_type VARCHAR(30) NOT NULL,
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            total_days DECIMAL(5, 2),
            reason TEXT,
            status VARCHAR(20) DEFAULT 'pending',
            requested_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            approved_by INTEGER,
            approved_date DATETIME,
            approval_comments TEXT,
            FOREIGN KEY (employee_id) REFERENCES employees(id)
        )
    ''')
    
    # Holidays table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS holidays (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(100) NOT NULL,
            date DATE NOT NULL,
            year INTEGER NOT NULL,
            holiday_type VARCHAR(30) DEFAULT 'public',
            description TEXT,
            is_mandatory BOOLEAN DEFAULT 1,
            is_observed BOOLEAN DEFAULT 1
        )
    ''')
    
    # Audit logs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type VARCHAR(50) NOT NULL,
            event_category VARCHAR(30) DEFAULT 'general',
            event_action VARCHAR(30),
            description TEXT,
            user_id INTEGER,
            target_type VARCHAR(50),
            target_id INTEGER,
            ip_address VARCHAR(45),
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            risk_level VARCHAR(20) DEFAULT 'low'
        )
    ''')
    
    conn.commit()
    print("✅ Database tables created successfully")


def create_default_users(conn):
    """Create default user accounts"""
    cursor = conn.cursor()
    
    # Check if users already exist
    cursor.execute('SELECT COUNT(*) FROM users')
    if cursor.fetchone()[0] > 0:
        print("ℹ️  Users already exist, skipping user creation")
        return False
    
    # Hash the default password
    password_hash = hash_password(SECURE_DEFAULT_PASSWORD)
    
    for user in DEFAULT_USERS:
        cursor.execute('''
            INSERT INTO users (
                username, email, password_hash, first_name, last_name,
                role, department, location, is_active, is_admin
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user['username'],
            user['email'],
            password_hash,
            user['first_name'],
            user['last_name'],
            user['role'],
            user['department'],
            user['location'],
            user['is_active'],
            user['is_admin']
        ))
    
    conn.commit()
    print(f"✅ Created {len(DEFAULT_USERS)} default users")
    return True


def create_default_employees(conn):
    """Create sample employee records"""
    cursor = conn.cursor()
    
    # Check if employees already exist
    cursor.execute('SELECT COUNT(*) FROM employees')
    if cursor.fetchone()[0] > 0:
        print("ℹ️  Employees already exist, skipping employee creation")
        return False
    
    hire_date = date.today() - timedelta(days=365)  # 1 year ago
    
    for emp in DEFAULT_EMPLOYEES:
        cursor.execute('''
            INSERT INTO employees (
                employee_id, first_name, last_name, email,
                department, position, location, shift,
                employment_type, hire_date, is_active
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            emp['employee_id'],
            emp['first_name'],
            emp['last_name'],
            emp['email'],
            emp['department'],
            emp['position'],
            emp['location'],
            emp['shift'],
            emp['employment_type'],
            hire_date.isoformat(),
            True
        ))
    
    conn.commit()
    print(f"✅ Created {len(DEFAULT_EMPLOYEES)} sample employees")
    return True


def create_kenyan_holidays(conn):
    """Create Kenyan public holidays for current year"""
    cursor = conn.cursor()
    
    current_year = date.today().year
    
    # Check if holidays already exist for this year
    cursor.execute('SELECT COUNT(*) FROM holidays WHERE year = ?', (current_year,))
    if cursor.fetchone()[0] > 0:
        print(f"ℹ️  Holidays for {current_year} already exist, skipping")
        return False
    
    kenyan_holidays = [
        (f"New Year's Day", f"{current_year}-01-01", 'public'),
        ("Good Friday", f"{current_year}-03-29", 'public'),  # Date varies
        ("Easter Monday", f"{current_year}-04-01", 'public'),  # Date varies
        ("Labour Day", f"{current_year}-05-01", 'public'),
        ("Madaraka Day", f"{current_year}-06-01", 'public'),
        ("Eid ul-Fitr", f"{current_year}-04-10", 'religious'),  # Date varies
        ("Mashujaa Day", f"{current_year}-10-20", 'public'),
        ("Jamhuri Day", f"{current_year}-12-12", 'public'),
        ("Christmas Day", f"{current_year}-12-25", 'public'),
        ("Boxing Day", f"{current_year}-12-26", 'public'),
    ]
    
    for name, holiday_date, holiday_type in kenyan_holidays:
        cursor.execute('''
            INSERT INTO holidays (name, date, year, holiday_type, is_mandatory, is_observed)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (name, holiday_date, current_year, holiday_type, True, True))
    
    conn.commit()
    print(f"✅ Created {len(kenyan_holidays)} Kenyan holidays for {current_year}")
    return True


def setup_database():
    """Main setup function"""
    print("\n" + "=" * 65)
    print("🏢 SAKINA GAS COMPANY - User Setup Script")
    print("=" * 65)
    
    # Test permissions
    if not test_database_permissions():
        print("\n❌ Cannot write to instance directory. Please check permissions.")
        return False
    
    try:
        # Ensure instance directory exists
        instance_dir = os.path.dirname(DB_PATH)
        os.makedirs(instance_dir, exist_ok=True)
        
        # Connect to database (creates if doesn't exist)
        print(f"\n📁 Database path: {DB_PATH}")
        conn = sqlite3.connect(DB_PATH)
        
        # Create tables
        print("\n📊 Creating database tables...")
        create_database_tables(conn)
        
        # Create default data
        print("\n👥 Creating default users...")
        create_default_users(conn)
        
        print("\n👔 Creating sample employees...")
        create_default_employees(conn)
        
        print("\n📅 Creating Kenyan holidays...")
        create_kenyan_holidays(conn)
        
        # Close connection
        conn.close()
        
        # Print credentials
        print("\n" + "=" * 65)
        print("✅ SETUP COMPLETED SUCCESSFULLY!")
        print("=" * 65)
        print("\n📋 DEFAULT LOGIN CREDENTIALS:")
        print("   ┌──────────────────┬───────────────────┬────────────────┐")
        print("   │ Username         │ Password          │ Role           │")
        print("   ├──────────────────┼───────────────────┼────────────────┤")
        print("   │ hr_manager       │ Manager123!       │ HR Manager     │")
        print("   │ dandora_manager  │ Manager123!       │ Station Mgr    │")
        print("   │ tassia_manager   │ Manager123!       │ Station Mgr    │")
        print("   │ kiambu_manager   │ Manager123!       │ Station Mgr    │")
        print("   └──────────────────┴───────────────────┴────────────────┘")
        print("\n⚠️  IMPORTANT: Change these passwords after first login!")
        
        # Verify
        print(f"\n🔍 DATABASE VERIFICATION:")
        print(f"   Database file exists: {os.path.exists(DB_PATH)}")
        print(f"   Database file size: {os.path.getsize(DB_PATH)} bytes")
        
        # Count records
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM users')
        user_count = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM employees')
        emp_count = cursor.fetchone()[0]
        conn.close()
        
        print(f"   Total users: {user_count}")
        print(f"   Total employees: {emp_count}")
        
        print(f"\n🔧 NEXT STEPS:")
        print("   1. Run 'python app.py' to start the application")
        print("   2. Open http://localhost:5000 in your browser")
        print("   3. Login with the credentials above")
        print("   4. Change the default passwords immediately")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


# =============================================================================
# Main Entry Point
# =============================================================================

if __name__ == '__main__':
    success = setup_database()
    sys.exit(0 if success else 1)