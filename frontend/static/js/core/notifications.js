/**
 * Vocalis Notification System
 * Toast notifications with auto-hide
 */

class NotificationManager {
    constructor() {
        this.container = this.createContainer();
        document.body.appendChild(this.container);
    }
    
    createContainer() {
        const container = document.createElement('div');
        container.className = 'notification';
        container.id = 'vocalis-notification';
        return container;
    }
    
    show(message, type = 'info', duration = 4000) {
        clearTimeout(this.hideTimeout);
        
        this.container.textContent = message;
        this.container.className = `notification ${type} show`;
        
        this.hideTimeout = setTimeout(() => {
            this.hide();
        }, duration);
    }
    
    hide() {
        this.container.classList.remove('show');
        clearTimeout(this.hideTimeout);
    }
    
    success(message, duration) {
        this.show(message, 'success', duration);
    }
    
    error(message, duration) {
        this.show(message, 'error', duration);
    }
    
    warning(message, duration) {
        this.show(message, 'warning', duration);
    }
    
    info(message, duration) {
        this.show(message, 'info', duration);
    }
}

// Export global instance
window.NotificationManager = NotificationManager;
window.notifications = new NotificationManager();
