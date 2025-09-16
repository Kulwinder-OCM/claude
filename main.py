#!/usr/bin/env python3
"""
Claude Life - Brand Analysis and Social Media Campaign Generator

A complete Python implementation that replaces the text-based agents with 
executable Python code that makes real API calls.
"""

import sys
from pathlib import Path

# Add src to path so we can import our modules
sys.path.append(str(Path(__file__).parent / "src"))

from orchestrator import BrandWorkflowOrchestrator

def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Claude Life - Brand Analysis and Social Media Campaign Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py https://example.com                    # Run complete workflow
  python main.py https://example.com --agent screenshot # Run only screenshot analysis
  python main.py https://example.com --agent business   # Run only business intelligence
  python main.py https://example.com --agent content    # Run only social content creation
  python main.py https://example.com --agent prompts    # Run only Instagram prompts
  python main.py https://example.com --agent images     # Run only image generation

Available agents:
  screenshot  - Capture and analyze website screenshots
  business    - Gather comprehensive business intelligence
  content     - Create social media content strategy
  prompts     - Generate Instagram image prompts
  images      - Generate actual Instagram images
  complete    - Run all agents in sequence (default)
        """
    )
    
    parser.add_argument("url", help="Website URL to analyze")
    parser.add_argument("--agent", 
                       choices=["screenshot", "business", "content", "prompts", "images", "complete"],
                       default="complete", 
                       help="Which agent to run (default: complete workflow)")
    parser.add_argument("--verbose", "-v", action="store_true", 
                       help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Set up logging level
    if args.verbose:
        import logging
        logging.basicConfig(level=logging.DEBUG)
    
    print("🚀 Claude Life - Brand Analysis & Social Media Campaign Generator")
    print(f"📊 Analyzing: {args.url}")
    print(f"🔧 Mode: {args.agent}")
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
            
            if results["workflow_status"] == "completed":
                print(f"\n🎉 Complete brand campaign generated successfully!")
                print(f"📁 Check the 'metrics/' directory for all generated files")
        else:
            results = orchestrator.run_single_agent(args.agent, args.url)
            
            if "error" not in results:
                print(f"\n✅ {args.agent} agent completed successfully!")
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