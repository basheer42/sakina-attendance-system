# 🏢 Sakina Gas Company - Attendance Management System

![Sakina Gas Logo](static/images/logo.png)

## 📋 Overview

Professional attendance management system built for Sakina Gas Company featuring multi-location support, shift management, and full compliance with Kenyan Employment Act 2007.

## ✨ Key Features

### 🌍 **Multi-Location Management**
- **Head Office** - Standard business hours
- **3 Gas Stations** - Dandora, Tassia, Kiambu
- **Dual Shift Support** - Day (06:00-18:00) & Night (18:00-06:00)

### 👥 **Role-Based Access Control**
- **HR Manager** - Full system administration and oversight
- **Station Managers** - Location-specific management and reporting

### ⚖️ **Kenyan Labor Law Compliance**
- **Employment Act 2007** integration
- **Automatic validation** for leave requests
- **Legal limit enforcement**:
  - Annual Leave: 21 days
  - Maternity Leave: 90 days (3 months)
  - Paternity Leave: 14 days
  - Sick Leave: 7 days (without certificate)

### 📊 **Executive Dashboard**
- **Real-time KPIs** and attendance metrics
- **Location breakdown** with shift details
- **Interactive attendance tracking**
- **Professional data visualization**

### 🚀 **Modern Features**
- **Responsive design** - Works on all devices
- **Real-time updates** - Live dashboard refresh
- **Professional UI** - Enterprise-grade interface
- **Brand integration** - Sakina Gas colors and logo

## 🛠️ Technology Stack

- **Backend**: Flask 3.0 (Python)
- **Database**: SQLite with SQLAlchemy ORM
- **Frontend**: Bootstrap 5.3 + Custom CSS
- **Authentication**: Flask-Login with session management
- **Icons**: Bootstrap Icons
- **Fonts**: Google Fonts (Inter)

## ⚡ Quick Start

### Prerequisites
- Python 3.7 or higher
- pip package manager

### Installation

1. **Clone the repository:**
```bash
git clone https://github.com/yourusername/sakina-attendance-system.git
cd sakina-attendance-system
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Run the application:**
```bash
python app.py
```

4. **Access the system:**
- URL: http://localhost:5000
- HR Manager: `hr_manager` / `Manager123!`
- Station Manager: `dandora_manager` / `Manager123!`

## 👤 Default User Accounts

| Role | Username | Password | Access Level |
|------|----------|----------|--------------|
| HR Manager | `hr_manager` | `Manager123!` | Full system access |
| Dandora Manager | `dandora_manager` | `Manager123!` | Dandora Station only |
| Tassia Manager | `tassia_manager` | `Manager123!` | Tassia Station only |
| Kiambu Manager | `kiambu_manager` | `Manager123!` | Kiambu Station only |

⚠️ **Change these passwords after first login for security**

## 📁 Project Structure

```
sakina-attendance-system/
├── app.py                 # Main Flask application
├── config.py             # Configuration settings
├── kenyan_labor_laws.py  # Legal compliance module
├── requirements.txt      # Python dependencies
├── models/
│   └── __init__.py       # Database models
├── routes/
│   ├── auth.py          # Authentication routes
│   ├── dashboard.py     # Dashboard and analytics
│   ├── employees.py     # Employee management
│   ├── attendance.py    # Attendance tracking
│   └── leaves.py        # Leave management
├── templates/
│   ├── base.html        # Base template with branding
│   ├── auth/            # Authentication pages
│   ├── dashboard/       # Dashboard templates
│   ├── employees/       # Employee management
│   ├── attendance/      # Attendance pages
│   └── leaves/          # Leave management
└── static/
    ├── css/             # Custom stylesheets
    ├── js/              # JavaScript files
    └── images/          # Company logo and assets
```

## 🚀 Deployment

### Local Development
The system is configured for immediate local development and testing.

### Production Deployment
Ready for deployment to:
- **PythonAnywhere** (recommended)
- **Heroku**
- **DigitalOcean**
- **AWS EC2**

See deployment documentation for platform-specific instructions.

## 📊 Features in Detail

### Executive Dashboard
- **Company-wide KPIs** with real-time data
- **Location-specific metrics** with shift breakdown
- **Visual attendance indicators** with color coding
- **Quick action buttons** for common tasks

### Employee Management
- **Comprehensive employee profiles**
- **Multi-location assignment**
- **Shift scheduling**
- **Department organization**

### Attendance Tracking
- **Clock in/out functionality**
- **Status tracking** (Present/Absent/On Leave)
- **Notes system** for absence reasons
- **Automatic calculations**

### Leave Management
- **Legal compliance validation**
- **Approval workflows**
- **Balance tracking**
- **HR override capabilities**

## ⚖️ Legal Compliance

This system is built to comply with:
- **Employment Act No. 11 of 2007** (Kenya)
- **Labour Relations Act** (Kenya)
- **Work Injury Benefits Act** (Kenya)

### Automatic Validations
- Leave duration limits
- Notice period requirements
- Medical certificate requirements
- Approval workflows

## 🔐 Security Features

- **Session management** with configurable timeouts
- **Role-based access control**
- **CSRF protection**
- **SQL injection prevention**
- **XSS protection**

## 📝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Commit your changes (`git commit -am 'Add new feature'`)
4. Push to the branch (`git push origin feature/new-feature`)
5. Create a Pull Request

## 📞 Support

For technical support or questions:
- **Email**: support@sakinagas.com
- **Documentation**: [Link to docs]
- **Issues**: GitHub Issues tab

## 📄 License

This project is proprietary software owned by Sakina Gas Company.

## 🏢 About Sakina Gas Company

Sakina Gas Company is a leading energy solutions provider in Kenya, committed to excellence in service delivery and operational efficiency.

---

**© 2025 Sakina Gas Company. Excellence in Energy Solutions.**
