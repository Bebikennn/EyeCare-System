// Utility Functions for EyeCare Admin Dashboard

// API Base URL
const API_BASE_URL = '/api';

let __csrfTokenCache = null;

async function getCsrfToken() {
    if (__csrfTokenCache) return __csrfTokenCache;

    try {
        const resp = await fetch(`${API_BASE_URL}/csrf-token`, {
            method: 'GET',
            credentials: 'same-origin',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (!resp.ok) {
            // If unauthenticated or endpoint unavailable, fall back to null.
            return null;
        }

        const data = await resp.json();
        __csrfTokenCache = data.csrf_token || null;
        return __csrfTokenCache;
    } catch (e) {
        return null;
    }
}

// Show loading spinner
function showLoading(containerId) {
    const container = document.getElementById(containerId);
    if (container) {
        container.innerHTML = '<div class="spinner"></div>';
    }
}

// Hide loading spinner
function hideLoading(containerId) {
    const container = document.getElementById(containerId);
    if (container) {
        container.innerHTML = '';
    }
}

// Show alert message
function showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} fade-in`;
    alertDiv.innerHTML = `
        <i class="material-icons">${getAlertIcon(type)}</i>
        <span>${message}</span>
        <button onclick="this.parentElement.remove()" style="margin-left: auto; background: none; border: none; cursor: pointer;">
            <i class="material-icons">close</i>
        </button>
    `;
    alertDiv.style.display = 'flex';
    
    const contentArea = document.querySelector('.content-area');
    if (contentArea) {
        contentArea.insertBefore(alertDiv, contentArea.firstChild);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            alertDiv.remove();
        }, 5000);
    }
}

// Toast notifications (non-blocking)
function showToast(message, type = 'info', timeoutMs = 4000) {
    let container = document.getElementById('toastContainer');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toastContainer';
        container.className = 'toast-container';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
        <i class="material-icons">${getAlertIcon(type)}</i>
        <span class="toast-message">${message}</span>
        <button class="toast-close" aria-label="Close" type="button">
            <i class="material-icons">close</i>
        </button>
    `;

    const closeBtn = toast.querySelector('.toast-close');
    if (closeBtn) {
        closeBtn.addEventListener('click', () => toast.remove());
    }

    container.appendChild(toast);

    if (timeoutMs && timeoutMs > 0) {
        setTimeout(() => {
            toast.remove();
        }, timeoutMs);
    }
}

function getAlertIcon(type) {
    const icons = {
        success: 'check_circle',
        error: 'error',
        warning: 'warning',
        info: 'info'
    };
    return icons[type] || 'info';
}

// API Request Helper
async function apiRequest(endpoint, options = {}) {
    try {
        const method = (options.method || 'GET').toUpperCase();
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers
        };

        // Attach CSRF token for unsafe methods
        if (!['GET', 'HEAD', 'OPTIONS'].includes(method)) {
            const csrfToken = await getCsrfToken();
            if (csrfToken) {
                headers['X-CSRFToken'] = csrfToken;
                headers['X-CSRF-Token'] = csrfToken;
            }
        }

        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            ...options,
            headers,
            credentials: options.credentials || 'same-origin'
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Request failed');
        }
        
        return data;
    } catch (error) {
        console.error('API Error:', error);
        showToast(error.message, 'error');
        throw error;
    }
}

// Format date
function formatDate(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

// Format datetime
function formatDateTime(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Format time ago
function timeAgo(dateString) {
    if (!dateString) return 'N/A';
    
    const now = new Date();
    const date = new Date(dateString);
    const seconds = Math.floor((now - date) / 1000);
    
    const intervals = {
        year: 31536000,
        month: 2592000,
        week: 604800,
        day: 86400,
        hour: 3600,
        minute: 60,
        second: 1
    };
    
    for (const [unit, secondsInUnit] of Object.entries(intervals)) {
        const interval = Math.floor(seconds / secondsInUnit);
        if (interval >= 1) {
            return `${interval} ${unit}${interval !== 1 ? 's' : ''} ago`;
        }
    }
    
    return 'Just now';
}

// Toggle sidebar
function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    if (sidebar) {
        sidebar.classList.toggle('active');
    }
}

// Close sidebar on mobile when clicking outside
document.addEventListener('click', (e) => {
    const sidebar = document.querySelector('.sidebar');
    const menuToggle = document.querySelector('.menu-toggle');
    
    if (window.innerWidth <= 768) {
        if (sidebar && !sidebar.contains(e.target) && !menuToggle.contains(e.target)) {
            sidebar.classList.remove('active');
        }
    }
});

// Set active menu item
function setActiveMenuItem() {
    const path = window.location.pathname;
    const menuItems = document.querySelectorAll('.sidebar-menu a');
    
    menuItems.forEach(item => {
        item.classList.remove('active');
        if (item.getAttribute('href') === path) {
            item.classList.add('active');
        }
    });
}

// Modal functions
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'flex';
        document.body.style.overflow = 'hidden';
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = 'auto';
    }
}

