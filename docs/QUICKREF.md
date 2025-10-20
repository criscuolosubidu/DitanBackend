# 快速参考

## 数据库管理

### 重置数据库

**Linux/macOS:**
```bash
./scripts/manage_db.sh reset
```

**Windows:**
```powershell
.\scripts\manage_db.ps1 reset
```

### 查看数据库状态

**Linux/macOS:**
```bash
./scripts/manage_db.sh status
```

**Windows:**
```powershell
.\scripts\manage_db.ps1 status
```

### 查看数据库日志

**Linux/macOS:**
```bash
./scripts/manage_db.sh logs
```

**Windows:**
```powershell
.\scripts\manage_db.ps1 logs
```

## 部署

### 正常部署（保留数据）

**Linux/macOS:**
```bash
./scripts/deploy.sh
```

**Windows:**
```powershell
.\scripts\deploy.ps1
```

### 部署并重置数据库

**Linux/macOS:**
```bash
./scripts/deploy.sh --reset-db
```

**Windows:**
```powershell
.\scripts\deploy.ps1 -ResetDb
```

### CI/CD 部署时重置数据库

```bash
git commit -m "更新代码 [reset-db]"
git push
```

## Docker 命令

### 启动服务

```bash
docker-compose up -d
```

### 停止服务

```bash
docker-compose down
```

### 停止服务并删除数据

```bash
docker-compose down -v
```

### 查看日志

```bash
# 所有服务
docker-compose logs -f

# 应用服务
docker-compose logs -f app

# 数据库服务
docker-compose logs -f db
```

### 查看容器状态

```bash
docker-compose ps
```

### 重启服务

```bash
# 重启所有服务
docker-compose restart

# 重启应用
docker-compose restart app

# 重启数据库
docker-compose restart db
```

## 开发命令

### 安装依赖

```bash
uv sync
```

### 运行开发服务器

```bash
uv run python scripts/run_dev.py
```

### 运行测试

```bash
uv run pytest
```

### 初始化数据库

```bash
uv run python scripts/init_db.py
```

### 构建 Docker 镜像

**Linux/macOS:**
```bash
./scripts/docker_build.sh
```

**Windows:**
```powershell
.\scripts\docker_build.ps1
```

## 数据库连接

### 使用 psql 连接

```bash
docker exec -it ditan_db psql -U huanyu -d ditan
```

### 查看表

```sql
\dt
```

### 查询数据

```sql
SELECT * FROM patients;
```

### 退出 psql

```sql
\q
```

## 常用端口

- **应用**: 8000 (可配置)
- **数据库**: 5432
- **API 文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health

## 环境变量

主要环境变量（在 `.env` 文件中配置）：

```env
# 数据库配置
DATABASE_HOST=db
DATABASE_PORT=5432
DATABASE_USER=huanyu
DATABASE_PASSWORD=Huanyu2020yyds!
DATABASE_NAME=ditan

# 应用配置
APP_NAME=DitanBackend
APP_PORT=8000
APP_DEBUG=False

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
```

## 故障排查

### 应用无法启动

1. 检查容器状态：`docker-compose ps`
2. 查看日志：`docker-compose logs app`
3. 检查数据库连接：`docker-compose logs db`

### 数据库连接失败

1. 确认数据库容器运行：`docker-compose ps db`
2. 检查健康状态：`docker inspect ditan_db`
3. 查看数据库日志：`docker-compose logs db`

### 端口冲突

1. 检查端口占用：`netstat -an | grep 8000`
2. 修改 `.env` 中的 `APP_PORT`
3. 重启服务：`docker-compose restart`

### 数据丢失

1. 如果是测试环境，重置数据库：`./scripts/manage_db.sh reset`
2. 如果是生产环境，从备份恢复（如有）

## 有用的链接

- [完整文档](../README.md)
- [API 文档](API.md)
- [部署文档](DEPLOYMENT.md)
- [数据库管理文档](DATABASE.md)

