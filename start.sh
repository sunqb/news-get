#!/bin/bash

# News Task Manager 一键启动脚本
# 用于本地开发或服务器真机部署

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"

# PID 文件
BACKEND_PID_FILE="$PROJECT_DIR/.backend.pid"
FRONTEND_PID_FILE="$PROJECT_DIR/.frontend.pid"

print_banner() {
    echo -e "${GREEN}"
    echo "╔═══════════════════════════════════════╗"
    echo "║     News Task Manager 启动脚本        ║"
    echo "╚═══════════════════════════════════════╝"
    echo -e "${NC}"
}

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查命令是否存在
check_command() {
    if ! command -v $1 &> /dev/null; then
        log_error "$1 未安装，请先安装"
        exit 1
    fi
}

# 启动后端
start_backend() {
    log_info "启动后端服务..."
    cd "$BACKEND_DIR"

    # 创建虚拟环境（如果不存在）
    if [ ! -d "venv" ]; then
        log_info "创建 Python 虚拟环境..."
        python3 -m venv venv
    fi

    # 激活虚拟环境并安装依赖
    source venv/bin/activate
    log_info "安装后端依赖..."
    pip install -q -r requirements.txt

    # 创建 .env 文件（如果不存在）
    if [ ! -f ".env" ]; then
        log_warn ".env 文件不存在，从模板创建..."
        cp .env.example .env
        log_warn "请编辑 backend/.env 配置邮件服务"
    fi

    # 启动服务
    log_info "启动 FastAPI 服务 (端口 8000)..."
    nohup fastapi run app/main.py --port 8000 > "$PROJECT_DIR/backend.log" 2>&1 &
    echo $! > "$BACKEND_PID_FILE"

    deactivate
    cd "$PROJECT_DIR"
}

# 启动前端
start_frontend() {
    log_info "启动前端服务..."
    cd "$FRONTEND_DIR"

    # 安装依赖
    if [ ! -d "node_modules" ]; then
        log_info "安装前端依赖..."
        npm install
    fi

    # 启动服务
    log_info "启动 Vite 开发服务器 (端口 5173)..."
    nohup npm run dev > "$PROJECT_DIR/frontend.log" 2>&1 &
    echo $! > "$FRONTEND_PID_FILE"

    cd "$PROJECT_DIR"
}

# 停止服务
stop_services() {
    log_info "停止所有服务..."

    if [ -f "$BACKEND_PID_FILE" ]; then
        PID=$(cat "$BACKEND_PID_FILE")
        if kill -0 $PID 2>/dev/null; then
            kill $PID
            log_info "后端服务已停止 (PID: $PID)"
        fi
        rm -f "$BACKEND_PID_FILE"
    fi

    if [ -f "$FRONTEND_PID_FILE" ]; then
        PID=$(cat "$FRONTEND_PID_FILE")
        if kill -0 $PID 2>/dev/null; then
            kill $PID
            log_info "前端服务已停止 (PID: $PID)"
        fi
        rm -f "$FRONTEND_PID_FILE"
    fi

    # 清理可能残留的进程
    pkill -f "fastapi run app/main.py" 2>/dev/null || true
    pkill -f "vite" 2>/dev/null || true

    log_info "所有服务已停止"
}

# 查看状态
status() {
    echo ""
    echo "服务状态:"
    echo "─────────────────────────────────"

    if [ -f "$BACKEND_PID_FILE" ] && kill -0 $(cat "$BACKEND_PID_FILE") 2>/dev/null; then
        echo -e "后端服务: ${GREEN}运行中${NC} (PID: $(cat $BACKEND_PID_FILE))"
    else
        echo -e "后端服务: ${RED}未运行${NC}"
    fi

    if [ -f "$FRONTEND_PID_FILE" ] && kill -0 $(cat "$FRONTEND_PID_FILE") 2>/dev/null; then
        echo -e "前端服务: ${GREEN}运行中${NC} (PID: $(cat $FRONTEND_PID_FILE))"
    else
        echo -e "前端服务: ${RED}未运行${NC}"
    fi

    echo "─────────────────────────────────"
    echo ""
}

# 查看日志
logs() {
    case "$1" in
        backend)
            tail -f "$PROJECT_DIR/backend.log"
            ;;
        frontend)
            tail -f "$PROJECT_DIR/frontend.log"
            ;;
        *)
            tail -f "$PROJECT_DIR/backend.log" "$PROJECT_DIR/frontend.log"
            ;;
    esac
}

# 主函数
main() {
    print_banner

    case "$1" in
        start)
            check_command python3
            check_command node
            check_command npm
            stop_services
            start_backend
            start_frontend
            sleep 2
            status
            echo "访问地址:"
            echo "  前端: http://localhost:5173"
            echo "  后端: http://localhost:8000"
            echo "  文档: http://localhost:8000/docs"
            echo ""
            echo "查看日志: $0 logs"
            echo "停止服务: $0 stop"
            ;;
        stop)
            stop_services
            ;;
        restart)
            stop_services
            sleep 1
            start_backend
            start_frontend
            sleep 2
            status
            ;;
        status)
            status
            ;;
        logs)
            logs "$2"
            ;;
        *)
            echo "用法: $0 {start|stop|restart|status|logs [backend|frontend]}"
            echo ""
            echo "命令:"
            echo "  start    启动所有服务"
            echo "  stop     停止所有服务"
            echo "  restart  重启所有服务"
            echo "  status   查看服务状态"
            echo "  logs     查看日志 (可选: backend/frontend)"
            exit 1
            ;;
    esac
}

main "$@"
