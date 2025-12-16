# News Task Manager

基于邮箱验证码登录的定时任务管理系统，类似 Grok 的任务调度功能。用户可以创建定时任务，系统会按照设定的频率执行任务并将结果通过邮件发送。

## 功能特性

- **邮箱验证码登录**：无需密码，通过邮箱验证码一次性登录
- **任务管理**：创建、编辑、删除、暂停/启用任务
- **多种频率**：支持一次性、每天、每周、每月、每年执行
- **定时执行**：自定义任务执行时间
- **专家模式**：可选的高级任务模式
- **邮件通知**：任务执行结果通过邮件发送
- **AI服务集成**：支持OpenAI兼容的API（包括本地LLM）
- **任务测试**：一键测试任务执行效果，实时预览AI响应
- **Toast通知**：优雅的操作反馈提示

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3 + Vite + Pinia |
| 后端 | Python FastAPI + SQLAlchemy |
| 数据库 | SQLite |
| 定时任务 | APScheduler |
| 部署 | Docker + Docker Compose |

## 项目结构

```
news-get/
├── Dockerfile                    # 🚀 单容器部署（前后端合并，推荐）
├── docker-compose.yml            # Docker编排配置
├── .env.example                  # 环境变量模板
│
├── backend/                      # 后端服务
│   ├── Dockerfile                # 后端独立部署用
│   ├── app/
│   │   ├── api/                  # API路由
│   │   │   ├── auth.py           # 认证接口
│   │   │   └── tasks.py          # 任务CRUD接口
│   │   ├── core/                 # 核心模块
│   │   │   ├── config.py         # 配置管理
│   │   │   ├── database.py       # 数据库连接
│   │   │   └── security.py       # JWT认证
│   │   ├── models/               # 数据模型
│   │   ├── schemas/              # Pydantic模式
│   │   ├── services/             # 业务服务
│   │   │   ├── ai_service.py     # AI服务（OpenAI兼容）
│   │   │   ├── email_service.py  # 邮件发送服务
│   │   │   └── scheduler_service.py
│   │   └── main.py               # 应用入口
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/                     # 前端应用
│   ├── Dockerfile                # 前端独立部署用（nginx）
│   ├── nginx.conf                # Nginx配置（独立部署时使用）
│   ├── src/
│   │   ├── components/           # Vue组件
│   │   ├── composables/          # Vue组合式函数
│   │   ├── stores/               # Pinia状态管理
│   │   ├── api/                  # API调用
│   │   └── assets/               # 静态资源
│   ├── package.json
│   └── vite.config.js
│
├── start-backend.sh              # 后端启动脚本（本地开发）
└── start-frontend.sh             # 前端启动脚本（本地开发）
```

## 快速开始

### 方式一：单容器部署（推荐）⭐

使用根目录的 `Dockerfile`，前后端合并到一个容器，部署最简单。

**1. 克隆项目并配置**

```bash
git clone https://github.com/sunqb/news-get.git
cd news-get
cp .env.example .env
```

**2. 编辑 `.env` 文件**

```bash
# 端口配置
PORT=8000

# JWT密钥（生产环境必须修改）
SECRET_KEY=your-super-secret-key

# 邮件配置（必填）
SMTP_HOST=smtp.qq.com
SMTP_PORT=587
SMTP_USER=your-email@qq.com
SMTP_PASSWORD=your-smtp-password
SMTP_FROM=your-email@qq.com
SMTP_TLS=true

# AI服务配置（可选）
OPENAI_API_KEY=your-api-key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini
```

**3. 构建并启动**

```bash
docker-compose up -d --build
```

**4. 访问应用**

- 应用地址：http://localhost:8000
- API文档：http://localhost:8000/docs

**5. 常用命令**

```bash
docker-compose logs -f      # 查看日志
docker-compose ps           # 查看状态
docker-compose down         # 停止服务
docker-compose up -d --build  # 重新构建
```

---

### 方式二：双容器部署（高级）

使用 `frontend/Dockerfile` 和 `backend/Dockerfile` 分别部署，适合需要独立扩展前后端的场景。

> ⚠️ 此方式需要配置 nginx 代理，配置较复杂，一般情况推荐使用方式一。

**特点**：
- 前端使用 nginx 提供静态文件
- 后端独立运行 FastAPI
- 需要配置 nginx 反向代理 `/api` 到后端

---

### 方式三：本地开发

#### 后端

**1. 创建虚拟环境并安装依赖**

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**2. 配置环境变量**

```bash
cp .env.example .env
# 编辑 .env 填写邮件配置
```

**3. 启动后端服务**

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 前端

**1. 安装依赖**

```bash
cd frontend
npm install
```

**2. 启动开发服务器**

```bash
npm run dev
```

**3. 访问应用**

打开浏览器访问 http://localhost:5173

## API 接口

