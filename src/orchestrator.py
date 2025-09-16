"""Main orchestrator for running the complete brand workflow."""

import logging
from typing import Dict, Any
from pathlib import Path

from agents.screenshot_analyzer import ScreenshotAnalyzer
from agents.business_intelligence_analyzer import BusinessIntelligenceAnalyzer
from agents.social_content_creator import SocialContentCreator
from agents.instagram_prompt_generator import InstagramPromptGenerator
from agents.brand_image_generator import BrandImageGenerator

class BrandWorkflowOrchestrator:
    """Orchestrates the complete brand analysis and content creation workflow."""
    
    def __init__(self):
        self.logger = self._setup_logger()
        
        # Initialize agents
        self.screenshot_analyzer = ScreenshotAnalyzer()
        self.business_analyzer = BusinessIntelligenceAnalyzer()
        self.content_creator = SocialContentCreator()
        self.prompt_generator = InstagramPromptGenerator()
        self.image_generator = BrandImageGenerator()
    
    def _setup_logger(self) -> logging.Logger:
        """Set up logging for the orchestrator."""
        logger = logging.getLogger("brand-workflow-orchestrator")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def run_complete_workflow(self, url: str) -> Dict[str, Any]:
        """Run the complete brand analysis and content creation workflow."""
        
        self.logger.info(f"Starting complete brand workflow for {url}")
        
        workflow_results = {
            "url": url,
            "workflow_status": "in_progress",
            "phases": {}
        }
        
        try:
            # Phase 1: Business Intelligence Analysis
            self.logger.info("Phase 1: Running business intelligence analysis")
            business_intel = self.business_analyzer.process(url)
            workflow_results["phases"]["business_intelligence"] = {
                "status": "completed" if "error" not in business_intel else "failed",
                "data": business_intel
            }
            
            # Phase 2: Screenshot & Design Analysis
            self.logger.info("Phase 2: Running design analysis")
            design_analysis = self.screenshot_analyzer.process(url)
            workflow_results["phases"]["design_analysis"] = {
                "status": "completed" if "error" not in design_analysis else "failed",
                "data": design_analysis
            }
            
            # Phase 3: Social Content Creation
            self.logger.info("Phase 3: Creating social media content")
            social_content = self.content_creator.process(
                url, 
                business_intel=business_intel,
                design_analysis=design_analysis
            )
            workflow_results["phases"]["social_content"] = {
                "status": "completed" if "error" not in social_content else "failed",
                "data": social_content
            }
            
            # Phase 4: Instagram Prompt Generation
            self.logger.info("Phase 4: Generating Instagram prompts")
            instagram_prompts = self.prompt_generator.process(
                url,
                social_content=social_content
            )
            workflow_results["phases"]["instagram_prompts"] = {
                "status": "completed" if "error" not in instagram_prompts else "failed",
                "data": instagram_prompts
            }
            
            # Phase 5: Brand Image Generation
            self.logger.info("Phase 5: Generating brand images")
            brand_images = self.image_generator.process(
                url,
                prompts_data=instagram_prompts
            )
            workflow_results["phases"]["brand_images"] = {
                "status": "completed" if "error" not in brand_images else "failed",
                "data": brand_images
            }
            
            # Final status
            failed_phases = [k for k, v in workflow_results["phases"].items() if v["status"] == "failed"]
            
            if not failed_phases:
                workflow_results["workflow_status"] = "completed"
                self.logger.info(f"Complete workflow finished successfully for {url}")
            else:
                workflow_results["workflow_status"] = "completed_with_errors"
                workflow_results["failed_phases"] = failed_phases
                self.logger.warning(f"Workflow completed with errors in phases: {failed_phases}")
            
        except Exception as e:
            workflow_results["workflow_status"] = "failed"
            workflow_results["error"] = str(e)
            self.logger.error(f"Workflow failed for {url}: {e}")
        
        return workflow_results
    
    def run_single_agent(self, agent_name: str, url: str, **kwargs) -> Dict[str, Any]:
        """Run a single agent."""
        
        agents = {
            "screenshot": self.screenshot_analyzer,
            "business": self.business_analyzer,
            "content": self.content_creator,
            "prompts": self.prompt_generator,
            "images": self.image_generator
        }
        
        if agent_name not in agents:
            raise ValueError(f"Unknown agent: {agent_name}. Available: {list(agents.keys())}")
        
        agent = agents[agent_name]
        self.logger.info(f"Running {agent_name} agent for {url}")
        
        return agent.process(url, **kwargs)


def main():
    """Main entry point for CLI usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Claude Life Brand Workflow")
    parser.add_argument("url", help="Website URL to analyze")
    parser.add_argument("--agent", choices=["screenshot", "business", "content", "prompts", "images", "complete"],
                       default="complete", help="Which agent to run (default: complete workflow)")
    
    args = parser.parse_args()
    
    orchestrator = BrandWorkflowOrchestrator()
    
    if args.agent == "complete":
        results = orchestrator.run_complete_workflow(args.url)
    else:
        results = orchestrator.run_single_agent(args.agent, args.url)
    
    # Print summary
    print(f"\n=== Results for {args.url} ===")
    if args.agent == "complete":
        print(f"Workflow Status: {results['workflow_status']}")
        for phase, data in results["phases"].items():
            print(f"  {phase}: {data['status']}")
    else:
        print(f"Agent: {args.agent}")
        print(f"Status: {'success' if 'error' not in results else 'failed'}")
    
    print(f"\nDetailed results saved to metrics/ directory")


if __name__ == "__main__":
    main()