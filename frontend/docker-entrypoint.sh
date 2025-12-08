#!/bin/sh

# Replace placeholder with actual environment variable value
# This allows runtime configuration of the API URL
sed -i "s|VITE_API_URL_PLACEHOLDER|${VITE_API_URL-http://localhost:8000}|g" /usr/share/nginx/html/env-config.js

# Start nginx
exec nginx -g 'daemon off;'
