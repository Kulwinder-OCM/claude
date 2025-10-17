"""Screenshot analyzer agent - captures and analyzes website screenshots."""

import os
import json
from typing import Dict, Any
from PIL import Image
from .base_agent import BaseAgent
from ai_providers.ai_factory import AIProviderFactory
from ai_providers.base_provider import AICapability

class ScreenshotAnalyzer(BaseAgent):
    """Captures website screenshots and analyzes design style."""

    def __init__(self):
        super().__init__("screenshot_analyzer", "metrics")
        self.screenshot_endpoint = os.getenv("SCREENSHOT_ENDPOINT")
        self.screenshot_api_key = os.getenv("SCREENSHOT_API_KEY")
        self.ai_provider = AIProviderFactory.get_configured_provider(AICapability.WEB_ANALYSIS)

    def extract_css_data(self, url: str) -> Dict[str, Any]:
        """Extract actual CSS colors and fonts from the webpage with frequency-based prioritization."""
        import requests
        from bs4 import BeautifulSoup
        import re
        from collections import Counter

        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=120)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            color_frequency = Counter()
            fonts = set()

            # Helper to convert RGB to Hex
            def rgb_to_hex(rgb_str):
                try:
                    numbers = re.findall(r'\d+', rgb_str)
                    if len(numbers) >= 3:
                        r, g, b = int(numbers[0]), int(numbers[1]), int(numbers[2])
                        return f'#{r:02X}{g:02X}{b:02X}'
                except:
                    pass
                return None

            # Helper to normalize hex colors
            def normalize_hex(color):
                color = color.upper()
                if len(color) == 4:  # #RGB to #RRGGBB
                    color = '#' + ''.join([c*2 for c in color[1:]])
                return color

            # Extract from style tags with priority weighting
            for style_tag in soup.find_all('style'):
                style_content = style_tag.string if style_tag.string else ''

                # CSS variables (highest priority - these are intentional brand colors)
                css_vars = re.findall(r'--[\w-]*(?:color|primary|brand|accent|theme)[\w-]*:\s*(#[a-fA-F0-9]{6}|#[a-fA-F0-9]{3}\b|rgb\([^)]+\))', style_content, re.IGNORECASE)
                for color in css_vars:
                    if color.startswith('#'):
                        color_frequency[normalize_hex(color)] += 10
                    elif color.startswith('rgb'):
                        hex_color = rgb_to_hex(color)
                        if hex_color:
                            color_frequency[hex_color] += 10

                # Brand-relevant selectors (high priority)
                brand_patterns = [
                    r'(?:button|\.btn|\.button)[^{]*\{[^}]*(?:background-color|background|color|border-color):\s*(#[a-fA-F0-9]{6}|#[a-fA-F0-9]{3}\b|rgb\([^)]+\))',
                    r'(?:header|\.header|nav|\.nav)[^{]*\{[^}]*(?:background-color|background|color|border-color):\s*(#[a-fA-F0-9]{6}|#[a-fA-F0-9]{3}\b|rgb\([^)]+\))',
                    r'(?:\.primary|\.brand|\.accent|\.highlight)[^{]*\{[^}]*(?:background-color|background|color|border-color):\s*(#[a-fA-F0-9]{6}|#[a-fA-F0-9]{3}\b|rgb\([^)]+\))',
                    r'(?:a:hover|a:active|\.link:hover)[^{]*\{[^}]*(?:color|background|border-color):\s*(#[a-fA-F0-9]{6}|#[a-fA-F0-9]{3}\b|rgb\([^)]+\))',
                    r'(?:\.cta|\.call-to-action|\.action)[^{]*\{[^}]*(?:background-color|background|color|border-color):\s*(#[a-fA-F0-9]{6}|#[a-fA-F0-9]{3}\b|rgb\([^)]+\))'
                ]

                for pattern in brand_patterns:
                    matches = re.findall(pattern, style_content, re.IGNORECASE)
                    for color in matches:
                        if color.startswith('#'):
                            normalized = normalize_hex(color)
                            if normalized not in ['#FFFFFF', '#000000', '#FFF', '#000']:
                                color_frequency[normalized] += 5
                        elif color.startswith('rgb'):
                            hex_color = rgb_to_hex(color)
                            if hex_color and hex_color not in ['#FFFFFF', '#000000']:
                                color_frequency[hex_color] += 5

                # Extract ALL color declarations to catch accent colors (lower priority)
                all_color_declarations = re.findall(r'(?:color|background-color|border-color):\s*(#[a-fA-F0-9]{6}|#[a-fA-F0-9]{3}\b)', style_content)
                for color in all_color_declarations:
                    normalized = normalize_hex(color)
                    if normalized not in ['#FFFFFF', '#000000', '#FFF', '#000']:
                        color_frequency[normalized] += 1  # Lower weight for general colors

                # Extract fonts
                font_families = re.findall(r'font-family:\s*([^;}]+)', style_content)
                for font_list in font_families:
                    for font in font_list.split(','):
                        clean_font = font.strip().replace('"', '').replace("'", '')
                        if clean_font and clean_font not in ['sans-serif', 'serif', 'monospace', 'cursive', 'fantasy', 'inherit']:
                            fonts.add(clean_font)

            # Extract from brand-relevant elements (medium priority)
            brand_elements = soup.select('header, nav, button, .btn, .button, .logo, [class*="brand"], [class*="primary"]')
            for element in brand_elements[:50]:  # Limit to first 50
                if element.get('style'):
                    colors = re.findall(r'#[a-fA-F0-9]{6}|#[a-fA-F0-9]{3}\b|rgb\([^)]+\)', element['style'])
                    for color in colors:
                        if color.startswith('#'):
                            normalized = normalize_hex(color)
                            if normalized not in ['#FFFFFF', '#000000']:
                                color_frequency[normalized] += 3
                        elif color.startswith('rgb'):
                            hex_color = rgb_to_hex(color)
                            if hex_color and hex_color not in ['#FFFFFF', '#000000']:
                                color_frequency[hex_color] += 3

            # Get most frequent colors (likely brand colors)
            most_common = color_frequency.most_common(15)

            # Include colors used 2+ times (lowered threshold to catch accent colors like #f60)
            extracted_colors = [color for color, count in most_common if count >= 2]

            # Ensure we have at least 8 colors for a good palette
            if len(extracted_colors) < 8 and len(most_common) > len(extracted_colors):
                extracted_colors = [color for color, count in most_common[:12]]

            self.logger.info(f"Found {len(color_frequency)} unique colors, selected {len(extracted_colors)} brand colors")
            self.logger.info(f"Top colors with frequency: {dict(most_common[:8])}")

            return {
                "extracted_colors": extracted_colors,
                "extracted_fonts": sorted(list(fonts))[:10],
                "color_frequencies": dict(most_common)
            }

        except Exception as e:
            self.logger.warning(f"Could not extract CSS data: {e}")
            return {
                "extracted_colors": [],
                "extracted_fonts": [],
                "color_frequencies": {}
            }

    def capture_screenshot(self, url: str) -> str:
        """Capture screenshot using ScreenshotOne API and save to temp file."""
        import requests

        temp_file = "/tmp/screenshot.png"

        if not self.screenshot_endpoint or not self.screenshot_api_key:
            raise Exception("Screenshot API credentials not configured")

        # Build screenshot request with proper parameters
        params = {
            'url': url,
            'access_key': self.screenshot_api_key,
            'format': 'png',
            'viewport_width': 1920,
            'viewport_height': 1080,
            'device_scale_factor': 1,
            'full_page': True,
            'block_cookie_banners': True,
            'block_ads': True
        }

        # Download screenshot using requests
        self.logger.info(f"Capturing screenshot for {url}")
        response = requests.get(self.screenshot_endpoint, params=params, timeout=60)

        # Check for errors
        if response.status_code != 200:
            error_msg = f"Screenshot API error {response.status_code}: {response.text}"
            self.logger.error(error_msg)
            raise Exception(error_msg)

        # Save screenshot
        with open(temp_file, 'wb') as f:
            f.write(response.content)

        if not os.path.exists(temp_file) or os.path.getsize(temp_file) == 0:
            raise Exception("Screenshot file was not created or is empty")

        self.logger.info(f"Screenshot saved to {temp_file}, size: {os.path.getsize(temp_file)} bytes")
        return temp_file

    def _compress_image_if_needed(self, image_path: str) -> str:
        """Compress image if it's too large for Claude API (5 MB base64 limit)."""
        import base64

        # Check current size
        file_size = os.path.getsize(image_path)

        # Base64 encoding increases size by ~33%, so we need the file to be < 3.75 MB
        # to stay under the 5 MB base64 limit
        max_file_size = 3_500_000  # 3.5 MB to be safe

        if file_size <= max_file_size:
            self.logger.info(f"Image size OK: {file_size} bytes")
            return image_path

        self.logger.info(f"Image too large ({file_size} bytes), compressing...")

        # Compress the image
        with Image.open(image_path) as img:
            # Convert RGBA to RGB if needed
            if img.mode in ('RGBA', 'P', 'LA'):
                # Create white background
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                if img.mode in ('RGBA', 'LA'):
                    background.paste(img, mask=img.split()[-1])
                    img = background
                else:
                    img = img.convert('RGB')

            # Resize if needed (keep under 2000px on longest side for better compression)
            width, height = img.size
            max_dimension = 2000
            if max(width, height) > max_dimension:
                if width > height:
                    new_width = max_dimension
                    new_height = int(height * (max_dimension / width))
                else:
                    new_height = max_dimension
                    new_width = int(width * (max_dimension / height))

                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                self.logger.info(f"Resized image to {new_width}x{new_height}")

            # Save compressed version
            compressed_path = "/tmp/screenshot_compressed.jpg"
            img.save(compressed_path, 'JPEG', quality=85, optimize=True)

            compressed_size = os.path.getsize(compressed_path)
            self.logger.info(f"Compressed image size: {compressed_size} bytes")

            return compressed_path

    def analyze_screenshot(self, image_path: str, url: str, prompt_file: str = None, css_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Analyze screenshot using AI vision.

        Args:
            image_path: Path to screenshot image
            url: Website URL
            prompt_file: Optional agent name for loading .md prompts
            css_data: Extracted CSS colors and fonts

        Returns:
            Design analysis data
        """
        # Compress image if needed before analysis
        compressed_path = self._compress_image_if_needed(image_path)

        # Load instructions from markdown file
        agent_name = prompt_file or self.name
        instructions = self.load_prompt_from_md(agent_name)

        if not instructions:
            raise ValueError(f"Failed to load instructions from {agent_name}.md")

        # Build prompt with instructions and CSS data
        css_context = ""
        if css_data and (css_data.get("extracted_colors") or css_data.get("extracted_fonts")):
            css_context = f"""

EXTRACTED CSS DATA FROM WEBPAGE:
Colors found in CSS: {', '.join(css_data.get('extracted_colors', [])[:15])}
Fonts found in CSS: {', '.join(css_data.get('extracted_fonts', [])[:8])}

IMPORTANT: Use these ACTUAL extracted colors and fonts in your analysis. These are the real brand colors and fonts from the website's CSS."""

        analysis_prompt = f"""{instructions}

Analyze this website screenshot for {url} and return the JSON.
{css_context}"""

        # Analyze with AI
        self.logger.info(f"Analyzing screenshot with AI")
        analysis_result = self.ai_provider.analyze_image_with_text(
            image_path=compressed_path,
            prompt=analysis_prompt
        )

        # Parse JSON from AI response
        if isinstance(analysis_result, str):
            # Extract JSON from text response
            json_start = analysis_result.find('{')
            json_end = analysis_result.rfind('}') + 1
            if json_start != -1 and json_end > json_start:
                json_str = analysis_result[json_start:json_end]
                parsed_analysis = json.loads(json_str)
            else:
                raise ValueError("No valid JSON found in AI response")
        else:
            parsed_analysis = analysis_result

        # Add metadata
        parsed_analysis.update({
            "url": url,
            "timestamp": self.get_timestamp(),
            "ai_provider": self.ai_provider.name,
            "ai_model": self.ai_provider.model
        })

        return parsed_analysis

    def process(self, url: str, prompt_file: str = None, **kwargs) -> Dict[str, Any]:
        """
        Process URL and return screenshot analysis.

        Args:
            url: The website URL to analyze
            prompt_file: Optional agent name for loading .md prompts
            **kwargs: Additional parameters

        Returns:
            Screenshot design analysis data saved to JSON file
        """
        temp_file = None
        try:
            # Extract CSS data from webpage first
            self.logger.info(f"Extracting CSS data from {url}")
            css_data = self.extract_css_data(url)

            # Capture screenshot
            temp_file = self.capture_screenshot(url)

            # Analyze screenshot with CSS data
            analysis = self.analyze_screenshot(temp_file, url, prompt_file, css_data)

            # Store CSS data in analysis for reference
            if css_data["extracted_colors"]:
                analysis["css_extracted_colors"] = css_data["extracted_colors"]
                self.logger.info(f"Extracted {len(css_data['extracted_colors'])} colors from CSS")

            if css_data["extracted_fonts"]:
                analysis["css_extracted_fonts"] = css_data["extracted_fonts"]
                self.logger.info(f"Extracted {len(css_data['extracted_fonts'])} fonts from CSS")

            # Add image dimensions
            if temp_file and os.path.exists(temp_file):
                try:
                    with Image.open(temp_file) as img:
                        analysis["image_dimensions"] = {
                            "width": img.width,
                            "height": img.height
                        }
                except Exception as e:
                    self.logger.warning(f"Could not get image dimensions: {e}")

            # Save to metrics/screenshots/analyses/{domain-name}-design-analysis-{date}.json
            domain = self.sanitize_domain(url)
            filename = self.get_output_filename(domain)
            self.save_json(analysis, filename, "screenshots/analyses")

            self.logger.info(f"Screenshot analysis saved to metrics/screenshots/analyses/{filename}")
            return analysis

        except Exception as e:
            self.logger.error(f"Error processing {url}: {e}")
            raise
        finally:
            # Cleanup temporary screenshot
            if temp_file and os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                    self.logger.info(f"Cleaned up temporary file")
                except Exception as e:
                    self.logger.warning(f"Could not remove temp file: {e}")

    def get_output_filename(self, domain: str) -> str:
        """Generate output filename for screenshot analysis."""
        return f"{domain}-design-analysis-{self.get_timestamp()}.json"