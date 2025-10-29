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

    def process(self, url: str, business_intel: Dict[str, Any] = None, design_analysis: Dict[str, Any] = None, facebook_posts: Dict[str, Any] = None, prompt_file: str = None, **kwargs) -> Dict[str, Any]:
        """
        Process and create social media content.

        Args:
            url: The website URL
            business_intel: Business intelligence data from business_intelligence_analyzer
            design_analysis: Design analysis data from screenshot_analyzer
            facebook_posts: Facebook posts data from facebook_scraper
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

        # Analyze Facebook posts if available
        facebook_analysis = None
        if facebook_posts and facebook_posts.get("status") == "success":
            facebook_analysis = self._analyze_facebook_posts(facebook_posts)
        else:
            # Try to load Facebook posts data if not provided
            facebook_analysis = self._load_facebook_posts_analysis(url)

        # Send business intelligence to AI with instructions
        social_content = self.ai_provider.create_content_strategy(
            business_intel,
            design_analysis,
            facebook_analysis=facebook_analysis,
            agent_name=agent_name
        )

        # Add detected language to social content if available
        if facebook_analysis and "detected_language" in facebook_analysis:
            if "brand_analysis" not in social_content:
                social_content["brand_analysis"] = {}
            social_content["brand_analysis"]["detected_language"] = facebook_analysis["detected_language"]

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

    def _load_facebook_posts_analysis(self, url: str) -> Dict[str, Any]:
        """
        Load Facebook posts data from file if available.
        
        Args:
            url: Website URL to find corresponding Facebook posts
            
        Returns:
            Facebook analysis data or None if not found
        """
        try:
            domain = self.sanitize_domain(url)
            facebook_posts_dir = f"metrics/facebook-posts/{domain}"
            
            # Look for the most recent Facebook posts file
            import os
            import glob
            from pathlib import Path
            
            if os.path.exists(facebook_posts_dir):
                pattern = f"{facebook_posts_dir}/*-facebook-posts-*.json"
                files = glob.glob(pattern)
                if files:
                    # Get the most recent file
                    latest_file = max(files, key=os.path.getctime)
                    self.logger.info(f"Loading Facebook posts from {latest_file}")
                    
                    import json
                    with open(latest_file, 'r', encoding='utf-8') as f:
                        facebook_posts = json.load(f)
                    
                    if facebook_posts.get("status") == "success":
                        return self._analyze_facebook_posts(facebook_posts)
            
            self.logger.info(f"No Facebook posts found for {domain}")
            return None
            
        except Exception as e:
            self.logger.warning(f"Failed to load Facebook posts: {e}")
            return None

    def _detect_language(self, text: str) -> str:
        """
        Simple language detection based on common words and patterns.
        
        Args:
            text: Text to analyze
            
        Returns:
            Detected language code (en, fr, da, etc.)
        """
        text_lower = text.lower()
        
        # French indicators
        french_words = ['le', 'la', 'les', 'de', 'du', 'des', 'et', 'est', 'que', 'pour', 'avec', 'dans', 'sur', 'par', 'son', 'ses', 'une', 'un', 'ce', 'cette', 'ces', 'mon', 'ma', 'mes', 'ton', 'ta', 'tes', 'notre', 'nos', 'votre', 'vos', 'leur', 'leurs']
        french_score = sum(1 for word in french_words if word in text_lower)
        
        # Danish indicators
        danish_words = ['og', 'er', 'at', 'i', 'det', 'som', 'på', 'med', 'til', 'for', 'af', 'har', 'ikke', 'der', 'kan', 'vil', 'skal', 'må', 'bliver', 'kommer', 'går', 'siger', 'ved', 'får', 'gør', 'tager', 'ser', 'hører', 'føler', 'tænker', 'kender', 'forstår', 'mener', 'tror', 'håber', 'ønsker', 'bør', 'behøver', 'tør', 'gider', 'orker', 'magter', 'formår', 'lykkes', 'slynges', 'hænger', 'står', 'sidder', 'ligger', 'kører', 'løber', 'hopper', 'springer', 'danser', 'synger', 'spiller', 'arbejder', 'studerer', 'lærer', 'underviser', 'hjælper', 'støtter', 'opmuntrer', 'inspirerer', 'motiverer', 'opfordrer', 'tilskynder', 'fremmer', 'udvikler', 'forbedrer', 'styrker', 'øger', 'forøger', 'udvider', 'uddyber', 'forklarer', 'beskriver', 'fortæller', 'beretter', 'rapporterer', 'meddeler', 'oplyser', 'informerer', 'onsdag', 'oktober', 'dansk', 'danmark', 'københavn', 'kødbyen', 'flæsketorvet', 'vinter', 'sommer', 'forår', 'efterår', 'mandag', 'tirsdag', 'onsdag', 'torsdag', 'fredag', 'lørdag', 'søndag']
        danish_score = sum(1 for word in danish_words if word in text_lower)
        
        # English indicators (fallback)
        english_words = ['the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during', 'before', 'after', 'above', 'below', 'between', 'among', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'shall', 'this', 'that', 'these', 'those', 'a', 'an', 'some', 'any', 'all', 'both', 'each', 'every', 'either', 'neither', 'one', 'two', 'three', 'first', 'second', 'last', 'next', 'other', 'another', 'such', 'same', 'different', 'various', 'several', 'many', 'much', 'more', 'most', 'less', 'least', 'few', 'little', 'enough', 'too', 'very', 'quite', 'rather', 'pretty', 'so', 'such', 'as', 'than', 'like', 'unlike', 'except', 'besides', 'instead', 'rather', 'whether', 'if', 'unless', 'although', 'though', 'even', 'though', 'while', 'whereas', 'because', 'since', 'as', 'so', 'that', 'in', 'order', 'to', 'so', 'as', 'to', 'so', 'that', 'in', 'case', 'provided', 'that', 'supposing', 'that', 'assuming', 'that', 'given', 'that', 'considering', 'that', 'seeing', 'that', 'now', 'that', 'once', 'when', 'whenever', 'where', 'wherever', 'why', 'how', 'what', 'which', 'who', 'whom', 'whose', 'where', 'when', 'why', 'how', 'what', 'which', 'who', 'whom', 'whose', 'where', 'when', 'why', 'how']
        english_score = sum(1 for word in english_words if word in text_lower)
        
        # Determine language based on scores with better logic
        # Check for specific language indicators first
        if 'onsdag' in text_lower or 'oktober' in text_lower or 'københavn' in text_lower:
            return "da"
        if 'jour' in text_lower or 'avec' in text_lower or 'dans' in text_lower:
            return "fr"
        
        # Then use scoring
        if french_score > danish_score and french_score > english_score:
            return "fr"
        elif danish_score > english_score and danish_score > 0:
            return "da"
        else:
            return "en"

    def _analyze_facebook_posts(self, facebook_posts: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze Facebook posts to extract tone, style, and content patterns.
        
        Args:
            facebook_posts: Facebook posts data from facebook_scraper
            
        Returns:
            Analysis of Facebook posts including tone, style, hashtags, language, etc.
        """
        if not facebook_posts.get("posts"):
            return None
            
        posts = facebook_posts["posts"]
        
        # Extract key information from posts
        analysis = {
            "total_posts": len(posts),
            "content_samples": [],
            "hashtags_used": set(),
            "common_themes": [],
            "tone_indicators": [],
            "engagement_patterns": {
                "avg_likes": 0,
                "avg_comments": 0,
                "avg_shares": 0
            },
            "post_types": [],
            "content_lengths": [],
            "detected_language": None
        }
        
        total_likes = 0
        total_comments = 0
        total_shares = 0
        
        # Language detection from all posts
        all_content = []
        for post in posts:
            content = post.get("content", "")
            if content:
                all_content.append(content)
        
        # Detect language from all content
        if all_content:
            combined_content = " ".join(all_content)
            analysis["detected_language"] = self._detect_language(combined_content)
            self.logger.info(f"Detected language from Facebook posts: {analysis['detected_language']}")
        
        for post in posts:
            # Extract content
            content = post.get("content", "")
            if content:
                analysis["content_samples"].append(content)
                analysis["content_lengths"].append(len(content))
            
            # Extract hashtags (simple regex for #hashtag pattern)
            import re
            hashtags = re.findall(r'#\w+', content)
            analysis["hashtags_used"].update(hashtags)
            
            # Extract engagement metrics
            likes = post.get("likes", 0)
            comments = post.get("num_comments", 0)
            shares = post.get("num_shares", 0)
            
            total_likes += likes
            total_comments += comments
            total_shares += shares
            
            # Extract post type
            post_type = post.get("post_type", "Unknown")
            if post_type not in analysis["post_types"]:
                analysis["post_types"].append(post_type)
        
        # Calculate averages
        if len(posts) > 0:
            analysis["engagement_patterns"]["avg_likes"] = total_likes / len(posts)
            analysis["engagement_patterns"]["avg_comments"] = total_comments / len(posts)
            analysis["engagement_patterns"]["avg_shares"] = total_shares / len(posts)
        
        # Convert set to list for JSON serialization
        analysis["hashtags_used"] = list(analysis["hashtags_used"])
        
        # Add page information
        if posts:
            first_post = posts[0]
            analysis["page_info"] = {
                "page_name": first_post.get("page_name", ""),
                "page_intro": first_post.get("page_intro", ""),
                "page_category": first_post.get("page_category", ""),
                "page_followers": first_post.get("page_followers", 0)
            }
        
        self.logger.info(f"Analyzed {len(posts)} Facebook posts for content strategy")
        return analysis

    def get_output_filename(self, domain: str) -> str:
        """Generate output filename for social content."""
        return f"{domain}-social-content-{self.get_timestamp()}.json"