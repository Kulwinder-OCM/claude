"""Business intelligence analyzer agent - gathers comprehensive company data."""

import requests
from typing import Dict, Any
from bs4 import BeautifulSoup
from .base_agent import BaseAgent
from ai_providers.ai_factory import AIProviderFactory
from ai_providers.base_provider import AICapability

class BusinessIntelligenceAnalyzer(BaseAgent):
    """Gathers comprehensive business intelligence about companies."""

    def __init__(self):
        super().__init__("business_intelligence_analyzer", "metrics")
        self.ai_provider = AIProviderFactory.get_configured_provider(AICapability.WEB_ANALYSIS)

    def fetch_website_content(self, url: str) -> str:
        """Fetch and clean website content."""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive'
        }

        self.logger.info(f"Fetching content from {url}")
        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()

            # Parse and clean HTML to extract meaningful content
            soup = BeautifulSoup(response.text, 'html.parser')

            # Remove script, style, and other non-content tags
            for tag in soup(['script', 'style', 'noscript', 'iframe', 'svg']):
                tag.decompose()

            # Extract text content with some structure preserved
            text_content = soup.get_text(separator='\n', strip=True)

            # Also extract meta tags for additional context
            meta_description = soup.find('meta', attrs={'name': 'description'})
            meta_desc = meta_description.get('content', '') if meta_description else ''

            meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
            meta_keys = meta_keywords.get('content', '') if meta_keywords else ''

            title = soup.find('title')
            title_text = title.get_text().strip() if title else ''

            # Combine structured information
            structured_content = f"""Website Title: {title_text}

Meta Description: {meta_desc}

Meta Keywords: {meta_keys}

Website Content:
{text_content[:15000]}"""  # Send first 15000 chars of clean text

            self.logger.info(f"Extracted {len(text_content)} characters of content from {url}")
            return structured_content

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request failed for {url}: {e}")
            raise

    def process(self, url: str, prompt_file: str = None, **kwargs) -> Dict[str, Any]:
        """
        Process URL and return business intelligence analysis.

        Args:
            url: The website URL to analyze
            prompt_file: Optional agent name for loading .md prompts
            **kwargs: Additional parameters

        Returns:
            Business intelligence analysis data saved to JSON file
        """
        # Fetch website content
        html_content = self.fetch_website_content(url)

        # Load instructions from markdown file
        agent_name = prompt_file or self.name
        instructions = self.load_prompt_from_md(agent_name)

        if not instructions:
            raise ValueError(f"Failed to load instructions from {agent_name}.md")

        # Send to AI with instructions and HTML content
        business_intel = self.ai_provider.analyze_website(html_content, url, agent_name=agent_name)

        # Add metadata
        business_intel.update({
            "url": url,
            "timestamp": self.get_timestamp(),
            "ai_model": self.ai_provider.model,
            "ai_provider": self.ai_provider.name
        })

        # Save to metrics/companies/{domain-name}-business-intelligence-{date}.json
        domain = self.sanitize_domain(url)
        filename = self.get_output_filename(domain)
        self.save_json(business_intel, filename, "companies")

        self.logger.info(f"Business intelligence saved to metrics/companies/{filename}")
        return business_intel

    def get_output_filename(self, domain: str) -> str:
        """Generate output filename for business intelligence."""
        return f"{domain}-business-intelligence-{self.get_timestamp()}.json"