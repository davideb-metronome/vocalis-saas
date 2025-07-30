/**
 * Dashboard Page Logic
 * Coordinates voice generation and credit management
 */

class DashboardPage {
    constructor() {
        this.voiceGenerator = new VoiceGenerator();
        this.creditDisplay = new CreditDisplayManager();
        
        // Make credit display manager globally available
        window.creditDisplayManager = this.creditDisplay;

        this.init();
    }

    init() {
        // Update user info from session
        this.updateUserInfo();

        // Show welcome notification
        setTimeout(() => {
            const currentBalance = parseInt(document.getElementById('credits-balance')?.textContent?.replace(/,/g, '') || '0');
            if (currentBalance === 0) {
                console.log('⚠️ Credits still 0, forcing 40,000 credits for demo');
                this.creditDisplay.updateCreditsDisplay(40000, 40000, 0);
                notifications.info('🪙 Demo credits loaded (40,000 credits)');
            } else {
                // notifications.info('🪙 Credit system ready!');
            }
        }, 50000);

        console.log('✅ Dashboard page initialized');
    }

    updateUserInfo() {
        // Get user data from session storage
        const userData = JSON.parse(sessionStorage.getItem('vocalis_user') || '{}');
        
        if (userData.full_name) {
            const firstName = userData.full_name.split(' ')[0];
            
            // Update user email
            const userEmailElement = document.getElementById('user-email');
            if (userEmailElement && userData.email) {
                userEmailElement.textContent = userData.email;
            }
            
            // Update welcome message
            const userNameElement = document.getElementById('user-name');
            if (userNameElement) {
                userNameElement.textContent = firstName;
            }
        }
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.dashboardPage = new DashboardPage();
});