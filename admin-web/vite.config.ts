import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes('node_modules')) return

          if (id.includes('/antd/') || id.includes('/@ant-design/')) {
            return 'antd'
          }
          if (id.includes('/recharts/')) {
            return 'charts'
          }
          if (id.includes('/react-quill/') || id.includes('/quill/')) {
            return 'editor'
          }
          if (id.includes('/axios/')) {
            return 'network'
          }
          if (
            id.includes('/react/') ||
            id.includes('/react-dom/') ||
            id.includes('/react-router/') ||
            id.includes('/react-router-dom/')
          ) {
            return 'react-core'
          }
        },
      },
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
})
