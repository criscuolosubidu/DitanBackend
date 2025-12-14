# 快速上手指南

本指南将帮助你快速了解和使用DitanBackend系统，特别是新增的医生管理功能。

## 目录

- [系统概述](#系统概述)
- [医生功能快速上手](#医生功能快速上手)
- [患者管理快速上手](#患者管理快速上手)
- [完整工作流程示例](#完整工作流程示例)

## 系统概述

DitanBackend 是一个中医智能诊疗系统后端服务，主要功能包括：

1. **医生管理** (v2.0.0新增)
    - 医生注册和登录
    - JWT认证保障系统安全
    - 医生信息管理

2. **患者管理**
    - 患者信息录入
    - 历史就诊记录查询

3. **就诊流程管理**
    - 预诊信息记录
    - 就诊记录管理

4. **AI辅助诊断**
    - 自动生成病历
    - 智能证型判断
    - 个性化处方生成
    - 运动处方生成

## 医生功能快速上手

### 1. 医生注册

医生首次使用系统需要先注册账户。

**API端点**: `POST /api/v1/doctor/register`

**请求示例**:

```bash
curl -X POST "http://localhost:8000/api/v1/doctor/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "doctor_zhang",
    "password": "secure_password123",
    "name": "张医生",
    "gender": "MALE",
    "phone": "13800138000",
    "department": "中医科",
    "position": "主治医师",
    "bio": "从事中医临床工作10年，擅长中医体质辨识和调理"
  }'
```

**响应示例**:

```json
{
  "success": true,
  "message": "医生注册成功",
  "data": {
    "doctor_id": 1,
    "username": "doctor_zhang",
    "name": "张医生",
    "gender": "MALE",
    "phone": "13800138000",
    "department": "中医科",
    "position": "主治医师",
    "bio": "从事中医临床工作10年，擅长中医体质辨识和调理",
    "created_at": "2024-01-15T10:00:00",
    "updated_at": "2024-01-15T10:00:00",
    "last_login": null
  }
}
```

**注意事项**:

- 用户名只能包含字母、数字和下划线
- 密码至少6位
- 手机号必须是有效的中国大陆手机号（11位，以1开头）
- 用户名和手机号不能重复

### 2. 医生登录

注册后，医生可以使用用户名和密码登录。

**API端点**: `POST /api/v1/doctor/login`

**请求示例**:

```bash
curl -X POST "http://localhost:8000/api/v1/doctor/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "doctor_zhang",
    "password": "secure_password123"
  }'
```

**响应示例**:

```json
{
  "success": true,
  "message": "登录成功",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "doctor": {
      "doctor_id": 1,
      "username": "doctor_zhang",
      "name": "张医生",
      "gender": "MALE",
      "phone": "13800138000",
      "department": "中医科",
      "position": "主治医师",
      "bio": "从事中医临床工作10年，擅长中医体质辨识和调理",
      "created_at": "2024-01-15T10:00:00",
      "updated_at": "2024-01-15T10:00:00",
      "last_login": "2024-01-15T14:00:00"
    }
  }
}
```

**重要**: 保存返回的 `access_token`，后续需要认证的操作都需要携带这个令牌。

### 3. 使用JWT令牌访问受保护的API

登录成功后，在需要认证的请求中携带JWT令牌：

```bash
curl -X GET "http://localhost:8000/api/v1/doctor/me" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**令牌有效期**: 默认24小时（可在环境变量中配置）

### 4. 查看和更新医生信息

#### 查看当前医生信息

**API端点**: `GET /api/v1/doctor/me`

```bash
curl -X GET "http://localhost:8000/api/v1/doctor/me" \
  -H "Authorization: Bearer <your_access_token>"
```

#### 更新医生信息

**API端点**: `PUT /api/v1/doctor/me`

```bash
curl -X PUT "http://localhost:8000/api/v1/doctor/me" \
  -H "Authorization: Bearer <your_access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "张伟",
    "position": "副主任医师",
    "bio": "从事中医临床工作15年，擅长中医体质辨识、调理和运动康复"
  }'
```

**注意**: username不能修改

### 5. 修改密码

**API端点**: `POST /api/v1/doctor/change-password`

```bash
curl -X POST "http://localhost:8000/api/v1/doctor/change-password" \
  -H "Authorization: Bearer <your_access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "old_password": "secure_password123",
    "new_password": "new_secure_password456"
  }'
```

修改密码后需要重新登录获取新的JWT令牌。

## 患者管理快速上手

### 1. 查询患者信息

医生在诊室接诊时，可以通过患者手机号查询患者信息和历史就诊记录。

**API端点**: `GET /api/v1/patient/query`

```bash
curl -X GET "http://localhost:8000/api/v1/patient/query?phone=13800138001"
```

**响应示例**:

```json
{
  "success": true,
  "message": "患者信息查询成功",
  "data": {
    "patient": {
      "patient_id": 1,
      "name": "张三",
      "sex": "MALE",
      "birthday": "1985-05-20",
      "phone": "13800138001"
    },
    "medical_records": [
      {
        "record_id": 1,
        "uuid": "550e8400-e29b-41d4-a716-446655440001",
        "status": "completed",
        "created_at": "2024-01-01T10:00:00",
        "patient_name": "张三",
        "patient_phone": "13800138001"
      }
    ]
  }
}
```

### 2. 创建就诊记录

就诊记录通常由预就诊系统创建。如果患者是首次就诊，系统会自动创建患者记录。

**API端点**: `POST /api/v1/medical-record`

```bash
curl -X POST "http://localhost:8000/api/v1/medical-record" \
  -H "Content-Type: application/json" \
  -d '{
    "uuid": "550e8400-e29b-41d4-a716-446655440001",
    "patient_phone": "13800138001",
    "patient_info": {
      "name": "张三",
      "sex": "MALE",
      "birthday": "1985-05-20",
      "phone": "13800138001"
    },
    "pre_diagnosis": {
      "uuid": "660e8400-e29b-41d4-a716-446655440001",
      "height": 175.0,
      "weight": 80.0,
      "coze_conversation_log": "患者与数字人的对话记录...",
      "sanzhen_analysis": {
        "face": "面色略黄，唇色偏淡",
        "tongue_front": "舌体偏胖，舌苔薄白",
        "tongue_bottom": "舌下络脉正常",
        "pulse": "脉象沉细",
        "diagnosis_result": "初步判断为脾虚湿困"
      }
    }
  }'
```

### 3. 获取就诊记录详情

**API端点**: `GET /api/v1/medical-record/{record_id}`

```bash
curl -X GET "http://localhost:8000/api/v1/medical-record/1"
```

### 4. 生成AI诊断

医患对话后，可以生成AI辅助诊断建议。

**API端点**: `POST /api/v1/medical-record/{record_id}/ai-diagnosis`

```bash
curl -X POST "http://localhost:8000/api/v1/medical-record/1/ai-diagnosis" \
  -H "Content-Type: application/json" \
  -d '{
    "asr_text": "医生：您好，请问有什么不舒服？\n患者：我最近体重增加了很多，感觉身体很沉重，特别容易疲劳。平时也不怎么想吃东西，但体重反而增加了。\n医生：除了这些，还有其他症状吗？\n患者：有时候会觉得四肢困重，不想动，而且饭后容易腹胀。"
  }'
