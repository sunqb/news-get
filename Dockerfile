# 单容器部署：前端 + 后端
# 构建命令: docker build -t news-task .
# 运行命令: docker run -d -p 8000:8000 --env-file .env news-task

# ===== 阶段1: 构建前端 =====
FROM node:20-alpine AS frontend-builder

WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# ===== 阶段2: 运行后端 + 提供前端静态文件 =====
FROM python:3.11-slim

WORKDIR /app

# 安装依赖
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制后端代码
COPY backend/app ./app

# 复制前端构建产物到静态文件目录
COPY --from=frontend-builder /frontend/dist ./static

# 创建数据目录
RUN mkdir -p /app/data

# 环境变量
ENV DATABASE_URL=sqlite+aiosqlite:///./data/app.db
ENV DEBUG=false

EXPOSE 8000

# 启动
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
