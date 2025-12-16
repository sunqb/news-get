FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

FROM nginx:alpine

# 复制构建产物
COPY --from=builder /app/dist /usr/share/nginx/html

# 复制nginx配置模板
COPY nginx.conf /etc/nginx/templates/default.conf.template

# 设置默认后端地址（Docker内部网络）
ENV BACKEND_URL=http://backend:80

EXPOSE 80

# nginx:alpine 镜像自带 envsubst 支持
# 启动时会自动将 /etc/nginx/templates/*.template 中的环境变量替换后复制到 /etc/nginx/conf.d/
CMD ["nginx", "-g", "daemon off;"]
