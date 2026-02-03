import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

/**
 * 文件级注释：Vite构建配置文件
 * 内部逻辑：配置React插件、开发服务器、构建设置
 */
export default defineConfig({
  /**
   * 路径解析配置
   * 内部逻辑：配置@别名指向src目录
   */
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src')
    }
  },

  /**
   * 插件配置
   * 内部逻辑：使用React插件支持JSX和Fast Refresh
   */
  plugins: [react()],

  /**
   * 开发服务器配置
   * 内部变量：port - 前端服务端口
   * 内部逻辑：配置API代理到后端服务
   */
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8010',  // 内部逻辑：后端服务端口
        changeOrigin: true,
      }
    }
  },

  /**
   * 构建设置
   * 内部逻辑：配置CommonJS转换和代码分割
   */
  build: {
    commonjsOptions: {
      include: [/node_modules/],
      transformMixedEsModules: true
    },
    /**
     * 代码分割配置
     * 内部逻辑：将第三方库分离到独立chunk，优化首屏加载
     */
    rollupOptions: {
      output: {
        manualChunks: {
          // React核心库
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          // UI组件库
          'antd': ['antd', '@ant-design/icons'],
          // 状态管理
          'state': ['zustand'],
          // HTTP客户端
          'http': ['axios'],
        }
      }
    },
    /**
     * chunk大小警告限制（KB）
     */
    chunkSizeWarningLimit: 1000
  }
})
