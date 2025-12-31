@echo off
REM Sakina Gas Attendance System - Windows Installation Script (Python 3.13 Compatible)

echo 🚀 Setting up Sakina Gas Attendance System (Python 3.13 Compatible)...
echo ================================================

REM Check Python version
python --version
if errorlevel 1 (
    echo ❌ Python is not installed. Please install Python 3.8+ and try again.
    pause
    exit /b 1
)

echo 📦 Installing compatible dependencies for your Python version...
python -m pip install --upgrade pip

REM Install specific compatible versions for Python 3.13
echo Installing Flask and core dependencies...
python -m pip install Flask==3.0.0
python -m pip install Werkzeug==3.0.1
python -m pip install Jinja2==3.1.2
python -m pip install MarkupSafe==2.1.3
python -m pip install click==8.1.7

echo Installing SQLAlchemy compatible version...
python -m pip install SQLAlchemy==2.0.23
python -m pip install Flask-SQLAlchemy==3.0.5

echo Installing Flask extensions...
python -m pip install Flask-Login==0.6.3
python -m pip install Flask-WTF==1.2.1
python -m pip install WTForms==3.1.1

echo Installing utility libraries...
python -m pip install python-dateutil==2.8.2

REM Optional dependencies
echo 📧 Installing optional dependencies...
python -m pip install Flask-Mail==0.9.1 2>nul || echo ⚠️  Flask-Mail skipped (optional)
python -m pip install python-dotenv==1.0.0 2>nul || echo ⚠️  python-dotenv skipped (optional)
python -m pip install bcrypt==4.1.2 2>nul || echo ⚠️  bcrypt skipped (optional)

echo.
echo ✅ Installation complete!
echo.
echo 🔧 PYTHON 3.13 COMPATIBILITY NOTE:
echo Using specifically tested compatible versions for Python 3.13
echo.
echo 🎯 To start the application:
echo    python app.py
echo.
echo 🌐 Access the system at: http://localhost:5000
echo 🔑 Login credentials:
echo    Username: hr_manager
echo    Password: Manager123!
echo.
echo 📝 If you encounter any issues, try running: python simple_app.py
echo.
pause