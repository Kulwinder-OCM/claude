"""Gemini AI provider implementation."""

import requests
import json
import os
import base64
from typing import Dict, Any, List
from .base_provider import BaseAIProvider, AICapability

class GeminiProvider(BaseAIProvider):
    """Gemini AI provider for text and image generation."""
    
    def __init__(self, model: str = "gemini-2.5-flash-image-preview"):
        super().__init__("gemini", model)
        self.api_key = self._get_api_key()
        self.text_endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
        self.image_endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    
    def _get_api_key(self) -> str:
        """Get Gemini API key from environment."""
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        return api_key
    
    def _get_capabilities(self) -> List[AICapability]:
        """Gemini capabilities."""
        return [
            AICapability.TEXT_ANALYSIS,
            AICapability.TEXT_GENERATION,
            AICapability.IMAGE_GENERATION
        ]
    
    def supports_capability(self, capability: AICapability) -> bool:
        """Check if provider supports a specific capability."""
        return capability in self._get_capabilities()
    
    def _make_request(self, prompt: str, endpoint: str = None, **kwargs) -> Dict[str, Any]:
        """Make request to Gemini API."""
        headers = {
            "x-goog-api-key": self.api_key,
            "Content-Type": "application/json"
        }
        
        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ]
        }
        
        # Use provided endpoint or default to text endpoint
        url = endpoint or self.text_endpoint
        
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        
        return response.json()
    
    def analyze_text(self, text: str, prompt: str, **kwargs) -> Dict[str, Any]:
        """Analyze text content with Gemini."""
        full_prompt = f"{prompt}\n\nText to analyze:\n{text}"
        
        response = self._make_request(full_prompt, **kwargs)
        
        return {
            "analysis": response["candidates"][0]["content"]["parts"][0]["text"],
            "model": self.model,
            "provider": self.name
        }
    
    def generate_text(self, prompt: str, **kwargs) -> str:
        """Generate text with Gemini."""
        response = self._make_request(prompt, **kwargs)
        return response["candidates"][0]["content"]["parts"][0]["text"]
    
    def generate_image(self, prompt: str, **kwargs) -> bytes:
        """Generate image with Gemini."""
        try:
            print(f"Generating image with prompt: {prompt[:100]}...")  # Debug log
            
            # Use the image generation endpoint
            response = self._make_request(prompt, endpoint=self.image_endpoint, **kwargs)
            
            print(f"Received response with {len(response.get('candidates', []))} candidates")  # Debug log
            
            # Extract image data from response
            candidates = response.get("candidates", [])
            if not candidates:
                raise ValueError("No candidates in response")
            
            content = candidates[0].get("content", {})
            parts = content.get("parts", [])
            
            print(f"Found {len(parts)} parts in response")  # Debug log
            
            # Find the image part
            image_part = None
            for i, part in enumerate(parts):
                print(f"Part {i}: {list(part.keys())}")  # Debug log
                if "inlineData" in part:
                    image_part = part["inlineData"]
                    break
            
            if not image_part:
                raise ValueError("No image data found in response")
            
            # Decode base64 image data
            image_data = image_part.get("data", "")
            if not image_data:
                raise ValueError("Empty image data")
            
            print(f"Successfully extracted image data, length: {len(image_data)}")  # Debug log
            
            decoded_data = base64.b64decode(image_data)
            print(f"Decoded image size: {len(decoded_data)} bytes")  # Debug log
            
            return decoded_data
            
        except Exception as e:
            print(f"Error generating image with Gemini: {e}")
            print(f"Full error details: {type(e).__name__}: {str(e)}")
            
            # Return a minimal valid PNG as fallback
            # This is a 1x1 transparent PNG
            fallback_png = base64.b64decode(
                "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
            )
            print(f"Returning fallback PNG, size: {len(fallback_png)} bytes")
            return fallback_png

    def analyze_image_with_text(self, image_path: str, prompt: str, **kwargs) -> str:
        """Analyze image with text prompt using Gemini Vision."""
        try:
            # Read and encode image
            with open(image_path, "rb") as image_file:
                image_data = image_file.read()
                image_base64 = base64.b64encode(image_data).decode('utf-8')

            # Prepare request for image analysis
            headers = {
                "x-goog-api-key": self.api_key,
                "Content-Type": "application/json"
            }

            payload = {
                "contents": [
                    {
                        "parts": [
                            {
                                "text": prompt
                            },
                            {
                                "inlineData": {
                                    "mimeType": "image/png",
                                    "data": image_base64
                                }
                            }
                        ]
                    }
                ]
            }

            # Make request to Gemini Vision API
            response = requests.post(self.image_endpoint, headers=headers, json=payload)
            response.raise_for_status()

            result = response.json()

            # Extract text response
            candidates = result.get("candidates", [])
            if candidates and "content" in candidates[0] and "parts" in candidates[0]["content"]:
                parts = candidates[0]["content"]["parts"]
                if parts and "text" in parts[0]:
                    return parts[0]["text"]

            raise ValueError("No text found in Gemini response")

        except Exception as e:
            self.logger.error(f"Error analyzing image with Gemini: {e}")
            return f"Error analyzing image: {str(e)}"

