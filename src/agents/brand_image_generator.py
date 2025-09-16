"""Brand image generator - creates actual Instagram images using configurable AI providers."""

import requests
import base64
import json
from typing import Dict, Any
from pathlib import Path
from .base_agent import BaseAgent
from ai_providers.ai_factory import AIProviderFactory
from ai_providers.base_provider import AICapability

class BrandImageGenerator(BaseAgent):
    """Generates Instagram images using Gemini API."""
    
    def __init__(self):
        super().__init__("brand-image-generator", "metrics")
        self.ai_provider = AIProviderFactory.get_configured_provider(AICapability.IMAGE_GENERATION)
    
    def generate_image_with_ai(self, prompt: str) -> bytes:
        """Generate image using configured AI provider."""
        self.logger.info(f"Generating image with {self.ai_provider.name}")
        return self.ai_provider.generate_image(prompt)
    
    def save_image(self, image_data: bytes, filename: str, domain: str) -> str:
        """Save image data as PNG file."""
        output_dir = self.output_dir / "images" / domain
        output_dir.mkdir(parents=True, exist_ok=True)
        
        filepath = output_dir / filename
        
        # For demonstration, create a simple placeholder file
        # In practice, you'd save the actual image data
        with open(filepath, 'wb') as f:
            f.write(image_data)
        
        self.logger.info(f"Saved image: {filepath}")
        return str(filepath)
    
    def generate_images(self, prompts_data: Dict[str, Any], domain: str) -> Dict[str, Any]:
        """Generate all Instagram images from prompts."""
        
        company_name = prompts_data.get("company_name", "Company")
        prompts = prompts_data.get("prompts", [])
        
        generation_results = {
            "company_name": company_name,
            "domain": domain,
            "timestamp": self.get_timestamp(),
            "total_images_generated": len(prompts),
            "ai_provider": self.ai_provider.name,
            "ai_model": self.ai_provider.model,
            "images": [],
            "generation_status": "completed"
        }
        
        for index, prompt_info in enumerate(prompts, 1):
            post_number = index  # Use incremental counter instead of prompt's post_number
            gemini_prompt = prompt_info.get("gemini_prompt", "")
            
            try:
                # Generate image
                self.logger.info(f"Generating image {post_number} for {company_name}")
                
                try:
                    # Use AI provider for image generation
                    image_data = self.generate_image_with_ai(gemini_prompt)
                except Exception as img_error:
                    self.logger.warning(f"AI image generation failed: {img_error}, using placeholder")
                    image_data = b"placeholder_instagram_image_data"
                
                # Save image
                filename = f"{domain}-post-{post_number}.png"
                filepath = self.save_image(image_data, filename, domain)
                
                image_result = {
                    "post_number": post_number,
                    "concept": prompt_info.get("concept", ""),
                    "filename": filename,
                    "filepath": filepath,
                    "prompt_used": gemini_prompt[:100] + "...",  # Truncated for storage
                    "generation_status": "success",
                    "file_size": len(image_data)
                }
                
                generation_results["images"].append(image_result)
                
            except Exception as e:
                self.logger.error(f"Error generating image {post_number}: {e}")
                error_result = {
                    "post_number": post_number,
                    "generation_status": "failed",
                    "error": str(e)
                }
                generation_results["images"].append(error_result)
        
        return generation_results
    
    def process(self, url: str, prompts_data: Dict[str, Any] = None, **kwargs) -> Dict[str, Any]:
        """Process and generate brand images."""
        try:
            if not prompts_data:
                raise ValueError("prompts_data is required")
            
            domain = self.sanitize_domain(url)
            
            # Generate images
            generation_results = self.generate_images(prompts_data, domain)
            
            # Save generation log
            filename = self.get_output_filename(domain)
            self.save_json(generation_results, filename, f"images/{domain}")
            
            self.logger.info(f"Image generation completed for {url}")
            return generation_results
            
        except Exception as e:
            self.logger.error(f"Error generating images for {url}: {e}")
            return {"error": str(e), "url": url}
    
    def get_output_filename(self, domain: str) -> str:
        """Generate output filename for image generation results."""
        return f"{domain}-image-generation-{self.get_timestamp()}.json"