"""Base AI provider interface for flexible model switching."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from enum import Enum

class AICapability(Enum):
    """AI capabilities that providers can support."""
    TEXT_ANALYSIS = "text_analysis"
    TEXT_GENERATION = "text_generation" 
    IMAGE_ANALYSIS = "image_analysis"
    IMAGE_GENERATION = "image_generation"
    WEB_ANALYSIS = "web_analysis"
    CONTENT_STRATEGY = "content_strategy"

class BaseAIProvider(ABC):
    """Base class for all AI providers."""
    
    def __init__(self, name: str, model: str = None):
        self.name = name
        self.model = model
        self.capabilities = self._get_capabilities()
    
    @abstractmethod
    def _get_capabilities(self) -> List[AICapability]:
        """Return list of capabilities this provider supports."""
        pass
    
    @abstractmethod
    def analyze_text(self, text: str, prompt: str, **kwargs) -> Dict[str, Any]:
        """Analyze text content with given prompt."""
        pass
    
    @abstractmethod
    def generate_text(self, prompt: str, **kwargs) -> str:
        """Generate text from prompt."""
        pass
    
    def analyze_image(self, image_data: bytes, prompt: str, **kwargs) -> Dict[str, Any]:
        """Analyze image content (override if supported)."""
        if AICapability.IMAGE_ANALYSIS not in self.capabilities:
            raise NotImplementedError(f"{self.name} does not support image analysis")
    
    def generate_image(self, prompt: str, **kwargs) -> bytes:
        """Generate image from prompt (override if supported)."""
        if AICapability.IMAGE_GENERATION not in self.capabilities:
            raise NotImplementedError(f"{self.name} does not support image generation")
    
    def analyze_website(self, html_content: str, url: str, **kwargs) -> Dict[str, Any]:
        """Analyze website content (override if supported)."""
        if AICapability.WEB_ANALYSIS not in self.capabilities:
            raise NotImplementedError(f"{self.name} does not support web analysis")
    
    def create_content_strategy(self, business_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Create content strategy (override if supported)."""
        if AICapability.CONTENT_STRATEGY not in self.capabilities:
            raise NotImplementedError(f"{self.name} does not support content strategy")
    
    def supports_capability(self, capability: AICapability) -> bool:
        """Check if provider supports given capability."""
        return capability in self.capabilities