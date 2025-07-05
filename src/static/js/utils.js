// Qryti - ISO 42001 Compliance Platform - Utility Functions

// DOM Utilities
const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => document.querySelectorAll(selector);

// Local Storage Utilities
const storage = {
    get: (key) => {
        try {
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : null;
        } catch (error) {
            console.error('Error reading from localStorage:', error);
            return null;
        }
    },
    
    set: (key, value) => {
        try {
            localStorage.setItem(key, JSON.stringify(value));
            return true;
        } catch (error) {
            console.error('Error writing to localStorage:', error);
            return false;
        }
    },
    
    remove: (key) => {
        try {
            localStorage.removeItem(key);
            return true;
        } catch (error) {
            console.error('Error removing from localStorage:', error);
            return false;
        }
    },
    
    clear: () => {
        try {
            localStorage.clear();
            return true;
        } catch (error) {
            console.error('Error clearing localStorage:', error);
            return false;
        }
    }
};

// Toast Notifications
const toast = {
    container: null,
    
    init() {
        this.container = $('#toast-container');
        if (!this.container) {
            this.container = document.createElement('div');
            this.container.id = 'toast-container';
            this.container.className = 'toast-container';
            document.body.appendChild(this.container);
        }
    },
    
    show(message, type = 'info', duration = 5000) {
        if (!this.container) this.init();
        
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        
        const icons = {
            success: 'check-circle',
            error: 'x-circle',
            warning: 'alert-triangle',
            info: 'info'
        };
        
        toast.innerHTML = `
            <i data-lucide="${icons[type] || 'info'}" class="toast-icon"></i>
            <div class="toast-content">
                <div class="toast-message">${message}</div>
            </div>
            <button class="toast-close" onclick="toast.remove(this.parentElement)">
                <i data-lucide="x"></i>
            </button>
        `;
        
        this.container.appendChild(toast);
        
        // Initialize Lucide icons
        if (window.lucide) {
            lucide.createIcons();
        }
        
        // Show toast
        setTimeout(() => toast.classList.add('visible'), 100);
        
        // Auto remove
        if (duration > 0) {
            setTimeout(() => this.remove(toast), duration);
        }
        
        return toast;
    },
    
    remove(toastElement) {
        if (toastElement && toastElement.parentElement) {
            toastElement.classList.remove('visible');
            setTimeout(() => {
                if (toastElement.parentElement) {
                    toastElement.parentElement.removeChild(toastElement);
                }
            }, 300);
        }
    },
    
    success(message, duration) {
        return this.show(message, 'success', duration);
    },
    
    error(message, duration) {
        return this.show(message, 'error', duration);
    },
    
    warning(message, duration) {
        return this.show(message, 'warning', duration);
    },
    
    info(message, duration) {
        return this.show(message, 'info', duration);
    }
};

// Modal Utilities
const modal = {
    overlay: null,
    content: null,
    
    init() {
        this.overlay = $('#modal-overlay');
        this.content = $('#modal-content');
        
        if (!this.overlay) {
            this.overlay = document.createElement('div');
            this.overlay.id = 'modal-overlay';
            this.overlay.className = 'modal-overlay hidden';
            this.overlay.innerHTML = '<div id="modal-content" class="modal-content"></div>';
            document.body.appendChild(this.overlay);
            this.content = $('#modal-content');
        }
        
        // Close on overlay click
        this.overlay.addEventListener('click', (e) => {
            if (e.target === this.overlay) {
                this.close();
            }
        });
        
        // Close on escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isOpen()) {
                this.close();
            }
        });
    },
    
    show(content, options = {}) {
        if (!this.overlay) this.init();
        
        const { title, size = 'medium', closable = true } = options;
        
        let modalHTML = '';
        
        if (title) {
            modalHTML += `
                <div class="modal-header">
                    <h3 class="modal-title">${title}</h3>
                    ${closable ? '<button class="modal-close" onclick="modal.close()"><i data-lucide="x"></i></button>' : ''}
                </div>
            `;
        }
        
        modalHTML += `<div class="modal-body">${content}</div>`;
        
        this.content.innerHTML = modalHTML;
        this.content.className = `modal-content modal-${size}`;
        
        this.overlay.classList.remove('hidden');
        setTimeout(() => this.overlay.classList.add('visible'), 10);
        
        // Initialize Lucide icons
        if (window.lucide) {
            lucide.createIcons();
        }
        
        // Focus management
        const firstFocusable = this.content.querySelector('button, input, select, textarea, [tabindex]:not([tabindex="-1"])');
        if (firstFocusable) {
            firstFocusable.focus();
        }
        
        return this.content;
    },
    
    close() {
        if (this.overlay) {
            this.overlay.classList.remove('visible');
            setTimeout(() => {
                this.overlay.classList.add('hidden');
                this.content.innerHTML = '';
            }, 300);
        }
    },
    
    isOpen() {
        return this.overlay && this.overlay.classList.contains('visible');
    },
    
    confirm(message, title = 'Confirm') {
        return new Promise((resolve) => {
            const content = `
                <p style="margin-bottom: 1.5rem;">${message}</p>
                <div class="modal-footer">
                    <button class="btn btn-outline" onclick="modal.close(); modal._resolveConfirm(false);">Cancel</button>
                    <button class="btn btn-primary" onclick="modal.close(); modal._resolveConfirm(true);">Confirm</button>
                </div>
            `;
            
            this._resolveConfirm = resolve;
            this.show(content, { title, closable: false });
        });
    }
};

