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
        this.selectedRechargeAmount = { credits: '200000', price: '50.00' };

        this.elements = {
            toggle: document.getElementById('autorecharge-toggle'),
            options: document.getElementById('autorecharge-options'),
            thresholdOptions: document.querySelectorAll('.threshold-option'),
            rechargeInput: document.getElementById('recharge-input'),
            presetButtons: document.querySelectorAll('.preset-btn'),
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
        this.elements.thresholdOptions.forEach(option => {
            option.addEventListener('click', (e) => this.selectThreshold(e.currentTarget));
        });

        // Recharge amount input
        if (this.elements.rechargeInput) {
            this.elements.rechargeInput.addEventListener('input', (e) => {
                e.target.value = this.calculator.formatInputValue(e.target.value);
            });
            
            this.elements.rechargeInput.addEventListener('change', (e) => {
                this.updateRechargeAmount(e.target.value);
            });
        }

        // Preset buttons
        this.elements.presetButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const amount = e.target.dataset.amount;
                this.setRechargePreset(amount);
            });
        });

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

    updateRechargeAmount(value) {
        const numValue = this.calculator.parseDollarInput(value);
        
        if (numValue < this.METRONOME_MIN_AMOUNT) {
            notifications.warning(`⚠️ Auto-recharge amount must be at least ${this.calculator.formatCurrency(this.METRONOME_MIN_AMOUNT)} (90,000 credits)`);
            this.elements.rechargeInput.style.borderColor = 'var(--error-red)';
            return;
        }
        
        if (numValue > 1000) {
            notifications.warning('⚠️ Auto-recharge amount cannot exceed $1,000');
            this.elements.rechargeInput.style.borderColor = 'var(--error-red)';
            return;
        }
        
        // Reset border color on valid input
        this.elements.rechargeInput.style.borderColor = '';
        
        // Calculate credits
        const credits = this.calculator.dollarsToCredits(numValue);
        
        // Update selected amount
        this.selectedRechargeAmount = {
            credits: credits.toString(),
            price: numValue.toFixed(2)
        };
        
        // Update preset button states
        this.updatePresetButtons(numValue);
        
        this.validateConfiguration();
        notifications.info(`Auto-recharge set to ${this.calculator.formatNumber(credits)} credits (${this.calculator.formatCurrency(numValue)})`);
    }

    setRechargePreset(amount) {
        const numAmount = parseFloat(amount);
        this.elements.rechargeInput.value = this.calculator.formatCurrency(numAmount);
        this.updateRechargeAmount(this.calculator.formatCurrency(numAmount));
    }

    updatePresetButtons(selectedAmount) {
        this.elements.presetButtons.forEach(btn => {
            btn.classList.remove('active');
            const btnAmount = parseFloat(btn.dataset.amount);
            if (btnAmount === selectedAmount) {
                btn.classList.add('active');
            }
        });
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
            return false; // Still block for this - it's a hard requirement
        }

        // ✅ FIXED: Check for immediate trigger risk but don't block - just warn
        if (purchaseAmount && thresholdDollars >= purchaseAmount * 0.85) {
            this.showWarning(
                `Warning: Your threshold (${this.calculator.formatCurrency(thresholdDollars)}) is close to your purchase amount (${this.calculator.formatCurrency(purchaseAmount)}). Auto-recharge may trigger immediately, charging an additional ${this.calculator.formatCurrency(rechargeDollars)}. Total charge would be ${this.calculator.formatCurrency(purchaseAmount + rechargeDollars)}.`
            );
            // ✅ CHANGED: Don't return false - just show warning and allow purchase
            // return false; // ← REMOVED THIS LINE
        } else {
            this.hideWarning();
        }
        
        return true; // ✅ Always return true (allow purchase) unless it's the hard minimum requirement
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