# AI Providers Guide

Claude Life now supports multiple AI providers with flexible configuration. Switch between Claude, OpenAI, and Gemini for different tasks.

## 🤖 Supported AI Providers

### Claude (Anthropic) 
- **Capabilities**: Text analysis, web analysis, content strategy
- **Strengths**: Excellent reasoning, long context, business analysis
- **API Key**: Get from [Anthropic Console](https://console.anthropic.com/)
- **Models**: claude-3-5-sonnet-20241022 (default), claude-3-haiku, claude-3-opus

### OpenAI
- **Capabilities**: Text analysis, image generation, content strategy  
- **Strengths**: DALL-E for images, GPT-4 for analysis
- **API Key**: Get from [OpenAI Platform](https://platform.openai.com/api-keys)
- **Models**: gpt-4 (default), gpt-3.5-turbo, dall-e-3

### Gemini (Google)
- **Capabilities**: Text analysis, text generation, image generation
- **Strengths**: Fast, multilingual, cost-effective
- **API Key**: Get from [Google AI Studio](https://makersuite.google.com/app/apikey)
- **Models**: gemini-2.0-flash (default), gemini-pro

## ⚙️ Configuration

### Environment Variables

Add to your `.env` file:

```bash
# API Keys
CLAUDE_API_KEY=your_claude_api_key_here
OPENAI_API_KEY=your_openai_api_key_here  
GEMINI_API_KEY=your_gemini_api_key_here

# Provider Preferences (optional)
AI_TEXT_ANALYSIS_PROVIDER=claude
AI_WEB_ANALYSIS_PROVIDER=claude  
AI_CONTENT_STRATEGY_PROVIDER=claude
AI_IMAGE_GENERATION_PROVIDER=openai
```

### Default Provider Assignment

| Capability | Default Provider | Alternatives |
|------------|------------------|--------------|
| Business Intelligence | Claude | OpenAI |
| Content Strategy | Claude | OpenAI |
| Text Analysis | Claude | OpenAI, Gemini |
| Image Generation | OpenAI | Gemini |

## 🚀 Usage Examples

### Check Provider Status
```bash
python cli.py --providers
```

### Run with Specific Configuration
```bash
# Use Claude for analysis, OpenAI for images
AI_WEB_ANALYSIS_PROVIDER=claude AI_IMAGE_GENERATION_PROVIDER=openai python cli.py https://example.com
```

### Test All Providers
```bash
python cli.py --test-providers
```

## 🔄 Provider Switching

The system automatically:
- **Detects available providers** based on API keys
- **Falls back gracefully** if preferred provider fails  
- **Uses capability-specific defaults** when not configured
- **Maintains consistent output format** across providers

## 📊 Cost Optimization

### Claude
- Best for: Complex business analysis, content strategy
- Cost: Medium, excellent value for analysis tasks

### OpenAI  
- Best for: Image generation (DALL-E), balanced text tasks
- Cost: Medium-High, premium for images

### Gemini
- Best for: High-volume text processing, cost-sensitive tasks
- Cost: Low, excellent for batch processing

## 🛠️ Adding New Providers

To add a new AI provider:

1. Create provider class inheriting from `BaseAIProvider`
2. Implement required capabilities 
3. Register in `AIProviderFactory`
4. Update environment variables

Example:
```python
class CustomProvider(BaseAIProvider):
    def _get_capabilities(self):
        return [AICapability.TEXT_ANALYSIS]
    
    def analyze_text(self, text, prompt, **kwargs):
        # Implementation
        pass
```

## 🔍 Troubleshooting

### Provider Not Available
```
ValueError: Environment variable CLAUDE_API_KEY not set
```
**Solution**: Add the required API key to your `.env` file

### Capability Not Supported
```
NotImplementedError: gemini does not support image analysis
```
**Solution**: The system will automatically fall back to a supported provider

### API Rate Limits
- **Claude**: 50,000 tokens/minute (Tier 1)
- **OpenAI**: Varies by model and tier
- **Gemini**: 60 requests/minute (free tier)

Use provider preferences to distribute load across different services.

## 📈 Performance Comparison

| Provider | Business Analysis | Content Strategy | Image Generation | Speed |
|----------|-------------------|------------------|------------------|--------|
| Claude   | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ❌ | Medium |
| OpenAI   | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Medium |
| Gemini   | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | Fast |

Choose providers based on your specific needs for quality, cost, and speed.