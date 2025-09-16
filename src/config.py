"""Configuration management for AI providers and system settings."""

import os
from typing import Dict, Any, Optional
from pathlib import Path

class Config:
    """Configuration manager for the Claude Life system."""
    
    def __init__(self):
        self._load_environment()
    
    def _load_environment(self):
        """Load environment variables from .env file."""
        env_file = Path('.env')
        if env_file.exists():
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key] = value
    
    @property
    def ai_providers(self) -> Dict[str, str]:
        """Get AI provider preferences."""
        return {
            "text_analysis": os.getenv("AI_TEXT_ANALYSIS_PROVIDER", "claude"),
            "text_generation": os.getenv("AI_TEXT_GENERATION_PROVIDER", "claude"), 
            "image_generation": "gemini",  # Always use Gemini for image generation
            "web_analysis": os.getenv("AI_WEB_ANALYSIS_PROVIDER", "claude"),
            "content_strategy": os.getenv("AI_CONTENT_STRATEGY_PROVIDER", "claude")
        }
    
    @property
    def api_keys(self) -> Dict[str, Optional[str]]:
        """Get API keys status."""
        return {
            "claude": os.getenv("CLAUDE_API_KEY"),
            "gemini": os.getenv("GEMINI_API_KEY"),
            "openai": os.getenv("OPENAI_API_KEY"),
            "screenshot_one": os.getenv("SCREENSHOT_API_KEY")
        }
    
    def is_provider_configured(self, provider: str) -> bool:
        """Check if a provider is properly configured."""
        key_map = {
            "claude": "CLAUDE_API_KEY",
            "gemini": "GEMINI_API_KEY", 
            "openai": "OPENAI_API_KEY"
        }
        
        if provider not in key_map:
            return False
            
        return bool(os.getenv(key_map[provider]))
    
    def get_available_providers(self) -> Dict[str, bool]:
        """Get list of available providers based on configuration."""
        return {
            provider: self.is_provider_configured(provider)
            for provider in ["claude", "gemini", "openai"]
        }

# Global config instance
config = Config()