// Global application JavaScript

// Socket.IO connection management
let socket = null;

function initializeSocketConnection() {
    try {
        socket = io();

        socket.on('connect', () => {
            console.log('Connected to server');
            updateConnectionStatus(true);
        });

        socket.on('disconnect', () => {
            console.log('Disconnected from server');
            updateConnectionStatus(false);
        });

        socket.on('server_status', (data) => {
            updateServerStatus(data.status);
        });

        socket.on('connections_update', (data) => {
            if (typeof updateConnectionsList === 'function') {
                updateConnectionsList(data.connections);
            }
        });

    } catch (error) {
        console.error('Failed to initialize socket connection:', error);
    }
}

function updateConnectionStatus(connected) {
    const statusElement = document.getElementById('connectionStatus');
    if (statusElement) {
        statusElement.textContent = connected ? 'Connected' : 'Disconnected';
        statusElement.className = connected ? 'status-connected' : 'status-disconnected';
    }
}

function updateServerStatus(status) {
    // Update server status across the application
    const elements = document.querySelectorAll('.server-status-indicator');
    elements.forEach(element => {
        element.textContent = status;
        element.className = `server-status-indicator status-${status}`;
    });
}

// Utility functions
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString();
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function showToast(message, type = 'info') {
    // Simple toast notification implementation
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 12px 20px;
        background: ${type === 'error' ? '#e74c3c' : type === 'success' ? '#27ae60' : '#3498db'};
        color: white;
        border-radius: 5px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.2);
        z-index: 1000;
        animation: slideIn 0.3s ease;
    `;

    document.body.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => {
            document.body.removeChild(toast);
        }, 300);
    }, 3000);
}

// Add CSS for animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
    
    .status-connected { color: #27ae60; }
    .status-disconnected { color: #e74c3c; }
    
    .server-status-indicator.status-running { color: #27ae60; }
    .server-status-indicator.status-stopped { color: #e74c3c; }
    .server-status-indicator.status-starting { color: #f39c12; }
`;
document.head.appendChild(style);

// Error handling
window.addEventListener('error', (event) => {
    console.error('Global error:', event.error);
    showToast('An unexpected error occurred', 'error');
});

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeSocketConnection();

    // Add any global initialization code here
    console.log('Minecraft Forge Server Gateway initialized');
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        initializeSocketConnection,
        showToast,
        formatDate,
        formatFileSize
    };
}