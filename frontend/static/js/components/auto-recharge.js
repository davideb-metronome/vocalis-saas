/**
 * Auto-Recharge Component
 * Handles auto-recharge configuration and validation
 */

class AutoRechargeManager {
    constructor(calculator) {
        this.calculator = calculator;
        this.METRONOME_MIN_AMOUNT = 0; // Minimum auto-recharge amount
        this.enabled = false;
        this.selectedThreshold = '25000';
        this.selectedRechargeAmount = { credits: '50000', price: '12.50' };

        this.elements = {
            toggle: document.getElementById('autorecharge-toggle'),
            options: document.getElementById('autorecharge-options'),
            thresholdOptions: document.querySelectorAll('.threshold-option'),
            rechargeAmountOptions: document.querySelectorAll('.recharge-amount-option'),
            warning: document.getElementById('validation-warning'),
            warningMessage: document.getElementById('warning-message')
        };

        this.init();
    }

    init() {
        if (!this.elements.toggle || !this.elements.options) {
            console.warn('Auto-recharge: Required elements not found');
            return;
        }

        // Bind event listeners
        this.elements.toggle.addEventListener('change', () => this.toggleAutoRecharge());
        
        // Threshold selection
        if (this.elements.thresholdOptions.length > 0) {
            this.elements.thresholdOptions.forEach(option => {
                option.addEventListener('click', (e) => this.selectThreshold(e.currentTarget));
            });
        }

        // Recharge amount selection
        if (this.elements.rechargeAmountOptions.length > 0) {
            this.elements.rechargeAmountOptions.forEach(option => {
                option.addEventListener('click', (e) => this.selectRechargeAmount(e.currentTarget));
            });
        }

        console.log('✅ Auto-recharge manager initialized');
    }

    toggleAutoRecharge() {
        this.enabled = this.elements.toggle.checked;
        
        if (this.enabled) {
            this.elements.options.classList.add('active');
            this.validateConfiguration();
            notifications.info('Auto-recharge enabled');
        } else {
            this.elements.options.classList.remove('active');
            this.hideWarning();
            notifications.info('Auto-recharge disabled');
        }
    }

    selectThreshold(element) {
        const threshold = element.dataset.threshold;
        
        // Update selection
        this.elements.thresholdOptions.forEach(opt => opt.classList.remove('selected'));
        element.classList.add('selected');
        
        this.selectedThreshold = threshold;
        
        const thresholdDollars = this.calculator.creditsToDollars(parseInt(threshold));
        this.validateConfiguration();
        
        notifications.info(`Threshold set to ${this.calculator.formatNumber(parseInt(threshold))} credits (${this.calculator.formatCurrency(thresholdDollars)})`);
    }

    selectRechargeAmount(element) {
        const amount = element.dataset.amount;
        
        // Update selection
        this.elements.rechargeAmountOptions.forEach(opt => opt.classList.remove('selected'));
        element.classList.add('selected');
        
        // Calculate credits and price
        const credits = parseInt(amount);
        const price = this.calculator.creditsToDollars(credits);
        
        this.selectedRechargeAmount = {
            credits: amount,
            price: price.toFixed(2)
        };
        
        this.validateConfiguration();
        
        notifications.info(`Auto-recharge set to ${this.calculator.formatNumber(credits)} credits (${this.calculator.formatCurrency(price)})`);
    }

    validateConfiguration(purchaseAmount = null) {
        if (!this.enabled) {
            this.hideWarning();
            return true;
        }

        const thresholdCredits = parseInt(this.selectedThreshold);
        const rechargeCredits = parseInt(this.selectedRechargeAmount.credits);
        
        const thresholdDollars = this.calculator.creditsToDollars(thresholdCredits);
        const rechargeDollars = this.calculator.creditsToDollars(rechargeCredits);

        // Check minimum recharge amount
        if (rechargeDollars < this.METRONOME_MIN_AMOUNT) {
            this.showWarning(
                `Auto-recharge amount (${this.calculator.formatCurrency(rechargeDollars)}) is below Metronome's minimum requirement of ${this.calculator.formatCurrency(this.METRONOME_MIN_AMOUNT)}. Please increase the auto-recharge amount.`
            );
            return false;
        }

        // Check for immediate trigger risk but don't block - just warn
        if (purchaseAmount && thresholdDollars >= purchaseAmount * 0.85) {
            this.showWarning(
                `Warning: Your threshold (${this.calculator.formatCurrency(thresholdDollars)}) is close to your purchase amount (${this.calculator.formatCurrency(purchaseAmount)}). Auto-recharge may trigger immediately, charging an additional ${this.calculator.formatCurrency(rechargeDollars)}. Total charge would be ${this.calculator.formatCurrency(purchaseAmount + rechargeDollars)}.`
            );
        } else {
            this.hideWarning();
        }
        
        return true;
    }

    showWarning(message) {
        if (this.elements.warning && this.elements.warningMessage) {
            this.elements.warningMessage.textContent = message;
            this.elements.warning.classList.add('show');
        }
    }

    hideWarning() {
        if (this.elements.warning) {
            this.elements.warning.classList.remove('show');
        }
    }

    getConfiguration() {
        if (!this.enabled) {
            return null;
        }

        return {
            enabled: true,
            threshold: parseInt(this.selectedThreshold),
            amount: parseInt(this.selectedRechargeAmount.credits),
            price: parseFloat(this.selectedRechargeAmount.price)
        };
    }
}

// Export for use in other modules
window.AutoRechargeManager = AutoRechargeManager;
