/**
 * Voice Generator Component
 * Handles voice generation and voice option selection
 */

class VoiceGenerator {
    constructor() {
        this.STANDARD_VOICE_COST = 1; // 1 credit per character
        this.PREMIUM_VOICE_COST = 2; // 2 credits per character
        this.VOICE_CLONE_COST = 25000; // 25,000 credits for voice cloning
        this.CREDIT_RATE = 0.00025; // $0.00025 per credit

        this.selectedVoice = 'Standard Voice';
        this.selectedVoiceType = 'standard';
        this.selectedCostPerChar = 1;
        this.hasCustomClone = false;

        this.elements = {
            textInput: document.getElementById('text-input'),
            characterCount: document.getElementById('character-count'),
            creditEstimate: document.getElementById('credit-estimate'),
            voiceOptions: document.getElementById('voice-options'),
            generateBtn: document.getElementById('generate-btn'),
            cloneCostDisplay: document.getElementById('clone-cost-display')
        };

        this.init();
    }

    init() {
        if (!this.elements.textInput || !this.elements.generateBtn) {
            console.warn('Voice Generator: Required elements not found');
            return;
        }

        // Bind event listeners
        this.elements.textInput.addEventListener('input', () => this.updateCreditEstimate());
        this.elements.generateBtn.addEventListener('click', () => this.handleGenerate());

        // Bind voice option clicks
        if (this.elements.voiceOptions) {
            this.elements.voiceOptions.addEventListener('click', (e) => {
                const option = e.target.closest('.voice-option');
                if (option) {
                    this.handleVoiceClick(option);
                }
            });
        }

        // Initial update
        this.updateCreditEstimate();

        console.log('✅ Voice generator initialized');
    }

    handleVoiceClick(optionElement) {
        const voiceType = optionElement.dataset.type;
        const costPerChar = parseInt(optionElement.dataset.cost);
        
        if (!voiceType) return;

        const text = this.elements.textInput.value || '';
        const characterCount = text.length;

        if (characterCount === 0 && voiceType !== 'standard') {
            notifications.warning('Please enter some text first!');
            return;
        }

        // Update selection visually
        document.querySelectorAll('.voice-option').forEach(option => {
            option.classList.remove('selected');
        });
        optionElement.classList.add('selected');

        // Update tracking variables
        this.selectedVoiceType = voiceType;
        this.selectedCostPerChar = costPerChar;

        const voiceNames = {
            'standard': 'Standard Voice',
            'premium': 'Premium Voice',
            'clone': 'Clone Voice'
        };
        this.selectedVoice = voiceNames[voiceType];

        if (voiceType === 'clone') {
            this.handleCloneVoice(characterCount);
        } else {
            this.updateCreditEstimate();
            notifications.info(`Selected ${this.selectedVoice}`);
        }
    }

    async handleCloneVoice(characterCount) {
        if (!this.hasCustomClone) {
            // Show setup confirmation
            const setupCost = this.VOICE_CLONE_COST * this.CREDIT_RATE;
            const confirmed = confirm(
                `Create your voice clone?\n\n` +
                `This will cost ${this.VOICE_CLONE_COST.toLocaleString()} credits (~$${setupCost.toFixed(2)}) one-time.\n\n` +
                `After setup, you can use your clone at standard rates (1 credit/character).`
            );

            if (confirmed) {
                await this.createVoiceCloneSetup();
            }
        } else {
            // Use existing clone
            this.updateCreditEstimate();
            notifications.info('Using your custom voice clone');
        }
    }

