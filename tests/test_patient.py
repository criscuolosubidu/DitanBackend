"""
病人数据上传 API 测试
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_patient_success(client: AsyncClient):
    """测试成功创建病人数据"""
    patient_data = {
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
    
    response = await client.post("/api/v1/patient", json=patient_data)
    
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["message"] == "患者数据上传成功"
    assert data["data"]["uuid"] == patient_data["uuid"]
    assert data["data"]["phone"] == patient_data["phone"]
    assert data["data"]["name"] == patient_data["name"]


@pytest.mark.asyncio
async def test_create_patient_minimal(client: AsyncClient):
    """测试仅必填字段创建病人数据"""
    patient_data = {
        "uuid": "550e8400-e29b-41d4-a716-446655440001",
        "phone": "13800138002",
    }
    
    response = await client.post("/api/v1/patient", json=patient_data)
    
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["uuid"] == patient_data["uuid"]
    assert data["data"]["phone"] == patient_data["phone"]


@pytest.mark.asyncio
async def test_create_patient_invalid_uuid(client: AsyncClient):
    """测试无效的 UUID 格式"""
    patient_data = {
        "uuid": "invalid-uuid",
        "phone": "13800138003",
    }
    
    response = await client.post("/api/v1/patient", json=patient_data)
    
    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False


@pytest.mark.asyncio
async def test_create_patient_invalid_phone(client: AsyncClient):
    """测试无效的手机号"""
    patient_data = {
        "uuid": "550e8400-e29b-41d4-a716-446655440002",
        "phone": "12345678901",  # 无效手机号
    }
    
    response = await client.post("/api/v1/patient", json=patient_data)
    
    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False


@pytest.mark.asyncio
async def test_create_patient_duplicate_uuid(client: AsyncClient):
    """测试重复的 UUID"""
    patient_data = {
        "uuid": "550e8400-e29b-41d4-a716-446655440003",
        "phone": "13800138004",
    }
    
    # 第一次创建
    response1 = await client.post("/api/v1/patient", json=patient_data)
    assert response1.status_code == 201
    
    # 第二次创建（重复）
    response2 = await client.post("/api/v1/patient", json=patient_data)
    assert response2.status_code == 409
    data = response2.json()
    assert data["success"] is False
    assert "已存在" in data["message"]


@pytest.mark.asyncio
async def test_create_patient_invalid_sex(client: AsyncClient):
    """测试无效的性别"""
    patient_data = {
        "uuid": "550e8400-e29b-41d4-a716-446655440004",
        "phone": "13800138005",
        "sex": "未知",  # 无效性别
    }
    
    response = await client.post("/api/v1/patient", json=patient_data)
    
    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False


@pytest.mark.asyncio
async def test_create_patient_invalid_birthday(client: AsyncClient):
    """测试无效的出生日期格式"""
    patient_data = {
        "uuid": "550e8400-e29b-41d4-a716-446655440005",
        "phone": "13800138006",
        "birthday": "1985/05/20",  # 错误格式
    }
    
    response = await client.post("/api/v1/patient", json=patient_data)
    
    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """测试健康检查端点"""
    response = await client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient):
    """测试根端点"""
    response = await client.get("/")
    
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data

