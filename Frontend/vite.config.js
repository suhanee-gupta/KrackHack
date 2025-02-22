import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'//config for dev server

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server:{
    port:3000,
  }
})
