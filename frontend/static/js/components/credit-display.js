/**
 * Credit Display Component
 * Manages credit balance display and auto-recharge info
 */

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

    init() {
        // Load initial data
        this.loadPurchaseData();
        this.setupAutoRechargeInfo();

        console.log('✅ Credit display manager initialized');
    }

    loadPurchaseData() {
        console.log('📊 Loading purchase data from sessionStorage...');
        
        // Get purchase data from billing page
        const purchaseData = JSON.parse(sessionStorage.getItem('vocalis_purchase') || '{}');
        const billingData = JSON.parse(sessionStorage.getItem('vocalis_billing') || '{}');
        
        console.log('Purchase data:', purchaseData);
        console.log('Billing data:', billingData);
        
        // Set default values - always start with 40,000 credits for demo
        let creditsBalance = 40000; // Default $10 purchase
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
            // Set default data in sessionStorage for consistency
            sessionStorage.setItem('vocalis_purchase', JSON.stringify({
                credits: 40000,
                amount: 10,
                billing_type: 'prepaid_credits'
            }));
            sessionStorage.setItem('vocalis_billing', JSON.stringify({
                billing_type: 'prepaid_credits',
                credits_balance: 40000
            }));
        }
        
        // Update UI with purchase data
        this.updateCreditsDisplay(creditsBalance, totalPurchased, totalUsed);
        
        console.log('📊 Credits loaded:', {
            balance: creditsBalance,
            purchased: totalPurchased,
            used: totalUsed
        });
    }

    updateCreditsDisplay(totalPurchased, purchased, used) {
        console.log('📊 Updating credits display:', { totalPurchased, purchased, used });
        
        // Calculate remaining balance
        const remaining = totalPurchased - used;
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
            this.elements.totalPurchased.textContent = totalPurchased.toLocaleString();
        }
        
        if (this.elements.totalUsed) {
            this.elements.totalUsed.textContent = used.toLocaleString();
        }
        
        if (this.elements.remainingBalance) {
            this.elements.remainingBalance.textContent = remaining.toLocaleString();
        }
        
        console.log('📊 Display updated:', {
            remaining: remaining,
            dollarValue: dollarValue,
            totalPurchased: totalPurchased,
            used: used
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
            // In a real app, this would call the API to get updated balance
            // For now, we'll simulate usage by updating the display
            
            console.log('🔄 Refreshing credit balance...');
            
            // This would be: const result = await vocalisAPI.getCreditBalance();
            // For demo, we'll update from stored data
            this.loadPurchaseData();
            
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