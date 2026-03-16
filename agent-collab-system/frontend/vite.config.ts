import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const apiTarget = env.VITE_API_TARGET || 'http://127.0.0.1:8000'

  return {
    plugins: [vue()],
    build: {
      chunkSizeWarningLimit: 900,
      rollupOptions: {
        output: {
          manualChunks(id) {
            if (!id.includes('node_modules')) {
              return undefined
            }
            if (id.includes('element-plus')) {
              return 'vendor-element-plus'
            }
            if (id.includes('@vue-flow')) {
              return 'vendor-vue-flow'
            }
            if (id.includes('echarts')) {
              return 'vendor-echarts'
            }
            if (id.includes('pinia') || id.includes('vue-router') || id.includes('/vue/')) {
              return 'vendor-vue-core'
            }
            return 'vendor-misc'
          },
        },
      },
    },
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url)),
      },
    },
    server: {
      port: 5173,
      proxy: {
        '/api': {
          target: apiTarget,
          changeOrigin: true,
        },
      },
    },
  }
})
