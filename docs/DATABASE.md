# 数据库管理指南

本文档介绍如何管理 DitanBackend 项目的数据库，包括重置、备份和常见问题处理。

## 目录

- [数据库架构](#数据库架构)
- [数据库管理脚本](#数据库管理脚本)
- [重置数据库](#重置数据库)
- [CI/CD 部署时的数据库管理](#cicd-部署时的数据库管理)
- [常见问题](#常见问题)

## 数据库架构

- **数据库类型**: PostgreSQL
- **数据持久化**: Docker Volume (`ditan_postgres_data`)
- **初始化**: 通过 `scripts/init_db.py` 创建表结构

## 数据库管理脚本

### 1. 数据库管理工具 (manage_db)

提供了完整的数据库管理功能：

**Linux/macOS:**
```bash
./scripts/manage_db.sh [command]
```

**Windows:**
```powershell
.\scripts\manage_db.ps1 [command]
```

**可用命令:**
- `reset` - 重置数据库（删除所有数据）
- `restart` - 重启数据库容器
- `logs` - 查看数据库日志
- `status` - 查看数据库状态
- `help` - 显示帮助信息

### 2. 部署脚本 (deploy)

用于手动部署应用，支持选择是否重置数据库：

**Linux/macOS:**
```bash
# 正常部署（保留数据库）
./scripts/deploy.sh

# 部署并重置数据库
./scripts/deploy.sh --reset-db
```

**Windows:**
```powershell
# 正常部署（保留数据库）
.\scripts\deploy.ps1

# 部署并重置数据库
.\scripts\deploy.ps1 -ResetDb
```

## 重置数据库

### 场景 1: 本地开发环境重置

当你需要清空所有测试数据或数据库模型发生变更时：

```bash
# 使用数据库管理工具
./scripts/manage_db.sh reset

# 或使用 docker-compose 命令
docker-compose down -v
docker-compose up -d
```

### 场景 2: 生产/测试环境重置

使用部署脚本的 `--reset-db` 参数：

```bash
./scripts/deploy.sh --reset-db
```

**⚠️ 警告**: 这将删除所有数据，请谨慎操作！

## CI/CD 部署时的数据库管理

### 默认行为

默认情况下，CI/CD 部署会**保留数据库数据**：

```bash
git commit -m "更新代码"
git push
# 部署时保留数据库
```

### 重置数据库

如果需要在部署时重置数据库，在 commit message 中添加 `[reset-db]` 标记：

```bash
git commit -m "更新数据库模型 [reset-db]"
git push
# 部署时会删除数据库 volume 并重建
```

### 工作原理

CI/CD 脚本会检查 commit message，如果包含 `[reset-db]` 标记，则执行：

```bash
# 停止容器并删除 volume
docker-compose down -v

# 重新启动
docker-compose up -d
```

否则执行：

```bash
# 只停止容器，保留 volume
docker-compose down

# 重新启动
docker-compose up -d
```

## 数据持久化

### Volume 管理

数据库数据存储在 Docker Volume 中：

```yaml
volumes:
  postgres_data:
    name: ditan_postgres_data
```

**查看 Volume:**
```bash
docker volume ls
docker volume inspect ditan_postgres_data
```

**手动删除 Volume:**
```bash
docker-compose down
docker volume rm ditan_postgres_data
```

### 数据库初始化流程

1. 容器启动时，PostgreSQL 自动初始化
2. 应用启动时，通过 SQLAlchemy 创建表结构：
   ```python
   async def init_db():
       async with engine.begin() as conn:
           await conn.run_sync(Base.metadata.create_all)
   ```

## 常见问题

### Q: 为什么部署后数据还在？

A: 默认情况下，Docker Volume 会持久化数据。要重置数据库，需要使用 `[reset-db]` 标记或手动删除 volume。

### Q: 如何查看数据库中的数据？

A: 可以使用数据库客户端工具连接：

```bash
# 获取数据库容器 IP
docker inspect ditan_db

# 使用 psql 连接
docker exec -it ditan_db psql -U huanyu -d ditan

# 查看表
\dt

# 查看数据
SELECT * FROM patients;
```

### Q: 数据库初始化失败怎么办？

A: 检查日志并重建：

```bash
# 查看数据库日志
./scripts/manage_db.sh logs

# 或者
docker-compose logs db

# 重置数据库
./scripts/manage_db.sh reset
```

### Q: 如何备份数据库？

A: 使用 pg_dump：

```bash
# 备份
docker exec ditan_db pg_dump -U huanyu ditan > backup.sql

# 恢复
docker exec -i ditan_db psql -U huanyu ditan < backup.sql
```

### Q: 本地和服务器的数据库如何同步？

A: 由于目前都是测试数据，建议：

1. 不要同步，各自独立
2. 如需同步，使用 pg_dump/pg_restore
3. 考虑使用数据迁移工具（如 Alembic）

## 最佳实践

### 开发环境

- ✅ 经常重置数据库，保持数据干净
- ✅ 使用脚本自动化操作
- ✅ 提交代码前测试数据库迁移

### 生产/测试环境

- ✅ 谨慎使用 `[reset-db]` 标记
- ✅ 部署前备份重要数据
- ✅ 监控数据库日志
- ✅ 定期清理无用数据

### 未来规划

当项目成熟后，建议：

1. 引入数据库迁移工具（Alembic）
2. 实现自动备份机制
3. 区分开发/测试/生产环境的数据管理策略
4. 添加数据库版本控制

## 相关文件

- `docker-compose.yml` - Docker 编排配置
- `app/core/database.py` - 数据库连接和初始化
- `app/models/` - 数据库模型定义
- `scripts/init_db.py` - 数据库初始化脚本
- `scripts/manage_db.sh` - 数据库管理脚本（Linux/macOS）
- `scripts/manage_db.ps1` - 数据库管理脚本（Windows）
- `scripts/deploy.sh` - 部署脚本（Linux/macOS）
- `scripts/deploy.ps1` - 部署脚本（Windows）
- `scripts/cicd_workflow.yml` - CI/CD 工作流配置

## 技术细节

### SQLAlchemy 表创建

```python
# app/core/database.py
async def init_db():
    """初始化数据库（创建所有表）"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
```

### Docker Volume 挂载

```yaml
# docker-compose.yml
services:
  db:
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
    name: ditan_postgres_data
```

### CI/CD 数据库重置逻辑

```bash
# scripts/cicd_workflow.yml
if [[ "${{ github.event.head_commit.message }}" == *"[reset-db]"* ]]; then
  echo "🗑️  删除数据库volume..."
  sudo docker-compose down -v
else
  echo "💾 保留数据库数据..."
  sudo docker-compose down
fi
```

## 总结

- 默认保留数据库数据，适合大多数场景
- 通过脚本或 `[reset-db]` 标记灵活控制数据库重置
- 提供了完整的管理工具和文档
- 未来可扩展支持数据库迁移和备份

如有问题，请查看日志或提交 Issue。

