/**
 * Billing Page Logic
 * Handles credit purchase flow and interactions
 */

class BillingPage {
    constructor() {
        this.calculator = new CreditCalculator();
        this.autoRecharge = new AutoRechargeManager(this.calculator);
        
        this.selectedAmount = 25;
        this.selectedCredits = 100000;

        this.elements = {
            amountInput: document.getElementById('amount-input'),
            amountDisplay: document.getElementById('amount-display'),
            creditsInfo: document.getElementById('credits-info'),
            standardMinutes: document.getElementById('standard-minutes'),
            premiumMinutes: document.getElementById('premium-minutes'),
            perCreditCost: document.getElementById('per-credit-cost'),
            totalAmount: document.getElementById('total-amount'),
            purchaseBtn: document.getElementById('purchase-btn'),
            closeBtn: document.getElementById('close-btn')
        };

        this.init();
    }

    init() {
        if (!this.elements.amountInput || !this.elements.purchaseBtn) {
            console.error('Billing: Required elements not found');
            return;
        }

        // Bind event listeners
        this.elements.amountInput.addEventListener('input', (e) => {
            e.target.value = this.calculator.formatInputValue(e.target.value);
        });

        this.elements.amountInput.addEventListener('change', (e) => {
            this.updateAmount(e.target.value);
        });

        this.elements.purchaseBtn.addEventListener('click', () => {
            this.handlePurchase();
        });

        if (this.elements.closeBtn) {
            this.elements.closeBtn.addEventListener('click', () => {
                this.goBack();
            });
        }

        // Initialize display
        this.updateDisplay();

        // Show welcome notification
        // setTimeout(() => {
        //     notifications.info('💳 Enhanced credit billing ready!');
        // }, 1000);

        console.log('✅ Billing page initialized');
    }

    updateAmount(value) {
        const validation = this.calculator.validateAmount(value.replace('$', ''));
        
        if (!validation.isValid) {
            notifications.error(validation.message);
            return;
        }

        this.selectedAmount = validation.amount;
        this.selectedCredits = validation.credits;
        
        this.updateDisplay();
        this.autoRecharge.validateConfiguration(this.selectedAmount);
        
        notifications.info(`${this.calculator.formatCurrency(this.selectedAmount)} = ${this.calculator.formatNumber(this.selectedCredits)} credits`);
    }

    updateDisplay() {
        const breakdown = this.calculator.calculateVoiceBreakdown(this.selectedCredits);
        
        // Update main display
        if (this.elements.amountDisplay) {
            this.elements.amountDisplay.textContent = this.calculator.formatCurrency(this.selectedAmount);
        }
        
        if (this.elements.creditsInfo) {
            this.elements.creditsInfo.textContent = `${this.calculator.formatNumber(this.selectedCredits)} credits`;
        }
        
        // Update breakdown
        if (this.elements.standardMinutes) {
            this.elements.standardMinutes.textContent = `~${breakdown.standardMinutes} minutes`;
        }
        
        if (this.elements.premiumMinutes) {
            this.elements.premiumMinutes.textContent = `~${breakdown.premiumMinutes} minutes`;
        }
        
        if (this.elements.perCreditCost) {
            this.elements.perCreditCost.textContent = `$${breakdown.perCreditCost.toFixed(5)}`;
        }
        
        // Update total and button
        if (this.elements.totalAmount) {
            this.elements.totalAmount.textContent = this.calculator.formatCurrency(this.selectedAmount);
        }
        
        if (this.elements.purchaseBtn) {
            this.elements.purchaseBtn.textContent = `Purchase ${this.calculator.formatCurrency(this.selectedAmount)} of credits`;
        }
        
        // Update input field
        if (this.elements.amountInput) {
            this.elements.amountInput.value = `$${this.selectedAmount.toFixed(0)}`;
        }
    }

    async handlePurchase() {
        try {
            // Validate auto-recharge configuration
            if (!this.autoRecharge.validateConfiguration(this.selectedAmount)) {
                notifications.error('Please fix auto-recharge configuration before proceeding');
                return;
            }

            // Show loading state
            LoadingStateManager.showLoading(this.elements.purchaseBtn, 'Processing...');

            // Prepare purchase data
            const purchaseData = {
                billing_type: 'prepaid_credits',
                credits: this.selectedCredits,
                amount: this.selectedAmount,
                auto_recharge: this.autoRecharge.getConfiguration()
            };

            console.log('💳 Processing credit purchase...', purchaseData);

            // Store purchase data for dashboard (regardless of API success)
            sessionStorage.setItem('vocalis_purchase', JSON.stringify(purchaseData));
            sessionStorage.setItem('vocalis_billing', JSON.stringify({
                billing_type: 'prepaid_credits',
                credits_balance: this.selectedCredits,
                auto_recharge: purchaseData.auto_recharge
            }));

            try {
                // Call API
                const result = await vocalisAPI.purchaseCredits(purchaseData);

                if (result.success) {
                    notifications.success(`✅ ${this.calculator.formatNumber(this.selectedCredits)} credits purchased successfully!`);
                    
                    // Update session data with contract ID if available
                    const billingData = JSON.parse(sessionStorage.getItem('vocalis_billing'));
                    billingData.contract_id = result.contract_id;
                    sessionStorage.setItem('vocalis_billing', JSON.stringify(billingData));
                    
                    // Redirect to dashboard
                    setTimeout(() => {
                        window.location.href = '/dashboard';
                    }, 1500);
                } else {
                    throw new Error(result.message || 'Purchase failed');
                }

            } catch (apiError) {
                console.log('API call failed, proceeding with demo flow:', apiError);
                
                if (apiError.message.includes('not implemented')) {
                    notifications.success(`✅ ${this.calculator.formatNumber(this.selectedCredits)} credits purchased (demo mode)`);
                } else {
                    notifications.warning('⚠️ Using demo mode - some features limited');
                }
                
                // Always redirect to dashboard for demo flow
                setTimeout(() => {
                    window.location.href = '/dashboard';
                }, 1500);
            }

        } catch (error) {
            console.error('❌ Credit purchase failed:', error);
            
            // Handle validation errors
            if (error.message.includes('auto-recharge') || error.message.includes('threshold')) {
                notifications.error('❌ Auto-recharge configuration error. Please check your settings.');
            } else {
                notifications.error(`❌ Purchase failed: ${error.message}`);
            }

        } finally {
            // Always restore button state
            setTimeout(() => {
                LoadingStateManager.hideLoading(this.elements.purchaseBtn);
            }, 2000);
        }
    }

    goBack() {
        window.history.back();
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.billingPage = new BillingPage();
});