# Technical Documentation: Brand Analysis & Social Media Content Generation System

## Table of Contents
1. [System Architecture Overview](#system-architecture-overview)
2. [Entry Points](#entry-points)
3. [Core Components](#core-components)
4. [Workflow Orchestration](#workflow-orchestration)
5. [Agent System](#agent-system)
6. [AI Provider System](#ai-provider-system)
7. [Data Flow](#data-flow)
8. [File Structure](#file-structure)
9. [Configuration Management](#configuration-management)
10. [API Integrations](#api-integrations)
11. [Error Handling](#error-handling)
12. [Dependencies](#dependencies)

---

## System Architecture Overview

### High-Level Architecture

The system follows a **modular agent-based architecture** where specialized agents perform specific tasks in a sequential workflow. The architecture consists of:

1. **Entry Layer**: Flask web application (`app.py`) and CLI (`cli.py`)
2. **Orchestration Layer**: `BrandWorkflowOrchestrator` coordinates all agents
3. **Agent Layer**: Specialized agents that inherit from `BaseAgent`
4. **AI Provider Layer**: Abstracted AI provider interface supporting multiple models
5. **Data Layer**: JSON file storage in `metrics/` directory structure

### Design Patterns Used

- **Factory Pattern**: `AIProviderFactory` creates AI providers dynamically
- **Strategy Pattern**: Different AI providers for different capabilities
- **Template Method Pattern**: `BaseAgent` defines common agent workflow
- **Singleton Pattern**: Global `config` instance for configuration

---

## Entry Points

### 1. Flask Web Application (`app.py`)

**Purpose**: HTTP web interface for the brand analysis system

**Key Components**:

```python
# Global workflow results storage (in-memory)
workflow_results = {}  # Stores session_id -> results mapping

# Flask app initialization
app = Flask(__name__)
app.secret_key = 'claude-life-secret-key-2025'
```

**Routes**:

#### `GET /` - Index Page
- Displays form with URL input and AI provider selection
- Queries `AIProviderFactory` for available providers
- Filters to only show configured providers with API keys
- Renders `templates/index.html`

**Technical Details**:
```python
available_providers = AIProviderFactory.list_available_providers()
configured_providers = config.get_available_providers()
# Filter to text-capable providers only
text_providers = [provider for provider in available_providers 
                  if provider in ["claude", "openai", "gemini"]]
```

#### `POST /analyze` - Start Analysis
- Accepts form data: `url`, `text_analysis_provider`, `text_generation_provider`, etc.
- Sets environment variables for this request session
- Generates unique `session_id` from URL and timestamp
- Starts workflow in **background thread** (non-blocking)
- Returns redirect to `/results/<session_id>`

**Technical Details**:
```python
# Session ID generation
session_id = f"{url.replace('https://', '').replace('http://', '').replace('/', '-').replace('.', '-')}-{int(time.time())}"

# Background thread execution
def run_workflow():
    orchestrator = BrandWorkflowOrchestrator()
    results = orchestrator.run_complete_workflow(url)
    workflow_results[session_id] = results

thread = threading.Thread(target=run_workflow)
thread.daemon = True
thread.start()
```

#### `GET /results/<session_id>` - Results Page
- Checks if session exists in `workflow_results`
- If `workflow_status == 'in_progress'`, renders `loading.html`
- If completed, extracts image data and renders `results.html`
- Extracts image metadata: `filename`, `filepath`, `post_number`, `file_size`

#### `GET /status/<session_id>` - Status API
- JSON endpoint for checking workflow status
- Returns: `status`, `phases`, `error` (if any)
- Used by frontend for polling progress

#### `GET /download/<path:filepath>` - Download Images
- Security checks: ensures path starts with `metrics/`
- Resolves absolute path and validates it's within metrics directory
- Uses Flask's `send_file` for secure file serving

**Security Implementation**:
```python
# Security: ensure the file is in the metrics directory
if not filepath.startswith('metrics/'):
    return "Access denied", 403

# Additional security check using path resolution
if not str(full_path.resolve()).startswith(str(base_dir / 'metrics')):
    return "Access denied", 403
```

#### `GET /providers` - Provider Status API
- Returns JSON of available AI providers and their capabilities
- Used by frontend for provider selection UI

### 2. CLI Interface (`cli.py`)

**Purpose**: Command-line interface for running individual agents or complete workflow

**Usage**:
```bash
python cli.py <url> [--agent <agent_name>]
```

**Technical Details**:
- Imports `BrandWorkflowOrchestrator`
- Supports single agent execution via `run_single_agent()`
- Supports complete workflow via `run_complete_workflow()`

---

## Core Components

### 1. Configuration System (`src/config.py`)

**Purpose**: Centralized configuration management

**Key Features**:
- Loads `.env` file automatically on initialization
- Provides API key status checking
- Manages AI provider preferences per capability

**Implementation**:
```python
class Config:
    def _load_environment(self):
        """Load environment variables from .env file."""
        env_file = Path('.env')
        if env_file.exists():
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key] = value
    
    @property
    def ai_providers(self) -> Dict[str, str]:
        """Get AI provider preferences."""
        return {
            "text_analysis": os.getenv("AI_TEXT_ANALYSIS_PROVIDER", "claude"),
            "text_generation": os.getenv("AI_TEXT_GENERATION_PROVIDER", "claude"),
            "image_generation": "gemini",  # Always use Gemini
            "web_analysis": os.getenv("AI_WEB_ANALYSIS_PROVIDER", "claude"),
            "content_strategy": os.getenv("AI_CONTENT_STRATEGY_PROVIDER", "claude")
        }
```

**Global Instance**: `config = Config()` (singleton pattern)

### 2. Base Agent (`src/agents/base_agent.py`)

**Purpose**: Abstract base class for all agents

**Key Features**:
- Logging setup with agent-specific loggers
- Environment variable loading from `.env`
- JSON file save/load utilities
- Domain sanitization
- Dynamic prompt loading from markdown files

**Abstract Methods**:
- `process(url: str, **kwargs) -> Dict[str, Any]`: Must be implemented by each agent
- `get_output_filename(domain: str) -> str`: Must be implemented for file naming

**Key Methods**:

#### `save_json(data, filename, subdir="")`
- Creates directory structure: `metrics/{subdir}/`
- Saves JSON with UTF-8 encoding and `ensure_ascii=False` for international characters
- Returns absolute filepath

#### `load_prompt_from_md(agent_name, prompts_dir=".claude/agents")`
- Loads markdown file: `.claude/agents/{agent_name}.md`
- Removes YAML front matter (content between `---` lines)
- Returns prompt content as string

#### `sanitize_domain(url: str) -> str`
- Extracts domain from URL
- Removes protocol, www, and path
- Replaces dots with hyphens for filesystem compatibility
- Example: `https://www.example.com/path` → `example-com`

---

## Workflow Orchestration

### BrandWorkflowOrchestrator (`src/brand_workflow_orchestrator.py`)

**Purpose**: Coordinates all agents in the correct sequence

**Initialization**:
```python
def __init__(self):
    super().__init__("brand_workflow_orchestrator", "metrics")
    
    # Initialize all agents
    self.business_analyzer = BusinessIntelligenceAnalyzer()
    self.screenshot_analyzer = ScreenshotAnalyzer()
    self.content_creator = SocialContentCreator()
    self.prompt_generator = InstagramPromptGenerator()
    self.image_generator = BrandImageGenerator()
    self.facebook_scraper = FacebookScraper()
```

### Complete Workflow Sequence

#### Phase 1: Business Intelligence Analysis
**Agent**: `BusinessIntelligenceAnalyzer`
**Input**: Website URL
**Output**: Business intelligence JSON with company info, founders, social media accounts
**File Saved**: `metrics/companies/{domain}-business-intelligence-{date}.json`

**Technical Details**:
- Fetches website HTML using `requests` with custom headers
- Parses HTML with `BeautifulSoup4`
- Extracts social media links using regex patterns
- Finds About pages using multilingual patterns
- Extracts founder details from About pages
- Sends cleaned content to AI for structured extraction

#### Phase 2: Design Style Analysis
**Agent**: `ScreenshotAnalyzer`
**Input**: Website URL
**Output**: Design analysis JSON with colors, fonts, style
**File Saved**: `metrics/screenshots/analyses/{domain}-design-analysis-{date}.json`

**Technical Details**:
- Uses ScreenshotOne API to capture website screenshot
- Sends screenshot to AI for visual analysis
- Extracts brand colors (hex codes), fonts, design style

#### Phase 3: Facebook Scraping
**Agent**: `FacebookScraper`
**Input**: Facebook URL (extracted from Phase 1)
**Output**: Facebook posts JSON with recent posts, captions, hashtags
**File Saved**: `metrics/facebook-posts/{domain}/{domain}-facebook-posts-{date}.json`

**Technical Details**:
- Uses Bright Data API for Facebook scraping
- Date range: 2 months ago to today
- Default: 5 posts
- 3-step process: trigger → monitor → retrieve

#### Phase 4: Social Content Creation
**Agent**: `SocialContentCreator`
**Input**: Business intel, design analysis, Facebook posts
**Output**: Social content strategy JSON with Instagram post ideas, captions, hashtags
**File Saved**: `metrics/social-content/{domain}-social-content-{date}.json`

**Technical Details**:
- Analyzes Facebook posts for tone, style, language
- Detects language using keyword matching (French, Danish, English)
- Generates content in detected language
- Creates 3 Instagram post concepts with captions and hashtags

#### Phase 5: Instagram Prompt Generation
**Agent**: `InstagramPromptGenerator`
**Input**: Social content data
**Output**: Detailed image generation prompts JSON
**File Saved**: `metrics/instagram-prompts/{domain}-instagram-prompts-{date}.json`

**Technical Details**:
- Generates detailed prompts for Gemini image generation
- Includes text overlay specifications
- Specifies colors, composition, style
- Language-aware (uses detected language from Phase 4)

#### Phase 6: Brand Image Generation
**Agent**: `BrandImageGenerator`
**Input**: Instagram prompts data
**Output**: PNG images with text overlays
**Files Saved**: `metrics/images/{domain}/{domain}-post-{1,2,3}.png`

**Technical Details**:
- Uses PIL (Pillow) for image generation
- Creates 1080x1080 Instagram square format images
- Extracts text overlay from AI prompts using regex
- Applies brand colors and fonts
- Handles text wrapping for different languages (French, Danish, English)

### Error Handling

```python
try:
    # All phases execute sequentially
    workflow_results["workflow_status"] = "completed"
except Exception as e:
    workflow_results["workflow_status"] = "failed"
    workflow_results["error"] = str(e)
    self.logger.error(f"Workflow failed: {e}")
```

---

## Agent System

### Agent Architecture

All agents inherit from `BaseAgent` and implement:
- `process(url: str, **kwargs) -> Dict[str, Any]`
- `get_output_filename(domain: str) -> str`

### 1. BusinessIntelligenceAnalyzer

**Purpose**: Comprehensive business data extraction

**Key Methods**:

#### `fetch_website_content(url: str) -> str`
- Uses `requests.Session()` with custom headers
- Parses HTML with BeautifulSoup
- Removes script, style, noscript, iframe, svg tags
- Extracts text content with `get_text(separator='\n')`
- Combines title, meta description, meta keywords, and content
- Limits to 15,000 characters for AI processing

#### `extract_social_media_links(url: str) -> List[Dict]`
- Scans all `<a>` tags with regex patterns for 14+ platforms
- Extracts usernames/handles from URLs
- Handles platform-specific URL formats (e.g., `/company/`, `/channel/`, `/@`)
- Checks meta tags for Open Graph URLs
- Returns list of social media account dictionaries

**Regex Patterns**:
```python
social_patterns = {
    'facebook': [r'facebook\.com/[^/\s]+', r'fb\.com/[^/\s]+'],
    'instagram': [r'instagram\.com/[^/\s]+', r'instagr\.am/[^/\s]+'],
    # ... 14+ platforms
}
```

#### `find_about_pages(base_url: str) -> List[str]`
- Detects JavaScript SPAs (Single Page Applications)
- Searches homepage for About sections
- Checks navigation menus and footers
- Supports multilingual About page patterns (15+ languages)
- Finds anchor links for single-page websites

**SPA Detection**:
```python
def _detect_javascript_spa(self, soup, url):
    page_text = soup.get_text()
    if len(page_text) < 200:
        # Check for empty root elements
        root_elements = soup.find_all(['div', 'main', 'app'], 
                                     id=lambda x: x in ['root', 'app', 'main'])
        # Check for framework indicators in script tags
        # Check for "loading" indicators
```

#### `extract_founder_details(about_pages: List[str]) -> List[Dict]`
- Processes each About page
- Extracts founder sections using keyword matching (multilingual)
- Sends content to AI for structured extraction
- Parses AI response (handles dict, JSON string, or nested structures)
- Merges duplicate founders by name

**AI Prompt Structure**:
```python
founder_prompt = f"""{founder_instructions}

TEXT TO ANALYZE FROM ABOUT PAGE:
{text_content[:3000]}

IMPORTANT: Follow the instructions in the founder_extractor.md file exactly.
"""
```

#### `process(url: str, **kwargs) -> Dict[str, Any]`
**Complete Flow**:
1. Fetch website HTML content
2. Load instructions from `.claude/agents/business_intelligence_analyzer.md`
3. Send to AI for business intelligence extraction
4. Find About pages
5. Extract enhanced founder details
6. Extract social media links
7. Merge all data
8. Save to JSON file

**Output Structure**:
```json
{
  "company": {...},
  "founders": [...],
  "socialMediaAccounts": [...],
  "url": "...",
  "timestamp": "2025-01-29",
  "ai_model": "claude-3-5-haiku-20241022",
  "ai_provider": "claude"
}
```

### 2. ScreenshotAnalyzer

**Purpose**: Visual design analysis from website screenshots

**Technical Details**:
- Uses ScreenshotOne API: `https://api.screenshotone.com/take`
- Captures full-page screenshot (1920x1080 viewport)
- Sends screenshot as base64 to AI for visual analysis
- Extracts: color palette, fonts, design style, visual elements

### 3. FacebookScraper

**Purpose**: Scrape Facebook posts using Bright Data API

**Bright Data API Integration**:

#### Step 1: Trigger Data Collection
```python
def trigger_data_collection(self, facebook_url: str, num_posts: int = 5):
    start_date, end_date = self._get_date_range()  # 2 months ago to today
    
    payload = [{
        "url": facebook_url,
        "num_of_posts": num_posts,
        "start_date": start_date,
        "end_date": end_date
    }]
    
    url = f"{self.base_url}/trigger"
    params = {"dataset_id": self.dataset_id, "include_errors": "true"}
    
    response = requests.post(url, headers=headers, json=payload, params=params)
    return snapshot_id  # From response
```

#### Step 2: Monitor Progress
```python
def monitor_progress(self, snapshot_id: str, max_wait_time: int = 300):
    url = f"{self.base_url}/progress/{snapshot_id}"
    
    while time.time() - start_time < max_wait_time:
        response = requests.get(url, headers=headers)
        status = response.json().get("status")
        
        if status in ["completed", "done", "finished", "ready"]:
            return True
        elif status in ["failed", "error"]:
            return False
        
        time.sleep(10)  # Poll every 10 seconds
```

#### Step 3: Get Delivery Data
```python
def get_delivery_data(self, snapshot_id: str):
    url = f"{self.base_url}/snapshot/{snapshot_id}"
    params = {"format": "json"}
    
    response = requests.get(url, headers=headers, params=params)
    return response.json()  # List of posts
```

**Configuration**:
- API key: `BRIGHT_DATA_API_KEY` from `.env`
- Dataset ID: `BRIGHT_DATA_DATASET_ID` from `.env`
- Base URL: `https://api.brightdata.com/datasets/v3`

**File Structure**:
- Saves to: `metrics/facebook-posts/{domain}/{domain}-facebook-posts-{date}.json`
- Uses domain from original URL (not Facebook URL) for directory structure

### 4. SocialContentCreator

**Purpose**: Generate Instagram content strategy based on brand analysis and Facebook posts

**Key Methods**:

#### `_analyze_facebook_posts(facebook_posts: Dict) -> Dict`
- Extracts content samples, hashtags, engagement metrics
- Detects language from all post content combined
- Analyzes tone, style, post types
- Returns analysis with `detected_language` field

#### `_detect_language(text: str) -> str`
- Simple keyword-based language detection
- French: checks for `['le', 'la', 'les', 'de', 'du', 'avec', ...]`
- Danish: checks for `['og', 'er', 'at', 'i', 'det', 'på', 'onsdag', ...]`
- English: fallback
- Uses scoring: counts keyword matches, returns highest score

**Language Detection Logic**:
```python
french_score = sum(1 for word in french_words if word in text_lower)
danish_score = sum(1 for word in danish_words if word in text_lower)
english_score = sum(1 for word in english_words if word in text_lower)

# Special indicators first
if 'onsdag' in text_lower or 'oktober' in text_lower:
    return "da"
if 'jour' in text_lower or 'avec' in text_lower:
    return "fr"

# Then scoring
if french_score > danish_score and french_score > english_score:
    return "fr"
elif danish_score > english_score and danish_score > 0:
    return "da"
else:
    return "en"
```

#### `_load_facebook_posts_analysis(url: str) -> Dict`
- Auto-loads Facebook posts if not provided
- Searches `metrics/facebook-posts/{domain}/` for most recent file
- Analyzes loaded posts and returns analysis

#### `process(url, business_intel, design_analysis, facebook_posts, **kwargs)`
- Requires `business_intel` and `design_analysis`
- Optionally accepts `facebook_posts` (or auto-loads)
- Analyzes Facebook posts for tone/style/language
- Sends to AI with instructions to generate content in detected language
- Stores `detected_language` in output JSON

**AI Integration**:
- Calls `ai_provider.create_content_strategy()` with `facebook_analysis` parameter
- AI provider includes language instruction in prompt

### 5. InstagramPromptGenerator

**Purpose**: Generate detailed image generation prompts for Gemini

**Technical Details**:
- Takes social content data (includes brand analysis and detected language)
- Loads instructions from `.claude/agents/instagram_prompt_generator.md`
- Calls `ai_provider.generate_instagram_prompts()`
- Generates prompts with text overlay specifications
- Language-aware: includes detected language in prompt

### 6. BrandImageGenerator

**Purpose**: Generate actual PNG images with text overlays

**Key Methods**:

#### `get_design_data(url: str) -> Dict`
- Loads most recent design analysis file
- Searches `metrics/screenshots/analyses/` for domain-specific files
- Returns design data with color kit and fonts

#### `hex_to_rgb(hex_color: str) -> tuple`
- Converts hex color (#RRGGBB) to RGB tuple
- Example: `#FF5733` → `(255, 87, 51)`

#### `create_text_image(text, background_color, text_color, font_family, post_number) -> Image`
- Creates 1080x1080 PNG image (Instagram square format)
- Uses PIL `Image.new('RGB', (width, height), bg_rgb)`
- Font loading with fallback chain:
  1. Brand font from system paths
  2. Common fonts (Arial, Helvetica, DejaVu Sans)
  3. PIL default font
- Text wrapping with language-aware width calculation:
  - French: 30-32 pixels per character (accounts for accents)
  - Other: 36 pixels per character
- Centers text vertically and horizontally
- Adds post number in bottom-right corner

**Text Wrapping Logic**:
```python
char_width = 30 if any(char in word for char in 'àâäéèêëïîôöùûüÿçñ') else 36
max_width = width - (padding * 2)  # 1080 - 160 = 920

words = text.split()
lines = []
current_line = []

for word in words:
    test_line = ' '.join(current_line + [word])
    if len(test_line) * char_width < max_width:
        current_line.append(word)
    else:
        if current_line:
            lines.append(' '.join(current_line))
        current_line = [word]
```

#### `process(url, prompts_data, **kwargs)`
**Complete Flow**:
1. Load design data (colors, fonts)
2. Extract brand colors: `brand_primary` (background), `brand_secondary` (text)
3. For each prompt in `prompts_data["instagram_posts"]`:
   - Extract text overlay using regex patterns
   - Create image with `create_text_image()`
   - Save to `metrics/images/{domain}/{domain}-post-{n}.png`
4. Return results with image metadata

**Text Extraction from AI Prompts**:
- Uses multiple regex patterns to extract overlay text from Gemini prompts
- Handles French prompts: `"Superposez le texte 'text'"`, `"ajoutez le texte 'text'"`
- Handles English prompts: `"TEXT OVERLAY: 'text'"`, `"overlay: 'text'"`
- Cleans extracted text: removes descriptive words, trailing punctuation
- Truncates overly long extractions intelligently

**Regex Patterns**:
```python
patterns = [
    r"TEXT OVERLAY:\s*['\"]([^'\"]+)['\"]",
    r"text overlay:\s*['\"]([^'\"]+)['\"]",
    r"overlay:\s*['\"]([^'\"]+)['\"]",
    r"Superposez le texte\s+['\"]([^'\"]+)['\"]",
    r"ajoutez le texte\s+['\"]([^'\"]+)['\"]",
    r"reading\s+['\"]([^'\"]+)['\"]",
    # Fallback: quoted text within 100 characters
    r"['\"]([^'\"]{1,100})['\"]"
]
```

---

## AI Provider System

### Architecture

**Abstract Base Class**: `BaseAIProvider`
**Factory**: `AIProviderFactory`
**Concrete Implementations**: `ClaudeProvider`, `GeminiProvider`, `OpenAIProvider`

### BaseAIProvider (`src/ai_providers/base_provider.py`)

**Capabilities Enum**:
```python
class AICapability(Enum):
    TEXT_ANALYSIS = "text_analysis"
    TEXT_GENERATION = "text_generation"
    IMAGE_ANALYSIS = "image_analysis"
    IMAGE_GENERATION = "image_generation"
    WEB_ANALYSIS = "web_analysis"
    CONTENT_STRATEGY = "content_strategy"
```

**Abstract Methods**:
- `analyze_text(text: str, prompt: str) -> Dict[str, Any]`
- `generate_text(prompt: str) -> str`
- `analyze_website(html_content: str, url: str, **kwargs) -> Dict[str, Any]`
- `create_content_strategy(business_data: Dict, **kwargs) -> Dict[str, Any]`

### AIProviderFactory (`src/ai_providers/ai_factory.py`)

**Purpose**: Creates and manages AI provider instances

**Key Methods**:

#### `create_provider(provider_name: str, model: str = None) -> BaseAIProvider`
- Maps provider names to classes
- Instantiates provider with optional model parameter

#### `get_configured_provider(capability: AICapability) -> BaseAIProvider`
- Checks environment variables for preferred provider
- Forces Gemini for image generation
- Falls back to default provider if configured one unavailable

**Provider Selection Logic**:
```python
# Force Gemini for image generation
if capability == AICapability.IMAGE_GENERATION:
    return cls.create_provider("gemini", "gemini-2.5-flash-image-preview")

# Check environment variables
provider_config = {
    AICapability.TEXT_ANALYSIS: os.getenv("AI_TEXT_ANALYSIS_PROVIDER", "claude"),
    AICapability.TEXT_GENERATION: os.getenv("AI_TEXT_GENERATION_PROVIDER", "claude"),
    # ...
}

preferred_provider = provider_config.get(capability, "claude")
return cls.create_provider(preferred_provider)
```

### ClaudeProvider (`src/ai_providers/claude_provider.py`)

**Model**: `claude-3-5-haiku-20241022` (default)

**API Integration**:
- Base URL: `https://api.anthropic.com/v1/messages`
- Authentication: `x-api-key` header
- API Version: `anthropic-version: 2023-06-01`

**Key Methods**:

#### `_make_request(prompt, system_prompt=None, content=None, **kwargs)`
- Constructs messages array
- Supports system prompts
- Retry logic for 529 (Overloaded) errors
- Returns JSON response

#### `analyze_website(html_content, url, agent_name, **kwargs)`
- Loads dynamic prompt from `.claude/agents/{agent_name}.md`
- Sends HTML content (truncated to 20,000 chars) to Claude
- Parses JSON response (handles markdown code blocks)
- Returns structured business intelligence data

**Response Parsing**:
```python
response_text = response["content"][0]["text"]

# Extract JSON from markdown code blocks
if "```json" in response_text:
    json_start = response_text.find("```json") + 7
    json_end = response_text.find("```", json_start)
    json_str = response_text[json_start:json_end].strip()
elif "```" in response_text:
    # Extract from plain code blocks
    # ...
else:
    # Try to parse directly as JSON
    json_str = response_text

business_intel = json.loads(json_str)
```

#### `create_content_strategy(business_intel, design_analysis, facebook_analysis=None, agent_name="social_content_creator")`
- Loads prompt from `.claude/agents/social_content_creator.md`
- Includes `facebook_analysis` with detected language
- Instructs AI to generate content in detected language
- Returns social content strategy JSON

#### `generate_instagram_prompts(social_content, url, agent_name="instagram_prompt_generator")`
- Loads prompt from `.claude/agents/instagram_prompt_generator.md`
- Extracts `detected_language` from social content
- Includes language in prompt for image generation
- Returns Instagram prompts JSON

**Capabilities**:
- ✅ TEXT_ANALYSIS
- ✅ TEXT_GENERATION
- ✅ WEB_ANALYSIS
- ✅ CONTENT_STRATEGY
- ❌ IMAGE_ANALYSIS
- ❌ IMAGE_GENERATION

### GeminiProvider (`src/ai_providers/gemini_provider.py`)

**Model**: `gemini-2.5-flash-image-preview` (for image generation)

**Capabilities**:
- ✅ IMAGE_GENERATION (primary use case)
- ✅ TEXT_ANALYSIS
- ✅ TEXT_GENERATION

**Note**: Gemini is primarily used for image generation, though it supports text capabilities.

### OpenAIProvider (`src/ai_providers/openai_provider.py`)

**Model**: `gpt-4o` (default)

**Capabilities**:
- ✅ TEXT_ANALYSIS
- ✅ TEXT_GENERATION
- ✅ WEB_ANALYSIS
- ✅ CONTENT_STRATEGY
- ❌ IMAGE_ANALYSIS
- ❌ IMAGE_GENERATION

---

## Data Flow

### Complete Data Flow Diagram

```
User Input (URL)
    ↓
[Flask App] → Session ID Generation
    ↓
[Background Thread] → BrandWorkflowOrchestrator
    ↓
Phase 1: BusinessIntelligenceAnalyzer
    ├─ Fetch HTML → BeautifulSoup
    ├─ Extract Social Media Links
    ├─ Find About Pages
    ├─ Extract Founder Details
    └─ AI Analysis → metrics/companies/{domain}-business-intelligence-{date}.json
    ↓
Phase 2: ScreenshotAnalyzer
    ├─ ScreenshotOne API → Screenshot
    └─ AI Visual Analysis → metrics/screenshots/analyses/{domain}-design-analysis-{date}.json
    ↓
Phase 3: FacebookScraper
    ├─ Bright Data API → Trigger → Monitor → Retrieve
    └─ Facebook Posts → metrics/facebook-posts/{domain}/{domain}-facebook-posts-{date}.json
    ↓
Phase 4: SocialContentCreator
    ├─ Load Business Intel + Design Analysis + Facebook Posts
    ├─ Analyze Facebook Posts (language detection)
    └─ AI Content Strategy → metrics/social-content/{domain}-social-content-{date}.json
    ↓
Phase 5: InstagramPromptGenerator
    ├─ Load Social Content
    └─ AI Prompt Generation → metrics/instagram-prompts/{domain}-instagram-prompts-{date}.json
    ↓
Phase 6: BrandImageGenerator
    ├─ Load Design Data + Instagram Prompts
    ├─ Extract Text Overlay (regex)
    └─ PIL Image Generation → metrics/images/{domain}/{domain}-post-{1,2,3}.png
    ↓
[Workflow Results] → workflow_results[session_id]
    ↓
[Flask Results Page] → Display JSON + Images
```

### Data Dependencies

**Phase 1** → **Phase 2**: Independent (can run in parallel)
**Phase 1** → **Phase 3**: Facebook URL extracted from Phase 1
**Phase 1 + Phase 2** → **Phase 4**: Both required
**Phase 3** → **Phase 4**: Optional (auto-loads if not provided)
**Phase 4** → **Phase 5**: Required
**Phase 2 + Phase 5** → **Phase 6**: Both required

### JSON Data Structures

#### Business Intelligence JSON
```json
{
  "company": {
    "name": "...",
    "description": "...",
    "industry": "...",
    "targetAudience": [...]
  },
  "founders": [
    {
      "name": "...",
      "role": "...",
      "background": "...",
      "linkedin": "..."
    }
  ],
  "socialMediaAccounts": [
    {
      "platform": "Facebook",
      "url": "...",
      "username": "...",
      "handle": "@..."
    }
  ],
  "url": "...",
  "timestamp": "2025-01-29",
  "ai_model": "...",
  "ai_provider": "claude"
}
```

#### Facebook Posts JSON
```json
{
  "status": "success",
  "facebook_url": "...",
  "snapshot_id": "...",
  "num_posts_requested": 5,
  "num_posts_retrieved": 5,
  "scraped_at": "2025-01-29T10:30:00",
  "posts": [
    {
      "content": "...",
      "likes": 100,
      "num_comments": 10,
      "num_shares": 5,
      "post_type": "photo",
      "page_name": "..."
    }
  ]
}
```

#### Social Content JSON
```json
{
  "brand_analysis": {
    "detected_language": "fr",
    "tone": "...",
    "style": "..."
  },
  "instagram_posts": [
    {
      "post_number": 1,
      "caption": "...",
      "hashtags": ["#hashtag1", "#hashtag2"],
      "theme": "...",
      "post_type": "inspirational",
      "target_emotion": "...",
      "engagement_goal": "..."
    }
  ],
  "url": "...",
  "timestamp": "2025-01-29",
  "ai_model": "...",
  "ai_provider": "claude"
}
```

#### Instagram Prompts JSON
```json
{
  "instagram_posts": [
    {
      "post_number": 1,
      "prompt": "Create a 1080x1080 image with... TEXT OVERLAY: 'Un trait après l'autre'",
      "text_overlay": "Un trait après l'autre",
      "style": "...",
      "colors": [...]
    }
  ]
}
```

---

## File Structure

### Directory Structure

```
/
├── app.py                          # Flask web application
├── cli.py                          # CLI interface
├── main.py                         # Alternative entry point
├── requirements.txt                # Python dependencies
├── .env                            # Environment variables (not in repo)
├── run_webapp.sh                   # Shell script to run webapp
│
├── src/
│   ├── __init__.py
│   ├── config.py                   # Configuration management
│   ├── brand_workflow_orchestrator.py  # Workflow coordinator
│   │
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base_agent.py           # Base agent class
│   │   ├── business_intelligence_analyzer.py
│   │   ├── screenshot_analyzer.py
│   │   ├── facebook_scraper.py
│   │   ├── social_content_creator.py
│   │   ├── instagram_prompt_generator.py
│   │   └── brand_image_generator.py
│   │
│   └── ai_providers/
│       ├── __init__.py
│       ├── ai_factory.py           # Provider factory
│       ├── base_provider.py        # Base provider interface
│       ├── claude_provider.py
│       ├── gemini_provider.py
│       └── openai_provider.py
│
├── templates/
│   ├── base.html
│   ├── index.html                  # Main form page
│   ├── loading.html                # Loading page
│   └── results.html                # Results display page
│
├── static/
│   ├── index.html
│   └── deployment-guide.html
│
├── metrics/                         # Generated data (not in repo)
│   ├── companies/
│   │   └── {domain}-business-intelligence-{date}.json
│   ├── screenshots/
│   │   └── analyses/
│   │       └── {domain}-design-analysis-{date}.json
│   ├── facebook-posts/
│   │   └── {domain}/
│   │       └── {domain}-facebook-posts-{date}.json
│   ├── social-content/
│   │   └── {domain}-social-content-{date}.json
│   ├── instagram-prompts/
│   │   └── {domain}-instagram-prompts-{date}.json
│   └── images/
│       └── {domain}/
│           ├── {domain}-post-1.png
│           ├── {domain}-post-2.png
│           └── {domain}-post-3.png
│
└── .claude/
    └── agents/                      # Dynamic prompts (not in repo)
        ├── business_intelligence_analyzer.md
        ├── screenshot_analyzer.md
        ├── social_content_creator.md
        ├── instagram_prompt_generator.md
        └── founder_extractor.md
```

### File Naming Convention

**Pattern**: `{domain}-{agent-type}-{date}.json` or `{domain}-post-{n}.png`

**Examples**:
- `jijihook-fr-business-intelligence-2025-01-29.json`
- `1community-dk-facebook-posts-2025-01-29.json`
- `sproutworld-com-post-1.png`

**Domain Sanitization**:
- `https://www.example.com/path` → `example-com`
- `https://shop.example.se` → `shop-example-se`
- Replaces dots with hyphens, removes protocol and path

---

## Configuration Management

### Environment Variables (`.env` file)

```bash
# AI Provider API Keys
CLAUDE_API_KEY=sk-ant-...
GEMINI_API_KEY=AIza...
OPENAI_API_KEY=sk-...

# AI Provider Preferences (optional)
AI_TEXT_ANALYSIS_PROVIDER=claude
AI_TEXT_GENERATION_PROVIDER=claude
AI_WEB_ANALYSIS_PROVIDER=claude
AI_CONTENT_STRATEGY_PROVIDER=claude

# Bright Data API (Facebook Scraping)
BRIGHT_DATA_API_KEY=brd-...
BRIGHT_DATA_DATASET_ID=gd_lkaxegm826bjpoo9m5

# ScreenshotOne API (Design Analysis)
SCREENSHOT_API_KEY=...

# Flask Configuration
PORT=5001
```

### Configuration Loading

**Automatic Loading**:
- `Config` class loads `.env` on initialization
- `BaseAgent` also loads `.env` in `_load_environment()`
- Agents access via `os.getenv()`

**Provider Selection**:
- Environment variables override defaults
- Per-capability provider selection
- Falls back to defaults if configured provider unavailable

---

## API Integrations

### 1. Anthropic Claude API

**Endpoint**: `https://api.anthropic.com/v1/messages`
**Authentication**: `x-api-key` header
**Model**: `claude-3-5-haiku-20241022`

**Request Format**:
```json
{
  "model": "claude-3-5-haiku-20241022",
  "messages": [{"role": "user", "content": [{"type": "text", "text": "..."}]}],
  "system": "...",
  "max_tokens": 4000
}
```

**Response Format**:
```json
{
  "content": [{"type": "text", "text": "..."}],
  "model": "...",
  "stop_reason": "end_turn"
}
```

**Error Handling**:
- 529 (Overloaded): Retries with exponential backoff (3s, 6s)
- Other errors: Raises exception

### 2. Bright Data API (Facebook Scraping)

**Base URL**: `https://api.brightdata.com/datasets/v3`
**Authentication**: `Authorization: Bearer {api_key}` header

**Endpoints**:
- `POST /trigger` - Start data collection
- `GET /progress/{snapshot_id}` - Check status
- `GET /snapshot/{snapshot_id}` - Retrieve data

**Request/Response Flow**:
1. Trigger: `POST /trigger?dataset_id={id}` with payload `[{"url": "...", "num_of_posts": 5, "start_date": "...", "end_date": "..."}]`
2. Monitor: `GET /progress/{snapshot_id}` (poll every 10s)
3. Retrieve: `GET /snapshot/{snapshot_id}?format=json`

### 3. ScreenshotOne API

**Endpoint**: `https://api.screenshotone.com/take`
**Authentication**: Query parameter `access_key`

**Request Format**:
```
GET /take?access_key={key}&url={url}&viewport_width=1920&viewport_height=1080&full_page=true
```

**Response**: PNG image (binary)

### 4. Google Gemini API

**Purpose**: Image generation
**Model**: `gemini-2.5-flash-image-preview`
**Note**: Implemented in `GeminiProvider`, primarily used for image generation

---

## Error Handling

### Workflow-Level Error Handling

```python
try:
    # All phases execute sequentially
    workflow_results["workflow_status"] = "completed"
except Exception as e:
    workflow_results["workflow_status"] = "failed"
    workflow_results["error"] = str(e)
    self.logger.error(f"Workflow failed: {e}")
```

### Agent-Level Error Handling

**Pattern**: Each agent logs errors and returns error status
```python
try:
    result = self.process(url)
    return {"status": "success", "data": result}
except Exception as e:
    self.logger.error(f"Agent error: {e}")
    return {"status": "failed", "error": str(e)}
```

### API-Level Error Handling

**Claude API**:
- 529 (Overloaded): Retry with backoff
- Other HTTP errors: Raise exception

**Bright Data API**:
- Network errors: Return failure status
- Timeout: Return failure after max wait time

**File Operations**:
- FileNotFoundError: Log warning, return None
- JSONDecodeError: Log error, return None

### User-Facing Error Handling

**Flask App**:
- Flash messages for validation errors
- Error pages for missing sessions
- JSON error responses for API endpoints

---

## Dependencies

### Python Dependencies (`requirements.txt`)

```txt
Flask>=2.3.0              # Web framework
requests>=2.31.0          # HTTP client
python-dotenv>=1.0.0      # Environment variable loading
Pillow>=10.4.0            # Image processing (PIL)
anthropic>=0.25.0         # Claude API client
openai>=1.30.0            # OpenAI API client
google-generativeai>=0.5.0  # Gemini API client
beautifulsoup4>=4.12.0    # HTML parsing
```

### System Dependencies

**Fonts** (for image generation):
- macOS: `/System/Library/Fonts/`
- Linux: `/usr/share/fonts/truetype/`
- Windows: `C:\Windows\Fonts\`

**Fallback Fonts**:
- Arial, Helvetica, DejaVu Sans, Liberation Sans
- PIL default font (last resort)

---

## Key Technical Details

### Language Detection Algorithm

**Method**: Keyword-based scoring
**Supported Languages**: French (fr), Danish (da), English (en)

**Implementation**:
1. Combine all text from Facebook posts
2. Count keyword matches for each language
3. Check for special indicators first (days, cities)
4. Return language with highest score

**Limitations**:
- Simple keyword matching (not ML-based)
- May misclassify multilingual content
- English as default fallback

### Text Extraction from AI Prompts

**Challenge**: Extracting overlay text from natural language AI prompts

**Solution**: Multi-pattern regex matching with fallback

**Patterns** (in order of specificity):
1. `TEXT OVERLAY: 'text'`
2. `text overlay: 'text'`
3. `overlay: 'text'`
4. `Superposez le texte 'text'` (French)
5. `ajoutez le texte 'text'` (French)
6. `reading 'text'`
7. `le texte 'text' apparaît` (French)
8. Fallback: Any quoted text up to 100 characters

**Text Cleaning**:
- Removes descriptive words: "diagonally", "across", "composition", "en police", "couleur"
- Removes trailing punctuation
- Truncates overly long extractions intelligently

### Image Generation Technical Details

**Format**: PNG, 1080x1080 pixels (Instagram square)

**Text Rendering**:
- Font size: 48px (default)
- Line spacing: 50% of font size
- Padding: 80px on all sides
- Text wrapping: Language-aware character width

**Color Handling**:
- Hex to RGB conversion
- Background: `brand_primary` from design analysis
- Text: `brand_secondary` from design analysis
- Fallback: Black background, white text

**Font Loading**:
- Attempts brand font first
- Falls back to common system fonts
- Last resort: PIL default font

---

## Conclusion

This system provides a complete, automated solution for brand analysis and social media content generation. The modular architecture allows for easy extension and maintenance, while the AI provider abstraction enables flexible model selection.

**Key Strengths**:
- Modular agent-based architecture
- Multi-language support
- Flexible AI provider system
- Comprehensive error handling
- Secure file serving

**Areas for Enhancement**:
- More sophisticated language detection (ML-based)
- Caching for repeated analyses
- Database storage option (beyond JSON files)
- Real-time progress updates via WebSockets
- Image generation with actual graphics (beyond text overlays)

---

*Last Updated: January 29, 2025*
