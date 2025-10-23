"""
病人和诊断相关 API 测试
"""
import pytest
from datetime import date
from httpx import AsyncClient
from unittest.mock import Mock, patch


# ========== 患者查询测试 ==========
@pytest.mark.asyncio
async def test_query_patient_success(client: AsyncClient):
    """测试成功查询患者信息"""
    # 先注册一个患者
    qrcode_data = {
        "card_number": "CARD001",
        "name": "张三",
        "phone": "13800138001",
        "gender": "Male",
        "birthday": "1985-05-20",
        "target_weight": "70"
    }
    
    register_response = await client.post("/api/v1/patient/register", json=qrcode_data)
    assert register_response.status_code == 201
    
    # 查询患者
    response = await client.get("/api/v1/patient/query?phone=13800138001")
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["patient"]["phone"] == "13800138001"
    assert data["data"]["patient"]["name"] == "张三"
    assert isinstance(data["data"]["medical_records"], list)


@pytest.mark.asyncio
async def test_query_patient_not_found(client: AsyncClient):
    """测试查询不存在的患者"""
    response = await client.get("/api/v1/patient/query?phone=13800138999")
    
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert "未找到" in data["message"]


# ========== 患者注册测试 ==========
@pytest.mark.asyncio
async def test_register_patient_success(client: AsyncClient):
    """测试成功注册患者"""
    qrcode_data = {
        "card_number": "CARD002",
        "name": "李四",
        "phone": "13800138002",
        "gender": "Female",
        "birthday": "1990-06-15",
        "target_weight": "60"
    }
    
    response = await client.post("/api/v1/patient/register", json=qrcode_data)
    
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["phone"] == "13800138002"
    assert data["data"]["name"] == "李四"


@pytest.mark.asyncio
async def test_register_patient_duplicate(client: AsyncClient):
    """测试注册重复患者"""
    qrcode_data = {
        "card_number": "CARD003",
        "name": "王五",
        "phone": "13800138003",
        "gender": "Male",
        "birthday": "1988-08-08"
    }
    
    # 第一次注册
    response1 = await client.post("/api/v1/patient/register", json=qrcode_data)
    assert response1.status_code == 201
    
    # 第二次注册（重复）
    response2 = await client.post("/api/v1/patient/register", json=qrcode_data)
    assert response2.status_code == 409
    data = response2.json()
    assert data["success"] is False
    assert "已注册" in data["message"]


@pytest.mark.asyncio
async def test_register_patient_invalid_phone(client: AsyncClient):
    """测试无效手机号注册"""
    qrcode_data = {
        "card_number": "CARD004",
        "name": "赵六",
        "phone": "12345678901",  # 无效手机号
        "gender": "Male",
        "birthday": "1992-01-01"
    }
    
    response = await client.post("/api/v1/patient/register", json=qrcode_data)
    
    assert response.status_code == 400


# ========== 创建就诊记录测试 ==========
@pytest.mark.asyncio
async def test_create_medical_record_new_patient(client: AsyncClient):
    """测试为新患者创建就诊记录"""
    record_data = {
        "uuid": "550e8400-e29b-41d4-a716-446655440001",
        "patient_phone": "13800138010",
        "patient_info": {
            "name": "新患者",
            "sex": "Male",
            "birthday": "1985-01-01",
            "phone": "13800138010"
        },
        "pre_diagnosis": {
            "uuid": "660e8400-e29b-41d4-a716-446655440001",
            "height": 175.0,
            "weight": 80.0,
            "coze_conversation_log": "患者：我最近体重增加了...",
            "sanzhen_analysis": {
                "face": "面色略黄",
                "tongue_front": "舌苔薄白",
                "tongue_bottom": "舌下正常",
                "pulse": "脉象沉细"
            }
        }
    }
    
    response = await client.post("/api/v1/medical-record", json=record_data)
    
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["uuid"] == "550e8400-e29b-41d4-a716-446655440001"
    assert data["data"]["patient"]["phone"] == "13800138010"


@pytest.mark.asyncio
async def test_create_medical_record_existing_patient(client: AsyncClient):
    """测试为现有患者创建就诊记录"""
    # 先注册患者
    qrcode_data = {
        "card_number": "CARD005",
        "name": "老患者",
        "phone": "13800138011",
        "gender": "Female",
        "birthday": "1990-01-01"
    }
    
    register_response = await client.post("/api/v1/patient/register", json=qrcode_data)
    assert register_response.status_code == 201
    
    # 创建就诊记录
    record_data = {
        "uuid": "550e8400-e29b-41d4-a716-446655440002",
        "patient_phone": "13800138011",
        "pre_diagnosis": {
            "uuid": "660e8400-e29b-41d4-a716-446655440002",
            "height": 160.0,
            "weight": 55.0
        }
    }
    
    response = await client.post("/api/v1/medical-record", json=record_data)
    
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["patient"]["name"] == "老患者"


