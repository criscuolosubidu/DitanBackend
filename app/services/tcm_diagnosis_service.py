"""
中医诊断服务
"""
import re
import time
from typing import Dict, Any, Optional, cast, List
from openai.types.chat import ChatCompletionMessageParam, ChatCompletionUserMessageParam

from app.services.openai_client import OpenAIChatCompletion
from app.services.prompt_templates import (
    MEDICAL_RECORD_PROMPT_TEMPLATE,
    TYPE_INFER_PROMPT_TEMPLATE,
    PRESCRIPTION_PROMPT_TEMPLATE,
    EXERCISE_PRESCRIPTION_PROMPT_TEMPLATE
)
from app.core.logging import get_logger


logger = get_logger(__name__)


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
    
    def generate_medical_record_from_transcript(self, transcript: str) -> Dict[str, Any]:
        """
        从对话转录文本生成病历
        
        Args:
            transcript (str): 对话转录文本
            
        Returns:
            Dict[str, Any]: 包含病历内容和状态的字典
        """
        try:
            logger.info("开始生成病历...")
            
            # 构建最终的prompt
            final_prompt = MEDICAL_RECORD_PROMPT_TEMPLATE.format(transcript=transcript)
            
            # 调用LLM生成病历
            start_time = time.time()
            
            messages: List[ChatCompletionMessageParam] = [
                cast(ChatCompletionUserMessageParam, {
                    "role": "user",
                    "content": final_prompt
                })
            ]
            
            medical_record = ""
            for chunk in self.llm.stream_chat(messages=messages, temperature=0.6):
                medical_record += chunk
            
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
            
            messages: List[ChatCompletionMessageParam] = [
                cast(ChatCompletionUserMessageParam, {
                    "role": "user",
                    "content": prompt
                })
            ]
            
            response = ""
            for chunk in self.llm.stream_chat(messages=messages, temperature=0.3):
                response += chunk
            
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
            
            messages: List[ChatCompletionMessageParam] = [
                cast(ChatCompletionUserMessageParam, {
                    "role": "user",
                    "content": prompt
                })
            ]
            
            response = ""
            for chunk in self.llm.stream_chat(messages=messages, temperature=0.3):
                response += chunk
            
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
            
            messages: List[ChatCompletionMessageParam] = [
                cast(ChatCompletionUserMessageParam, {
                    "role": "user",
                    "content": prompt
                })
            ]
            
            response = ""
            for chunk in self.llm.stream_chat(messages=messages, temperature=0.5):
                response += chunk
            
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
        weight: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        处理完整的诊断流程
        
        Args:
            transcript (str): 对话转录文本
            height (Optional[float]): 身高(cm)
            weight (Optional[float]): 体重(kg)
            
        Returns:
            Dict[str, Any]: 包含完整处理结果的字典
        """
        logger.info("开始完整诊断流程...")
        
        start_time = time.time()
        
        # 1. 生成病历
        logger.info("[1/4] 生成病历")
        medical_result = self.generate_medical_record_from_transcript(transcript)
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

