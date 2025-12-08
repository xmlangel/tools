// API Configuration
// This file provides centralized API endpoint configuration
// that can be overridden at runtime via environment variables

const getApiUrl = () => {
    // Check if runtime environment config is available (injected by docker-entrypoint.sh)
    if (typeof window !== 'undefined' && window.ENV && window.ENV.VITE_API_URL) {
        return window.ENV.VITE_API_URL;
    }

    // Fallback to build-time environment variable (for local development)
    if (import.meta.env.VITE_API_URL) {
        return import.meta.env.VITE_API_URL;
    }

    // Default to localhost for local development
    return 'http://localhost:8000';
};

// Use a getter to ensure the value is evaluated at runtime, not at module load time
Object.defineProperty(exports, 'API_URL', {
    get: getApiUrl
});

export { getApiUrl as API_URL };

export default {
    get API_URL() {
        return getApiUrl();
    }
};
