// Notification Bell System
let notificationCheckInterval;

// Initialize notification system
function initNotifications() {
    loadNotifications();
    updateNotificationBadge();
    
    // Check for new notifications every 30 seconds
    notificationCheckInterval = setInterval(() => {
        updateNotificationBadge();
    }, 30000);
}

// Load and display notifications
async function loadNotifications() {
    try {
        const response = await fetch('/api/notifications/?limit=10');
        if (!response.ok) throw new Error('Failed to fetch notifications');
        
        const data = await response.json();
        displayNotifications(data.notifications);
        updateBadgeCount(data.unread_count);
    } catch (error) {
        console.error('Error loading notifications:', error);
    }
}

// Update notification badge count
async function updateNotificationBadge() {
    try {
        const response = await fetch('/api/notifications/?unread_only=true');
        if (!response.ok) return;
        
        const data = await response.json();
        updateBadgeCount(data.unread_count);
    } catch (error) {
        console.error('Error updating badge:', error);
    }
}

// Update badge count in UI
function updateBadgeCount(count) {
    const badge = document.querySelector('.notification-badge');
    if (badge) {
        if (count > 0) {
            badge.textContent = count > 99 ? '99+' : count;
            badge.style.display = 'flex';
        } else {
            badge.style.display = 'none';
        }
    }
}

// Display notifications in dropdown
function displayNotifications(notifications) {
    const container = document.getElementById('notificationDropdown');
    if (!container) return;
    
    if (notifications.length === 0) {
        container.innerHTML = `
            <div class="notification-empty">
                <p>No notifications</p>
            </div>
        `;
        return;
    }
    
    let html = '';
    notifications.forEach(notification => {
        const timeAgo = getTimeAgo(notification.created_at);
        const readClass = notification.is_read ? 'read' : 'unread';
        const typeClass = `notification-${notification.type}`;
        
        html += `
            <div class="notification-item ${readClass} ${typeClass}" 
                 data-id="${notification.id}"
                 onclick="handleNotificationClick(${notification.id}, '${notification.link || ''}')">
                <div class="notification-icon">
                    ${getNotificationIcon(notification.type)}
                </div>
                <div class="notification-content">
                    <div class="notification-title">${notification.title}</div>
                    <div class="notification-message">${notification.message}</div>
                    <div class="notification-time">${timeAgo}</div>
                </div>
                ${!notification.is_read ? '<div class="notification-unread-dot"></div>' : ''}
            </div>
        `;
    });
    
    container.innerHTML = html;
}

// Get icon for notification type
function getNotificationIcon(type) {
    const icons = {
        'success': '✓',
        'error': '✕',
        'warning': '⚠',
        'info': 'ℹ'
    };
    return icons[type] || 'ℹ';
}

// Handle notification click
async function handleNotificationClick(notificationId, link) {
    try {
        // Mark as read
        await fetch(`/api/notifications/${notificationId}/read`, {
            method: 'POST'
        });
        
        // Update UI
        const notificationEl = document.querySelector(`[data-id="${notificationId}"]`);
        if (notificationEl) {
            notificationEl.classList.remove('unread');
            notificationEl.classList.add('read');
            const dot = notificationEl.querySelector('.notification-unread-dot');
            if (dot) dot.remove();
        }
        
        // Update badge
        updateNotificationBadge();
        
        // Navigate if link provided
        if (link) {
            window.location.href = link;
        }
    } catch (error) {
        console.error('Error handling notification click:', error);
    }
}

// Mark all as read
async function markAllNotificationsRead() {
    try {
        const response = await fetch('/api/notifications/read-all', {
            method: 'POST'
        });
        
        if (response.ok) {
            // Update UI
            document.querySelectorAll('.notification-item.unread').forEach(item => {
                item.classList.remove('unread');
                item.classList.add('read');
                const dot = item.querySelector('.notification-unread-dot');
                if (dot) dot.remove();
            });
            
            updateBadgeCount(0);
            showToast('All notifications marked as read', 'success');
        }
    } catch (error) {
        console.error('Error marking all as read:', error);
        showToast('Failed to mark notifications as read', 'error');
    }
}

// Clear all notifications
async function clearAllNotifications() {
    if (!confirm('Are you sure you want to clear all notifications?')) return;
    
    try {
        const response = await fetch('/api/notifications/clear-all', {
            method: 'DELETE'
        });
        
        if (response.ok) {
            document.getElementById('notificationDropdown').innerHTML = `
                <div class="notification-empty">
                    <p>No notifications</p>
                </div>
            `;
            updateBadgeCount(0);
            showToast('All notifications cleared', 'success');
        }
    } catch (error) {
        console.error('Error clearing notifications:', error);
        showToast('Failed to clear notifications', 'error');
    }
}

// Toggle notification dropdown
function toggleNotificationDropdown() {
    const dropdown = document.getElementById('notificationDropdownContainer');
    if (!dropdown) return;
    
    const isVisible = dropdown.style.display === 'block';
    
    if (isVisible) {
        dropdown.style.display = 'none';
    } else {
        dropdown.style.display = 'block';
        loadNotifications();
    }
}

// Close dropdown when clicking outside
document.addEventListener('click', (e) => {
    const dropdown = document.getElementById('notificationDropdownContainer');
    const bell = document.querySelector('.notification-bell');
    
    if (dropdown && bell && !dropdown.contains(e.target) && !bell.contains(e.target)) {
        dropdown.style.display = 'none';
    }
});

// Get relative time
function getTimeAgo(timestamp) {
    const now = new Date();
    const time = new Date(timestamp);
    const diff = Math.floor((now - time) / 1000); // seconds
    
    if (diff < 60) return 'Just now';
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    if (diff < 604800) return `${Math.floor(diff / 86400)}d ago`;
    return time.toLocaleDateString();
}

// Auto-initialize on page load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initNotifications);
} else {
    initNotifications();
}
