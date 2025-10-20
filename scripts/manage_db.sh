#!/bin/bash

# 数据库管理脚本

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 显示帮助信息
show_help() {
    echo -e "${BLUE}数据库管理脚本${NC}"
    echo ""
    echo "用法: ./scripts/manage_db.sh [命令]"
    echo ""
    echo "命令:"
    echo "  reset        重置数据库（删除volume并重启数据库容器）"
    echo "  restart      重启数据库容器"
    echo "  logs         查看数据库日志"
    echo "  status       查看数据库状态"
    echo "  backup       备份数据库（TODO）"
    echo "  help         显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  ./scripts/manage_db.sh reset      # 重置数据库"
    echo "  ./scripts/manage_db.sh logs       # 查看数据库日志"
}

# 重置数据库
reset_db() {
    echo -e "${YELLOW}⚠️  警告: 这将删除所有数据库数据！${NC}"
    read -p "确认继续？ (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${BLUE}操作已取消${NC}"
        exit 0
    fi
    
    echo -e "${YELLOW}🛑 停止数据库容器...${NC}"
    docker-compose stop db
    
    echo -e "${YELLOW}🗑️  删除数据库volume...${NC}"
    docker volume rm ditan_postgres_data || echo -e "${YELLOW}⚠️  Volume 不存在或无法删除${NC}"
    
    echo -e "${YELLOW}🚀 启动数据库容器...${NC}"
    docker-compose up -d db
    
    echo -e "${YELLOW}⏳ 等待数据库就绪...${NC}"
    sleep 10
    
    echo -e "${YELLOW}🔧 初始化数据库表...${NC}"
    docker-compose exec app uv run python scripts/init_db.py || echo -e "${YELLOW}⚠️  应用未运行或初始化脚本失败${NC}"
    
    echo -e "${GREEN}✅ 数据库重置完成！${NC}"
}

# 重启数据库
restart_db() {
    echo -e "${YELLOW}🔄 重启数据库容器...${NC}"
    docker-compose restart db
    echo -e "${GREEN}✅ 数据库已重启${NC}"
}

# 查看日志
show_logs() {
    echo -e "${BLUE}📋 数据库日志:${NC}"
    docker-compose logs -f db
}

# 查看状态
show_status() {
    echo -e "${BLUE}📊 数据库状态:${NC}"
    docker-compose ps db
    echo ""
    echo -e "${BLUE}🗄️  Volume 信息:${NC}"
    docker volume inspect ditan_postgres_data 2>/dev/null || echo -e "${YELLOW}⚠️  Volume 不存在${NC}"
}

# 解析命令
case "$1" in
    reset)
        reset_db
        ;;
    restart)
        restart_db
        ;;
    logs)
        show_logs
        ;;
    status)
        show_status
        ;;
    backup)
        echo -e "${YELLOW}⚠️  备份功能待实现${NC}"
        ;;
    help|--help|-h|"")
        show_help
        ;;
    *)
        echo -e "${RED}错误: 未知命令 '$1'${NC}"
        echo ""
        show_help
        exit 1
        ;;
esac

