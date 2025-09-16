# Claude Life Web Interface

A beautiful web interface for the Claude Life Multi-AI Brand Analysis & Social Media Campaign Generator.

## Features

✨ **Easy-to-Use Interface**: Simple web form for URL input and AI provider selection
🤖 **Multiple AI Providers**: Choose different AI models for different tasks
📸 **Image Generation**: Always uses Google Gemini for optimal Instagram image quality
⬇️ **Downloadable Results**: View and download generated images directly from the browser
📊 **Real-time Progress**: Watch your analysis progress with live updates
📱 **Mobile-Friendly**: Responsive design works on all devices

## What You Get

- **Business Intelligence**: Comprehensive company analysis
- **Design Analysis**: Brand colors, fonts, and visual style extraction
- **Social Media Strategy**: AI-generated content strategy
- **Instagram Images**: 3 professional, ready-to-post images (1080x1080)
- **Downloadable Assets**: All images available for immediate download

## Quick Start

1. **Set up your API keys** (required):
   ```bash
   export CLAUDE_API_KEY="your_claude_api_key"
   export GEMINI_API_KEY="your_gemini_api_key"
   export OPENAI_API_KEY="your_openai_api_key"  # optional
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Start the web server**:
   ```bash
   ./run_webapp.sh
   ```
   Or manually:
   ```bash
   python app.py
   ```

4. **Open your browser** and go to:
   ```
   http://localhost:5001
   ```

## How to Use

1. **Enter a URL**: Input any website URL you want to analyze
2. **Choose AI Providers**: Select your preferred AI models for different tasks:
   - **Text Analysis**: Claude, OpenAI, or Gemini
   - **Text Generation**: Claude, OpenAI, or Gemini
   - **Web Analysis**: Claude or OpenAI
   - **Content Strategy**: Claude or OpenAI
   - **Image Generation**: Google Gemini (fixed for quality)
3. **Submit**: Click "Generate Brand Campaign"
4. **Watch Progress**: See real-time updates as each phase completes
5. **Download Images**: View and download your generated Instagram images

## AI Provider Configuration

The web interface allows you to choose different AI providers for different tasks:

- **Claude**: Excellent for analysis and strategic content
- **OpenAI**: Great for creative content and analysis
- **Gemini**: Fixed choice for image generation (optimal quality)

**Note**: Image generation always uses Google Gemini regardless of your selection to ensure the best quality Instagram images.

## Generated Files

All analysis results and images are saved in the `metrics/` directory:
- `metrics/companies/` - Business intelligence reports
- `metrics/screenshots/` - Website design analysis
- `metrics/social-content/` - Social media strategies
- `metrics/instagram-prompts/` - Image generation prompts
- `metrics/images/` - Generated Instagram images

## Technical Details

- **Backend**: Flask web framework
- **Frontend**: Bootstrap 5 with custom styling
- **Real-time Updates**: JavaScript polling for progress tracking
- **File Serving**: Secure image download with path validation
- **Background Processing**: Multi-threaded workflow execution

## Troubleshooting

**Port 5000 in use?**
- The app automatically uses port 5001
- Or set a custom port: `python app.py` (modify the port in app.py)

**Missing API keys?**
- Set environment variables before starting
- Check that all required providers have valid API keys

**Images not generating?**
- Ensure GEMINI_API_KEY is set correctly
- Check the logs for specific error messages

## Development

To extend the web interface:
- Templates are in `templates/`
- Static files go in `static/`
- Main Flask app is in `app.py`
- Backend logic uses existing `src/` modules

## Security Notes

- File downloads are restricted to the `metrics/` directory
- Sessions are isolated using unique IDs
- No sensitive data is stored in browser localStorage
- Development server only - use production WSGI for deployment