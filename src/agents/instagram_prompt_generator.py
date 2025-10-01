"""Instagram prompt generator - creates Gemini-ready prompts for image generation."""

from typing import Dict, Any
from .base_agent import BaseAgent
from ai_providers.ai_factory import AIProviderFactory
from ai_providers.base_provider import AICapability

class InstagramPromptGenerator(BaseAgent):
    """Generates detailed Gemini prompts for Instagram image creation."""

    def __init__(self):
        super().__init__("instagram_prompt_generator", "metrics")
        self.ai_provider = AIProviderFactory.get_configured_provider(AICapability.CONTENT_STRATEGY)

    def process(self, url: str, social_content: Dict[str, Any] = None, prompt_file: str = None, **kwargs) -> Dict[str, Any]:
        """
        Process and generate Instagram prompts.

        Args:
            url: The website URL
            social_content: Social content data from social_content_creator (contains design_analysis)
            prompt_file: Optional agent name for loading .md prompts
            **kwargs: Additional parameters

        Returns:
            Generated Instagram prompts data saved to JSON file
        """
        if not social_content:
            raise ValueError("social_content is required")

        # Load instructions from markdown file
        agent_name = prompt_file or self.name
        instructions = self.load_prompt_from_md(agent_name)

        if not instructions:
            raise ValueError(f"Failed to load instructions from {agent_name}.md")

        # Send social content to AI with instructions to generate prompts
        prompts_data = self.ai_provider.generate_instagram_prompts(
            social_content,
            url,
            agent_name=agent_name
        )

        # Add metadata
        prompts_data.update({
            "url": url,
            "timestamp": self.get_timestamp(),
            "ai_model": self.ai_provider.model,
            "ai_provider": self.ai_provider.name
        })

        # Save to metrics/instagram-prompts/{domain-name}-instagram-prompts-{date}.json
        domain = self.sanitize_domain(url)
        filename = self.get_output_filename(domain)
        self.save_json(prompts_data, filename, "instagram-prompts")

        self.logger.info(f"Instagram prompts saved to metrics/instagram-prompts/{filename}")
        return prompts_data

    def get_output_filename(self, domain: str) -> str:
        """Generate output filename for Instagram prompts."""
        return f"{domain}-instagram-prompts-{self.get_timestamp()}.json"