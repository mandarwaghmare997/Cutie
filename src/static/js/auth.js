// Qryti - ISO 42001 Compliance Platform - Authentication Module

class AuthManager {
    constructor() {
        this.currentUser = null;
        this.isAuthenticated = false;
        this.init();
    }

    init() {
        // Check if user is already authenticated
        const token = utils.storage.get('accessToken');
        const user = utils.storage.get('user');
        
        if (token && user) {
            this.currentUser = user;
            this.isAuthenticated = true;
            api.setToken(token);
        }

        this.bindEvents();
        this.setupAuthForms();
    }

    bindEvents() {
        // Get started button
        const getStartedBtn = utils.$('#get-started-btn');
        if (getStartedBtn) {
            getStartedBtn.addEventListener('click', () => {
                if (this.isAuthenticated) {
                    this.showDashboard();
                } else {
                    this.showAuthPage();
                }
            });
        }

        // Auth switch button
        const authSwitchBtn = utils.$('#auth-switch-btn');
        if (authSwitchBtn) {
            authSwitchBtn.addEventListener('click', () => {
                this.toggleAuthMode();
            });
        }

        // Logout button
        const logoutBtn = utils.$('#logout-btn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', () => {
                this.logout();
            });
        }

        // Resend OTP button
        const resendOtpBtn = utils.$('#resend-otp-btn');
        if (resendOtpBtn) {
            resendOtpBtn.addEventListener('click', () => {
                this.resendOTP();
            });
        }
    }

    setupAuthForms() {
        // Login form
        const loginForm = utils.$('#login-form');
        if (loginForm) {
            loginForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleLogin(loginForm);
            });
        }

        // Registration form
        const registerForm = utils.$('#register-form');
        if (registerForm) {
            registerForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleRegistration(registerForm);
            });
        }

        // OTP form
        const otpForm = utils.$('#otp-form');
        if (otpForm) {
            otpForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleOTPVerification(otpForm);
            });
        }

        // Auto-format OTP input
        const otpInput = utils.$('#otp-code');
        if (otpInput) {
            otpInput.addEventListener('input', (e) => {
                // Only allow numbers
                e.target.value = e.target.value.replace(/[^0-9]/g, '');
                
                // Auto-submit when 6 digits entered
                if (e.target.value.length === 6) {
                    setTimeout(() => {
                        const submitBtn = otpForm.querySelector('button[type="submit"]');
                        if (submitBtn) submitBtn.click();
                    }, 500);
                }
            });
        }
    }

    async handleLogin(form) {
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

            const response = await api.auth.login(formData.email, formData.password);
            
            if (response.requiresVerification) {
                // Show OTP form
                this.showOTPForm(formData.email);
                utils.toast.info('Please check your email for the verification code.');
            } else {
                // Login successful
                await this.handleLoginSuccess(response);
            }

        } catch (error) {
            utils.errorHandler.handle(error, 'Login');
        } finally {
            utils.form.setLoading(submitBtn, false);
        }
    }

    async handleRegistration(form) {
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

            // Additional validation
            if (formData.password.length < 8) {
                utils.form.showError(form.querySelector('#register-password'), 'Password must be at least 8 characters long');
                return;
            }

            const userData = {
                firstName: formData['first-name'],
                lastName: formData['last-name'],
                email: formData.email,
                password: formData.password,
                organization: formData.organization,
                industry: formData.industry,
                role: formData.role,
                country: formData.country
            };

            const response = await api.auth.register(userData);
            
            // Show OTP form for email verification
            this.showOTPForm(formData.email);
            utils.toast.success('Registration successful! Please check your email for the verification code.');

        } catch (error) {
            utils.errorHandler.handle(error, 'Registration');
        } finally {
            utils.form.setLoading(submitBtn, false);
        }
    }

    async handleOTPVerification(form) {
        const submitBtn = form.querySelector('button[type="submit"]');
        utils.form.setLoading(submitBtn, true);
        utils.form.clearAllErrors(form);

        try {
            const formData = utils.form.serialize(form);
            const email = this.pendingVerificationEmail;

            if (!email) {
                throw new Error('No email found for verification');
            }

            if (!formData['otp-code'] || formData['otp-code'].length !== 6) {
                utils.form.showError(form.querySelector('#otp-code'), 'Please enter a valid 6-digit code');
                return;
            }

            const response = await api.auth.verifyEmail(email, formData['otp-code']);
            
            // Verification successful
            await this.handleLoginSuccess(response);
            utils.toast.success('Email verified successfully!');

        } catch (error) {
            utils.errorHandler.handle(error, 'Email Verification');
        } finally {
            utils.form.setLoading(submitBtn, false);
        }
    }

    async handleLoginSuccess(response) {
        // Store tokens and user data
        api.setToken(response.accessToken);
        if (response.refreshToken) {
            api.setRefreshToken(response.refreshToken);
        }
        
        this.currentUser = response.user;
        this.isAuthenticated = true;
        utils.storage.set('user', response.user);

        // Update UI
        this.updateAuthUI();
        
        // Navigate to dashboard
        this.showDashboard();
    }

    async resendOTP() {
        const resendBtn = utils.$('#resend-otp-btn');
        if (!this.pendingVerificationEmail) {
            utils.toast.error('No email found for verification');
            return;
        }

        utils.form.setLoading(resendBtn, true);

        try {
            await api.auth.resendOTP(this.pendingVerificationEmail);
            utils.toast.success('Verification code sent to your email');
            
            // Disable resend button for 60 seconds
            this.startResendCooldown();

        } catch (error) {
            utils.errorHandler.handle(error, 'Resend OTP');
        } finally {
            utils.form.setLoading(resendBtn, false);
        }
    }

    startResendCooldown() {
        const resendBtn = utils.$('#resend-otp-btn');
        if (!resendBtn) return;

        let countdown = 60;
        resendBtn.disabled = true;
        resendBtn.textContent = `Resend in ${countdown}s`;

        const timer = setInterval(() => {
            countdown--;
            resendBtn.textContent = `Resend in ${countdown}s`;

            if (countdown <= 0) {
                clearInterval(timer);
                resendBtn.disabled = false;
                resendBtn.innerHTML = '<i data-lucide="refresh-cw"></i> Resend Code';
                if (window.lucide) lucide.createIcons();
            }
        }, 1000);
    }

    toggleAuthMode() {
        const loginForm = utils.$('#login-form');
        const registerForm = utils.$('#register-form');
        const authTitle = utils.$('#auth-title');
        const authSubtitle = utils.$('#auth-subtitle');
        const authSwitchText = utils.$('#auth-switch-text');
        const authSwitchBtn = utils.$('#auth-switch-btn');

        if (loginForm.classList.contains('hidden')) {
            // Switch to login
            loginForm.classList.remove('hidden');
            registerForm.classList.add('hidden');
            authTitle.textContent = 'Welcome Back';
            authSubtitle.textContent = 'Sign in to continue your compliance journey';
            authSwitchText.textContent = "Don't have an account?";
            authSwitchBtn.textContent = 'Sign up here';
        } else {
            // Switch to register
            loginForm.classList.add('hidden');
            registerForm.classList.remove('hidden');
            authTitle.textContent = 'Create Account';
            authSubtitle.textContent = 'Start your ISO 42001 compliance journey';
            authSwitchText.textContent = 'Already have an account?';
            authSwitchBtn.textContent = 'Sign in here';
        }

        // Clear any existing errors
        utils.form.clearAllErrors(loginForm);
        utils.form.clearAllErrors(registerForm);
    }

    showOTPForm(email) {
        this.pendingVerificationEmail = email;
        
        const loginForm = utils.$('#login-form');
        const registerForm = utils.$('#register-form');
        const otpForm = utils.$('#otp-form');
        const authTitle = utils.$('#auth-title');
        const authSubtitle = utils.$('#auth-subtitle');
        const authSwitchText = utils.$('#auth-switch-text');
        const authSwitchBtn = utils.$('#auth-switch-btn');

        // Hide other forms
        loginForm.classList.add('hidden');
        registerForm.classList.add('hidden');
        otpForm.classList.remove('hidden');

        // Update text
        authTitle.textContent = 'Verify Your Email';
        authSubtitle.textContent = `We've sent a verification code to ${email}`;
        authSwitchText.textContent = 'Wrong email?';
        authSwitchBtn.textContent = 'Go back';

        // Update switch button behavior
        authSwitchBtn.onclick = () => {
            this.hideOTPForm();
        };

        // Focus OTP input
        const otpInput = utils.$('#otp-code');
        if (otpInput) {
            setTimeout(() => otpInput.focus(), 100);
        }
    }

    hideOTPForm() {
        const loginForm = utils.$('#login-form');
        const registerForm = utils.$('#register-form');
        const otpForm = utils.$('#otp-form');

        otpForm.classList.add('hidden');
        loginForm.classList.remove('hidden');

        // Reset auth form
        this.toggleAuthMode();
        this.pendingVerificationEmail = null;

        // Clear OTP form
        const otpInput = utils.$('#otp-code');
        if (otpInput) otpInput.value = '';
    }

    showAuthPage() {
        this.showPage('auth-page');
    }

    showDashboard() {
        this.showPage('dashboard-page');
        this.updateAuthUI();
        
        // Load dashboard data
        if (window.dashboard) {
            dashboard.loadDashboardData();
        }
    }

    showPage(pageId) {
        // Hide all pages
        const pages = utils.$$('.page');
        pages.forEach(page => page.classList.remove('active'));

        // Show target page
        const targetPage = utils.$(`#${pageId}`);
        if (targetPage) {
            targetPage.classList.add('active');
        }

        // Update navigation
        this.updateNavigation(pageId);
    }

    updateNavigation(activePageId) {
        const navbar = utils.$('#navbar');
        const mainContent = utils.$('#main-content');

        if (activePageId === 'landing-page' || activePageId === 'auth-page') {
            // Hide navbar for landing and auth pages
            navbar.classList.add('hidden');
            mainContent.classList.remove('with-nav');
        } else {
            // Show navbar for app pages
            navbar.classList.remove('hidden');
            mainContent.classList.add('with-nav');

            // Update active nav link
            const navLinks = utils.$$('.nav-link');
            navLinks.forEach(link => link.classList.remove('active'));

            const pageToNavMap = {
                'dashboard-page': 'dashboard',
                'assessment-page': 'assessments',
                'profile-page': 'profile'
            };

            const activeNav = pageToNavMap[activePageId];
            if (activeNav) {
                const activeLink = utils.$(`[data-page="${activeNav}"]`);
                if (activeLink) {
                    activeLink.classList.add('active');
                }
            }
        }
    }

    updateAuthUI() {
        if (this.isAuthenticated && this.currentUser) {
            // Update profile information
            const profileName = utils.$('#profile-name');
            const profileEmail = utils.$('#profile-email');

            if (profileName) {
                profileName.textContent = `${this.currentUser.firstName} ${this.currentUser.lastName}`;
            }
            if (profileEmail) {
                profileEmail.textContent = this.currentUser.email;
            }

            // Fill profile form
            this.fillProfileForm();
        }
    }

    fillProfileForm() {
        if (!this.currentUser) return;

        const fields = {
            'profile-first-name': this.currentUser.firstName,
            'profile-last-name': this.currentUser.lastName,
            'profile-organization': this.currentUser.organization,
            'profile-industry': this.currentUser.industry,
            'profile-role': this.currentUser.role
        };

        Object.entries(fields).forEach(([fieldId, value]) => {
            const field = utils.$(`#${fieldId}`);
            if (field && value) {
                field.value = value;
            }
        });
    }

    async updateProfile(profileData) {
        try {
            const response = await api.auth.updateProfile(profileData);
            
            // Update local user data
            this.currentUser = { ...this.currentUser, ...response.user };
            utils.storage.set('user', this.currentUser);
            
            // Update UI
            this.updateAuthUI();
            
            utils.toast.success('Profile updated successfully');
            return response;

        } catch (error) {
            utils.errorHandler.handle(error, 'Profile Update');
            throw error;
        }
    }

    logout() {
        // Clear authentication
        this.currentUser = null;
        this.isAuthenticated = false;
        api.clearAuth();

        // Show landing page
        this.showPage('landing-page');
        
        utils.toast.info('You have been logged out');
    }

    // Check if user is authenticated
    isLoggedIn() {
        return this.isAuthenticated && this.currentUser;
    }

    // Get current user
    getCurrentUser() {
        return this.currentUser;
    }

    // Require authentication
    requireAuth() {
        if (!this.isLoggedIn()) {
            this.showAuthPage();
            return false;
        }
        return true;
    }
}

// Initialize authentication manager
const auth = new AuthManager();

// Export for global use
window.auth = auth;

