#!/bin/bash

# 部署脚本 - 用于手动部署和管理数据库

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 显示帮助信息
show_help() {
    echo "用法: ./scripts/deploy.sh [选项]"
    echo ""
    echo "选项:"
    echo "  --reset-db       重置数据库（删除所有数据并重建）"
    echo "  --keep-db        保留数据库数据（默认）"
    echo "  --help           显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  ./scripts/deploy.sh                # 正常部署，保留数据库"
    echo "  ./scripts/deploy.sh --reset-db     # 部署并重置数据库"
}

# 默认不重置数据库
RESET_DB=false

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --reset-db)
            RESET_DB=true
            shift
            ;;
        --keep-db)
            RESET_DB=false
            shift
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            echo -e "${RED}错误: 未知选项 $1${NC}"
            show_help
            exit 1
            ;;
    esac
done

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   Ditan Backend 部署脚本${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# 停止容器
echo -e "${YELLOW}🛑 停止旧容器...${NC}"
if [ "$RESET_DB" = true ]; then
    echo -e "${YELLOW}🗑️  删除数据库volume...${NC}"
    docker-compose down -v
else
    echo -e "${YELLOW}💾 保留数据库数据...${NC}"
    docker-compose down
fi

# 拉取最新镜像
echo -e "${YELLOW}⬇️  拉取最新镜像...${NC}"
docker-compose pull

# 启动容器
echo -e "${YELLOW}🚀 启动新容器...${NC}"
docker-compose up -d

# 等待服务启动
echo -e "${YELLOW}⏳ 等待服务启动...${NC}"
sleep 15

# 检查容器状态
echo -e "${YELLOW}📊 检查容器状态...${NC}"
docker-compose ps

# 健康检查
echo -e "${YELLOW}🏥 检查应用健康状态...${NC}"
APP_PORT=${APP_PORT:-8000}
for i in {1..5}; do
    if curl -f http://localhost:${APP_PORT}/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ 应用健康检查通过${NC}"
        echo ""
        echo -e "${GREEN}========================================${NC}"
        echo -e "${GREEN}🎉 部署成功！${NC}"
        echo -e "${GREEN}🔗 应用地址: http://localhost:${APP_PORT}${NC}"
        echo -e "${GREEN}========================================${NC}"
        exit 0
    fi
    echo -e "${YELLOW}⏳ 等待应用就绪... ($i/5)${NC}"
    sleep 5
done

echo -e "${RED}⚠️  健康检查未通过，请查看日志:${NC}"
docker-compose logs --tail=50 app
exit 1

