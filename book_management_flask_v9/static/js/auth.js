// API Base URL
const API_BASE_URL = '/api';

// Token management using sessionStorage
const TokenManager = {
    set: (token) => {
        sessionStorage.setItem('auth_token', token);
    },
    get: () => {
        return sessionStorage.getItem('auth_token');
    },
    remove: () => {
        sessionStorage.removeItem('auth_token');
    },
    isAuthenticated: () => {
        const token = TokenManager.get();
        if (!token) return false;
        
        // Check if token is expired
        try {
            const payload = JSON.parse(atob(token.split('.')[1]));
            const exp = payload.exp * 1000; // Convert to milliseconds
            return Date.now() < exp;
        } catch (e) {
            return false;
        }
    },
    getUserFromToken: () => {
        const token = TokenManager.get();
        if (!token) return null;
        
        try {
            const payload = JSON.parse(atob(token.split('.')[1]));
            return payload;
        } catch (e) {
            return null;
        }
    }
};

// API helper with automatic token injection
const api = {
    request: async (endpoint, options = {}) => {
        const token = TokenManager.get();
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers
        };
        
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }
        
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            ...options,
            headers
        });
        
        if (response.status === 401) {
            // Token expired or invalid
            TokenManager.remove();
            window.location.href = '/login.html';
            throw new Error('Unauthorized');
        }
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.message || 'Request failed');
        }
        
        return data;
    },
    
    get: (endpoint) => api.request(endpoint, { method: 'GET' }),
    post: (endpoint, body) => api.request(endpoint, { method: 'POST', body: JSON.stringify(body) }),
    put: (endpoint, body) => api.request(endpoint, { method: 'PUT', body: JSON.stringify(body) }),
    delete: (endpoint) => api.request(endpoint, { method: 'DELETE' })
};

// Auth functions
async function login(email) {
    try {
        const response = await fetch(`${API_BASE_URL}/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.message || 'Login failed');
        }
        
        // Save token to sessionStorage
        TokenManager.set(data.token);
        
        return data;
    } catch (error) {
        throw error;
    }
}

async function register(name, email) {
    try {
        const response = await fetch(`${API_BASE_URL}/auth/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ name, email })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.message || 'Registration failed');
        }
        
        return data;
    } catch (error) {
        throw error;
    }
}

function logout() {
    TokenManager.remove();
    window.location.href = '/login.html';
}

async function loginWithGoogle() {
    try {
        const response = await fetch(`${API_BASE_URL}/auth/google`);
        const data = await response.json();
        
        if (data.auth_url) {
            // Open Google login in popup
            const width = 500;
            const height = 600;
            const left = (screen.width / 2) - (width / 2);
            const top = (screen.height / 2) - (height / 2);
            
            const popup = window.open(
                data.auth_url,
                'Google Login',
                `width=${width},height=${height},left=${left},top=${top}`
            );
            
            // Listen for message from popup
            window.addEventListener('message', function(event) {
                if (event.data.type === 'google_auth_success' && event.data.token) {
                    TokenManager.set(event.data.token);
                    window.location.href = '/';
                    if (popup) popup.close();
                }
            });
        }
    } catch (error) {
        console.error('Google login error:', error);
        alert('Failed to initiate Google login');
    }
}

// Check authentication on page load
function checkAuth() {
    if (!TokenManager.isAuthenticated()) {
        if (window.location.pathname !== '/login.html' && window.location.pathname !== '/register.html') {
            window.location.href = '/login.html';
        }
    }
}

// Show alert message
function showAlert(message, type = 'error') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type}`;
    alertDiv.textContent = message;
    
    const container = document.querySelector('.auth-container') || document.querySelector('.content');
    if (container) {
        container.insertBefore(alertDiv, container.firstChild);
        
        setTimeout(() => {
            alertDiv.remove();
        }, 5000);
    }
}
