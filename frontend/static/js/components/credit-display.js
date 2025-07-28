/**
 * Credit Display Component - FIXED VERSION WITH ENHANCED SSE DEBUGGING
 * Manages credit balance display and auto-recharge info with real-time updates
 */

class CreditDisplayManager {
    constructor() {
        this.CREDIT_RATE = 0.00025;
        this.eventSource = null;
        this.isLoaded = false; // ✅ Track if real data is loaded

        this.elements = {
            creditsBalance: document.getElementById('credits-balance'),
            balanceValue: document.getElementById('balance-value'),
            totalPurchased: document.getElementById('total-purchased'),
            totalUsed: document.getElementById('total-used'),
            remainingBalance: document.getElementById('remaining-balance'),
            autoRechargeInfo: document.getElementById('auto-recharge-info'),
            autoRechargeDetails: document.getElementById('auto-recharge-details')
        };

        // ✅ PREVENT FLASH: Hide balance until loaded
        this.showLoadingState();
        this.init();
    }

    showLoadingState() {
        // Show loading skeleton instead of default values
        if (this.elements.creditsBalance) {
            this.elements.creditsBalance.textContent = '...';
            this.elements.creditsBalance.style.opacity = '0.5';
        }
        if (this.elements.balanceValue) {
            this.elements.balanceValue.textContent = 'Loading...';
        }
        if (this.elements.totalPurchased) {
            this.elements.totalPurchased.textContent = '...';
        }
        if (this.elements.totalUsed) {
            this.elements.totalUsed.textContent = '...';
        }
        if (this.elements.remainingBalance) {
            this.elements.remainingBalance.textContent = '...';
        }
    }

    async init() {
        console.log('📊 Initializing credit display manager...');
        
        // Load real balance first (this will update the display)
        await this.loadRealBalance();
        
        // Setup auto-recharge info
        this.setupAutoRechargeInfo();

        // Start real-time updates
        this.startRealTimeUpdates();

        console.log('✅ Credit display manager initialized');
    }


    async loadRealBalance() {
        console.log('📊 Loading real balance from Metronome API...');
        
        try {
            const customerId = sessionStorage.getItem('vocalis_customer_id');
            
            if (!customerId) {
                console.log('⚠️ No customer ID found, using demo balance');
                this.loadDemoBalance();
                return;
            }
            
            const response = await fetch(`/api/billing/credits/balance/${customerId}`);
            
            if (!response.ok) {
                throw new Error(`Balance API failed: ${response.status}`);
            }
            
            const balanceData = await response.json();
            console.log('📊 Balance API Response:', balanceData);
            
            const balance = balanceData.balance || 0;
            const dollarValue = balanceData.dollar_value || (balance * this.CREDIT_RATE);
            const source = balanceData.source || 'api';
            
            console.log(`📊 Real balance loaded: ${balance} credits ($${dollarValue.toFixed(2)}) from ${source}`);
            
            // ✅ Update display and mark as loaded
            this.updateCreditsDisplay(balance, balance, 0, source);
            this.isLoaded = true;
            
            if (source === 'metronome_api') {
                notifications.info(`📊 Real balance loaded: ${balance.toLocaleString()} credits`);
            } else {
                notifications.warning(`⚠️ Using ${source} balance: ${balance.toLocaleString()} credits`);
            }
            
        } catch (error) {
            console.error('❌ Failed to load real balance:', error);
            console.log('📊 Falling back to demo balance');
            
            this.loadDemoBalance();
            notifications.warning('⚠️ Using demo balance - API unavailable');
        }
    }


    loadDemoBalance() {
        console.log('📊 Loading demo balance from sessionStorage...');
        
        const purchaseData = JSON.parse(sessionStorage.getItem('vocalis_purchase') || '{}');
        const billingData = JSON.parse(sessionStorage.getItem('vocalis_billing') || '{}');
        
        let creditsBalance = 80000; // ✅ Use 80K to match what user actually has
        let totalPurchased = 80000;
        let totalUsed = 0;
        
        if (purchaseData.credits && purchaseData.credits > 0) {
            creditsBalance = purchaseData.credits;
            totalPurchased = purchaseData.credits;
            console.log('✅ Found purchase data - Credits:', creditsBalance);
        } else if (billingData.credits_balance && billingData.credits_balance > 0) {
            creditsBalance = billingData.credits_balance;
            totalPurchased = billingData.credits_balance;
            console.log('✅ Found billing data - Credits:', creditsBalance);
        } else {
            console.log('⚠️ No purchase data found, using default 80,000 credits');
        }
        
        // ✅ Update display and mark as loaded
        this.updateCreditsDisplay(creditsBalance, totalPurchased, totalUsed, 'demo');
        this.isLoaded = true;
    }

