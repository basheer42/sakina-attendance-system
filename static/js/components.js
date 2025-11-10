/*
Sakina Gas Company - UI Components JavaScript
Additional interactive components and utility functions
*/

// ========================================
// UI COMPONENTS LIBRARY
// ========================================
const SakinaUI = {
    // ========================================
    // TOAST NOTIFICATIONS
    // ========================================
    showToast(message, type = 'info', duration = 5000) {
        const toastContainer = this.getToastContainer();
        const toastId = 'toast-' + Date.now();
        
        const toastHTML = `
            <div class="toast fade show" id="${toastId}" role="alert" aria-live="assertive" aria-atomic="true">
                <div class="toast-header bg-${type} text-white">
                    <div class="icon-circle-sm me-2">
                        <i class="icon ${this.getToastIcon(type)}"></i>
                    </div>
                    <strong class="me-auto">Sakina Gas System</strong>
                    <small class="text-white-50">now</small>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast"></button>
                </div>
                <div class="toast-body">
                    ${message}
                </div>
            </div>
        `;
        
        toastContainer.insertAdjacentHTML('beforeend', toastHTML);
        
        // Auto remove after duration
        setTimeout(() => {
            const toastElement = document.getElementById(toastId);
            if (toastElement) {
                const bsToast = bootstrap.Toast.getInstance(toastElement);
                if (bsToast) {
                    bsToast.hide();
                }
                setTimeout(() => {
                    if (toastElement && toastElement.parentNode) {
                        toastElement.remove();
                    }
                }, 500);
            }
        }, duration);
        
        return toastId;
    },
    
    getToastContainer() {
        let container = document.getElementById('toastContainer');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toastContainer';
            container.className = 'toast-container position-fixed top-0 end-0 p-3';
            container.style.zIndex = '9999';
            document.body.appendChild(container);
        }
        return container;
    },
    
    getToastIcon(type) {
        const icons = {
            'success': 'icon-success',
            'warning': 'icon-warning',
            'danger': 'icon-error',
            'info': 'icon-info'
        };
        return icons[type] || 'icon-info';
    },

    // ========================================
    // LOADING STATES
    // ========================================
    showLoading(element, text = 'Loading...') {
        if (typeof element === 'string') {
            element = document.querySelector(element);
        }
        
        if (element) {
            element.classList.add('loading-state');
            const originalContent = element.innerHTML;
            element.dataset.originalContent = originalContent;
            
            element.innerHTML = `
                <div class="d-flex align-items-center justify-content-center">
                    <div class="loading-spinner me-2"></div>
                    <span>${text}</span>
                </div>
            `;
            element.disabled = true;
        }
    },
    
    hideLoading(element) {
        if (typeof element === 'string') {
            element = document.querySelector(element);
        }
        
        if (element && element.dataset.originalContent) {
            element.classList.remove('loading-state');
            element.innerHTML = element.dataset.originalContent;
            element.disabled = false;
            delete element.dataset.originalContent;
        }
    },

    // ========================================
    // CONFIRMATION DIALOGS
    // ========================================
    confirm(options) {
        const defaults = {
            title: 'Confirm Action',
            message: 'Are you sure you want to proceed?',
            confirmText: 'Confirm',
            cancelText: 'Cancel',
            confirmClass: 'btn-primary',
            cancelClass: 'btn-secondary',
            onConfirm: () => {},
            onCancel: () => {}
        };
        
        const config = { ...defaults, ...options };
        
        const modalHTML = `
            <div class="modal fade" id="confirmModal" tabindex="-1">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">${config.title}</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <p>${config.message}</p>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn ${config.cancelClass}" data-bs-dismiss="modal">
                                ${config.cancelText}
                            </button>
                            <button type="button" class="btn ${config.confirmClass}" id="confirmAction">
                                ${config.confirmText}
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Remove existing modal
        const existingModal = document.getElementById('confirmModal');
        if (existingModal) {
            existingModal.remove();
        }
        
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        
        const modal = new bootstrap.Modal(document.getElementById('confirmModal'));
        const confirmBtn = document.getElementById('confirmAction');
        
        confirmBtn.addEventListener('click', () => {
            modal.hide();
            config.onConfirm();
        });
        
        modal._element.addEventListener('hidden.bs.modal', () => {
            modal._element.remove();
            config.onCancel();
        });
        
        modal.show();
    },

    // ========================================
    // DYNAMIC TABLE UTILITIES
    // ========================================
    initializeDataTable(tableId, options = {}) {
        const table = document.getElementById(tableId);
        if (!table) return;
        
        const defaults = {
            searchable: true,
            sortable: true,
            pagination: true,
            pageSize: 10
        };
        
        const config = { ...defaults, ...options };
        
        if (config.searchable) {
            this.addTableSearch(table);
        }
        
        if (config.sortable) {
            this.addTableSort(table);
        }
        
        if (config.pagination) {
            this.addTablePagination(table, config.pageSize);
        }
    },
    
    addTableSearch(table) {
        const tableContainer = table.closest('.table-responsive') || table.parentNode;
        
        const searchHTML = `
            <div class="table-search mb-3">
                <div class="input-group">
                    <span class="input-group-text">
                        <i class="icon icon-search"></i>
                    </span>
                    <input type="text" class="form-control" placeholder="Search table...">
                </div>
            </div>
        `;
        
        tableContainer.insertAdjacentHTML('beforebegin', searchHTML);
        
        const searchInput = tableContainer.previousElementSibling.querySelector('input');
        searchInput.addEventListener('input', (e) => {
            const searchTerm = e.target.value.toLowerCase();
            const rows = table.querySelectorAll('tbody tr');
            
            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(searchTerm) ? '' : 'none';
            });
        });
    },
    
    addTableSort(table) {
        const headers = table.querySelectorAll('thead th');
        
        headers.forEach((header, index) => {
            if (header.dataset.sortable !== 'false') {
                header.style.cursor = 'pointer';
                header.classList.add('sortable');
                header.innerHTML += ' <span class="sort-indicator">⇅</span>';
                
                header.addEventListener('click', () => {
                    this.sortTable(table, index, header);
                });
            }
        });
    },
    
    sortTable(table, columnIndex, header) {
        const tbody = table.querySelector('tbody');
        const rows = Array.from(tbody.querySelectorAll('tr'));
        const isAscending = header.dataset.sortDirection !== 'asc';
        
        // Reset other headers
        table.querySelectorAll('th').forEach(th => {
            if (th !== header) {
                th.dataset.sortDirection = '';
                const indicator = th.querySelector('.sort-indicator');
                if (indicator) indicator.textContent = '⇅';
            }
        });
        
        // Set current header direction
        header.dataset.sortDirection = isAscending ? 'asc' : 'desc';
        const indicator = header.querySelector('.sort-indicator');
        if (indicator) {
            indicator.textContent = isAscending ? '↑' : '↓';
        }
        
        // Sort rows
        rows.sort((a, b) => {
            const aValue = a.cells[columnIndex].textContent.trim();
            const bValue = b.cells[columnIndex].textContent.trim();
            
            // Try to parse as numbers
            const aNum = parseFloat(aValue);
            const bNum = parseFloat(bValue);
            
            if (!isNaN(aNum) && !isNaN(bNum)) {
                return isAscending ? aNum - bNum : bNum - aNum;
            } else {
                return isAscending ? 
                    aValue.localeCompare(bValue) : 
                    bValue.localeCompare(aValue);
            }
        });
        
        // Re-append sorted rows
        rows.forEach(row => tbody.appendChild(row));
    },

    // ========================================
    // FORM UTILITIES
    // ========================================
    validateForm(formId) {
        const form = document.getElementById(formId);
        if (!form) return false;
        
        let isValid = true;
        const requiredFields = form.querySelectorAll('[required]');
        
        requiredFields.forEach(field => {
            this.clearFieldError(field);
            
            if (!field.value.trim()) {
                this.showFieldError(field, 'This field is required');
                isValid = false;
            }
        });
        
        // Email validation
        const emailFields = form.querySelectorAll('[type="email"]');
        emailFields.forEach(field => {
            if (field.value && !this.isValidEmail(field.value)) {
                this.showFieldError(field, 'Please enter a valid email address');
                isValid = false;
            }
        });
        
        // Phone validation
        const phoneFields = form.querySelectorAll('[type="tel"]');
        phoneFields.forEach(field => {
            if (field.value && !this.isValidPhone(field.value)) {
                this.showFieldError(field, 'Please enter a valid phone number');
                isValid = false;
            }
        });
        
        return isValid;
    },
    
    showFieldError(field, message) {
        field.classList.add('is-invalid');
        
        let errorElement = field.parentNode.querySelector('.invalid-feedback');
        if (!errorElement) {
            errorElement = document.createElement('div');
            errorElement.className = 'invalid-feedback';
            field.parentNode.appendChild(errorElement);
        }
        
        errorElement.textContent = message;
    },
    
    clearFieldError(field) {
        field.classList.remove('is-invalid');
        const errorElement = field.parentNode.querySelector('.invalid-feedback');
        if (errorElement) {
            errorElement.remove();
        }
    },
    
    isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    },
    
    isValidPhone(phone) {
        const phoneRegex = /^(\+254|0)[17]\d{8}$/; // Kenyan phone format
        return phoneRegex.test(phone.replace(/\s+/g, ''));
    },

    // ========================================
    // REAL-TIME UPDATES
    // ========================================
    startRealTimeUpdates() {
        // Update attendance counts every 30 seconds
        setInterval(() => {
            this.updateAttendanceCounts();
        }, 30000);
        
        // Update current time every second
        setInterval(() => {
            this.updateCurrentTime();
        }, 1000);
    },
    
    updateAttendanceCounts() {
        const countElements = document.querySelectorAll('[data-live-count]');
        
        countElements.forEach(element => {
            const endpoint = element.dataset.liveCount;
            fetch(endpoint)
                .then(response => response.json())
                .then(data => {
                    element.textContent = data.count;
                    
                    // Update parent card data attributes
                    const card = element.closest('.attendance-card');
                    if (card && data.count > 0) {
                        card.style.cursor = 'pointer';
                    }
                })
                .catch(error => {
                    console.error('Failed to update count:', error);
                });
        });
    },
    
    updateCurrentTime() {
        const timeElements = document.querySelectorAll('[data-live-time]');
        const now = new Date();
        
        timeElements.forEach(element => {
            const format = element.dataset.liveTime;
            let timeString;
            
            switch (format) {
                case 'time':
                    timeString = now.toLocaleTimeString('en-US', {
                        hour12: false,
                        timeZone: 'Africa/Nairobi'
                    });
                    break;
                case 'datetime':
                    timeString = now.toLocaleString('en-US', {
                        timeZone: 'Africa/Nairobi',
                        year: 'numeric',
                        month: 'long',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit',
                        hour12: false
                    }) + ' (GMT+3)';
                    break;
                case 'date':
                    timeString = now.toLocaleDateString('en-US', {
                        timeZone: 'Africa/Nairobi',
                        year: 'numeric',
                        month: 'long',
                        day: 'numeric'
                    });
                    break;
                default:
                    timeString = now.toLocaleTimeString();
            }
            
            element.textContent = timeString;
        });
    },

    // ========================================
    // MOBILE UTILITIES
    // ========================================
    isMobile() {
        return window.innerWidth <= 768;
    },
    
    setupMobileOptimizations() {
        if (this.isMobile()) {
            // Add mobile-specific classes
            document.body.classList.add('mobile-device');
            
            // Optimize table scrolling
            const tables = document.querySelectorAll('.table-responsive');
            tables.forEach(table => {
                table.style.overflowX = 'auto';
                table.style.webkitOverflowScrolling = 'touch';
            });
            
            // Add swipe gestures for navigation
            this.setupSwipeNavigation();
        }
    },
    
    setupSwipeNavigation() {
        let startX, startY;
        
        document.addEventListener('touchstart', (e) => {
            startX = e.touches[0].clientX;
            startY = e.touches[0].clientY;
        });
        
        document.addEventListener('touchend', (e) => {
            if (!startX || !startY) return;
            
            const endX = e.changedTouches[0].clientX;
            const endY = e.changedTouches[0].clientY;
            
            const deltaX = endX - startX;
            const deltaY = endY - startY;
            
            // Check if it's a horizontal swipe
            if (Math.abs(deltaX) > Math.abs(deltaY) && Math.abs(deltaX) > 50) {
                if (deltaX > 0) {
                    // Swipe right - go back
                    if (window.history.length > 1) {
                        window.history.back();
                    }
                }
            }
            
            startX = startY = null;
        });
    },

    // ========================================
    // ACCESSIBILITY HELPERS
    // ========================================
    announceToScreenReader(message) {
        const announcement = document.createElement('div');
        announcement.setAttribute('aria-live', 'polite');
        announcement.setAttribute('aria-atomic', 'true');
        announcement.classList.add('sr-only');
        announcement.textContent = message;
        
        document.body.appendChild(announcement);
        
        setTimeout(() => {
            document.body.removeChild(announcement);
        }, 1000);
    },
    
    setupKeyboardNavigation() {
        // Add keyboard navigation for cards
        const cards = document.querySelectorAll('.attendance-card, .dashboard-card');
        
        cards.forEach(card => {
            card.setAttribute('tabindex', '0');
            
            card.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    card.click();
                }
            });
        });
    }
};

// ========================================
// ENHANCED ATTENDANCE FEATURES
// ========================================
const AttendanceEnhancements = {
    // Quick attendance entry with barcode/RFID simulation
    setupQuickEntry() {
        const quickEntryInput = document.getElementById('quickEntryCode');
        if (quickEntryInput) {
            quickEntryInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    this.processQuickEntry(quickEntryInput.value);
                    quickEntryInput.value = '';
                }
            });
        }
    },
    
    processQuickEntry(code) {
        SakinaUI.showLoading('#quickEntryBtn', 'Processing...');
        
        // Simulate API call
        setTimeout(() => {
            SakinaUI.hideLoading('#quickEntryBtn');
            
            // Mock response - in real app, this would be an API call
            if (code.startsWith('EMP')) {
                SakinaUI.showToast(
                    `Employee ${code} clocked in successfully at ${new Date().toLocaleTimeString()}`,
                    'success'
                );
            } else {
                SakinaUI.showToast('Invalid employee code', 'warning');
            }
        }, 1500);
    },
    
    // Attendance summary with charts (using Chart.js if available)
    renderAttendanceChart(canvasId, data) {
        const canvas = document.getElementById(canvasId);
        if (!canvas || typeof Chart === 'undefined') return;
        
        new Chart(canvas, {
            type: 'doughnut',
            data: {
                labels: ['Present', 'Absent', 'Late', 'On Leave'],
                datasets: [{
                    data: [data.present, data.absent, data.late, data.leave],
                    backgroundColor: [
                        'var(--status-present)',
                        'var(--status-absent)',
                        'var(--status-late)',
                        'var(--status-leave)'
                    ],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }
};

// ========================================
// INITIALIZE ENHANCED UI
// ========================================
document.addEventListener('DOMContentLoaded', function() {
    // Initialize UI components
    SakinaUI.setupMobileOptimizations();
    SakinaUI.setupKeyboardNavigation();
    SakinaUI.startRealTimeUpdates();
    
    // Initialize attendance enhancements
    AttendanceEnhancements.setupQuickEntry();
    
    // Initialize data tables
    const dataTables = document.querySelectorAll('[data-table="enhanced"]');
    dataTables.forEach(table => {
        SakinaUI.initializeDataTable(table.id);
    });
    
    // Form validation on submit
    const forms = document.querySelectorAll('form[data-validate="true"]');
    forms.forEach(form => {
        form.addEventListener('submit', (e) => {
            if (!SakinaUI.validateForm(form.id)) {
                e.preventDefault();
                SakinaUI.showToast('Please fix the errors in the form', 'warning');
            }
        });
    });
    
    // Add click handlers for delete buttons
    document.addEventListener('click', (e) => {
        if (e.target.matches('.btn-delete') || e.target.closest('.btn-delete')) {
            e.preventDefault();
            
            const target = e.target.matches('.btn-delete') ? e.target : e.target.closest('.btn-delete');
            const itemName = target.dataset.itemName || 'this item';
            
            SakinaUI.confirm({
                title: 'Confirm Deletion',
                message: `Are you sure you want to delete ${itemName}? This action cannot be undone.`,
                confirmText: 'Delete',
                confirmClass: 'btn-danger',
                onConfirm: () => {
                    const form = target.closest('form');
                    if (form) {
                        form.submit();
                    } else {
                        window.location.href = target.href;
                    }
                }
            });
        }
    });
    
    console.log('🚀 Enhanced UI Components Initialized');
});

// Export for global access
window.SakinaUI = SakinaUI;
window.AttendanceEnhancements = AttendanceEnhancements;