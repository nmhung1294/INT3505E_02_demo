// API Base URL
const API_BASE_URL = '/api';

// Token management using HTTP-only cookies
// Note: We cannot access HTTP-only cookies from JavaScript for security reasons
// The token is automatically sent with each request by the browser
const TokenManager = {
    // HTTP-only cookies are managed by the browser automatically
    // We can't set, get, or remove them directly from JavaScript
    
    isAuthenticated: async () => {
        // Check authentication by calling the /auth/me endpoint
        try {
            const response = await fetch(`${API_BASE_URL}/auth/me`, {
                method: 'GET',
                credentials: 'same-origin'  // Include cookies
            });
            return response.ok;
        } catch (e) {
            return false;
        }
    },
    
    getUserFromToken: async () => {
        // Get user info from the /auth/me endpoint
        try {
            const response = await fetch(`${API_BASE_URL}/auth/me`, {
                method: 'GET',
                credentials: 'same-origin'
            });
            if (response.ok) {
                return await response.json();
            }
            return null;
        } catch (e) {
            return null;
        }
    }
};

// API helper with automatic cookie handling
const api = {
    request: async (endpoint, options = {}) => {
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers
        };
        
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            ...options,
            headers,
            credentials: 'same-origin'  // Important: Include cookies in requests
        });
        
        if (response.status === 401) {
            // Token expired or invalid
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
            credentials: 'same-origin',  // Include cookies
            body: JSON.stringify({ email })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.message || 'Login failed');
        }
        
        // Token is now set in HTTP-only cookie by the server
        // No need to save it manually
        
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

async function logout() {
    try {
        // Call logout endpoint to clear HTTP-only cookie
        await fetch(`${API_BASE_URL}/auth/logout`, {
            method: 'POST',
            credentials: 'same-origin'
        });
    } catch (error) {
        console.error('Logout error:', error);
    }
    
    // Redirect to login page
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
                if (event.data.type === 'google_auth_success') {
                    // Cookie is set by the server, just reload
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
async function checkAuth() {
    const isAuth = await TokenManager.isAuthenticated();
    if (!isAuth) {
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
