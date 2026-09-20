import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  // Read the repo-root .env (not frontend/.env) — there is only ever one .env file.
  envDir: '../',
})
