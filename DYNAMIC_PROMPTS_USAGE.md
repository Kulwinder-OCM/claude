# Dynamic Prompts Usage Guide

This guide explains how to use the refactored AI agents with dynamic prompts loaded from markdown files.

## Overview

All AI agents in the Claude Life system have been refactored to support dynamic prompt loading from markdown files located in `.claude/agents/`. This allows you to customize AI instructions without modifying the Python code.

## Available Agents with Dynamic Prompt Support

### 1. Brand Workflow Orchestrator
**File**: `src/brand_workflow_orchestrator.py`
**Prompt File**: `.claude/agents/brand_workflow_orchestrator.md`

```python
from src.brand_workflow_orchestrator import BrandWorkflowOrchestrator

orchestrator = BrandWorkflowOrchestrator()

# Run complete workflow with default prompts
result = orchestrator.run_complete_workflow("https://example.com")

# Run complete workflow with custom prompts for individual agents
custom_prompts = {
    "business": "custom-business-analyzer",
    "screenshot": "custom-screenshot-analyzer",
    "social": "custom-social-creator",
    "instagram": "custom-instagram-generator"
}
result = orchestrator.run_complete_workflow("https://example.com", custom_prompts=custom_prompts)

# Run single agent with custom prompt
result = orchestrator.run_single_agent("business", "https://example.com", prompt_file="custom-business-analyzer")

# Use as BaseAgent (supports process method)
result = orchestrator.process("https://example.com", custom_prompts=custom_prompts)
```

**CLI Usage with Dynamic Prompts:**
```bash
# Complete workflow with default prompts
python src/brand_workflow_orchestrator.py https://example.com

# Complete workflow with custom prompts
python src/brand_workflow_orchestrator.py https://example.com \
  --business-prompt custom-business-analyzer \
  --screenshot-prompt custom-screenshot-analyzer

# Single agent with custom prompt
python src/brand_workflow_orchestrator.py https://example.com \
  --agent business --prompt-file custom-business-analyzer
```

### 2. Business Intelligence Analyzer
**File**: `src/agents/business_intelligence_analyzer.py`
**Prompt File**: `.claude/agents/business-intelligence-analyzer.md`

```python
from src.agents.business_intelligence_analyzer import BusinessIntelligenceAnalyzer

# Use default prompts (fallback to hardcoded)
analyzer = BusinessIntelligenceAnalyzer()
result = analyzer.process("https://example.com")

# Use custom prompt file
result = analyzer.process("https://example.com", prompt_file="business-intelligence-analyzer")

# Use different agent's prompts
result = analyzer.process("https://example.com", prompt_file="custom-business-analyzer")
```

### 2. Screenshot Analyzer
**File**: `src/agents/screenshot_analyzer.py`
**Prompt File**: `.claude/agents/screenshot-analyzer.md`

```python
from src.agents.screenshot_analyzer import ScreenshotAnalyzer

analyzer = ScreenshotAnalyzer()

# Use default prompts
result = analyzer.process("https://example.com")

# Use custom prompt file
result = analyzer.process("https://example.com", prompt_file="screenshot-analyzer")
```

### 3. Social Media Content Creator
**File**: `src/agents/social_content_creator.py`
**Prompt File**: `.claude/agents/social-media-content-creator.md`

```python
from src.agents.social_content_creator import SocialContentCreator

creator = SocialContentCreator()
result = creator.process(
    "https://example.com",
    business_intel=business_data,
    design_analysis=design_data,
    prompt_file="social-media-content-creator"
)
```

### 4. Instagram Prompt Generator
**File**: `src/agents/instagram_prompt_generator.py`
**Prompt File**: `.claude/agents/instagram-prompt-generator.md`

```python
from src.agents.instagram_prompt_generator import InstagramPromptGenerator

generator = InstagramPromptGenerator()
result = generator.process(
    "https://example.com",
    social_content=social_data,
    prompt_file="instagram-prompt-generator"
)
```

### 5. Claude Provider (AI Backend)
**File**: `src/ai_providers/claude_provider.py`
**Prompt Files**: Various agent markdown files

```python
from src.ai_providers.claude_provider import ClaudeProvider

provider = ClaudeProvider()

# Website analysis with dynamic prompts
result = provider.analyze_website(
    html_content,
    url,
    agent_name="business-intelligence-analyzer"
)

# Content strategy with dynamic prompts
result = provider.create_content_strategy(
    business_data,
    design_data,
    agent_name="social-media-content-creator"
)
```

## Helper Function Usage

The `load_prompt_from_md()` function is available in the `BaseAgent` class:

```python
from src.agents.base_agent import BaseAgent

# In any agent class
prompt_content = self.load_prompt_from_md("business-intelligence-analyzer")
if prompt_content:
    # Use dynamic prompt
    system_prompt = prompt_content
else:
    # Fall back to hardcoded prompt
    system_prompt = "Default hardcoded prompt..."
```

## Creating Custom Prompt Files

1. **Create a new markdown file** in `.claude/agents/`:
   ```
   .claude/agents/my-custom-agent.md
   ```

