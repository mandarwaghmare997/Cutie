// Qryti - ISO 42001 Compliance Platform - Assessment Modulee

class AssessmentsManager {
    constructor() {
        this.assessments = [];
        this.currentAssessment = null;
        this.controls = {};
        this.init();
    }

    init() {
        this.bindEvents();
    }

    bindEvents() {
        // This will be called when the assessments page is loaded
    }

    async loadAssessments() {
        try {
            const response = await api.assessments.getAll();
            this.assessments = response.assessments || [];
            this.renderAssessments();

        } catch (error) {
            utils.errorHandler.handle(error, 'Load Assessments');
        }
    }

    renderAssessments() {
        const container = utils.$('#assessments-list');
        if (!container) return;

        if (this.assessments.length === 0) {
            container.innerHTML = this.renderEmptyState();
            return;
        }

        const assessmentsHTML = this.assessments.map(assessment => 
            this.renderAssessmentCard(assessment)
        ).join('');

        container.innerHTML = assessmentsHTML;
        this.bindAssessmentEvents();
    }

    renderEmptyState() {
        return `
            <div class="empty-state">
                <div class="empty-icon">📋</div>
                <h3 class="empty-title">No Assessments Yet</h3>
                <p class="empty-description">
                    Start your ISO 42001 compliance journey by creating your first assessment.
                </p>
                <button class="btn btn-primary" onclick="dashboard.showNewAssessmentModal()">
                    <i data-lucide="plus"></i>
                    Create Your First Assessment
                </button>
            </div>
        `;
    }

    renderAssessmentCard(assessment) {
        const progress = assessment.progress || {};
        const overallProgress = progress.overall || 0;
        const statusClass = this.getStatusClass(assessment.status);
        const riskClass = this.getRiskClass(assessment.riskLevel);

        return `
            <div class="assessment-card" data-assessment-id="${assessment.id}">
                <div class="assessment-header">
                    <div>
                        <h3 class="assessment-title">${assessment.name}</h3>
                        <p class="assessment-org">${assessment.organizationName}</p>
                    </div>
                    <span class="assessment-status ${statusClass}">
                        ${this.formatStatus(assessment.status)}
                    </span>
                </div>
                
                <div class="assessment-details">
                    <div class="detail-item">
                        <strong>AI System:</strong> ${assessment.aiSystemName}
                    </div>
                    <div class="detail-item">
                        <strong>Risk Level:</strong> 
                        <span class="badge badge-${riskClass}">${this.formatRiskLevel(assessment.riskLevel)}</span>
                    </div>
                    <div class="detail-item">
                        <strong>Current Stage:</strong> ${this.formatStage(assessment.currentStage)}
                    </div>
                </div>
                
                <div class="assessment-progress">
                    <div class="progress-label">
                        <span class="progress-text">Overall Progress</span>
                        <span class="progress-percentage">${Math.round(overallProgress)}%</span>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${overallProgress}%"></div>
                    </div>
                </div>
                
                <div class="assessment-meta">
                    <span>Created ${utils.dateUtils.timeAgo(assessment.createdAt)}</span>
                    ${assessment.finalScore ? `<span>Score: ${Math.round(assessment.finalScore)}%</span>` : ''}
                </div>
                
                <div class="assessment-actions">
                    <button class="btn btn-outline btn-small" onclick="assessments.viewAssessment('${assessment.id}')">
                        <i data-lucide="eye"></i>
                        View
                    </button>
                    ${assessment.status === 'in_progress' ? `
                        <button class="btn btn-primary btn-small" onclick="assessments.continueAssessment('${assessment.id}')">
                            <i data-lucide="play"></i>
                            Continue
                        </button>
                    ` : ''}
                    ${assessment.status === 'completed' && assessment.finalScore >= 70 ? `
                        <button class="btn btn-success btn-small" onclick="assessments.downloadCertificate('${assessment.id}')">
                            <i data-lucide="download"></i>
                            Certificate
                        </button>
                    ` : ''}
                </div>
            </div>
        `;
    }

    bindAssessmentEvents() {
        // Events are bound via onclick attributes in the HTML
        // This approach is used for simplicity in this implementation
    }

    async viewAssessment(assessmentId) {
        try {
            const assessment = await api.assessments.get(assessmentId, true);
            this.currentAssessment = assessment;
            this.showAssessmentModal(assessment);

        } catch (error) {
            utils.errorHandler.handle(error, 'View Assessment');
        }
    }

