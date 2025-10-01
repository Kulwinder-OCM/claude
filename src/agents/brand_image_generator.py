"""Brand image generator - creates actual Instagram images using Gemini API."""

from typing import Dict, Any
from pathlib import Path
from .base_agent import BaseAgent
from ai_providers.ai_factory import AIProviderFactory
from ai_providers.base_provider import AICapability

class BrandImageGenerator(BaseAgent):
    """Generates Instagram images using Gemini API."""

    def __init__(self):
        super().__init__("brand_image_generator", "metrics")
        self.ai_provider = AIProviderFactory.get_configured_provider(AICapability.IMAGE_GENERATION)

    def process(self, url: str, prompts_data: Dict[str, Any] = None, **kwargs) -> Dict[str, Any]:
        """
        Process and generate brand images.

        Args:
            url: The website URL
            prompts_data: Instagram prompts data from instagram_prompt_generator
            **kwargs: Additional parameters

        Returns:
            Image generation results data with PNG files saved
        """
        if not prompts_data:
            raise ValueError("prompts_data is required")

        domain = self.sanitize_domain(url)

        # Extract prompts from the prompts_data JSON
        prompts = prompts_data.get("prompts", []) or prompts_data.get("instagram_prompts", [])

        if not prompts:
            raise ValueError("No prompts found in prompts_data")

        # Create output directory for images: metrics/images/{domain-name}/
        output_dir = self.output_dir / "images" / domain
        output_dir.mkdir(parents=True, exist_ok=True)

        generation_results = {
            "domain": domain,
            "url": url,
            "timestamp": self.get_timestamp(),
            "total_images": len(prompts),
            "ai_provider": self.ai_provider.name,
            "ai_model": self.ai_provider.model,
            "images": []
        }

        # Generate each image
        for index, prompt_info in enumerate(prompts, 1):
            gemini_prompt = prompt_info.get("gemini_prompt", "")

            if not gemini_prompt:
                self.logger.warning(f"No gemini_prompt found for post {index}, skipping")
                continue

            try:
                self.logger.info(f"Generating image {index}/{len(prompts)} for {domain}")

                # Generate image using AI provider
                image_data = self.ai_provider.generate_image(gemini_prompt)

                # Save image as PNG: {domain-name}-post-{number}.png
                filename = f"{domain}-post-{index}.png"
                filepath = output_dir / filename

                with open(filepath, 'wb') as f:
                    f.write(image_data)

                self.logger.info(f"Saved image: {filepath}")

                generation_results["images"].append({
                    "post_number": index,
                    "filename": filename,
                    "filepath": str(filepath),
                    "file_size": len(image_data),
                    "status": "success"
                })

            except Exception as e:
                self.logger.error(f"Error generating image {index}: {e}")
                generation_results["images"].append({
                    "post_number": index,
                    "status": "failed",
                    "error": str(e)
                })

        # Save generation metadata to metrics/images/{domain-name}/{domain-name}-metadata.json
        metadata_filename = f"{domain}-metadata.json"
        self.save_json(generation_results, metadata_filename, f"images/{domain}")

        self.logger.info(f"Generated {len([img for img in generation_results['images'] if img.get('status') == 'success'])} images in metrics/images/{domain}/")
        return generation_results

    def get_output_filename(self, domain: str) -> str:
        """Generate output filename for image generation metadata."""
        return f"{domain}-metadata.json"