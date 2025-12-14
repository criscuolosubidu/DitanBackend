# 部署文档

## 目录

1. [环境要求](#环境要求)
2. [安装步骤](#安装步骤)
3. [配置说明](#配置说明)
4. [数据库设置](#数据库设置)
5. [运行服务](#运行服务)
6. [测试](#测试)
7. [生产环境部署](#生产环境部署)
8. [故障排查](#故障排查)

---

## 环境要求

### 基础环境

- **Python**: 3.11 或更高版本
- **PostgreSQL**: 12 或更高版本
- **uv**: Python 包管理工具

### 安装 Python 3.11+

**Windows**:

```bash
# 从 Python 官网下载并安装
# https://www.python.org/downloads/
```

**Linux (Ubuntu/Debian)**:

```bash
sudo apt update
sudo apt install python3.11 python3.11-dev python3.11-venv
```

**macOS**:

```bash
brew install python@3.11
```

### 安装 uv

```bash
# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Linux/macOS
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 安装 PostgreSQL

**Windows**:

- 从官网下载安装程序: https://www.postgresql.org/download/windows/

**Linux (Ubuntu/Debian)**:

```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

**macOS**:

```bash
brew install postgresql@14
brew services start postgresql@14
```

---

## 安装步骤

### 1. 克隆项目（或获取项目文件）

```bash
cd /path/to/your/project
cd DitanBackend
```

### 2. 安装依赖

使用 uv 安装项目依赖：

```bash
# 安装所有依赖
uv sync

# 如果需要安装开发依赖（用于测试）
uv sync --extra dev
```

---

## 配置说明

### 1. 创建 .env 文件

在项目根目录创建 `.env` 文件：

```bash
# Windows
copy .env.example .env

# Linux/macOS
cp .env.example .env
```

### 2. 编辑 .env 文件

打开 `.env` 文件并根据实际情况修改配置：

```env
# 数据库配置
DATABASE_HOST=localhost          # 数据库主机地址
DATABASE_PORT=5432              # 数据库端口
DATABASE_USER=postgres          # 数据库用户名
DATABASE_PASSWORD=your_password # 数据库密码（请修改）
DATABASE_NAME=ditan_db          # 数据库名称

# 应用配置
APP_NAME=DitanBackend
APP_VERSION=0.1.0
APP_HOST=0.0.0.0               # 监听地址（0.0.0.0 表示所有网卡）
APP_PORT=8000                   # 服务端口
APP_DEBUG=False                 # 生产环境设为 False

# 日志配置
LOG_LEVEL=INFO                  # 日志级别: DEBUG, INFO, WARNING, ERROR
LOG_FILE=logs/app.log           # 日志文件路径
```

### 配置项说明

| 配置项                 | 说明      | 默认值           | 备注                       |
|---------------------|---------|---------------|--------------------------|
| `DATABASE_HOST`     | 数据库主机地址 | localhost     | 生产环境可能是其他地址              |
| `DATABASE_PORT`     | 数据库端口   | 5432          | PostgreSQL 默认端口          |
| `DATABASE_USER`     | 数据库用户名  | postgres      | 根据实际情况修改                 |
| `DATABASE_PASSWORD` | 数据库密码   | your_password | **必须修改**                 |
| `DATABASE_NAME`     | 数据库名称   | ditan_db      | 可自定义                     |
| `APP_HOST`          | 服务监听地址  | 0.0.0.0       | 本地开发可用 127.0.0.1         |
| `APP_PORT`          | 服务端口    | 8000          | 可自定义                     |
| `APP_DEBUG`         | 调试模式    | False         | 生产环境务必设为 False           |
| `LOG_LEVEL`         | 日志级别    | INFO          | DEBUG/INFO/WARNING/ERROR |

---

## 数据库设置

### 1. 创建数据库

登录 PostgreSQL 并创建数据库：

```bash
# Linux/macOS
sudo -u postgres psql

# Windows (以管理员身份运行 psql)
psql -U postgres
```

在 PostgreSQL 命令行中执行：

```sql
-- 创建数据库
CREATE DATABASE ditan_db;

-- 创建用户（如果需要）
CREATE USER ditan_user WITH PASSWORD 'your_secure_password';

-- 授予权限
GRANT ALL PRIVILEGES ON DATABASE ditan_db TO ditan_user;

-- 退出
\q
```

### 2. 初始化数据库表

运行数据库初始化脚本：

```bash
# 使用 uv 运行脚本
uv run python scripts/init_db.py
```

或者启动服务时会自动初始化：

```bash
uv run python main.py
```

---

## 运行服务

### 开发环境

使用开发脚本启动（支持热重载）：

```bash
uv run python scripts/run_dev.py
```

或者直接运行：

```bash
uv run python main.py
```

### 访问服务

服务启动后，可以访问：

- **主页**: http://localhost:8000/
- **健康检查**: http://localhost:8000/health
- **API 文档 (Swagger)**: http://localhost:8000/docs
- **API 文档 (ReDoc)**: http://localhost:8000/redoc

---

## 测试

### 运行单元测试

```bash
# 使用 uv 运行测试
uv run pytest

# 或使用测试脚本
uv run python scripts/run_tests.py

# 查看详细输出
uv run pytest -v

# 查看测试覆盖率
uv run pytest --cov=app --cov-report=html
```

### 手动测试 API

使用 curl 测试：

```bash
# 健康检查
curl http://localhost:8000/health

# 创建患者数据
curl -X POST "http://localhost:8000/api/v1/patient" \
  -H "Content-Type: application/json" \
  -d '{
    "uuid": "550e8400-e29b-41d4-a716-446655440000",
    "phone": "13800138001",
    "name": "测试用户"
  }'
```

---

## 生产环境部署

### 方式一：使用 Uvicorn 直接部署

```bash
# 使用多个工作进程
uv run uvicorn main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4 \
  --log-level info
```

### 方式二：使用 Gunicorn + Uvicorn Workers

安装 Gunicorn：

```bash
uv add gunicorn
```

启动服务：

```bash
uv run gunicorn main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --log-level info \
  --access-logfile logs/access.log \
  --error-logfile logs/error.log
```

### 方式三：使用 Systemd 服务（Linux）

创建服务文件 `/etc/systemd/system/ditanbackend.service`：

```ini
[Unit]
Description=DitanBackend Patient Data Upload Service
After=network.target postgresql.service

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/path/to/DitanBackend
Environment="PATH=/path/to/DitanBackend/.venv/bin"
ExecStart=/path/to/.local/bin/uv run uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启动服务：

```bash
sudo systemctl daemon-reload
sudo systemctl start ditanbackend
sudo systemctl enable ditanbackend
sudo systemctl status ditanbackend
```

### 方式四：使用 Docker

创建 `Dockerfile`：

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装 uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# 复制项目文件
COPY . .

# 安装依赖
RUN uv sync --frozen

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

创建 `docker-compose.yml`：

```yaml
version: '3.8'

services:
  db:
    image: postgres:14
    environment:
      POSTGRES_DB: ditan_db
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: your_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      DATABASE_HOST: db
      DATABASE_PORT: 5432
      DATABASE_USER: postgres
      DATABASE_PASSWORD: your_password
      DATABASE_NAME: ditan_db
    depends_on:
      - db
    volumes:
      - ./logs:/app/logs

volumes:
  postgres_data:
```

运行：

```bash
docker-compose up -d
```

### 使用 Nginx 反向代理

安装 Nginx：

```bash
# Ubuntu/Debian
sudo apt install nginx

# CentOS/RHEL
sudo yum install nginx
```

配置文件 `/etc/nginx/sites-available/ditanbackend`：

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 日志
    access_log /var/log/nginx/ditanbackend_access.log;
    error_log /var/log/nginx/ditanbackend_error.log;
}
```

启用配置：

```bash
sudo ln -s /etc/nginx/sites-available/ditanbackend /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## 故障排查

### 数据库连接失败

**错误信息**: `could not connect to server`

**解决方案**:

1. 检查 PostgreSQL 是否运行：`sudo systemctl status postgresql`
2. 检查 `.env` 文件中的数据库配置是否正确
3. 检查防火墙设置
4. 检查 PostgreSQL 的 `pg_hba.conf` 配置

### 端口被占用

**错误信息**: `Address already in use`

**解决方案**:

```bash
# 查找占用端口的进程
# Linux/macOS
lsof -i :8000

# Windows
netstat -ano | findstr :8000

# 修改 .env 中的 APP_PORT 为其他端口
```

### 日志文件权限错误

**错误信息**: `Permission denied: 'logs/app.log'`

**解决方案**:

```bash
# 创建日志目录并设置权限
mkdir -p logs
chmod 755 logs
```

### 依赖安装失败

**解决方案**:

```bash
# 清理并重新安装
rm -rf .venv uv.lock
uv sync
```

### 查看日志

```bash
# 查看应用日志
tail -f logs/app.log

# 查看 systemd 日志
sudo journalctl -u ditanbackend -f

# 查看 Nginx 日志
tail -f /var/log/nginx/ditanbackend_error.log
```

---

## 维护建议

1. **定期备份数据库**
   ```bash
   pg_dump -U postgres ditan_db > backup_$(date +%Y%m%d).sql
   ```

2. **监控日志文件大小**
    - 配置日志轮转（logrotate）
    - 定期清理旧日志

3. **更新依赖**
   ```bash
   uv sync --upgrade
   ```

4. **安全建议**
    - 使用强密码
    - 启用防火墙
    - 使用 HTTPS（配置 SSL 证书）
    - 定期更新系统和依赖包
    - 不要在生产环境启用 DEBUG 模式

5. **性能优化**
    - 根据服务器配置调整 worker 数量
    - 配置数据库连接池
    - 使用 CDN 和缓存
    - 监控服务器资源使用情况

---

## 联系支持

如有问题，请查看：

- API 文档: [docs/API.md](./API.md)
- 项目 README: [README.md](../README.md)

