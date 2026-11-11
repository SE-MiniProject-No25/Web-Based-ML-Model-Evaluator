import react from '@vitejs/plugin-react'
import { defineConfig } from 'vitest/config'

// Unit and component tests (TEST-01): `npm test`, or `npm run coverage` for line and branch coverage.
export default defineConfig({
  plugins: [react()],
  esbuild: { jsx: 'automatic' },
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.js'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json-summary', 'html'],
      include: ['src/**/*.{js,jsx}'],
      // main.jsx only mounts the app; mockAPI.js is a development stand-in for the backend.
      exclude: ['src/main.jsx', 'src/mockAPI.js', 'src/test/**'],
    },
  },
})
