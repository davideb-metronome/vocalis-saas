/**
 * Plan Selector Component
 * Fetches plans and handles plan selection actions
 */

class PlanSelector {
    constructor(api) {
        this.api = api || window.vocalisAPI;
        this.tabs = {
            plans: document.getElementById('tab-plans'),
            credits: document.getElementById('tab-credits'),
        };
        this.sections = {
            plans: document.getElementById('plans-section'),
            credits: document.getElementById('credits-section'),
        };
        this.planButtons = Array.from(document.querySelectorAll('.plan-select-btn'));
        this.status = document.getElementById('plan-status');
        this.init();
    }

    init() {
        // Tabs
        if (this.tabs.plans && this.tabs.credits) {
            this.tabs.plans.addEventListener('click', () => this.showSection('plans'));
            this.tabs.credits.addEventListener('click', () => this.showSection('credits'));
        }

        // Plan buttons
        this.planButtons.forEach(btn => {
            btn.addEventListener('click', () => this.selectPlan(btn.dataset.plan));
        });

        // Load plans to populate numbers
        this.refreshPlans();
    }

    showSection(which) {
        const setActive = (tabEl, active) => {
            tabEl.classList.toggle('active', active);
            tabEl.setAttribute('aria-selected', active ? 'true' : 'false');
        };
        const show = (el, on) => el.classList.toggle('hidden', !on);

        if (which === 'plans') {
            setActive(this.tabs.plans, true);
            setActive(this.tabs.credits, false);
            show(this.sections.plans, true);
            show(this.sections.credits, false);
        } else {
            setActive(this.tabs.plans, false);
            setActive(this.tabs.credits, true);
            show(this.sections.plans, false);
            show(this.sections.credits, true);
        }
    }

    async refreshPlans() {
        try {
            const data = await this.api.getPlans();
            // Populate trial / creator / pro text if present
            const creator = data.plans.find(p => p.id === 'creator');
            const pro = data.plans.find(p => p.id === 'pro');
            const trial = data.plans.find(p => p.id === 'trial');

            if (creator) {
                const price = document.getElementById('creator-price');
                const credits = document.getElementById('creator-credits');
                if (price) price.textContent = `$${creator.price_usd} / month`;
                if (credits) credits.textContent = `${this.formatNumber(creator.monthly_credits)} credits / month`;
            }
            if (pro) {
                const price = document.getElementById('pro-price');
                const credits = document.getElementById('pro-credits');
                if (price) price.textContent = `$${pro.price_usd} / month`;
                if (credits) credits.textContent = `${this.formatNumber(pro.monthly_credits)} credits / month`;
            }
            if (trial) {
                const credits = document.getElementById('trial-credits');
                if (credits) credits.textContent = `${this.formatNumber(trial.monthly_credits)} credits for ${trial.trial_days} days`;
            }
        } catch (e) {
            console.warn('Failed to load plans:', e.message);
        }
    }

    async selectPlan(planId) {
        try {
            if (!this.api.getCustomerId()) {
                notifications.error('Please sign up or sign in first.');
                return;
            }
            const btn = document.querySelector(`.plan-select-btn[data-plan="${planId}"]`);
            if (btn) LoadingStateManager.showLoading(btn, 'Processing...');

            const res = await this.api.selectPlan(planId);
            if (res.success) {
                notifications.success(res.message || 'Plan activated');
                // After plan selection, go to dashboard
                setTimeout(() => { window.location.href = '/dashboard'; }, 1200);
            } else {
                notifications.error(res.message || 'Plan selection failed');
            }
        } catch (e) {
            notifications.error(`Plan selection failed: ${e.message}`);
        } finally {
            const btn = document.querySelector(`.plan-select-btn[data-plan="${planId}"]`);
            if (btn) LoadingStateManager.hideLoading(btn);
        }
    }

    formatNumber(n) {
        return (n ?? 0).toLocaleString();
    }
}

// Expose
window.PlanSelector = PlanSelector;

