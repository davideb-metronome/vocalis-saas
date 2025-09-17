class TrialBanner {
    constructor() {
        this.el = document.getElementById('trial-banner');
        this.daysEl = document.getElementById('trial-days');
        this.endEl = document.getElementById('trial-end');
    }

    async checkOnLoad() {
        try {
            const customerId = sessionStorage.getItem('vocalis_customer_id');
            if (!customerId) return;
            const res = await fetch(`/api/billing/trial-status?customer_id=${customerId}`);
            if (!res.ok) return;
            const data = await res.json();
            if (data.is_trial && data.days_left > 0 && data.days_left <= 3) {
                this.showPush({ days_left: data.days_left, end_at_utc: data.end_at_utc });
            }
        } catch (e) {
            console.warn('trial-status fetch failed', e);
        }
    }

    showPush(data) {
        if (!this.el) return;
        if (this.daysEl && data.days_left) this.daysEl.textContent = `${data.days_left}`;
        if (this.endEl && data.end_at_utc) this.endEl.textContent = `Ends ${data.end_at_utc}`;
        this.el.classList.remove('hidden');
        // Suppress demo toast; show only the on-page red banner
        // notifications.info('🔔 Trial ends soon — conversion push displayed');
    }
}

window.TrialBanner = TrialBanner;