```

**AI诊断包含**:

- 格式化的中医病历
- 证型推断（脾虚湿困型/胃热燔脾型/气滞血瘀型/脾肾阳虚型）
- 个性化中药处方
- 4周运动处方计划

## 完整工作流程示例

以下是一个完整的就诊流程，包含医生登录、患者查询、AI诊断等步骤。

### 步骤1: 医生登录

```bash
# 登录
LOGIN_RESPONSE=$(curl -X POST "http://localhost:8000/api/v1/doctor/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "doctor_zhang",
    "password": "secure_password123"
  }')

# 提取access_token (使用jq工具)
ACCESS_TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.data.access_token')
echo "Access Token: $ACCESS_TOKEN"
```

### 步骤2: 患者到达诊室，扫码或输入手机号

```bash
# 查询患者信息和历史记录
curl -X GET "http://localhost:8000/api/v1/patient/query?phone=13800138001"
```

### 步骤3: 查看预诊信息

```bash
# 假设从步骤2得到 record_id = 1
curl -X GET "http://localhost:8000/api/v1/medical-record/1"
```

### 步骤4: 医患对话后，生成AI诊断

```bash
curl -X POST "http://localhost:8000/api/v1/medical-record/1/ai-diagnosis" \
  -H "Content-Type: application/json" \
  -d '{
    "asr_text": "医生：您好，请问有什么不舒服？\n患者：我最近体重增加了很多..."
  }'