// Close modal when clicking outside
window.addEventListener('click', (e) => {
    if (e.target.classList.contains('modal-overlay')) {
        e.target.style.display = 'none';
        document.body.style.overflow = 'auto';
    }
});

// Confirm dialog
function confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

// Debounce function
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Search functionality
function initSearch(inputId, callback) {
    const input = document.getElementById(inputId);
    if (!input) return;
    
    const debouncedCallback = debounce(callback, 300);
    
    input.addEventListener('input', (e) => {
        debouncedCallback(e.target.value);
    });
}

// Pagination
function renderPagination(containerId, currentPage, totalPages, onPageChange) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    let html = '<div class="pagination">';
    
    // Previous button
    html += `<button ${currentPage === 1 ? 'disabled' : ''} onclick="${onPageChange}(${currentPage - 1})">
        <i class="material-icons">chevron_left</i>
    </button>`;
    
    // Page numbers
    const maxVisible = 5;
    let startPage = Math.max(1, currentPage - Math.floor(maxVisible / 2));
    let endPage = Math.min(totalPages, startPage + maxVisible - 1);
    
    if (endPage - startPage < maxVisible - 1) {
        startPage = Math.max(1, endPage - maxVisible + 1);
    }
    
    if (startPage > 1) {
        html += `<button onclick="${onPageChange}(1)">1</button>`;
        if (startPage > 2) {
            html += '<span>...</span>';
        }
    }
    
    for (let i = startPage; i <= endPage; i++) {
        html += `<button class="${i === currentPage ? 'active' : ''}" onclick="${onPageChange}(${i})">${i}</button>`;
    }
    
    if (endPage < totalPages) {
        if (endPage < totalPages - 1) {
            html += '<span>...</span>';
        }
        html += `<button onclick="${onPageChange}(${totalPages})">${totalPages}</button>`;
    }
    
    // Next button
    html += `<button ${currentPage === totalPages ? 'disabled' : ''} onclick="${onPageChange}(${currentPage + 1})">
        <i class="material-icons">chevron_right</i>
    </button>`;
    
    html += '</div>';
    container.innerHTML = html;
}

// Export table to CSV
function exportTableToCSV(tableId, filename = 'data.csv') {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    let csv = [];
    const rows = table.querySelectorAll('tr');
    
    rows.forEach(row => {
        const cells = row.querySelectorAll('th, td');
        const rowData = Array.from(cells).map(cell => {
            let text = cell.textContent.trim();
            // Escape quotes
            text = text.replace(/"/g, '""');
            return `"${text}"`;
        });
        csv.push(rowData.join(','));
    });
    
    // Download
    const blob = new Blob([csv.join('\n')], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    window.URL.revokeObjectURL(url);
}

// User menu (profile dropdown)
function _getUserMenuEls() {
    const toggle = document.getElementById('userMenuToggle');
    const dropdown = document.getElementById('userMenuDropdown');
    const container = document.getElementById('userMenu');
    return { toggle, dropdown, container };
}

function openUserMenu() {
    const { toggle, dropdown } = _getUserMenuEls();
    if (!toggle || !dropdown) return;
    dropdown.style.display = 'block';
    toggle.setAttribute('aria-expanded', 'true');
}

function closeUserMenu() {
    const { toggle, dropdown } = _getUserMenuEls();
    if (!toggle || !dropdown) return;
    dropdown.style.display = 'none';
    toggle.setAttribute('aria-expanded', 'false');
}

function toggleUserMenu(event) {
    if (event) event.stopPropagation();
    const { dropdown } = _getUserMenuEls();
    if (!dropdown) return;
    const isOpen = dropdown.style.display !== 'none' && dropdown.style.display !== '';
    if (isOpen) {
        closeUserMenu();
    } else {
        openUserMenu();
    }
}

document.addEventListener('click', (e) => {
    const { container, dropdown } = _getUserMenuEls();
    if (!container || !dropdown) return;
    if (dropdown.style.display === 'none' || dropdown.style.display === '') return;
    if (!container.contains(e.target)) {
        closeUserMenu();
    }
});

document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        closeUserMenu();
    }
});

// Logout
async function logout() {
    try {
        closeUserMenu();
        await apiRequest('/auth/logout', { method: 'POST' });
        window.location.href = '/login';
    } catch (error) {
        console.error('Logout error:', error);
    }
}

// Check session
async function checkSession() {
    try {
        const data = await apiRequest('/auth/check-session');
        if (!data.authenticated) {
            window.location.href = '/login';
        }
        if (data.admin && data.admin.role) {
            sessionStorage.setItem('role', data.admin.role);
        }
        // Update navbar with user info
        updateNavbarProfile(data.admin);
        return data.admin;
    } catch (error) {
        window.location.href = '/login';
    }
}