2. **Optional YAML front matter**:
   ```yaml
   ---
   name: my-custom-agent
   description: Custom agent description
   model: sonnet
   color: blue
   ---
   ```

3. **Prompt content** (everything after the YAML front matter):
   ```markdown
   You are a specialized AI agent for custom tasks.

   Your instructions here...
   ```

4. **Use the custom prompt**:
   ```python
   result = agent.process(url, prompt_file="my-custom-agent")
   ```

## Template Variables for Instagram Prompts

The `InstagramPromptGenerator` supports template variable substitution in markdown files:

Available variables:
- `{company_name}` - Company name
- `{headline}` - Post headline
- `{subtext}` - Post subtext
- `{call_to_action}` - Call to action text
- `{background_color}` - Background color hex
- `{brand_primary}` - Primary brand color hex
- `{text_primary}` - Primary text color hex
- `{text_secondary}` - Secondary text color hex
- `{font_classification}` - Font classification
- `{visual_focus}` - Visual focus description
- `{target_emotion}` - Target emotion
- `{content_type}` - Content type

Example template in `.claude/agents/instagram-prompt-generator.md`:
```markdown
Create a professional Instagram post for {company_name}:

LAYOUT:
- Background: {background_color}
- Primary Brand Color: {brand_primary}

CONTENT:
- Headline: "{headline}"
- Subtext: "{subtext}"
- Call to Action: "{call_to_action}"

TARGET:
- Emotion: {target_emotion}
- Type: {content_type}
```

## Error Handling

All agents include fallback behavior:

1. **If markdown file doesn't exist**: Uses hardcoded prompt
2. **If markdown file is malformed**: Uses hardcoded prompt
3. **If template variables fail**: Uses hardcoded prompt

## File Structure

```
project/
├── .claude/
│   └── agents/
│       ├── business-intelligence-analyzer.md
│       ├── screenshot-analyzer.md
│       ├── social-media-content-creator.md
│       ├── instagram-prompt-generator.md
│       ├── brand_image_generator.md
│       └── brand_workflow_orchestrator.md
└── src/
    ├── agents/
    │   ├── base_agent.py (contains load_prompt_from_md())
    │   ├── business_intelligence_analyzer.py
    │   ├── screenshot_analyzer.py
    │   ├── social_content_creator.py
    │   └── instagram_prompt_generator.py
    └── ai_providers/
        └── claude_provider.py
```

## Benefits

1. **No code changes needed** to update AI instructions
2. **Version control friendly** - prompts are in markdown files
3. **Easy A/B testing** - swap prompt files without restarting
4. **Fallback safety** - original hardcoded prompts remain as backup
5. **Template support** - dynamic variable substitution for prompts

## Complete Example Workflows

### Option 1: Using Individual Agents

```python
# Initialize agents
business_analyzer = BusinessIntelligenceAnalyzer()
screenshot_analyzer = ScreenshotAnalyzer()
content_creator = SocialContentCreator()
prompt_generator = InstagramPromptGenerator()

# Run complete pipeline with custom prompts
url = "https://example.com"

# Step 1: Business intelligence with custom prompt
business_intel = business_analyzer.process(
    url,
    prompt_file="business-intelligence-analyzer"
)

# Step 2: Screenshot analysis with custom prompt
design_analysis = screenshot_analyzer.process(
    url,
    prompt_file="screenshot-analyzer"
)

# Step 3: Social content with custom prompt
social_content = content_creator.process(
    url,
    business_intel=business_intel,
    design_analysis=design_analysis,
    prompt_file="social-media-content-creator"
)

# Step 4: Instagram prompts with custom template
instagram_prompts = prompt_generator.process(
    url,
    social_content=social_content,
    prompt_file="instagram-prompt-generator"
)

print("All agents completed with dynamic prompts!")
```

### Option 2: Using Workflow Orchestrator (Recommended)

```python
from src.brand_workflow_orchestrator import BrandWorkflowOrchestrator

orchestrator = BrandWorkflowOrchestrator()

# Complete workflow with all custom prompts
custom_prompts = {
    "business": "business-intelligence-analyzer",
    "screenshot": "screenshot-analyzer",
    "social": "social-media-content-creator",
    "instagram": "instagram-prompt-generator"
}

result = orchestrator.run_complete_workflow(
    "https://example.com",
    custom_prompts=custom_prompts
)

# Check results
print(f"Workflow Status: {result['workflow_status']}")
print(f"Instructions Source: {result['workflow_config']['instructions_source']}")

for phase, data in result["phases"].items():
    print(f"{phase}: {data['status']} (using {data['prompt_file']})")
```

### Option 3: CLI Usage

```bash
# Complete workflow with mixed custom prompts
python src/brand_workflow_orchestrator.py https://example.com \
  --business-prompt custom-business-analyzer \
  --social-prompt enhanced-social-creator

# Single agent with custom prompt
python src/brand_workflow_orchestrator.py https://example.com \
  --agent screenshot --prompt-file custom-screenshot-analyzer
```