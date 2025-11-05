# Brand Analysis & Social Media Content Generation System

## What This Project Does

This is an AI-powered system that analyzes any business website and automatically creates personalized social media content for them. Think of it as a "brand consultant in a box" that can understand a company's style and generate matching Instagram posts, captions, and images.

## The Complete Process (6 Steps)

### 1. **Business Intelligence Analysis** 🔍
- **What it does**: Visits a company's website and learns everything about them
- **What it finds**: 
  - What the company does
  - Their target customers
  - Their brand colors and style
  - Their social media accounts (Facebook, Instagram, etc.)
- **Example**: For a yoga studio, it discovers they focus on mindfulness, use calming colors, and target wellness enthusiasts

### 2. **Design Analysis** 🎨
- **What it does**: Analyzes the website's visual design and branding
- **What it finds**:
  - Brand colors and fonts
  - Design style (modern, classic, playful, etc.)
  - Visual elements and patterns
- **Example**: Discovers the yoga studio uses soft blues, clean fonts, and minimalist design

### 3. **Facebook Content Scraping** 📱
- **What it does**: Automatically scrapes recent Facebook posts from the company's page
- **What it finds**:
  - Recent posts and captions
  - Hashtags they use
  - Their writing style and tone
  - What language they post in
- **Example**: Finds 5 recent posts about meditation, wellness tips, and class schedules

### 4. **Social Content Creation** ✍️
- **What it does**: Creates new Instagram captions and hashtags based on the Facebook analysis
- **What it generates**:
  - 3 Instagram post ideas with captions
  - Relevant hashtags
  - Content that matches their existing style and language
- **Example**: Creates captions about "Finding inner peace through Zentangle art" in French (if that's their language)

### 5. **Instagram Prompt Generation** 🤖
- **What it does**: Creates detailed AI prompts for generating Instagram images
- **What it generates**:
  - Detailed descriptions for each post
  - Specific text overlays for the images
  - Style instructions (colors, mood, composition)
- **Example**: "Create a 1080x1080 image with soft blue background, hand drawing Zentangle patterns, with text 'Un trait après l'autre' in elegant font"

### 6. **Brand Image Generation** 🖼️
- **What it does**: Creates actual Instagram-ready images with text overlays
- **What it generates**:
  - 3 professional-looking images
  - Text properly overlaid on each image
  - Images that match the brand's style and colors
- **Example**: Generates 3 images with French text about Zentangle art, using the company's brand colors

## Key Features

### 🌍 **Multi-Language Support**
- Automatically detects what language the company posts in
- Generates all content in the same language
- Works with French, Danish, English, and more

### 🎯 **Brand-Accurate Content**
- Analyzes existing social media to match tone and style
- Uses the company's actual colors and fonts
- Creates content that feels authentic to the brand

### 🚀 **Fully Automated**
- Just provide a website URL
- Everything else happens automatically
- No manual content creation needed

### 📊 **Comprehensive Analysis**
- Learns from Facebook posts, website design, and business info
- Creates a complete brand profile
- Generates content that truly represents the business

## Real-World Example

**Input**: `https://jijihook.fr/` (French Zentangle art website)

**What the system discovers**:
- Company: Zentangle art therapy and wellness
- Language: French
- Style: Calming, artistic, therapeutic
- Colors: Soft blues and grays
- Facebook posts: About mindfulness, art therapy, personal growth

**What it generates**:
- 3 Instagram captions in French about Zentangle art
- Hashtags like #artthérapie #bienêtre #zen
- 3 images with French text like "Un trait après l'autre" (One stroke after another)
- All content matches their existing style and language

## Technical Architecture

### **AI Agents** (Specialized Workers)
- **Business Intelligence Agent**: Website analysis
- **Design Analyzer**: Visual brand analysis  
- **Facebook Scraper**: Social media data collection
- **Social Content Creator**: Caption and hashtag generation
- **Instagram Prompt Generator**: Image description creation
- **Brand Image Generator**: Actual image creation

### **AI Providers**
- **Claude AI**: For content strategy and prompt generation
- **Bright Data API**: For Facebook data scraping
- **PIL (Python Imaging)**: For image generation

### **Web Interface**
- Simple form to enter website URL
- Real-time progress tracking
- Results page showing all generated content
- Click-to-copy hashtags and captions

## Business Value

### **For Marketing Agencies**
- Quickly create brand-accurate content for multiple clients
- Reduce content creation time from hours to minutes
- Ensure consistency across all client content

### **For Small Businesses**
- Get professional social media content without hiring designers
- Maintain consistent brand voice across platforms
- Save time on content creation

### **For Content Creators**
- Generate ideas and inspiration for client work
- Create multiple variations quickly
- Ensure brand consistency

## How to Use

1. **Start the system**: Run `python3 app.py`
2. **Enter website URL**: Paste any business website
3. **Wait for analysis**: System analyzes everything automatically
4. **View results**: See generated captions, hashtags, and images
5. **Download content**: Copy captions and save images for use

## What Makes This Special

- **Truly Brand-Accurate**: Learns from actual social media posts, not just website
- **Language-Aware**: Automatically works in the company's language
- **Complete Solution**: From analysis to final images in one process
- **Scalable**: Can handle any type of business or industry
- **Professional Quality**: Generates content that looks professionally created

This system essentially gives any business the power of a full marketing team and content creation studio, all automated and ready to use in minutes.
