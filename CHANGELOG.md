# 更新日志

本文档记录了项目的主要变更和版本更新信息。

## [2.0.0] - 2025-01-15

### 新增功能 ✨

#### 医生管理系统

- 新增医生注册功能 (`POST /api/v1/doctor/register`)
    - 支持用户名、密码、姓名、性别、手机号等必填信息
    - 支持科室、职位、个人简介等可选信息
    - 用户名和手机号唯一性验证
    - 密码强度验证（至少6位）

- 新增医生登录功能 (`POST /api/v1/doctor/login`)
    - 用户名和密码认证
    - 返回JWT访问令牌（默认有效期24小时）
    - 记录最后登录时间

- 新增医生信息管理功能
    - 获取当前登录医生信息 (`GET /api/v1/doctor/me`)
    - 更新医生信息 (`PUT /api/v1/doctor/me`)
    - 修改密码 (`POST /api/v1/doctor/change-password`)

#### 认证和安全

- 实现JWT认证机制
    - 使用 python-jose 生成和验证JWT令牌
    - HTTP Bearer 认证方案
    - 可配置的令牌过期时间

- 密码安全
    - 使用 bcrypt 哈希算法加密密码
    - 密码验证使用恒定时间比较，防止时序攻击

#### 数据库模型

- 新增 `Doctor` 实体
    - doctor_id（主键）
    - username（唯一，用于登录）
    - password_hash（bcrypt加密）
    - name, gender, phone（必填）
    - department, position, bio（可选）
    - created_at, updated_at, last_login（时间戳）

- 更新 `DoctorDiagnosisRecord` 实体
    - doctor_id 从 String 改为 Integer
    - 添加外键关联到 Doctor 表
    - 支持通过医生ID查询所有诊断记录

### 改进 🚀

#### API文档

- 更新 API.md，新增医生管理章节
    - 详细的接口说明和示例
    - 认证机制说明
    - 错误响应格式说明

- 新增 QUICKSTART.md 快速上手指南
    - 医生功能使用指南
    - 完整工作流程示例
    - 常见问题解答

- 新增 DATABASE.md 数据库文档
    - 数据库结构详细说明
    - 迁移指南（v1.0 到 v2.0）
    - 性能优化建议
    - 数据库监控查询

#### 项目配置

- 更新 pyproject.toml，新增依赖
    - python-jose[cryptography]>=3.3.0（JWT支持）
    - passlib[bcrypt]>=1.7.4（密码加密）

- 更新配置文件 (app/core/config.py)
    - 新增 JWT_SECRET_KEY 配置
    - 新增 JWT_ALGORITHM 配置
    - 新增 JWT_ACCESS_TOKEN_EXPIRE_MINUTES 配置

#### README更新

- 更新特性列表，突出医生管理功能
- 更新技术栈，添加认证相关库
- 更新项目结构说明
- 新增医生功能使用示例
- 更新版本号到 2.0.0

### 测试 🧪

#### 单元测试

- 新增 tests/test_doctor.py
    - 医生注册测试（成功、重复用户名、重复手机号、无效输入）
    - 医生登录测试（成功、错误密码、不存在的用户）
    - 医生信息管理测试（查询、更新、未认证访问）
    - 密码修改测试（成功、错误旧密码）
    - 集成测试（完整工作流程）

### 技术债务和优化 🔧

#### 代码质量

- 所有新增代码通过 linter 检查
- 遵循现有代码风格和架构模式
- 完善的类型注解

#### 索引优化

- doctors 表新增索引
    - idx_doctors_username（用于登录查询）
    - idx_doctors_phone（用于手机号查询）
- doctor_diagnosis_records 表新增索引
    - idx_doctor_diagnosis_records_doctor_id（用于医生诊断记录查询）

### 破坏性变更 ⚠️

#### 数据库结构变更

- DoctorDiagnosisRecord.doctor_id 类型从 String 变更为 Integer
- 需要执行数据库迁移才能从 v1.0 升级到 v2.0
- 迁移脚本见 docs/DATABASE.md

### 安全注意事项 🔒

1. **JWT密钥配置**
    - 生产环境必须修改 JWT_SECRET_KEY
    - 建议使用至少32字节的强随机字符串
    - 示例: `openssl rand -hex 32`

2. **密码策略**
    - 当前最小密码长度为6位
    - 建议生产环境要求更强的密码策略

3. **令牌管理**
    - JWT令牌默认24小时过期
    - 令牌无法主动撤销，请妥善保管
    - 考虑实现刷新令牌机制

