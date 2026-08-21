import {resolve} from 'node:path';

import {defineConfig} from 'vite';
import react from '@vitejs/plugin-react';

/**
 * The build output lands in `backend/static`, which the FastAPI app serves.
 * One container, one origin, no CORS in production.
 */
export default defineConfig({
  plugins: [react()],
  build: {
    outDir: '../backend/static',
    emptyOutDir: true,
    sourcemap: false,
    rollupOptions: {
      input: {
        // `preview.html` renders captured fixtures with no live session, so the
        // catalog can be reviewed and regression-tested without an API key.
        main: resolve(__dirname, 'index.html'),
        preview: resolve(__dirname, 'preview.html'),
      },
    },
  },
  server: {
    port: 5173,
    // During local development Vite serves the SPA and proxies the API and the
    // websocket to the Python backend on 8080.
    proxy: {
      '/api': {target: 'http://localhost:8080', changeOrigin: true},
      '/healthz': {target: 'http://localhost:8080', changeOrigin: true},
      '/ws': {target: 'ws://localhost:8080', ws: true},
    },
  },
});
