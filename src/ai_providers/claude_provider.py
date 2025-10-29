"""Claude AI provider implementation."""

import requests
import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
from .base_provider import BaseAIProvider, AICapability

class ClaudeProvider(BaseAIProvider):
    """Claude AI provider for text analysis and generation."""
    
    def __init__(self, model: str = "claude-3-5-haiku-20241022"):
        super().__init__("claude", model)
        self.api_key = self._get_api_key()
        self.base_url = "https://api.anthropic.com/v1/messages"
    
    def _get_api_key(self) -> str:
        """Get Claude API key from environment."""
        api_key = os.getenv("CLAUDE_API_KEY")
        if not api_key:
            raise ValueError("CLAUDE_API_KEY environment variable not set")
        return api_key

    def _load_prompt_from_md(self, agent_name: str, prompts_dir: str = ".claude/agents") -> Optional[str]:
        """
        Load AI instructions/prompt from a markdown file.

        Args:
            agent_name: Name of the agent (e.g., 'business_intelligence_analyzer')
            prompts_dir: Directory containing the prompt markdown files

        Returns:
            The prompt content as string, or None if file not found
        """
        try:
            prompt_file = Path(prompts_dir) / f"{agent_name}.md"

            if not prompt_file.exists():
                return None

            with open(prompt_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Remove YAML front matter if present (everything between --- lines)
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    content = parts[2].strip()

            return content

        except Exception:
            return None
    
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
    
    def analyze_website(self, html_content: str, url: str, agent_name: str = "business_intelligence_analyzer", **kwargs) -> Dict[str, Any]:
        """
        Analyze website content with Claude using dynamic prompts from markdown files.

        Args:
            html_content: The HTML content to analyze
            url: The website URL
            agent_name: Name of the agent for loading the corresponding .md prompt file
            **kwargs: Additional arguments

        Returns:
            Analyzed business intelligence data
        """
        # Try to load system prompt from markdown file
        dynamic_prompt = self._load_prompt_from_md(agent_name)

        if dynamic_prompt:
            system_prompt = dynamic_prompt
        else:
            # Fallback disabled - force md file usage
            raise ValueError(f"Failed to load prompt from {agent_name}.md file. Fallback disabled - md file is required.")

        prompt = f"""Analyze the website content for: {url}

Website Content:
{html_content[:20000]}

IMPORTANT: Analyze this ACTUAL website content thoroughly. Extract REAL information from the content provided above. Do not make assumptions or use placeholder data. Return only the JSON analysis object with accurate data extracted from the website content, no other text."""

        # Enhanced retry logic with exponential backoff and jitter
        import time
        import random
        max_retries = 6  # Increased retries for critical business analysis
        base_delay = 5  # Base delay in seconds
        last_exception = None

        for attempt in range(max_retries):
            try:
                # Set higher max_tokens for detailed business analysis
                kwargs.setdefault("max_tokens", 6000)
                response = self._make_request(prompt, system_prompt, **kwargs)
                break  # Success, exit retry loop
            except Exception as e:
                last_exception = e
                error_str = str(e).lower()

                # Check for various API overload/error conditions
                is_retryable = any(error_indicator in error_str for error_indicator in [
                    "529", "overloaded", "server error", "rate limit", "502", "503", "504",
                    "timeout", "connection", "temporary", "unavailable"
                ])

                if is_retryable and attempt < max_retries - 1:
                    # Exponential backoff with jitter
                    exponential_delay = base_delay * (2 ** attempt)
                    jitter = random.uniform(0.5, 1.5)  # Add randomness to avoid thundering herd
                    wait_time = exponential_delay * jitter

                    print(f"Claude API issue during business analysis: {str(e)[:100]}")
                    print(f"Retrying in {wait_time:.1f} seconds... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                    continue
                elif not is_retryable:
                    # For non-retryable errors (like invalid API key), fail fast
                    print(f"Non-retryable error: {str(e)}")
                    raise
                # If we've exhausted retries for a retryable error, we'll raise below

        else:
            # If we exhausted all retries, raise the last exception
            print(f"Exhausted all {max_retries} retry attempts for business intelligence analysis")
            raise last_exception

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

            # Strategy 4: Parse embedded JSON within text using improved regex
            import re
            # More flexible regex pattern that handles nested JSON structures better
            json_pattern = r'\{(?:[^{}]|(?:\{(?:[^{}]|\{[^{}]*\})*\}))*\}'

            try:
                json_matches = re.findall(json_pattern, analysis_text, re.DOTALL)

                for match in json_matches:
                    try:
                        # Try to parse each potential JSON object found
                        potential_json = json.loads(match)
                        if isinstance(potential_json, dict) and len(potential_json) > 3:
                            self._add_metadata(potential_json, url)
                            return potential_json
                    except json.JSONDecodeError:
                        continue
            except re.error as e:
                # If regex fails, skip this strategy
                print(f"Regex pattern error: {e}")
                pass

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

    def create_content_strategy(self, business_data: Dict[str, Any], design_data: Dict[str, Any] = None, facebook_analysis: Dict[str, Any] = None, agent_name: str = "social_content_creator", **kwargs) -> Dict[str, Any]:
        """
        Create social media content strategy with Claude using dynamic prompts from markdown files.

        Args:
            business_data: Business intelligence data
            design_data: Design analysis data
            facebook_analysis: Facebook posts analysis data
            agent_name: Name of the agent for loading the corresponding .md prompt file
            **kwargs: Additional arguments

        Returns:
            Social media content strategy data
        """
        # Try to load system prompt from markdown file
        dynamic_prompt = self._load_prompt_from_md(agent_name)

        if dynamic_prompt:
            system_prompt = dynamic_prompt
        else:
            # Fallback to original hardcoded prompt
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

        Facebook Posts Analysis:
        {json.dumps(facebook_analysis, indent=2) if facebook_analysis else "No Facebook posts analysis available"}

            Create 3 Instagram post concepts that align with the brand and resonate with their target audience.
            If Facebook analysis is available, use the tone, style, hashtags, and content patterns from the Facebook posts to create content that feels authentic to the brand owner's voice.

            LANGUAGE REQUIREMENT: If Facebook analysis shows a detected language (detected_language field), generate ALL captions and content in that same language. For example:
            - If detected_language is "fr", generate French captions
            - If detected_language is "da", generate Danish captions  
            - If detected_language is "en", generate English captions
            - If no language is detected, default to English

            IMPORTANT: Return ONLY the JSON object as specified in the system prompt. Do not include any explanatory text, markdown formatting, or other content outside of the JSON structure."""
        
        response = self._make_request(prompt, system_prompt, **kwargs)
        
        # Parse response
        raw_response_text = response["content"][0]["text"]
        try:
            content_text = raw_response_text
            if "```json" in content_text:
                json_start = content_text.find("```json") + 7
                json_end = content_text.find("```", json_start)
                content_text = content_text[json_start:json_end]

            content_strategy = json.loads(content_text)
            # Add raw response to successful parsing
            content_strategy["raw_response"] = raw_response_text
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
                "raw_response": raw_response_text
            }
        
        content_strategy.update({
            "model": self.model,
            "provider": self.name
        })

        return content_strategy

    def generate_instagram_prompts(self, social_content: Dict[str, Any], url: str = "", agent_name: str = "instagram_prompt_generator", **kwargs) -> Dict[str, Any]:
        """
        Generate Instagram prompts using Claude with dynamic prompts from markdown files.

        Args:
            social_content: Social content strategy data
            url: Website URL
            agent_name: Name of the agent for loading the corresponding .md prompt file

        Returns:
            Instagram prompts data
        """
        # Try to load system prompt from markdown file
        dynamic_prompt = self._load_prompt_from_md(agent_name)

        if dynamic_prompt:
            system_prompt = dynamic_prompt
        else:
            # Fallback disabled - force md file usage
            raise ValueError(f"Failed to load prompt from {agent_name}.md file. Fallback disabled - md file is required.")

        company_name = social_content.get("company_name", "Company")

        # Extract detected language from social content
        detected_language = None
        if "brand_analysis" in social_content and "detected_language" in social_content["brand_analysis"]:
            detected_language = social_content["brand_analysis"]["detected_language"]
        elif "facebook_analysis" in social_content and "detected_language" in social_content["facebook_analysis"]:
            detected_language = social_content["facebook_analysis"]["detected_language"]

        prompt = f"""Generate Instagram image prompts for {company_name}.

        Social Content Data:
        {json.dumps(social_content, indent=2)}

        URL: {url}

        Create 3 detailed Gemini prompts for Instagram image generation that align with the brand and social content strategy.

        LANGUAGE REQUIREMENT: If the social content shows a detected language (detected_language field), generate ALL text overlays and prompts in that same language. For example:
        - If detected_language is "fr", generate French text overlays
        - If detected_language is "da", generate Danish text overlays  
        - If detected_language is "en", generate English text overlays
        - If no language is detected, default to English

        IMPORTANT: Return ONLY the JSON object as specified in the system prompt. Do not include any explanatory text, markdown formatting, or other content outside of the JSON structure."""

        response = self._make_request(prompt, system_prompt, **kwargs)

        # Parse response
        raw_response_text = response["content"][0]["text"]
        try:
            content_text = raw_response_text
            if "```json" in content_text:
                json_start = content_text.find("```json") + 7
                json_end = content_text.find("```", json_start)
                content_text = content_text[json_start:json_end]

            prompts_data = json.loads(content_text)
            # Add raw response to successful parsing
            prompts_data["raw_response"] = raw_response_text
        except (json.JSONDecodeError, KeyError):
            # Fallback structure
            prompts_data = {
                "company_name": company_name,
                "timestamp": datetime.now().strftime("%Y-%m-%d"),
                "total_prompts": 3,
                "prompts": [
                    {
                        "post_number": 1,
                        "concept": "Brand Expertise",
                        "headline": f"Expert Solutions from {company_name}",
                        "gemini_prompt": "Create a professional 1080x1080 Instagram post with brand colors and typography",
                        "target_emotion": "Trust",
                        "content_type": "Educational"
                    },
                    {
                        "post_number": 2,
                        "concept": "Innovation Focus",
                        "headline": "Innovation Meets Excellence",
                        "gemini_prompt": "Create a professional 1080x1080 Instagram post with brand colors and typography",
                        "target_emotion": "Inspiration",
                        "content_type": "Brand Story"
                    },
                    {
                        "post_number": 3,
                        "concept": "Results & Impact",
                        "headline": "Results That Matter",
                        "gemini_prompt": "Create a professional 1080x1080 Instagram post with brand colors and typography",
                        "target_emotion": "Confidence",
                        "content_type": "Social Proof"
                    }
                ],
                "raw_response": raw_response_text
            }

        prompts_data.update({
            "model": self.model,
            "provider": self.name
        })

        return prompts_data

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