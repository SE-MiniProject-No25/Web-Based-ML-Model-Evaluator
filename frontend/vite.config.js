import process from 'node:process'

import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  // In development, /api requests go to the FastAPI backend (see the README for how to start it).
  // VITE_API_TARGET points them elsewhere, e.g. the end-to-end tests' own backend.
  server: { proxy: { '/api': process.env.VITE_API_TARGET || 'http://localhost:8000' } },
})
