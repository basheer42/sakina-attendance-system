# Sakina Gas Company - Attendance Management System
## Complete Development & Deployment Manual

### 📋 PROJECT OVERVIEW
**Company**: Sakina Gas Company (Kenyan Company)
**System**: Professional Attendance Management System
**Locations**: Head Office + 3 Stations (Dandora, Tassia, Kiambu)
**Users**: HR Manager (Admin), Station Managers
**Compliance**: Kenyan Labor Laws (Employment Act 2007)

---

## 🏗️ SYSTEM ARCHITECTURE

### **Locations & Shifts**
- **Head Office**: No shifts (regular 8-5 schedule)
- **Stations (3)**: Two shifts each
  - **Day Shift**: 06:00 - 18:00
  - **Night Shift**: 18:00 - 06:00

### **User Roles & Permissions**
1. **HR Manager** (Super Admin)
   - Full system access
   - Employee management (add/edit/remove)
   - Approve/reject ALL leave requests
   - View all locations & reports
   - Override attendance records

2. **Station Managers**
   - Manage their specific station only
   - Mark attendance for their employees
   - Request leaves for employees
   - View their station's reports only

### **Core Features Required**
1. **Professional Dashboard** with company logo
2. **Attendance Overview** showing all locations/shifts
3. **Real-time Present/Absent counts** (clickable for details)
4. **Advanced Leave Management** with Kenyan law compliance
5. **Filterable Employee Lists**
6. **Notes System** for absences
7. **Automatic Leave Calculations**
8. **Warning System** for law violations

---

## 📚 KENYAN LABOR LAW COMPLIANCE

### **Leave Entitlements (Employment Act 2007)**
```python
KENYAN_LEAVE_LAWS = {
    'annual_leave': {
        'days': 21,
        'note': 'Minimum 21 working days per year'
    },
    'sick_leave': {
        'days': 7,
        'note': 'Up to 7 days with certificate, more with medical board'
    },
    'maternity_leave': {
        'days': 90,  # 3 months
        'note': '3 months (can be split before/after birth)'
    },
    'paternity_leave': {
        'days': 14,
        'note': 'Maximum 14 consecutive days'
    },
    'compassionate_leave': {
        'days': 7,
        'note': 'Up to 7 days for family bereavement'
    }
}
```

### **System Warnings Required**
- Pop-up warnings when exceeding legal limits
- HR override capability with logged justification
- Automatic calculation of remaining leave days
- Compliance reporting features

---

## 🛠️ DEVELOPMENT PHASES

### **PHASE 1: Foundation Setup** ✅
**Files Created:**
- `requirements.txt` - Python dependencies
- `config.py` - Application configuration
- `models/__init__.py` - Database models
- `app.py` - Main Flask application

**Database Models:**
- User (authentication)
- Employee (staff records)
- AttendanceRecord (daily attendance)
- LeaveRequest (leave management)
- Holiday (company holidays)

### **PHASE 2: Backend Routes** ✅
**Route Files:**
- `routes/auth.py` - Login/logout
- `routes/dashboard.py` - Main dashboard & overviews
- `routes/employees.py` - Employee management
- `routes/attendance.py` - Attendance marking
- `routes/leaves.py` - Leave management

### **PHASE 3: Frontend Templates** 🔄 (In Progress)
**Template Structure:**
```
templates/
├── base.html (main layout with navigation)
├── auth/
│   └── login.html
├── dashboard/
│   ├── main.html (overview dashboard)
│   └── attendance_details.html
├── employees/
│   ├── list.html
│   └── add.html
├── attendance/
│   └── mark.html
└── leaves/
    ├── list.html
    └── request.html
```

### **PHASE 4: Styling & Assets**
**Static Files:**
- `static/css/style.css` - Custom CSS
- `static/js/app.js` - Custom JavaScript
- `static/images/logo.png` - Company logo

### **PHASE 5: Kenyan Law Integration**
**Enhanced Features:**
- Leave law validation system
- Warning popups for violations
- Compliance dashboard
- Legal limits configuration
- Override logging system

### **PHASE 6: Testing & Refinement**
**Testing Tasks:**
- Create test employees
- Test all user roles
- Verify law compliance
- Test attendance workflows
- Check report generation

### **PHASE 7: Deployment Preparation**
**Pre-deployment:**
- Production configuration
- Security hardening
- Database optimization
- Performance testing

### **PHASE 8: PythonAnywhere Deployment**
**Deployment Steps:**
1. Upload files to PythonAnywhere
2. Set up virtual environment
3. Configure database
4. Set environment variables
5. Configure WSGI
6. Test live system
7. DNS setup (if custom domain)

