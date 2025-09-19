"""Screenshot analyzer agent - captures and analyzes website screenshots with advanced AI vision."""

import os
import subprocess
import tempfile
from typing import Dict, Any, List
from PIL import Image
import io
from .base_agent import BaseAgent

class ScreenshotAnalyzer(BaseAgent):
    """Professional Website Screenshot and Design Style Analysis Specialist.

    Captures screenshots using ScreenshotOne API and provides detailed analysis
    of design styles, visual aesthetics, and design trends with AI vision.
    """

    def __init__(self):
        super().__init__("screenshot-analyzer", "metrics")

        # Load environment variables from .env file if not already loaded
        try:
            # Check if key environment variables are already loaded
            if not os.getenv("CLAUDE_API_KEY") or not os.getenv("SCREENSHOT_API_KEY"):
                from dotenv import load_dotenv
                load_dotenv()
                self.logger.info("Environment variables loaded from .env file")
            else:
                self.logger.info("Environment variables already available")
        except ImportError:
            self.logger.warning("python-dotenv not available, checking if env vars are set manually")
        except Exception as e:
            self.logger.warning(f"Could not load .env file: {e}")

        self.screenshot_endpoint = self._get_env_var("SCREENSHOT_ENDPOINT")
        self.screenshot_api_key = self._get_env_var("SCREENSHOT_API_KEY")

        # Initialize AI providers for image analysis
        self._setup_ai_providers()

    def _get_env_var(self, key: str) -> str:
        """Get environment variable with error handling."""
        value = os.getenv(key)
        if not value:
            self.logger.warning(f"Environment variable {key} not set - using fallback analysis")
            return ""
        return value

    def _setup_ai_providers(self):
        """Setup AI providers for image analysis."""
        try:
            # Import with correct relative path
            import sys
            import os

            # Add the src directory to the path so we can import ai_providers
            src_path = os.path.join(os.path.dirname(__file__), '..')
            if src_path not in sys.path:
                sys.path.append(src_path)

            from ai_providers.claude_provider import ClaudeProvider
            from ai_providers.gemini_provider import GeminiProvider

            # Get the configured provider for web analysis
            provider_name = os.getenv('AI_WEB_ANALYSIS_PROVIDER', 'claude').lower()

            self.logger.info(f"Attempting to initialize AI provider: {provider_name}")

            if provider_name == 'claude':
                self.ai_provider = ClaudeProvider()
            elif provider_name == 'gemini':
                self.ai_provider = GeminiProvider()
            else:
                self.logger.warning(f"Unknown AI provider: {provider_name}, defaulting to Claude")
                self.ai_provider = ClaudeProvider()

            self.logger.info(f"Successfully initialized AI provider: {provider_name}")

        except ImportError as e:
            self.logger.error(f"Failed to import AI provider modules: {e}")
            self.ai_provider = None
        except Exception as e:
            self.logger.error(f"Failed to initialize AI provider: {e}")
            import traceback
            self.logger.error(f"Full traceback: {traceback.format_exc()}")
            self.ai_provider = None

    def capture_screenshot_with_bash(self, url: str) -> str:
        """Capture screenshot using bash/curl command and save to temp file."""
        try:
            # Create temporary file for screenshot
            temp_file = "/tmp/screenshot.png"

            # Check if we have the required credentials
            if not self.screenshot_endpoint or not self.screenshot_api_key:
                raise Exception("Screenshot API credentials not available - check SCREENSHOT_ENDPOINT and SCREENSHOT_API_KEY environment variables")

            # Build the full URL for curl
            screenshot_url = f"{self.screenshot_endpoint}?url={url}&access_key={self.screenshot_api_key}&format=png&viewport_width=375&viewport_height=812&device_scale_factor=2&full_page=true&block_cookie_banners=true&block_ads=true"

            # Build curl command
            curl_cmd = [
                "curl", "-o", temp_file, screenshot_url
            ]

            self.logger.info(f"Capturing screenshot for {url}")
            self.logger.info(f"Screenshot API endpoint: {self.screenshot_endpoint}")
            result = subprocess.run(curl_cmd, capture_output=True, text=True)

            if result.returncode != 0:
                self.logger.error(f"Curl stderr: {result.stderr}")
                self.logger.error(f"Curl stdout: {result.stdout}")
                raise Exception(f"Screenshot capture failed: {result.stderr}")

            # Verify file was created and has content
            if not os.path.exists(temp_file):
                raise Exception("Screenshot file was not created")

            file_size = os.path.getsize(temp_file)
            if file_size == 0:
                raise Exception("Screenshot file is empty")

            self.logger.info(f"Screenshot saved to {temp_file}, size: {file_size} bytes")
            return temp_file

        except Exception as e:
            self.logger.error(f"Error capturing screenshot: {e}")
            raise

    def analyze_screenshot_with_ai(self, image_path: str, url: str, prompt_file: str = None) -> Dict[str, Any]:
        """
        Analyze screenshot using AI vision with professional design analysis and dynamic prompts.

        Args:
            image_path: Path to the screenshot image file
            url: The website URL
            prompt_file: Optional agent name for loading .md prompts (defaults to this agent's name)

        Returns:
            Screenshot design analysis data
        """

        if not self.ai_provider:
            self.logger.error("AI provider is None - using fallback analysis")
            self.logger.error("Check AI provider initialization in _setup_ai_providers method")
            return self._fallback_analysis(url)

        self.logger.info(f"AI provider available: {type(self.ai_provider).__name__}")

        # Verify the image file exists
        if not os.path.exists(image_path):
            self.logger.error(f"Screenshot file does not exist: {image_path}")
            return self._fallback_analysis(url)

        # Check if ai_provider has the required method
        if not hasattr(self.ai_provider, 'analyze_image_with_text'):
            self.logger.error(f"AI provider {type(self.ai_provider).__name__} does not have analyze_image_with_text method")
            return self._fallback_analysis(url)

        try:
            # Try to load analysis prompt from markdown file
            agent_name = prompt_file or self.name
            dynamic_prompt = self.load_prompt_from_md(agent_name)

            if dynamic_prompt:
                # Use dynamic prompt from markdown file
                analysis_prompt = f"{dynamic_prompt}\n\nAnalyze this website screenshot for {url}."
            else:
                # Fallback to original hardcoded prompt
                analysis_prompt = f"""
You are a professional brand designer analyzing this website screenshot for {url}.

CRITICAL REQUIREMENTS:
- Return ONLY a JSON object. No explanations, no extra text, no markdown blocks.
- EXAMINE EVERY SINGLE COLOR visible in the screenshot - backgrounds, text, buttons, borders, icons, gradients.
- Extract ACTUAL hex colors you see, not placeholders.
- Identify ALL visible fonts and typography.
- Never use placeholder text like "#ACTUAL_HEX" or "FontName".
- Give exact hex codes for every color (e.g. #FF5722, #1976D2, #FFFFFF).

MANDATORY COLOR ANALYSIS:
Look at EVERY visible element and extract:
1. All background colors (page, sections, cards, etc.)
2. All text colors (headings, body, links, labels)
3. All interactive element colors (buttons, links, forms)
4. All accent colors (borders, icons, highlights)
5. All brand colors (logos, primary elements)

JSON schema you MUST follow exactly:

{{
  "style_snapshot": {{
    "vibe_keywords": ["word1", "word2", "word3"],
    "art_direction": "One short sentence describing the visual style"
  }},
  "color_kit": {{
    "background": {{"hex": "#HEXCODE", "where_seen": "main background"}},
    "brand_primary": {{"hex": "#HEXCODE", "where_seen": "logo/primary buttons"}},
    "text_primary": {{"hex": "#HEXCODE", "where_seen": "main headings"}},
    "text_secondary": {{"hex": "#HEXCODE", "where_seen": "body text"}},
    "accent_colors": [
      {{"hex": "#HEXCODE", "where_seen": "specific UI element", "role": "accent/highlight/border"}},
      {{"hex": "#HEXCODE", "where_seen": "specific UI element", "role": "accent/highlight/border"}}
    ],
    "additional_colors": [
      {{"hex": "#HEXCODE", "where_seen": "specific element", "usage": "description"}}
    ]
  }},
  "typography_kit": {{
    "classification": "serif/sans-serif/monospace",
    "likely_families": [
      {{"name": "FontName", "confidence": 0.8}}
    ],
    "weights_used": {{"h1": 700, "h2": 600, "body": 400}},
    "sizes_observed": {{"h1": "32px", "h2": "24px", "body": "16px"}}
  }},
  "composition": {{
    "alignment": "left/center/right",
    "shape_cues": ["rounded corners", "shadows", "borders"],
    "spacing_patterns": "description of spacing and layout"
  }},
  "visual_feel_description": "detailed sensory description of the design"
}}

IMPORTANT: Analyze the ACTUAL screenshot content. Extract REAL colors you observe, not generic examples.
"""


            # Analyze with AI provider
            self.logger.info(f"Starting AI image analysis for {url}")
            analysis_result = self.ai_provider.analyze_image_with_text(
                image_path=image_path,
                prompt=analysis_prompt
            )

            self.logger.info(f"AI analysis completed, result type: {type(analysis_result)}")
            self.logger.info(f"AI analysis result preview: {str(analysis_result)[:200]}...")

            # Parse JSON response
            import json
            try:
                if isinstance(analysis_result, str):
                    # Extract JSON from response if wrapped in text
                    json_start = analysis_result.find('{')
                    json_end = analysis_result.rfind('}') + 1
                    if json_start != -1 and json_end > json_start:
                        json_str = analysis_result[json_start:json_end]
                        self.logger.info(f"Extracted JSON string: {json_str[:200]}...")
                        parsed_analysis = json.loads(json_str)
                        self.logger.info("Successfully parsed JSON from AI response")
                    else:
                        self.logger.warning("No JSON structure found in AI response")
                        raise ValueError("No JSON found in response")
                else:
                    parsed_analysis = analysis_result
                    self.logger.info("AI response is already structured data")

                # Add metadata
                parsed_analysis.update({
                    "url": url,
                    "timestamp": self.get_timestamp(),
                    "analysis_method": "ai_vision_analysis",
                    "ai_provider": os.getenv('AI_WEB_ANALYSIS_PROVIDER', 'claude'),
                    "prompt_source": f"{agent_name}.md" if dynamic_prompt else "default",
                    "screenshot_api_request": f"{self.screenshot_endpoint}?url={url}&access_key=***&format=png&viewport_width=375&viewport_height=812&device_scale_factor=2&full_page=true&block_cookie_banners=true&block_ads=true"
                })

                self.logger.info("AI analysis completed successfully with structured data")
                return parsed_analysis

            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to parse AI analysis JSON: {e}")
                self.logger.error(f"Raw AI response: {analysis_result}")
                return self._create_fallback_with_ai_text(url, analysis_result)

        except Exception as e:
            self.logger.error(f"AI analysis failed: {e}")
            import traceback
            self.logger.error(f"Full traceback: {traceback.format_exc()}")
            return self._fallback_analysis(url)

    def _create_fallback_with_ai_text(self, url: str, ai_text: str) -> Dict[str, Any]:
        """Create fallback analysis when AI returns non-JSON response."""
        return {
            "url": url,
            "timestamp": self.get_timestamp(),
            "analysis_method": "ai_text_analysis",
            "ai_provider": os.getenv('AI_WEB_ANALYSIS_PROVIDER', 'claude'),
            "raw_analysis": ai_text,
            "style_snapshot": {
                "vibe_keywords": ["modern", "professional", "clean"],
                "art_direction": "AI analysis provided in text format"
            },
            "note": "AI provided detailed text analysis rather than structured JSON"
        }

    def _fallback_analysis(self, url: str) -> Dict[str, Any]:
        """Fallback analysis when AI is not available."""
        return {
            "url": url,
            "timestamp": self.get_timestamp(),
            "analysis_method": "basic_fallback",
            "style_snapshot": {
                "vibe_keywords": ["modern", "clean", "professional"],
                "art_direction": "Basic analysis - AI provider not available"
            },
            "color_kit": {
                "background": {"hex": "#FFFFFF", "where_seen": "assumed main background"},
                "brand_primary": {"hex": "#007AFF", "where_seen": "estimated brand color"},
                "text_primary": {"hex": "#1D1D1F", "where_seen": "standard dark text"},
                "text_secondary": {"hex": "#86868B", "where_seen": "standard gray text"},
                "recommended_pairings": ["Dark text on light background"]
            },
            "typography_kit": {
                "classification": "sans-serif, modern",
                "likely_families": [{"name": "System Font", "confidence": 0.5}],
                "weights_used": {"h1": 700, "h2": 600, "body": 400},
                "hierarchy": {
                    "h1": {"size": "48px", "leading": "tight"},
                    "h2": {"size": "36px", "leading": "normal"},
                    "body": {"size": "16px", "leading": "normal"}
                }
            },
            "note": "Fallback analysis used - screenshot API or AI analysis unavailable"
        }
    
    def process(self, url: str, prompt_file: str = None, **kwargs) -> Dict[str, Any]:
        """
        Process URL and return comprehensive screenshot analysis.

        Args:
            url: The website URL to analyze
            prompt_file: Optional agent name for loading .md prompts (e.g., 'screenshot-analyzer')
            **kwargs: Additional parameters

        Returns:
            Screenshot design analysis data
        """
        # Log any additional parameters passed
        if kwargs:
            self.logger.info(f"Processing with additional parameters: {kwargs}")

        temp_file = None
        try:
            # Capture screenshot using bash/curl method
            temp_file = self.capture_screenshot_with_bash(url)

            # Analyze screenshot with AI vision using optional custom prompt
            analysis = self.analyze_screenshot_with_ai(temp_file, url, prompt_file)

            # Add image dimensions if available
            if temp_file and os.path.exists(temp_file):
                try:
                    with Image.open(temp_file) as img:
                        analysis["image_dimensions"] = {
                            "width": img.width,
                            "height": img.height
                        }
                except Exception as e:
                    self.logger.warning(f"Could not get image dimensions: {e}")

            # Save analysis
            domain = self.sanitize_domain(url)
            filename = self.get_output_filename(domain)
            self.save_json(analysis, filename, "screenshots/analyses")

            self.logger.info(f"Screenshot analysis completed for {url}")
            self.logger.info(f"AI Provider initialized: {self.ai_provider}")

            return analysis

        except Exception as e:
            self.logger.error(f"Error processing {url}: {e}")
            return {
                "error": str(e),
                "url": url,
                "timestamp": self.get_timestamp(),
                "analysis_method": "error_fallback"
            }
        finally:
            # Cleanup temporary screenshot file
            if temp_file and os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                    self.logger.info(f"Cleaned up temporary file: {temp_file}")
                except Exception as e:
                    self.logger.warning(f"Could not remove temp file {temp_file}: {e}")

    def get_output_filename(self, domain: str) -> str:
        """Generate output filename for screenshot analysis."""
        return f"{domain}-design-analysis-{self.get_timestamp()}.json"