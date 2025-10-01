"""Brand image generator - creates simple text-on-background Instagram images."""

from typing import Dict, Any
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import textwrap
from .base_agent import BaseAgent

class BrandImageGenerator(BaseAgent):
    """Generates simple Instagram images with brand colors and fonts."""

    def __init__(self):
        super().__init__("brand_image_generator", "metrics")

    def get_design_data(self, url: str) -> Dict[str, Any]:
        """Load the design analysis JSON file for the URL."""
        domain = self.sanitize_domain(url)
        timestamp = self.get_timestamp()

        # Try to find the most recent design analysis file
        design_dir = self.output_dir / "screenshots" / "analyses"
        design_files = list(design_dir.glob(f"{domain}-design-analysis-*.json"))

        if not design_files:
            raise ValueError(f"No design analysis file found for {domain}")

        # Get the most recent file
        latest_file = sorted(design_files)[-1]

        import json
        with open(latest_file, 'r') as f:
            return json.load(f)

    def hex_to_rgb(self, hex_color: str) -> tuple:
        """Convert hex color to RGB tuple."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def create_text_image(self, text: str, background_color: str, text_color: str,
                         font_family: str = None, post_number: int = 1) -> Image.Image:
        """Create a simple image with text on a colored background."""
        # Instagram square format
        width, height = 1080, 1080

        # Create image with background color
        bg_rgb = self.hex_to_rgb(background_color)
        image = Image.new('RGB', (width, height), bg_rgb)
        draw = ImageDraw.Draw(image)

        # Try to load custom font, fallback to default
        try:
            # Try common font locations
            font_paths = [
                f"/System/Library/Fonts/{font_family}.ttf",
                f"/Library/Fonts/{font_family}.ttf",
                f"/usr/share/fonts/truetype/{font_family.lower()}/{font_family}.ttf",
            ]

            font = None
            for font_path in font_paths:
                try:
                    font = ImageFont.truetype(font_path, 72)
                    break
                except:
                    continue

            if not font:
                # Try system default fonts
                font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 72)
        except:
            # Fallback to PIL default
            font = ImageFont.load_default()
            self.logger.warning("Using default font - custom font not found")

        # Wrap text to fit width with padding
        padding = 80
        max_width = width - (padding * 2)

        # Wrap text manually
        words = text.split()
        lines = []
        current_line = []

        for word in words:
            test_line = ' '.join(current_line + [word])
            # Estimate width (rough approximation)
            if len(test_line) * 40 < max_width:  # Rough character width estimate
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]

        if current_line:
            lines.append(' '.join(current_line))

        # Limit to reasonable number of lines
        if len(lines) > 8:
            lines = lines[:8]
            lines[-1] = lines[-1][:50] + "..."

        wrapped_text = '\n'.join(lines)

        # Get text bounding box
        text_bbox = draw.multiline_textbbox((0, 0), wrapped_text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]

        # Center text
        x = (width - text_width) // 2
        y = (height - text_height) // 2

        # Draw text with increased line spacing
        text_rgb = self.hex_to_rgb(text_color)
        # Increase line spacing by 1.5x (spacing parameter adds extra pixels between lines)
        line_spacing = int(font.size * 0.5)  # Add 50% of font size as extra spacing
        draw.multiline_text((x, y), wrapped_text, fill=text_rgb, font=font, align='center', spacing=line_spacing)

        # Add post number in corner
        number_font_size = 36
        try:
            number_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", number_font_size)
        except:
            number_font = ImageFont.load_default()

        number_text = f"#{post_number}"
        number_bbox = draw.textbbox((0, 0), number_text, font=number_font)
        number_width = number_bbox[2] - number_bbox[0]

        # Bottom right corner
        number_x = width - number_width - 30
        number_y = height - 60
        draw.text((number_x, number_y), number_text, fill=text_rgb, font=number_font)

        return image

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

        # Load design analysis to get brand colors and fonts
        try:
            design_data = self.get_design_data(url)
            self.logger.info(f"Loaded design analysis for {domain}")
        except Exception as e:
            self.logger.error(f"Could not load design analysis: {e}")
            raise

        # Extract brand colors
        color_kit = design_data.get("color_kit", {})

        # Use brand_primary for background color
        background_color = color_kit.get("brand_primary", {}).get("hex", "#000000")

        # Use text_primary for text color
        text_color = color_kit.get("text_primary", {}).get("hex", "#FFFFFF")

        # Ensure contrast - if background and text are too similar, use opposite
        bg_brightness = sum(self.hex_to_rgb(background_color)) / 3
        text_brightness = sum(self.hex_to_rgb(text_color)) / 3

        if abs(bg_brightness - text_brightness) < 100:
            # Not enough contrast, use black or white based on background
            text_color = "#000000" if bg_brightness > 128 else "#FFFFFF"
            self.logger.info(f"Adjusted text color for contrast: {text_color}")

        # Extract font family
        typography_kit = design_data.get("typography_kit", {})
        likely_families = typography_kit.get("likely_families", [])
        font_family = likely_families[0].get("name", "Helvetica") if likely_families else "Helvetica"

        self.logger.info(f"Using background: {background_color}, text: {text_color}, font: {font_family}")

        # Extract prompts from the prompts_data JSON
        prompts = prompts_data.get("prompts", []) or prompts_data.get("instagram_prompts", [])

        if not prompts:
            raise ValueError("No prompts found in prompts_data")

        # Limit to 3 images
        prompts = prompts[:3]

        # Create output directory for images: metrics/images/{domain-name}/
        output_dir = self.output_dir / "images" / domain
        output_dir.mkdir(parents=True, exist_ok=True)

        generation_results = {
            "domain": domain,
            "url": url,
            "timestamp": self.get_timestamp(),
            "total_images": len(prompts),
            "generator": "PIL/Text-on-Background",
            "background_color": background_color,
            "text_color": text_color,
            "font_family": font_family,
            "images": []
        }

        # Generate each image
        for index, prompt_info in enumerate(prompts, 1):
            # Extract the actual message text from the gemini_prompt
            # Look for quoted text like 'Your Website. Your Control.'
            import re

            gemini_prompt = prompt_info.get("gemini_prompt", "")
            theme = prompt_info.get("theme", "")

            # Try to extract quoted text from gemini_prompt
            quoted_texts = re.findall(r"['\"]([^'\"]+)['\"]", gemini_prompt)

            # Filter for actual message text (not color codes or filenames)
            message_text = None
            for text in quoted_texts:
                if not text.startswith('#') and len(text) > 10 and not text.endswith('.png'):
                    message_text = text
                    break

            # Fallback to theme or headline
            text = message_text or theme or prompt_info.get("headline", "") or f"Post {index}"

            # Clean up text
            text = text.strip()

            try:
                self.logger.info(f"Generating image {index}/{len(prompts)} for {domain}")

                # Create simple text image
                image = self.create_text_image(
                    text=text,
                    background_color=background_color,
                    text_color=text_color,
                    font_family=font_family,
                    post_number=index
                )

                # Save image as PNG: {domain-name}-post-{number}.png
                filename = f"{domain}-post-{index}.png"
                filepath = output_dir / filename

                image.save(filepath, 'PNG', optimize=True)
                file_size = filepath.stat().st_size

                self.logger.info(f"Saved image: {filepath}")

                generation_results["images"].append({
                    "post_number": index,
                    "filename": filename,
                    "filepath": str(filepath),
                    "file_size": file_size,
                    "text": text[:100],
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