@pytest.mark.asyncio
async def test_create_medical_record_duplicate_uuid(client: AsyncClient):
    """测试创建重复UUID的就诊记录"""
    # 先注册患者
    qrcode_data = {
        "card_number": "CARD006",
        "name": "测试患者",
        "phone": "13800138012",
        "gender": "Male",
        "birthday": "1985-01-01"
    }
    
    await client.post("/api/v1/patient/register", json=qrcode_data)
    
    record_data = {
        "uuid": "550e8400-e29b-41d4-a716-446655440003",
        "patient_phone": "13800138012",
        "pre_diagnosis": {
            "uuid": "660e8400-e29b-41d4-a716-446655440003",
            "height": 170.0,
            "weight": 70.0
        }
    }
    
    # 第一次创建
    response1 = await client.post("/api/v1/medical-record", json=record_data)
    assert response1.status_code == 201
    
    # 第二次创建（重复UUID）
    response2 = await client.post("/api/v1/medical-record", json=record_data)
    assert response2.status_code == 409


# ========== 查询就诊记录测试 ==========
@pytest.mark.asyncio
async def test_get_medical_record_success(client: AsyncClient):
    """测试成功查询就诊记录"""
    # 先创建就诊记录
    record_data = {
        "uuid": "550e8400-e29b-41d4-a716-446655440004",
        "patient_phone": "13800138013",
        "patient_info": {
            "name": "查询测试",
            "sex": "Male",
            "birthday": "1985-01-01",
            "phone": "13800138013"
        },
        "pre_diagnosis": {
            "uuid": "660e8400-e29b-41d4-a716-446655440004",
            "height": 175.0,
            "weight": 80.0
        }
    }
    
    create_response = await client.post("/api/v1/medical-record", json=record_data)
    assert create_response.status_code == 201
    record_id = create_response.json()["data"]["record_id"]
    
    # 查询就诊记录
    response = await client.get(f"/api/v1/medical-record/{record_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["record_id"] == record_id
    assert data["data"]["patient"]["phone"] == "13800138013"
    assert data["data"]["pre_diagnosis"] is not None


@pytest.mark.asyncio
async def test_get_medical_record_not_found(client: AsyncClient):
    """测试查询不存在的就诊记录"""
    response = await client.get("/api/v1/medical-record/99999")
    
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False


# ========== AI诊断测试 ==========
@pytest.mark.asyncio
async def test_create_ai_diagnosis_success(client: AsyncClient):
    """测试成功创建AI诊断"""
    # 先创建就诊记录
    record_data = {
        "uuid": "550e8400-e29b-41d4-a716-446655440005",
        "patient_phone": "13800138014",
        "patient_info": {
            "name": "AI诊断测试",
            "sex": "Male",
            "birthday": "1985-01-01",
            "phone": "13800138014"
        },
        "pre_diagnosis": {
            "uuid": "660e8400-e29b-41d4-a716-446655440005",
            "height": 175.0,
            "weight": 85.0
        }
    }
    
    create_response = await client.post("/api/v1/medical-record", json=record_data)
    assert create_response.status_code == 201
    record_id = create_response.json()["data"]["record_id"]
    
    # Mock TCM诊断服务
    mock_diagnosis_result = {
        "overall_status": "success",
        "medical_record_result": {
            "medical_record": "主诉：体重增加\n病史：身高175cm，体重85kg..."
        },
        "diagnosis_result": {
            "diagnosis": "脾虚湿困型",
            "diagnosis_explanation": "患者肢体困重，懒言少动..."
        },
        "prescription_result": {
            "prescription": "党参 10g\n麸炒白术 15g\n茯苓 15g..."
        },
        "exercise_prescription_result": {
            "exercise_prescription": "第一周：快走30分钟，每周5次..."
        },
        "total_processing_time": 10.5
    }
    
    with patch('app.api.patient.get_tcm_service') as mock_service:
        mock_instance = Mock()
        mock_instance.process_complete_diagnosis.return_value = mock_diagnosis_result
        mock_service.return_value = mock_instance
        
        # 创建AI诊断
        diagnosis_data = {
            "asr_text": "医生：您好，请问有什么不舒服？\n患者：我最近体重增加了很多..."
        }
        
        response = await client.post(
            f"/api/v1/medical-record/{record_id}/ai-diagnosis",
            json=diagnosis_data
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["type_inference"] == "脾虚湿困型"
        assert data["data"]["prescription"] is not None
        assert data["data"]["exercise_prescription"] is not None


@pytest.mark.asyncio
async def test_create_ai_diagnosis_record_not_found(client: AsyncClient):
    """测试为不存在的就诊记录创建AI诊断"""
    diagnosis_data = {
        "asr_text": "测试对话内容..."
    }
    
    response = await client.post(
        "/api/v1/medical-record/99999/ai-diagnosis",
        json=diagnosis_data
    )
    
    assert response.status_code == 404


# ========== 健康检查测试 ==========
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

