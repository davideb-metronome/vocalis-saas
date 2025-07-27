/**
 * Form Validation Component
 * Reusable form validation utilities
 */

class FormValidator {
    constructor() {
        this.validators = {
            email: this.validateEmail,
            password: this.validatePassword,
            required: this.validateRequired
        };
    }

    validateEmail(value) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return {
            isValid: emailRegex.test(value),
            message: 'Please enter a valid email address'
        };
    }

    validatePassword(value) {
        const minLength = value.length >= 6;
        const hasUpper = /[A-Z]/.test(value);
        const hasNumber = /[0-9]/.test(value);
        const hasSpecial = /[^A-Za-z0-9]/.test(value);

        const score = [minLength, hasUpper, hasNumber, hasSpecial].filter(Boolean).length;
        
        let strength = 'weak';
        if (score >= 3) strength = 'strong';
        else if (score >= 2) strength = 'medium';

        return {
            isValid: minLength,
            message: minLength ? '' : 'Password must be at least 6 characters',
            strength: strength,
            score: score
        };
    }

    validateRequired(value) {
        return {
            isValid: value && value.trim().length > 0,
            message: 'This field is required'
        };
    }

    validateField(fieldId, rules = []) {
        const field = document.getElementById(fieldId);
        if (!field) return { isValid: false, message: 'Field not found' };

        const value = field.value;
        
        for (const rule of rules) {
            const validator = this.validators[rule];
            if (validator) {
                const result = validator(value);
                if (!result.isValid) {
                    return result;
                }
            }
        }

        return { isValid: true, message: '' };
    }

    validateForm(formId, fieldRules) {
        const results = {};
        let isFormValid = true;

        for (const [fieldId, rules] of Object.entries(fieldRules)) {
            const result = this.validateField(fieldId, rules);
            results[fieldId] = result;
            
            if (!result.isValid) {
                isFormValid = false;
            }
        }

        return {
            isValid: isFormValid,
            fields: results
        };
    }
}

// Password Strength Indicator
class PasswordStrengthIndicator {
    constructor(passwordFieldId, strengthLabelId, strengthFillId) {
        this.passwordField = document.getElementById(passwordFieldId);
        this.strengthLabel = document.getElementById(strengthLabelId);
        this.strengthFill = document.getElementById(strengthFillId);
        this.strengthBar = this.strengthFill?.parentElement?.parentElement;
        this.validator = new FormValidator();

        this.init();
    }

    init() {
        if (!this.passwordField || !this.strengthLabel || !this.strengthFill) {
            console.warn('Password strength indicator: Required elements not found');
            return;
        }

        this.passwordField.addEventListener('input', (e) => {
            this.updateStrength(e.target.value);
        });
    }

    updateStrength(password) {
        const result = this.validator.validatePassword(password);
        
        // Update label
        if (password.length === 0) {
            this.strengthLabel.textContent = 'Enter password';
        } else {
            this.strengthLabel.textContent = result.strength.charAt(0).toUpperCase() + result.strength.slice(1);
        }

        // Update visual indicator
        if (this.strengthBar) {
            this.strengthBar.className = 'password-strength';
            if (password.length > 0) {
                this.strengthBar.classList.add(`strength-${result.strength}`);
            }
        }
    }
}

// Loading State Manager
class LoadingStateManager {
    static showLoading(button, text = 'Loading...') {
        if (!button) return;
        
        button.disabled = true;
        button.dataset.originalText = button.innerHTML;
        button.innerHTML = `
            <div class="loading-state">
                <div class="spinner"></div>
                <span>${text}</span>
            </div>
        `;
    }

    static hideLoading(button) {
        if (!button) return;
        
        button.disabled = false;
        if (button.dataset.originalText) {
            button.innerHTML = button.dataset.originalText;
            delete button.dataset.originalText;
        }
    }
}

// Export for use in other modules
window.FormValidator = FormValidator;
window.PasswordStrengthIndicator = PasswordStrengthIndicator;
window.LoadingStateManager = LoadingStateManager;