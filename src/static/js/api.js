// Qryti - ISO 42001 Compliance Platform - API Client

class APIClient {
    constructor() {
        // Use the deployed API Gateway URL
        this.baseURL = 'https://jipehrp7qa.execute-api.ap-south-1.amazonaws.com/production';
        this.token = utils.storage.get('accessToken');
        this.refreshToken = utils.storage.get('refreshToken');
    }

    // Set authentication token
    setToken(token) {
        this.token = token;
        utils.storage.set('accessToken', token);
    }

    // Set refresh token
    setRefreshToken(token) {
        this.refreshToken = token;
        utils.storage.set('refreshToken', token);
    }

    // Clear authentication
    clearAuth() {
        this.token = null;
        this.refreshToken = null;
        utils.storage.remove('accessToken');
        utils.storage.remove('refreshToken');
        utils.storage.remove('user');
    }

    // Get authentication headers
    getAuthHeaders() {
        const headers = {
            'Content-Type': 'application/json'
        };

        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }

        return headers;
    }

    // Make HTTP request
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            headers: this.getAuthHeaders(),
            ...options
        };

        try {
            const response = await fetch(url, config);
            
            // Handle token expiration
            if (response.status === 401 && this.refreshToken) {
                const refreshed = await this.refreshAccessToken();
                if (refreshed) {
                    // Retry the original request with new token
                    config.headers = this.getAuthHeaders();
                    const retryResponse = await fetch(url, config);
                    return await this.handleResponse(retryResponse);
                } else {
                    // Refresh failed, redirect to login
                    this.clearAuth();
                    window.location.hash = '#auth';
                    throw new Error('Session expired. Please log in again.');
                }
            }

            return await this.handleResponse(response);
        } catch (error) {
            if (error.name === 'TypeError' && error.message.includes('fetch')) {
                throw new Error('Network error. Please check your connection.');
            }
            throw error;
        }
    }

    // Handle response
    async handleResponse(response) {
        const contentType = response.headers.get('content-type');
        
        if (contentType && contentType.includes('application/json')) {
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.message || `HTTP ${response.status}: ${response.statusText}`);
            }
            
            return data;
        } else {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            return response;
        }
    }

    // Refresh access token
    async refreshAccessToken() {
        if (!this.refreshToken) {
            return false;
        }

        try {
            const response = await fetch(`${this.baseURL}/api/auth/refresh`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.refreshToken}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.setToken(data.accessToken);
                return true;
            } else {
                return false;
            }
        } catch (error) {
            console.error('Token refresh failed:', error);
            return false;
        }
    }

    // GET request
    async get(endpoint) {
        return this.request(endpoint, { method: 'GET' });
    }

    // POST request
    async post(endpoint, data) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    // PUT request
    async put(endpoint, data) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    // DELETE request
    async delete(endpoint) {
        return this.request(endpoint, { method: 'DELETE' });
    }

    // Upload file
    async upload(endpoint, formData) {
        const headers = {};
        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }

        return this.request(endpoint, {
            method: 'POST',
            headers,
            body: formData
        });
    }

    // Authentication API
    auth = {
        // Register new user
        register: async (userData) => {
            return this.post('/api/auth/register', userData);
        },

        // Verify email with OTP
        verifyEmail: async (email, otpCode) => {
            return this.post('/api/auth/verify-email', { email, otpCode });
        },

        // Login user
        login: async (email, password) => {
            return this.post('/api/auth/login', { email, password });
        },

        // Resend OTP
        resendOTP: async (email) => {
            return this.post('/api/auth/resend-otp', { email });
        },

        // Get user profile
        getProfile: async () => {
            return this.get('/api/auth/profile');
        },

        // Update user profile
        updateProfile: async (profileData) => {
            return this.put('/api/auth/profile', profileData);
        },

        // Logout (client-side)
        logout: () => {
            this.clearAuth();
            window.location.hash = '#landing';
        }
    };

    // Assessment API
    assessments = {
        // Get all assessments
        getAll: async (params = {}) => {
            const queryString = new URLSearchParams(params).toString();
            const endpoint = queryString ? `/api/assessments?${queryString}` : '/api/assessments';
            return this.get(endpoint);
        },

        // Get single assessment
        get: async (id, includeResponses = false) => {
            const params = includeResponses ? '?include_responses=true' : '';
            return this.get(`/api/assessments/${id}${params}`);
        },

        // Create new assessment
        create: async (assessmentData) => {
            return this.post('/api/assessments', assessmentData);
        },

        // Update assessment
        update: async (id, assessmentData) => {
            return this.put(`/api/assessments/${id}`, assessmentData);
        },

        // Submit response
        submitResponse: async (id, responseData) => {
            return this.put(`/api/assessments/${id}/responses`, responseData);
        },

        // Get responses
        getResponses: async (id, params = {}) => {
            const queryString = new URLSearchParams(params).toString();
            const endpoint = queryString ? `/api/assessments/${id}/responses?${queryString}` : `/api/assessments/${id}/responses`;
            return this.get(endpoint);
        },

        // Calculate scores
        calculateScore: async (id) => {
            return this.post(`/api/assessments/${id}/calculate-score`);
        },

        // Advance stage
        advanceStage: async (id) => {
            return this.post(`/api/assessments/${id}/advance-stage`);
        },

        // Generate report
        generateReport: async (id, format = 'json', type = 'executive') => {
            return this.get(`/api/assessments/${id}/report?format=${format}&type=${type}`);
        },

        // Get controls
        getControls: async (stage = null) => {
            const params = stage ? `?stage=${stage}` : '';
            return this.get(`/api/assessments/controls${params}`);
        }
    };

    // File API
    files = {
        // Upload file
        upload: async (assessmentId, file, metadata = {}) => {
            const formData = new FormData();
            formData.append('file', file);
            formData.append('assessmentId', assessmentId);
            
            Object.keys(metadata).forEach(key => {
                formData.append(key, metadata[key]);
            });

            return this.upload('/api/files/upload', formData);
        },

        // Get file info
        get: async (fileId) => {
            return this.get(`/api/files/${fileId}`);
        },

        // Download file
        download: async (fileId) => {
            const response = await this.request(`/api/files/${fileId}/download`, {
                method: 'GET'
            });
            return response; // This will be the actual file response
        },

        // Delete file
        delete: async (fileId) => {
            return this.delete(`/api/files/${fileId}`);
        },

        // Get assessment files
        getAssessmentFiles: async (assessmentId, params = {}) => {
            const queryString = new URLSearchParams(params).toString();
            const endpoint = queryString ? `/api/files/assessment/${assessmentId}?${queryString}` : `/api/files/assessment/${assessmentId}`;
            return this.get(endpoint);
        },

        // Update file metadata
        updateMetadata: async (fileId, metadata) => {
            return this.put(`/api/files/${fileId}/metadata`, metadata);
        }
    };

    // Admin API
    admin = {
        // Get dashboard stats
        getDashboardStats: async () => {
            return this.get('/api/admin/dashboard');
        },

        // Get all users
        getUsers: async (params = {}) => {
            const queryString = new URLSearchParams(params).toString();
            const endpoint = queryString ? `/api/admin/users?${queryString}` : '/api/admin/users';
            return this.get(endpoint);
        },

        // Get user details
        getUserDetails: async (userId) => {
            return this.get(`/api/admin/users/${userId}`);
        },

        // Toggle user status
        toggleUserStatus: async (userId) => {
            return this.post(`/api/admin/users/${userId}/toggle-status`);
        },

        // Get all assessments
        getAllAssessments: async (params = {}) => {
            const queryString = new URLSearchParams(params).toString();
            const endpoint = queryString ? `/api/admin/assessments?${queryString}` : '/api/admin/assessments';
            return this.get(endpoint);
        },

        // Get compliance trends
        getComplianceTrends: async (days = 30) => {
            return this.get(`/api/admin/analytics/compliance-trends?days=${days}`);
        },

        // Get system health
        getSystemHealth: async () => {
            return this.get('/api/admin/system/health');
        }
    };

    // Health check
    health = {
        check: async () => {
            return this.get('/api/health');
        }
    };
}

// Create global API instance
const api = new APIClient();

// Auto-refresh token on page load if needed
document.addEventListener('DOMContentLoaded', async () => {
    if (api.token && api.refreshToken) {
        try {
            // Test if current token is valid
            await api.auth.getProfile();
        } catch (error) {
            // Token might be expired, try to refresh
            const refreshed = await api.refreshAccessToken();
            if (!refreshed) {
                // Refresh failed, clear auth
                api.clearAuth();
            }
        }
    }
});

// Export API client
window.api = api;

