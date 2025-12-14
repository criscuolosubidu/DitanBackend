"""
OpenAI客户端服务
"""
from typing import List, Optional, Any, cast, AsyncGenerator

import httpx
import openai
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionUserMessageParam,
    ChatCompletionSystemMessageParam
)

from app.core.logging import get_logger

logger = get_logger(__name__)

# 配置适合流式传输的超时时间
# connect: 连接建立超时
# read: 读取单个chunk的超时（流式传输时每个chunk都会重置）
# write: 写入请求的超时
# pool: 连接池获取连接的超时
STREAM_TIMEOUT = httpx.Timeout(
    connect=30.0,  # 连接超时30秒
    read=120.0,  # 读取超时120秒（流式响应可能有较长间隔）
    write=30.0,  # 写入超时30秒
    pool=30.0  # 连接池超时30秒
)


class OpenAIChatCompletion:
    """
    OpenAI Chat Completion API的封装类
    
    用于方便地调用OpenAI的聊天完成API，支持自定义API密钥、基础URL和模型名称。
    支持同步和异步调用。
    """

    def __init__(self, api_key: str, base_url: str, model_name: str):
        """
        初始化OpenAI Chat Completion客户端
        
        Args:
            api_key (str): OpenAI API密钥
            base_url (str): API基础URL
            model_name (str): 要使用的模型名称
        """
        self.api_key = api_key
        self.base_url = base_url
        self.model_name = model_name

        # 初始化同步OpenAI客户端（带超时配置）
        self.client = openai.OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=STREAM_TIMEOUT
        )

        # 初始化异步OpenAI客户端（带超时配置）
        self.async_client = openai.AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=STREAM_TIMEOUT
        )
        logger.info(
            f"OpenAI客户端初始化成功，模型: {model_name}, 超时配置: connect={STREAM_TIMEOUT.connect}s, read={STREAM_TIMEOUT.read}s")

    def chat(self, messages: List[ChatCompletionMessageParam],
             temperature: float = 0.7,
             max_tokens: Optional[int] = None,
             stream: bool = False,
             **kwargs) -> Any:
        """
        发送聊天完成请求
        
        Args:
            messages (List[ChatCompletionMessageParam]): 消息列表
            temperature (float): 温度参数，控制输出的随机性 (0-2)
            max_tokens (Optional[int]): 最大token数量
            stream (bool): 是否使用流式输出
            **kwargs: 其他OpenAI API参数
            
        Returns:
            OpenAI API响应对象
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=stream,
                **kwargs
            )
            return response
        except Exception as e:
            logger.error(f"调用OpenAI API时发生错误: {e}")
            raise e

    def simple_chat(self, user_message: str,
                    system_message: Optional[str] = None,
                    temperature: float = 0.7,
                    max_tokens: Optional[int] = None) -> str:
        """
        简单的单轮对话方法
        
        Args:
            user_message (str): 用户消息
            system_message (Optional[str]): 系统消息（可选）
            temperature (float): 温度参数
            max_tokens (Optional[int]): 最大token数量
            
        Returns:
            str: AI的回复内容
        """
        messages: List[ChatCompletionMessageParam] = []

        if system_message:
            messages.append(cast(ChatCompletionSystemMessageParam, {
                "role": "system",
                "content": system_message
            }))

        messages.append(cast(ChatCompletionUserMessageParam, {
            "role": "user",
            "content": user_message
        }))

        response = self.chat(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )

        return response.choices[0].message.content

    def stream_chat(self, messages: List[ChatCompletionMessageParam],
                    temperature: float = 0.7,
                    max_tokens: Optional[int] = None,
                    **kwargs):
        """
        流式聊天方法（同步版本）
        
        Args:
            messages (List[ChatCompletionMessageParam]): 消息列表
            temperature (float): 温度参数
            max_tokens (Optional[int]): 最大token数量
            **kwargs: 其他OpenAI API参数
            
        Yields:
            流式响应的每个chunk
        """
        response = self.chat(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
            **kwargs
        )

        for chunk in response:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content

    async def async_stream_chat(
            self,
            messages: List[ChatCompletionMessageParam],
            temperature: float = 0.7,
            max_tokens: Optional[int] = None,
            **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        异步流式聊天方法
        
        Args:
            messages (List[ChatCompletionMessageParam]): 消息列表
            temperature (float): 温度参数
            max_tokens (Optional[int]): 最大token数量
            **kwargs: 其他OpenAI API参数
            
        Yields:
            流式响应的每个chunk
        """
        try:
            response = await self.async_client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
                **kwargs
            )

            async for chunk in response:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            logger.error(f"异步流式调用OpenAI API时发生错误: {e}")
            raise e

    def get_model_info(self) -> dict:
        """
        获取当前配置的模型信息
        
        Returns:
            dict: 包含模型配置信息的字典
        """
        return {
            "model_name": self.model_name,
            "base_url": self.base_url,
            "api_key_preview": f"{self.api_key[:8]}...{self.api_key[-4:]}" if len(self.api_key) > 12 else "***"
        }
