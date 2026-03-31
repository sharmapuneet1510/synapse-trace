import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/trace': { target: 'http://localhost:8000', changeOrigin: true },
      '/graph': { target: 'http://localhost:8000', changeOrigin: true },
      '/config': { target: 'http://localhost:8000', changeOrigin: true },
      '/logs': { target: 'http://localhost:8000', changeOrigin: true },
    },
  },
});
