"""
中医诊断服务
"""
import json
import re
import time
from typing import Dict, Any, Optional, AsyncGenerator, List, cast

from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionUserMessageParam,
)

from app.core.logging import get_logger
from app.services.openai_client import OpenAIChatCompletion
from app.services.prompt_templates import (
    MEDICAL_RECORD_PROMPT_TEMPLATE,
    TYPE_INFER_PROMPT_TEMPLATE,
    PRESCRIPTION_PROMPT_TEMPLATE,
    EXERCISE_PRESCRIPTION_PROMPT_TEMPLATE
)

logger = get_logger(__name__)


# 流式诊断阶段定义
class DiagnosisStage:
    MEDICAL_RECORD = "medical_record"
    DIAGNOSIS = "diagnosis"
    PRESCRIPTION = "prescription"
    EXERCISE_PRESCRIPTION = "exercise_prescription"


class TCMDiagnosisService:
    """
    中医诊疗服务
    提供病历生成、证型判断、处方生成和运动处方生成的完整诊疗流程
    """

    def __init__(self, api_key: str, base_url: str, model_name: str = 'deepseek-chat'):
        """
        初始化中医诊疗服务
        
        Args:
            api_key (str): OpenAI API密钥
            base_url (str): API基础URL
            model_name (str): 模型名称
        """
        self.llm = OpenAIChatCompletion(api_key, base_url, model_name)
        self.model_name = model_name
        logger.info(f"中医诊疗服务初始化成功，模型: {model_name}")

    def extract_answer_from_response(self, response: str) -> str:
        """
        从LLM响应中提取<answer>标签中的内容
        
        Args:
            response (str): LLM的完整响应
            
        Returns:
            str: 提取的答案内容
        """
        answer_pattern = r'<answer>(.*?)</answer>'
        match = re.search(answer_pattern, response, re.DOTALL | re.IGNORECASE)

        if match:
            answer = match.group(1).strip()
            return answer
        else:
            logger.warning("未找到<answer>标签，返回完整响应")
            return response.strip()

    def extract_think_from_response(self, response: str) -> Optional[str]:
        """
        从LLM响应中提取<think>标签中的内容
        
        Args:
            response (str): LLM的完整响应
            
        Returns:
            Optional[str]: 提取的思考过程内容
        """
        think_pattern = r'<think>(.*?)</think>'
        match = re.search(think_pattern, response, re.DOTALL | re.IGNORECASE)

        if match:
            think = match.group(1).strip()
            return think
        return None

    def generate_medical_record_from_transcript_and_coze_conversation(self, transcript: str,
                                                                      coze_conversation_log: str) -> Dict[str, Any]:
        """
        从预问诊和对话转录文本生成病历
        
        Args:
            transcript (str): 对话转录文本
            coze_conversation_log(Dict[str, Any]): AI预问诊对话记录，需要拼接。
        Returns:
            Dict[str, Any]: 包含病历内容和状态的字典
        """
        try:
            logger.info("开始生成病历...")

            # 构建最终的prompt
            final_prompt = MEDICAL_RECORD_PROMPT_TEMPLATE.format(transcript=transcript,
                                                                 log_string=coze_conversation_log)

            # 调用LLM生成病历
            start_time = time.time()

            # 直接调用非流式API
            medical_record = self.llm.simple_chat(
                user_message=final_prompt,
                temperature=0.6
            )

            end_time = time.time()
            duration = round(end_time - start_time, 2)

            # 提取答案
            extracted_medical_record = self.extract_answer_from_response(medical_record)

            logger.info(f"病历生成完成，耗时: {duration}s")

            return {
                "input_transcript": transcript,
                "medical_record": extracted_medical_record,
                "llm_response": medical_record,
                "status": "success",
                "processing_time": duration,
                "timestamp": time.time()
            }

        except Exception as e:
            logger.error(f"病历生成出错: {str(e)}", exc_info=True)
            return {
                "input_transcript": transcript,
                "medical_record": None,
                "status": "error",
                "error_message": str(e),
                "timestamp": time.time()
            }

    def judge_symptom_type(self, medical_record: str) -> Dict[str, Any]:
        """
        对病历进行证型判断
        
        Args:
            medical_record (str): 格式化的病历文本
            
        Returns:
            Dict[str, Any]: 包含证型判断结果的字典
        """
        try:
            logger.info("开始进行证型判断...")

            # 使用模板格式化提示词
            prompt = TYPE_INFER_PROMPT_TEMPLATE.format(medical_record=medical_record)

            # 调用LLM进行判断
            start_time = time.time()

            # 直接调用非流式API
            response = self.llm.simple_chat(
                user_message=prompt,
                temperature=0.3
            )

            end_time = time.time()
            duration = round(end_time - start_time, 2)

            # 提取答案
            diagnosis_result = self.extract_answer_from_response(response)
            diagnosis_explanation = self.extract_think_from_response(response)

            logger.info(f"证型判断完成: {diagnosis_result}，耗时: {duration}s")

            return {
                "input_medical_record": medical_record,
                "diagnosis": diagnosis_result,
                "diagnosis_explanation": diagnosis_explanation,
                "llm_response": response,
                "status": "success",
                "processing_time": duration,
                "timestamp": time.time()
            }

        except Exception as e:
            logger.error(f"证型判断出错: {str(e)}", exc_info=True)
            return {
                "input_medical_record": medical_record,
                "diagnosis": None,
                "status": "error",
                "error_message": str(e),
                "timestamp": time.time()
            }

    def generate_prescription(self, medical_record: str, diagnosis_result: str) -> Dict[str, Any]:
        """
        根据病历和证型判断结果生成处方
        
        Args:
            medical_record (str): 格式化的病历文本
            diagnosis_result (str): 证型判断结果
            
        Returns:
            Dict[str, Any]: 包含处方结果的字典
        """
        try:
            logger.info("开始生成处方...")

            # 使用模板格式化提示词
            prompt = PRESCRIPTION_PROMPT_TEMPLATE.format(
                medical_record=medical_record,
                diagnosis_result=diagnosis_result
            )

            # 调用LLM生成处方
            start_time = time.time()

            # 直接调用非流式API
            response = self.llm.simple_chat(
                user_message=prompt,
                temperature=0.3
            )

            end_time = time.time()
            duration = round(end_time - start_time, 2)

            # 提取处方
            prescription = self.extract_answer_from_response(response)

            logger.info(f"处方生成完成，耗时: {duration}s")

            return {
                "input_medical_record": medical_record,
                "input_diagnosis": diagnosis_result,
                "prescription": prescription,
                "llm_response": response,
                "status": "success",
                "processing_time": duration,
                "timestamp": time.time()
            }

        except Exception as e:
            logger.error(f"处方生成出错: {str(e)}", exc_info=True)
            return {
                "input_medical_record": medical_record,
                "input_diagnosis": diagnosis_result,
                "prescription": None,
                "status": "error",
                "error_message": str(e),
                "timestamp": time.time()
            }

    def generate_exercise_prescription(
            self,
            medical_record: str,
            diagnosis_result: str,
            height: Optional[float] = None,
            weight: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        根据病历和证型生成运动处方
        
        Args:
            medical_record (str): 格式化的病历文本
            diagnosis_result (str): 证型判断结果
            height (Optional[float]): 身高(cm)
            weight (Optional[float]): 体重(kg)
            
        Returns:
            Dict[str, Any]: 包含运动处方结果的字典
        """
        try:
            logger.info("开始生成运动处方...")

            # 计算BMI
            bmi = "未提供"
            if height and weight:
                height_m = height / 100
                bmi_value = weight / (height_m ** 2)
                bmi = f"{bmi_value:.2f}"

            # 使用模板格式化提示词
            prompt = EXERCISE_PRESCRIPTION_PROMPT_TEMPLATE.format(
                medical_record=medical_record,
                diagnosis_result=diagnosis_result,
                height=height if height else "未提供",
                weight=weight if weight else "未提供",
                bmi=bmi
            )

            # 调用LLM生成运动处方
            start_time = time.time()

            # 直接调用非流式API
            response = self.llm.simple_chat(
                user_message=prompt,
                temperature=0.5
            )

            end_time = time.time()
            duration = round(end_time - start_time, 2)

            # 提取运动处方
            exercise_prescription = self.extract_answer_from_response(response)

            logger.info(f"运动处方生成完成，耗时: {duration}s")

            return {
                "input_medical_record": medical_record,
                "input_diagnosis": diagnosis_result,
                "exercise_prescription": exercise_prescription,
                "llm_response": response,
                "status": "success",
                "processing_time": duration,
                "timestamp": time.time()
            }

        except Exception as e:
            logger.error(f"运动处方生成出错: {str(e)}", exc_info=True)
            return {
                "input_medical_record": medical_record,
                "input_diagnosis": diagnosis_result,
                "exercise_prescription": None,
                "status": "error",
                "error_message": str(e),
                "timestamp": time.time()
            }

    def process_complete_diagnosis(
            self,
            transcript: str,
            height: Optional[float] = None,
            weight: Optional[float] = None,
            coze_conversation_log: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        处理完整的诊断流程
        
        Args:
            transcript (str): 对话转录文本
            height (Optional[float]): 身高(cm)
            weight (Optional[float]): 体重(kg)
            coze_conversation_log (Optional[str]):数字人的对话日志。
        Returns:
            Dict[str, Any]: 包含完整处理结果的字典
        """
        logger.info("开始完整诊断流程...")

        start_time = time.time()

        # 1. 生成病历
        logger.info("[1/4] 生成病历")
        medical_result = self.generate_medical_record_from_transcript_and_coze_conversation(transcript,
                                                                                            coze_conversation_log)
        if medical_result["status"] != "success":
            logger.error("病历生成失败")
            return {
                "input_transcript": transcript,
                "medical_record_result": medical_result,
                "diagnosis_result": {"status": "skipped", "reason": "medical_record_generation_failed"},
                "prescription_result": {"status": "skipped", "reason": "medical_record_generation_failed"},
                "exercise_prescription_result": {"status": "skipped", "reason": "medical_record_generation_failed"},
                "overall_status": "failed",
                "timestamp": time.time()
            }

        medical_record = medical_result["medical_record"]

        # 2. 证型判断
        logger.info("[2/4] 证型判断")
        diagnosis_result = self.judge_symptom_type(medical_record)
        if diagnosis_result["status"] != "success":
            logger.error("证型判断失败")
            return {
                "input_transcript": transcript,
                "medical_record_result": medical_result,
                "diagnosis_result": diagnosis_result,
                "prescription_result": {"status": "skipped", "reason": "diagnosis_failed"},
                "exercise_prescription_result": {"status": "skipped", "reason": "diagnosis_failed"},
                "overall_status": "failed",
                "timestamp": time.time()
            }

        diagnosis = diagnosis_result["diagnosis"]

        # 3. 处方生成
        logger.info("[3/4] 处方生成")
        prescription_result = self.generate_prescription(medical_record, diagnosis)

        # 4. 运动处方生成
        logger.info("[4/4] 运动处方生成")
        exercise_prescription_result = self.generate_exercise_prescription(
            medical_record, diagnosis, height, weight
        )

        # 整合结果
        end_time = time.time()
        total_duration = round(end_time - start_time, 2)

        overall_status = "success" if (
                prescription_result["status"] == "success" and
                exercise_prescription_result["status"] == "success"
        ) else "partial_success" if prescription_result["status"] == "success" else "failed"

        logger.info(f"完整诊断流程完成，总耗时: {total_duration}s，状态: {overall_status}")

        return {
            "input_transcript": transcript,
            "medical_record_result": medical_result,
            "diagnosis_result": diagnosis_result,
            "prescription_result": prescription_result,
            "exercise_prescription_result": exercise_prescription_result,
            "overall_status": overall_status,
            "total_processing_time": total_duration,
            "timestamp": time.time()
        }

    async def _async_stream_llm_response(
            self,
            prompt: str,
            temperature: float = 0.7
    ) -> AsyncGenerator[str, None]:
        """
        异步流式调用LLM并返回内容块
        
        Args:
            prompt: 提示词
            temperature: 温度参数
            
        Yields:
            str: 响应内容块
        """
        messages: List[ChatCompletionMessageParam] = [
            cast(ChatCompletionUserMessageParam, {
                "role": "user",
                "content": prompt
            })
        ]

        async for chunk in self.llm.async_stream_chat(
                messages=messages,
                temperature=temperature
        ):
            yield chunk

    async def stream_complete_diagnosis(
            self,
            transcript: str,
            height: Optional[float] = None,
            weight: Optional[float] = None,
            coze_conversation_log: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        流式处理完整的诊断流程，使用 SSE 格式返回
        
        Args:
            transcript (str): 对话转录文本
            height (Optional[float]): 身高(cm)
            weight (Optional[float]): 体重(kg)
            coze_conversation_log (Optional[str]): 数字人的对话日志
            
        Yields:
            str: SSE格式的事件数据
        """
        logger.info("开始流式诊断流程...")
        start_time = time.time()

        # 用于存储各阶段结果
        medical_record = ""
        diagnosis = ""
        diagnosis_explanation = ""
        prescription = ""
        exercise_prescription = ""

        def create_sse_event(event_type: str, data: Dict[str, Any]) -> str:
            """创建SSE事件格式"""
            return f"event: {event_type}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"

        try:
            # ========== 阶段1: 生成病历 ==========
            yield create_sse_event("stage_start", {
                "stage": DiagnosisStage.MEDICAL_RECORD,
                "stage_name": "生成病历",
                "step": "1/4"
            })

            logger.info("[1/4] 流式生成病历")
            medical_record_prompt = MEDICAL_RECORD_PROMPT_TEMPLATE.format(
                transcript=transcript,
                log_string=coze_conversation_log
            )

            full_medical_response = ""
            async for chunk in self._async_stream_llm_response(medical_record_prompt, temperature=0.6):
                full_medical_response += chunk
                yield create_sse_event("content", {
                    "stage": DiagnosisStage.MEDICAL_RECORD,
                    "chunk": chunk
                })

            medical_record = self.extract_answer_from_response(full_medical_response)

            yield create_sse_event("stage_complete", {
                "stage": DiagnosisStage.MEDICAL_RECORD,
                "stage_name": "生成病历",
                "result": medical_record
            })

            if not medical_record:
                yield create_sse_event("error", {
                    "stage": DiagnosisStage.MEDICAL_RECORD,
                    "message": "病历生成失败"
                })
                return

            # ========== 阶段2: 证型判断 ==========
            yield create_sse_event("stage_start", {
                "stage": DiagnosisStage.DIAGNOSIS,
                "stage_name": "证型判断",
                "step": "2/4"
            })

            logger.info("[2/4] 流式证型判断")
            diagnosis_prompt = TYPE_INFER_PROMPT_TEMPLATE.format(medical_record=medical_record)

            full_diagnosis_response = ""
            async for chunk in self._async_stream_llm_response(diagnosis_prompt, temperature=0.3):
                full_diagnosis_response += chunk
                yield create_sse_event("content", {
                    "stage": DiagnosisStage.DIAGNOSIS,
                    "chunk": chunk
                })

            diagnosis = self.extract_answer_from_response(full_diagnosis_response)
            diagnosis_explanation = self.extract_think_from_response(full_diagnosis_response)

            yield create_sse_event("stage_complete", {
                "stage": DiagnosisStage.DIAGNOSIS,
                "stage_name": "证型判断",
                "result": diagnosis,
                "explanation": diagnosis_explanation
            })

            if not diagnosis:
                yield create_sse_event("error", {
                    "stage": DiagnosisStage.DIAGNOSIS,
                    "message": "证型判断失败"
                })
                return

            # ========== 阶段3: 处方生成 ==========
            yield create_sse_event("stage_start", {
                "stage": DiagnosisStage.PRESCRIPTION,
                "stage_name": "处方生成",
                "step": "3/4"
            })

            logger.info("[3/4] 流式处方生成")
            prescription_prompt = PRESCRIPTION_PROMPT_TEMPLATE.format(
                medical_record=medical_record,
                diagnosis_result=diagnosis
            )

            full_prescription_response = ""
            async for chunk in self._async_stream_llm_response(prescription_prompt, temperature=0.3):
                full_prescription_response += chunk
                yield create_sse_event("content", {
                    "stage": DiagnosisStage.PRESCRIPTION,
                    "chunk": chunk
                })

            prescription = self.extract_answer_from_response(full_prescription_response)

            yield create_sse_event("stage_complete", {
                "stage": DiagnosisStage.PRESCRIPTION,
                "stage_name": "处方生成",
                "result": prescription
            })

            # ========== 阶段4: 运动处方生成 ==========
            yield create_sse_event("stage_start", {
                "stage": DiagnosisStage.EXERCISE_PRESCRIPTION,
                "stage_name": "运动处方生成",
                "step": "4/4"
            })

            logger.info("[4/4] 流式运动处方生成")

            # 计算BMI
            bmi = "未提供"
            if height and weight:
                height_m = height / 100
                bmi_value = weight / (height_m ** 2)
                bmi = f"{bmi_value:.2f}"

            exercise_prompt = EXERCISE_PRESCRIPTION_PROMPT_TEMPLATE.format(
                medical_record=medical_record,
                diagnosis_result=diagnosis,
                height=height if height else "未提供",
                weight=weight if weight else "未提供",
                bmi=bmi
            )

            full_exercise_response = ""
            async for chunk in self._async_stream_llm_response(exercise_prompt, temperature=0.5):
                full_exercise_response += chunk
                yield create_sse_event("content", {
                    "stage": DiagnosisStage.EXERCISE_PRESCRIPTION,
                    "chunk": chunk
                })

            exercise_prescription = self.extract_answer_from_response(full_exercise_response)

            yield create_sse_event("stage_complete", {
                "stage": DiagnosisStage.EXERCISE_PRESCRIPTION,
                "stage_name": "运动处方生成",
                "result": exercise_prescription
            })

            # ========== 完成 ==========
            end_time = time.time()
            total_duration = round(end_time - start_time, 2)

            logger.info(f"流式诊断流程完成，总耗时: {total_duration}s")

            yield create_sse_event("complete", {
                "status": "success",
                "total_processing_time": total_duration,
                "formatted_medical_record": medical_record,
                "type_inference": diagnosis,
                "diagnosis_explanation": diagnosis_explanation,
                "prescription": prescription,
                "exercise_prescription": exercise_prescription
            })

        except Exception as e:
            logger.error(f"流式诊断出错: {str(e)}", exc_info=True)
            yield create_sse_event("error", {
                "message": f"诊断过程出错: {str(e)}"
            })
