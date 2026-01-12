/**
 * Print Feedback Modal - Automatically prompts for feedback after print completion
 */

class FeedbackModal {
    constructor() {
        this.checkInterval = 30000; // Check every 30 seconds
        this.isChecking = false;
        this.createModal();
        this.startPolling();
    }

    createModal() {
        const modalHTML = `
            <div id="feedbackModal" class="modal" style="display: none;">
                <div class="modal-content">
                    <span class="modal-close" onclick="feedbackModal.closeModal()">&times;</span>
                    <h2>🖨️ Print Completed!</h2>
                    <div id="feedbackContent">
                        <p id="feedbackFilename" style="color: #00bcd4; margin-bottom: 20px;"></p>
                        
                        <div class="feedback-form">
                            <div class="form-group">
                                <label>How did the print go?</label>
                                <div class="button-group">
                                    <button class="btn-feedback btn-success" onclick="feedbackModal.setResult('success')">
                                        ✓ Success
                                    </button>
                                    <button class="btn-feedback btn-failure" onclick="feedbackModal.setResult('failure')">
                                        ✗ Failed
                                    </button>
                                </div>
                            </div>

                            <div id="failureTypeGroup" style="display: none;">
                                <div class="form-group">
                                    <label>What went wrong?</label>
                                    <select id="failureType" class="form-select">
                                        <option value="">Select issue...</option>
                                        <option value="under_extrusion">Under-extrusion</option>
                                        <option value="over_extrusion">Over-extrusion</option>
                                        <option value="stringing">Stringing</option>
                                        <option value="adhesion">Bed adhesion issue</option>
                                        <option value="warping">Warping</option>
                                        <option value="layer_shift">Layer shift</option>
                                        <option value="blobs">Blobs/zits</option>
                                        <option value="other">Other</option>
                                    </select>
                                </div>
                            </div>

                            <div class="form-group">
                                <label>Quality Rating (optional)</label>
                                <div class="rating-group">
                                    <button class="btn-rating" onclick="feedbackModal.setRating(1)">1 ⭐</button>
                                    <button class="btn-rating" onclick="feedbackModal.setRating(2)">2 ⭐</button>
                                    <button class="btn-rating" onclick="feedbackModal.setRating(3)">3 ⭐</button>
                                    <button class="btn-rating" onclick="feedbackModal.setRating(4)">4 ⭐</button>
                                    <button class="btn-rating" onclick="feedbackModal.setRating(5)">5 ⭐</button>
                                </div>
                            </div>

                            <div class="form-group">
                                <label>Notes (optional)</label>
                                <textarea id="feedbackNotes" rows="3" placeholder="Any additional comments..."></textarea>
                            </div>

                            <div class="form-actions">
                                <button class="btn-submit" onclick="feedbackModal.submitFeedback()">Submit Feedback</button>
                                <button class="btn-dismiss" onclick="feedbackModal.dismissFeedback()">Maybe Later</button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Inject modal HTML
        const div = document.createElement('div');
        div.innerHTML = modalHTML;
        document.body.appendChild(div.firstElementChild);

        // Inject modal styles
        this.injectStyles();
    }

    injectStyles() {
        const styles = `
            .modal {
                display: none;
                position: fixed;
                z-index: 9999;
                left: 0;
                top: 0;
                width: 100%;
                height: 100%;
                background-color: rgba(0,0,0,0.8);
                animation: fadeIn 0.3s;
            }

            @keyframes fadeIn {
                from { opacity: 0; }
                to { opacity: 1; }
            }

            .modal-content {
                background-color: #1e1e1e;
                margin: 5% auto;
                padding: 30px;
                border: 1px solid #00bcd4;
                border-radius: 12px;
                width: 90%;
                max-width: 500px;
                box-shadow: 0 4px 20px rgba(0,188,212,0.3);
                animation: slideIn 0.3s;
            }

            @keyframes slideIn {
                from { transform: translateY(-50px); opacity: 0; }
                to { transform: translateY(0); opacity: 1; }
            }

            .modal-close {
                color: #9e9e9e;
                float: right;
                font-size: 28px;
                font-weight: bold;
                cursor: pointer;
                transition: color 0.2s;
            }

            .modal-close:hover {
                color: #00bcd4;
            }

            .feedback-form {
                margin-top: 20px;
            }

            .form-group {
                margin-bottom: 20px;
            }

            .form-group label {
                display: block;
                color: #00bcd4;
                margin-bottom: 10px;
                font-weight: 500;
            }

            .button-group {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 10px;
            }

            .btn-feedback {
                padding: 15px;
                font-size: 16px;
                border: 2px solid transparent;
                border-radius: 6px;
                cursor: pointer;
                transition: all 0.2s;
            }

            .btn-success {
                background: #2e7d32;
                color: white;
            }

            .btn-success:hover, .btn-success.selected {
                background: #4caf50;
                border-color: #81c784;
            }

            .btn-failure {
                background: #c62828;
                color: white;
            }

            .btn-failure:hover, .btn-failure.selected {
                background: #f44336;
                border-color: #ef5350;
            }

            .form-select {
                width: 100%;
                padding: 10px;
                background: #2a2a2a;
                border: 1px solid #424242;
                border-radius: 6px;
                color: #e0e0e0;
                font-size: 14px;
            }

            .rating-group {
                display: flex;
                gap: 8px;
            }

            .btn-rating {
                flex: 1;
                padding: 10px;
                background: #2a2a2a;
                border: 2px solid #424242;
                border-radius: 6px;
                color: #e0e0e0;
                cursor: pointer;
                transition: all 0.2s;
            }

            .btn-rating:hover, .btn-rating.selected {
                background: #00bcd4;
                border-color: #00bcd4;
                color: #121212;
            }

            textarea {
                width: 100%;
                padding: 10px;
                background: #2a2a2a;
                border: 1px solid #424242;
                border-radius: 6px;
                color: #e0e0e0;
                font-family: inherit;
                resize: vertical;
            }

            .form-actions {
                display: flex;
                gap: 10px;
                margin-top: 25px;
            }

            .btn-submit {
                flex: 2;
                padding: 12px 24px;
                background: #00bcd4;
                color: #121212;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                cursor: pointer;
                transition: all 0.2s;
            }

            .btn-submit:hover {
                background: #00acc1;
                transform: translateY(-2px);
                box-shadow: 0 4px 8px rgba(0,188,212,0.3);
            }

            .btn-dismiss {
                flex: 1;
                padding: 12px;
                background: #424242;
                color: #e0e0e0;
                border: none;
                border-radius: 6px;
                cursor: pointer;
                transition: all 0.2s;
            }

            .btn-dismiss:hover {
                background: #555;
            }
        `;

        const styleSheet = document.createElement('style');
        styleSheet.textContent = styles;
        document.head.appendChild(styleSheet);
    }

    startPolling() {
        // Check immediately
        this.checkPendingFeedback();
        
        // Then check periodically
        setInterval(() => this.checkPendingFeedback(), this.checkInterval);
    }

    async checkPendingFeedback() {
        if (this.isChecking) return;
        
        try {
            this.isChecking = true;
            const response = await fetch(`${API_BASE}/pending-feedback`);
            const data = await response.json();
            
            if (data.pending_feedback && data.pending_feedback.length > 0) {
                // Show modal for first pending feedback
                this.showFeedbackModal(data.pending_feedback[0]);
            }
        } catch (error) {
            console.error('Error checking pending feedback:', error);
        } finally {
            this.isChecking = false;
        }
    }

    showFeedbackModal(pendingFeedback) {
        this.currentFeedback = pendingFeedback;
        this.selectedResult = null;
        this.selectedRating = null;
        
        document.getElementById('feedbackFilename').textContent = 
            `File: ${pendingFeedback.filename}`;
        
        document.getElementById('feedbackModal').style.display = 'block';
        
        // Reset form
        document.querySelectorAll('.btn-feedback').forEach(btn => btn.classList.remove('selected'));
        document.querySelectorAll('.btn-rating').forEach(btn => btn.classList.remove('selected'));
        document.getElementById('failureTypeGroup').style.display = 'none';
        document.getElementById('failureType').value = '';
        document.getElementById('feedbackNotes').value = '';
    }

    closeModal() {
        document.getElementById('feedbackModal').style.display = 'none';
    }

    setResult(result) {
        this.selectedResult = result;
        
        document.querySelectorAll('.btn-feedback').forEach(btn => btn.classList.remove('selected'));
        event.target.classList.add('selected');
        
        document.getElementById('failureTypeGroup').style.display = 
            result === 'failure' ? 'block' : 'none';
    }

    setRating(rating) {
        this.selectedRating = rating;
        
        document.querySelectorAll('.btn-rating').forEach(btn => btn.classList.remove('selected'));
        event.target.classList.add('selected');
    }

    async submitFeedback() {
        if (!this.selectedResult) {
            alert('Please select if the print was successful or not');
            return;
        }

        const feedbackData = {
            printer_id: this.currentFeedback.printer_id || 'default',
            material: 'PLA', // TODO: Get from print metadata
            profile: 'standard',
            profile_version: 1,
            result: this.selectedResult,
            failure_type: this.selectedResult === 'failure' ? 
                document.getElementById('failureType').value : null,
            quality_rating: this.selectedRating,
            notes: document.getElementById('feedbackNotes').value
        };

        try {
            const response = await fetch(`${API_BASE}/feedback`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(feedbackData)
            });

            if (response.ok) {
                // Mark as submitted
                await fetch(`${API_BASE}/pending-feedback/${this.currentFeedback.id}/submit`, {
                    method: 'POST'
                });
                
                alert('✓ Feedback submitted! Thank you for helping improve print quality.');
                this.closeModal();
            } else {
                alert('Failed to submit feedback. Please try again.');
            }
        } catch (error) {
            console.error('Error submitting feedback:', error);
            alert('Error submitting feedback. Please try again.');
        }
    }

    async dismissFeedback() {
        try {
            await fetch(`${API_BASE}/pending-feedback/${this.currentFeedback.id}/dismiss`, {
                method: 'POST'
            });
            this.closeModal();
        } catch (error) {
            console.error('Error dismissing feedback:', error);
        }
    }
}

// Initialize when DOM is ready
let feedbackModal;
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        feedbackModal = new FeedbackModal();
    });
} else {
    feedbackModal = new FeedbackModal();
}
