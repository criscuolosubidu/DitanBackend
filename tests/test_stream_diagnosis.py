"""
流式AI诊断接口测试

此脚本可以作为:
1. pytest 单元测试运行: pytest tests/test_stream_diagnosis.py -v
2. 独立脚本手动测试: python tests/test_stream_diagnosis.py

独立运行时需要:
- 确保服务器已启动 (例如: uvicorn main:app --reload)
- 设置正确的 BASE_URL 和认证信息
"""
import asyncio
import json
from unittest.mock import Mock, patch

import pytest
from httpx import AsyncClient


# ========== Pytest 单元测试 ==========

@pytest.mark.asyncio
async def test_stream_diagnosis_success(client: AsyncClient, auth_headers: dict):
    """测试流式AI诊断成功返回"""
    # 先创建就诊记录
    record_data = {
        "uuid": "550e8400-e29b-41d4-a716-446655440100",
        "patient_phone": "13800138100",
        "patient_info": {
            "name": "流式诊断测试患者",
            "sex": "MALE",
            "birthday": "1985-01-01",
            "phone": "13800138100"
        },
        "pre_diagnosis": {
            "uuid": "660e8400-e29b-41d4-a716-446655440100",
            "height": 175.0,
            "weight": 85.0,
            "coze_conversation_log": "AI: 您好，请问您有什么不适？\nUser: 我最近感觉很疲劳。"
        }
    }

    create_response = await client.post("/api/v1/medical-record", json=record_data)
    assert create_response.status_code == 201
    record_id = create_response.json()["data"]["record_id"]

    # Mock 流式诊断服务
    async def mock_stream_diagnosis(*args, **kwargs):
        """模拟流式诊断生成器"""
        events = [
            'event: stage_start\ndata: {"stage": "medical_record", "stage_name": "生成病历", "step": "1/4"}\n\n',
            'event: content\ndata: {"stage": "medical_record", "chunk": "主诉："}\n\n',
            'event: content\ndata: {"stage": "medical_record", "chunk": "疲劳"}\n\n',
            'event: stage_complete\ndata: {"stage": "medical_record", "stage_name": "生成病历", "result": "主诉：疲劳\\n病史：..."}\n\n',
            'event: stage_start\ndata: {"stage": "diagnosis", "stage_name": "证型判断", "step": "2/4"}\n\n',
            'event: content\ndata: {"stage": "diagnosis", "chunk": "脾虚"}\n\n',
            'event: stage_complete\ndata: {"stage": "diagnosis", "stage_name": "证型判断", "result": "脾虚湿困型", "explanation": "患者疲劳..."}\n\n',
            'event: stage_start\ndata: {"stage": "prescription", "stage_name": "处方生成", "step": "3/4"}\n\n',
            'event: stage_complete\ndata: {"stage": "prescription", "stage_name": "处方生成", "result": "党参 10g..."}\n\n',
            'event: stage_start\ndata: {"stage": "exercise_prescription", "stage_name": "运动处方生成", "step": "4/4"}\n\n',
            'event: stage_complete\ndata: {"stage": "exercise_prescription", "stage_name": "运动处方生成", "result": "快走30分钟..."}\n\n',
            'event: complete\ndata: {"status": "success", "total_processing_time": 10.5, "formatted_medical_record": "主诉：疲劳", "type_inference": "脾虚湿困型", "diagnosis_explanation": "患者疲劳...", "prescription": "党参 10g...", "exercise_prescription": "快走30分钟..."}\n\n',
        ]
        for event in events:
            yield event
            await asyncio.sleep(0.01)

    with patch('app.api.patient.get_tcm_service') as mock_service:
        mock_instance = Mock()
        mock_instance.stream_complete_diagnosis = mock_stream_diagnosis
        mock_service.return_value = mock_instance

        diagnosis_data = {
            "asr_text": "医生：您好，请问有什么不舒服？\n患者：我最近感觉很疲劳，浑身没力气。"
        }

        # 发起流式请求
        async with client.stream(
                "POST",
                f"/api/v1/medical-record/{record_id}/ai-diagnosis/stream",
                json=diagnosis_data,
                headers=auth_headers
        ) as response:
            assert response.status_code == 200
            assert response.headers.get("content-type") == "text/event-stream; charset=utf-8"

            # 收集所有事件
            events = []
            async for line in response.aiter_lines():
                if line:
                    events.append(line)

            # 验证事件结构
            assert len(events) > 0

            # 解析事件
            event_types = []
            for i, line in enumerate(events):
                if line.startswith("event: "):
                    event_types.append(line[7:])

            # 验证包含关键事件类型
            assert "stage_start" in event_types
            assert "content" in event_types
            assert "stage_complete" in event_types
            assert "complete" in event_types


