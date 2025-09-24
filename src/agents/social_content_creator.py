"""Social media content creator agent - generates Instagram post concepts."""

from typing import Dict, Any, List
from .base_agent import BaseAgent
from ai_providers.ai_factory import AIProviderFactory
from ai_providers.base_provider import AICapability

class SocialContentCreator(BaseAgent):
    """Creates Instagram post concepts based on business intelligence."""
    
    def __init__(self):
        super().__init__("social_content_creator", "metrics")
        self.ai_provider = AIProviderFactory.get_configured_provider(AICapability.CONTENT_STRATEGY)
    
    def create_social_content(self, business_intel: Dict[str, Any], design_analysis: Dict[str, Any], prompt_file: str = None) -> Dict[str, Any]:
        """
        Create social media content using AI analysis with dynamic prompts.

        Args:
            business_intel: Business intelligence data
            design_analysis: Design analysis data
            prompt_file: Optional agent name for loading .md prompts (defaults to this agent's name)

        Returns:
            Social media content strategy data
        """
        try:
            # Use the prompt_file parameter or default to this agent's name
            agent_name = prompt_file or self.name

            # Use AI provider for intelligent content strategy with dynamic prompts
            social_content = self.ai_provider.create_content_strategy(business_intel, design_analysis, agent_name=agent_name)

            # Add metadata
            social_content.update({
                "timestamp": self.get_timestamp(),
                "creation_method": "ai_enhanced",
                "ai_model": self.ai_provider.model,
                "ai_provider": self.ai_provider.name,
                "prompt_source": f"{agent_name}.md" if prompt_file else "default",
                "design_guidelines": {
                    "colors": design_analysis.get("color_kit", {}),
                    "typography": design_analysis.get("typography_kit", {}),
                    "layout_style": design_analysis.get("composition", {})
                }
            })

            return social_content

        except Exception as e:
            # Fallback disabled - force md file usage
            self.logger.error(f"AI content creation failed and fallback disabled: {e}")
            raise e  # Re-raise to force retry or proper error handling
    
    def _template_based_content(self, business_intel: Dict[str, Any], design_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback template-based content creation."""
        company_name = business_intel.get("company_overview", {}).get("name", "Company")
        industry = business_intel.get("company_overview", {}).get("industry", "Technology")
        
        posts = [
            {
                "post_number": 1,
                "concept": "Brand Expertise",
                "headline": f"Expert {industry} Solutions",
                "subtext": f"Discover how {company_name} transforms businesses",
                "call_to_action": "Learn More",
                "content_type": "Educational",
                "target_emotion": "Trust",
                "visual_focus": "Professional imagery with brand colors",
                "text_placement": "Center-aligned with generous spacing"
            },
            {
                "post_number": 2,
                "concept": "Innovation Focus",
                "headline": "Innovation Meets Excellence",
                "subtext": f"See what makes {company_name} different",
                "call_to_action": "Get Started",
                "content_type": "Brand Story",
                "target_emotion": "Inspiration",
                "visual_focus": "Modern design elements with brand identity",
                "text_placement": "Left-aligned with bold typography"
            },
            {
                "post_number": 3,
                "concept": "Results & Impact",
                "headline": "Results That Matter",
                "subtext": f"Join successful businesses using {company_name}",
                "call_to_action": "Contact Us",
                "content_type": "Social Proof",
                "target_emotion": "Confidence",
                "visual_focus": "Clean layout with testimonial-style design",
                "text_placement": "Centered with strong hierarchy"
            }
        ]
        
        return {
            "company_name": company_name,
            "timestamp": self.get_timestamp(),
            "creation_method": "template_based",
            "brand_voice": {
                "tone": "Professional yet approachable",
                "personality": ["Expert", "Trustworthy", "Innovative"],
                "messaging_style": "Clear and direct"
            },
            "target_audience": {
                "primary": business_intel.get("market_analysis", {}).get("target_audience", "Business professionals"),
                "demographics": "Decision makers, business owners, managers",
                "interests": ["Business growth", "Digital transformation", "Innovation"]
            },
            "content_strategy": {
                "posting_frequency": "3-4 times per week",
                "best_times": ["9:00 AM", "1:00 PM", "6:00 PM"],
                "hashtag_strategy": f"#{company_name.lower().replace(' ', '')} #{industry.lower()} #business"
            },
            "instagram_posts": posts,
            "design_guidelines": {
                "colors": design_analysis.get("color_kit", {}),
                "typography": design_analysis.get("typography_kit", {}),
                "layout_style": design_analysis.get("composition", {})
            }
        }
    
    def process(self, url: str, business_intel: Dict[str, Any] = None, design_analysis: Dict[str, Any] = None, prompt_file: str = None, **kwargs) -> Dict[str, Any]:
        """
        Process and create social media content.

        Args:
            url: The website URL
            business_intel: Business intelligence data
            design_analysis: Design analysis data
            prompt_file: Optional agent name for loading .md prompts (e.g., 'social_content_creator')
            **kwargs: Additional parameters

        Returns:
            Social media content strategy data
        """
        try:
            if not business_intel or not design_analysis:
                raise ValueError("Both business_intel and design_analysis are required")

            # Create social content with optional custom prompt
            social_content = self.create_social_content(business_intel, design_analysis, prompt_file)

            # Save content
            domain = self.sanitize_domain(url)
            filename = self.get_output_filename(domain)
            self.save_json(social_content, filename, "social_content")

            self.logger.info(f"Social content creation completed for {url}")
            return social_content

        except Exception as e:
            self.logger.error(f"Error creating social content for {url}: {e}")
            return {"error": str(e), "url": url}
    
    def get_output_filename(self, domain: str) -> str:
        """Generate output filename for social content."""
        return f"{domain}-social-content-{self.get_timestamp()}.json"