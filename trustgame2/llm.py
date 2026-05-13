from typing import Optional, Any
import json_repair
from openai import AsyncOpenAI, RateLimitError, InternalServerError, APIConnectionError
import json
import yaml
import os
import re
import asyncio
from pathlib import Path
from pydantic import BaseModel, Field

__all__ = ["LLMConfig"]


class LLMModelConfig(BaseModel):
    model: str
    mark: str
    concurrency: int


class LLMConfig(BaseModel):
    base_url: str
    api_key: str
    model: LLMModelConfig
    temperature: float
    concurrency: int
    client: Optional[AsyncOpenAI] = Field(default=None, exclude=True)
    semaphore: Optional[asyncio.Semaphore] = Field(default=None, exclude=True)

    model_config = {"arbitrary_types_allowed": True, "validate_assignment": True}

    def _get_client(self) -> AsyncOpenAI:
        """Get or create the OpenAI client"""
        if self.client is None:
            self.client = AsyncOpenAI(
                base_url=self.base_url,
                api_key=self.api_key,
            )
            self.semaphore = asyncio.Semaphore(self.concurrency)
        return self.client

    async def _chat_completion(self, messages: list, **kwargs) -> str:
        """Send chat completion request and return the response"""
        client = self._get_client()
        assert self.semaphore is not None
        async with self.semaphore:
            max_retries = 10
            retry_count = 0

            while retry_count < max_retries:
                try:
                    response = await client.chat.completions.create(
                        model=self.model.model,
                        messages=messages,
                        temperature=self.temperature,
                        **kwargs,
                    )
                    return response.choices[0].message.content
                except Exception as e:
                    error_str = str(e)
                    # 检查是否是速率限制错误（优先检查openai.RateLimitError，然后检查字符串匹配）
                    is_rate_limit = (
                        isinstance(
                            e, (RateLimitError, InternalServerError, APIConnectionError)
                        )
                    ) or ("429" in error_str and "limit_requests" in error_str)

                    if is_rate_limit:
                        retry_count += 1
                        if retry_count < max_retries:
                            # 二进制指数退让：等待时间从1秒开始，每次重试翻倍，但不超过30秒
                            wait_time = min(
                                2 ** (retry_count - 1), 30
                            )  # 1, 2, 4, 8, 16, 30, 30, 30, 30, 30秒
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            # 重试次数用完，抛出异常
                            raise Exception(
                                f"LLM API call failed after {max_retries} retries: {error_str}"
                            )
                    # 非速率限制错误直接抛出
                    raise Exception(f"LLM API call failed: {error_str}")

            # 理论上不会到达这里，但为了满足类型检查
            raise Exception("Unexpected end of retry loop")

    async def chat_completion_json(self, messages: list, **kwargs) -> dict:
        """Send chat completion request and return parsed JSON response"""
        response = await self._chat_completion(messages, **kwargs)
        try:
            return json_repair.loads(response)  # type: ignore
        except json.JSONDecodeError as e:
            raise Exception(
                f"Failed to parse JSON response: {response}. Error: {str(e)}"
            )

    def to_model_mark(self) -> str:
        return self.model.mark

    def to_temperature_mark(self) -> str:
        mapper = {
            0: "T00",
            0.1: "T01",
            0.2: "T02",
            0.3: "T03",
            0.4: "T04",
            0.5: "T05",
            0.6: "T06",
            0.7: "T07",
            0.8: "T08",
            0.9: "T09",
            1: "T10",
        }
        return mapper[self.temperature]


class LLMMultiConfig(BaseModel):
    base_url: str
    api_key: str
    models: list[LLMModelConfig]
    temperatures: list[float]


class LLMsConfig(BaseModel):
    llms: list[LLMMultiConfig]

    @classmethod
    def from_yaml(cls, yaml_path: str) -> "LLMsConfig":
        """从YAML文件加载配置，支持环境变量展开"""
        yaml_file = Path(yaml_path)
        if not yaml_file.exists():
            raise FileNotFoundError(f"YAML配置文件不存在: {yaml_file}")

        with open(yaml_file, "r", encoding="utf-8") as f:
            raw_config = yaml.safe_load(f)

        # 展开环境变量
        config_data = cls._expand_env_vars(raw_config)

        # 使用 Pydantic 进行验证和创建实例
        return cls.model_validate(config_data)

    @staticmethod
    def _expand_env_vars(data: Any) -> Any:
        """递归展开配置中的环境变量"""
        if isinstance(data, dict):
            return {
                key: LLMsConfig._expand_env_vars(value) for key, value in data.items()
            }
        elif isinstance(data, list):
            return [LLMsConfig._expand_env_vars(item) for item in data]
        elif isinstance(data, str):
            # 支持 ${VAR_NAME} 和 $VAR_NAME 格式的环境变量
            def replace_env_var(match):
                var_name = match.group(1) or match.group(2)
                return os.getenv(
                    var_name, match.group(0)
                )  # 如果环境变量不存在，保持原样

            # 匹配 ${VAR_NAME} 或 $VAR_NAME 格式
            pattern = r"\$\{([^}]+)\}|\$([A-Za-z_][A-Za-z0-9_]*)"
            return re.sub(pattern, replace_env_var, data)
        else:
            return data

    def to_llm_configs(self) -> list[LLMConfig]:
        """将LLMsConfig拆分为多个LLMConfig实例"""
        llm_configs = []

        for llm_multi in self.llms:
            # 为每个模型和温度组合创建一个LLMConfig
            for model in llm_multi.models:
                for temperature in llm_multi.temperatures:
                    llm_config = LLMConfig(
                        base_url=llm_multi.base_url,
                        api_key=llm_multi.api_key,
                        model=model,
                        temperature=temperature,
                        concurrency=model.concurrency,
                    )
                    llm_configs.append(llm_config)

        return llm_configs
