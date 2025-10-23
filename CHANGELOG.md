# 更新日志

## v2.0.0 - 2024-01-22

### 🎉 主要更新

这是一次重大的架构重构，将系统从简单的患者数据上传服务升级为完整的中医智能诊疗系统。

### ✨ 新功能

#### 1. 数据库模型重构
- **新增模型**：
  - `Patient` - 患者基本信息
  - `PatientMedicalRecord` - 就诊记录（聚合根）
  - `PreDiagnosisRecord` - 预诊记录
  - `SanzhenAnalysisResult` - 三诊分析结果
  - `DiagnosisRecord` - 诊断记录基类
  - `AIDiagnosisRecord` - AI诊断记录
  - `DoctorDiagnosisRecord` - 医生诊断记录

- **模型特性**：
  - 使用SQLAlchemy多态继承实现诊断记录类型
  - 完整的关系映射和级联删除
  - 支持枚举类型（Gender, DiagnosisType）

#### 2. AI智能诊断引擎
- **病历生成**：从ASR转录文本自动提取关键信息生成结构化病历
- **证型判断**：基于中医理论智能判断四大证型
  - 脾虚湿困型
  - 胃热燔脾型
  - 气滞血瘀型
  - 脾肾阳虚型
- **处方生成**：根据证型和症状生成个性化中药处方
- **运动处方**：根据体质、证型和BMI生成4周个性化运动计划

#### 3. 完整的API接口
- **患者管理**：
  - `POST /api/v1/patient/register` - 从二维码注册患者
  - `GET /api/v1/patient/query` - 通过手机号查询患者信息

- **就诊记录管理**：
  - `POST /api/v1/medical-record` - 创建就诊记录
  - `GET /api/v1/medical-record/{record_id}` - 获取完整就诊信息

- **AI诊断**：
  - `POST /api/v1/medical-record/{record_id}/ai-diagnosis` - 生成AI诊断

#### 4. 服务层架构
- **OpenAIChatCompletion** - OpenAI兼容API客户端
- **TCMDiagnosisService** - 中医诊断服务
  - 支持流式输出
  - 完整的错误处理
  - 处理时间统计
- **Prompt Templates** - 专业的中医诊断Prompt模板

### 🔧 配置更新

#### 新增环境变量
```env
AI_API_KEY - AI服务API密钥
AI_BASE_URL - AI服务基础URL
AI_MODEL_NAME - AI模型名称（默认：deepseek-chat）
```

#### Docker配置更新
- 更新 `docker-compose.yml` 添加AI服务配置
- 更新 `cicd_workflow.yml` 添加AI环境变量

### 📝 文档更新

- ✅ 完全重写 `docs/API.md` - 详细的API接口文档
- ✅ 更新 `README.md` - 新功能介绍和使用指南
- ✅ 创建 `.env.example` - 环境变量示例

### 🧪 测试

#### 新增测试文件
- `tests/test_patient_new.py` - 完整的API测试套件
  - 患者查询测试
  - 患者注册测试
  - 就诊记录创建测试
  - AI诊断测试（包含mock）

#### 测试覆盖
- ✅ 患者管理功能
- ✅ 就诊记录管理
- ✅ AI诊断流程
- ✅ 错误处理

### 🗂️ 项目结构变化

#### 新增目录
```
app/
├── services/
│   ├── openai_client.py
│   ├── prompt_templates.py
│   └── tcm_diagnosis_service.py
```

#### 修改文件
- `app/models/patient.py` - 完全重写
- `app/schemas/patient.py` - 完全重写
- `app/api/patient.py` - 完全重写
- `app/core/config.py` - 添加AI配置

### ⚠️ 破坏性变更

#### 数据库架构变更
- 旧的 `Patient` 表结构已完全改变
- 需要执行数据库迁移或重置数据库

#### API变更
- 移除旧的 `POST /api/v1/patient` 端点
- 新的API接口结构和请求/响应格式

### 📦 依赖更新

无新增依赖，所有功能使用现有依赖实现：
- `openai>=2.6.0` - AI服务客户端
- `sqlalchemy>=2.0.35` - ORM
- `fastapi>=0.115.0` - Web框架

### 🚀 迁移指南

#### 1. 更新环境变量
在 `.env` 文件中添加AI配置：
```env
AI_API_KEY=your_api_key
AI_BASE_URL=https://api.deepseek.com
AI_MODEL_NAME=deepseek-chat
```

#### 2. 重置数据库
```bash
# 如果使用Docker
docker-compose down -v
docker-compose up -d

# 如果本地开发
uv run python scripts/init_db.py
```

#### 3. 更新应用代码
如果有客户端代码，需要更新API调用方式：

**旧方式**：
```python
POST /api/v1/patient
{
  "uuid": "...",
  "phone": "...",
  ...
}
```

**新方式**：
```python
# 1. 注册患者
POST /api/v1/patient/register
{
  "card_number": "...",
  "name": "...",
  ...
}

# 2. 创建就诊记录
POST /api/v1/medical-record
{
  "uuid": "...",
  "patient_phone": "...",
  "pre_diagnosis": {...}
}

# 3. 生成AI诊断
POST /api/v1/medical-record/{id}/ai-diagnosis
{
  "asr_text": "..."
}
```

### 🐛 已知问题

- AI诊断需要10-20秒，建议前端做好加载提示
- 需要配置有效的AI API密钥才能使用诊断功能

### 📈 性能

- AI诊断平均响应时间：10-15秒
- 数据库查询优化：使用eager loading减少N+1查询
- 异步处理：所有数据库操作都是异步的

### 🙏 致谢

感谢 `demo/mini-tcm/mini_tcm_demo.py` 提供的AI诊断引擎参考实现。

---

## v1.0.1 - 2024-01-15

### 修复
- 修复数据验证问题
- 优化日志输出

## v1.0.0 - 2024-01-01

### 初始版本
- 基础患者数据上传功能
- PostgreSQL数据库支持
- FastAPI框架
