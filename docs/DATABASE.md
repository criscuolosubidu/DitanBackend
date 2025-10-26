# 数据库管理文档

## 数据库结构

### 核心实体

#### 1. Doctor（医生）
医生用户实体，用于系统登录和诊断管理。

**字段说明：**
- `doctor_id`: 医生ID（主键）
- `username`: 用户名（唯一，用于登录）
- `password_hash`: 密码哈希（使用bcrypt加密）
- `name`: 医生姓名
- `gender`: 性别（MALE/FEMALE/OTHER）
- `phone`: 手机号（唯一）
- `department`: 科室（可选）
- `position`: 职位（可选）
- `bio`: 个人简介（可选）
- `created_at`: 创建时间
- `updated_at`: 更新时间
- `last_login`: 最后登录时间

**关系：**
- 一个医生可以有多个诊断记录（DoctorDiagnosisRecord）

#### 2. Patient（患者）
患者基本信息。

**字段说明：**
- `patient_id`: 患者ID（主键）
- `name`: 患者姓名
- `sex`: 性别
- `birthday`: 出生日期
- `phone`: 手机号（唯一）

**关系：**
- 一个患者可以有多个就诊记录（PatientMedicalRecord）

#### 3. PatientMedicalRecord（就诊记录）
代表一次完整的就诊事件（聚合根）。

**字段说明：**
- `record_id`: 就诊记录ID（主键）
- `patient_id`: 患者ID（外键）
- `uuid`: UUID（用于幂等性控制）
- `status`: 状态（pending/in_progress/completed）
- `created_at`: 创建时间
- `updated_at`: 更新时间

**关系：**
- 属于一个患者
- 包含一个预诊记录（PreDiagnosisRecord）
- 可以有多个诊断记录（DiagnosisRecord）

#### 4. PreDiagnosisRecord（预诊记录）
预诊阶段的数据采集记录。

**字段说明：**
- `pre_diagnosis_id`: 预诊记录ID（主键）
- `record_id`: 就诊记录ID（外键）
- `uuid`: UUID
- `height`: 身高（cm）
- `weight`: 体重（kg）
- `coze_conversation_log`: 对话记录
- `created_at`: 创建时间
- `updated_at`: 更新时间

**关系：**
- 属于一个就诊记录
- 可以有一个三诊分析结果（SanzhenAnalysisResult）

#### 5. SanzhenAnalysisResult（三诊分析结果）
面诊、舌诊、脉诊的分析结果。

**字段说明：**
- `sanzhen_id`: 三诊分析ID（主键）
- `pre_diagnosis_id`: 预诊记录ID（外键）
- `face`: 面诊结果
- `tongue_front`: 舌诊正面
- `tongue_bottom`: 舌诊舌下
- `pulse`: 脉诊结果
- `diagnosis_result`: 综合诊断结果

#### 6. DiagnosisRecord（诊断记录基类）
诊断记录的抽象基类，使用单表继承（STI）模式。

**字段说明：**
- `diagnosis_id`: 诊断记录ID（主键）
- `record_id`: 就诊记录ID（外键）
- `type`: 诊断类型（AI_DIAGNOSIS/DOCTOR_DIAGNOSIS）
- `formatted_medical_record`: 格式化病历
- `type_inference`: 证型推断
- `treatment`: 治疗建议
- `prescription`: 处方
- `exercise_prescription`: 运动处方
- `created_at`: 创建时间
- `updated_at`: 更新时间

#### 7. AIDiagnosisRecord（AI诊断记录）
继承自DiagnosisRecord。

**额外字段：**
- `diagnosis_explanation`: 诊断解释
- `response_time`: 响应时间（秒）
- `model_name`: 模型名称

#### 8. DoctorDiagnosisRecord（医生诊断记录）
继承自DiagnosisRecord，关联到医生。

**额外字段：**
- `doctor_id`: 医生ID（外键，关联到Doctor表）
- `comments`: 医生备注

**关系：**
- 属于一个医生

## 数据库初始化

### 创建数据库

```sql
CREATE DATABASE ditan_db;
```

### 初始化表结构

```bash
# 使用初始化脚本
uv run python scripts/init_db.py
```

该脚本会自动创建所有表，包括：
- doctors（医生表）
- patients（患者表）
- patient_medical_records（就诊记录表）
- pre_diagnosis_records（预诊记录表）
- sanzhen_analysis_results（三诊分析结果表）
- diagnosis_records（诊断记录表）
- ai_diagnosis_records（AI诊断记录表）
- doctor_diagnosis_records（医生诊断记录表）

## 数据库迁移

### v2.0.0 迁移说明

如果你从 v1.0.0 升级到 v2.0.0，需要执行以下迁移：