// Form Utilities
const form = {
    validate(formElement) {
        const errors = [];
        const inputs = formElement.querySelectorAll('input[required], select[required], textarea[required]');
        
        inputs.forEach(input => {
            this.clearError(input);
            
            if (!input.value.trim()) {
                this.showError(input, 'This field is required');
                errors.push(`${input.name || input.id} is required`);
            } else if (input.type === 'email' && !this.isValidEmail(input.value)) {
                this.showError(input, 'Please enter a valid email address');
                errors.push('Invalid email format');
            } else if (input.type === 'password' && input.value.length < 8) {
                this.showError(input, 'Password must be at least 8 characters long');
                errors.push('Password too short');
            }
        });
        
        return errors;
    },
    
    showError(input, message) {
        input.classList.add('error');
        
        let errorElement = input.parentElement.querySelector('.form-error');
        if (!errorElement) {
            errorElement = document.createElement('div');
            errorElement.className = 'form-error';
            input.parentElement.appendChild(errorElement);
        }
        
        errorElement.textContent = message;
        input.classList.add('animate-shake');
        setTimeout(() => input.classList.remove('animate-shake'), 500);
    },
    
    clearError(input) {
        input.classList.remove('error');
        const errorElement = input.parentElement.querySelector('.form-error');
        if (errorElement) {
            errorElement.remove();
        }
    },
    
    clearAllErrors(formElement) {
        const inputs = formElement.querySelectorAll('input, select, textarea');
        inputs.forEach(input => this.clearError(input));
    },
    
    isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    },
    
    serialize(formElement) {
        const formData = new FormData(formElement);
        const data = {};
        
        for (let [key, value] of formData.entries()) {
            if (data[key]) {
                if (Array.isArray(data[key])) {
                    data[key].push(value);
                } else {
                    data[key] = [data[key], value];
                }
            } else {
                data[key] = value;
            }
        }
        
        return data;
    },
    
    setLoading(button, loading = true) {
        if (loading) {
            button.disabled = true;
            button.classList.add('btn-loading');
            button.dataset.originalText = button.textContent;
        } else {
            button.disabled = false;
            button.classList.remove('btn-loading');
            if (button.dataset.originalText) {
                button.textContent = button.dataset.originalText;
            }
        }
    }
};

// Progress Utilities
const progress = {
    updateCircle(element, percentage) {
        const circle = element.querySelector('.progress-ring, .chart-circle');
        if (circle) {
            const degrees = (percentage / 100) * 360;
            circle.style.background = `conic-gradient(
                var(--primary-500) 0deg ${degrees}deg,
                var(--gray-200) ${degrees}deg 360deg
            )`;
        }
        
        const percentageElement = element.querySelector('.progress-percentage, .chart-percentage');
        if (percentageElement) {
            percentageElement.textContent = `${Math.round(percentage)}%`;
        }
    },
    
    updateBar(element, percentage) {
        const fill = element.querySelector('.progress-fill');
        if (fill) {
            fill.style.width = `${percentage}%`;
        }
    },
    
    animateProgress(element, targetPercentage, duration = 1000) {
        const startTime = Date.now();
        const startPercentage = 0;
        
        const animate = () => {
            const elapsed = Date.now() - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const currentPercentage = startPercentage + (targetPercentage - startPercentage) * progress;
            
            if (element.classList.contains('progress-circle-large') || element.classList.contains('compliance-chart')) {
                this.updateCircle(element, currentPercentage);
            } else {
                this.updateBar(element, currentPercentage);
            }
            
            if (progress < 1) {
                requestAnimationFrame(animate);
            }
        };
        
        requestAnimationFrame(animate);
    }
};

