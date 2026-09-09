import path from 'node:path'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  build: {
    // The edge proxy in front of this deployment truncates any single response
    // over ~104 KiB, so no emitted asset may exceed that. Splitting the vendor
    // bundle per package keeps every chunk well under the limit.
    chunkSizeWarningLimit: 100,
    rollupOptions: {
      output: {
        manualChunks(id: string) {
          if (!id.includes('node_modules')) return
          const match = id.split('node_modules/')[1]
          const pkg = match.startsWith('@')
            ? match.split('/').slice(0, 2).join('/')
            : match.split('/')[0]
          if (pkg.startsWith('react-dom')) return 'vendor-react-dom'
          if (pkg === 'react' || pkg === 'scheduler') return 'vendor-react'
          if (pkg.startsWith('react-router')) return 'vendor-router'
          if (pkg.startsWith('@radix-ui')) return 'vendor-radix'
          if (pkg === 'lucide-react') return 'vendor-icons'
          if (pkg === 'recharts' || pkg === 'd3' || pkg.startsWith('d3-')) return 'vendor-charts'
          if (pkg === 'axios') return 'vendor-axios'
          return 'vendor-misc'
        },
      },
    },
  },
  server: {
    host: true,
    port: 5173,
    allowedHosts: ['face.api.nsumt.uz'],
    proxy: {
      '/api': {
        target: 'http://backend:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
})
