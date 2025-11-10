/*
Sakina Gas Company - Professional Attendance Management System
Custom JavaScript - Interactive Features & Kenyan Labor Law Compliance
*/

// ========================================
// KENYAN LABOR LAW CONSTANTS
// ========================================
const KENYAN_LABOR_LAWS = {
    annual_leave: {
        max_days: 21,
        description: 'Annual Leave (Employment Act 2007)',
        warning: 'Maximum 21 working days per year as per Kenyan Employment Act 2007'
    },
    sick_leave: {
        max_days: 7,
        description: 'Sick Leave (Without Medical Certificate)',
        warning: 'More than 7 days requires medical certificate as per Employment Act 2007'
    },
    maternity_leave: {
        max_days: 90,
        description: 'Maternity Leave',
        warning: 'Maximum 90 days (3 months) as per Kenyan Employment Act 2007'
    },
    paternity_leave: {
        max_days: 14,
        description: 'Paternity Leave',
        warning: 'Maximum 14 consecutive days as per Kenyan Employment Act 2007'
    },
    compassionate_leave: {
        max_days: 7,
        description: 'Compassionate/Bereavement Leave',
        warning: 'Typically up to 7 days for family bereavement'
    }
};

// ========================================
// MAIN APPLICATION OBJECT
// ========================================
const SakinaAttendanceApp = {
    // Initialize the application
    init() {
        this.setupEventListeners();
        this.initializeTooltips();
        this.setupFormValidation();
        this.initializeDatePickers();
        this.setupLiveSearch();
        this.updateDateTime();
        
        // Update date/time every minute
        setInterval(() => this.updateDateTime(), 60000);
        
        console.log('🏢 Sakina Gas Attendance System Initialized');
    },

    // ========================================
    // EVENT LISTENERS SETUP
    // ========================================
    setupEventListeners() {
        // Attendance card clicks for details
        document.querySelectorAll('.attendance-card').forEach(card => {
            card.addEventListener('click', this.handleAttendanceCardClick);
        });

        // Quick action buttons
        document.querySelectorAll('.quick-action-btn').forEach(btn => {
            btn.addEventListener('click', this.handleQuickAction);
        });

        // Leave form submission
        const leaveForm = document.getElementById('leaveRequestForm');
        if (leaveForm) {
            leaveForm.addEventListener('submit', this.handleLeaveSubmission.bind(this));
        }

        // Employee form validation
        const employeeForm = document.getElementById('employeeForm');
        if (employeeForm) {
            employeeForm.addEventListener('submit', this.handleEmployeeSubmission.bind(this));
        }

        // Location change handler
        const locationSelect = document.getElementById('location');
        if (locationSelect) {
            locationSelect.addEventListener('change', this.handleLocationChange.bind(this));
        }

        // Attendance form handlers
        const clockInBtn = document.getElementById('clockInBtn');
        const clockOutBtn = document.getElementById('clockOutBtn');
        if (clockInBtn) clockInBtn.addEventListener('click', this.handleClockIn.bind(this));
        if (clockOutBtn) clockOutBtn.addEventListener('click', this.handleClockOut.bind(this));
    },

    // ========================================
    // ATTENDANCE CARD INTERACTIONS
    // ========================================
    handleAttendanceCardClick(event) {
        const card = event.currentTarget;
        const location = card.dataset.location;
        const status = card.dataset.status;
        const count = card.querySelector('.attendance-number').textContent;

        if (parseInt(count) > 0) {
            // Show attendance details modal
            SakinaAttendanceApp.showAttendanceDetails(location, status, count);
        }
    },

    showAttendanceDetails(location, status, count) {
        // Create and show modal with attendance details
        const modalHTML = `
            <div class="modal fade" id="attendanceDetailsModal" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">
                                ${status.charAt(0).toUpperCase() + status.slice(1)} Employees - ${location}
                            </h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <p>Loading ${count} ${status} employees from ${location}...</p>
                            <div class="text-center">
                                <div class="loading-spinner"></div>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Remove existing modal if any
        const existingModal = document.getElementById('attendanceDetailsModal');
        if (existingModal) {
            existingModal.remove();
        }

        // Add modal to page
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        
        // Show modal
        const modal = new bootstrap.Modal(document.getElementById('attendanceDetailsModal'));
        modal.show();

        // Load actual data (would be an AJAX call in real implementation)
        setTimeout(() => {
            this.loadAttendanceDetails(location, status);
        }, 1000);
    },

    loadAttendanceDetails(location, status) {
        // This would make an AJAX call to get actual attendance details
        // For now, we'll simulate the data
        const mockData = this.generateMockAttendanceData(location, status);
        
        const modalBody = document.querySelector('#attendanceDetailsModal .modal-body');
        modalBody.innerHTML = `
            <div class="table-responsive">
                <table class="table table-custom">
                    <thead>
                        <tr>
                            <th>Employee ID</th>
                            <th>Name</th>
                            <th>Time</th>
                            <th>Status</th>
                            <th>Notes</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${mockData.map(emp => `
                            <tr>
                                <td>${emp.id}</td>
                                <td>${emp.name}</td>
                                <td>${emp.time}</td>
                                <td><span class="status-badge status-${emp.status}">${emp.status}</span></td>
                                <td>${emp.notes}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
    },

    generateMockAttendanceData(location, status) {
        // Mock data for demonstration
        const employees = [
            { id: 'EMP001', name: 'John Kamau', time: '08:00', status: status, notes: status === 'late' ? 'Traffic jam' : '-' },
            { id: 'EMP002', name: 'Mary Wanjiku', time: '08:15', status: status, notes: status === 'absent' ? 'Sick' : '-' },
            { id: 'EMP003', name: 'Peter Mwangi', time: '07:45', status: status, notes: '-' }
        ];
        return employees.slice(0, Math.min(3, Math.random() * 3 + 1));
    },

    // ========================================
    // LEAVE REQUEST VALIDATION
    // ========================================
    handleLeaveSubmission(event) {
        event.preventDefault();
        
        const form = event.target;
        const formData = new FormData(form);
        
        const leaveType = formData.get('leave_type');
        const startDate = new Date(formData.get('start_date'));
        const endDate = new Date(formData.get('end_date'));
        const days = this.calculateLeaveDays(startDate, endDate);
        
        // Validate against Kenyan labor laws
        const validation = this.validateLeaveRequest(leaveType, days);
        
        if (!validation.isValid) {
            this.showWarningModal(validation);
            return false;
        }
        
        // If validation passes, show confirmation
        this.showConfirmationModal(leaveType, days, () => {
            form.submit();
        });
        
        return false;
    },

    calculateLeaveDays(startDate, endDate) {
        const timeDiff = endDate.getTime() - startDate.getTime();
        const dayDiff = Math.ceil(timeDiff / (1000 * 3600 * 24)) + 1; // Include both start and end days
        return dayDiff;
    },

    validateLeaveRequest(leaveType, requestedDays) {
        const lawInfo = KENYAN_LABOR_LAWS[leaveType];
        
        if (!lawInfo) {
            return { isValid: true };
        }

        if (requestedDays > lawInfo.max_days) {
            return {
                isValid: false,
                type: 'violation',
                message: `⚠️ KENYAN LABOR LAW VIOLATION\n\n${lawInfo.warning}\n\nRequested: ${requestedDays} days\nMaximum Allowed: ${lawInfo.max_days} days\n\nThis request exceeds legal limits and requires special HR approval.`,
                lawReference: lawInfo.description
            };
        }

        if (requestedDays > lawInfo.max_days * 0.8) {
            return {
                isValid: false,
                type: 'warning',
                message: `⚠️ HIGH LEAVE REQUEST WARNING\n\nRequested: ${requestedDays} days\nLegal Maximum: ${lawInfo.max_days} days\n\nThis request is approaching the legal limit. Please ensure this is necessary.`,
                lawReference: lawInfo.description
            };
        }

        return { isValid: true };
    },

    showWarningModal(validation) {
        const modalHTML = `
            <div class="modal fade" id="leaveWarningModal" tabindex="-1">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header bg-warning text-dark">
                            <h5 class="modal-title">
                                <i class="fas fa-exclamation-triangle"></i>
                                ${validation.type === 'violation' ? 'Legal Violation Detected' : 'Leave Warning'}
                            </h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div class="alert ${validation.type === 'violation' ? 'alert-danger' : 'alert-warning'}">
                                ${validation.message.split('\n').join('<br>')}
                            </div>
                            <p><strong>Reference:</strong> ${validation.lawReference}</p>
                            ${validation.type === 'violation' ? 
                                '<p class="text-muted"><small>HR Manager can override this with proper justification.</small></p>' : 
                                ''
                            }
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel Request</button>
                            ${validation.type === 'violation' ? 
                                '<button type="button" class="btn btn-danger" id="overrideSubmit">Submit Anyway (HR Override)</button>' :
                                '<button type="button" class="btn btn-warning" id="warningSubmit">Continue Anyway</button>'
                            }
                        </div>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHTML);
        const modal = new bootstrap.Modal(document.getElementById('leaveWarningModal'));
        modal.show();

        // Handle override/continue button
        const overrideBtn = document.getElementById('overrideSubmit') || document.getElementById('warningSubmit');
        if (overrideBtn) {
            overrideBtn.addEventListener('click', () => {
                modal.hide();
                document.getElementById('leaveRequestForm').submit();
            });
        }

        // Cleanup modal after hiding
        modal._element.addEventListener('hidden.bs.modal', () => {
            modal._element.remove();
        });
    },

    showConfirmationModal(leaveType, days, onConfirm) {
        const modalHTML = `
            <div class="modal fade" id="leaveConfirmModal" tabindex="-1">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header bg-success text-white">
                            <h5 class="modal-title">
                                <i class="fas fa-check-circle"></i>
                                Confirm Leave Request
                            </h5>
                            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <p>Please confirm your leave request:</p>
                            <ul>
                                <li><strong>Type:</strong> ${leaveType.replace('_', ' ').toUpperCase()}</li>
                                <li><strong>Duration:</strong> ${days} days</li>
                                <li><strong>Status:</strong> Compliant with Kenyan Labor Laws ✅</li>
                            </ul>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                            <button type="button" class="btn btn-success" id="confirmSubmit">Submit Request</button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHTML);
        const modal = new bootstrap.Modal(document.getElementById('leaveConfirmModal'));
        modal.show();

        document.getElementById('confirmSubmit').addEventListener('click', () => {
            modal.hide();
            onConfirm();
        });

        modal._element.addEventListener('hidden.bs.modal', () => {
            modal._element.remove();
        });
    },

    // ========================================
    // EMPLOYEE FORM VALIDATION
    // ========================================
    handleEmployeeSubmission(event) {
        const form = event.target;
        const formData = new FormData(form);
        
        // Validate employee ID format
        const employeeId = formData.get('employee_id');
        if (!this.validateEmployeeId(employeeId)) {
            this.showAlert('Please enter a valid Employee ID (e.g., EMP001, SKN001)', 'danger');
            event.preventDefault();
            return false;
        }

        // Validate required fields
        const requiredFields = ['first_name', 'last_name', 'location', 'department', 'position'];
        for (const field of requiredFields) {
            if (!formData.get(field) || formData.get(field).trim() === '') {
                this.showAlert(`Please fill in the ${field.replace('_', ' ')} field`, 'danger');
                event.preventDefault();
                return false;
            }
        }

        return true;
    },

    validateEmployeeId(employeeId) {
        // Employee ID should be alphanumeric and 3-10 characters
        const regex = /^[A-Z0-9]{3,10}$/;
        return regex.test(employeeId);
    },

    // ========================================
    // LOCATION CHANGE HANDLER
    // ========================================
    handleLocationChange(event) {
        const location = event.target.value;
        const shiftContainer = document.getElementById('shiftContainer');
        
        if (location === 'head_office') {
            shiftContainer.style.display = 'none';
            document.getElementById('shift').removeAttribute('required');
        } else {
            shiftContainer.style.display = 'block';
            document.getElementById('shift').setAttribute('required', 'required');
        }
    },

    // ========================================
    // CLOCK IN/OUT HANDLERS
    // ========================================
    handleClockIn(event) {
        event.preventDefault();
        const employeeSelect = document.getElementById('employee_id');
        const selectedEmployee = employeeSelect.value;
        
        if (!selectedEmployee) {
            this.showAlert('Please select an employee', 'warning');
            return;
        }

        // Get employee info from the select option
        const selectedOption = employeeSelect.options[employeeSelect.selectedIndex];
        const employeeName = selectedOption.text;
        
        // Show confirmation modal
        this.showClockInConfirmation(selectedEmployee, employeeName);
    },

    handleClockOut(event) {
        event.preventDefault();
        const employeeSelect = document.getElementById('employee_id');
        const selectedEmployee = employeeSelect.value;
        
        if (!selectedEmployee) {
            this.showAlert('Please select an employee', 'warning');
            return;
        }

        const selectedOption = employeeSelect.options[employeeSelect.selectedIndex];
        const employeeName = selectedOption.text;
        
        this.showClockOutConfirmation(selectedEmployee, employeeName);
    },

    showClockInConfirmation(employeeId, employeeName) {
        const now = new Date();
        const timeString = now.toLocaleTimeString('en-US', { 
            hour12: false, 
            timeZone: 'Africa/Nairobi'
        });

        const modalHTML = `
            <div class="modal fade" id="clockInModal" tabindex="-1">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header bg-success text-white">
                            <h5 class="modal-title">
                                <i class="fas fa-clock"></i>
                                Clock In Confirmation
                            </h5>
                            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <p><strong>Employee:</strong> ${employeeName}</p>
                            <p><strong>Clock In Time:</strong> ${timeString} (GMT+3)</p>
                            <p><strong>Date:</strong> ${now.toLocaleDateString()}</p>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                            <button type="button" class="btn btn-success" id="confirmClockIn">Confirm Clock In</button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHTML);
        const modal = new bootstrap.Modal(document.getElementById('clockInModal'));
        modal.show();

        document.getElementById('confirmClockIn').addEventListener('click', () => {
            // Submit the clock in form
            document.getElementById('clockInForm').submit();
        });

        modal._element.addEventListener('hidden.bs.modal', () => {
            modal._element.remove();
        });
    },

    showClockOutConfirmation(employeeId, employeeName) {
        // Similar to clock in but for clock out
        const now = new Date();
        const timeString = now.toLocaleTimeString('en-US', { 
            hour12: false, 
            timeZone: 'Africa/Nairobi'
        });

        const modalHTML = `
            <div class="modal fade" id="clockOutModal" tabindex="-1">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header bg-warning text-dark">
                            <h5 class="modal-title">
                                <i class="fas fa-clock"></i>
                                Clock Out Confirmation
                            </h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <p><strong>Employee:</strong> ${employeeName}</p>
                            <p><strong>Clock Out Time:</strong> ${timeString} (GMT+3)</p>
                            <p><strong>Date:</strong> ${now.toLocaleDateString()}</p>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                            <button type="button" class="btn btn-warning" id="confirmClockOut">Confirm Clock Out</button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHTML);
        const modal = new bootstrap.Modal(document.getElementById('clockOutModal'));
        modal.show();

        document.getElementById('confirmClockOut').addEventListener('click', () => {
            document.getElementById('clockOutForm').submit();
        });

        modal._element.addEventListener('hidden.bs.modal', () => {
            modal._element.remove();
        });
    },

    // ========================================
    // UTILITY FUNCTIONS
    // ========================================
    initializeTooltips() {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    },

    setupFormValidation() {
        // Add Bootstrap validation classes
        const forms = document.querySelectorAll('.needs-validation');
        forms.forEach(form => {
            form.addEventListener('submit', event => {
                if (!form.checkValidity()) {
                    event.preventDefault();
                    event.stopPropagation();
                }
                form.classList.add('was-validated');
            }, false);
        });
    },

    initializeDatePickers() {
        // Set minimum date for leave requests to today
        const dateInputs = document.querySelectorAll('input[type="date"]');
        const today = new Date().toISOString().split('T')[0];
        
        dateInputs.forEach(input => {
            if (input.id === 'start_date' || input.id === 'end_date') {
                input.min = today;
            }
        });

        // Auto-update end date when start date changes
        const startDateInput = document.getElementById('start_date');
        const endDateInput = document.getElementById('end_date');
        
        if (startDateInput && endDateInput) {
            startDateInput.addEventListener('change', () => {
                endDateInput.min = startDateInput.value;
                if (endDateInput.value && endDateInput.value < startDateInput.value) {
                    endDateInput.value = startDateInput.value;
                }
            });
        }
    },

    setupLiveSearch() {
        const searchInputs = document.querySelectorAll('.live-search');
        searchInputs.forEach(input => {
            input.addEventListener('input', this.handleLiveSearch.bind(this));
        });
    },

    handleLiveSearch(event) {
        const searchTerm = event.target.value.toLowerCase();
        const targetTable = document.querySelector(event.target.dataset.target);
        
        if (targetTable) {
            const rows = targetTable.querySelectorAll('tbody tr');
            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(searchTerm) ? '' : 'none';
            });
        }
    },

    updateDateTime() {
        const dateTimeElement = document.getElementById('currentDateTime');
        if (dateTimeElement) {
            const now = new Date();
            const options = {
                timeZone: 'Africa/Nairobi',
                year: 'numeric',
                month: 'long',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
                hour12: false
            };
            dateTimeElement.textContent = now.toLocaleDateString('en-US', options) + ' (GMT+3)';
        }
    },

    handleQuickAction(event) {
        const action = event.target.dataset.action;
        switch (action) {
            case 'mark_attendance':
                window.location.href = '/attendance/mark';
                break;
            case 'add_employee':
                window.location.href = '/employees/add';
                break;
            case 'request_leave':
                window.location.href = '/leaves/request';
                break;
            case 'view_reports':
                window.location.href = '/reports';
                break;
        }
    },

    showAlert(message, type = 'info') {
        const alertHTML = `
            <div class="alert alert-${type} alert-dismissible fade show" role="alert">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        // Insert at the top of the main content
        const mainContent = document.querySelector('.main-content');
        if (mainContent) {
            mainContent.insertAdjacentHTML('afterbegin', alertHTML);
        }
    }
};

// ========================================
// INITIALIZE APPLICATION WHEN DOM IS READY
// ========================================
document.addEventListener('DOMContentLoaded', function() {
    SakinaAttendanceApp.init();
});

// ========================================
// GLOBAL FUNCTIONS FOR TEMPLATE USE
// ========================================
window.SakinaAttendanceApp = SakinaAttendanceApp;

// Export for potential module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SakinaAttendanceApp;
}