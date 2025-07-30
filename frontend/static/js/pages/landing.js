/**
 * Landing Page Logic
 * Handles landing page interactions and animations
 */

class LandingPage {
    constructor() {
        this.init();
    }

    init() {
        // Smooth scrolling for anchor links
        this.setupSmoothScrolling();
        
        // Add interaction effects
        this.setupInteractionEffects();
        
        // Show welcome notification
        setTimeout(() => {
            notifications.info('Welcome to Vocalis! 🎉');
        }, 50000);

        console.log('✅ Landing page initialized');
    }

    setupSmoothScrolling() {
        // Handle smooth scrolling for navigation links
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', (e) => {
                e.preventDefault();
                const target = document.querySelector(anchor.getAttribute('href'));
                
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            });
        });
    }

    setupInteractionEffects() {
        // Add hover effects to feature cards
        const featureCards = document.querySelectorAll('.feature-card');
        featureCards.forEach(card => {
            card.addEventListener('mouseenter', () => {
                card.style.transform = 'translateY(-5px)';
            });
            
            card.addEventListener('mouseleave', () => {
                card.style.transform = 'translateY(0)';
            });
        });

        // Add click tracking for CTA buttons
        const ctaButtons = document.querySelectorAll('.btn-large.primary');
        ctaButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                // Track CTA click
                console.log('CTA clicked:', button.textContent.trim());
                
                // Add subtle animation
                button.style.transform = 'scale(0.98)';
                setTimeout(() => {
                    button.style.transform = '';
                }, 150);
            });
        });

        // Demo button handling
        const demoButtons = document.querySelectorAll('a[href="#demo"]');
        demoButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                this.showDemoModal();
            });
        });
    }

    showDemoModal() {
        // Show demo notification (placeholder for future demo modal)
        notifications.info('🎬 Demo video coming soon! For now, try our free trial.');
    }

    // Utility method to animate elements on scroll (if needed in future)
    setupScrollAnimations() {
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animate-in');
                }
            });
        }, observerOptions);

        // Observe elements that should animate in
        const animateElements = document.querySelectorAll('.feature-card, .pricing-card');
        animateElements.forEach(el => observer.observe(el));
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.landingPage = new LandingPage();
});