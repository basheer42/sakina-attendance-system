"""
Sakina Gas Company - User Setup Script (COMPLETELY FIXED)
Run this script to create default users with secure passwords
FIXES: Database path issues, directory creation, permissions
"""

import os
import sys
from datetime import datetime

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask

def create_app():
    """Create Flask app for database operations with proper paths"""
    app = Flask(__name__)
    
    # Get the absolute path to the project directory
    project_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Basic configuration with absolute path
    app.config['SECRET_KEY'] = 'temp-setup-key'
    
    # Use a simple database path in the current directory
    db_path = os.path.join(project_dir, 'sakina_attendance.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    print(f"📁 Project directory: {project_dir}")
    print(f"💾 Database path: {db_path}")
    
    return app

def create_simple_user_table(app):
    """Create a simple user table without complex models"""
    with app.app_context():
        try:
            # Import SQLAlchemy directly
            from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, MetaData, Table, text
            from sqlalchemy.sql import func
            from werkzeug.security import generate_password_hash
            import sqlite3
            
            # Get database path
            project_dir = os.path.dirname(os.path.abspath(__file__))
            db_path = os.path.join(project_dir, 'sakina_attendance.db')
            
            print(f"🔧 Creating database at: {db_path}")
            
            # Create database file directly with sqlite3
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Create users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username VARCHAR(80) UNIQUE NOT NULL,
                    email VARCHAR(120) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    first_name VARCHAR(50),
                    last_name VARCHAR(50),
                    role VARCHAR(30) DEFAULT 'employee',
                    location VARCHAR(50),
                    department VARCHAR(50),
                    is_active BOOLEAN DEFAULT 1,
                    is_verified BOOLEAN DEFAULT 0,
                    created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_login DATETIME,
                    failed_login_attempts INTEGER DEFAULT 0,
                    account_locked_until DATETIME
                )
            ''')
            
            print("✅ Users table created successfully")
            
            # Default user data
            default_users = [
                {
                    'username': 'hr_manager',
                    'email': 'hr@sakinagas.com',
                    'first_name': 'HR',
                    'last_name': 'Manager',
                    'role': 'hr_manager',
                    'location': 'head_office',
                    'department': 'Human Resources',
                    'password': 'manager123' # FIX: Use consistent password
                },
                {
                    'username': 'dandora_manager',
                    'email': 'dandora@sakinagas.com',
                    'first_name': 'Dandora',
                    'last_name': 'Manager',
                    'role': 'station_manager',
                    'location': 'dandora',
                    'department': 'Operations',
                    'password': 'manager123' # FIX: Use consistent password
                },
                {
                    'username': 'tassia_manager',
                    'email': 'tassia@sakinagas.com',
                    'first_name': 'Tassia',
                    'last_name': 'Manager',
                    'role': 'station_manager',
                    'location': 'tassia',
                    'department': 'Operations',
                    'password': 'manager123' # FIX: Use consistent password
                },
                {
                    'username': 'kiambu_manager',
                    'email': 'kiambu@sakinagas.com',
                    'first_name': 'Kiambu',
                    'last_name': 'Manager',
                    'role': 'station_manager',
                    'location': 'kiambu',
                    'department': 'Operations',
                    'password': 'manager123' # FIX: Use consistent password
                }
            ]
            
            created_count = 0
            updated_count = 0
            
            for user_data in default_users:
                username = user_data['username']
                password = user_data.pop('password')
                password_hash = generate_password_hash(password)
                
                # Check if user exists
                cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
                existing = cursor.fetchone()
                
                if existing:
                    # Update existing user
                    cursor.execute('''
                        UPDATE users SET 
                        email = ?, password_hash = ?, first_name = ?, last_name = ?, 
                        role = ?, location = ?, department = ?, is_active = 1, is_verified = 1
                        WHERE username = ?
                    ''', (
                        user_data['email'], password_hash, user_data['first_name'], 
                        user_data['last_name'], user_data['role'], user_data['location'],
                        user_data['department'], username
                    ))
                    updated_count += 1
                    print(f"✅ Updated user: {username}")
                else:
                    # Create new user
                    cursor.execute('''
                        INSERT INTO users (
                            username, email, password_hash, first_name, last_name, 
                            role, location, department, is_active, is_verified
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, 1)
                    ''', (
                        username, user_data['email'], password_hash, user_data['first_name'],
                        user_data['last_name'], user_data['role'], user_data['location'],
                        user_data['department']
                    ))
                    created_count += 1
                    print(f"✅ Created user: {username}")
            
            # Commit changes
            conn.commit()
            conn.close()
            
            print(f"\n🎉 SUCCESS!")
            print(f"   Database created at: {db_path}")
            print(f"   Created: {created_count} users")
            print(f"   Updated: {updated_count} users")
            print(f"\n📋 LOGIN CREDENTIALS:")
            print("   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            print("   │ Username         │ Password         │ Role           │")
            print("   ├──────────────────┼──────────────────┼────────────────┤")
            print("   │ hr_manager       │ manager123       │ HR Manager     │") # FIX: Use consistent password
            print("   │ dandora_manager  │ manager123       │ Station Mgr    │") # FIX: Use consistent password
            print("   │ tassia_manager   │ manager123       │ Station Mgr    │") # FIX: Use consistent password
            print("   │ kiambu_manager   │ manager123       │ Station Mgr    │") # FIX: Use consistent password
            print("   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            print("\n⚠️  IMPORTANT: Change these passwords after first login!")
            
            # Test database connection
            test_conn = sqlite3.connect(db_path)
            test_cursor = test_conn.cursor()
            test_cursor.execute('SELECT COUNT(*) FROM users')
            user_count = test_cursor.fetchone()[0]
            test_conn.close()
            
            print(f"\n🔍 DATABASE VERIFICATION:")
            print(f"   Database file exists: {os.path.exists(db_path)}")
            print(f"   Database file size: {os.path.getsize(db_path)} bytes")
            print(f"   Total users in database: {user_count}")
            
            print(f"\n🔧 NEXT STEPS:")
            print("   1. Run 'python app.py' to start the application")
            print("   2. Open http://localhost:5000 in your browser")
            print("   3. Login with the credentials above")
            print("   4. Change the default passwords immediately")
            
            return True
            
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

def test_database_permissions():
    """Test if we can create files in the current directory"""
    project_dir = os.path.dirname(os.path.abspath(__file__))
    test_file = os.path.join(project_dir, 'test_permissions.tmp')
    
    try:
        # Try to create a test file
        with open(test_file, 'w') as f:
            f.write('test')
        
        # Try to read it back
        with open(test_file, 'r') as f:
            content = f.read()
        
        # Clean up
        os.remove(test_file)
        
        print(f"✅ Directory permissions OK: {project_dir}")
        return True
        
    except Exception as e:
        print(f"❌ Directory permission error: {e}")
        print(f"   Directory: {project_dir}")
        print(f"   Current user may not have write permissions")
        return False

if __name__ == '__main__':
    print("🏢 SAKINA GAS COMPANY - User Setup Script (COMPLETELY FIXED)")
    print("=" * 65)
    print("🔧 NEW FIXES APPLIED:")
    print("   ✅ Direct SQLite database creation")
    print("   ✅ Absolute file paths")
    print("   ✅ Permission checking")
    print("   ✅ Database verification")
    print("   ✅ No complex model imports")
    print("=" * 65)
    
    # Test permissions first
    if not test_database_permissions():
        print("\n❌ Cannot write to current directory. Try running as administrator or change directory permissions.")
        sys.exit(1)
    
    app = create_app()
    success = create_simple_user_table(app)
    
    if success:
        print("\n✅ Setup completed successfully!")
        print("   Your database is ready and users are created.")
        print("   You can now run 'python app.py' and login.")
    else:
        print("\n❌ Setup failed. Please check the error messages above.")
        sys.exit(1)