#### 1. 添加 doctors 表

```sql
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
```

#### 2. 修改 doctor_diagnosis_records 表

```sql
-- 添加外键约束到 doctors 表
ALTER TABLE doctor_diagnosis_records 
    ALTER COLUMN doctor_id TYPE INTEGER USING doctor_id::integer;

ALTER TABLE doctor_diagnosis_records
    ADD CONSTRAINT fk_doctor_diagnosis_doctor
    FOREIGN KEY (doctor_id) REFERENCES doctors(doctor_id);

ALTER TABLE doctor_diagnosis_records
    ALTER COLUMN doctor_id SET NOT NULL;

CREATE INDEX idx_doctor_diagnosis_records_doctor_id ON doctor_diagnosis_records(doctor_id);
```

## 数据库重置

### 使用管理脚本

**Linux/macOS:**
```bash
./scripts/manage_db.sh reset
```

**Windows:**
```powershell
.\scripts\manage_db.ps1 reset
```

这会删除所有表并重新创建。

### 手动重置

```bash
# 1. 删除数据库
psql -U postgres -c "DROP DATABASE IF EXISTS ditan_db;"

# 2. 重新创建数据库
psql -U postgres -c "CREATE DATABASE ditan_db;"

# 3. 初始化表结构
uv run python scripts/init_db.py
```

## 常见问题

### Q: 如何修改数据库结构？

A: 
1. 修改 `app/models/patient.py` 中的模型定义
2. 运行 `uv run python scripts/init_db.py` 重新创建表
3. 注意：这会删除所有现有数据

### Q: 如何备份数据？

A:
```bash
# 备份数据库
pg_dump -U postgres ditan_db > backup.sql

# 恢复数据库
psql -U postgres ditan_db < backup.sql
```

### Q: 如何查看数据库表结构？

A:
```bash
# 连接数据库
psql -U postgres ditan_db

# 查看所有表
\dt

# 查看表结构
\d doctors
\d patients
\d patient_medical_records
```

### Q: 医生诊断记录如何关联医生？

A: 
DoctorDiagnosisRecord 表通过 `doctor_id` 字段关联到 Doctor 表。创建医生诊断记录时，需要提供有效的医生ID。

```python
# 示例：创建医生诊断记录
doctor_diagnosis = DoctorDiagnosisRecord(
    record_id=medical_record.record_id,
    doctor_id=current_doctor.doctor_id,  # 从JWT令牌中获取
    formatted_medical_record="...",
    type_inference="脾虚湿困型",
    prescription="...",
    comments="患者需要注意饮食调理"
)
```

## 性能优化

### 索引

系统已创建以下索引：

**doctors 表：**
- `idx_doctors_username`: username字段（用于登录查询）
- `idx_doctors_phone`: phone字段（用于手机号查询）

**patients 表：**
- `idx_patients_phone`: phone字段（用于患者查询）

**patient_medical_records 表：**
- `idx_medical_records_patient_id`: patient_id字段
- `idx_medical_records_uuid`: uuid字段

**pre_diagnosis_records 表：**
- `idx_pre_diagnosis_record_id`: record_id字段
- `idx_pre_diagnosis_uuid`: uuid字段

**sanzhen_analysis_results 表：**
- `idx_sanzhen_pre_diagnosis_id`: pre_diagnosis_id字段

**diagnosis_records 表：**
- `idx_diagnosis_record_id`: record_id字段

**doctor_diagnosis_records 表：**
- `idx_doctor_diagnosis_records_doctor_id`: doctor_id字段（用于查询某医生的诊断记录）

### 连接池配置

在 `app/core/database.py` 中已配置连接池：

```python
engine = create_async_engine(
    settings.database_url,
    echo=settings.APP_DEBUG,
    pool_pre_ping=True,  # 连接前先ping
    pool_size=10,        # 连接池大小
    max_overflow=20,     # 最大溢出连接数
)
```

## 数据库监控

### 查看活动连接

```sql
SELECT * FROM pg_stat_activity WHERE datname = 'ditan_db';
```

### 查看表大小

```sql
SELECT 
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### 查看索引使用情况

```sql
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY idx_scan DESC;
```

## 安全建议

1. **密码存储**：医生密码使用 bcrypt 哈希，永远不要存储明文密码
2. **JWT密钥**：生产环境必须修改 `JWT_SECRET_KEY` 为强随机字符串
3. **数据库权限**：生产环境应为应用创建专用数据库用户，限制权限
4. **备份策略**：定期备份数据库，建议每天备份一次

## 相关文档

- [API文档](API.md)
- [部署文档](DEPLOYMENT.md)
- [快速开始](../README.md)
