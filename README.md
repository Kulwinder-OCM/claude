# Claude Life - Brand Analysis & Social Media Campaign Generator

A Python-based system that analyzes websites and generates complete branded social media campaigns with actual Instagram images.

## 🚀 Features

- **Multi-AI Integration** - Switch between Claude, OpenAI, and Gemini for different tasks
- **AI-Powered Business Intelligence** - Deep company analysis using advanced language models
- **Smart Content Strategy** - AI-generated Instagram campaigns tailored to brand voice
- **Professional Image Generation** - Create branded visuals with DALL-E or Gemini
- **Flexible Provider System** - Configure AI providers per capability for optimal results
- **Complete Workflow** - Orchestrated multi-AI pipeline for full campaign creation

## 📋 Prerequisites

- Python 3.8+
- AI Provider API Keys (at least one required):
  - **Claude API Key** - Get from [Anthropic Console](https://console.anthropic.com/) **(Recommended)**
  - **OpenAI API Key** - Get from [OpenAI Platform](https://platform.openai.com/api-keys) 
  - **Gemini API Key** - Get from [Google AI Studio](https://makersuite.google.com/app/apikey)
- **ScreenshotOne API Key** - Get from [ScreenshotOne](https://screenshotone.com/)

## 🛠️ Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd Claudelife-main
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure environment variables**

Edit the `.env` file and add your API keys:
```bash
# AI Provider API Keys (add the ones you have)
CLAUDE_API_KEY=your_claude_api_key_here
OPENAI_API_KEY=your_openai_api_key_here  
GEMINI_API_KEY=your_gemini_api_key_here

# ScreenshotOne API Configuration  
SCREENSHOT_ENDPOINT=https://api.screenshotone.com/take
SCREENSHOT_API_KEY=your_screenshotone_api_key_here

# AI Provider Preferences (optional - smart defaults used)
AI_WEB_ANALYSIS_PROVIDER=claude
AI_CONTENT_STRATEGY_PROVIDER=claude
AI_IMAGE_GENERATION_PROVIDER=openai
```

## 🎯 Usage

### Complete Workflow (Recommended)
Generate a complete AI-powered branded social media campaign:
```bash
python cli.py https://example.com
```

### Check AI Provider Status
See which AI providers are configured and available:
```bash
python cli.py --providers
```

### Individual Agents
Run specific agents:

```bash
# Screenshot analysis only
python cli.py https://example.com --agent screenshot

# AI-powered business intelligence 
python cli.py https://example.com --agent business

# AI-generated social content strategy
python cli.py https://example.com --agent content

# Instagram prompts generation
python cli.py https://example.com --agent prompts

# AI image generation
python cli.py https://example.com --agent images
```

### Advanced Usage
```bash
# Enable detailed logging
python cli.py https://example.com --verbose

# Test all configured AI providers
python cli.py --test-providers

# Use specific AI provider for analysis
AI_WEB_ANALYSIS_PROVIDER=openai python cli.py https://example.com
```

## 📁 Output Structure

All generated files are organized in the `metrics/` directory:

```
metrics/
├── companies/
│   └── domain-business-intelligence-YYYY-MM-DD.json
├── screenshots/analyses/
│   └── domain-design-analysis-YYYY-MM-DD.json
├── social-content/
│   └── domain-social-content-YYYY-MM-DD.json
├── instagram-prompts/
│   └── domain-instagram-prompts-YYYY-MM-DD.json
└── images/domain/
    ├── domain-post-1.png
    ├── domain-post-2.png
    ├── domain-post-3.png
    └── domain-image-generation-YYYY-MM-DD.json
```

## 🔧 Architecture

The system consists of 5 main agents:

1. **ScreenshotAnalyzer** - Captures website screenshots using ScreenshotOne API and extracts design elements (colors, typography, layout)

2. **BusinessIntelligenceAnalyzer** - Scrapes website content to gather business information, services, and market positioning

3. **SocialContentCreator** - Creates Instagram post concepts based on business intelligence and design analysis

4. **InstagramPromptGenerator** - Generates detailed Gemini API prompts for image creation

5. **BrandImageGenerator** - Uses Gemini API to generate actual Instagram images

6. **BrandWorkflowOrchestrator** - Coordinates all agents to run the complete workflow

## 📊 Example Workflow

1. **Input**: `https://moodpublishing.com`

2. **Processing**:
   - Captures screenshot → Extracts dark gaming aesthetic with cyan/orange accents
   - Analyzes business → Danish board game publisher specializing in video game adaptations  
   - Creates content → 3 Instagram posts about craftsmanship, brand story, community
   - Generates prompts → Detailed Gemini prompts with exact brand colors and typography
   - Creates images → 3 branded Instagram images ready for posting

3. **Output**: Complete branded social media campaign with analysis data and actual images

## 🛡️ Error Handling

- Comprehensive logging for all operations
- Graceful failure handling for individual agents
- Partial workflow completion if some agents fail
- Detailed error reporting with stack traces in verbose mode

## 🔍 API Integration

### ScreenshotOne API
- Mobile-first screenshot capture (375x812px)
- Full-page screenshots with cookie banner/ad blocking
- High-resolution 2x device scale factor

### Gemini API  
- Text-to-image generation for Instagram posts
- Brand-consistent image creation with detailed prompts
- 1080x1080 Instagram-optimized format

## 📈 Extensibility

The modular architecture makes it easy to:
- Add new agents for additional functionality
- Integrate different APIs (replace ScreenshotOne, Gemini)  
- Customize output formats and file organization
- Add new social media platforms beyond Instagram

## 🐛 Troubleshooting

**Missing API Keys**:
```
ValueError: Environment variable GEMINI_API_KEY not set
```
→ Check your `.env` file has valid API keys

**Network Issues**:
```
requests.exceptions.ConnectionError
```  
→ Check internet connection and API endpoints

**Image Generation Issues**:
The current implementation includes placeholder image generation. For actual image generation, ensure your Gemini API key has access to image generation models.

## 📄 License

This project is part of the Claude Life ecosystem for automated brand analysis and social media campaign generation.