import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/merchants_1o1': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      }
    }
  }
}) 