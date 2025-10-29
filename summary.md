# Brand Analysis Workflow - Project Summary

## Overview
A comprehensive brand analysis platform that combines business intelligence, design analysis, social content creation, and Facebook scraping to provide complete brand insights.

## Core Features

### 1. Business Intelligence Analysis
- **Agent**: `business_intelligence_analyzer.py`
- **Purpose**: Extracts comprehensive business data from websites
- **Output**: Company details, founder information, social media accounts, competitive analysis
- **Saves to**: `metrics/companies/`

### 2. Design Analysis
- **Agent**: `screenshot_analyzer.py`
- **Purpose**: Analyzes website design and visual elements
- **Output**: Design insights, color schemes, layout analysis
- **Saves to**: `metrics/screenshots/analyses/`

### 3. Brand Image Generation
- **Agent**: `brand_image_generator.py`
- **Purpose**: Creates branded social media images
- **Output**: Generated images with brand elements
- **Saves to**: `metrics/images/`

### 4. Social Content Creation
- **Agent**: `social_content_creator.py`
- **Purpose**: Generates social media content strategies
- **Output**: Content ideas, hashtags, posting strategies
- **Saves to**: `metrics/social-content/`

### 5. Instagram Prompt Generation
- **Agent**: `instagram_prompt_generator.py`
- **Purpose**: Creates AI prompts for Instagram content
- **Output**: Prompt templates for content creation
- **Saves to**: `metrics/instagram-prompts/`

### 6. Facebook Scraping
- **Agent**: `facebook_scraper.py`
- **Purpose**: Scrapes Facebook posts using Bright Data API
- **Configuration**: 2 months date range, 5 posts limit
- **Output**: Facebook posts data
- **Saves to**: `metrics/facebook-posts/`

## Workflow Orchestration
- **Main Orchestrator**: `brand_workflow_orchestrator.py`
- **Phases**:
  1. Business Intelligence Analysis
  2. Design Analysis
  3. Facebook Scraping (for content analysis)
  4. Social Content Creation (with Facebook analysis)
  5. Instagram Prompt Generation
  6. Brand Image Generation

## AI Providers
- **Claude**: Primary AI provider for analysis
- **OpenAI**: Alternative AI provider
- **Gemini**: Google's AI provider
- **Factory Pattern**: `ai_factory.py` manages provider selection

## Web Interface
- **Flask App**: `app.py`
- **Templates**: HTML templates in `templates/`
- **Static Assets**: CSS/JS in `static/`
- **Startup Script**: `run_webapp.sh`

## Configuration
- **Environment Variables**: `.env` file for API keys
- **Dependencies**: `requirements.txt`
- **Virtual Environment**: `venv/`

## Data Storage
All analysis results are saved in the `metrics/` directory with organized subdirectories:
- `companies/` - Business intelligence data
- `screenshots/` - Design analysis results
- `images/` - Generated brand images
- `social-content/` - Social media content
- `instagram-prompts/` - Instagram prompt templates
- `facebook-posts/` - Scraped Facebook data

## Recent Updates
- ✅ Facebook scraper integrated with Bright Data API
- ✅ Date range configured to 2 months (start: 2 months ago, end: today)
- ✅ Posts limit set to 5 by default
- ✅ Clean project structure (test files removed)
- ✅ Environment-based configuration (no hardcoded API keys)

## Usage
1. **Web Interface**: Run `./run_webapp.sh` and visit the web interface
2. **CLI**: Use `python main.py` for command-line analysis
3. **Single Agent**: Use orchestrator to run individual agents

## Dependencies
- Flask (web framework)
- Requests (HTTP client)
- Python-dotenv (environment variables)
- AI provider SDKs (OpenAI, Anthropic, Google)
- Bright Data API (Facebook scraping)

## Work Log & Future Reference

### Recent Work Completed

**API Configuration Fix (2025-10-29)**
- **Issue**: Claude API returning 404 error with model `claude-3-5-sonnet-20241022`
- **Root Cause**: Model name was incorrect/not available in the API
- **Solution**: Updated Claude provider to use working model `claude-3-5-haiku-20241022`
- **Testing**: Verified all workflow phases now complete successfully
- **Status**: ✅ Resolved - Complete workflow now functional
- **Facebook Scraper Integration**: Successfully integrated Bright Data API for Facebook post scraping
- **Configuration Updates**: Set date range to 2 months (start: 2 months ago, end: today), posts limit to 5
- **Environment Configuration**: Removed hardcoded API keys, now reads from .env file
- **Project Cleanup**: Removed all test files, debug scripts, and temporary documentation
- **Summary Restoration**: Recreated comprehensive project summary for reference
- **Enhanced Social Content Creator**: Integrated Facebook posts analysis to generate authentic content matching brand owner's tone and style
- **Web Interface Enhancement**: Added display of generated captions and hashtags on results page
- **Interactive Features**: Click-to-copy hashtags, responsive design for social content display
- **Image Text Extraction Fix**: Improved text extraction from Instagram prompts to properly handle French text with apostrophes
- **Facebook Posts Directory Structure**: Enhanced Facebook scraper to save JSON files in company-specific directories (facebook-posts/{company-name}/)
- **Multi-Language Content Generation**: Implemented automatic language detection from Facebook posts to generate captions in the same language (Danish, French, English)

### Current Status
- ✅ All 6 agents fully functional
- ✅ Facebook scraper working with Bright Data API
- ✅ Enhanced social content creator with Facebook analysis integration
- ✅ Workflow orchestration updated (Facebook scraping → Social content creation)
- ✅ Web interface enhanced with social content display (captions & hashtags)
- ✅ Interactive features: click-to-copy hashtags, responsive design
- ✅ Facebook posts organized in company-specific directories
- ✅ Multi-language content generation (Danish, French, English) based on Facebook posts
- ✅ Clean project structure ready for production
- ✅ Environment-based configuration implemented
- ✅ Web interface and CLI both operational

### Notes for Future Development
- Facebook scraper requires active Bright Data account
- Social content creator now analyzes Facebook posts for authentic tone matching
- Workflow phases: Business Intelligence → Design Analysis → Facebook Scraping → Social Content Creation → Instagram Prompts → Brand Images
- All analysis results saved in organized metrics/ directory
- Webapp can be started with `./run_webapp.sh`
- CLI available via `python main.py`
- Individual agents can be run via orchestrator
