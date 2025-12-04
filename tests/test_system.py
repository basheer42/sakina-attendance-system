"""
Sakina Gas Attendance System - Application Test Script
Use this to test your system and identify any issues
"""

import sys
import os

def test_imports():
    """Test if all required modules can be imported"""
    print("🔍 Testing imports...")
    
    tests = [
        ("Flask framework", "flask"),
        ("Database connection", "database"),
        ("Configuration", "config"),
        ("User model", "models.user"),
        ("Employee model", "models.employee"),
        ("Attendance model", "models.attendance"),
        ("Leave model", "models.leave"),
        ("Holiday model", "models.holiday"),
        ("Audit model", "models.audit"),
        ("Performance model", "models.performance"),
        ("Auth routes", "routes.auth"),
        ("Dashboard routes", "routes.dashboard"),
        ("Employee routes", "routes.employees"),
        ("Leave routes", "routes.leaves"),
    ]
    
    failed_imports = []
    
    for name, module in tests:
        try:
            __import__(module)
            print(f"  ✅ {name}")
        except ImportError as e:
            print(f"  ❌ {name}: {str(e)}")
            failed_imports.append((name, module, str(e)))
    
    return failed_imports

def test_database_connection():
    """Test database connection and table creation"""
    print("\n🗄️ Testing database connection...")
    
    try:
        from database import db, init_database
        from app import create_app
        
        # Create app and initialize database
        app = create_app('development')
        with app.app_context():
            # Test database connection
            result = db.session.execute(db.text('SELECT 1')).scalar()
            if result == 1:
                print("  ✅ Database connection successful")
            else:
                print("  ❌ Database connection failed")
                return False
                
        return True
    except Exception as e:
        print(f"  ❌ Database test failed: {str(e)}")
        return False

def test_models():
    """Test model creation and basic functionality"""
    print("\n🏗️ Testing models...")
    
    try:
        from app import create_app
        from models.user import User
        from models.employee import Employee
        
        app = create_app('development')
        with app.app_context():
            # Test User model
            user_count = User.query.count()
            print(f"  ✅ User model working - {user_count} users in database")
            
            # Test Employee model
            employee_count = Employee.query.count()
            print(f"  ✅ Employee model working - {employee_count} employees in database")
            
        return True
    except Exception as e:
        print(f"  ❌ Model test failed: {str(e)}")
        return False

def test_routes():
    """Test route registration"""
    print("\n🛣️ Testing routes...")
    
    try:
        from app import create_app
        
        app = create_app('development')
        
        # List all registered routes
        routes = []
        for rule in app.url_map.iter_rules():
            routes.append(str(rule))
        
        print(f"  ✅ {len(routes)} routes registered")
        
        # Check for key routes
        key_routes = ['/auth/login', '/', '/employees/list', '/attendance/mark', '/leaves/list']
        for route in key_routes:
            if any(route in r for r in routes):
                print(f"  ✅ {route} route found")
            else:
                print(f"  ⚠️ {route} route not found")
        
        return True
    except Exception as e:
        print(f"  ❌ Route test failed: {str(e)}")
        return False

def run_comprehensive_test():
    """Run all tests"""
    print("🚀 SAKINA GAS ATTENDANCE SYSTEM - DIAGNOSTIC TEST")
    print("=" * 60)
    
    # Test Python version
    python_version = sys.version
    print(f"🐍 Python Version: {python_version}")
    
    if "3.12" in python_version:
        print("  ✅ Python 3.12 detected (recommended)")
    elif "3.14" in python_version:
        print("  ⚠️ Python 3.14 detected - may have compatibility issues")
    else:
        print("  ⚠️ Unexpected Python version")
    
    print("\n📂 Working Directory:", os.getcwd())
    
    # Run tests
    failed_imports = test_imports()
    db_success = test_database_connection()
    model_success = test_models()
    route_success = test_routes()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY:")
    
    if not failed_imports:
        print("  ✅ All imports successful")
    else:
        print(f"  ❌ {len(failed_imports)} import failures")
    
    print(f"  {'✅' if db_success else '❌'} Database connection")
    print(f"  {'✅' if model_success else '❌'} Model functionality")
    print(f"  {'✅' if route_success else '❌'} Route registration")
    
    if failed_imports or not (db_success and model_success and route_success):
        print("\n🔧 ISSUES DETECTED:")
        
        if failed_imports:
            print("\n  Import Failures:")
            for name, module, error in failed_imports[:5]:  # Show first 5 errors
                print(f"    • {name}: {error}")
        
        print("\n💡 RECOMMENDED ACTIONS:")
        if failed_imports:
            print("  1. Check file locations match the directory structure")
            print("  2. Verify all required files are in the correct folders")
            print("  3. Update import statements if needed")
        
        if not db_success:
            print("  4. Check database.py configuration")
            print("  5. Ensure SQLAlchemy is properly installed")
        
        return False
    else:
        print("\n🎉 ALL TESTS PASSED! Your system is ready to run.")
        print("\n🚀 To start the application, run:")
        print("     python app.py")
        return True

if __name__ == "__main__":
    success = run_comprehensive_test()
    sys.exit(0 if success else 1)