# 数据库重置使用指南

## 问题说明

当数据库模型发生变更时，部署后仍然使用旧的数据库数据，因为 Docker Volume 会持久化数据。

## 解决方案

提供三种方式来重置数据库：

---

## 方式 1: 通过 Commit Message（推荐用于 CI/CD）

在 commit message 中添加 `[reset-db]` 标记，部署时自动重置数据库：

```bash
git add .
git commit -m "更新数据库模型 [reset-db]"
git push
```

**优点**: 自动化，适合 CI/CD 流程  
**使用场景**: 数据库模型变更时

---

## 方式 2: 使用数据库管理脚本（推荐用于本地）

### Linux/macOS:
```bash
# 重置数据库（会提示确认）
./scripts/manage_db.sh reset

# 查看数据库状态
./scripts/manage_db.sh status

# 查看数据库日志
./scripts/manage_db.sh logs
```

### Windows:
```powershell
# 重置数据库（会提示确认）
.\scripts\manage_db.ps1 reset

# 查看数据库状态
.\scripts\manage_db.ps1 status

# 查看数据库日志
.\scripts\manage_db.ps1 logs
```

**优点**: 精确控制，仅操作数据库  
**使用场景**: 本地开发测试

---

## 方式 3: 使用部署脚本

### Linux/macOS:
```bash
# 部署并重置数据库
./scripts/deploy.sh --reset-db

# 正常部署（保留数据）
./scripts/deploy.sh
```

### Windows:
```powershell
# 部署并重置数据库
.\scripts\deploy.ps1 -ResetDb

# 正常部署（保留数据）
.\scripts\deploy.ps1
```

**优点**: 一键部署+重置  
**使用场景**: 手动部署时需要重置数据库

---

## 方式对比

| 方式 | 适用场景 | 自动化程度 | 影响范围 |
|------|---------|-----------|---------|
| Commit Message | CI/CD 自动部署 | 高 | 完整部署 |
| 数据库管理脚本 | 本地开发 | 中 | 仅数据库 |
| 部署脚本 | 手动部署 | 中 | 完整部署 |

---

## 工作原理

### 默认行为（保留数据）
```bash
docker-compose down        # 停止容器，保留 volume
docker-compose up -d       # 启动容器，使用已有数据
```

### 重置数据库
```bash
docker-compose down -v     # 停止容器并删除 volume
docker-compose up -d       # 启动容器，创建新数据库
```

---

## 快速参考

### ✅ 需要重置数据库的情况

- 数据库表结构变更
- 字段类型修改
- 添加/删除字段
- 清空测试数据

### ❌ 不需要重置的情况

- 仅修改业务逻辑
- 前端代码更新
- API 接口调整（不涉及数据库）
- 配置文件修改

---

## 注意事项

⚠️ **警告**: 重置数据库会删除所有数据！

- 测试环境：可以随意重置
- 生产环境：谨慎使用，建议先备份

---

## 常见问题

### Q: 如何确认数据库已被重置？

A: 查看部署日志中是否有 "删除数据库volume" 的提示，或者使用：
```bash
./scripts/manage_db.sh status
```

### Q: 可以手动删除 volume 吗？

A: 可以，但建议使用脚本：
```bash
docker-compose down
docker volume rm ditan_postgres_data
docker-compose up -d
```

### Q: 如何验证新的数据库结构？

A: 连接数据库查看：
```bash
docker exec -it ditan_db psql -U huanyu -d ditan
\dt  # 查看表
\d patients  # 查看表结构
```

---

## 相关文档

- [完整数据库管理文档](DATABASE.md)
- [快速参考](QUICKREF.md)
- [部署文档](DEPLOYMENT.md)

---

**文档版本**: v1.0  
**最后更新**: 2025-10-20