    async createVoiceCloneSetup() {
        try {
            // Show loading on clone option
            const cloneOption = document.querySelector('.clone-option');
            const voiceName = cloneOption.querySelector('.voice-name');
            const voiceDescription = cloneOption.querySelector('.voice-description');
            const creditCost = cloneOption.querySelector('.credit-cost');

            const originalName = voiceName.textContent;
            const originalDescription = voiceDescription.textContent;
            const originalCost = creditCost.textContent;

            voiceName.textContent = 'Creating Clone...';
            voiceDescription.textContent = 'This may take a moment';
            creditCost.textContent = 'Processing...';
            cloneOption.style.pointerEvents = 'none';

            // Call API to create voice clone
            const result = await vocalisAPI.generateVoice({
                text: '',
                voice_name: 'Custom Clone',
                voice_type: 'clone',
                character_count: 0
            });

            if (result.success) {
                const actualCreditsUsed = result.credits_consumed || this.VOICE_CLONE_COST;
                const dollarCost = actualCreditsUsed * this.CREDIT_RATE;

                this.hasCustomClone = true;
                this.updateCloneDisplay();

                notifications.success(
                    `✓ Voice clone created successfully! Used ${actualCreditsUsed.toLocaleString()} credits (~$${dollarCost.toFixed(2)})`
                );

                // Update credit display
                window.creditDisplayManager?.refreshBalance();

            } else {
                throw new Error(result.message || 'Clone creation failed');
            }

        } catch (error) {
            console.error('Voice cloning failed:', error);
            
            if (error.message.includes('not implemented')) {
                notifications.info('✨ Voice clone feature coming soon! (Backend API not implemented)');
            } else {
                notifications.error(`Voice cloning failed: ${error.message}`);
            }
        } finally {
            // Restore original content
            setTimeout(() => {
                const cloneOption = document.querySelector('.clone-option');
                if (cloneOption && !this.hasCustomClone) {
                    const voiceName = cloneOption.querySelector('.voice-name');
                    const voiceDescription = cloneOption.querySelector('.voice-description');
                    const creditCost = cloneOption.querySelector('.credit-cost');

                    if (voiceName) voiceName.textContent = 'Clone Voice';
                    if (voiceDescription) voiceDescription.textContent = 'Create or use your custom voice';
                    if (creditCost) creditCost.textContent = '25,000 credits setup';
                }
                cloneOption.style.pointerEvents = '';
            }, 1000);
        }
    }

    updateCloneDisplay() {
        if (this.elements.cloneCostDisplay) {
            this.elements.cloneCostDisplay.textContent = this.hasCustomClone 
                ? '1 credit/character' 
                : '25,000 credits setup';
        }
    }

    updateCreditEstimate() {
        const text = this.elements.textInput.value || '';
        const characterCount = text.length;

        // Update character count
        if (this.elements.characterCount) {
            this.elements.characterCount.textContent = `${characterCount} characters`;
        }

        // Calculate credits needed
        let creditsNeeded;
        if (this.selectedVoiceType === 'clone' && this.hasCustomClone) {
            creditsNeeded = characterCount * 1; // Clone uses standard rate after setup
        } else if (this.selectedVoiceType === 'clone') {
            creditsNeeded = this.VOICE_CLONE_COST; // Setup cost
        } else {
            creditsNeeded = characterCount * this.selectedCostPerChar;
        }

        const dollarCost = creditsNeeded * this.CREDIT_RATE;

        // Update credit estimate
        // if (this.elements.creditEstimate) {
        //     if (this.selectedVoiceType === 'clone' && !this.hasCustomClone) {
        //         this.elements.creditEstimate.innerHTML = `
        //             <strong>Clone Voice:</strong> One-time setup cost ${this.VOICE_CLONE_COST.toLocaleString()} credits (~$${(this.VOICE_CLONE_COST * this.CREDIT_RATE).toFixed(2)})
        //         `;
        //     } else {
        //         this.elements.creditEstimate.innerHTML = `
        //             <strong>Estimated cost:</strong> ${creditsNeeded.toLocaleString()} credits (~$${dollarCost.toFixed(2)}) with ${this.selectedVoice}
        //         `;
        //     }
        // }
            // if (this.elements.creditEstimate) {
            //     const dollarCost = creditsNeeded * this.CREDIT_RATE;
            //     if (this.selectedVoiceType === 'clone' && !this.hasCustomClone) {
            //         this.elements.creditEstimate.innerHTML = `
            //             <strong>Clone Voice:</strong> One-time setup cost ${this.VOICE_CLONE_COST.toLocaleString()} VC <span class="dollar-reference">(≈ $${(this.VOICE_CLONE_COST * this.CREDIT_RATE).toFixed(2)})</span>
            //         `;
            //     } else {
            //         this.elements.creditEstimate.innerHTML = `
            //             <strong>Estimated cost:</strong> ${creditsNeeded.toLocaleString()} VC <span class="dollar-reference">(≈ $${dollarCost.toFixed(2)})</span> with ${this.selectedVoice}
            //         `;
            //     }

        if (this.elements.creditEstimate) {
            const dollarCost = creditsNeeded * this.CREDIT_RATE;
            if (this.selectedVoiceType === 'clone' && !this.hasCustomClone) {
                this.elements.creditEstimate.innerHTML = `
                    <strong>Clone Voice:</strong> One-time setup cost ${this.VOICE_CLONE_COST.toLocaleString()} credits <span class="dollar-reference">(≈ $${(this.VOICE_CLONE_COST * this.CREDIT_RATE).toFixed(2)})</span>
                `;
            } else {
                this.elements.creditEstimate.innerHTML = `
                    <strong>Estimated cost:</strong> ${creditsNeeded.toLocaleString()} credits <span class="dollar-reference">(≈ $${dollarCost.toFixed(2)})</span> with ${this.selectedVoice}
                `;
        }


}
    }

