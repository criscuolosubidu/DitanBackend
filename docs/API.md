# API 文档

## 概述

DitanBackend 是一个病人数据上传后端服务，提供了 RESTful API 接口用于接收和存储患者的四诊信息。

**基础 URL**: `http://your-domain:8000/api/v1`

**API 版本**: v1

---

## 通用响应格式

### 成功响应

```json
{
  "success": true,
  "message": "操作成功消息",
  "data": {
    // 响应数据
  }
}
```

### 错误响应

```json
{
  "success": false,
  "message": "错误消息",
  "detail": "错误详情（仅在调试模式下显示）"
}
```

### HTTP 状态码

- `200 OK` - 请求成功
- `201 Created` - 创建成功
- `400 Bad Request` - 请求参数错误
- `404 Not Found` - 资源未找到
- `409 Conflict` - 资源冲突（如重复数据）
- `500 Internal Server Error` - 服务器内部错误

---

## API 端点

### 1. 健康检查

**端点**: `GET /health`

**描述**: 检查服务健康状态

**响应示例**:
```json
{
  "status": "healthy",
  "service": "DitanBackend",
  "version": "0.1.0"
}
```

---

### 2. 根路径

**端点**: `GET /`

**描述**: 获取服务基本信息

**响应示例**:
```json
{
  "message": "欢迎使用 DitanBackend",
  "version": "0.1.0",
  "docs": "/docs"
}
```

---

### 3. 创建患者数据

**端点**: `POST /api/v1/patient`

**描述**: 上传患者的基本信息和四诊分析结果

**Content-Type**: `application/json`

#### 请求参数

| 字段名 | 类型 | 必填 | 描述 | 示例 |
|--------|------|------|------|------|
| `uuid` | String | **是** | 客户端生成的唯一标识符（UUID v4） | "550e8400-e29b-41d4-a716-446655440000" |
| `phone` | String | **是** | 患者的11位手机号 | "13800138001" |
| `name` | String | 否 | 患者姓名 | "张三" |
| `sex` | String | 否 | 患者性别（"男" 或 "女"） | "男" |
| `birthday` | String | 否 | 出生日期（格式: YYYY-MM-DD） | "1985-05-20" |
| `height` | String | 否 | 身高（cm） | "175" |
| `weight` | String | 否 | 体重（kg） | "70" |
| `analysisResults` | Object | 否 | 四诊分析结果 | 见下方 |
| `analysisResults.face` | String | 否 | 面诊分析结果 | "面色略黄..." |
| `analysisResults.tongueFront` | String | 否 | 舌诊（正面）分析结果 | "舌体偏胖..." |
| `analysisResults.tongueBottom` | String | 否 | 舌诊（舌下）分析结果 | "舌下络脉..." |
| `analysisResults.pulse` | String | 否 | 脉诊分析结果 | "脉象沉细..." |
| `cozeConversationLog` | String | 否 | 与数字人完整的对话记录 | "USER: 你好\nAI: ..." |

#### 请求示例

```json
{
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
  "cozeConversationLog": "USER: 你好\nAI: 你好，请问有什么可以帮您？\n..."
}
```

#### 最小请求示例（仅必填字段）

```json
{
  "uuid": "550e8400-e29b-41d4-a716-446655440000",
  "phone": "13800138001"
}
```

#### 成功响应 (201 Created)

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
    "coze_conversation_log": "USER: 你好\nAI: 你好，请问有什么可以帮您？\n...",
    "created_at": "2024-01-15T10:30:00",
    "updated_at": "2024-01-15T10:30:00"
  }
}
```

#### 错误响应

**UUID 格式错误 (400 Bad Request)**
```json
{
  "success": false,
  "message": "请求参数验证失败",
  "detail": "uuid: UUID 格式不正确"
}
```

**手机号格式错误 (400 Bad Request)**
```json
{
  "success": false,
  "message": "请求参数验证失败",
  "detail": "phone: 手机号格式不正确"
}
```

**性别格式错误 (400 Bad Request)**
```json
{
  "success": false,
  "message": "请求参数验证失败",
  "detail": "sex: 性别只能是 '男' 或 '女'"
}
```

**UUID 重复 (409 Conflict)**
```json
{
  "success": false,
  "message": "患者 UUID 550e8400-e29b-41d4-a716-446655440000 已存在",
  "detail": null
}
```

**数据库错误 (500 Internal Server Error)**
```json
{
  "success": false,
  "message": "创建患者记录时发生错误",
  "detail": "详细错误信息（仅调试模式）"
}
```

---

## 数据验证规则

### UUID
- 必须符合 UUID v4 格式
- 格式: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`（小写或大写十六进制字符）
- 示例: `550e8400-e29b-41d4-a716-446655440000`

### 手机号
- 必须是11位数字
- 必须以 1 开头，第二位为 3-9
- 示例: `13800138001`

### 性别
- 只能是 "男" 或 "女"

### 出生日期
- 格式必须为 `YYYY-MM-DD`
- 示例: `1985-05-20`

---

## 使用示例

### cURL 示例

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

### Python 示例

```python
import requests
import json

url = "http://localhost:8000/api/v1/patient"
data = {
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
}

response = requests.post(url, json=data)
print(response.status_code)
print(json.dumps(response.json(), indent=2, ensure_ascii=False))
```

### JavaScript (Fetch) 示例

```javascript
const url = "http://localhost:8000/api/v1/patient";
const data = {
  uuid: "550e8400-e29b-41d4-a716-446655440000",
  phone: "13800138001",
  name: "张三",
  sex: "男",
  birthday: "1985-05-20",
  height: "175",
  weight: "70",
  analysisResults: {
    face: "面色略黄，唇色偏淡，有轻微黑眼圈。",
    tongueFront: "舌体偏胖，舌苔薄白，边有齿痕。",
    tongueBottom: "舌下络脉颜色正常，无明显瘀滞。",
    pulse: "脉象沉细，左手关脉较弱。"
  },
  cozeConversationLog: "USER: 你好\nAI: 你好，请问有什么可以帮您？"
};

fetch(url, {
  method: "POST",
  headers: {
    "Content-Type": "application/json"
  },
  body: JSON.stringify(data)
})
  .then(response => response.json())
  .then(data => console.log(data))
  .catch(error => console.error("Error:", error));
```

---

## 交互式 API 文档

服务启动后，可以访问以下地址查看交互式 API 文档：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

这些页面提供了可视化的 API 文档，并且可以直接在浏览器中测试 API。

---

## 注意事项

1. **UUID 唯一性**: 每个患者的 UUID 必须是唯一的，重复提交相同的 UUID 会返回 409 错误
2. **手机号验证**: 手机号必须符合中国大陆手机号格式（11位，以1开头）
3. **日期格式**: 出生日期必须严格遵循 YYYY-MM-DD 格式
4. **字段可选性**: 除了 uuid 和 phone 之外，所有字段都是可选的
5. **日志记录**: 所有请求和响应都会被记录到日志文件中
6. **错误处理**: 服务使用自定义异常，不会暴露详细的堆栈跟踪（除非在调试模式下）

