"""Claude AI provider implementation."""

import requests
import json
import os
from typing import Dict, Any, List
from .base_provider import BaseAIProvider, AICapability

class ClaudeProvider(BaseAIProvider):
    """Claude AI provider for text analysis and generation."""
    
    def __init__(self, model: str = "claude-3-5-sonnet-20241022"):
        super().__init__("claude", model)
        self.api_key = self._get_api_key()
        self.base_url = "https://api.anthropic.com/v1/messages"
    
    def _get_api_key(self) -> str:
        """Get Claude API key from environment."""
        api_key = os.getenv("CLAUDE_API_KEY")
        if not api_key:
            raise ValueError("CLAUDE_API_KEY environment variable not set")
        return api_key
    
    def _get_capabilities(self) -> List[AICapability]:
        """Claude capabilities."""
        return [
            AICapability.TEXT_ANALYSIS,
            AICapability.TEXT_GENERATION,
            AICapability.WEB_ANALYSIS,
            AICapability.CONTENT_STRATEGY
        ]
    
    def _make_request(self, prompt: str, system_prompt: str = None, content: List = None, **kwargs) -> Dict[str, Any]:
        """Make request to Claude API with support for image content."""
        import time

        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01"
        }

        # Use provided content or create text content from prompt
        if content:
            messages = [{"role": "user", "content": content}]
        else:
            messages = [{"role": "user", "content": [{"type": "text", "text": prompt}]}]

        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": kwargs.get("max_tokens", 4000)
        }

        if system_prompt:
            payload["system"] = system_prompt

        # Add retry logic for API overload issues
        max_retries = 2  # Less retries for regular requests
        for attempt in range(max_retries):
            try:
                response = requests.post(self.base_url, headers=headers, json=payload)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 529:  # Overloaded
                    if attempt < max_retries - 1:
                        wait_time = (attempt + 1) * 3  # 3, 6 seconds
                        print(f"Claude API overloaded, retrying in {wait_time} seconds...")
                        time.sleep(wait_time)
                        continue
                raise
    
    def analyze_text(self, text: str, prompt: str, **kwargs) -> Dict[str, Any]:
        """Analyze text content with Claude."""
        full_prompt = f"{prompt}\n\nText to analyze:\n{text}"
        
        response = self._make_request(full_prompt, **kwargs)
        
        return {
            "analysis": response["content"][0]["text"],
            "model": self.model,
            "provider": self.name
        }
    
    def generate_text(self, prompt: str, **kwargs) -> str:
        """Generate text with Claude."""
        response = self._make_request(prompt, **kwargs)
        return response["content"][0]["text"]
    
    def analyze_website(self, html_content: str, url: str, **kwargs) -> Dict[str, Any]:
        """Analyze website content with Claude."""
        system_prompt = """You are a business intelligence analyst. Analyze the provided website content and extract comprehensive business information.

CRITICAL REQUIREMENTS:
1. Return ONLY a valid JSON object
2. No explanations, no markdown formatting, no additional text before or after the JSON
3. Start your response with { and end with }
4. Do not wrap JSON in code blocks or use ``` markers

Required JSON structure:
{
  "company_overview": {
    "name": "Company Name",
    "description": "Brief company description",
    "industry": "Industry sector",
    "location": "Location if available",
    "size": "Company size if determinable"
  },
  "services_products": {
    "main_offerings": ["Service 1", "Service 2"],
    "value_propositions": ["Value prop 1", "Value prop 2"]
  },
  "target_market": {
    "audience": "Primary target audience",
    "customer_segments": ["Segment 1", "Segment 2"]
  },
  "competitive_advantages": ["Advantage 1", "Advantage 2"],
  "business_model": {
    "revenue_model": "How they make money",
    "key_metrics": ["Metric 1", "Metric 2"]
  },
  "brand_positioning": {
    "tone": "Brand tone",
    "messaging": "Core messaging",
    "personality": ["Trait 1", "Trait 2"]
  }
}

Extract actual information from the website content. If specific information isn't available, use reasonable inferences based on what you can observe.

REMEMBER: Your entire response must be valid JSON starting with { and ending with }."""

        prompt = f"""Analyze the website content for: {url}

HTML Content:
{html_content[:8000]}

Return only the JSON analysis object, no other text."""

        response = self._make_request(prompt, system_prompt, **kwargs)

        # Enhanced JSON parsing with multiple fallback strategies
        try:
            analysis_text = response["content"][0]["text"]

            # Strategy 1: Try direct JSON parsing
            try:
                analysis_data = json.loads(analysis_text)
                self._add_metadata(analysis_data, url)
                return analysis_data
            except json.JSONDecodeError:
                pass

            # Strategy 2: Extract JSON from markdown blocks
            if "```json" in analysis_text:
                json_start = analysis_text.find("```json") + 7
                json_end = analysis_text.find("```", json_start)
                if json_end != -1:
                    json_str = analysis_text[json_start:json_end].strip()
                    try:
                        analysis_data = json.loads(json_str)
                        self._add_metadata(analysis_data, url)
                        return analysis_data
                    except json.JSONDecodeError:
                        pass

            # Strategy 3: Find JSON object boundaries with improved parsing
            json_start = analysis_text.find('{')
            if json_start != -1:
                # Find the matching closing brace
                brace_count = 0
                json_end = json_start
                for i, char in enumerate(analysis_text[json_start:]):
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            json_end = json_start + i + 1
                            break

                if json_end > json_start:
                    json_str = analysis_text[json_start:json_end]
                    try:
                        analysis_data = json.loads(json_str)
                        self._add_metadata(analysis_data, url)
                        return analysis_data
                    except json.JSONDecodeError:
                        pass

            # Strategy 4: Parse embedded JSON within text using regex
            import re
            json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
            json_matches = re.findall(json_pattern, analysis_text)

            for match in json_matches:
                try:
                    # Try to parse each potential JSON object found
                    potential_json = json.loads(match)
                    if isinstance(potential_json, dict) and len(potential_json) > 3:
                        self._add_metadata(potential_json, url)
                        return potential_json
                except json.JSONDecodeError:
                    continue

            # Strategy 5: Extract JSON from explanatory text
            lines = analysis_text.split('\n')
            json_lines = []
            in_json = False

            for line in lines:
                stripped = line.strip()
                if stripped.startswith('{') or in_json:
                    json_lines.append(line)
                    in_json = True
                if stripped.endswith('}') and in_json:
                    break

            if json_lines:
                json_str = '\n'.join(json_lines)
                try:
                    analysis_data = json.loads(json_str)
                    self._add_metadata(analysis_data, url)
                    return analysis_data
                except json.JSONDecodeError:
                    pass

            # Strategy 6: Last resort - return raw text with parsing error
            return {
                "raw_analysis": analysis_text,
                "parsing_error": "Could not parse JSON, returned raw text"
            }

        except (KeyError, IndexError):
            return {
                "raw_analysis": str(response),
                "parsing_error": "Invalid response structure"
            }

    def _add_metadata(self, analysis_data: Dict[str, Any], url: str) -> None:
        """Add metadata to analysis data."""
        analysis_data.update({
            "url": url,
            "model": self.model,
            "provider": self.name
        })

    def create_content_strategy(self, business_data: Dict[str, Any], design_data: Dict[str, Any] = None, **kwargs) -> Dict[str, Any]:
        """Create social media content strategy with Claude."""
        system_prompt = """You are a social media strategist. Create Instagram post concepts based on business intelligence and design data.
        
        Return a JSON object with:
        - brand_voice: tone, personality, messaging_style
        - target_audience: demographics, interests, pain_points
        - content_strategy: themes, posting_frequency, best_times
        - instagram_posts: array of 3 post concepts with headline, subtext, call_to_action, content_type, target_emotion
        
        Make content authentic, engaging, and aligned with the brand."""
        
        company_name = business_data.get("company_overview", {}).get("name", "Company")
        
        prompt = f"""Create a social media content strategy for {company_name}.
        
        Business Intelligence:
        {json.dumps(business_data, indent=2)}
        
        Design Analysis:
        {json.dumps(design_data, indent=2) if design_data else "No design data provided"}
        
        Create 3 Instagram post concepts that align with the brand and resonate with their target audience."""
        
        response = self._make_request(prompt, system_prompt, **kwargs)
        
        # Parse response
        try:
            content_text = response["content"][0]["text"]
            if "```json" in content_text:
                json_start = content_text.find("```json") + 7
                json_end = content_text.find("```", json_start)
                content_text = content_text[json_start:json_end]
            
            content_strategy = json.loads(content_text)
        except (json.JSONDecodeError, KeyError):
            # Fallback structure
            content_strategy = {
                "company_name": company_name,
                "brand_voice": {
                    "tone": "Professional yet approachable",
                    "personality": ["Expert", "Trustworthy", "Innovative"]
                },
                "target_audience": {
                    "primary": "Business professionals",
                    "demographics": "Decision makers, business owners"
                },
                "instagram_posts": [
                    {
                        "post_number": 1,
                        "concept": "Brand Expertise",
                        "headline": f"Expert Solutions from {company_name}",
                        "subtext": "Discover what makes us different",
                        "call_to_action": "Learn More",
                        "content_type": "Educational",
                        "target_emotion": "Trust"
                    },
                    {
                        "post_number": 2,
                        "concept": "Innovation Focus", 
                        "headline": "Innovation Meets Excellence",
                        "subtext": f"See how {company_name} leads the way",
                        "call_to_action": "Get Started",
                        "content_type": "Brand Story",
                        "target_emotion": "Inspiration"
                    },
                    {
                        "post_number": 3,
                        "concept": "Results & Impact",
                        "headline": "Results That Matter",
                        "subtext": f"Join successful businesses using {company_name}",
                        "call_to_action": "Contact Us",
                        "content_type": "Social Proof", 
                        "target_emotion": "Confidence"
                    }
                ],
                "raw_response": response["content"][0]["text"]
            }
        
        content_strategy.update({
            "model": self.model,
            "provider": self.name
        })

        return content_strategy

    def analyze_image_with_text(self, image_path: str, prompt: str, **kwargs) -> str:
        """Analyze image with text prompt using Claude Vision."""
        try:
            # Read and possibly compress image
            import base64
            import mimetypes
            from PIL import Image
            import io
            import time

            # Check image dimensions and compress if needed (Claude has 8000px max dimension limit)
            file_size = os.path.getsize(image_path)
            print(f"Original image size: {file_size} bytes")

            # Always check dimensions and compress if needed
            with Image.open(image_path) as img:
                width, height = img.size
                print(f"Original dimensions: {width}x{height}")
                max_dim = max(width, height)

                # Claude API limit is 8000px on any dimension
                needs_resize = max_dim > 7500 or file_size > 15_000_000  # Leave some safety margin

                if needs_resize:
                    print("Image needs compression due to size or dimensions...")

                    # Convert to RGB if necessary
                    if img.mode in ("RGBA", "P"):
                        img = img.convert("RGB")

                    # Calculate new dimensions keeping aspect ratio, max 7500px on any side
                    if max_dim > 7500:
                        scale_factor = 7500 / max_dim
                        new_width = int(width * scale_factor)
                        new_height = int(height * scale_factor)
                        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                        print(f"Resized to: {new_width}x{new_height}")

                    # Save compressed version
                    buffer = io.BytesIO()
                    img.save(buffer, format="JPEG", quality=85, optimize=True)
                    image_data = buffer.getvalue()
                    mime_type = "image/jpeg"
                    print(f"Compressed image size: {len(image_data)} bytes")
                else:
                    # Use original image
                    with open(image_path, "rb") as image_file:
                        image_data = image_file.read()

                    # Detect image format
                    mime_type = mimetypes.guess_type(image_path)[0]
                    if not mime_type or not mime_type.startswith('image/'):
                        mime_type = "image/png"

            # Encode to base64
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            print(f"Base64 encoded size: {len(image_base64)} characters")

            # Prepare content with image
            content = [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": mime_type,
                        "data": image_base64
                    }
                },
                {
                    "type": "text",
                    "text": prompt
                }
            ]

            # Make request with image analysis with higher max_tokens for detailed analysis
            kwargs.setdefault("max_tokens", 4000)

            # Add retry logic for API overload issues
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = self._make_request("", "", content=content, **kwargs)
                    break
                except Exception as e:
                    if "529" in str(e) or "overloaded" in str(e).lower():
                        if attempt < max_retries - 1:
                            wait_time = (attempt + 1) * 2  # 2, 4, 6 seconds
                            print(f"Claude API overloaded, retrying in {wait_time} seconds... (attempt {attempt + 1}/{max_retries})")
                            time.sleep(wait_time)
                            continue
                    raise

            # Extract text response
            if response and "content" in response and response["content"]:
                return response["content"][0]["text"]

            raise ValueError("No text found in Claude response")

        except Exception as e:
            print(f"Error analyzing image with Claude: {e}")
            print(f"Error details: {type(e).__name__}: {str(e)}")
            # Also print the response if available for debugging
            if hasattr(e, 'response') and hasattr(e.response, 'text'):
                print(f"API Response: {e.response.text[:500]}")
            return f"Error analyzing image: {str(e)}"