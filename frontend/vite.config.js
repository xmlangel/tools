import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    {
      name: 'spa-fallback',
      configureServer(server) {
        server.middlewares.use((req, res, next) => {
          console.log('[SPA Fallback] Request URL:', req.url)
          // If the request is for a route (not a file), serve index.html
          if (!req.url.includes('.') && !req.url.startsWith('/api')) {
            console.log('[SPA Fallback] Rewriting to /index.html')
            req.url = '/index.html'
          }
          next()
        })
      },
    },
  ],
})
