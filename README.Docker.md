# Docker 部署指南

本文档介绍如何使用 Docker 快速构建和部署 DitanBackend 服务。

## 目录

- [快速开始](#快速开始)
- [环境准备](#环境准备)
- [使用脚本](#使用脚本)
- [手动操作](#手动操作)
- [配置说明](#配置说明)
- [常见问题](#常见问题)

---

## 快速开始

### Windows 用户

```powershell
# 1. 初始化环境
.\scripts\docker_build.ps1 init

# 2. 修改 .env 文件中的数据库密码

# 3. 启动服务
.\scripts\docker_build.ps1 up

# 4. 查看日志
.\scripts\docker_build.ps1 logs -f
```

### Linux/macOS 用户

```bash
# 1. 给脚本添加执行权限
chmod +x scripts/docker_build.sh

# 2. 初始化环境
./scripts/docker_build.sh init

# 3. 修改 .env 文件中的数据库密码

# 4. 启动服务
./scripts/docker_build.sh up

# 5. 查看日志
./scripts/docker_build.sh logs -f
```

---

## 环境准备

### 安装 Docker

**Windows:**

- 下载并安装 [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop)

**Linux (Ubuntu/Debian):**

```bash
# 安装 Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 安装 Docker Compose
sudo apt-get update
sudo apt-get install docker-compose-plugin

# 将当前用户添加到 docker 组
sudo usermod -aG docker $USER
```

**macOS:**

- 下载并安装 [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop)

### 验证安装

```bash
docker --version
docker-compose --version
```

---

## 使用脚本

我们提供了两个脚本来简化 Docker 操作：

- **Windows**: `scripts\docker_build.ps1`
- **Linux/macOS**: `scripts/docker_build.sh`

### 可用命令

| 命令        | 说明                     |
|-----------|------------------------|
| `init`    | 初始化环境（创建 .env 文件和日志目录） |
| `build`   | 构建 Docker 镜像           |
| `up`      | 启动服务（后台运行）             |
| `down`    | 停止服务                   |
| `restart` | 重启服务                   |
| `logs`    | 查看日志（加 `-f` 参数实时跟踪）    |
| `ps`      | 查看服务运行状态               |
| `dev`     | 启动开发环境（支持热重载）          |
| `prod`    | 启动生产环境                 |
| `clean`   | 清理所有容器、镜像和数据卷          |
| `help`    | 显示帮助信息                 |

### 使用示例

**Windows:**

```powershell
# 查看帮助
.\scripts\docker_build.ps1 help

# 构建镜像
.\scripts\docker_build.ps1 build

# 启动服务
.\scripts\docker_build.ps1 up

# 查看日志（实时）
.\scripts\docker_build.ps1 logs -f

# 查看状态
.\scripts\docker_build.ps1 ps

# 停止服务
.\scripts\docker_build.ps1 down
```

**Linux/macOS:**

```bash
# 查看帮助
./scripts/docker_build.sh help

# 构建镜像
./scripts/docker_build.sh build

# 启动服务
./scripts/docker_build.sh up

# 查看日志（实时）
./scripts/docker_build.sh logs -f

# 查看状态
./scripts/docker_build.sh ps

# 停止服务
./scripts/docker_build.sh down
```

---

## 手动操作

如果不使用脚本，也可以直接使用 `docker-compose` 命令：

### 生产环境

```bash
# 构建并启动
docker-compose up -d --build

# 停止
docker-compose down

# 查看日志
docker-compose logs -f

# 查看状态
docker-compose ps

# 重启
docker-compose restart

# 重新构建某个服务
docker-compose build app
docker-compose up -d app
```

### 开发环境

```bash
# 启动开发环境（支持热重载）
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build

# 停止
docker-compose -f docker-compose.yml -f docker-compose.dev.yml down
```

---

## 配置说明

### 环境变量

在 `.env` 文件中配置以下环境变量：

```env
# 数据库配置
DATABASE_HOST=localhost          # Docker 环境中会自动设为 db
DATABASE_PORT=5432
DATABASE_USER=postgres
DATABASE_PASSWORD=changeme123    # 请修改为强密码
DATABASE_NAME=ditan_db

# 应用配置
APP_NAME=DitanBackend
APP_VERSION=0.2.0
APP_HOST=0.0.0.0
APP_PORT=8000
APP_DEBUG=False

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
```

### 端口映射

- **应用服务**: http://localhost:8000
- **数据库服务**: localhost:5432
- **API 文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health

### 数据持久化

PostgreSQL 数据存储在 Docker 卷 `ditan_postgres_data` 中，即使删除容器数据也不会丢失。

如需清空数据：

```bash
docker-compose down -v
```

---

## 常见问题

### 1. 端口被占用

**错误信息**: `Bind for 0.0.0.0:8000 failed: port is already allocated`

**解决方案**:

- 修改 `.env` 文件中的 `APP_PORT`
- 或停止占用端口的程序

### 2. 数据库连接失败

**错误信息**: `could not connect to server`

**解决方案**:

- 检查数据库容器是否正常运行：`docker-compose ps`
- 查看数据库日志：`docker-compose logs db`
- 确保应用在数据库启动后才启动（已配置 `depends_on`）

### 3. 镜像构建失败

**解决方案**:

```bash
# 清理构建缓存
docker system prune -a

# 重新构建
docker-compose build --no-cache
```

### 4. 查看容器内部

```bash
# 进入应用容器
docker-compose exec app bash

# 进入数据库容器
docker-compose exec db psql -U postgres -d ditan_db
```

### 5. 更新代码后重新部署

```bash
# 重新构建并启动
docker-compose up -d --build

# 或使用脚本
./scripts/docker_build.sh up --build
```

### 6. 查看资源使用情况

```bash
# 查看容器资源使用
docker stats

# 查看 Docker 磁盘使用
docker system df
```

### 7. 完全清理环境

```bash
# 停止并删除容器、网络、卷
docker-compose down -v

# 删除镜像
docker-compose down --rmi all

# 或使用脚本（会提示确认）
./scripts/docker_build.sh clean
```

---

## 开发环境 vs 生产环境

### 开发环境特点

- 启用调试模式（`APP_DEBUG=True`）
- 日志级别为 DEBUG
- 挂载代码目录，支持热重载
- 单个 worker 进程

```bash
# 启动开发环境
./scripts/docker_build.sh dev
```

### 生产环境特点

- 关闭调试模式（`APP_DEBUG=False`）
- 日志级别为 INFO
- 不挂载代码，使用镜像内代码
- 多个 worker 进程（4个）
- 配置健康检查

```bash
# 启动生产环境
./scripts/docker_build.sh prod
```

---

## 监控和维护

### 健康检查

```bash
# 检查服务健康状态
curl http://localhost:8000/health

# 查看 Docker 健康检查状态
docker-compose ps
```

### 日志管理

```bash
# 查看最近 100 行日志
docker-compose logs --tail=100

# 实时跟踪日志
docker-compose logs -f

# 只查看应用日志
docker-compose logs app

# 只查看数据库日志
docker-compose logs db
```

### 数据库备份

```bash
# 备份数据库
docker-compose exec db pg_dump -U postgres ditan_db > backup_$(date +%Y%m%d).sql

# 恢复数据库
docker-compose exec -T db psql -U postgres ditan_db < backup_20241016.sql
```

---

## 性能优化

### 调整 Worker 数量

编辑 `Dockerfile` 中的启动命令：

```dockerfile
# 根据 CPU 核心数调整 workers 数量
# 建议: workers = 2 * CPU_CORES + 1
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

### 数据库连接池

应用已配置数据库连接池，默认设置在 `app/core/database.py` 中。

### 内存限制

在 `docker-compose.yml` 中添加资源限制：

```yaml
services:
  app:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
```

---

## 更多信息

- [完整部署文档](docs/DEPLOYMENT.md)
- [API 文档](docs/API.md)
- [项目 README](README.md)