    async handleGenerate() {
        const text = this.elements.textInput.value?.trim();
        
        if (!text) {
            notifications.warning('Please enter some text to convert');
            return;
        }

        const characterCount = text.length;
        let creditsNeeded;

        if (this.selectedVoiceType === 'clone' && this.hasCustomClone) {
            creditsNeeded = characterCount * 1;
        } else if (this.selectedVoiceType === 'clone') {
            creditsNeeded = this.VOICE_CLONE_COST;
        } else {
            creditsNeeded = characterCount * this.selectedCostPerChar;
        }

        try {
            // Show loading state
            this.elements.generateBtn.disabled = true;
            this.elements.generateBtn.textContent = 'Generating...';

            // Call API
            const result = await vocalisAPI.generateVoice({
                text: text,
                voice_name: this.selectedVoice,
                voice_type: this.selectedVoiceType,
                character_count: characterCount
            });

            if (result.success) {
                const actualCreditsUsed = result.credits_consumed || creditsNeeded;
                const dollarCost = actualCreditsUsed * this.CREDIT_RATE;

                // notifications.success(
                //     `✓ Voice generated with ${this.selectedVoice}! Used ${actualCreditsUsed.toLocaleString()} credits (~$${dollarCost.toFixed(2)})`
                // );

                    notifications.success(
                     `✓ Voice generated with ${this.selectedVoice}! Used ${actualCreditsUsed.toLocaleString()} credits (≈ $${dollarCost.toFixed(2)})`
                );

                // Update balance immediately
                if (result.new_balance !== undefined && window.creditDisplayManager) {
                    window.creditDisplayManager.updateCreditsDisplay(
                        result.new_balance, 
                        result.new_balance, 
                        actualCreditsUsed, 
                        'voice_generation'
                    );
                } else {
                    window.creditDisplayManager?.refreshBalance();
                }

            } else {
                throw new Error(result.message || 'Generation failed');
            }

        } catch (error) {
            console.error('Voice generation failed:', error);
            
            if (error.message.includes('Insufficient credits')) {
                notifications.error(`❌ Not enough credits! You need ${creditsNeeded.toLocaleString()} credits.`);
            } else if (error.message.includes('not implemented')) {
                notifications.info('✨ Voice generation feature working! (Backend API coming soon)');
            } else {
                notifications.error(`❌ Generation failed: ${error.message}`);
            }
        } finally {
            // Restore button
            this.elements.generateBtn.disabled = false;
            this.elements.generateBtn.textContent = 'Generate Voice';
        }
    }
}

// Export for use in other modules
window.VoiceGenerator = VoiceGenerator;