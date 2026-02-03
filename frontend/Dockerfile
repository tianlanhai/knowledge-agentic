# 前端Dockerfile
# 构建阶段：使用多阶段构建，减少最终镜像大小
FROM node:20-alpine AS build

# 安装 pnpm
RUN npm install -g pnpm@latest

# 设置工作目录
WORKDIR /app

# 复制package文件并安装依赖
# 先复制依赖文件，利用Docker缓存层优化构建速度
COPY package.json pnpm-lock.yaml ./

# 安装依赖（使用pnpm install --frozen-lockfile，确保使用锁文件中的精确版本）
RUN pnpm install --frozen-lockfile

# 复制源代码文件（排除node_modules等，由.dockerignore处理）
COPY src ./src
COPY index.html ./
COPY vite.config.ts ./
COPY tailwind.config.js ./
COPY postcss.config.js ./
COPY tsconfig.json ./
COPY tsconfig.node.json ./
COPY tsconfig.app.json ./

# 构建生产版本（跳过类型检查以加快构建速度）
RUN pnpm run build:skip-type-check

# 运行阶段：使用nginx alpine版本（更小的镜像体积）
FROM nginx:alpine

# 删除nginx默认配置和静态文件
RUN rm -rf /usr/share/nginx/html/* && \
    rm -f /etc/nginx/conf.d/default.conf

# 复制构建产物到nginx静态文件目录
COPY --from=build /app/dist /usr/share/nginx/html

# 复制nginx配置文件
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 暴露端口
EXPOSE 80

# 健康检查
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost/ || exit 1

# 启动nginx（前台运行，便于容器管理）
CMD ["nginx", "-g", "daemon off;"]
