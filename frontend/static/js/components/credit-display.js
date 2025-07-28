/**
 * Credit Display Component
 * Manages credit balance display and auto-recharge info with real-time updates
 */

class CreditDisplayManager {
    constructor() {
        this.CREDIT_RATE = 0.00025; // $0.00025 per credit
        this.eventSource = null; // For SSE connection

        this.elements = {
            creditsBalance: document.getElementById('credits-balance'),
            balanceValue: document.getElementById('balance-value'),
            totalPurchased: document.getElementById('total-purchased'),
            totalUsed: document.getElementById('total-used'),
            remainingBalance: document.getElementById('remaining-balance'),
            autoRechargeInfo: document.getElementById('auto-recharge-info'),
            autoRechargeDetails: document.getElementById('auto-recharge-details')
        };

        this.init();
    }

    async init() {
        console.log('📊 Initializing credit display manager...');
        
        // First try to load real balance from API
        await this.loadRealBalance();
        
        // Setup auto-recharge info
        this.setupAutoRechargeInfo();

        // 🚀 Start real-time updates
        this.startRealTimeUpdates();

        console.log('✅ Credit display manager initialized with real-time updates');
    }

    async loadRealBalance() {
        console.log('📊 Loading real balance from Metronome API...');
        
        try {
            // Get customer ID from session
            const customerId = sessionStorage.getItem('vocalis_customer_id');
            
            if (!customerId) {
                console.log('⚠️ No customer ID found, using demo balance');
                this.loadDemoBalance();
                return;
            }
            
            // Call the balance API
            console.log(`📊 Calling balance API for customer: ${customerId}`);
            const response = await fetch(`/api/billing/credits/balance/${customerId}`);
            
            if (!response.ok) {
                throw new Error(`Balance API failed: ${response.status}`);
            }
            
            const balanceData = await response.json();
            console.log('📊 Balance API Response:', balanceData);
            
            // Update display with real balance
            const balance = balanceData.balance || 0;
            const dollarValue = balanceData.dollar_value || (balance * this.CREDIT_RATE);
            const source = balanceData.source || 'api';
            
            console.log(`📊 Real balance loaded: ${balance} credits ($${dollarValue.toFixed(2)}) from ${source}`);
            
            // Update the UI
            this.updateCreditsDisplay(balance, balance, 0, source);
            
            // Show success notification
            if (source === 'metronome_api') {
                notifications.info(`📊 Real balance loaded: ${balance.toLocaleString()} credits`);
            } else {
                notifications.warning(`⚠️ Using ${source} balance: ${balance.toLocaleString()} credits`);
            }
            
        } catch (error) {
            console.error('❌ Failed to load real balance:', error);
            console.log('📊 Falling back to demo balance');
            
            // Fallback to demo balance
            this.loadDemoBalance();
            notifications.warning('⚠️ Using demo balance - API unavailable');
        }
    }

    loadDemoBalance() {
        console.log('📊 Loading demo balance from sessionStorage...');
        
        // Get purchase data from billing page
        const purchaseData = JSON.parse(sessionStorage.getItem('vocalis_purchase') || '{}');
        const billingData = JSON.parse(sessionStorage.getItem('vocalis_billing') || '{}');
        
        console.log('Purchase data:', purchaseData);
        console.log('Billing data:', billingData);
        
        // Set default values - use purchase data if available
        let creditsBalance = 40000; // Default
        let totalPurchased = 40000;
        let totalUsed = 0;
        
        // Use purchase data if available
        if (purchaseData.credits && purchaseData.credits > 0) {
            creditsBalance = purchaseData.credits;
            totalPurchased = purchaseData.credits;
            console.log('✅ Found purchase data - Credits:', creditsBalance);
        } else if (billingData.credits_balance && billingData.credits_balance > 0) {
            creditsBalance = billingData.credits_balance;
            totalPurchased = billingData.credits_balance;
            console.log('✅ Found billing data - Credits:', creditsBalance);
        } else {
            console.log('⚠️ No purchase data found, using default 40,000 credits');
        }
        
        // Update UI with demo data
        this.updateCreditsDisplay(creditsBalance, totalPurchased, totalUsed, 'demo');
    }

    updateCreditsDisplay(remaining, purchased, used, source = 'unknown') {
        console.log('📊 Updating credits display:', { remaining, purchased, used, source });
        
        const dollarValue = remaining * this.CREDIT_RATE;
        
        // Update main balance
        if (this.elements.creditsBalance) {
            this.elements.creditsBalance.textContent = remaining.toLocaleString();
        }
        
        // Update dollar value
        if (this.elements.balanceValue) {
            this.elements.balanceValue.textContent = `≈ $${dollarValue.toFixed(2)} value`;
        }
        
        // Update breakdown
        if (this.elements.totalPurchased) {
            this.elements.totalPurchased.textContent = purchased.toLocaleString();
        }
        
        if (this.elements.totalUsed) {
            this.elements.totalUsed.textContent = used.toLocaleString();
        }
        
        if (this.elements.remainingBalance) {
            this.elements.remainingBalance.textContent = remaining.toLocaleString();
        }
        
        // Add visual indicator of data source
        if (this.elements.creditsBalance) {
            const indicator = source === 'metronome_api' ? '🟢' : 
                            source === 'real_time_update' ? '🔴' :
                            source === 'demo' ? '🟡' : '🔴';
            this.elements.creditsBalance.title = `${indicator} Data source: ${source}`;
        }
        
        console.log('📊 Display updated:', {
            remaining: remaining,
            dollarValue: dollarValue,
            purchased: purchased,
            used: used,
            source: source
        });
    }

