import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  // In development, /api requests go to the FastAPI backend (see the README for how to start it).
  server: { proxy: { '/api': 'http://localhost:8000' } },
})
