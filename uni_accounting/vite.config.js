import { fileURLToPath, URL } from 'node:url';
import path from 'path';
import { defineConfig } from 'vite';
import uni from '@dcloudio/vite-plugin-uni';

// 确保在 Vite 启动的最早阶段就设置好输入目录
process.env.UNI_INPUT_DIR = path.resolve(__dirname, 'src');

export default defineConfig({
  plugins: [uni()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    host: '0.0.0.0',
    port: 5175,
    strictPort: true,
    // H5 开发：浏览器请求 /api → 转发到本地 Django
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8030',
        changeOrigin: true,
      },
    },
  },
});