    async continueAssessment(assessmentId) {
        try {
            const assessment = await api.assessments.get(assessmentId, true);
            this.currentAssessment = assessment;
            this.showAssessmentWorkflow(assessment);

        } catch (error) {
            utils.errorHandler.handle(error, 'Continue Assessment');
        }
    }

    showAssessmentModal(assessment) {
        const progress = assessment.progress || {};
        const stages = ['requirements_gathering', 'gap_assessment', 'policy_review', 'implementation_status', 'internal_audit'];
        
        const stageProgress = stages.map(stage => {
            const stageData = progress.stages?.[stage] || {};
            return {
                name: this.formatStage(stage),
                progress: stageData.progress || 0,
                completed: stageData.completed || false
            };
        });

        const modalContent = `
            <div class="modal-header">
                <h3 class="modal-title">${assessment.name}</h3>
                <button class="modal-close" onclick="utils.modal.close()">
                    <i data-lucide="x"></i>
                </button>
            </div>
            <div class="modal-body">
                <div class="assessment-overview">
                    <div class="overview-section">
                        <h4>Assessment Details</h4>
                        <div class="detail-grid">
                            <div class="detail-item">
                                <strong>Organization:</strong> ${assessment.organizationName}
                            </div>
                            <div class="detail-item">
                                <strong>AI System:</strong> ${assessment.aiSystemName}
                            </div>
                            <div class="detail-item">
                                <strong>Risk Level:</strong> 
                                <span class="badge badge-${this.getRiskClass(assessment.riskLevel)}">
                                    ${this.formatRiskLevel(assessment.riskLevel)}
                                </span>
                            </div>
                            <div class="detail-item">
                                <strong>Status:</strong> 
                                <span class="badge badge-${this.getStatusClass(assessment.status)}">
                                    ${this.formatStatus(assessment.status)}
                                </span>
                            </div>
                            <div class="detail-item">
                                <strong>Created:</strong> ${utils.dateUtils.format(assessment.createdAt)}
                            </div>
                            ${assessment.completedAt ? `
                                <div class="detail-item">
                                    <strong>Completed:</strong> ${utils.dateUtils.format(assessment.completedAt)}
                                </div>
                            ` : ''}
                        </div>
                    </div>
                    
                    <div class="overview-section">
                        <h4>AI System Description</h4>
                        <p>${assessment.aiSystemDescription}</p>
                    </div>
                    
                    <div class="overview-section">
                        <h4>Stage Progress</h4>
                        <div class="stage-progress">
                            ${stageProgress.map(stage => `
                                <div class="stage-item">
                                    <div class="stage-header">
                                        <span class="stage-name">${stage.name}</span>
                                        <span class="stage-percentage">${Math.round(stage.progress)}%</span>
                                    </div>
                                    <div class="progress-bar progress-bar-small">
                                        <div class="progress-fill" style="width: ${stage.progress}%"></div>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                    
                    ${assessment.finalScore ? `
                        <div class="overview-section">
                            <h4>Compliance Score</h4>
                            <div class="score-display">
                                <div class="score-circle">
                                    <span class="score-value">${Math.round(assessment.finalScore)}%</span>
                                </div>
                                <div class="score-details">
                                    <p>Overall compliance score based on ISO 42001 requirements</p>
                                    ${assessment.finalScore >= 70 ? 
                                        '<p class="score-status success">✓ Meets compliance threshold</p>' :
                                        '<p class="score-status warning">⚠ Below compliance threshold</p>'
                                    }
                                </div>
                            </div>
                        </div>
                    ` : ''}
                </div>
            </div>
            <div class="modal-footer">
                <button class="btn btn-outline" onclick="utils.modal.close()">Close</button>
                ${assessment.status === 'in_progress' ? `
                    <button class="btn btn-primary" onclick="utils.modal.close(); assessments.continueAssessment('${assessment.id}')">
                        <i data-lucide="play"></i>
                        Continue Assessment
                    </button>
                ` : ''}
                ${assessment.status === 'completed' && assessment.finalScore >= 70 ? `
                    <button class="btn btn-success" onclick="assessments.downloadCertificate('${assessment.id}')">
                        <i data-lucide="download"></i>
                        Download Certificate
                    </button>
                ` : ''}
            </div>
        `;

        utils.modal.show(modalContent, { size: 'large' });
    }

    async showAssessmentWorkflow(assessment) {
        // This would show the assessment workflow interface
        // For now, we'll show a placeholder modal
        const modalContent = `
            <div class="modal-header">
                <h3 class="modal-title">Assessment Workflow</h3>
                <button class="modal-close" onclick="utils.modal.close()">
                    <i data-lucide="x"></i>
                </button>
            </div>
            <div class="modal-body">
                <div class="workflow-container">
                    <h4>Current Stage: ${this.formatStage(assessment.currentStage)}</h4>
                    <p>The assessment workflow interface would be implemented here.</p>
                    <p>This would include:</p>
                    <ul>
                        <li>Stage-specific questionnaires</li>
                        <li>File upload capabilities</li>
                        <li>Progress tracking</li>
                        <li>Control mapping</li>
                        <li>Real-time scoring</li>
                    </ul>
                    <div class="workflow-placeholder">
                        <div class="placeholder-content">
                            <i data-lucide="construction" style="font-size: 3rem; color: var(--gray-400);"></i>
                            <p>Assessment workflow interface coming soon...</p>
                        </div>
                    </div>
                </div>
            </div>
            <div class="modal-footer">
                <button class="btn btn-outline" onclick="utils.modal.close()">Close</button>
                <button class="btn btn-primary" onclick="utils.modal.close()">
                    <i data-lucide="save"></i>
                    Save Progress
                </button>
            </div>
        `;

        utils.modal.show(modalContent, { size: 'large' });
    }

    async downloadCertificate(assessmentId) {
        try {
            utils.toast.info('Generating certificate...');
            
            // This would trigger certificate generation
            // For now, we'll show a placeholder
            utils.toast.success('Certificate generation feature coming soon!');

        } catch (error) {
            utils.errorHandler.handle(error, 'Download Certificate');
        }
    }

    // Utility methods
    getStatusClass(status) {
        const classes = {
            'not_started': 'badge-gray',
            'in_progress': 'badge-warning',
            'completed': 'badge-success',
            'on_hold': 'badge-error'
        };
        return classes[status] || 'badge-gray';
    }

    getRiskClass(riskLevel) {
        const classes = {
            'low': 'success',
            'medium': 'warning',
            'high': 'error',
            'critical': 'error'
        };
        return classes[riskLevel] || 'gray';
    }

    formatStatus(status) {
        const formats = {
            'not_started': 'Not Started',
            'in_progress': 'In Progress',
            'completed': 'Completed',
            'on_hold': 'On Hold'
        };
        return formats[status] || status;
    }

    formatRiskLevel(riskLevel) {
        const formats = {
            'low': 'Low Risk',
            'medium': 'Medium Risk',
            'high': 'High Risk',
            'critical': 'Critical Risk'
        };
        return formats[riskLevel] || riskLevel;
    }

    formatStage(stage) {
        const formats = {
            'requirements_gathering': 'Requirements Gathering',
            'gap_assessment': 'Gap Assessment',
            'policy_review': 'Policy Review',
            'implementation_status': 'Implementation Status',
            'internal_audit': 'Internal Audit'
        };
        return formats[stage] || stage;
    }

    // Search and filter methods
    filterAssessments(filters) {
        let filtered = [...this.assessments];

        if (filters.status) {
            filtered = filtered.filter(a => a.status === filters.status);
        }

        if (filters.riskLevel) {
            filtered = filtered.filter(a => a.riskLevel === filters.riskLevel);
        }

        if (filters.search) {
            const searchTerm = filters.search.toLowerCase();
            filtered = filtered.filter(a => 
                a.name.toLowerCase().includes(searchTerm) ||
                a.organizationName.toLowerCase().includes(searchTerm) ||
                a.aiSystemName.toLowerCase().includes(searchTerm)
            );
        }

        return filtered;
    }

    sortAssessments(assessments, sortBy, sortOrder = 'desc') {
        return assessments.sort((a, b) => {
            let aValue, bValue;

            switch (sortBy) {
                case 'name':
                    aValue = a.name.toLowerCase();
                    bValue = b.name.toLowerCase();
                    break;
                case 'created':
                    aValue = new Date(a.createdAt);
                    bValue = new Date(b.createdAt);
                    break;
                case 'progress':
                    aValue = a.progress?.overall || 0;
                    bValue = b.progress?.overall || 0;
                    break;
                case 'score':
                    aValue = a.finalScore || 0;
                    bValue = b.finalScore || 0;
                    break;
                default:
                    return 0;
            }

            if (aValue < bValue) return sortOrder === 'asc' ? -1 : 1;
            if (aValue > bValue) return sortOrder === 'asc' ? 1 : -1;
            return 0;
        });
    }
}

// Initialize assessments manager
const assessments = new AssessmentsManager();

// Export for global use
window.assessments = assessments;

