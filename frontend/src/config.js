// API Configuration
// This file provides centralized API endpoint configuration
// that can be overridden at runtime via environment variables

const getApiUrl = () => {
    // Check if runtime environment config is available (injected by docker-entrypoint.sh)
    if (typeof window !== 'undefined' && window.ENV && window.ENV.VITE_API_URL) {
        return window.ENV.VITE_API_URL;
    }

    // Fallback to build-time environment variable (for local development)
    if (typeof import.meta !== 'undefined' && import.meta.env && import.meta.env.VITE_API_URL) {
        return import.meta.env.VITE_API_URL;
    }

    // Default to localhost for local development
    return 'http://localhost:8000';
};

// Export as a Proxy that calls getApiUrl() when converted to string
// This ensures the value is evaluated at usage time, not module load time
const apiUrlHandler = {
    toString: getApiUrl,
    valueOf: getApiUrl
};

export const API_URL = new Proxy(apiUrlHandler, {
    get(target, prop) {
        if (prop === 'toString' || prop === 'valueOf' || prop === Symbol.toPrimitive) {
            return () => getApiUrl();
        }
        return getApiUrl()[prop];
    }
});

export default {
    get API_URL() {
        return getApiUrl();
    }
};
