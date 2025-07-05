// ISO 42001 Admin Dashboard JavaScript

class AdminDashboard {
    constructor() {
        this.currentSection = 'overview';
        this.data = {
            users: [],
            assessments: [],
            certificates: [],
            stats: {}
        };
        this.charts = {};
        this.filters = {
            users: { search: '', status: '', industry: '' },
            assessments: { search: '', status: '', risk: '' },
            certificates: { search: '', date: '' }
        };
        this.pagination = {
            users: { page: 1, limit: 10, total: 0 },
            assessments: { page: 1, limit: 10, total: 0 },
            certificates: { page: 1, limit: 10, total: 0 }
        };
    }

    init() {
        this.bindEvents();
        this.loadInitialData();
        this.initializeCharts();
    }

    bindEvents() {
        // Navigation
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const section = link.dataset.section;
                this.showSection(section);
            });
        });

        // Refresh data
        document.getElementById('refresh-data-btn')?.addEventListener('click', () => {
            this.refreshAllData();
        });

        // Logout
        document.getElementById('admin-logout-btn')?.addEventListener('click', () => {
            this.logout();
        });

        // Search and filters
        this.bindFilterEvents();

        // Export buttons
        this.bindExportEvents();
    }

    bindFilterEvents() {
        // Users filters
        const usersSearch = document.getElementById('users-search');
        const usersStatusFilter = document.getElementById('users-status-filter');
        const usersIndustryFilter = document.getElementById('users-industry-filter');

        if (usersSearch) {
            usersSearch.addEventListener('input', this.debounce(() => {
                this.filters.users.search = usersSearch.value;
                this.loadUsers();
            }, 300));
        }

        if (usersStatusFilter) {
            usersStatusFilter.addEventListener('change', () => {
                this.filters.users.status = usersStatusFilter.value;
                this.loadUsers();
            });
        }

        if (usersIndustryFilter) {
            usersIndustryFilter.addEventListener('change', () => {
                this.filters.users.industry = usersIndustryFilter.value;
                this.loadUsers();
            });
        }

        // Assessments filters
        const assessmentsSearch = document.getElementById('assessments-search');
        const assessmentsStatusFilter = document.getElementById('assessments-status-filter');
        const assessmentsRiskFilter = document.getElementById('assessments-risk-filter');

        if (assessmentsSearch) {
            assessmentsSearch.addEventListener('input', this.debounce(() => {
                this.filters.assessments.search = assessmentsSearch.value;
                this.loadAssessments();
            }, 300));
        }

        if (assessmentsStatusFilter) {
            assessmentsStatusFilter.addEventListener('change', () => {
                this.filters.assessments.status = assessmentsStatusFilter.value;
                this.loadAssessments();
            });
        }

        if (assessmentsRiskFilter) {
            assessmentsRiskFilter.addEventListener('change', () => {
                this.filters.assessments.risk = assessmentsRiskFilter.value;
                this.loadAssessments();
            });
        }

        // Certificates filters
        const certificatesSearch = document.getElementById('certificates-search');
        const certificatesDateFilter = document.getElementById('certificates-date-filter');

        if (certificatesSearch) {
            certificatesSearch.addEventListener('input', this.debounce(() => {
                this.filters.certificates.search = certificatesSearch.value;
                this.loadCertificates();
            }, 300));
        }

        if (certificatesDateFilter) {
            certificatesDateFilter.addEventListener('change', () => {
                this.filters.certificates.date = certificatesDateFilter.value;
                this.loadCertificates();
            });
        }
    }

    bindExportEvents() {
        document.getElementById('export-users-btn')?.addEventListener('click', () => {
            this.exportData('users');
        });

        document.getElementById('export-assessments-btn')?.addEventListener('click', () => {
            this.exportData('assessments');
        });

        document.getElementById('export-certificates-btn')?.addEventListener('click', () => {
            this.exportData('certificates');
        });
    }

    showSection(section) {
        // Update navigation
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
        });
        document.querySelector(`[data-section="${section}"]`)?.classList.add('active');

        // Update sections
        document.querySelectorAll('.admin-section').forEach(sec => {
            sec.classList.remove('active');
        });
        document.getElementById(`${section}-section`)?.classList.add('active');

        this.currentSection = section;

        // Load section-specific data
        switch (section) {
            case 'overview':
                this.loadOverviewData();
                break;
            case 'users':
                this.loadUsers();
                break;
            case 'assessments':
                this.loadAssessments();
                break;
            case 'certificates':
                this.loadCertificates();
                break;
            case 'analytics':
                this.loadAnalytics();
                break;
        }
    }

    async loadInitialData() {
        try {
            await this.loadOverviewData();
        } catch (error) {
            console.error('Error loading initial data:', error);
            this.showError('Failed to load dashboard data');
        }
    }

    async loadOverviewData() {
        try {
            // Load overview statistics
            const statsResponse = await this.apiCall('/api/admin/stats');
            this.data.stats = statsResponse;

            this.updateKPICards();
            this.updateOverviewCharts();
            this.loadRecentActivity();

        } catch (error) {
            console.error('Error loading overview data:', error);
            this.showError('Failed to load overview data');
        }
    }

    async loadUsers() {
        try {
            const params = new URLSearchParams({
                page: this.pagination.users.page,
                limit: this.pagination.users.limit,
                ...this.filters.users
            });

            const response = await this.apiCall(`/api/admin/users?${params}`);
            this.data.users = response.users || [];
            this.pagination.users.total = response.total || 0;

            this.renderUsersTable();
            this.renderPagination('users');

        } catch (error) {
            console.error('Error loading users:', error);
            this.showError('Failed to load users data');
        }
    }

    async loadAssessments() {
        try {
            const params = new URLSearchParams({
                page: this.pagination.assessments.page,
                limit: this.pagination.assessments.limit,
                ...this.filters.assessments
            });

            const response = await this.apiCall(`/api/admin/assessments?${params}`);
            this.data.assessments = response.assessments || [];
            this.pagination.assessments.total = response.total || 0;

            this.renderAssessmentsTable();
            this.renderPagination('assessments');

        } catch (error) {
            console.error('Error loading assessments:', error);
            this.showError('Failed to load assessments data');
        }
    }

    async loadCertificates() {
        try {
            const params = new URLSearchParams({
                page: this.pagination.certificates.page,
                limit: this.pagination.certificates.limit,
                ...this.filters.certificates
            });

            const response = await this.apiCall(`/api/admin/certificates?${params}`);
            this.data.certificates = response.certificates || [];
            this.pagination.certificates.total = response.total || 0;

            this.renderCertificatesTable();
            this.renderPagination('certificates');

        } catch (error) {
            console.error('Error loading certificates:', error);
            this.showError('Failed to load certificates data');
        }
    }

    async loadAnalytics() {
        try {
            const analyticsResponse = await this.apiCall('/api/admin/analytics');
            this.updateAnalyticsCharts(analyticsResponse);
            this.updateInsights(analyticsResponse);

        } catch (error) {
            console.error('Error loading analytics:', error);
            this.showError('Failed to load analytics data');
        }
    }

    async loadRecentActivity() {
        try {
            const response = await this.apiCall('/api/admin/activity?limit=5');
            this.renderRecentActivity(response.activities || []);

        } catch (error) {
            console.error('Error loading recent activity:', error);
        }
    }

    updateKPICards() {
        const stats = this.data.stats;

        this.updateKPICard('total-users', stats.totalUsers || 0);
        this.updateKPICard('total-assessments', stats.totalAssessments || 0);
        this.updateKPICard('total-certificates', stats.totalCertificates || 0);
        this.updateKPICard('avg-compliance-score', stats.avgComplianceScore ? `${stats.avgComplianceScore.toFixed(1)}%` : '--');
    }

    updateKPICard(id, value) {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value;
            element.classList.add('animate-fade-in');
        }
    }

    renderUsersTable() {
        const tbody = document.getElementById('users-table-body');
        if (!tbody) return;

        if (this.data.users.length === 0) {
            tbody.innerHTML = this.renderEmptyState('No users found');
            return;
        }

        tbody.innerHTML = this.data.users.map(user => `
            <tr>
                <td>
                    <div class="user-info">
                        <div class="user-avatar">
                            ${this.getInitials(user.firstName, user.lastName)}
                        </div>
                        <div class="user-details">
                            <div class="user-name">${user.firstName} ${user.lastName}</div>
                            <div class="user-email">${user.email}</div>
                        </div>
                    </div>
                </td>
                <td>${user.organization || 'N/A'}</td>
                <td>${user.industry || 'N/A'}</td>
                <td>${user.assessmentCount || 0}</td>
                <td>${user.certificateCount || 0}</td>
                <td>${this.formatDate(user.lastLoginAt) || 'Never'}</td>
                <td>
                    <span class="status-badge ${user.isActive ? 'active' : 'inactive'}">
                        ${user.isActive ? 'Active' : 'Inactive'}
                    </span>
                </td>
                <td>
                    <div class="table-actions">
                        <button class="action-btn primary" onclick="adminDashboard.viewUser('${user.id}')" title="View Details">
                            <i data-lucide="eye"></i>
                        </button>
                        <button class="action-btn warning" onclick="adminDashboard.editUser('${user.id}')" title="Edit User">
                            <i data-lucide="edit"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `).join('');

        // Reinitialize Lucide icons
        if (window.lucide) {
            lucide.createIcons();
        }
    }

    renderAssessmentsTable() {
        const tbody = document.getElementById('assessments-table-body');
        if (!tbody) return;

        if (this.data.assessments.length === 0) {
            tbody.innerHTML = this.renderEmptyState('No assessments found');
            return;
        }

        tbody.innerHTML = this.data.assessments.map(assessment => `
            <tr>
                <td>
                    <div class="assessment-info">
                        <div class="assessment-name">${assessment.name}</div>
                    </div>
                </td>
                <td>${assessment.organizationName}</td>
                <td>${assessment.aiSystemName}</td>
                <td>
                    <span class="risk-badge ${assessment.riskLevel}">
                        ${this.formatRiskLevel(assessment.riskLevel)}
                    </span>
                </td>
                <td>
                    <div class="progress-cell">
                        <div class="progress-bar-small">
                            <div class="progress-fill-small" style="width: ${assessment.progress?.overall || 0}%"></div>
                        </div>
                        <span class="progress-text">${Math.round(assessment.progress?.overall || 0)}%</span>
                    </div>
                </td>
                <td>
                    <div class="score-cell">
                        <span class="score-value">${assessment.finalScore ? `${assessment.finalScore.toFixed(1)}%` : '--'}</span>
                        ${assessment.finalScore ? `<div class="score-indicator ${this.getScoreClass(assessment.finalScore)}"></div>` : ''}
                    </div>
                </td>
                <td>
                    <span class="status-badge ${assessment.status}">
                        ${this.formatStatus(assessment.status)}
                    </span>
                </td>
                <td>${this.formatDate(assessment.createdAt)}</td>
                <td>
                    <div class="table-actions">
                        <button class="action-btn primary" onclick="adminDashboard.viewAssessment('${assessment.id}')" title="View Details">
                            <i data-lucide="eye"></i>
                        </button>
                        ${assessment.certificateGenerated ? `
                            <button class="action-btn success" onclick="adminDashboard.viewCertificate('${assessment.id}')" title="View Certificate">
                                <i data-lucide="award"></i>
                            </button>
                        ` : ''}
                    </div>
                </td>
            </tr>
        `).join('');

        // Reinitialize Lucide icons
        if (window.lucide) {
            lucide.createIcons();
        }
    }

    renderCertificatesTable() {
        const tbody = document.getElementById('certificates-table-body');
        if (!tbody) return;

        if (this.data.certificates.length === 0) {
            tbody.innerHTML = this.renderEmptyState('No certificates found');
            return;
        }

        tbody.innerHTML = this.data.certificates.map(cert => `
            <tr>
                <td>
                    <code class="certificate-id">${cert.certificateId}</code>
                </td>
                <td>${cert.organizationName}</td>
                <td>${cert.aiSystemName}</td>
                <td>
                    <div class="score-cell">
                        <span class="score-value">${cert.complianceScore.toFixed(1)}%</span>
                        <div class="score-indicator ${this.getScoreClass(cert.complianceScore)}"></div>
                    </div>
                </td>
                <td>${this.formatDate(cert.issuedDate)}</td>
                <td>${this.formatDate(cert.validUntil)}</td>
                <td>
                    <span class="status-badge active">Valid</span>
                </td>
                <td>
                    <div class="table-actions">
                        <button class="action-btn primary" onclick="adminDashboard.verifyCertificate('${cert.certificateId}')" title="Verify">
                            <i data-lucide="shield-check"></i>
                        </button>
                        <button class="action-btn success" onclick="adminDashboard.downloadCertificate('${cert.assessmentId}')" title="Download">
                            <i data-lucide="download"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `).join('');

        // Reinitialize Lucide icons
        if (window.lucide) {
            lucide.createIcons();
        }
    }

    renderPagination(type) {
        const container = document.getElementById(`${type}-pagination`);
        if (!container) return;

        const pagination = this.pagination[type];
        const totalPages = Math.ceil(pagination.total / pagination.limit);

        if (totalPages <= 1) {
            container.innerHTML = '';
            return;
        }

        let paginationHTML = '';

        // Previous button
        paginationHTML += `
            <button class="pagination-btn" ${pagination.page === 1 ? 'disabled' : ''} 
                    onclick="adminDashboard.changePage('${type}', ${pagination.page - 1})">
                <i data-lucide="chevron-left"></i>
            </button>
        `;

        // Page numbers
        const startPage = Math.max(1, pagination.page - 2);
        const endPage = Math.min(totalPages, pagination.page + 2);

        for (let i = startPage; i <= endPage; i++) {
            paginationHTML += `
                <button class="pagination-btn ${i === pagination.page ? 'active' : ''}" 
                        onclick="adminDashboard.changePage('${type}', ${i})">
                    ${i}
                </button>
            `;
        }

        // Next button
        paginationHTML += `
            <button class="pagination-btn" ${pagination.page === totalPages ? 'disabled' : ''} 
                    onclick="adminDashboard.changePage('${type}', ${pagination.page + 1})">
                <i data-lucide="chevron-right"></i>
            </button>
        `;

        container.innerHTML = paginationHTML;

        // Reinitialize Lucide icons
        if (window.lucide) {
            lucide.createIcons();
        }
    }

    renderEmptyState(message) {
        return `
            <tr>
                <td colspan="100%" class="empty-state">
                    <div class="empty-state-icon">📭</div>
                    <h3>No Data Found</h3>
                    <p>${message}</p>
                </td>
            </tr>
        `;
    }

    renderRecentActivity(activities) {
        const container = document.getElementById('recent-activity-list');
        if (!container) return;

        if (activities.length === 0) {
            container.innerHTML = '<div class="empty-state">No recent activity</div>';
            return;
        }

        container.innerHTML = activities.map(activity => `
            <div class="activity-item">
                <div class="activity-icon ${activity.type}">
                    <i data-lucide="${this.getActivityIcon(activity.type)}"></i>
                </div>
                <div class="activity-content">
                    <div class="activity-text">${activity.description}</div>
                    <div class="activity-time">${this.formatTimeAgo(activity.timestamp)}</div>
                </div>
            </div>
        `).join('');

        // Reinitialize Lucide icons
        if (window.lucide) {
            lucide.createIcons();
        }
    }

    // Chart initialization and updates
    initializeCharts() {
        // Initialize Chart.js charts
        this.initUserTrendChart();
        this.initAssessmentStatusChart();
    }

    initUserTrendChart() {
        const ctx = document.getElementById('user-trend-chart');
        if (!ctx) return;

        this.charts.userTrend = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'New Users',
                    data: [],
                    borderColor: '#2563eb',
                    backgroundColor: 'rgba(37, 99, 235, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1
                        }
                    }
                }
            }
        });
    }

    initAssessmentStatusChart() {
        const ctx = document.getElementById('assessment-status-chart');
        if (!ctx) return;

        this.charts.assessmentStatus = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Completed', 'In Progress', 'Not Started', 'On Hold'],
                datasets: [{
                    data: [0, 0, 0, 0],
                    backgroundColor: [
                        '#10b981',
                        '#f59e0b',
                        '#6b7280',
                        '#ef4444'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }

    updateOverviewCharts() {
        // Update charts with real data
        if (this.charts.userTrend && this.data.stats.userTrend) {
            this.charts.userTrend.data.labels = this.data.stats.userTrend.labels;
            this.charts.userTrend.data.datasets[0].data = this.data.stats.userTrend.data;
            this.charts.userTrend.update();
        }

        if (this.charts.assessmentStatus && this.data.stats.assessmentStatus) {
            this.charts.assessmentStatus.data.datasets[0].data = this.data.stats.assessmentStatus;
            this.charts.assessmentStatus.update();
        }
    }

    // Action handlers
    async viewUser(userId) {
        try {
            const user = await this.apiCall(`/api/admin/users/${userId}`);
            this.showUserModal(user);
        } catch (error) {
            this.showError('Failed to load user details');
        }
    }

    async viewAssessment(assessmentId) {
        try {
            const assessment = await this.apiCall(`/api/admin/assessments/${assessmentId}`);
            this.showAssessmentModal(assessment);
        } catch (error) {
            this.showError('Failed to load assessment details');
        }
    }

    async verifyCertificate(certificateId) {
        try {
            const verification = await this.apiCall(`/api/certificates/verify/${certificateId}`);
            this.showCertificateVerificationModal(verification);
        } catch (error) {
            this.showError('Failed to verify certificate');
        }
    }

    changePage(type, page) {
        this.pagination[type].page = page;
        
        switch (type) {
            case 'users':
                this.loadUsers();
                break;
            case 'assessments':
                this.loadAssessments();
                break;
            case 'certificates':
                this.loadCertificates();
                break;
        }
    }

    async exportData(type) {
        try {
            const response = await this.apiCall(`/api/admin/export/${type}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(this.filters[type])
            });

            // Create download link
            const blob = new Blob([response], { type: 'text/csv' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${type}_export_${new Date().toISOString().split('T')[0]}.csv`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);

            this.showSuccess(`${type.charAt(0).toUpperCase() + type.slice(1)} data exported successfully`);

        } catch (error) {
            this.showError(`Failed to export ${type} data`);
        }
    }

    async refreshAllData() {
        try {
            this.showLoading('Refreshing data...');
            await this.loadInitialData();
            
            // Refresh current section
            switch (this.currentSection) {
                case 'users':
                    await this.loadUsers();
                    break;
                case 'assessments':
                    await this.loadAssessments();
                    break;
                case 'certificates':
                    await this.loadCertificates();
                    break;
                case 'analytics':
                    await this.loadAnalytics();
                    break;
            }

            this.hideLoading();
            this.showSuccess('Data refreshed successfully');

        } catch (error) {
            this.hideLoading();
            this.showError('Failed to refresh data');
        }
    }

    logout() {
        // Clear admin session and redirect
        localStorage.removeItem('adminToken');
        window.location.href = '/admin/login';
    }

    // Utility methods
    async apiCall(url, options = {}) {
        const token = localStorage.getItem('adminToken');
        
        const defaultOptions = {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        };

        const response = await fetch(url, { ...defaultOptions, ...options });
        
        if (!response.ok) {
            throw new Error(`API call failed: ${response.statusText}`);
        }

        return response.json();
    }

    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    getInitials(firstName, lastName) {
        return `${firstName?.charAt(0) || ''}${lastName?.charAt(0) || ''}`.toUpperCase();
    }

    formatDate(dateString) {
        if (!dateString) return 'N/A';
        return new Date(dateString).toLocaleDateString();
    }

    formatTimeAgo(dateString) {
        if (!dateString) return 'Unknown';
        
        const now = new Date();
        const date = new Date(dateString);
        const diffInSeconds = Math.floor((now - date) / 1000);

        if (diffInSeconds < 60) return 'Just now';
        if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`;
        if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`;
        return `${Math.floor(diffInSeconds / 86400)}d ago`;
    }

    formatStatus(status) {
        const statusMap = {
            'not_started': 'Not Started',
            'in_progress': 'In Progress',
            'completed': 'Completed',
            'on_hold': 'On Hold'
        };
        return statusMap[status] || status;
    }

    formatRiskLevel(riskLevel) {
        const riskMap = {
            'low': 'Low',
            'medium': 'Medium',
            'high': 'High',
            'critical': 'Critical'
        };
        return riskMap[riskLevel] || riskLevel;
    }

    getScoreClass(score) {
        if (score >= 80) return 'excellent';
        if (score >= 70) return 'good';
        return 'poor';
    }

    getActivityIcon(type) {
        const iconMap = {
            'user': 'user-plus',
            'assessment': 'clipboard-list',
            'certificate': 'award'
        };
        return iconMap[type] || 'activity';
    }

    showSuccess(message) {
        // Implement toast notification
        console.log('Success:', message);
    }

    showError(message) {
        // Implement toast notification
        console.error('Error:', message);
    }

    showLoading(message) {
        // Implement loading indicator
        console.log('Loading:', message);
    }

    hideLoading() {
        // Hide loading indicator
        console.log('Loading complete');
    }

    showUserModal(user) {
        // Implement user details modal
        console.log('Show user modal:', user);
    }

    showAssessmentModal(assessment) {
        // Implement assessment details modal
        console.log('Show assessment modal:', assessment);
    }

    showCertificateVerificationModal(verification) {
        // Implement certificate verification modal
        console.log('Show certificate verification modal:', verification);
    }
}

// Initialize admin dashboard
const adminDashboard = new AdminDashboard();

// Export for global use
window.adminDashboard = adminDashboard;

