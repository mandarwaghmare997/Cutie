// Qryti - ISO 42001 Compliance Platform - Dashboard Module

class DashboardManager {
    constructor() {
        this.assessments = [];
        this.stats = {};
        this.init();
    }

    init() {
        this.bindEvents();
    }

    bindEvents() {
        // New assessment button
        const newAssessmentBtn = utils.$('#new-assessment-btn');
        if (newAssessmentBtn) {
            newAssessmentBtn.addEventListener('click', () => {
                this.showNewAssessmentModal();
            });
        }

        // Navigation links
        const navLinks = utils.$$('.nav-link');
        navLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const page = link.dataset.page;
                this.navigateToPage(page);
            });
        });

        // Profile form
        const profileForm = utils.$('#profile-form');
        if (profileForm) {
            profileForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleProfileUpdate(profileForm);
            });
        }
    }

    async loadDashboardData() {
        try {
            // Load assessments and stats in parallel
            const [assessmentsResponse, statsResponse] = await Promise.all([
                api.assessments.getAll({ limit: 10 }),
                this.getDashboardStats()
            ]);

            this.assessments = assessmentsResponse.assessments || [];
            this.stats = statsResponse;

            this.updateDashboardUI();

        } catch (error) {
            utils.errorHandler.handle(error, 'Dashboard');
        }
    }

    async getDashboardStats() {
        try {
            // Calculate stats from assessments
            const assessments = await api.assessments.getAll();
            
            const stats = {
                totalAssessments: assessments.assessments?.length || 0,
                activeAssessments: 0,
                completedAssessments: 0,
                averageScore: 0,
                certificates: 0,
                overallProgress: 0
            };

            if (assessments.assessments && assessments.assessments.length > 0) {
                assessments.assessments.forEach(assessment => {
                    if (assessment.status === 'in_progress') {
                        stats.activeAssessments++;
                    } else if (assessment.status === 'completed') {
                        stats.completedAssessments++;
                        if (assessment.finalScore >= 70) {
                            stats.certificates++;
                        }
                    }
                });

                // Calculate average score
                const completedWithScores = assessments.assessments.filter(a => 
                    a.status === 'completed' && a.finalScore !== null
                );
                
                if (completedWithScores.length > 0) {
                    stats.averageScore = completedWithScores.reduce((sum, a) => 
                        sum + a.finalScore, 0) / completedWithScores.length;
                }

                // Calculate overall progress
                const totalProgress = assessments.assessments.reduce((sum, a) => {
                    const progress = a.progress || {};
                    return sum + (progress.overall || 0);
                }, 0);
                
                stats.overallProgress = totalProgress / assessments.assessments.length;
            }

            return stats;

        } catch (error) {
            console.error('Error calculating dashboard stats:', error);
            return {
                totalAssessments: 0,
                activeAssessments: 0,
                completedAssessments: 0,
                averageScore: 0,
                certificates: 0,
                overallProgress: 0
            };
        }
    }

    updateDashboardUI() {
        // Update progress circle
        const progressCircle = utils.$('.progress-circle-large');
        if (progressCircle) {
            utils.progress.animateProgress(progressCircle, this.stats.overallProgress);
        }

        // Update stat cards
        this.updateStatCard('active-assessments', this.stats.activeAssessments);
        this.updateStatCard('compliance-score', 
            this.stats.averageScore > 0 ? Math.round(this.stats.averageScore) + '%' : '--'
        );
        this.updateStatCard('certificates', this.stats.certificates);

        // Update recent assessments
        this.updateRecentAssessments();
    }

    updateStatCard(type, value) {
        // Find the stat card by looking for specific text content
        const cards = utils.$$('.dashboard-card');
        
        cards.forEach(card => {
            const title = card.querySelector('.card-title');
            if (!title) return;

            let shouldUpdate = false;
            
            if (type === 'active-assessments' && title.textContent.includes('Active Assessments')) {
                shouldUpdate = true;
            } else if (type === 'compliance-score' && title.textContent.includes('Compliance Score')) {
                shouldUpdate = true;
            } else if (type === 'certificates' && title.textContent.includes('Certificates')) {
                shouldUpdate = true;
            }

            if (shouldUpdate) {
                const statValue = card.querySelector('.stat-value');
                if (statValue) {
                    statValue.textContent = value;
                    statValue.classList.add('animate-fade-in');
                }
            }
        });
    }

    updateRecentAssessments() {
        // This would be implemented if we had a recent assessments section
        // For now, we'll just log the assessments
        console.log('Recent assessments:', this.assessments.slice(0, 5));
    }

    navigateToPage(page) {
        switch (page) {
            case 'dashboard':
                auth.showPage('dashboard-page');
                this.loadDashboardData();
                break;
            case 'assessments':
                auth.showPage('assessment-page');
                if (window.assessments) {
                    assessments.loadAssessments();
                }
                break;
            case 'profile':
                auth.showPage('profile-page');
                break;
            default:
                console.warn('Unknown page:', page);
        }
    }

    async showNewAssessmentModal() {
        const modalContent = `
            <div class="modal-header">
                <h3 class="modal-title">Start New Assessment</h3>
                <button class="modal-close" onclick="utils.modal.close()">
                    <i data-lucide="x"></i>
                </button>
            </div>
            <div class="modal-body">
                <form id="new-assessment-form">
                    <div class="form-group">
                        <label for="assessment-name" class="form-label">Assessment Name</label>
                        <input type="text" id="assessment-name" name="name" class="form-input" 
                               placeholder="e.g., Q1 2024 AI Compliance Assessment" required>
                    </div>
                    
                    <div class="form-group">
                        <label for="ai-system-name" class="form-label">AI System Name</label>
                        <input type="text" id="ai-system-name" name="aiSystemName" class="form-input" 
                               placeholder="e.g., Customer Service Chatbot" required>
                    </div>
                    
                    <div class="form-group">
                        <label for="ai-system-description" class="form-label">AI System Description</label>
                        <textarea id="ai-system-description" name="aiSystemDescription" class="form-textarea" 
                                  placeholder="Describe the AI system, its purpose, and key functionalities..." required></textarea>
                    </div>
                    
                    <div class="form-row">
                        <div class="form-group">
                            <label for="risk-level" class="form-label">Risk Level</label>
                            <select id="risk-level" name="riskLevel" class="form-select" required>
                                <option value="">Select risk level</option>
                                <option value="low">Low Risk</option>
                                <option value="medium">Medium Risk</option>
                                <option value="high">High Risk</option>
                                <option value="critical">Critical Risk</option>
                            </select>
                        </div>
                        
                        <div class="form-group">
                            <label for="target-completion" class="form-label">Target Completion</label>
                            <input type="date" id="target-completion" name="targetCompletion" class="form-input">
                        </div>
                    </div>
                    
                    <div class="form-group">
                        <label for="regulatory-requirements" class="form-label">Regulatory Requirements</label>
                        <textarea id="regulatory-requirements" name="regulatoryRequirements" class="form-textarea" 
                                  placeholder="List any specific regulatory requirements or standards that apply..."></textarea>
                    </div>
                    
                    <div class="modal-footer">
                        <button type="button" class="btn btn-outline" onclick="utils.modal.close()">Cancel</button>
                        <button type="submit" class="btn btn-primary">
                            <i data-lucide="plus"></i>
                            Create Assessment
                        </button>
                    </div>
                </form>
            </div>
        `;

        utils.modal.show(modalContent, { size: 'large' });

        // Bind form submission
        const form = utils.$('#new-assessment-form');
        if (form) {
            form.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleNewAssessment(form);
            });
        }

        // Set default target completion date (30 days from now)
        const targetInput = utils.$('#target-completion');
        if (targetInput) {
            const defaultDate = new Date();
            defaultDate.setDate(defaultDate.getDate() + 30);
            targetInput.value = defaultDate.toISOString().split('T')[0];
        }
    }

    async handleNewAssessment(form) {
        const submitBtn = form.querySelector('button[type="submit"]');
        utils.form.setLoading(submitBtn, true);
        utils.form.clearAllErrors(form);

        try {
            const formData = utils.form.serialize(form);
            const errors = utils.form.validate(form);

            if (errors.length > 0) {
                utils.errorHandler.validation(errors);
                return;
            }

            const assessmentData = {
                name: formData.name,
                aiSystemName: formData.aiSystemName,
                aiSystemDescription: formData.aiSystemDescription,
                riskLevel: formData.riskLevel,
                targetCompletion: formData.targetCompletion || null,
                regulatoryRequirements: formData.regulatoryRequirements || null,
                organizationName: auth.getCurrentUser()?.organization || 'Unknown Organization',
                industry: auth.getCurrentUser()?.industry || 'Unknown'
            };

            const response = await api.assessments.create(assessmentData);
            
            utils.modal.close();
            utils.toast.success('Assessment created successfully!');
            
            // Refresh dashboard data
            await this.loadDashboardData();
            
            // Navigate to assessments page
            this.navigateToPage('assessments');

        } catch (error) {
            utils.errorHandler.handle(error, 'Create Assessment');
        } finally {
            utils.form.setLoading(submitBtn, false);
        }
    }

    async handleProfileUpdate(form) {
        const submitBtn = form.querySelector('button[type="submit"]');
        utils.form.setLoading(submitBtn, true);
        utils.form.clearAllErrors(form);

        try {
            const formData = utils.form.serialize(form);
            const errors = utils.form.validate(form);

            if (errors.length > 0) {
                utils.errorHandler.validation(errors);
                return;
            }

            const profileData = {
                firstName: formData['first-name'],
                lastName: formData['last-name'],
                organization: formData.organization,
                industry: formData.industry,
                role: formData.role
            };

            await auth.updateProfile(profileData);

        } catch (error) {
            utils.errorHandler.handle(error, 'Profile Update');
        } finally {
            utils.form.setLoading(submitBtn, false);
        }
    }

    // Utility method to format numbers
    formatNumber(num) {
        if (num >= 1000000) {
            return (num / 1000000).toFixed(1) + 'M';
        } else if (num >= 1000) {
            return (num / 1000).toFixed(1) + 'K';
        }
        return num.toString();
    }

    // Utility method to get status color
    getStatusColor(status) {
        const colors = {
            'not_started': 'gray',
            'in_progress': 'warning',
            'completed': 'success',
            'on_hold': 'error'
        };
        return colors[status] || 'gray';
    }

    // Utility method to get risk level color
    getRiskLevelColor(riskLevel) {
        const colors = {
            'low': 'success',
            'medium': 'warning',
            'high': 'error',
            'critical': 'error'
        };
        return colors[riskLevel] || 'gray';
    }
}

// Initialize dashboard manager
const dashboard = new DashboardManager();

// Export for global use
window.dashboard = dashboard;

