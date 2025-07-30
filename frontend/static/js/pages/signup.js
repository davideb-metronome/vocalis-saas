/**
 * Signup Page Logic
 * Handles signup form submission and user interactions
 */

class SignupPage {
    constructor() {
        this.form = document.getElementById('signup-form');
        this.submitButton = document.getElementById('submit-btn');
        this.validator = new FormValidator();
        
        this.fieldRules = {
            firstname: ['required'],
            lastname: ['required'],
            email: ['required', 'email'],
            password: ['required', 'password']
        };

        this.init();
    }

    init() {
        if (!this.form || !this.submitButton) {
            console.error('Signup: Required form elements not found');
            return;
        }

        // Initialize password strength indicator
        this.passwordStrength = new PasswordStrengthIndicator('password', 'strength-label', 'strength-fill');
        
        // Bind form submission
        this.form.addEventListener('submit', (e) => this.handleSubmit(e));

        // Show welcome notification
        setTimeout(() => {
            notifications.info('Welcome to Vocalis! 🎉');
        }, 50000);

        console.log('✅ Signup page initialized');
    }

    async handleSubmit(event) {
        event.preventDefault();
        
        try {
            // Validate form
            const validation = this.validator.validateForm('signup-form', this.fieldRules);
            if (!validation.isValid) {
                this.showValidationErrors(validation.fields);
                return;
            }

            // Show loading state
            LoadingStateManager.showLoading(this.submitButton, 'Creating Account...');

            // Collect form data
            const formData = this.collectFormData();
            
            // Store user data for session (even if API fails)
            sessionStorage.setItem('vocalis_user', JSON.stringify(formData));
            
            try {
                // Call API
                const result = await vocalisAPI.signup(formData);
                
                if (result.success) {
                    notifications.success('✅ Account created successfully!');
                    
                    // Redirect to billing page
                    setTimeout(() => {
                        window.location.href = '/billing';
                    }, 1500);
                } else {
                    throw new Error(result.message || 'Signup failed');
                }

            } catch (apiError) {
                console.log('API call failed, proceeding with demo flow:', apiError);
                
                // Generate demo customer ID for session
                const customerId = `demo_${formData.email.split('@')[0]}_${Date.now()}`;
                sessionStorage.setItem('vocalis_customer_id', customerId);
                
                if (apiError.message.includes('not implemented')) {
                    notifications.success('✅ Account created (demo mode)');
                } else {
                    notifications.warning('⚠️ Using demo mode - some features limited');
                }
                
                // Always redirect to billing for demo flow
                setTimeout(() => {
                    window.location.href = '/billing';
                }, 1500);
            }

        } catch (error) {
            console.error('Form validation failed:', error);
            notifications.error(`Signup failed: ${error.message}`);
        } finally {
            // Always restore button state
            setTimeout(() => {
                LoadingStateManager.hideLoading(this.submitButton);
            }, 2000);
        }
    }

    collectFormData() {
        const firstname = document.getElementById('firstname').value.trim();
        const lastname = document.getElementById('lastname').value.trim();
        
        return {
            first_name: firstname,
            last_name: lastname,
            full_name: `${firstname} ${lastname}`,
            email: document.getElementById('email').value.trim(),
            password: document.getElementById('password').value
        };
    }

    showValidationErrors(fields) {
        // Find first invalid field and show error
        for (const [fieldId, result] of Object.entries(fields)) {
            if (!result.isValid) {
                notifications.error(result.message);
                
                // Focus the problematic field
                const field = document.getElementById(fieldId);
                if (field) {
                    field.focus();
                    field.style.borderColor = 'var(--error-red)';
                    
                    // Reset border color after a delay
                    setTimeout(() => {
                        field.style.borderColor = '';
                    }, 3000);
                }
                break;
            }
        }
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.signupPage = new SignupPage();
});