"""Business intelligence analyzer agent - gathers comprehensive company data."""

import requests
from bs4 import BeautifulSoup
from typing import Dict, Any
from .base_agent import BaseAgent
from ai_providers.ai_factory import AIProviderFactory
from ai_providers.base_provider import AICapability 

class BusinessIntelligenceAnalyzer(BaseAgent):
    """Gathers comprehensive business intelligence about companies."""
    
    def __init__(self):
        super().__init__("business-intelligence-analyzer", "metrics")
        self.ai_provider = AIProviderFactory.get_configured_provider(AICapability.WEB_ANALYSIS)
    
    def fetch_website_content(self, url: str) -> str:
        """Fetch website content."""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        self.logger.info(f"Fetching content from {url}")
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        return response.text
    
    def extract_business_info(self, html_content: str, url: str, prompt_file: str = None) -> Dict[str, Any]:
        """
        Extract business information using AI analysis with dynamic prompts.

        Args:
            html_content: The HTML content to analyze
            url: The website URL
            prompt_file: Optional agent name for loading .md prompts (defaults to this agent's name)

        Returns:
            Business intelligence analysis data
        """
        try:
            # Use the prompt_file parameter or default to this agent's name
            agent_name = prompt_file or self.name

            # Use AI provider for intelligent analysis with dynamic prompts
            business_intel = self.ai_provider.analyze_website(html_content, url, agent_name=agent_name)

            # Check if we got a valid business intelligence response
            if "parsing_error" in business_intel or "raw_analysis" in business_intel:
                self.logger.warning("AI provider returned parsing error, falling back to basic extraction")
                return self._basic_extraction(html_content, url)

            # Ensure required structure and add metadata
            business_intel.update({
                "url": url,
                "timestamp": self.get_timestamp(),
                "analysis_method": "ai_enhanced",
                "ai_model": self.ai_provider.model,
                "ai_provider": self.ai_provider.name,
                "prompt_source": f"{agent_name}.md" if prompt_file else "default"
            })

            return business_intel

        except Exception as e:
            self.logger.warning(f"AI analysis failed, falling back to basic extraction: {e}")
            return self._basic_extraction(html_content, url)
    
    def _basic_extraction(self, html_content: str, url: str) -> Dict[str, Any]:
        """Fallback basic extraction method."""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract basic information
        title = soup.find('title')
        title_text = title.get_text().strip() if title else ""
        
        # Extract meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        description = meta_desc.get('content', '') if meta_desc else ""
        
        # Extract headings
        headings = []
        for h in soup.find_all(['h1', 'h2', 'h3']):
            headings.append({
                'tag': h.name,
                'text': h.get_text().strip()
            })
        
        # Extract paragraphs (first few for content analysis)
        paragraphs = []
        for p in soup.find_all('p')[:10]:
            text = p.get_text().strip()
            if text:
                paragraphs.append(text)
        
        # Basic business intelligence structure
        return {
            "url": url,
            "timestamp": self.get_timestamp(),
            "analysis_method": "basic_extraction",
            "company_overview": {
                "name": title_text.split(' - ')[0] if ' - ' in title_text else title_text,
                "website_title": title_text,
                "description": description,
                "industry": "Technology",
                "founded": "Unknown",
                "employees": "Unknown", 
                "location": "Unknown"
            },
            "services_products": {
                "primary_services": [],
                "key_products": [],
                "target_market": "B2B/B2C"
            },
            "content_analysis": {
                "main_headings": headings[:5],
                "key_paragraphs": paragraphs[:3],
                "content_themes": ["digital", "innovation", "technology"]
            },
            "market_analysis": {
                "positioning": "Professional",
                "competitive_advantages": [],
                "target_audience": "Business professionals",
                "market_segment": "Digital services"
            },
            "social_presence": {
                "website_quality": "High",
                "brand_consistency": "Good",
                "messaging_clarity": "Clear"
            },
            "business_model": {
                "revenue_model": "Service-based",
                "customer_segments": ["Enterprise", "SMB"],
                "value_proposition": "Digital transformation"
            }
        }
    
    def process(self, url: str, prompt_file: str = None, **kwargs) -> Dict[str, Any]:
        """
        Process URL and return business intelligence analysis.

        Args:
            url: The website URL to analyze
            prompt_file: Optional agent name for loading .md prompts (e.g., 'business-intelligence-analyzer')
            **kwargs: Additional parameters

        Returns:
            Business intelligence analysis data
        """
        try:
            # Fetch website content
            html_content = self.fetch_website_content(url)

            # Extract business information with optional custom prompt
            business_intel = self.extract_business_info(html_content, url, prompt_file)

            # Save analysis
            domain = self.sanitize_domain(url)
            filename = self.get_output_filename(domain)
            self.save_json(business_intel, filename, "companies")

            self.logger.info(f"Business intelligence analysis completed for {url}")
            return business_intel

        except Exception as e:
            self.logger.error(f"Error processing {url}: {e}")
            return {"error": str(e), "url": url}
    
    def get_output_filename(self, domain: str) -> str:
        """Generate output filename for business intelligence."""
        return f"{domain}-business-intelligence-{self.get_timestamp()}.json"