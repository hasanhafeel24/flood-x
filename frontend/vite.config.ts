import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import { resolve } from 'path'

export default defineConfig(({ mode }) => {
  // Load env variables for the current mode so we can use them in config
  const env = loadEnv(mode, process.cwd(), '')

  // In development, proxy to the local backend.
  // In production (Vercel), the frontend calls VITE_API_BASE_URL directly —
  // no proxy needed because the Render backend serves the API over HTTPS.
  const devBackendUrl = env.VITE_API_BASE_URL || 'http://localhost:8000'
  const devWsUrl = devBackendUrl.replace(/^http/, 'ws')

  return {
    plugins: [react()],

    resolve: {
      alias: {
        '@': resolve(import.meta.dirname, './src'),
      },
    },

    // Dev server proxy — only active during `npm run dev`
    server: {
      port: 5173,
      proxy: {
        '/api': {
          target: devBackendUrl,
          changeOrigin: true,
        },
        '/ws': {
          target: devWsUrl,
          ws: true,
          changeOrigin: true,
        },
      },
    },

    build: {
      outDir: 'dist',
      sourcemap: false,
      // Target modern browsers that support MapLibre GL JS
      target: 'es2020',
      rollupOptions: {
        output: {
          manualChunks(id) {
            if (id.includes('maplibre-gl')) return 'map'
            if (id.includes('recharts') || id.includes('d3-')) return 'charts'
            if (id.includes('zustand')) return 'state'
            if (id.includes('react-dom') || id.includes('react-router')) return 'vendor'
          },
        },
      },
    },
  }
})
