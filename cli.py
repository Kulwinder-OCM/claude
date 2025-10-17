#!/usr/bin/env python3
"""
Claude Life CLI - Command line interface with AI provider management
"""

import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from brand_workflow_orchestrator import BrandWorkflowOrchestrator
from ai_providers.ai_factory import AIProviderFactory
from config import config

def show_provider_status():
    """Show available AI providers and their status."""
    print("\n🤖 AI Provider Status:")
    print("-" * 40)
    
    available_providers = AIProviderFactory.list_available_providers()
    configured_providers = config.get_available_providers()
    
    for provider, status in available_providers.items():
        if status.get("available"):
            configured = "✅" if configured_providers.get(provider, False) else "❌"
            print(f"  {configured} {provider.upper()}: {status.get('model', 'N/A')}")
            if status.get("capabilities"):
                print(f"    Capabilities: {', '.join(status['capabilities'])}")
        else:
            print(f"  ❌ {provider.upper()}: {status.get('error', 'Not configured')}")
    
    print(f"\n📋 Current Configuration:")
    ai_prefs = config.ai_providers
    for capability, provider in ai_prefs.items():
        status = "✅" if configured_providers.get(provider, False) else "❌"
        print(f"  {status} {capability}: {provider}")

def main():
    """Enhanced main entry point with provider management."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Claude Life - Multi-AI Brand Analysis & Social Media Campaign Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py https://example.com                     # Run complete workflow
  python cli.py https://example.com --agent screenshot  # Run only screenshot analysis
  python cli.py --providers                            # Show AI provider status
  python cli.py --test-providers                       # Test all configured providers

Available agents:
  screenshot  - Capture and analyze website screenshots
  business    - AI-powered comprehensive business intelligence
  founders    - Extract detailed founder and leadership information only
  content     - AI-generated social media content strategy  
  prompts     - Generate Instagram image prompts
  images      - Generate actual Instagram images with AI
  complete    - Run all agents in sequence (default)

AI Provider Configuration:
  Set environment variables to choose providers:
  - AI_TEXT_ANALYSIS_PROVIDER (claude|openai|gemini)
  - AI_TEXT_GENERATION_PROVIDER (claude|openai|gemini)
  - AI_WEB_ANALYSIS_PROVIDER (claude|openai)
  - AI_CONTENT_STRATEGY_PROVIDER (claude|openai)
  
  Note: Image generation always uses Gemini for optimal quality
        """
    )
    
    parser.add_argument("url", nargs="?", help="Website URL to analyze")
    parser.add_argument("--agent", 
                       choices=["screenshot", "business", "founders", "content", "prompts", "images", "complete"],
                       default="complete", 
                       help="Which agent to run (default: complete workflow)")
    parser.add_argument("--verbose", "-v", action="store_true", 
                       help="Enable verbose logging")
    parser.add_argument("--providers", action="store_true",
                       help="Show AI provider status and configuration")
    parser.add_argument("--test-providers", action="store_true", 
                       help="Test all configured AI providers")
    
    args = parser.parse_args()
    
    # Handle provider status/test commands
    if args.providers:
        show_provider_status()
        return
    
    if args.test_providers:
        print("🧪 Testing AI Providers...")
        show_provider_status()
        # Add provider testing logic here
        return
    
    # Require URL for analysis commands
    if not args.url:
        print("❌ Error: URL is required for analysis")
        parser.print_help()
        return
    
    # Set up logging level
    if args.verbose:
        import logging
        logging.basicConfig(level=logging.DEBUG)
    
    print("🚀 Claude Life - Multi-AI Brand Analysis & Social Media Campaign Generator")
    print(f"📊 Analyzing: {args.url}")
    print(f"🔧 Mode: {args.agent}")
    print(f"🤖 AI Providers: {', '.join(k for k, v in config.get_available_providers().items() if v)}")
    print("-" * 60)
    
    try:
        orchestrator = BrandWorkflowOrchestrator()
        
        if args.agent == "complete":
            results = orchestrator.run_complete_workflow(args.url)
            
            print(f"\n✅ Workflow Status: {results['workflow_status']}")
            print("\n📋 Phase Results:")
            for phase, data in results["phases"].items():
                status_icon = "✅" if data["status"] == "completed" else "❌"
                print(f"  {status_icon} {phase}: {data['status']}")
                
                # Show AI provider used if available
                if "data" in data and isinstance(data["data"], dict):
                    ai_provider = data["data"].get("ai_provider")
                    ai_model = data["data"].get("ai_model")
                    if ai_provider:
                        print(f"    🤖 AI: {ai_provider} ({ai_model})")
            
            if results["workflow_status"] == "completed":
                print(f"\n🎉 Complete AI-powered brand campaign generated successfully!")
                print(f"📁 Check the 'metrics/' directory for all generated files")
        else:
            results = orchestrator.run_single_agent(args.agent, args.url)
            
            if "error" not in results:
                print(f"\n✅ {args.agent} agent completed successfully!")
                ai_provider = results.get("ai_provider")
                if ai_provider:
                    print(f"🤖 Powered by: {ai_provider}")
            else:
                print(f"\n❌ {args.agent} agent failed: {results['error']}")
    
    except KeyboardInterrupt:
        print("\n\n⏹️  Process interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()