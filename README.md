# DitanBackend - 病人数据上传后端服务

一个基于 FastAPI 构建的病人数据上传后端服务，用于接收和存储患者的基本信息及四诊分析结果。

## 特性

- ✅ 基于 FastAPI 构建，性能优异
- ✅ 使用 SQLAlchemy ORM 操作 PostgreSQL 数据库
- ✅ 完整的请求/响应验证（Pydantic）
- ✅ 自定义异常处理，友好的错误提示
- ✅ 完善的日志记录（请求、响应、错误）
- ✅ 环境配置管理（.env）
- ✅ 使用 uv 进行依赖管理
- ✅ 完整的单元测试
- ✅ 交互式 API 文档（Swagger UI / ReDoc）

## 技术栈

- **Web 框架**: FastAPI 0.115+
- **数据库**: PostgreSQL
- **ORM**: SQLAlchemy 2.0+（异步）
- **数据验证**: Pydantic 2.9+
- **日志**: Python logging
- **包管理**: uv
- **测试**: pytest + httpx

## 项目结构

```
DitanBackend/
├── app/
│   ├── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── patient.py          # 患者 API 路由
│   │   └── router.py            # 路由汇总
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py            # 配置管理
│   │   ├── database.py          # 数据库连接
│   │   ├── exceptions.py        # 自定义异常
│   │   └── logging.py           # 日志配置
│   ├── models/
│   │   ├── __init__.py
│   │   └── patient.py           # 患者数据模型
│   └── schemas/
│       ├── __init__.py
│       └── patient.py           # Pydantic 模型
├── docs/
│   ├── API.md                   # API 文档
│   └── DEPLOYMENT.md            # 部署文档
├── logs/                        # 日志目录
├── scripts/
│   ├── cicd_workflow.yml       # CI/CD 工作流配置
│   ├── deploy.sh               # Linux/macOS 部署脚本
│   ├── deploy.ps1              # Windows 部署脚本
│   ├── docker_build.sh         # Docker 构建脚本
│   ├── init_db.py              # 数据库初始化脚本
│   ├── manage_db.sh            # Linux/macOS 数据库管理脚本
│   ├── manage_db.ps1           # Windows 数据库管理脚本
│   ├── run_dev.py              # 开发环境启动脚本
│   └── run_tests.py            # 测试运行脚本
├── tests/
│   ├── __init__.py
│   ├── conftest.py             # 测试配置
│   └── test_patient.py         # 患者 API 测试
├── .env                         # 环境配置（需创建）
├── .env.example                 # 环境配置示例
├── .gitignore
├── main.py                      # 应用入口
├── pyproject.toml              # 项目配置
├── pytest.ini                  # pytest 配置
└── README.md                   # 项目说明
```

## 快速开始

### 1. 环境要求

- Python 3.11+
- PostgreSQL 12+
- uv（Python 包管理工具）

### 2. 安装 uv

```bash
# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Linux/macOS
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 3. 克隆项目并安装依赖

```bash
cd DitanBackend

# 安装依赖
uv sync

# 安装开发依赖（包含测试工具）
uv sync --extra dev
```

### 4. 配置环境变量

创建 `.env` 文件：

```bash
# Windows
copy .env.example .env

# Linux/macOS
cp .env.example .env
```

编辑 `.env` 文件，配置数据库连接：

```env
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_USER=postgres
DATABASE_PASSWORD=your_password
DATABASE_NAME=ditan_db

APP_HOST=0.0.0.0
APP_PORT=8000
APP_DEBUG=True

LOG_LEVEL=INFO
LOG_FILE=logs/app.log
```

### 5. 初始化数据库

确保 PostgreSQL 已运行，并创建数据库：

```sql
CREATE DATABASE ditan_db;
```

运行初始化脚本：

```bash
uv run python scripts/init_db.py
```

### 6. 启动服务

```bash
# 开发模式（支持热重载）
uv run python scripts/run_dev.py

# 或直接运行
uv run python main.py
```

服务启动后访问：

- **主页**: http://localhost:8000/
- **健康检查**: http://localhost:8000/health
- **API 文档**: http://localhost:8000/docs
- **ReDoc 文档**: http://localhost:8000/redoc

## API 使用示例

### 创建患者数据

```bash
curl -X POST "http://localhost:8000/api/v1/patient" \
  -H "Content-Type: application/json" \
  -d '{
    "uuid": "550e8400-e29b-41d4-a716-446655440000",
    "phone": "13800138001",
    "name": "张三",
    "sex": "男",
    "birthday": "1985-05-20",
    "height": "175",
    "weight": "70",
    "analysisResults": {
      "face": "面色略黄，唇色偏淡，有轻微黑眼圈。",
      "tongueFront": "舌体偏胖，舌苔薄白，边有齿痕。",
      "tongueBottom": "舌下络脉颜色正常，无明显瘀滞。",
      "pulse": "脉象沉细，左手关脉较弱。"
    },
    "cozeConversationLog": "USER: 你好\nAI: 你好，请问有什么可以帮您？"
  }'
