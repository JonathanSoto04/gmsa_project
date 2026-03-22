import { defineConfig } from 'vite'
import { svelte } from '@sveltejs/vite-plugin-svelte'

// Configuración base de Vite para levantar el frontend Svelte en localhost.
export default defineConfig({
  plugins: [svelte()],
  server: {
    port: 5173,
    host: '0.0.0.0'
  }
})
