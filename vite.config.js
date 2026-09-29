import {defineConfig} from 'vite';
import react from '@vitejs/plugin-react';
export default defineConfig({plugins:[react()],base:'./',define:{__DATA_VERSION__:JSON.stringify(String(Date.now()))},build:{outDir:'docs',chunkSizeWarningLimit:700}});
