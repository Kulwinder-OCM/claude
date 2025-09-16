"""OpenAI provider implementation."""

import requests
import json
import os
import base64
from typing import Dict, Any, List
from .base_provider import BaseAIProvider, AICapability

class OpenAIProvider(BaseAIProvider):
    """OpenAI provider for text analysis, generation, and image generation."""
    
    def __init__(self, model: str = "gpt-4"):
        super().__init__("openai", model)
        self.api_key = self._get_api_key()
        self.base_url = "https://api.openai.com/v1"
    
    def _get_api_key(self) -> str:
        """Get OpenAI API key from environment."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        return api_key
    
    def _get_capabilities(self) -> List[AICapability]:
        """OpenAI capabilities."""
        return [
            AICapability.TEXT_ANALYSIS,
            AICapability.TEXT_GENERATION,
            AICapability.IMAGE_GENERATION,
            AICapability.WEB_ANALYSIS,
            AICapability.CONTENT_STRATEGY
        ]
    
    def _make_chat_request(self, messages: List[Dict], **kwargs) -> Dict[str, Any]:
        """Make chat completion request to OpenAI API."""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": kwargs.get("max_tokens", 4000)
        }
        
        response = requests.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
        response.raise_for_status()
        
        return response.json()
    
    def analyze_text(self, text: str, prompt: str, **kwargs) -> Dict[str, Any]:
        """Analyze text content with OpenAI."""
        messages = [
            {"role": "system", "content": "You are an expert text analyst."},
            {"role": "user", "content": f"{prompt}\n\nText to analyze:\n{text}"}
        ]
        
        response = self._make_chat_request(messages, **kwargs)
        
        return {
            "analysis": response["choices"][0]["message"]["content"],
            "model": self.model,
            "provider": self.name
        }
    
    def generate_text(self, prompt: str, **kwargs) -> str:
        """Generate text with OpenAI."""
        messages = [
            {"role": "user", "content": prompt}
        ]
        
        response = self._make_chat_request(messages, **kwargs)
        return response["choices"][0]["message"]["content"]
    
    def generate_image(self, prompt: str, **kwargs) -> bytes:
        """Generate image with DALL-E."""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        payload = {
            "model": "dall-e-3",
            "prompt": prompt,
            "size": kwargs.get("size", "1024x1024"),
            "quality": "standard",
            "response_format": "b64_json"
        }
        
        response = requests.post(f"{self.base_url}/images/generations", headers=headers, json=payload)
        response.raise_for_status()
        
        result = response.json()
        image_b64 = result["data"][0]["b64_json"]
        
        return base64.b64decode(image_b64)
    
    def analyze_website(self, html_content: str, url: str, **kwargs) -> Dict[str, Any]:
        """Analyze website content with OpenAI."""
        messages = [
            {"role": "system", "content": "You are a business intelligence analyst. Analyze websites and extract comprehensive business information in JSON format."},
            {"role": "user", "content": f"Analyze this website for: {url}\n\nHTML Content:\n{html_content[:8000]}\n\nProvide comprehensive business intelligence in JSON format."}
        ]
        
        response = self._make_chat_request(messages, **kwargs)
        
        # Try to parse JSON response
        try:
            analysis_text = response["choices"][0]["message"]["content"]
            if "```json" in analysis_text:
                json_start = analysis_text.find("```json") + 7
                json_end = analysis_text.find("```", json_start)
                analysis_text = analysis_text[json_start:json_end]
            
            analysis_data = json.loads(analysis_text)
        except (json.JSONDecodeError, KeyError):
            analysis_data = {
                "raw_analysis": response["choices"][0]["message"]["content"],
                "parsing_error": "Could not parse JSON"
            }
        
        analysis_data.update({
            "url": url,
            "model": self.model,
            "provider": self.name
        })
        
        return analysis_data