### 认证接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/auth/send-code` | 发送验证码 |
| POST | `/api/auth/verify-code` | 验证码登录 |
| GET | `/api/auth/me` | 获取当前用户信息 |

### 任务接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/tasks` | 获取任务列表 |
| POST | `/api/tasks` | 创建任务 |
| GET | `/api/tasks/{id}` | 获取任务详情 |
| PUT | `/api/tasks/{id}` | 更新任务 |
| DELETE | `/api/tasks/{id}` | 删除任务 |
| POST | `/api/tasks/{id}/toggle` | 切换任务状态 |
| POST | `/api/tasks/{id}/test` | 测试任务执行 |
| GET | `/api/tasks/{id}/executions` | 获取执行历史 |

### 请求示例

**发送验证码**

```bash
curl -X POST http://localhost:8000/api/auth/send-code \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com"}'
```

**验证码登录**

```bash
curl -X POST http://localhost:8000/api/auth/verify-code \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "code": "123456"}'
```

**创建任务**

```bash
curl -X POST http://localhost:8000/api/tasks \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "name": "每日新闻摘要",
    "frequency": "daily",
    "scheduled_time": "08:00",
    "prompt": "获取今日科技新闻摘要",
    "expert_mode": false
  }'
```

## 邮件服务配置

### QQ 邮箱

1. 登录 QQ 邮箱，进入「设置」→「账户」
2. 开启「POP3/SMTP服务」
3. 生成授权码（非登录密码）
4. 配置：
   ```
   SMTP_HOST=smtp.qq.com
   SMTP_PORT=587
   SMTP_USER=your-qq@qq.com
   SMTP_PASSWORD=授权码
   ```

### 163 邮箱

1. 登录 163 邮箱，进入「设置」→「POP3/SMTP/IMAP」
2. 开启 SMTP 服务并设置授权码
3. 配置：
   ```
   SMTP_HOST=smtp.163.com
   SMTP_PORT=587
   SMTP_USER=your-email@163.com
   SMTP_PASSWORD=授权码
   ```

### Gmail

1. 开启两步验证
2. 生成应用专用密码
3. 配置：
   ```
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=your-email@gmail.com
   SMTP_PASSWORD=应用专用密码
   ```

## 任务频率说明

| 频率 | 说明 |
|------|------|
| `once` | 一次性任务，执行后自动禁用 |
| `daily` | 每天在指定时间执行 |
| `weekly` | 每周一在指定时间执行 |
| `monthly` | 每月1日在指定时间执行 |
| `yearly` | 每年1月1日在指定时间执行 |

## 开发调试

### 调试模式

后端在 `DEBUG=true` 模式下：
- 验证码会在控制台打印（方便测试）
- 数据库操作日志会输出
- 邮件发送失败不会阻断流程

### 数据库

SQLite 数据库文件位于：
- 本地开发：`backend/app.db`
- Docker部署：`app-data` 卷中的 `data/app.db`

### 查看数据库

```bash
# 进入容器
docker exec -it news-task sh

# 使用 sqlite3 查看数据
sqlite3 /app/data/app.db
.tables
SELECT * FROM users;
SELECT * FROM tasks;
```

## AI 服务配置

系统已内置 OpenAI 兼容的 AI 服务支持。配置方式如下：

### OpenAI

```env
OPENAI_API_KEY=sk-xxxxxxxx
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini
```

### 本地 LLM（如 Ollama）

```env
OPENAI_API_KEY=ollama
OPENAI_BASE_URL=http://localhost:11434/v1/
OPENAI_MODEL=llama2
```

### 其他兼容服务（如 DeepSeek）

```env
OPENAI_API_KEY=your-deepseek-key
OPENAI_BASE_URL=https://api.deepseek.com/
OPENAI_MODEL=deepseek-chat
```

**说明**：
- AI 服务为可选配置，未配置时任务测试会返回提示信息
- 系统提示词会自动包含当前时间（北京时间）
- 支持普通模式和专家模式两种对话风格

## 扩展开发

### 接入新闻 API

```python
async def _process_task_prompt(self, prompt: str, expert_mode: bool) -> str:
    import httpx
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://newsapi.org/v2/top-headlines",
            params={"country": "cn", "apiKey": "your-api-key"}
        )
        articles = response.json()["articles"]
        # 处理并返回新闻摘要
        return "\n".join([a["title"] for a in articles[:10]])
```

## 常见问题

**Q: 验证码收不到？**
- 检查邮件配置是否正确
- 检查垃圾邮件文件夹
- 确认 SMTP 服务已开启
- 开发模式下验证码会打印在控制台

**Q: Docker 启动失败？**
- 确保 Docker 和 Docker Compose 已安装
- 检查端口是否被占用（默认8000）
- 查看日志：`docker-compose logs`

**Q: 任务没有执行？**
- 确认任务状态为启用（is_active: true）
- 检查调度时间是否正确
- 查看后端日志中的 `[Scheduler]` 信息

## License

MIT