@pytest.mark.asyncio
async def test_stream_diagnosis_record_not_found(client: AsyncClient, auth_headers: dict):
    """测试流式诊断 - 就诊记录不存在"""
    diagnosis_data = {
        "asr_text": "测试对话内容..."
    }

    response = await client.post(
        "/api/v1/medical-record/99999/ai-diagnosis/stream",
        json=diagnosis_data,
        headers=auth_headers
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_stream_diagnosis_unauthorized(client: AsyncClient):
    """测试流式诊断 - 未认证"""
    diagnosis_data = {
        "asr_text": "测试对话内容..."
    }

    response = await client.post(
        "/api/v1/medical-record/1/ai-diagnosis/stream",
        json=diagnosis_data
    )

    assert response.status_code == 401


# ========== 独立脚本测试（手动测试用）==========

async def manual_test_stream_diagnosis():
    """
    手动测试流式诊断接口
    
    运行前请确保:
    1. 服务器已启动
    2. 修改下面的配置参数
    """
    import httpx

    # ============ 配置参数 ============
    BASE_URL = "http://localhost:8000"  # 修改为你的服务器地址

    # 医生登录信息（请根据实际情况修改）
    DOCTOR_USERNAME = "doctor_zhang"
    DOCTOR_PASSWORD = "password123"

    # 测试用的就诊记录ID（如果已有记录可直接使用，否则会自动创建）
    RECORD_ID = None  # 设为 None 表示自动创建

    # ASR转录文本
    ASR_TEXT = """医生：您好，请问有什么不舒服？
患者：我最近感觉很疲劳，浑身没力气，而且体重增加了不少。
医生：睡眠怎么样？
患者：睡眠还可以，但有时候会失眠。
医生：饮食呢？
患者：吃完饭后经常感觉腹胀，有时候还会便溏。
医生：有没有其他症状？
患者：肢体有些困重，不太想动。"""
    # ============ 配置结束 ============

    # 配置超时：connect=10秒, read=300秒（流式响应需要较长的读取超时）, write=30秒
    timeout_config = httpx.Timeout(
        connect=10.0,
        read=300.0,  # 读取超时设置长一些，因为LLM生成可能较慢
        write=30.0,
        pool=10.0
    )
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=timeout_config) as client:
        print("=" * 60)
        print("流式AI诊断接口测试")
        print("=" * 60)

        # 1. 医生登录获取token
        print("\n[1] 医生登录...")
        login_response = await client.post(
            "/api/v1/doctor/login",
            json={"username": DOCTOR_USERNAME, "password": DOCTOR_PASSWORD}
        )

        if login_response.status_code != 200:
            print(f"❌ 登录失败: {login_response.text}")
            print("提示: 请确保医生账号存在，或修改 DOCTOR_USERNAME 和 DOCTOR_PASSWORD")
            return

        token_data = login_response.json()
        access_token = token_data["data"]["access_token"]
        auth_headers = {"Authorization": f"Bearer {access_token}"}
        print(f"✅ 登录成功，医生: {token_data['data']['doctor']['name']}")

        # 2. 创建就诊记录（如果需要）
        record_id = RECORD_ID
        if record_id is None:
            print("\n[2] 创建测试就诊记录...")
            import uuid
            record_uuid = str(uuid.uuid4())
            pre_uuid = str(uuid.uuid4())

            record_data = {
                "uuid": record_uuid,
                "patient_phone": "13800138888",
                "patient_info": {
                    "name": "流式测试患者",
                    "sex": "MALE",
                    "birthday": "1985-05-20",
                    "phone": "13800138888"
                },
                "pre_diagnosis": {
                    "uuid": pre_uuid,
                    "height": 175.0,
                    "weight": 85.0,
                    "coze_conversation_log": "AI: 您好，请问您有什么不适？\nUser: 我最近感觉很疲劳，体重增加了。\nAI: 睡眠质量如何？\nUser: 有时会失眠。"
                }
            }

            create_response = await client.post("/api/v1/medical-record", json=record_data)
            if create_response.status_code != 201:
                print(f"❌ 创建就诊记录失败: {create_response.text}")
                return

            record_id = create_response.json()["data"]["record_id"]
            print(f"✅ 就诊记录创建成功，record_id: {record_id}")
        else:
            print(f"\n[2] 使用已有就诊记录，record_id: {record_id}")

        # 3. 调用流式诊断接口
        print("\n[3] 开始流式AI诊断...")
        print("-" * 60)

        diagnosis_data = {"asr_text": ASR_TEXT}

        current_stage = None
        current_content = ""

        async with client.stream(
                "POST",
                f"/api/v1/medical-record/{record_id}/ai-diagnosis/stream",
                json=diagnosis_data,
                headers=auth_headers
        ) as response:
            if response.status_code != 200:
                print(f"❌ 请求失败: {response.status_code}")
                content = await response.aread()
                print(content.decode())
                return

            print("✅ 连接成功，开始接收流式数据...\n")

            event_type = None
            event_data = None

            async for line in response.aiter_lines():
                line = line.strip()
                if not line:
                    # 空行表示事件结束，处理事件
                    if event_type and event_data:
                        try:
                            data = json.loads(event_data)

                            if event_type == "stage_start":
                                stage_name = data.get("stage_name", "")
                                step = data.get("step", "")
                                print(f"\n🔄 [{step}] {stage_name} 开始...")
                                current_stage = data.get("stage")
                                current_content = ""

                            elif event_type == "content":
                                chunk = data.get("chunk", "")
                                print(chunk, end="", flush=True)
                                current_content += chunk

                            elif event_type == "stage_complete":
                                stage_name = data.get("stage_name", "")
                                print(f"\n✅ {stage_name} 完成")

                                # 如果有提取的结果，显示
                                result = data.get("result")
                                if result and len(result) < 200:
                                    print(f"   结果: {result[:100]}...")

                            elif event_type == "complete":
                                print("\n" + "=" * 60)
                                print("🎉 诊断完成!")
                                print("=" * 60)
                                print(f"总耗时: {data.get('total_processing_time', 'N/A')}秒")
                                print(f"\n📋 病历摘要:")
                                print(data.get('formatted_medical_record', 'N/A')[:200] + "...")
                                print(f"\n🔍 证型判断: {data.get('type_inference', 'N/A')}")
                                print(f"\n💊 处方摘要:")
                                print(data.get('prescription', 'N/A')[:200] + "...")
                                print(f"\n🏃 运动处方摘要:")
                                print(data.get('exercise_prescription', 'N/A')[:200] + "...")

                            elif event_type == "saved":
                                diagnosis_id = data.get("diagnosis_id")
                                print(f"\n💾 诊断记录已保存，diagnosis_id: {diagnosis_id}")

                            elif event_type == "error":
                                print(f"\n❌ 错误: {data.get('message', '未知错误')}")

                            elif event_type == "save_error":
                                print(f"\n⚠️ 保存失败: {data.get('message', '未知错误')}")

                        except json.JSONDecodeError as e:
                            print(f"JSON解析错误: {e}")

                    # 重置
                    event_type = None
                    event_data = None
                    continue

                if line.startswith("event: "):
                    event_type = line[7:]
                elif line.startswith("data: "):
                    event_data = line[6:]

        print("\n" + "=" * 60)
        print("测试完成!")
        print("=" * 60)


def run_manual_test():
    """运行手动测试"""
    asyncio.run(manual_test_stream_diagnosis())


if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════╗
║           流式AI诊断接口测试脚本                              ║
╠══════════════════════════════════════════════════════════════╣
║  使用方法:                                                    ║
║  1. 确保后端服务已启动                                        ║
║  2. 根据需要修改脚本中的配置参数:                             ║
║     - BASE_URL: 服务器地址                                    ║
║     - DOCTOR_USERNAME/PASSWORD: 医生登录信息                  ║
║     - RECORD_ID: 就诊记录ID (设为None自动创建)                ║
║     - ASR_TEXT: ASR转录文本                                   ║
║  3. 运行此脚本: python tests/test_stream_diagnosis.py         ║
╚══════════════════════════════════════════════════════════════╝
    """)
    run_manual_test()
