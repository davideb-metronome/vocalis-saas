/**
 * Vocalis API Client
 * Centralized API communication with error handling
 */

class VocalisAPI {
    constructor(baseURL = '/api') {
        this.baseURL = baseURL;
        this.customerId = this.getCustomerId();
    }
    
    /**
     * Get customer ID from session storage
     */
    getCustomerId() {
        return sessionStorage.getItem('vocalis_customer_id') || null;
    }
    
    /**
     * Set customer ID in session storage
     */
    setCustomerId(customerId) {
        sessionStorage.setItem('vocalis_customer_id', customerId);
        this.customerId = customerId;
    }
    
    /**
     * Make HTTP request with error handling
     */
    async makeRequest(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
            },
        };
        
        const requestOptions = { ...defaultOptions, ...options };
        
        try {
            const response = await fetch(url, requestOptions);
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.detail || `HTTP ${response.status}: ${response.statusText}`);
            }
            
            return data;
        } catch (error) {
            console.error(`API Request failed: ${endpoint}`, error);
            throw error;
        }
    }
    
    /**
     * User signup
     */
    async signup(userData) {
        const response = await this.makeRequest('/auth/signup', {
            method: 'POST',
            body: JSON.stringify(userData),
        });
        
        if (response.success && response.customer_id) {
            this.setCustomerId(response.customer_id);
        }
        
        return response;
    }
    
    /**
     * Purchase credits
     */
    async purchaseCredits(purchaseData) {
        if (!this.customerId) {
            throw new Error('Customer ID not found. Please sign up first.');
        }
        
        return await this.makeRequest(`/billing/credits/purchase?customer_id=${this.customerId}`, {
            method: 'POST',
            body: JSON.stringify(purchaseData),
        });
    }
    
    /**
     * Get credit balance
     */
    async getCreditBalance() {
        if (!this.customerId) {
            throw new Error('Customer ID not found. Please sign up first.');
        }
        
        return await this.makeRequest(`/billing/credits/balance/${this.customerId}`);
    }
    
    /**
     * Generate voice
     */
    async generateVoice(voiceData) {
        if (!this.customerId) {
            throw new Error('Customer ID not found. Please sign up first.');
        }
        
        return await this.makeRequest(`/usage/generate-voice?customer_id=${this.customerId}`, {
            method: 'POST',
            body: JSON.stringify(voiceData),
        });
    }
}

// Export global instance
window.VocalisAPI = VocalisAPI;
window.vocalisAPI = new VocalisAPI();
