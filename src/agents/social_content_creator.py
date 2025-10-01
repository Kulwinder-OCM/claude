"""Social media content creator agent - generates Instagram post concepts."""

from typing import Dict, Any
from .base_agent import BaseAgent
from ai_providers.ai_factory import AIProviderFactory
from ai_providers.base_provider import AICapability

class SocialContentCreator(BaseAgent):
    """Creates Instagram post concepts based on business intelligence."""

    def __init__(self):
        super().__init__("social_content_creator", "metrics")
        self.ai_provider = AIProviderFactory.get_configured_provider(AICapability.CONTENT_STRATEGY)

    def process(self, url: str, business_intel: Dict[str, Any] = None, design_analysis: Dict[str, Any] = None, prompt_file: str = None, **kwargs) -> Dict[str, Any]:
        """
        Process and create social media content.

        Args:
            url: The website URL
            business_intel: Business intelligence data from business_intelligence_analyzer
            design_analysis: Design analysis data from screenshot_analyzer
            prompt_file: Optional agent name for loading .md prompts
            **kwargs: Additional parameters

        Returns:
            Social media content strategy data saved to JSON file
        """
        if not business_intel or not design_analysis:
            raise ValueError("Both business_intel and design_analysis are required")

        # Load instructions from markdown file
        agent_name = prompt_file or self.name
        instructions = self.load_prompt_from_md(agent_name)

        if not instructions:
            raise ValueError(f"Failed to load instructions from {agent_name}.md")

        # Send business intelligence to AI with instructions
        social_content = self.ai_provider.create_content_strategy(
            business_intel,
            design_analysis,
            agent_name=agent_name
        )

        # Add metadata
        social_content.update({
            "url": url,
            "timestamp": self.get_timestamp(),
            "ai_model": self.ai_provider.model,
            "ai_provider": self.ai_provider.name
        })

        # Save to metrics/social-content/{domain-name}-social-content-{date}.json
        domain = self.sanitize_domain(url)
        filename = self.get_output_filename(domain)
        self.save_json(social_content, filename, "social-content")

        self.logger.info(f"Social content saved to metrics/social-content/{filename}")
        return social_content

    def get_output_filename(self, domain: str) -> str:
        """Generate output filename for social content."""
        return f"{domain}-social-content-{self.get_timestamp()}.json"