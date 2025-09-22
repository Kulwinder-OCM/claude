"""Instagram prompt generator - creates Gemini-ready prompts for image generation."""

from typing import Dict, Any, List
from .base_agent import BaseAgent

class InstagramPromptGenerator(BaseAgent):
    """Generates detailed Gemini prompts for Instagram image creation."""
    
    def __init__(self):
        super().__init__("instagram-prompt-generator", "metrics")
    
    def create_gemini_prompt(self, post: Dict[str, Any], design_guidelines: Dict[str, Any], company_name: str, url: str = "", prompt_file: str = None) -> str:
        """
        Create a detailed Gemini prompt for image generation using dynamic templates.

        Args:
            post: Instagram post data
            design_guidelines: Design analysis data
            company_name: Company name
            prompt_file: Optional agent name for loading .md prompts (defaults to this agent's name)

        Returns:
            Generated Gemini prompt for image creation
        """
        # Try to load prompt template from markdown file
        agent_name = prompt_file or self.name
        dynamic_prompt = self.load_prompt_from_md(agent_name)

        # Always use the hardcoded template which properly extracts and uses brand colors
        # The markdown file is for AI instructions, not Python string templates
        if True:  # Skip dynamic prompt templating to avoid KeyError with JSON braces
            # Fallback to original hardcoded template
            # Extract comprehensive design colors from screenshot analysis
            color_kit = design_guidelines.get("colors", {})  # Updated path for nested structure
            background_color = color_kit.get("background", {}).get("hex", "#FFFFFF")
            brand_primary = color_kit.get("brand_primary", {}).get("hex", "#007AFF")
            text_primary = color_kit.get("text_primary", {}).get("hex", "#1D1D1F")
            text_secondary = color_kit.get("text_secondary", {}).get("hex", "#666666")

            # Extract accent colors for additional visual elements
            accent_colors = color_kit.get("accent_colors", [])
            accent_color = accent_colors[0].get("hex", "#E5E5E5") if accent_colors else "#E5E5E5"

            # Extract additional colors for variety
            additional_colors = color_kit.get("additional_colors", [])

            # Extract comprehensive typography info from screenshot analysis
            typography = design_guidelines.get("typography", {})  # Updated path
            font_classification = typography.get("classification", "modern sans-serif")

            # Get specific font families with confidence scores
            font_families = typography.get("likely_families", [])
            primary_font = font_families[0].get("name", "Inter") if font_families else "Inter"
            font_confidence = font_families[0].get("confidence", 0.8) if font_families else 0.8

            # Use high-confidence fonts, fallback to classification if low confidence
            if font_confidence >= 0.7:
                font_style = f"{primary_font} (or similar {font_classification})"
            else:
                font_style = f"{font_classification} (similar to {primary_font})"

            # Create color palette description for the AI
            color_palette_desc = f"""
BRAND COLOR PALETTE (extracted from actual website):
- Primary Background: {background_color}
- Brand Primary: {brand_primary} (CRITICAL: use this exact color for buttons, CTAs, and key brand elements)
- Text Primary: {text_primary} (main headings, important text)
- Text Secondary: {text_secondary} (body text, descriptions)"""

            if accent_colors:
                accent_desc = "\n- Accent Colors: "
                for i, accent in enumerate(accent_colors[:2]):  # Use up to 2 accent colors
                    accent_desc += f"{accent.get('hex', '#E5E5E5')} ({accent.get('role', 'accent')})"
                    if i < len(accent_colors[:2]) - 1:
                        accent_desc += ", "
                color_palette_desc += accent_desc

            if additional_colors:
                color_palette_desc += f"\n- Additional Colors: {', '.join([c.get('hex', '#E5E5E5') for c in additional_colors[:2]])}"

            prompt = f"""Create a professional Instagram post image (1080x1080 pixels) based on REAL brand analysis:

LAYOUT & COMPOSITION:
- Canvas: Perfect 1080x1080 square format
- Background: Use exact color {background_color} (from brand analysis)
- Padding: 60px margin on all sides for safe viewing area
- Style: Match the brand's actual visual aesthetic

TYPOGRAPHY (based on website analysis):
- Main headline: "{post.get('headline', 'Professional Services')}"
- Font style: {font_style} (confidence: {font_confidence:.0%})
- Headline size: 48-56px, bold weight
- Headline color: {text_primary} (exact brand color)
- Supporting text: "{post.get('subtext', '')}"
- Supporting text color: {text_secondary} (from brand analysis)
- Supporting text size: 18-20px, regular weight
- Line spacing: 1.4x for optimal readability

{color_palette_desc}

CRITICAL BRAND REQUIREMENTS:
- Call-to-action button: "{post.get('call_to_action', 'Learn More')}"
  MUST use exact brand color {brand_primary} as button background
- Button text should be white or high-contrast color for readability
- All colors MUST match the actual brand colors extracted from website
- Do NOT include any company name or brand name text in the image

VISUAL ELEMENTS:
- {post.get('visual_focus', 'Clean professional design matching brand aesthetic')}
- Use accent color {accent_color} for subtle design elements
- Maintain brand consistency with the actual website design
- Professional, modern layout that reflects the brand's visual identity

CONTENT MOOD & POSITIONING:
- Target emotion: {post.get('target_emotion', 'Professional')}
- Content type: {post.get('content_type', 'Brand')}
- Overall feel: Mirror the brand's actual website personality

TECHNICAL REQUIREMENTS:
- High resolution, crisp text rendering
- Mobile-optimized for Instagram feed viewing
- Ensure perfect text readability at small sizes
- No text cutoff at edges
- Colors must be web-accurate and consistent
- Professional, brand-aligned finish

IMPORTANT: This design MUST use the actual extracted brand colors and fonts from the website analysis. Create an image that looks like it belongs to this specific brand's visual identity system."""

            return prompt
    
    def generate_prompts(self, social_content: Dict[str, Any], url: str = "", prompt_file: str = None) -> Dict[str, Any]:
        """
        Generate Gemini prompts for all Instagram posts using dynamic templates.

        Args:
            social_content: Social content strategy data
            prompt_file: Optional agent name for loading .md prompts (defaults to this agent's name)

        Returns:
            Generated prompts data
        """

        company_name = social_content.get("company_name", "Company")
        design_guidelines = social_content.get("design_guidelines", {})
        posts = social_content.get("instagram_posts", [])

        agent_name = prompt_file or self.name

        prompts_data = {
            "company_name": company_name,
            "timestamp": self.get_timestamp(),
            "total_prompts": len(posts),
            "design_guidelines_applied": design_guidelines,
            "prompt_source": f"{agent_name}.md" if prompt_file else "default",
            "prompts": []
        }

        for index, post in enumerate(posts, 1):
            gemini_prompt = self.create_gemini_prompt(post, design_guidelines, company_name, url, prompt_file)

            prompt_data = {
                "post_number": post.get("post_number", index),  # Use sequential index if no post_number provided
                "concept": post.get("concept", "Brand"),
                "headline": post.get("headline", ""),
                "gemini_prompt": gemini_prompt,
                "target_emotion": post.get("target_emotion", "Professional"),
                "content_type": post.get("content_type", "Brand"),
                "visual_specifications": {
                    "format": "1080x1080 Instagram square",
                    "colors": design_guidelines.get("color_kit", {}),
                    "typography": design_guidelines.get("typography_kit", {}),
                    "layout": design_guidelines.get("layout_style", {})
                }
            }

            prompts_data["prompts"].append(prompt_data)

        return prompts_data
    
    def process(self, url: str, social_content: Dict[str, Any] = None, prompt_file: str = None, **kwargs) -> Dict[str, Any]:
        """
        Process and generate Instagram prompts.

        Args:
            url: The website URL
            social_content: Social content strategy data
            prompt_file: Optional agent name for loading .md prompts (e.g., 'instagram-prompt-generator')
            **kwargs: Additional parameters

        Returns:
            Generated Instagram prompts data
        """
        try:
            if not social_content:
                raise ValueError("social_content is required")

            # Generate prompts with optional custom template
            prompts_data = self.generate_prompts(social_content, url, prompt_file)

            # Save prompts
            domain = self.sanitize_domain(url)
            filename = self.get_output_filename(domain)
            self.save_json(prompts_data, filename, "instagram-prompts")

            self.logger.info(f"Instagram prompts generated for {url}")
            return prompts_data

        except Exception as e:
            self.logger.error(f"Error generating Instagram prompts for {url}: {e}")
            return {"error": str(e), "url": url}
    
    def get_output_filename(self, domain: str) -> str:
        """Generate output filename for Instagram prompts."""
        return f"{domain}-instagram-prompts-{self.get_timestamp()}.json"