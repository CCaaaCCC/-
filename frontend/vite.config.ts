import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          'vendor-vue': ['vue', 'vue-router'],
          'vendor-ep': ['element-plus'],
          'vendor-icons': ['@element-plus/icons-vue'],
          'vendor-chart': ['echarts'],
          'vendor-http': ['axios']
        }
      }
    }
  }
})
