import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Собирается в статику (dist/), которую забирает Nginx на втором этапе сборки.
export default defineConfig({
  plugins: [react()],
  build: {
    outDir: 'dist',
    sourcemap: false,
  },
  server: {
    port: 5173,
    host: true,
  },
})
