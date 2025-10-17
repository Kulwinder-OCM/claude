"""Business intelligence analyzer agent - gathers comprehensive company data."""

import requests
import re
from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from .base_agent import BaseAgent
from ai_providers.ai_factory import AIProviderFactory
from ai_providers.base_provider import AICapability

class BusinessIntelligenceAnalyzer(BaseAgent):
    """Gathers comprehensive business intelligence about companies."""

    def __init__(self):
        super().__init__("business_intelligence_analyzer", "metrics")
        self.ai_provider = AIProviderFactory.get_configured_provider(AICapability.WEB_ANALYSIS)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive'
        })

    def extract_social_media_links(self, url: str) -> List[Dict[str, Any]]:
        """Extract social media links from a website."""
        social_media_accounts = []
        
        try:
            # Fetch the website content
            soup = self._fetch_and_parse(url)
            if not soup:
                return social_media_accounts
            
            # Define social media platform patterns
            social_patterns = {
                'facebook': [
                    r'facebook\.com/[^/\s]+',
                    r'fb\.com/[^/\s]+',
                    r'facebook\.com/pages/[^/\s]+'
                ],
                'twitter': [
                    r'twitter\.com/[^/\s]+',
                    r'x\.com/[^/\s]+',
                    r't\.co/[^/\s]+'
                ],
                'instagram': [
                    r'instagram\.com/[^/\s]+',
                    r'instagr\.am/[^/\s]+'
                ],
                'linkedin': [
                    r'linkedin\.com/company/[^/\s]+',
                    r'linkedin\.com/in/[^/\s]+',
                    r'linkedin\.com/org/[^/\s]+'
                ],
                'youtube': [
                    r'youtube\.com/channel/[^/\s]+',
                    r'youtube\.com/c/[^/\s]+',
                    r'youtube\.com/user/[^/\s]+',
                    r'youtube\.com/@[^/\s]+',
                    r'youtu\.be/[^/\s]+'
                ],
                'tiktok': [
                    r'tiktok\.com/@[^/\s]+',
                    r'vm\.tiktok\.com/[^/\s]+'
                ],
                'pinterest': [
                    r'pinterest\.com/[^/\s]+',
                    r'pin\.it/[^/\s]+'
                ],
                'snapchat': [
                    r'snapchat\.com/add/[^/\s]+',
                    r'snap\.ly/[^/\s]+'
                ],
                'whatsapp': [
                    r'wa\.me/[^/\s]+',
                    r'whatsapp\.com/send\?phone=[^/\s]+'
                ],
                'telegram': [
                    r't\.me/[^/\s]+',
                    r'telegram\.me/[^/\s]+'
                ],
                'discord': [
                    r'discord\.gg/[^/\s]+',
                    r'discord\.com/invite/[^/\s]+'
                ],
                'reddit': [
                    r'reddit\.com/r/[^/\s]+',
                    r'reddit\.com/u/[^/\s]+'
                ],
                'github': [
                    r'github\.com/[^/\s]+'
                ],
                'behance': [
                    r'behance\.net/[^/\s]+'
                ],
                'dribbble': [
                    r'dribbble\.com/[^/\s]+'
                ],
                'medium': [
                    r'medium\.com/@[^/\s]+',
                    r'medium\.com/[^/\s]+'
                ]
            }
            
            # Find all links on the page
            all_links = soup.find_all('a', href=True)
            
            # Extract social media links
            found_platforms = set()
            
            for link in all_links:
                href = link.get('href', '').lower()
                link_text = link.get_text().strip().lower()
                
                # Check if it's a social media link
                for platform, patterns in social_patterns.items():
                    for pattern in patterns:
                        if re.search(pattern, href, re.IGNORECASE):
                            # Extract the username/handle
                            match = re.search(pattern, href, re.IGNORECASE)
                            if match:
                                username = match.group(0)
                                
                                # Clean up the username
                                if platform == 'facebook' and '/pages/' in username:
                                    username = username.split('/pages/')[-1]
                                elif platform == 'linkedin' and '/company/' in username:
                                    username = username.split('/company/')[-1]
                                elif platform == 'linkedin' and '/in/' in username:
                                    username = username.split('/in/')[-1]
                                elif platform == 'youtube' and '/channel/' in username:
                                    username = username.split('/channel/')[-1]
                                elif platform == 'youtube' and '/c/' in username:
                                    username = username.split('/c/')[-1]
                                elif platform == 'youtube' and '/user/' in username:
                                    username = username.split('/user/')[-1]
                                elif platform == 'youtube' and '/@' in username:
                                    username = username.split('/@')[-1]
                                elif platform == 'tiktok' and '/@' in username:
                                    username = username.split('/@')[-1]
                                elif platform == 'snapchat' and '/add/' in username:
                                    username = username.split('/add/')[-1]
                                elif platform == 'whatsapp' and '/send?phone=' in username:
                                    username = username.split('/send?phone=')[-1]
                                elif platform == 'telegram' and '/me/' in username:
                                    username = username.split('/me/')[-1]
                                elif platform == 'discord' and '/gg/' in username:
                                    username = username.split('/gg/')[-1]
                                elif platform == 'discord' and '/invite/' in username:
                                    username = username.split('/invite/')[-1]
                                elif platform == 'reddit' and '/r/' in username:
                                    username = username.split('/r/')[-1]
                                elif platform == 'reddit' and '/u/' in username:
                                    username = username.split('/u/')[-1]
                                elif platform == 'medium' and '/@' in username:
                                    username = username.split('/@')[-1]
                                
                                # Create social media account entry
                                if platform not in found_platforms:
                                    social_media_accounts.append({
                                        'platform': platform.title(),
                                        'url': href,
                                        'username': username,
                                        'handle': f"@{username}" if not username.startswith('@') else username,
                                        'verified': False,  # Could be enhanced with verification detection
                                        'followers': None,  # Could be enhanced with follower count extraction
                                        'description': f"{platform.title()} profile"
                                    })
                                    found_platforms.add(platform)
                                    break
            
            # Also check for social media icons with data attributes or classes
            social_icons = soup.find_all(['a', 'div', 'span'], class_=lambda x: x and any(
                term in x.lower() for term in ['social', 'facebook', 'twitter', 'instagram', 'linkedin', 'youtube', 'tiktok']
            ))
            
            for icon in social_icons:
                href = icon.get('href', '')
                if href and any(platform in href.lower() for platform in social_patterns.keys()):
                    # This is already covered by the link extraction above
                    continue
            
            # Check meta tags for social media information
            meta_tags = soup.find_all('meta', property=lambda x: x and 'og:' in x)
            for meta in meta_tags:
                property_name = meta.get('property', '')
                content = meta.get('content', '')
                
                if 'og:url' in property_name and any(platform in content.lower() for platform in social_patterns.keys()):
                    # Extract platform from URL
                    for platform in social_patterns.keys():
                        if platform in content.lower():
                            if platform not in found_platforms:
                                social_media_accounts.append({
                                    'platform': platform.title(),
                                    'url': content,
                                    'username': content.split('/')[-1],
                                    'handle': f"@{content.split('/')[-1]}",
                                    'verified': False,
                                    'followers': None,
                                    'description': f"{platform.title()} profile from meta tags"
                                })
                                found_platforms.add(platform)
                            break
            
            self.logger.info(f"Found {len(social_media_accounts)} social media accounts")
            return social_media_accounts
            
        except Exception as e:
            self.logger.error(f"Error extracting social media links: {e}")
            return []

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

    def find_about_pages(self, base_url: str) -> List[str]:
        """
        Find About/About Me pages by checking homepage and navigation.
        
        Args:
            base_url: The base website URL
            
        Returns:
            List of About page URLs found
        """
        about_pages = []
        
        try:
            # First, check the homepage for About sections
            self.logger.info(f"Checking homepage for About sections: {base_url}")
            homepage_soup = self._fetch_and_parse(base_url)
            
            if homepage_soup:
                # Check if this is a JavaScript SPA
                is_spa = self._detect_javascript_spa(homepage_soup, base_url)
                
                if is_spa:
                    self.logger.warning(f"JavaScript SPA detected at {base_url} - limited content extraction possible")
                    # For SPAs, we can only work with the minimal content available
                    # Still try to extract from what's available
                    about_sections = self._find_about_sections_on_page(homepage_soup, base_url)
                    about_pages.extend(about_sections)
                else:
                    # Check for About sections on homepage
                    about_sections = self._find_about_sections_on_page(homepage_soup, base_url)
                    about_pages.extend(about_sections)
                    
                    # Check navigation for About links
                    nav_about_pages = self._find_about_links_in_navigation(homepage_soup, base_url)
                    about_pages.extend(nav_about_pages)
                    
                    # Check for anchor links (single-page websites)
                    anchor_sections = self._find_about_anchor_sections(homepage_soup, base_url)
                    about_pages.extend(anchor_sections)
            
            # Remove duplicates while preserving order
            seen = set()
            unique_about_pages = []
            for page in about_pages:
                if page not in seen:
                    seen.add(page)
                    unique_about_pages.append(page)
            
            self.logger.info(f"Found {len(unique_about_pages)} About pages: {unique_about_pages}")
            return unique_about_pages
            
        except Exception as e:
            self.logger.error(f"Error finding About pages: {e}")
            return []
    
    def _detect_javascript_spa(self, soup: BeautifulSoup, url: str) -> bool:
        """Detect if the website is a JavaScript-heavy Single Page Application."""
        try:
            # Check for common SPA indicators
            page_text = soup.get_text(separator=' ', strip=True)
            
            # Very minimal content (likely SPA)
            if len(page_text) < 200:
                # Check for empty root element (React/Vue/Angular)
                root_elements = soup.find_all(['div', 'main', 'app'], id=lambda x: x and x.lower() in ['root', 'app', 'main'])
                for root in root_elements:
                    if not root.get_text().strip():
                        self.logger.warning(f"Detected JavaScript SPA at {url} - content loaded dynamically")
                        return True
                
                # Check for JavaScript framework indicators
                scripts = soup.find_all('script', src=True)
                for script in scripts:
                    src = script.get('src', '').lower()
                    if any(framework in src for framework in ['react', 'vue', 'angular', 'next', 'nuxt', 'svelte']):
                        self.logger.warning(f"Detected JavaScript framework SPA at {url}")
                        return True
                
                # Check for common SPA patterns
                if any(indicator in page_text.lower() for indicator in ['loading', 'please wait', 'javascript required']):
                    self.logger.warning(f"Detected potential SPA at {url}")
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error detecting SPA: {e}")
            return False

    def _fetch_and_parse(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch and parse a URL, returning BeautifulSoup object."""
        try:
            response = self.session.get(url, timeout=30)
            
            # Check for Cloudflare protection or other blocking
            if response.status_code == 403:
                soup = BeautifulSoup(response.text, 'html.parser')
                page_text = soup.get_text().lower()
                if 'cloudflare' in page_text or 'just a moment' in page_text or 'enable javascript' in page_text:
                    self.logger.warning(f"Cloudflare protection detected at {url} - content blocked")
                    return None
            
            response.raise_for_status()
            return BeautifulSoup(response.text, 'html.parser')
        except Exception as e:
            self.logger.warning(f"Failed to fetch {url}: {e}")
            return None

    def _find_about_sections_on_page(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Find About sections directly on the current page."""
        about_sections = []
        
        # First, check if the homepage itself contains substantial founder information
        page_text = soup.get_text(separator=' ', strip=True)
        founder_keywords = [
            'founder', 'co-founder', 'ceo', 'cto', 'president', 'director',
            'about the founder', 'meet the founder', 'our founder',
            'leadership', 'team', 'about us', 'our story', 'about me',
            'owner', 'creator', 'started', 'began', 'established',
            'my name is', 'i am', 'i founded', 'i started'
        ]
        
        # Check if the page contains founder-related content
        if any(keyword in page_text.lower() for keyword in founder_keywords):
            about_sections.append(base_url)
            self.logger.info(f"Homepage contains founder information: {base_url}")
        
        # Look for About sections by common patterns
        about_patterns = [
            r'about\s+(?:us|me|the\s+founder|the\s+team)',
            r'our\s+story',
            r'meet\s+the\s+founder',
            r'founder\'?s?\s+story',
            r'leadership',
            r'team'
        ]
        
        # Check headings and sections
        for pattern in about_patterns:
            # Look in headings
            headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            for heading in headings:
                if heading.get_text() and re.search(pattern, heading.get_text(), re.IGNORECASE):
                    # Found an About section on this page
                    if base_url not in about_sections:
                        about_sections.append(base_url)
                    break
            
            if about_sections:  # If we found one, no need to check other patterns
                break
        
        return about_sections

    def _find_about_links_in_navigation(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Find About page links in navigation menus and footer."""
        about_pages = []
        
        # Common About page link patterns (multilingual support)
        about_link_patterns = [
            # English
            r'about', r'about-us', r'about-me', r'our-story', r'team', r'leadership', r'founder', r'meet-the-team',
            # Danish - more specific patterns
            r'^om$', r'om-os', r'om-mig', r'vores-historie', r'hold', r'ledelse', r'om-universal', r'om-',
            # French
            r'à-propos', r'à-propos-de-nous', r'à-propos-de-moi', r'notre-histoire', r'équipe', r'direction',
            # German
            r'über', r'über-uns', r'über-mich', r'unser-geschichte', r'team', r'führung',
            # Spanish
            r'acerca-de', r'sobre-nosotros', r'sobre-mí', r'nuestra-historia', r'equipo', r'liderazgo',
            # Italian
            r'chi-siamo', r'su-di-noi', r'su-di-me', r'la-nostra-storia', r'squadra', r'leadership',
            # Portuguese
            r'sobre', r'sobre-nós', r'sobre-mim', r'nossa-história', r'equipe', r'liderança',
            # Dutch
            r'over', r'over-ons', r'over-mij', r'ons-verhaal', r'team', r'leiderschap',
            # Swedish - more specific patterns
            r'^om$', r'om-oss', r'om-mig', r'vår-historia', r'team', r'ledning', r'om-',
            # Norwegian - more specific patterns
            r'^om$', r'om-oss', r'om-meg', r'vår-historie', r'team', r'ledelse', r'om-',
            # Finnish
            r'tietoa', r'tietoa-meistä', r'tietoa-minusta', r'tarinamme', r'tiimi', r'johto'
        ]
        
        # Look in navigation elements (header, nav, main menu, mega menus)
        nav_selectors = [
            'nav', 'header', '.nav', '.navigation', '.menu', '.header',
            '[role="navigation"]', '.navbar', '.main-nav', '.top-nav',
            # Mega menu and dropdown selectors
            '.mega-menu', '.dropdown', '.submenu', '.sub-menu', '.mega-nav',
            '.dropdown-menu', '.nav-dropdown', '.menu-dropdown', '.mega-dropdown',
            '.nav-item', '.menu-item', '.nav-link', '.menu-link'
        ]
        
        # Look in footer elements
        footer_selectors = [
            'footer', '.footer', '#footer', '.site-footer', '.page-footer'
        ]
        
        # Search in navigation elements
        for selector in nav_selectors:
            nav_elements = soup.select(selector)
            for nav in nav_elements:
                links = nav.find_all('a', href=True)
                for link in links:
                    href = link.get('href', '')
                    link_text = link.get_text().strip().lower()
                    
                    # Check if link text matches About patterns
                    for pattern in about_link_patterns:
                        if re.search(pattern, link_text, re.IGNORECASE):
                            full_url = urljoin(base_url, href)
                            if self._is_same_domain(full_url, base_url):
                                about_pages.append(full_url)
                                break
                    
                    # Also check href for About patterns
                    for pattern in about_link_patterns:
                        if re.search(pattern, href, re.IGNORECASE):
                            full_url = urljoin(base_url, href)
                            if self._is_same_domain(full_url, base_url):
                                about_pages.append(full_url)
                                break
        
        # Search in footer elements
        for selector in footer_selectors:
            footer_elements = soup.select(selector)
            for footer in footer_elements:
                links = footer.find_all('a', href=True)
                for link in links:
                    href = link.get('href', '')
                    link_text = link.get_text().strip().lower()
                    
                    # Check if link text matches About patterns
                    for pattern in about_link_patterns:
                        if re.search(pattern, link_text, re.IGNORECASE):
                            full_url = urljoin(base_url, href)
                            if self._is_same_domain(full_url, base_url):
                                about_pages.append(full_url)
                                break
                    
                    # Also check href for About patterns
                    for pattern in about_link_patterns:
                        if re.search(pattern, href, re.IGNORECASE):
                            full_url = urljoin(base_url, href)
                            if self._is_same_domain(full_url, base_url):
                                about_pages.append(full_url)
                                break
        
        return about_pages

    def _find_about_anchor_sections(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Find About sections using anchor links (for single-page websites)."""
        about_sections = []
        
        try:
            # Look for anchor links in navigation
            anchor_links = soup.find_all('a', href=True)
            
            for link in anchor_links:
                href = link.get('href', '')
                link_text = link.get_text().strip().lower()
                
                # Check if it's an anchor link with About-related text
                if href.startswith('#') and any(term in link_text for term in [
                    'about', 'founder', 'team', 'leadership', 'who we are', 'our story',
                    # Multilingual terms
                    'om', 'grundlægger', 'hold', 'ledelse',  # Danish
                    'à propos', 'fondateur', 'équipe', 'direction',  # French
                    'über', 'gründer', 'team', 'führung',  # German
                    'acerca de', 'fundador', 'equipo', 'liderazgo',  # Spanish
                    'chi siamo', 'fondatore', 'squadra', 'leadership',  # Italian
                    'sobre', 'fundador', 'equipe', 'liderança',  # Portuguese
                    'over', 'oprichter', 'team', 'leiderschap',  # Dutch
                    'om', 'grundare', 'team', 'ledning',  # Swedish
                    'om', 'grunnlegger', 'team', 'ledelse',  # Norwegian
                    'tietoa', 'perustaja', 'tiimi', 'johto'  # Finnish
                ]):
                    # Extract the anchor ID
                    anchor_id = href[1:]  # Remove the # symbol
                    
                    # Look for the corresponding section on the page
                    target_element = soup.find(id=anchor_id)
                    if target_element:
                        # Check if this section contains substantial content
                        section_text = target_element.get_text(separator=' ', strip=True)
                        if len(section_text) > 100:  # Only consider sections with substantial content
                            # Create a URL for this anchor section
                            anchor_url = f"{base_url}{href}"
                            about_sections.append(anchor_url)
                            self.logger.info(f"Found anchor About section: {anchor_url}")
            
            # Also look for sections with About-related IDs directly
            about_id_patterns = [
                'about', 'about-us', 'about-me', 'founder', 'founders', 'team', 'leadership',
                'who-we-are', 'our-story', 'meet-the-team', 'meet-the-founder',
                # Multilingual patterns
                'om', 'om-os', 'om-mig', 'grundlægger', 'hold', 'ledelse',
                'a-propos', 'fondateur', 'equipe', 'direction',
                'uber', 'gründer', 'team', 'führung',
                'acerca-de', 'fundador', 'equipo', 'liderazgo',
                'chi-siamo', 'fondatore', 'squadra', 'leadership',
                'sobre', 'fundador', 'equipe', 'lideranca',
                'over', 'oprichter', 'team', 'leiderschap',
                'om', 'grundare', 'team', 'ledning',
                'om', 'grunnlegger', 'team', 'ledelse',
                'tietoa', 'perustaja', 'tiimi', 'johto'
            ]
            
            for pattern in about_id_patterns:
                elements = soup.find_all(id=lambda x: x and pattern in x.lower())
                for element in elements:
                    section_text = element.get_text(separator=' ', strip=True)
                    if len(section_text) > 100:  # Only consider sections with substantial content
                        anchor_url = f"{base_url}#{element.get('id')}"
                        if anchor_url not in about_sections:
                            about_sections.append(anchor_url)
                            self.logger.info(f"Found About section by ID: {anchor_url}")
            
        except Exception as e:
            self.logger.error(f"Error finding anchor About sections: {e}")
        
        return about_sections

    def _is_same_domain(self, url1: str, url2: str) -> bool:
        """Check if two URLs are from the same domain."""
        try:
            domain1 = urlparse(url1).netloc.lower()
            domain2 = urlparse(url2).netloc.lower()
            return domain1 == domain2
        except:
            return False

    def extract_founder_details(self, about_pages: List[str]) -> List[Dict[str, Any]]:
        """
        Extract detailed founder information from About pages.
        
        Args:
            about_pages: List of About page URLs
            
        Returns:
            List of founder details dictionaries
        """
        founders = []
        
        for about_url in about_pages:
            try:
                self.logger.info(f"Extracting founder details from: {about_url}")
                soup = self._fetch_and_parse(about_url)
                
                if not soup:
                    continue
                
                # Extract founder information from this page
                page_founders = self._extract_founders_from_page(soup, about_url)
                founders.extend(page_founders)
                
            except Exception as e:
                self.logger.error(f"Error extracting founders from {about_url}: {e}")
                continue
        
        # Remove duplicates based on name
        unique_founders = []
        seen_names = set()
        
        for founder in founders:
            name = founder.get('name', '').lower().strip()
            if name and name not in seen_names:
                seen_names.add(name)
                unique_founders.append(founder)
        
        self.logger.info(f"Extracted {len(unique_founders)} unique founders")
        return unique_founders

    def _extract_founders_from_page(self, soup: BeautifulSoup, page_url: str) -> List[Dict[str, Any]]:
        """Extract founder information from a single page or page section."""
        founders = []
        
        try:
            # Check if this is an anchor URL (single-page website section)
            if '#' in page_url:
                anchor_id = page_url.split('#')[-1]
                # Find the specific section by ID
                target_section = soup.find(id=anchor_id)
                if target_section:
                    self.logger.info(f"Extracting from anchor section: {anchor_id}")
                    # Use only the target section for extraction
                    soup = target_section
            
            # Remove script and style tags for cleaner text extraction
            for tag in soup(['script', 'style', 'noscript']):
                tag.decompose()
            
        except Exception as e:
            self.logger.error(f"Error processing anchor section: {e}")
        
        # Look for founder information in various ways
        founder_sections = self._find_founder_sections(soup)
        
        # Always try to extract from the entire page content first, then specific sections
        self.logger.info(f"Analyzing entire page content for {page_url}")
        entire_page_section = soup
        founder_info = self._parse_founder_section(entire_page_section, page_url, soup)
        if founder_info:
            founders.append(founder_info)
        
        # Also try specific founder sections if found
        if founder_sections:
            self.logger.info(f"Found {len(founder_sections)} specific founder sections, analyzing them")
            for section in founder_sections:
                founder_info = self._parse_founder_section(section, page_url, soup)
                if founder_info:
                    founders.append(founder_info)
        
        # If still no founders found, try to extract from domain/company name as fallback
        if not founders:
            self.logger.info(f"No founders found through content analysis, trying domain-based extraction for {page_url}")
            domain_founder = self._extract_founder_from_domain(page_url, soup)
            if domain_founder:
                founders.append(domain_founder)
        
        return founders

    def _find_founder_sections(self, soup: BeautifulSoup) -> List[BeautifulSoup]:
        """Find sections that likely contain founder information."""
        founder_sections = []
        
        # Look for sections with founder-related keywords (multilingual support)
        founder_keywords = [
            # English
            'founder', 'co-founder', 'ceo', 'cto', 'president', 'director',
            'about the founder', 'meet the founder', 'our founder',
            'leadership', 'team', 'about us', 'our story', 'about me',
            'owner', 'creator', 'started', 'began', 'established',
            'my story', 'personal', 'background', 'journey',
            # Danish
            'grundlægger', 'medgrundlægger', 'direktør', 'ledelse', 'hold', 'om os', 'vores historie', 'om mig',
            'ejer', 'skaber', 'startede', 'begyndte', 'etablerede', 'min historie', 'personlig', 'baggrund',
            # French
            'fondateur', 'co-fondateur', 'directeur', 'direction', 'équipe', 'à propos de nous', 'notre histoire', 'à propos de moi',
            'propriétaire', 'créateur', 'commencé', 'établi', 'mon histoire', 'personnel', 'parcours',
            # German
            'gründer', 'mitgründer', 'direktor', 'führung', 'team', 'über uns', 'unsere geschichte', 'über mich',
            'besitzer', 'schöpfer', 'begonnen', 'etabliert', 'meine geschichte', 'persönlich', 'hintergrund',
            # Spanish
            'fundador', 'co-fundador', 'director', 'liderazgo', 'equipo', 'sobre nosotros', 'nuestra historia', 'sobre mí',
            'propietario', 'creador', 'comenzó', 'establecido', 'mi historia', 'personal', 'antecedentes',
            # Italian
            'fondatore', 'co-fondatore', 'direttore', 'leadership', 'squadra', 'chi siamo', 'la nostra storia', 'su di me',
            'proprietario', 'creatore', 'iniziato', 'stabilito', 'la mia storia', 'personale', 'sfondo',
            # Portuguese
            'fundador', 'co-fundador', 'diretor', 'liderança', 'equipe', 'sobre nós', 'nossa história', 'sobre mim',
            'proprietário', 'criador', 'começou', 'estabelecido', 'minha história', 'pessoal', 'antecedentes',
            # Dutch
            'oprichter', 'mede-oprichter', 'directeur', 'leiderschap', 'team', 'over ons', 'ons verhaal', 'over mij',
            'eigenaar', 'maker', 'begonnen', 'gevestigd', 'mijn verhaal', 'persoonlijk', 'achtergrond',
            # Swedish
            'grundare', 'medgrundare', 'direktör', 'ledning', 'team', 'om oss', 'vår historia', 'om mig',
            'ägare', 'skapare', 'startade', 'etablerade', 'min historia', 'personlig', 'bakgrund',
            # Norwegian
            'grunnlegger', 'medgrunnlegger', 'direktør', 'ledelse', 'team', 'om oss', 'vår historie', 'om meg',
            'eier', 'skaper', 'startet', 'etablert', 'min historie', 'personlig', 'bakgrunn',
            # Finnish
            'perustaja', 'perustajajäsen', 'johtaja', 'johto', 'tiimi', 'tietoa meistä', 'tarina', 'tietoa minusta',
            'omistaja', 'luoja', 'aloitettu', 'perustettu', 'tarina', 'henkilökohtainen', 'tausta'
        ]
        
        # Check headings and their following content
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        
        for heading in headings:
            heading_text = heading.get_text().strip().lower()
            
            for keyword in founder_keywords:
                if keyword in heading_text:
                    # Found a potential founder section
                    section = self._extract_section_content(heading)
                    if section:
                        founder_sections.append(section)
                    break
        
        # Also look for common founder section patterns
        founder_selectors = [
            '.founder', '.founder-info', '.about-founder', '.team-member',
            '.leadership', '.executive', '.ceo', '.cto', '.president',
            '.about-me', '.personal', '.story', '.bio', '.profile',
            '[class*="about"]', '[class*="founder"]', '[class*="owner"]',
            '[class*="creator"]', '[class*="personal"]'
        ]
        
        for selector in founder_selectors:
            sections = soup.select(selector)
            founder_sections.extend(sections)
        
        # Look for main content areas that might contain founder info
        main_content_selectors = [
            'main', '.main-content', '.content', '.page-content',
            '.about-content', '.story', '.bio'
        ]
        
        for selector in main_content_selectors:
            sections = soup.select(selector)
            for section in sections:
                # Check if this section contains founder-related keywords
                section_text = section.get_text().lower()
                if any(keyword in section_text for keyword in ['founder', 'owner', 'creator', 'started', 'began', 'my story', 'about me']):
                    founder_sections.append(section)
        
        return founder_sections

    def _extract_section_content(self, heading: BeautifulSoup) -> Optional[BeautifulSoup]:
        """Extract content section following a heading."""
        # Get the parent container
        parent = heading.parent
        if not parent:
            return None
        
        # Look for content in the same parent or following siblings
        content_elements = []
        
        # Add the heading itself
        content_elements.append(heading)
        
        # Add following siblings until we hit another heading of same or higher level
        heading_level = int(heading.name[1]) if heading.name.startswith('h') else 6
        
        for sibling in parent.find_next_siblings():
            if sibling.name and sibling.name.startswith('h'):
                sibling_level = int(sibling.name[1])
                if sibling_level <= heading_level:
                    break
            content_elements.append(sibling)
        
        # Create a new soup object with just this section
        if content_elements:
            section_html = ''.join(str(elem) for elem in content_elements)
            return BeautifulSoup(section_html, 'html.parser')
        
        return None

    def _parse_founder_section(self, section: BeautifulSoup, page_url: str, soup: BeautifulSoup = None) -> Optional[Dict[str, Any]]:
        """Parse a founder section to extract structured information."""
        try:
            # Extract text content
            text_content = section.get_text(separator=' ', strip=True)
            
            self.logger.info(f"Extracted text content length: {len(text_content)} characters")
            self.logger.debug(f"First 500 characters of content: {text_content[:500]}")
            
            if len(text_content) < 50:  # Too short to be meaningful
                self.logger.warning(f"Content too short ({len(text_content)} chars), skipping")
                return None
            
            # Load dedicated founder extractor instructions
            founder_instructions = self.load_prompt_from_md("founder_extractor")
            
            if not founder_instructions:
                self.logger.error("Could not load founder_extractor.md instructions")
                return None
            
            # Use ONLY the founder extractor instructions - no additional prompts
            founder_prompt = f"""{founder_instructions}

TEXT TO ANALYZE FROM ABOUT PAGE:
{text_content[:3000]}

IMPORTANT: Follow the instructions in the founder_extractor.md file exactly. Extract founder information and return the JSON structure as specified in those instructions.
"""
            
            # Extract the most relevant content for founder analysis
            # Look for main content areas and extract the most relevant parts
            main_content = self._extract_main_content_for_founder_analysis(soup, text_content)
            
            # Send to AI for structured extraction
            ai_response = self.ai_provider.analyze_text(
                main_content, 
                founder_prompt
            )
            
            # Parse AI response
            self.logger.info(f"AI response type: {type(ai_response)}")
            self.logger.info(f"AI response content: {str(ai_response)[:1000]}")
            
            if isinstance(ai_response, dict):
                # AI returned a dictionary directly
                founder_data = ai_response
                
                # Check if the response has the expected structure (direct founder object)
                if founder_data and founder_data.get('name'):
                    self.logger.info(f"Successfully extracted founder: {founder_data.get('name')}")
                    return founder_data
                # Check if the response has founders array (full JSON structure)
                elif founder_data and founder_data.get('founders') and len(founder_data.get('founders', [])) > 0:
                    founder_info = founder_data['founders'][0]  # Get first founder
                    self.logger.info(f"Successfully extracted founder from founders array: {founder_info.get('name')}")
                    return founder_info
                # Check if the response has an 'analysis' field with JSON content (fallback)
                elif founder_data and founder_data.get('analysis'):
                    analysis_text = founder_data.get('analysis')
                    # Try to extract JSON from the analysis text
                    json_start = analysis_text.find('{')
                    json_end = analysis_text.rfind('}') + 1
                    if json_start != -1 and json_end > json_start:
                        json_str = analysis_text[json_start:json_end]
                        import json
                        try:
                            extracted_data = json.loads(json_str)
                            # Check if this contains founder information
                            if extracted_data and extracted_data.get('founders') and len(extracted_data.get('founders', [])) > 0:
                                founder_info = extracted_data['founders'][0]  # Get first founder
                                self.logger.info(f"Successfully extracted founder from analysis: {founder_info.get('name')}")
                                return founder_info
                        except json.JSONDecodeError:
                            pass
                
                self.logger.warning(f"No founder name found in AI response for {page_url}")
                self.logger.info(f"AI response keys: {list(founder_data.keys()) if founder_data else 'None'}")
            elif isinstance(ai_response, str):
                # Try to extract JSON from response
                json_start = ai_response.find('{')
                json_end = ai_response.rfind('}') + 1
                if json_start != -1 and json_end > json_start:
                    json_str = ai_response[json_start:json_end]
                    import json
                    try:
                        founder_data = json.loads(json_str)
                        if founder_data and founder_data.get('name'):
                            self.logger.info(f"Successfully extracted founder: {founder_data.get('name')}")
                            return founder_data
                        else:
                            self.logger.warning(f"No founder name found in AI response for {page_url}")
                    except json.JSONDecodeError as e:
                        self.logger.error(f"JSON decode error in founder extraction: {e}")
                        self.logger.debug(f"AI response: {ai_response}")
            else:
                self.logger.warning(f"Unexpected AI response type: {type(ai_response)}")
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error parsing founder section: {e}")
            return None

    def _extract_founder_from_domain(self, url: str, soup: BeautifulSoup) -> Optional[Dict[str, Any]]:
        """
        Extract founder information from domain name and available content as fallback.
        This method tries to infer founder information when direct content extraction fails.
        """
        try:
            # Extract domain information
            domain = urlparse(url).netloc.lower()
            domain_parts = domain.replace('www.', '').replace('shop.', '').replace('.se', '').replace('.com', '').split('.')
            
            # Get page title and any available text
            title = soup.find('title')
            title_text = title.get_text().strip() if title else ''
            
            # Get any available text content
            page_text = soup.get_text(separator=' ', strip=True)[:1000]
            
            # Load founder extractor instructions for domain-based extraction
            founder_instructions = self.load_prompt_from_md("founder_extractor")
            
            if not founder_instructions:
                self.logger.error("Could not load founder_extractor.md instructions for domain extraction")
                return None
            
            # Enhanced prompt for SPA/domain-based extraction
            domain_prompt = f"""{founder_instructions}

WEBSITE INFORMATION TO ANALYZE:
Website URL: {url}
Domain: {domain}
Domain parts: {domain_parts}
Page title: {title_text}
Available text: {page_text}

SPA DETECTION: This appears to be a JavaScript Single Page Application (SPA) with minimal static content. The actual content is loaded dynamically via JavaScript.

DOMAIN ANALYSIS: Analyze the domain name and available information to infer potential founder details:
- Domain: {domain}
- Domain parts: {domain_parts}
- Business type: {title_text}

IMPORTANT: Since this is a SPA with minimal content, you may need to:
1. Infer founder information from the domain name and business description
2. Make educated guesses based on the business type and domain
3. If no specific founder information is available, return null or minimal information
4. Focus on what can be reasonably inferred from the available data

Follow the instructions in the founder_extractor.md file exactly and return the JSON structure as specified.
"""
            
            # Send to AI for analysis
            ai_response = self.ai_provider.analyze_text(
                f"Domain: {domain}, Title: {title_text}, Text: {page_text[:1000]}", 
                domain_prompt
            )
            
            # Parse AI response
            if isinstance(ai_response, dict):
                founder_data = ai_response
                if founder_data and founder_data.get('name'):
                    self.logger.info(f"Successfully extracted founder from domain: {founder_data.get('name')}")
                    return founder_data
            elif isinstance(ai_response, str):
                json_start = ai_response.find('{')
                json_end = ai_response.rfind('}') + 1
                if json_start != -1 and json_end > json_start:
                    json_str = ai_response[json_start:json_end]
                    import json
                    try:
                        founder_data = json.loads(json_str)
                        if founder_data and founder_data.get('name'):
                            self.logger.info(f"Successfully extracted founder from domain: {founder_data.get('name')}")
                            return founder_data
                    except json.JSONDecodeError:
                        pass
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error in domain-based founder extraction: {e}")
            return None

    def _extract_main_content_for_founder_analysis(self, soup: BeautifulSoup, full_text: str) -> str:
        """
        Extract the most relevant content for founder analysis by focusing on main content areas
        and filtering out navigation, currency, and other non-relevant content.
        """
        try:
            # Look for main content areas
            main_content_selectors = [
                'main', '.main-content', '.content', '.page-content',
                '.about-content', '.story', '.bio', '.about-me',
                '[class*="about"]', '[class*="story"]', '[class*="bio"]'
            ]
            
            main_content = ""
            
            # Try to find main content areas
            for selector in main_content_selectors:
                elements = soup.select(selector)
                for element in elements:
                    element_text = element.get_text(separator=' ', strip=True)
                    if len(element_text) > 100:  # Only consider substantial content
                        main_content += element_text + "\n\n"
            
            # If no main content found, try to extract relevant parts from full text
            if not main_content or len(main_content) < 200:
                # Look for patterns that might indicate founder information
                lines = full_text.split('\n')
                relevant_lines = []
                
                for line in lines:
                    line = line.strip()
                    if len(line) > 20:  # Skip very short lines
                        # Look for lines that might contain founder information (multilingual)
                        if any(keyword in line.lower() for keyword in [
                            # English
                            'name is', 'my name', 'founder', 'owner', 'creator',
                            'started', 'began', 'established', 'company', 'business',
                            'about me', 'personal', 'background', 'story', 'journey',
                            # Danish
                            'jeg hedder', 'mit navn', 'grundlægger', 'ejer', 'skaber',
                            'startede', 'begyndte', 'etablerede', 'virksomhed', 'om mig',
                            # French
                            'je m\'appelle', 'mon nom', 'fondateur', 'propriétaire', 'créateur',
                            'commencé', 'établi', 'entreprise', 'à propos de moi',
                            # German
                            'ich heiße', 'mein name', 'gründer', 'besitzer', 'schöpfer',
                            'begonnen', 'etabliert', 'unternehmen', 'über mich',
                            # Spanish
                            'me llamo', 'mi nombre', 'fundador', 'propietario', 'creador',
                            'comenzó', 'establecido', 'empresa', 'sobre mí',
                            # Italian
                            'mi chiamo', 'il mio nome', 'fondatore', 'proprietario', 'creatore',
                            'iniziato', 'stabilito', 'azienda', 'su di me',
                            # Portuguese
                            'meu nome', 'fundador', 'proprietário', 'criador',
                            'começou', 'estabelecido', 'empresa', 'sobre mim',
                            # Dutch
                            'mijn naam', 'oprichter', 'eigenaar', 'maker',
                            'begonnen', 'gevestigd', 'bedrijf', 'over mij',
                            # Swedish
                            'jag heter', 'mitt namn', 'grundare', 'ägare', 'skapare',
                            'startade', 'etablerade', 'företag', 'om mig',
                            # Norwegian
                            'jeg heter', 'mitt navn', 'grunnlegger', 'eier', 'skaper',
                            'startet', 'etablert', 'bedrift', 'om meg',
                            # Finnish
                            'nimeni on', 'perustaja', 'omistaja', 'luoja',
                            'aloitettu', 'perustettu', 'yritys', 'tietoa minusta'
                        ]):
                            relevant_lines.append(line)
                
                main_content = '\n'.join(relevant_lines)
            
            # If still no good content, use a filtered version of the full text
            if not main_content or len(main_content) < 100:
                # Remove common navigation/currency patterns and take a middle section
                lines = full_text.split('\n')
                filtered_lines = []
                
                for line in lines:
                    line = line.strip()
                    # Skip lines that are clearly navigation/currency
                    if not any(skip_word in line.lower() for skip_word in [
                        'currency', 'shipping', 'payment', 'cart', 'checkout',
                        'menu', 'navigation', 'skip to', 'free shipping',
                        'choose 3', 'use code', 'afghanistan', 'albania'
                    ]):
                        if len(line) > 10:  # Only keep substantial lines
                            filtered_lines.append(line)
                
                # Take the middle section which is more likely to contain main content
                if filtered_lines:
                    start_idx = len(filtered_lines) // 4
                    end_idx = start_idx + (len(filtered_lines) // 2)
                    main_content = '\n'.join(filtered_lines[start_idx:end_idx])
            
            # Limit to reasonable size for AI processing
            if len(main_content) > 4000:
                main_content = main_content[:4000]
            
            self.logger.info(f"Extracted main content for founder analysis: {len(main_content)} characters")
            self.logger.debug(f"Main content preview: {main_content[:500]}")
            
            return main_content
            
        except Exception as e:
            self.logger.error(f"Error extracting main content for founder analysis: {e}")
            # Fallback to first 3000 characters
            return full_text[:3000]

    def process(self, url: str, prompt_file: str = None, **kwargs) -> Dict[str, Any]:
        """
        Process URL and return business intelligence analysis with enhanced founder details.

        Args:
            url: The website URL to analyze
            prompt_file: Optional agent name for loading .md prompts
            **kwargs: Additional parameters

        Returns:
            Business intelligence analysis data saved to JSON file
        """
        # Step 1: Fetch website content (existing functionality)
        html_content = self.fetch_website_content(url)

        # Step 2: Load instructions from markdown file (existing functionality)
        agent_name = prompt_file or self.name
        instructions = self.load_prompt_from_md(agent_name)

        if not instructions:
            raise ValueError(f"Failed to load instructions from {agent_name}.md")

        # Step 3: Send to AI with instructions and HTML content (existing functionality)
        business_intel = self.ai_provider.analyze_website(html_content, url, agent_name=agent_name)

        # Step 4: Enhanced founder details extraction (NEW FUNCTIONALITY)
        self.logger.info("Starting enhanced founder details extraction...")
        
        try:
            # Find About pages
            about_pages = self.find_about_pages(url)
            
            if about_pages:
                # Extract detailed founder information
                enhanced_founders = self.extract_founder_details(about_pages)
                
                # Merge with existing founder data if any
                existing_founders = business_intel.get('founders', [])
                
                # Combine and deduplicate founders
                all_founders = self._merge_founder_data(existing_founders, enhanced_founders)
                business_intel['founders'] = all_founders
                
                # Note: Founder details are included in the main business intelligence JSON file
                
                self.logger.info(f"Enhanced founder extraction completed. Found {len(all_founders)} founders total.")
            else:
                self.logger.info("No About pages found for enhanced founder extraction.")
                
        except Exception as e:
            self.logger.error(f"Error in enhanced founder extraction: {e}")
            # Continue with existing data if enhancement fails

        # Step 5: Social media links extraction (NEW FUNCTIONALITY)
        self.logger.info("Starting social media links extraction...")
        
        try:
            # Extract social media links
            social_media_accounts = self.extract_social_media_links(url)
            
            # Replace the existing socialMediaAccounts with detailed extraction
            business_intel['socialMediaAccounts'] = social_media_accounts
            business_intel['enhanced_social_media_extraction'] = True
            
            self.logger.info(f"Social media extraction completed. Found {len(social_media_accounts)} social media accounts.")
            
        except Exception as e:
            self.logger.error(f"Error in social media extraction: {e}")
            business_intel['enhanced_social_media_extraction'] = False

        # Step 6: Add metadata (existing functionality)
        business_intel.update({
            "url": url,
            "timestamp": self.get_timestamp(),
            "ai_model": self.ai_provider.model,
            "ai_provider": self.ai_provider.name,
            "enhanced_founder_extraction": True  # Flag to indicate enhanced extraction was used
        })

        # Step 6: Save to metrics/companies/{domain-name}-business-intelligence-{date}.json (existing functionality)
        domain = self.sanitize_domain(url)
        filename = self.get_output_filename(domain)
        self.save_json(business_intel, filename, "companies")

        self.logger.info(f"Enhanced business intelligence saved to metrics/companies/{filename}")
        return business_intel

    def _merge_founder_data(self, existing_founders: List[Dict[str, Any]], enhanced_founders: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Merge existing founder data with enhanced founder data, avoiding duplicates.
        
        Args:
            existing_founders: Founders from original business intelligence analysis
            enhanced_founders: Founders from enhanced extraction
            
        Returns:
            Merged list of unique founders
        """
        merged_founders = []
        seen_names = set()
        
        # First, add enhanced founders (they have more detailed information)
        for founder in enhanced_founders:
            name = founder.get('name', '').lower().strip()
            if name and name not in seen_names:
                seen_names.add(name)
                merged_founders.append(founder)
        
        # Then add existing founders that weren't already included
        for founder in existing_founders:
            name = founder.get('name', '').lower().strip()
            if name and name not in seen_names:
                seen_names.add(name)
                merged_founders.append(founder)
        
        return merged_founders


    def extract_founders_only(self, url: str) -> Dict[str, Any]:
        """
        Extract only founder details and save to separate JSON file.
        This method focuses solely on founder extraction without full business intelligence.
        
        Args:
            url: The website URL to analyze
            
        Returns:
            Founder details data saved to separate JSON file
        """
        self.logger.info(f"Starting founder-only extraction for {url}")
        
        try:
            # Find About pages
            about_pages = self.find_about_pages(url)
            
            if not about_pages:
                self.logger.warning("No About pages found for founder extraction")
                # Check for specific blocking issues
                homepage_soup = self._fetch_and_parse(url)
                if homepage_soup is None:
                    # Check if it's a Cloudflare protection issue
                    try:
                        response = self.session.get(url, timeout=10)
                        if response.status_code == 403:
                            soup = BeautifulSoup(response.text, 'html.parser')
                            page_text = soup.get_text().lower()
                            if 'cloudflare' in page_text or 'just a moment' in page_text:
                                return {"error": "Cloudflare protection detected - website blocked", "founders": []}
                    except:
                        pass
                    return {"error": "Website not accessible", "founders": []}
                
                # For SPAs or minimal content sites, try to extract from domain and available content
                is_spa = self._detect_javascript_spa(homepage_soup, url)
                if is_spa:
                    self.logger.info("Attempting to extract founder info from domain and minimal content for SPA")
                    domain_founder = self._extract_founder_from_domain(url, homepage_soup)
                    if domain_founder:
                        return {"founders": [domain_founder], "spa_detected": True}
                return {"error": "No About pages found", "founders": []}
            
            # Extract detailed founder information
            founders = self.extract_founder_details(about_pages)
            
            # Extract social media links as well
            social_media_accounts = self.extract_social_media_links(url)
            
            # Create founder-focused data structure
            founder_data = {
                "company": {
                    "name": "Unknown Company",  # Will be updated if we can extract it
                    "website": url,
                    "analysisDate": self.get_timestamp(),
                    "totalFounders": len(founders),
                    "analysisScope": "Founder and Leadership Research"
                },
                "founders": founders,
                "socialMediaAccounts": social_media_accounts,
                "companyCulture": {
                    "foundingStory": "",
                    "missionStatement": "",
                    "businessType": ""
                },
                "fileConfirmation": "Founder-Analysis-Complete2",
                "url": url,
                "timestamp": self.get_timestamp(),
                "ai_model": self.ai_provider.model,
                "ai_provider": self.ai_provider.name,
                "extractionMethod": "Standalone Founder Details Extraction"
            }
            
            # Note: Founder details are now included in the main business intelligence JSON file
            # No separate founder file is created
            self.logger.info(f"Founder-only extraction completed. Found {len(founders)} founders.")
            
            return founder_data
            
        except Exception as e:
            self.logger.error(f"Error in founder-only extraction: {e}")
            return {"error": str(e), "founders": []}

    def get_output_filename(self, domain: str) -> str:
        """Generate output filename for business intelligence."""
        return f"{domain}-business-intelligence-{self.get_timestamp()}.json"