---

## 💻 LOCAL DEVELOPMENT SETUP

### **Installation Steps:**
```bash
# 1. Navigate to project folder
cd sakina_attendance_system

# 2. Install dependencies
pip install -r requirements.txt --break-system-packages

# 3. Run the application
python app.py

# 4. Access system
# URL: http://localhost:5000
# Login: hr_manager / admin123
```

### **Default Users Created:**
- **hr_manager** / admin123 (HR Manager - Full Access)
- **dandora_manager** / manager123 (Dandora Station)
- **tassia_manager** / manager123 (Tassia Station)
- **kiambu_manager** / manager123 (Kiambu Station)

### **Testing Workflow:**
1. Login as HR Manager
2. Add test employees to different locations
3. Test attendance marking
4. Create leave requests
5. Test approval workflow
6. Verify dashboard displays

---

## 🚀 DEPLOYMENT TO PYTHONANYWHERE

### **Account Setup:**
1. Create PythonAnywhere account (Free tier available)
2. Choose web app plan
3. Set up Python 3.9+ environment

### **File Upload:**
1. Upload project files via Files tab
2. Extract to `/home/yourusername/sakina_attendance`
3. Install dependencies in console

### **Web App Configuration:**
```python
# WSGI configuration file
import sys
import os

path = '/home/yourusername/sakina_attendance'
if path not in sys.path:
    sys.path.append(path)

from app import create_app
application = create_app()
```

### **Environment Variables:**
```bash
export SECRET_KEY="your-secret-key"
export DATABASE_URL="sqlite:///sakina_attendance.db"
```

### **Go-Live Checklist:**
- [ ] Files uploaded and configured
- [ ] Database created and migrations run
- [ ] Default users created
- [ ] Static files serving correctly
- [ ] SSL certificate enabled
- [ ] Custom domain configured (optional)
- [ ] Backup procedures in place

---

## 📊 DASHBOARD REQUIREMENTS

### **Main Dashboard Layout:**
```
+----------------------------------------------------------+
|                SAKINA GAS COMPANY [LOGO]                |
+----------------------------------------------------------+
| Today's Attendance Overview - [DATE]                    |
+----------------------------------------------------------+
| HEAD OFFICE          | Present: [15] | Absent: [3]     |
+----------------------------------------------------------+
| DANDORA STATION      |                                |
| Day Shift            | Present: [8]  | Absent: [1]     |
| Night Shift          | Present: [7]  | Absent: [2]     |
+----------------------------------------------------------+
| TASSIA STATION       |                                |
| Day Shift            | Present: [9]  | Absent: [0]     |
| Night Shift          | Present: [8]  | Absent: [1]     |
+----------------------------------------------------------+
| KIAMBU STATION       |                                |
| Day Shift            | Present: [10] | Absent: [1]     |
| Night Shift          | Present: [9]  | Absent: [0]     |
+----------------------------------------------------------+
```

### **Detailed View (Clickable Numbers):**
- Employee list with status
- Filter options (All/Present/Absent/On Leave)
- Notes column for absence reasons
- Quick action buttons

---

## ⚖️ LEGAL COMPLIANCE FEATURES

### **Warning System:**
```javascript
// Example validation
if (paternity_days > 14) {
    showWarning("Kenyan law allows maximum 14 days paternity leave. Continue?");
}
```

### **Required Validations:**
- Annual leave: Max 21 days per year
- Maternity leave: Max 90 days (3 months)
- Paternity leave: Max 14 consecutive days
- Sick leave: Medical certificate required >7 days

### **HR Approval Interface:**
- View all leave details
- See remaining leave balances
- Add approval/rejection notes
- Override warnings with justification

---

## 🔧 MAINTENANCE & UPDATES

### **Regular Tasks:**
- Database backups (weekly)
- Log file rotation
- Performance monitoring
- Security updates
- User account reviews

### **Backup Strategy:**
- Daily database exports
- Weekly full system backup
- Monthly archive storage

---

## 📞 SUPPORT & TROUBLESHOOTING

### **Common Issues:**
1. **Login Problems**: Check user credentials in database
2. **Database Errors**: Verify file permissions
3. **Performance**: Monitor employee count limits
4. **Compliance**: Review warning system logs

### **Contact Information:**
- Development Support: [Contact Details]
- Legal Compliance: [HR Department]
- Technical Issues: [IT Support]

---

**Last Updated**: November 2025
**Version**: 1.0
**Status**: In Development

This manual should be referenced for continuity across multiple development sessions.
