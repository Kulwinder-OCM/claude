"""AI Provider Factory for creating and managing AI providers."""

import os
from typing import Dict, Any, Optional
from .base_provider import BaseAIProvider, AICapability
from .claude_provider import ClaudeProvider
from .gemini_provider import GeminiProvider  
from .openai_provider import OpenAIProvider

class AIProviderFactory:
    """Factory for creating and managing AI providers."""
    
    _providers = {
        "claude": ClaudeProvider,
        "gemini": GeminiProvider,
        "openai": OpenAIProvider
    }
    
    @classmethod
    def create_provider(cls, provider_name: str, model: str = None) -> BaseAIProvider:
        """Create an AI provider instance."""
        if provider_name not in cls._providers:
            raise ValueError(f"Unknown provider: {provider_name}. Available: {list(cls._providers.keys())}")
        
        provider_class = cls._providers[provider_name]
        
        if model:
            return provider_class(model)
        else:
            return provider_class()
    
    @classmethod
    def get_default_provider(cls, capability: AICapability) -> BaseAIProvider:
        """Get default provider for a specific capability."""
        # Force Gemini for image generation
        if capability == AICapability.IMAGE_GENERATION:
            try:
                return cls.create_provider("gemini", "gemini-2.5-flash-image-preview")
            except ValueError:
                raise ValueError("Gemini provider is required for image generation but is not available")
        
        # Priority order based on capability (for all other capabilities)
        capability_priorities = {
            AICapability.TEXT_ANALYSIS: ["claude", "openai", "gemini"],
            AICapability.TEXT_GENERATION: ["claude", "openai", "gemini"], 
            AICapability.WEB_ANALYSIS: ["claude", "openai"],
            AICapability.CONTENT_STRATEGY: ["claude", "openai"]
        }
        
        providers_to_try = capability_priorities.get(capability, ["claude", "openai", "gemini"])
        
        for provider_name in providers_to_try:
            try:
                provider = cls.create_provider(provider_name)
                if provider.supports_capability(capability):
                    return provider
            except ValueError:
                continue  # Try next provider
        
        raise ValueError(f"No available provider found for capability: {capability}")
    
    @classmethod
    def get_configured_provider(cls, capability: AICapability) -> BaseAIProvider:
        """Get provider based on environment configuration."""
        # Force Gemini for image generation regardless of configuration
        if capability == AICapability.IMAGE_GENERATION:
            try:
                return cls.create_provider("gemini", "gemini-2.5-flash-image-preview")
            except ValueError:
                raise ValueError("Gemini provider is required for image generation but is not available")
        
        # Check environment variables for preferred providers (for all other capabilities)
        provider_config = {
            AICapability.TEXT_ANALYSIS: os.getenv("AI_TEXT_ANALYSIS_PROVIDER", "claude"),
            AICapability.TEXT_GENERATION: os.getenv("AI_TEXT_GENERATION_PROVIDER", "claude"),
            AICapability.WEB_ANALYSIS: os.getenv("AI_WEB_ANALYSIS_PROVIDER", "claude"),
            AICapability.CONTENT_STRATEGY: os.getenv("AI_CONTENT_STRATEGY_PROVIDER", "claude")
        }
        
        preferred_provider = provider_config.get(capability, "claude")
        
        try:
            provider = cls.create_provider(preferred_provider)
            if provider.supports_capability(capability):
                return provider
        except ValueError:
            pass  # Fall back to default
        
        return cls.get_default_provider(capability)
    
    @classmethod
    def list_available_providers(cls) -> Dict[str, Dict[str, Any]]:
        """List all available providers and their capabilities."""
        available = {}
        
        for name, provider_class in cls._providers.items():
            try:
                provider = provider_class()
                available[name] = {
                    "model": provider.model,
                    "capabilities": [cap.value for cap in provider.capabilities],
                    "available": True
                }
            except ValueError as e:
                available[name] = {
                    "available": False,
                    "error": str(e)
                }
        
        return available