    setupAutoRechargeInfo() {
        // Get purchase data to check for auto-recharge
        const purchaseData = JSON.parse(sessionStorage.getItem('vocalis_purchase') || '{}');
        
        if (purchaseData.auto_recharge && purchaseData.auto_recharge.enabled) {
            const threshold = purchaseData.auto_recharge.threshold || 5000;
            const amount = purchaseData.auto_recharge.amount || 50000;
            
            if (this.elements.autoRechargeInfo) {
                this.elements.autoRechargeInfo.classList.add('show');
            }
            
            if (this.elements.autoRechargeDetails) {
                this.elements.autoRechargeDetails.textContent = 
                    `We'll automatically add ${amount.toLocaleString()} credits when you drop below ${threshold.toLocaleString()} credits.`;
            }
        }
    }

    startRealTimeUpdates() {
  const customerId = sessionStorage.getItem('vocalis_customer_id');
    
    if (!customerId) {
        console.log('⚠️ No customer ID found, skipping real-time updates');
        return;
    }

    try {
        console.log('🚀 Starting real-time balance updates...');
        console.log('🔗 Customer ID:', customerId);
        
        const sseUrl = `/api/webhooks/events/${customerId}`;
        console.log('🔗 Connecting to SSE:', sseUrl);
        
        this.eventSource = new EventSource(sseUrl);
        
        // 🚀 ADD MORE DEBUG LOGGING:
        this.eventSource.onmessage = (event) => {
            console.log('🔥 RAW SSE EVENT RECEIVED:', event);
            console.log('🔥 RAW EVENT DATA:', event.data);
            
            try {
                const data = JSON.parse(event.data);
                console.log('🔥 PARSED EVENT DATA:', data);
                this.handleRealTimeEvent(data);
            } catch (error) {
                console.error('❌ Failed to parse SSE event:', error);
                console.error('❌ Raw data that failed:', event.data);
            }
        };
        
        this.eventSource.onopen = () => {
            console.log('✅ Real-time updates connected');
            console.log('🔥 SSE ReadyState:', this.eventSource.readyState);
            notifications.info('🔄 Real-time balance updates active');
        };
        
        this.eventSource.onerror = (error) => {
            console.log('❌ Real-time updates connection error:', error);
            console.log('🔥 SSE ReadyState:', this.eventSource.readyState);
            console.log('🔄 SSE will automatically reconnect...');
        };
        
    } catch (error) {
        console.error('Failed to start real-time updates:', error);
    }
}

    handleRealTimeEvent(data) {
        console.log('📡 Real-time event received:', data);
        
        switch (data.type) {
            case 'connected':
                console.log('🔄 SSE connection established');
                break;
                
            case 'balance_updated':
                console.log('💰 Balance update received:', data.new_balance);
                
                // Update the display with new balance
                this.updateCreditsDisplay(data.new_balance, data.new_balance, 0, 'real_time_update');
                
                // Show notification
                if (data.auto_recharge) {
                    notifications.success(`🎉 Auto-recharge complete! Your balance has been updated to ${data.new_balance.toLocaleString()} credits`);
                } else {
                    notifications.info(`💰 Balance updated: ${data.new_balance.toLocaleString()} credits`);
                }
                break;
                
            case 'auto_recharge_complete':
                console.log('🔄 Auto-recharge completed');
                notifications.success('🎉 Auto-recharge completed successfully!');
                
                // Refresh balance to get the latest data
                setTimeout(() => {
                    this.loadRealBalance();
                }, 2000);
                break;
            
            case 'auto_recharge_failed':
                console.log('❌ Auto-recharge failed');
                notifications.error('❌ Auto-recharge failed. Please update your payment method.');
                break;
                
            case 'ping':
                // Keep-alive ping, do nothing
                break;
                
            default:
                console.log('📡 Unknown event type:', data.type);
        }
    }

    destroy() {
        if (this.eventSource) {
            console.log('🔌 Closing real-time updates connection');
            this.eventSource.close();
            this.eventSource = null;
        }
    }

    async refreshBalance() {
        try {
            console.log('🔄 Refreshing credit balance...');
            await this.loadRealBalance();
        } catch (error) {
            console.error('Failed to refresh balance:', error);
        }
    }

    formatNumber(number) {
        return new Intl.NumberFormat('en-US').format(number);
    }

    formatCurrency(amount) {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD'
        }).format(amount);
    }
}

// Export for use in other modules
window.CreditDisplayManager = CreditDisplayManager;

// Clean up on page unload
window.addEventListener('beforeunload', () => {
    if (window.creditDisplayManager) {
        window.creditDisplayManager.destroy();
    }
});