   updateCreditsDisplay(remaining, purchased, used, source = 'unknown') {
        console.log('📊 Updating credits display:', { remaining, purchased, used, source });
        
        const dollarValue = remaining * this.CREDIT_RATE;
        
        // ✅ RESTORE OPACITY: Remove loading state
        if (this.elements.creditsBalance) {
            this.elements.creditsBalance.textContent = remaining.toLocaleString();
            this.elements.creditsBalance.style.opacity = '1'; // Restore full opacity
        }
        
        if (this.elements.balanceValue) {
            this.elements.balanceValue.textContent = `≈ $${dollarValue.toFixed(2)} value`;
        }
        
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
        
        console.log('📊 Display updated successfully');
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
        console.log('🚀 === startRealTimeUpdates() method entered ===');
        
        const customerId = sessionStorage.getItem('vocalis_customer_id');
        console.log('🔍 Customer ID from session:', customerId);
        
        if (!customerId) {
            console.log('⚠️ No customer ID found, skipping real-time updates');
            return;
        }

        try {
            console.log('🚀 Starting real-time balance updates...');
            
            const sseUrl = `/api/webhooks/events/${customerId}`;
            console.log('🔗 SSE URL constructed:', sseUrl);
            
            // 🔥 CRITICAL DEBUG: Check if EventSource is available
            if (typeof EventSource === 'undefined') {
                console.error('❌ EventSource not supported in this browser');
                notifications.warning('Real-time updates not supported in this browser');
                return;
            }
            
            console.log('🔗 Creating EventSource...');
            this.eventSource = new EventSource(sseUrl);
            console.log('🔗 EventSource created:', this.eventSource);
            console.log('🔍 EventSource readyState:', this.eventSource.readyState);
            console.log('🔍 EventSource url:', this.eventSource.url);
            
            // 🚀 Enhanced event listeners with more debugging
            this.eventSource.onopen = (event) => {
                console.log('✅ SSE connection opened successfully!');
                console.log('🔍 Open event:', event);
                console.log('🔍 EventSource readyState after open:', this.eventSource.readyState);
                notifications.info('🔄 Real-time balance updates connected');
            };
            
            this.eventSource.onmessage = (event) => {
                console.log('🔥 === SSE MESSAGE RECEIVED ===');
                console.log('🔥 Raw event object:', event);
                console.log('🔥 Event data:', event.data);
                console.log('🔥 Event type:', event.type);
                console.log('🔥 Event timestamp:', new Date().toISOString());
                
                try {
                    const data = JSON.parse(event.data);
                    console.log('🔥 Parsed event data:', data);
                    this.handleRealTimeEvent(data);
                } catch (parseError) {
                    console.error('❌ Failed to parse SSE event data:', parseError);
                    console.error('❌ Raw data that failed to parse:', event.data);
                }
            };
            
            this.eventSource.onerror = (error) => {
                console.log('❌ === SSE ERROR OCCURRED ===');
                console.log('❌ Error event:', error);
                console.log('🔍 EventSource readyState during error:', this.eventSource.readyState);
                
                // Log different readyState meanings
                const readyStates = {
                    0: 'CONNECTING',
                    1: 'OPEN', 
                    2: 'CLOSED'
                };
                console.log(`🔍 ReadyState meaning: ${readyStates[this.eventSource.readyState] || 'UNKNOWN'}`);
                
                // Don't show error notification immediately - SSE will retry
                console.log('🔄 SSE will automatically attempt to reconnect...');
            };
            
            // 🔥 ADDITIONAL DEBUG: Log after 2 seconds to see if connection was established
            setTimeout(() => {
                console.log('⏰ 2-second SSE status check:');
                console.log('🔍 EventSource exists:', !!this.eventSource);
                console.log('🔍 EventSource readyState:', this.eventSource?.readyState);
                console.log('🔍 EventSource url:', this.eventSource?.url);
                
                if (this.eventSource?.readyState === 0) {
                    console.log('⚠️ Still CONNECTING after 2 seconds - this might indicate a network issue');
                } else if (this.eventSource?.readyState === 2) {
                    console.log('❌ Connection CLOSED after 2 seconds - check server logs');
                }
            }, 2000);
            
        } catch (error) {
            console.error('❌ Failed to start real-time updates:', error);
            console.error('❌ Error stack:', error.stack);
            notifications.error('Failed to start real-time updates');
        }
        
        console.log('🚀 === startRealTimeUpdates() method completed ===');
    }

    handleRealTimeEvent(data) {
        console.log('📡 === HANDLING REAL-TIME EVENT ===');
        console.log('📡 Event data:', data);
        
        switch (data.type) {
            case 'connected':
                console.log('🔄 SSE connection confirmation received');
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
                console.log('🏓 Keep-alive ping received');
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