```

### 响应示例

```json
{
  "success": true,
  "message": "患者数据上传成功",
  "data": {
    "uuid": "550e8400-e29b-41d4-a716-446655440000",
    "phone": "13800138001",
    "name": "张三",
    "sex": "男",
    "birthday": "1985-05-20",
    "height": "175",
    "weight": "70",
    "analysis_face": "面色略黄，唇色偏淡，有轻微黑眼圈。",
    "analysis_tongue_front": "舌体偏胖，舌苔薄白，边有齿痕。",
    "analysis_tongue_bottom": "舌下络脉颜色正常，无明显瘀滞。",
    "analysis_pulse": "脉象沉细，左手关脉较弱。",
    "coze_conversation_log": "USER: 你好\nAI: 你好，请问有什么可以帮您？",
    "created_at": "2024-01-15T10:30:00",
    "updated_at": "2024-01-15T10:30:00"
  }
}
```

## 运行测试

```bash
# 运行所有测试
uv run pytest

# 使用测试脚本
uv run python scripts/run_tests.py

# 查看详细输出
uv run pytest -v

# 生成覆盖率报告
uv run pytest --cov=app --cov-report=html
```

## 数据库管理

### 重置数据库（清空所有数据）

当数据库结构变更或需要清空测试数据时，可以使用以下脚本：

**Linux/macOS:**
```bash
# 查看帮助
./scripts/manage_db.sh help

# 重置数据库（会提示确认）
./scripts/manage_db.sh reset

# 重启数据库
./scripts/manage_db.sh restart

# 查看数据库状态
./scripts/manage_db.sh status

# 查看数据库日志
./scripts/manage_db.sh logs
```

**Windows:**
```powershell
# 查看帮助
.\scripts\manage_db.ps1 help

# 重置数据库（会提示确认）
.\scripts\manage_db.ps1 reset

# 重启数据库
.\scripts\manage_db.ps1 restart

# 查看数据库状态
.\scripts\manage_db.ps1 status

# 查看数据库日志
.\scripts\manage_db.ps1 logs
```

### 部署时重置数据库

在 CI/CD 自动部署时，如果需要重置数据库，可以在 commit message 中添加 `[reset-db]` 标记：

```bash
git commit -m "更新数据库模型 [reset-db]"
git push
```

这样部署时会自动删除数据库 volume 并重建数据库。

### 手动部署脚本

**Linux/macOS:**
```bash
# 保留数据库数据（默认）
./scripts/deploy.sh

# 重置数据库并部署
./scripts/deploy.sh --reset-db
```

**Windows:**
```powershell
# 保留数据库数据（默认）
.\scripts\deploy.ps1

# 重置数据库并部署
.\scripts\deploy.ps1 -ResetDb
```

## 数据验证规则

### 必填字段

- `uuid`: UUID v4 格式（例如：`550e8400-e29b-41d4-a716-446655440000`）
- `phone`: 11位手机号，以1开头（例如：`13800138001`）

### 可选字段

- `name`: 患者姓名
- `sex`: 性别（"男" 或 "女"）
- `birthday`: 出生日期（格式：YYYY-MM-DD）
- `height`: 身高（cm）
- `weight`: 体重（kg）
- `analysisResults`: 四诊分析结果对象
  - `face`: 面诊结果
  - `tongueFront`: 舌诊（正面）结果
  - `tongueBottom`: 舌诊（舌下）结果
  - `pulse`: 脉诊结果
- `cozeConversationLog`: 对话记录

## 文档

- [API 文档](docs/API.md) - 详细的 API 接口说明
- [部署文档](docs/DEPLOYMENT.md) - 完整的部署指南
- [数据库管理文档](docs/DATABASE.md) - 数据库管理和维护指南

## 日志

所有请求、响应和错误都会记录到日志文件中：

- 日志文件位置: `logs/app.log`
- 日志级别: INFO（可在 .env 中配置）
- 日志包含: 请求参数、响应数据、错误信息

## 异常处理

服务使用自定义异常，不会暴露详细的堆栈跟踪（除非在 DEBUG 模式）：

- `ValidationException` (400) - 请求参数验证失败
- `NotFoundException` (404) - 资源未找到
- `DuplicateException` (409) - 数据重复（如 UUID 已存在）
- `DatabaseException` (500) - 数据库操作失败
- `InternalServerException` (500) - 服务器内部错误

## 生产环境部署

### 使用 Uvicorn

```bash
uv run uvicorn main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4 \
  --log-level info
```

### 使用 Docker

```bash
docker-compose up -d
```

更多部署选项请参考 [部署文档](docs/DEPLOYMENT.md)。

## 开发指南

### 添加新的 API 端点

1. 在 `app/models/` 中创建数据模型
2. 在 `app/schemas/` 中创建 Pydantic 模型
3. 在 `app/api/` 中创建路由文件
4. 在 `app/api/router.py` 中注册路由
5. 在 `tests/` 中添加测试

### 代码规范

- 使用类型注解
- 遵循 PEP 8 代码风格
- 编写清晰的文档字符串
- 保持高内聚低耦合
- 不过度使用设计模式

## 许可证

本项目仅供学习和研究使用。

## 贡献

欢迎提交 Issue 和 Pull Request！

## 联系方式

如有问题，请查看项目文档或提交 Issue。

---

**Version**: 1.0.0  
**Python**: 3.11+  
**Framework**: FastAPI 0.115+