// Update navbar profile display
function updateNavbarProfile(admin) {
    if (!admin) return;
    
    // Update avatar initial
    const avatar = document.querySelector('.user-avatar');
    if (avatar) {
        avatar.textContent = admin.username ? admin.username.charAt(0).toUpperCase() : 'A';
    }
    
    // Update name
    const nameElement = document.querySelector('.user-info .name');
    if (nameElement) {
        nameElement.textContent = admin.full_name || admin.username || 'Admin';
    }
    
    // Update role with proper formatting
    const roleElement = document.querySelector('.user-info .role');
    if (roleElement) {
        const roleMap = {
            'super_admin': 'Super Admin',
            'admin': 'Admin',
            'data_analyst': 'Data Analyst',
            'staff': 'Staff'
        };
        roleElement.textContent = roleMap[admin.role] || admin.role;
    }
    
    // Update sidebar based on role
    updateSidebarForRole(admin.role);
}

// Update sidebar menu based on user role
function updateSidebarForRole(role) {
    // Normalize role (legacy compatibility)
    const normalizedRole = role === 'analyst' ? 'data_analyst' : role;

    const allowedByRole = {
        staff: new Set(['/dashboard', '/healthtips', '/my-requests', '/settings']),
        data_analyst: new Set(['/dashboard', '/assessments', '/ml-analytics', '/my-requests', '/settings']),
        admin: null, // all
        super_admin: null // all
    };

    const allowedSet = allowedByRole[normalizedRole] ?? null;

    // Toggle visibility of sidebar links
    const sidebarLinks = document.querySelectorAll('.sidebar-menu a[href^="/"]');
    sidebarLinks.forEach(a => {
        const href = a.getAttribute('href');
        if (!href) return;

        const li = a.parentElement;
        if (!li) return;

        if (!allowedSet) {
            li.style.display = 'block';
            return;
        }

        li.style.display = allowedSet.has(href) ? 'block' : 'none';
    });

    // Approvals vs My Requests
    const approvalsLink = document.querySelector('a[href="/approvals"]');
    const myRequestsLink = document.querySelector('a[href="/my-requests"]');

    if (normalizedRole === 'admin' || normalizedRole === 'super_admin') {
        if (approvalsLink && approvalsLink.parentElement) approvalsLink.parentElement.style.display = 'block';
        if (myRequestsLink && myRequestsLink.parentElement) myRequestsLink.parentElement.style.display = 'block';
    } else {
        if (approvalsLink && approvalsLink.parentElement) approvalsLink.parentElement.style.display = 'none';
        if (myRequestsLink && myRequestsLink.parentElement) myRequestsLink.parentElement.style.display = 'block';
    }
}

function getCurrentRole() {
    const role = sessionStorage.getItem('role');
    return role === 'analyst' ? 'data_analyst' : role;
}

function isSuperAdmin() {
    return getCurrentRole() === 'super_admin';
}

// Form validation
function validateForm(formId) {
    const form = document.getElementById(formId);
    if (!form) return false;
    
    const inputs = form.querySelectorAll('input[required], textarea[required], select[required]');
    let isValid = true;
    
    inputs.forEach(input => {
        if (!input.value.trim()) {
            input.style.borderColor = 'var(--red)';
            isValid = false;
        } else {
            input.style.borderColor = 'var(--gray-300)';
        }
    });
    
    return isValid;
}

// Copy to clipboard
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showAlert('Copied to clipboard!', 'success');
    }).catch(err => {
        console.error('Failed to copy:', err);
        showAlert('Failed to copy', 'error');
    });
}

// Number formatting
function formatNumber(num) {
    return new Intl.NumberFormat('en-US').format(num);
}

// Percentage formatting
function formatPercentage(value) {
    return (value * 100).toFixed(2) + '%';
}

// Initialize tooltips (if using a tooltip library)
function initTooltips() {
    const elements = document.querySelectorAll('[data-tooltip]');
    elements.forEach(element => {
        element.addEventListener('mouseenter', (e) => {
            const tooltip = document.createElement('div');
            tooltip.className = 'tooltip';
            tooltip.textContent = e.target.getAttribute('data-tooltip');
            document.body.appendChild(tooltip);
            
            const rect = e.target.getBoundingClientRect();
            tooltip.style.top = (rect.top - tooltip.offsetHeight - 8) + 'px';
            tooltip.style.left = (rect.left + rect.width / 2 - tooltip.offsetWidth / 2) + 'px';
        });
        
        element.addEventListener('mouseleave', () => {
            const tooltip = document.querySelector('.tooltip');
            if (tooltip) tooltip.remove();
        });
    });
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    setActiveMenuItem();
    initTooltips();
});
