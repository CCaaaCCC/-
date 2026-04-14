import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    strictPort: true,
  },
  build: {
    chunkSizeWarningLimit: 900,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes('node_modules')) {
            return;
          }

          if (id.includes('node_modules/vue/') || id.includes('node_modules/vue-router/')) {
            return 'vendor-vue';
          }

          if (id.includes('node_modules/axios/')) {
            return 'vendor-http';
          }

          if (id.includes('node_modules/echarts/')) {
            return 'vendor-chart';
          }

          if (id.includes('node_modules/@element-plus/icons-vue/')) {
            return 'vendor-icons';
          }

          if (id.includes('node_modules/element-plus/')) {
            return 'vendor-ep';
          }
        },
      }
    }
  }
})
