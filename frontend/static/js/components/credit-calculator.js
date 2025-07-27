/**
 * Credit Calculator Component
 * Handles credit calculations and pricing logic
 */

class CreditCalculator {
    constructor() {
        this.CREDIT_RATE = 0.00025; // $0.00025 per credit (4000 credits per $1)
        this.MIN_AMOUNT = 5;
        this.MAX_AMOUNT = 1000;
    }

    /**
     * Convert dollars to credits
     */
    dollarsToCredits(dollars) {
        return Math.floor(dollars / this.CREDIT_RATE);
    }

    /**
     * Convert credits to dollars
     */
    creditsToDollars(credits) {
        return credits * this.CREDIT_RATE;
    }

    /**
     * Calculate breakdown for different voice types
     */
    calculateVoiceBreakdown(credits) {
        return {
            standardMinutes: Math.floor(credits / 1000), // 1 credit per char, ~1000 chars per minute
            premiumMinutes: Math.floor(credits / 2000),  // 2 credits per char
            perCreditCost: this.CREDIT_RATE
        };
    }

    /**
     * Validate amount input
     */
    validateAmount(amount) {
        const numAmount = parseFloat(amount);
        
        if (isNaN(numAmount)) {
            return { isValid: false, message: 'Please enter a valid number' };
        }
        
        if (numAmount < this.MIN_AMOUNT) {
            return { isValid: false, message: `Minimum amount is $${this.MIN_AMOUNT}` };
        }
        
        if (numAmount > this.MAX_AMOUNT) {
            return { isValid: false, message: `Maximum amount is $${this.MAX_AMOUNT}` };
        }
        
        return { isValid: true, amount: numAmount, credits: this.dollarsToCredits(numAmount) };
    }

    /**
     * Format currency display
     */
    formatCurrency(amount) {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD'
        }).format(amount);
    }

    /**
     * Format number with commas
     */
    formatNumber(number) {
        return new Intl.NumberFormat('en-US').format(number);
    }

    /**
     * Format input value with dollar sign
     */
    formatInputValue(value) {
        // Remove any existing dollar sign and non-numeric characters except decimal point
        let cleanValue = value.replace(/[^\d.]/g, '');
        
        // Add dollar sign if not empty
        if (cleanValue && cleanValue !== '') {
            return `$${cleanValue}`;
        }
        
        return cleanValue;
    }

    /**
     * Parse dollar input to number
     */
    parseDollarInput(value) {
        return parseFloat(value.replace(/[^\d.]/g, ''));
    }
}

// Export for use in other modules
window.CreditCalculator = CreditCalculator;