```

### 步骤5: 医生查看AI诊断建议，调整后确认

```bash
# 再次查看完整就诊记录（包含AI诊断）
curl -X GET "http://localhost:8000/api/v1/medical-record/1"
```

## 使用Swagger UI测试

访问 http://localhost:8000/docs 可以使用Swagger UI进行交互式测试。

### 在Swagger UI中使用认证

1. 登录获取access_token
2. 点击页面右上角的 "Authorize" 按钮
3. 在弹出框中输入: `Bearer <your_access_token>`
4. 点击 "Authorize" 完成认证
5. 现在可以测试需要认证的API端点

## 常见问题

### Q: JWT令牌过期了怎么办？

A: 重新登录获取新的令牌。默认有效期是24小时。

### Q: 忘记密码怎么办？

A: 目前系统没有密码找回功能。开发环境下可以直接在数据库中修改密码哈希，或者联系管理员。

### Q: 可以同时登录多个设备吗？

A: 可以。每次登录都会生成新的JWT令牌，多个令牌可以同时有效。

### Q: 医生可以查看其他医生的诊断记录吗？

A: 可以。目前所有医生都可以查看所有就诊记录，但创建医生诊断记录时会记录操作医生的ID。

### Q: 如何区分AI诊断和医生诊断？

A: 诊断记录的 `type` 字段标识类型：

- `AI_DIAGNOSIS`: AI诊断
- `DOCTOR_DIAGNOSIS`: 医生诊断

医生诊断记录会包含医生ID和备注。

## 开发提示

### 环境变量配置

在开发环境中，建议在 `.env` 文件中配置：

```env
# 开发环境使用DEBUG模式
APP_DEBUG=True

# 使用较短的令牌过期时间方便测试
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60

# 开发环境使用简单的密钥（生产环境必须修改）
JWT_SECRET_KEY=dev-secret-key-change-in-production
```

### 测试数据创建

可以使用以下脚本快速创建测试数据：

```python
# test_data.py
import asyncio
from httpx import AsyncClient

async def create_test_data():
    async with AsyncClient(base_url="http://localhost:8000") as client:
        # 1. 注册医生
        doctor_response = await client.post("/api/v1/doctor/register", json={
            "username": "test_doctor",
            "password": "test123",
            "name": "测试医生",
            "gender": "MALE",
            "phone": "13900000001"
        })
        print("医生注册:", doctor_response.json())
        
        # 2. 登录
        login_response = await client.post("/api/v1/doctor/login", json={
            "username": "test_doctor",
            "password": "test123"
        })
        token = login_response.json()["data"]["access_token"]
        print("登录成功, Token:", token[:20] + "...")
        
        # 3. 创建患者和就诊记录
        # ... 省略

if __name__ == "__main__":
    asyncio.run(create_test_data())
```

## 下一步

- 阅读完整的 [API文档](API.md)
- 了解 [数据库结构](DATABASE.md)
- 查看 [部署指南](DEPLOYMENT.md)
- 运行单元测试: `uv run pytest`

## 获取帮助

如有问题，请查看：

- [README.md](../README.md) - 项目概述和安装指南
- [API.md](API.md) - 完整的API文档
- GitHub Issues - 提交问题和建议
