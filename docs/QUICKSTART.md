# 快速开始指南

本指南将帮助您快速部署和使用中医智能诊疗系统。

## 目录
- [环境准备](#环境准备)
- [快速部署](#快速部署)
- [API使用示例](#api使用示例)
- [常见问题](#常见问题)

---

## 环境准备

### 1. 系统要求
- Python 3.11+
- PostgreSQL 12+
- Docker & Docker Compose（可选）

### 2. 获取AI API密钥

本系统使用OpenAI兼容的API，推荐使用DeepSeek API：

1. 访问 [https://platform.deepseek.com](https://platform.deepseek.com)
2. 注册账号并充值
3. 获取API密钥

---

## 快速部署

### 方式一：Docker部署（推荐）

#### 1. 克隆项目
```bash
git clone <repository-url>
cd DitanBackend
```

#### 2. 配置环境变量
```bash
# 创建.env文件
cat > .env << EOF
DATABASE_USER=huanyu
DATABASE_PASSWORD=Huanyu2020yyds!
DATABASE_NAME=ditan
DATABASE_PORT=5432
DATABASE_HOST=db
APP_PORT=8000
APP_NAME=DitanBackend
APP_VERSION=2.0.0
APP_HOST=0.0.0.0
APP_DEBUG=False
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
AI_API_KEY=your_deepseek_api_key
AI_BASE_URL=https://api.deepseek.com
AI_MODEL_NAME=deepseek-chat
EOF
```

#### 3. 启动服务
```bash
docker-compose up -d
```

#### 4. 检查服务状态
```bash
# 查看容器状态
docker-compose ps

# 查看应用日志
docker-compose logs -f app

# 健康检查
curl http://localhost:8000/health
```

#### 5. 访问API文档
浏览器打开：http://localhost:8000/docs

---

### 方式二：本地开发部署

#### 1. 安装uv包管理器
```bash
# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Linux/macOS
curl -LsSf https://astral.sh/uv/install.sh | sh
```

#### 2. 安装依赖
```bash
cd DitanBackend
uv sync --extra dev
```

#### 3. 启动PostgreSQL
```bash
# 使用Docker启动PostgreSQL
docker run -d \
  --name postgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=ditan \
  -p 5432:5432 \
  postgres:latest
```

#### 4. 配置环境变量
创建 `.env` 文件：
```env
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_USER=postgres
DATABASE_PASSWORD=password
DATABASE_NAME=ditan

APP_HOST=0.0.0.0
APP_PORT=8000
APP_DEBUG=True

LOG_LEVEL=INFO
LOG_FILE=logs/app.log

AI_API_KEY=your_deepseek_api_key
AI_BASE_URL=https://api.deepseek.com
AI_MODEL_NAME=deepseek-chat
```

#### 5. 初始化数据库
```bash
uv run python scripts/init_db.py
```

#### 6. 启动应用
```bash
uv run python scripts/run_dev.py
```

访问：http://localhost:8000/docs

---

## API使用示例

### 完整就诊流程示例

#### 步骤1：扫码注册患者

```bash
curl -X POST "http://localhost:8000/api/v1/patient/register" \
  -H "Content-Type: application/json" \
  -d '{
    "card_number": "CARD20240122001",
    "name": "张三",
    "phone": "13800138001",
    "gender": "Male",
    "birthday": "1985-05-20",
    "target_weight": "70"
  }'
```

**响应**：
```json
{
  "success": true,
  "message": "患者注册成功",
  "data": {
    "patient_id": 1,
    "name": "张三",
    "sex": "Male",
    "birthday": "1985-05-20",
    "phone": "13800138001"
  }
}
```

---

#### 步骤2：创建就诊记录

```bash
curl -X POST "http://localhost:8000/api/v1/medical-record" \
  -H "Content-Type: application/json" \
  -d '{
    "uuid": "550e8400-e29b-41d4-a716-446655440001",
    "patient_phone": "13800138001",
    "pre_diagnosis": {
      "uuid": "660e8400-e29b-41d4-a716-446655440001",
      "height": 175.0,
      "weight": 85.0,
      "coze_conversation_log": "患者：我最近体重增加了很多，感觉身体很沉重...",
      "sanzhen_analysis": {
        "face": "面色略黄，唇色偏淡",
        "tongue_front": "舌体偏胖，舌苔薄白，边有齿痕",
        "tongue_bottom": "舌下络脉颜色正常",
        "pulse": "脉象沉细，左手关脉较弱",
        "diagnosis_result": "初步判断为脾虚湿困"
      }
    }
  }'
```

**响应**：
```json
{
  "success": true,
  "message": "就诊记录创建成功",
  "data": {
    "record_id": 1,
    "uuid": "550e8400-e29b-41d4-a716-446655440001",
    "status": "pending",
    "patient": {...},
    "pre_diagnosis": {...}
  }
}
```

---

#### 步骤3：生成AI诊断

```bash
curl -X POST "http://localhost:8000/api/v1/medical-record/1/ai-diagnosis" \
  -H "Content-Type: application/json" \
  -d '{
    "asr_text": "医生：您好，请问有什么不舒服的地方？\n患者：我最近体重增加了很多，有10多斤，感觉身体很沉重，特别是下午的时候。\n医生：还有其他症状吗？比如食欲怎么样？\n患者：食欲还行，但是吃完饭后容易胀，大便也不太成形。\n医生：睡眠如何？\n患者：晚上睡得还可以，但是白天容易犯困。\n医生：好的，让我看看您的舌头和把把脉..."
  }'
```

**注意**：AI诊断需要10-20秒，请耐心等待。

**响应**：
```json
{
  "success": true,
  "message": "AI诊断完成",
  "data": {
    "diagnosis_id": 1,
    "record_id": 1,
    "type": "AI_DIAGNOSIS",
    "formatted_medical_record": "主诉：体重增加，身体沉重\n病史：初诊日期2024-01-22，身高175cm，体重85kg，近期体重增加10kg...",
    "type_inference": "脾虚湿困型",
    "prescription": "党参 10g\n麸炒白术 15g\n茯苓 15g\n泽泻 15g\n陈皮 10g\n姜厚朴 10g\n山药 15g\n薏苡仁 15g\n升麻 15g\n垂盆草 15g",
    "exercise_prescription": "运动处方（4周计划）：\n\n## 第一周（适应期）\n- 运动类型：快走\n- 运动强度：低强度\n- 运动时长：每次30分钟...",
    "diagnosis_explanation": "根据患者症状分析：\n1. 肢体困重，懒言少动...",
    "response_time": 12.5,
    "model_name": "deepseek-chat"
  }
}
```

---

#### 步骤4：查询完整就诊记录

```bash
curl -X GET "http://localhost:8000/api/v1/medical-record/1"
```

---

#### 步骤5：查询患者历史记录

```bash
curl -X GET "http://localhost:8000/api/v1/patient/query?phone=13800138001"
```

**响应**：
```json
{
  "success": true,
  "message": "患者信息查询成功",
  "data": {
    "patient": {...},
    "medical_records": [
      {
        "record_id": 1,
        "uuid": "550e8400-e29b-41d4-a716-446655440001",
        "status": "completed",
        "created_at": "2024-01-22T10:00:00",
        "patient_name": "张三",
        "patient_phone": "13800138001"
      }
    ]
  }
}
```

---

## 常见问题

### 1. AI诊断失败

**问题**：调用AI诊断接口返回500错误

**解决方案**：
- 检查 `AI_API_KEY` 是否正确配置
- 检查 `AI_BASE_URL` 是否可访问
- 检查API密钥余额是否充足
- 查看应用日志：`docker-compose logs app`

### 2. 数据库连接失败

**问题**：启动时报数据库连接错误

**解决方案**：
```bash
# 检查数据库容器状态
docker-compose ps

# 重启数据库
docker-compose restart db

# 查看数据库日志
docker-compose logs db
```

### 3. UUID格式错误

**问题**：创建记录时提示UUID格式不正确

**解决方案**：
UUID必须符合v4格式：`xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`

使用在线工具生成：https://www.uuidgenerator.net/version4

或使用Python生成：
```python
import uuid
str(uuid.uuid4())
```

### 4. 手机号验证失败

**问题**：注册患者时提示手机号格式不正确

**解决方案**：
手机号必须符合以下规则：
- 11位数字
- 以1开头
- 例如：13800138001

### 5. AI诊断响应慢

**问题**：AI诊断需要很长时间

**说明**：
- 正常情况下AI诊断需要10-20秒
- 包括4个步骤：病历生成、证型判断、处方生成、运动处方生成
- 建议前端添加加载动画和提示

### 6. Docker容器无法启动

**问题**：执行 `docker-compose up` 后容器无法启动

**解决方案**：
```bash
# 查看详细日志
docker-compose logs

# 清理并重新构建
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```

### 7. 如何重置数据库

**问题**：需要清空所有数据

**解决方案**：
```bash
# 使用Docker
docker-compose down -v
docker-compose up -d

# 本地开发
dropdb ditan
createdb ditan
uv run python scripts/init_db.py
```

---

## 更多资源

- [完整API文档](API.md)
- [部署文档](DEPLOYMENT.md)
- [数据库管理](DATABASE.md)
- [更新日志](../CHANGELOG.md)

---

## 技术支持

如有问题，请查看：
1. 应用日志：`logs/app.log` 或 `docker-compose logs app`
2. GitHub Issues
3. 项目文档

---

**祝您使用愉快！** 🎉