### 已知问题 🐛

暂无

### 未来计划 📋

- [ ] 密码找回功能
- [ ] 刷新令牌机制
- [ ] 医生权限分级（管理员、普通医生等）
- [ ] 医生操作日志
- [ ] 账户锁定机制（防暴力破解）
- [ ] 双因素认证（2FA）
- [ ] 医生之间的协作功能

### 迁移指南 📚

## v3.0.0 (2025-10-26)

### BREAKING CHANGE

- 修改了数据库模型，需要进行数据库的迁移或者重建

### Feat

- **core**: 添加用户的登录验证模块

## v2.0.0 (2025-10-23)

### BREAKING CHANGE

- 更新项目依赖环境
- 数据库的结构发生改变

### Feat

- **core**: 添加预就诊记录的接口，获取用户数据接口，获取用户就诊记录数据接口，AI生成处方和证型接口
- **core**: 集成ai诊断模块，添加更多接口

## v1.0.1 (2025-10-20)

### Fix

- **deploy**: 解决了网络超时的问题，因为网络情况不太稳定，所以必须要增加更多的等待时间

#### 从 v1.0.0 升级到 v2.0.0

1. **更新代码**
   ```bash
   git pull origin main
   uv sync
   ```

2. **更新环境变量**
   在 .env 文件中添加：
   ```env
   JWT_SECRET_KEY=your-secret-key-change-this-in-production
   JWT_ALGORITHM=HS256
   JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440
   ```

3. **数据库迁移**

   **方式1: 完全重置（推荐用于开发环境）**
   ```bash
   # Linux/macOS
   ./scripts/manage_db.sh reset
   
   # Windows
   .\scripts\manage_db.ps1 reset
   ```

   **方式2: 手动迁移（生产环境）**
   ```sql
   -- 1. 创建 doctors 表
   CREATE TABLE doctors (
       doctor_id SERIAL PRIMARY KEY,
       username VARCHAR(50) NOT NULL UNIQUE,
       password_hash VARCHAR(255) NOT NULL,
       name VARCHAR(50) NOT NULL,
       gender VARCHAR(10) NOT NULL,
       phone VARCHAR(11) NOT NULL UNIQUE,
       department VARCHAR(100),
       position VARCHAR(100),
       bio TEXT,
       created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
       updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
       last_login TIMESTAMP
   );
   
   CREATE INDEX idx_doctors_username ON doctors(username);
   CREATE INDEX idx_doctors_phone ON doctors(phone);
   
   -- 2. 修改 doctor_diagnosis_records 表
   ALTER TABLE doctor_diagnosis_records 
       ALTER COLUMN doctor_id TYPE INTEGER USING doctor_id::integer;
   
   ALTER TABLE doctor_diagnosis_records
       ADD CONSTRAINT fk_doctor_diagnosis_doctor
       FOREIGN KEY (doctor_id) REFERENCES doctors(doctor_id);
   
   ALTER TABLE doctor_diagnosis_records
       ALTER COLUMN doctor_id SET NOT NULL;
   
   CREATE INDEX idx_doctor_diagnosis_records_doctor_id 
       ON doctor_diagnosis_records(doctor_id);
   ```

4. **验证迁移**
   ```bash
   # 运行测试
   uv run pytest tests/test_doctor.py -v
   
   # 启动服务
   uv run python main.py
   
   # 访问API文档
   http://localhost:8000/docs
   ```

### 贡献者 👥

- 开发团队

---

## [1.0.0] - 2024-01-01

### 初始版本

#### 核心功能

- 患者管理功能
- 就诊记录管理
- AI智能诊断
    - 病历生成
    - 证型判断
    - 处方生成
    - 运动处方生成

#### 技术架构

- FastAPI 框架
- PostgreSQL 数据库
- SQLAlchemy ORM
- Pydantic 数据验证
- OpenAI Compatible API 集成

#### 文档

- API 文档
- 部署文档
- README

#### 测试

- 患者管理测试
- 就诊流程测试

---

## 版本命名规范

本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/) 规范：

- **主版本号（MAJOR）**: 不兼容的API修改
- **次版本号（MINOR）**: 向下兼容的功能性新增
- **修订号（PATCH）**: 向下兼容的问题修正

示例：

- 1.0.0 -> 1.0.1: Bug修复
- 1.0.1 -> 1.1.0: 新增功能（向下兼容）
- 1.1.0 -> 2.0.0: 破坏性变更（需要迁移）