// Date Utilities
const dateUtils = {
    format(date, format = 'MMM DD, YYYY') {
        const d = new Date(date);
        const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                       'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
        
        const formatMap = {
            'YYYY': d.getFullYear(),
            'MM': String(d.getMonth() + 1).padStart(2, '0'),
            'MMM': months[d.getMonth()],
            'DD': String(d.getDate()).padStart(2, '0'),
            'HH': String(d.getHours()).padStart(2, '0'),
            'mm': String(d.getMinutes()).padStart(2, '0')
        };
        
        return format.replace(/YYYY|MMM|MM|DD|HH|mm/g, match => formatMap[match]);
    },
    
    timeAgo(date) {
        const now = new Date();
        const diff = now - new Date(date);
        const seconds = Math.floor(diff / 1000);
        const minutes = Math.floor(seconds / 60);
        const hours = Math.floor(minutes / 60);
        const days = Math.floor(hours / 24);
        
        if (days > 0) return `${days} day${days > 1 ? 's' : ''} ago`;
        if (hours > 0) return `${hours} hour${hours > 1 ? 's' : ''} ago`;
        if (minutes > 0) return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
        return 'Just now';
    },
    
    isToday(date) {
        const today = new Date();
        const checkDate = new Date(date);
        return today.toDateString() === checkDate.toDateString();
    }
};

// URL Utilities
const urlUtils = {
    getParams() {
        const params = new URLSearchParams(window.location.search);
        const result = {};
        for (let [key, value] of params.entries()) {
            result[key] = value;
        }
        return result;
    },
    
    setParam(key, value) {
        const url = new URL(window.location);
        url.searchParams.set(key, value);
        window.history.pushState({}, '', url);
    },
    
    removeParam(key) {
        const url = new URL(window.location);
        url.searchParams.delete(key);
        window.history.pushState({}, '', url);
    },
    
    navigate(path) {
        window.history.pushState({}, '', path);
        window.dispatchEvent(new PopStateEvent('popstate'));
    }
};

// Debounce Utility
const debounce = (func, wait) => {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
};

// Throttle Utility
const throttle = (func, limit) => {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
};

// Animation Utilities
const animate = {
    fadeIn(element, duration = 300) {
        element.style.opacity = '0';
        element.style.display = 'block';
        
        let start = null;
        const step = (timestamp) => {
            if (!start) start = timestamp;
            const progress = timestamp - start;
            const opacity = Math.min(progress / duration, 1);
            
            element.style.opacity = opacity;
            
            if (progress < duration) {
                requestAnimationFrame(step);
            }
        };
        
        requestAnimationFrame(step);
    },
    
    fadeOut(element, duration = 300) {
        let start = null;
        const initialOpacity = parseFloat(getComputedStyle(element).opacity);
        
        const step = (timestamp) => {
            if (!start) start = timestamp;
            const progress = timestamp - start;
            const opacity = initialOpacity * (1 - Math.min(progress / duration, 1));
            
            element.style.opacity = opacity;
            
            if (progress < duration) {
                requestAnimationFrame(step);
            } else {
                element.style.display = 'none';
            }
        };
        
        requestAnimationFrame(step);
    },
    
    slideUp(element, duration = 300) {
        const height = element.offsetHeight;
        element.style.height = height + 'px';
        element.style.overflow = 'hidden';
        
        let start = null;
        const step = (timestamp) => {
            if (!start) start = timestamp;
            const progress = timestamp - start;
            const currentHeight = height * (1 - Math.min(progress / duration, 1));
            
            element.style.height = currentHeight + 'px';
            
            if (progress < duration) {
                requestAnimationFrame(step);
            } else {
                element.style.display = 'none';
                element.style.height = '';
                element.style.overflow = '';
            }
        };
        
        requestAnimationFrame(step);
    }
};

// Error Handling
const errorHandler = {
    handle(error, context = 'Application') {
        console.error(`${context} Error:`, error);
        
        let message = 'An unexpected error occurred. Please try again.';
        
        if (error.message) {
            message = error.message;
        } else if (typeof error === 'string') {
            message = error;
        }
        
        toast.error(message);
    },
    
    network(error) {
        console.error('Network Error:', error);
        toast.error('Network error. Please check your connection and try again.');
    },
    
    validation(errors) {
        if (Array.isArray(errors)) {
            errors.forEach(error => toast.warning(error));
        } else {
            toast.warning(errors);
        }
    }
};

// Initialize utilities when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    toast.init();
    modal.init();
});

// Export utilities for use in other modules
window.utils = {
    $, $$, storage, toast, modal, form, progress, dateUtils, urlUtils,
    debounce, throttle, animate, errorHandler
};

