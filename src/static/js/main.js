// Qryti - ISO 42001 Compliance Platform - Main Application

class App {
    constructor() {
        this.isInitialized = false;
        this.currentRoute = '';
        this.init();
    }

    async init() {
        try {
            // Wait for DOM to be ready
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', () => this.start());
            } else {
                this.start();
            }
        } catch (error) {
            console.error('App initialization error:', error);
            utils.errorHandler.handle(error, 'Application Initialization');
        }
    }

    async start() {
        try {
            // Initialize Lucide icons
            if (window.lucide) {
                lucide.createIcons();
            }

            // Setup routing
            this.setupRouting();

            // Setup global event listeners
            this.setupGlobalEvents();

            // Initialize loading screen
            this.initLoadingScreen();

            // Check authentication and route
            await this.checkAuthAndRoute();

            // Mark as initialized
            this.isInitialized = true;

            console.log('Qryti - ISO 42001 Compliance Platform initialized successfully');

        } catch (error) {
            console.error('App start error:', error);
            utils.errorHandler.handle(error, 'Application Start');
        }
    }

    setupRouting() {
        // Handle hash changes
        window.addEventListener('hashchange', () => {
            this.handleRoute();
        });

        // Handle back/forward navigation
        window.addEventListener('popstate', () => {
            this.handleRoute();
        });

        // Initial route
        this.handleRoute();
    }

    handleRoute() {
        const hash = window.location.hash.slice(1) || 'landing';
        this.currentRoute = hash;

        // Route to appropriate page
        switch (hash) {
            case 'landing':
                this.showLandingPage();
                break;
            case 'auth':
                this.showAuthPage();
                break;
            case 'dashboard':
                if (auth.requireAuth()) {
                    this.showDashboardPage();
                }
                break;
            case 'assessments':
                if (auth.requireAuth()) {
                    this.showAssessmentsPage();
                }
                break;
            case 'profile':
                if (auth.requireAuth()) {
                    this.showProfilePage();
                }
                break;
            default:
                // Unknown route, redirect to landing
                this.navigate('landing');
        }
    }

    setupGlobalEvents() {
        // Global error handler
        window.addEventListener('error', (event) => {
            console.error('Global error:', event.error);
            utils.errorHandler.handle(event.error, 'Global');
        });

        // Unhandled promise rejection handler
        window.addEventListener('unhandledrejection', (event) => {
            console.error('Unhandled promise rejection:', event.reason);
            utils.errorHandler.handle(event.reason, 'Promise');
        });

        // Network status
        window.addEventListener('online', () => {
            utils.toast.success('Connection restored');
        });

        window.addEventListener('offline', () => {
            utils.toast.warning('Connection lost. Some features may not work.');
        });

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            this.handleKeyboardShortcuts(e);
        });

        // Auto-save functionality (for forms)
        this.setupAutoSave();
    }

    handleKeyboardShortcuts(e) {
        // Ctrl/Cmd + K for search (if implemented)
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            // Implement global search if needed
        }

        // Escape to close modals
        if (e.key === 'Escape') {
            if (utils.modal.isOpen()) {
                utils.modal.close();
            }
        }
    }

    setupAutoSave() {
        // Auto-save form data to localStorage
        const autoSaveFields = document.querySelectorAll('[data-autosave]');
        
        autoSaveFields.forEach(field => {
            const key = `autosave_${field.dataset.autosave}`;
            
            // Load saved value
            const savedValue = utils.storage.get(key);
            if (savedValue && !field.value) {
                field.value = savedValue;
            }

            // Save on input
            field.addEventListener('input', utils.debounce(() => {
                utils.storage.set(key, field.value);
            }, 1000));
        });
    }

    initLoadingScreen() {
        const loadingScreen = utils.$('#loading-screen');
        if (loadingScreen) {
            // Hide loading screen after a short delay
            setTimeout(() => {
                loadingScreen.classList.add('fade-out');
                setTimeout(() => {
                    loadingScreen.style.display = 'none';
                }, 500);
            }, 1500);
        }
    }

    async checkAuthAndRoute() {
        // Check if user is authenticated
        if (auth.isLoggedIn()) {
            // Verify token is still valid
            try {
                await api.auth.getProfile();
                
                // If current route is landing or auth, redirect to dashboard
                if (this.currentRoute === 'landing' || this.currentRoute === 'auth') {
                    this.navigate('dashboard');
                }
            } catch (error) {
                // Token invalid, clear auth and show landing
                auth.logout();
                this.navigate('landing');
            }
        } else {
            // Not authenticated, show landing page
            if (this.currentRoute !== 'auth') {
                this.navigate('landing');
            }
        }
    }

    // Page navigation methods
    showLandingPage() {
        auth.showPage('landing-page');
        this.updatePageTitle('Qryti - ISO 42001 Compliance Platform');
    }

    showAuthPage() {
        auth.showPage('auth-page');
        this.updatePageTitle('Sign In - Qryti Platform');
    }

    showDashboardPage() {
        auth.showPage('dashboard-page');
        dashboard.loadDashboardData();
        this.updatePageTitle('Dashboard - Qryti Platform');
    }

    showAssessmentsPage() {
        auth.showPage('assessment-page');
        assessments.loadAssessments();
        this.updatePageTitle('Assessments - Qryti Platform');
    }

    showProfilePage() {
        auth.showPage('profile-page');
        this.updatePageTitle('Profile - Qryti Platform');
    }

    // Navigation helper
    navigate(route) {
        window.location.hash = route;
    }

    // Update page title
    updatePageTitle(title) {
        document.title = title;
    }

    // Health check
    async performHealthCheck() {
        try {
            await api.health.check();
            return true;
        } catch (error) {
            console.warn('Health check failed:', error);
            return false;
        }
    }

    // Performance monitoring
    measurePerformance() {
        if ('performance' in window) {
            const navigation = performance.getEntriesByType('navigation')[0];
            const loadTime = navigation.loadEventEnd - navigation.loadEventStart;
            
            console.log(`Page load time: ${loadTime}ms`);
            
            // Report to analytics if needed
            if (loadTime > 3000) {
                console.warn('Slow page load detected');
            }
        }
    }

    // Feature detection
    checkBrowserSupport() {
        const requiredFeatures = [
            'fetch',
            'Promise',
            'localStorage',
            'addEventListener'
        ];

        const unsupportedFeatures = requiredFeatures.filter(feature => 
            !(feature in window)
        );

        if (unsupportedFeatures.length > 0) {
            const message = `Your browser doesn't support required features: ${unsupportedFeatures.join(', ')}. Please update your browser.`;
            utils.toast.error(message, 0); // Don't auto-hide
            return false;
        }

        return true;
    }

    // Service worker registration (for future PWA features)
    async registerServiceWorker() {
        if ('serviceWorker' in navigator) {
            try {
                const registration = await navigator.serviceWorker.register('/sw.js');
                console.log('Service Worker registered:', registration);
            } catch (error) {
                console.log('Service Worker registration failed:', error);
            }
        }
    }

    // Analytics tracking (placeholder)
    trackEvent(category, action, label = null, value = null) {
        // Implement analytics tracking here
        console.log('Analytics event:', { category, action, label, value });
    }

    // Error reporting (placeholder)
    reportError(error, context = 'Unknown') {
        // Implement error reporting here
        console.error('Error reported:', { error, context, timestamp: new Date().toISOString() });
    }

    // App state management
    getAppState() {
        return {
            isInitialized: this.isInitialized,
            currentRoute: this.currentRoute,
            isAuthenticated: auth.isLoggedIn(),
            user: auth.getCurrentUser()
        };
    }

    // Debug helpers
    debug() {
        return {
            app: this.getAppState(),
            auth: {
                isLoggedIn: auth.isLoggedIn(),
                user: auth.getCurrentUser()
            },
            storage: {
                token: utils.storage.get('accessToken'),
                user: utils.storage.get('user')
            },
            api: {
                baseURL: api.baseURL,
                hasToken: !!api.token
            }
        };
    }
}

// Initialize application
const app = new App();

// Global app reference
window.app = app;

// Development helpers
if (process?.env?.NODE_ENV === 'development' || window.location.hostname === 'localhost') {
    window.debug = () => app.debug();
    window.clearStorage = () => {
        utils.storage.clear();
        location.reload();
    };
}

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = App;
}

