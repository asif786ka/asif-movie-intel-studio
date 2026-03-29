import os
import json
from typing import AsyncIterator, Optional
from abc import ABC, abstractmethod
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class LLMProvider(ABC):
    @abstractmethod
    async def generate(self, prompt: str, system_prompt: str = "", temperature: float = 0.3, max_tokens: int = 2048) -> str:
        pass

    @abstractmethod
    async def generate_stream(self, prompt: str, system_prompt: str = "", temperature: float = 0.3, max_tokens: int = 2048) -> AsyncIterator[str]:
        pass


class OpenAIProvider(LLMProvider):
    def __init__(self):
        self.api_key = settings.openai_api_key or os.environ.get("OPENAI_API_KEY", "")
        self.base_url = settings.openai_base_url
        self.model = settings.openai_model

    async def generate(self, prompt: str, system_prompt: str = "", temperature: float = 0.3, max_tokens: int = 2048) -> str:
        try:
            from langchain_openai import ChatOpenAI
            kwargs = {"model": self.model, "temperature": temperature, "max_tokens": max_tokens}
            if self.api_key:
                kwargs["api_key"] = self.api_key
            if self.base_url:
                kwargs["base_url"] = self.base_url
            llm = ChatOpenAI(**kwargs)
            messages = []
            if system_prompt:
                messages.append(("system", system_prompt))
            messages.append(("human", prompt))
            response = await llm.ainvoke(messages)
            return response.content
        except Exception as e:
            logger.error(f"OpenAI generation failed: {e}")
            return f"I encountered an error generating a response. Please try again. Error: {str(e)}"

    async def generate_stream(self, prompt: str, system_prompt: str = "", temperature: float = 0.3, max_tokens: int = 2048) -> AsyncIterator[str]:
        try:
            from langchain_openai import ChatOpenAI
            kwargs = {"model": self.model, "temperature": temperature, "max_tokens": max_tokens, "streaming": True}
            if self.api_key:
                kwargs["api_key"] = self.api_key
            if self.base_url:
                kwargs["base_url"] = self.base_url
            llm = ChatOpenAI(**kwargs)
            messages = []
            if system_prompt:
                messages.append(("system", system_prompt))
            messages.append(("human", prompt))
            async for chunk in llm.astream(messages):
                if chunk.content:
                    yield chunk.content
        except Exception as e:
            logger.error(f"OpenAI streaming failed: {e}")
            yield f"Error: {str(e)}"


class BedrockProvider(LLMProvider):
    def __init__(self):
        self.model_id = settings.bedrock_model_id
        self.region = settings.aws_region

    async def generate(self, prompt: str, system_prompt: str = "", temperature: float = 0.3, max_tokens: int = 2048) -> str:
        try:
            from langchain_community.chat_models import BedrockChat
            llm = BedrockChat(
                model_id=self.model_id,
                region_name=self.region,
                model_kwargs={"temperature": temperature, "max_tokens": max_tokens},
            )
            messages = []
            if system_prompt:
                messages.append(("system", system_prompt))
            messages.append(("human", prompt))
            response = await llm.ainvoke(messages)
            return response.content
        except Exception as e:
            logger.error(f"Bedrock generation failed: {e}")
            return f"Bedrock error: {str(e)}"

    async def generate_stream(self, prompt: str, system_prompt: str = "", temperature: float = 0.3, max_tokens: int = 2048) -> AsyncIterator[str]:
        try:
            from langchain_community.chat_models import BedrockChat
            llm = BedrockChat(
                model_id=self.model_id,
                region_name=self.region,
                model_kwargs={"temperature": temperature, "max_tokens": max_tokens},
                streaming=True,
            )
            messages = []
            if system_prompt:
                messages.append(("system", system_prompt))
            messages.append(("human", prompt))
            async for chunk in llm.astream(messages):
                if chunk.content:
                    yield chunk.content
        except Exception as e:
            logger.error(f"Bedrock streaming failed: {e}")
            yield f"Error: {str(e)}"


class MockLLMProvider(LLMProvider):
    async def generate(self, prompt: str, system_prompt: str = "", temperature: float = 0.3, max_tokens: int = 2048) -> str:
        if "classify" in prompt.lower() or "classification" in prompt.lower():
            if any(word in prompt.lower() for word in ["theme", "review", "analysis", "explain", "summarize", "recurring"]):
                return "rag_only"
            elif any(word in prompt.lower() for word in ["compare", "contrast", "both", "reception and"]):
                return "hybrid"
            return "structured_only"

        if "evidence sufficiency" in prompt.lower() or "rate the evidence" in prompt.lower():
            return "0.7"

        if "compliance" in prompt.lower() or "check for" in prompt.lower():
            return "PASS"

        return (
            "Based on the available information, here is what I found:\n\n"
            "The provided context contains relevant information about the queried movies. "
            "This is a demonstration response from the mock LLM provider. "
            "In production, this would be replaced with a real LLM-generated response "
            "with proper citations [Source 1] and grounded analysis [Source 2].\n\n"
            "To enable real AI responses, configure an LLM provider (OpenAI or AWS Bedrock) "
            "in your environment variables."
        )

    async def generate_stream(self, prompt: str, system_prompt: str = "", temperature: float = 0.3, max_tokens: int = 2048) -> AsyncIterator[str]:
        response = await self.generate(prompt, system_prompt, temperature, max_tokens)
        words = response.split()
        for i, word in enumerate(words):
            yield word + (" " if i < len(words) - 1 else "")


def get_llm_provider() -> LLMProvider:
    provider = settings.llm_provider.lower()

    proxy_base_url = os.environ.get("AI_INTEGRATIONS_OPENAI_BASE_URL", "")
    proxy_api_key = os.environ.get("AI_INTEGRATIONS_OPENAI_API_KEY", "")

    if provider == "openai" and settings.openai_api_key:
        logger.info("Using OpenAI LLM provider (user API key)")
        return OpenAIProvider()
    elif proxy_base_url and proxy_api_key:
        logger.info("Using OpenAI LLM provider via AI proxy")
        p = OpenAIProvider()
        p.api_key = proxy_api_key
        p.base_url = proxy_base_url
        p.model = settings.openai_model
        return p
    elif provider == "bedrock" and settings.aws_access_key_id:
        logger.info("Using AWS Bedrock LLM provider")
        return BedrockProvider()
    elif provider == "mock":
        logger.info("Using Mock LLM provider (explicitly configured)")
        return MockLLMProvider()
    else:
        logger.info("Using Mock LLM provider (no API keys configured)")
        return MockLLMProvider()


llm_provider = get_llm_provider()
