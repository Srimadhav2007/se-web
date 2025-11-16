import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,   // or any free port
    proxy: {
      "/logic": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
        secure: false,
      },
      "/static": {
        target: "http://127.0.0.1:8000",
      }
    }
  }
})
