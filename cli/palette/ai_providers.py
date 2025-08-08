"""
AI Provider Abstraction Layer for Python Backend
Unified interface for OpenAI, Anthropic, and other providers
"""

import os
import asyncio
from typing import Dict, Any, Optional, AsyncGenerator, List
from enum import Enum
from dataclasses import dataclass
import openai
import anthropic
from anthropic import AsyncAnthropic
from openai import AsyncOpenAI


class ProviderType(Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


@dataclass
class ProviderConfig:
    provider: ProviderType
    model: str
    max_tokens: int
    supports_streaming: bool
    supports_functions: bool
    default_temperature: Optional[float] = None


class AIProviderRegistry:
    """Registry for AI providers with unified interface"""
    
    PROVIDER_CONFIGS: Dict[str, ProviderConfig] = {
        # OpenAI Models
        "gpt-4o": ProviderConfig(
            provider=ProviderType.OPENAI,
            model="gpt-4o",
            max_tokens=4096,
            supports_streaming=True,
            supports_functions=True,
            default_temperature=0.7
        ),
        "gpt-4o-mini": ProviderConfig(
            provider=ProviderType.OPENAI,
            model="gpt-4o-mini",
            max_tokens=16384,
            supports_streaming=True,
            supports_functions=True,
            default_temperature=0.7
        ),
        "gpt-5": ProviderConfig(
            provider=ProviderType.OPENAI,
            model="gpt-5",
            max_tokens=2000,  # Conservative limit for 10K TPM
            supports_streaming=True,
            supports_functions=False,
        ),
        "gpt-5-mini": ProviderConfig(
            provider=ProviderType.OPENAI,
            model="gpt-5-mini", 
            max_tokens=2000,
            supports_streaming=True,
            supports_functions=False,
        ),
        "gpt-3.5-turbo": ProviderConfig(
            provider=ProviderType.OPENAI,
            model="gpt-3.5-turbo",
            max_tokens=4096,
            supports_streaming=True,
            supports_functions=True,
            default_temperature=0.7
        ),
        
        # Anthropic Models
        "claude-3-5-sonnet-20241022": ProviderConfig(
            provider=ProviderType.ANTHROPIC,
            model="claude-3-5-sonnet-20241022",
            max_tokens=8192,
            supports_streaming=True,
            supports_functions=False,
            default_temperature=0.7
        ),
        "claude-3-5-haiku-20241022": ProviderConfig(
            provider=ProviderType.ANTHROPIC,
            model="claude-3-5-haiku-20241022", 
            max_tokens=8192,
            supports_streaming=True,
            supports_functions=False,
            default_temperature=0.7
        ),
        "claude-3-opus-20240229": ProviderConfig(
            provider=ProviderType.ANTHROPIC,
            model="claude-3-opus-20240229",
            max_tokens=4096,
            supports_streaming=True,
            supports_functions=False,
            default_temperature=0.7
        )
    }
    
    def __init__(self):
        self._openai_client: Optional[AsyncOpenAI] = None
        self._anthropic_client: Optional[AsyncAnthropic] = None
    
    @classmethod
    def get_provider_config(cls, model: str) -> ProviderConfig:
        """Get provider configuration for a model"""
        config = cls.PROVIDER_CONFIGS.get(model)
        if not config:
            print(f"🎨 Unknown model {model}, using gpt-4o-mini as fallback")
            return cls.PROVIDER_CONFIGS["gpt-4o-mini"]
        return config
    
    def get_openai_client(self) -> AsyncOpenAI:
        """Get or create OpenAI client"""
        if not self._openai_client:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable not set")
            self._openai_client = AsyncOpenAI(api_key=api_key)
        return self._openai_client
    
    def get_anthropic_client(self) -> AsyncAnthropic:
        """Get or create Anthropic client"""
        if not self._anthropic_client:
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY environment variable not set")
            self._anthropic_client = AsyncAnthropic(api_key=api_key)
        return self._anthropic_client
    
    async def generate_response(
        self,
        model: str,
        system_prompt: str,
        messages: List[Dict[str, str]],
        stream: bool = False,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> AsyncGenerator[str, None]:
        """Generate response using the appropriate provider"""
        config = self.get_provider_config(model)
        
        # Use config defaults if not specified
        if temperature is None and config.default_temperature is not None:
            temperature = config.default_temperature
        if max_tokens is None:
            max_tokens = config.max_tokens
        
        if config.provider == ProviderType.OPENAI:
            async for chunk in self._generate_openai_response(
                config, system_prompt, messages, stream, temperature, max_tokens
            ):
                yield chunk
        elif config.provider == ProviderType.ANTHROPIC:
            async for chunk in self._generate_anthropic_response(
                config, system_prompt, messages, stream, temperature, max_tokens
            ):
                yield chunk
        else:
            raise ValueError(f"Unsupported provider: {config.provider}")
    
    async def _generate_openai_response(
        self,
        config: ProviderConfig,
        system_prompt: str,
        messages: List[Dict[str, str]],
        stream: bool,
        temperature: Optional[float],
        max_tokens: int
    ) -> AsyncGenerator[str, None]:
        """Generate response using OpenAI"""
        client = self.get_openai_client()
        
        # Prepare messages for OpenAI format
        openai_messages = [{"role": "system", "content": system_prompt}]
        openai_messages.extend(messages)
        
        params = {
            "model": config.model,
            "messages": openai_messages,
            "max_tokens": max_tokens,
            "stream": stream,
        }
        
        if temperature is not None:
            params["temperature"] = temperature
        
        if stream:
            response = await client.chat.completions.create(**params)
            async for chunk in response:
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if delta.content:
                        yield delta.content
        else:
            response = await client.chat.completions.create(**params)
            if response.choices and len(response.choices) > 0:
                yield response.choices[0].message.content or ""
    
    async def _generate_anthropic_response(
        self,
        config: ProviderConfig,
        system_prompt: str,
        messages: List[Dict[str, str]],
        stream: bool,
        temperature: Optional[float],
        max_tokens: int
    ) -> AsyncGenerator[str, None]:
        """Generate response using Anthropic"""
        client = self.get_anthropic_client()
        
        params = {
            "model": config.model,
            "system": system_prompt,
            "messages": messages,
            "max_tokens": max_tokens,
            "stream": stream,
        }
        
        if temperature is not None:
            params["temperature"] = temperature
        
        if stream:
            response = await client.messages.create(**params)
            async for chunk in response:
                if chunk.type == "content_block_delta":
                    if hasattr(chunk.delta, 'text'):
                        yield chunk.delta.text
        else:
            response = await client.messages.create(**params)
            if response.content and len(response.content) > 0:
                yield response.content[0].text
    
    @classmethod
    def supports_streaming(cls, model: str) -> bool:
        """Check if model supports streaming"""
        config = cls.get_provider_config(model)
        return config.supports_streaming
    
    @classmethod
    def get_available_models(cls) -> List[str]:
        """Get all available models"""
        return list(cls.PROVIDER_CONFIGS.keys())
    
    @classmethod
    def validate_provider(cls, model: str) -> Dict[str, Any]:
        """Validate that provider is properly configured"""
        config = cls.get_provider_config(model)
        
        if config.provider == ProviderType.OPENAI:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                return {
                    "valid": False,
                    "error": "OpenAI API key not configured in environment"
                }
        elif config.provider == ProviderType.ANTHROPIC:
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                return {
                    "valid": False,
                    "error": "Anthropic API key not configured in environment"
                }
        
        return {"valid": True}
    
    @classmethod
    def get_recommended_model(cls, use_case: str = "balanced") -> str:
        """Get recommended model based on use case"""
        recommendations = {
            "speed": "gpt-4o-mini",
            "quality": "gpt-4o", 
            "cost": "gpt-3.5-turbo",
            "balanced": "gpt-4o-mini",
            "anthropic": "claude-3-5-sonnet-20241022"
        }
        return recommendations.get(use_case, "gpt-4o-mini")


# Global instance for the application
ai_provider_registry = AIProviderRegistry()


async def generate_ai_response(
    model: str,
    system_prompt: str, 
    messages: List[Dict[str, str]],
    stream: bool = False,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None
) -> AsyncGenerator[str, None]:
    """Convenience function for generating AI responses"""
    async for chunk in ai_provider_registry.generate_response(
        model=model,
        system_prompt=system_prompt,
        messages=messages,
        stream=stream,
        temperature=temperature,
        max_tokens=max_tokens
    ):
        yield chunk


def validate_model_configuration(model: str) -> Dict[str, Any]:
    """Validate model configuration"""
    return AIProviderRegistry.validate_provider(model)


def get_supported_models() -> List[str]:
    """Get list of supported models"""
    return AIProviderRegistry.get_available_models()