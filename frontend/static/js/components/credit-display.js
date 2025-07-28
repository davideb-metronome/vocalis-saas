/**
 * Credit Display Component
 * Manages credit balance display and auto-recharge info
 */

// Update the CreditDisplayManager in frontend/static/js/components/credit-display.js

class CreditDisplayManager {
    constructor() {
        this.CREDIT_RATE = 0.00025; // $0.00025 per credit

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

        console.log('✅ Credit display manager initialized');
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