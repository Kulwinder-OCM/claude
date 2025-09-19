"""Main orchestrator for running the complete brand workflow."""

import logging
from typing import Dict, Any, Optional
from pathlib import Path

from agents.base_agent import BaseAgent
from agents.screenshot_analyzer import ScreenshotAnalyzer
from agents.business_intelligence_analyzer import BusinessIntelligenceAnalyzer
from agents.social_content_creator import SocialContentCreator
from agents.instagram_prompt_generator import InstagramPromptGenerator
from agents.brand_image_generator import BrandImageGenerator

class BrandWorkflowOrchestrator(BaseAgent):
    """Orchestrates the complete brand analysis and content creation workflow."""
    
    def __init__(self):
        super().__init__("brand-workflow-orchestrator", "metrics")

        # Load workflow instructions from markdown file
        self.workflow_instructions = self.load_prompt_from_md("brand_workflow_orchestrator")

        # Initialize agents
        self.screenshot_analyzer = ScreenshotAnalyzer()
        self.business_analyzer = BusinessIntelligenceAnalyzer()
        self.content_creator = SocialContentCreator()
        self.prompt_generator = InstagramPromptGenerator()
        self.image_generator = BrandImageGenerator()
    
    def get_workflow_config(self) -> Dict[str, Any]:
        """
        Get workflow configuration from loaded instructions.

        Returns:
            Configuration dictionary with workflow settings
        """
        if not self.workflow_instructions:
            return self._get_default_workflow_config()

        # Parse markdown content to extract configuration
        # For now, return default config but with indication it was loaded
        config = self._get_default_workflow_config()
        config["instructions_source"] = "brand_workflow_orchestrator.md"
        config["instructions_loaded"] = True
        config["raw_instructions"] = self.workflow_instructions[:200] + "..." if len(self.workflow_instructions) > 200 else self.workflow_instructions

        return config

    def _get_default_workflow_config(self) -> Dict[str, Any]:
        """Get default workflow configuration."""
        return {
            "instructions_source": "hardcoded",
            "instructions_loaded": False,
            "phases": [
                "business_intelligence",
                "design_analysis",
                "social_content",
                "instagram_prompts",
                "brand_images"
            ],
            "required_phases": 5,
            "sequential_execution": True,
            "error_handling": "continue_with_errors"
        }
    
    def run_complete_workflow(self, url: str, prompt_file: str = None, custom_prompts: Dict[str, str] = None) -> Dict[str, Any]:
        """
        Run the complete brand analysis and content creation workflow using dynamic instructions.

        Args:
            url: Website URL to analyze
            prompt_file: Optional agent name for loading workflow instructions (defaults to 'brand-workflow-orchestrator')
            custom_prompts: Optional dictionary of custom prompt files for individual agents
                          e.g., {"business": "custom-business-analyzer", "screenshot": "custom-screenshot-analyzer"}

        Returns:
            Complete workflow results with phase-by-phase status
        """

        # Load workflow configuration
        config = self.get_workflow_config()

        self.logger.info(f"Starting complete brand workflow for {url}")
        self.logger.info(f"Using instructions from: {config['instructions_source']}")

        workflow_results = {
            "url": url,
            "workflow_status": "in_progress",
            "workflow_config": config,
            "phases": {}
        }

        try:
            # Get custom prompt file names or use defaults
            custom_prompts = custom_prompts or {}

            # Phase 1: Business Intelligence Analysis
            self.logger.info("Phase 1: Running business intelligence analysis")
            business_prompt = custom_prompts.get("business", "business-intelligence-analyzer")
            business_intel = self.business_analyzer.process(url, prompt_file=business_prompt)
            workflow_results["phases"]["business_intelligence"] = {
                "status": "completed" if "error" not in business_intel else "failed",
                "prompt_file": business_prompt,
                "data": business_intel
            }

            # Phase 2: Screenshot & Design Analysis
            self.logger.info("Phase 2: Running design analysis")
            screenshot_prompt = custom_prompts.get("screenshot", "screenshot-analyzer")
            design_analysis = self.screenshot_analyzer.process(url, prompt_file=screenshot_prompt)
            workflow_results["phases"]["design_analysis"] = {
                "status": "completed" if "error" not in design_analysis else "failed",
                "prompt_file": screenshot_prompt,
                "data": design_analysis
            }

            # Phase 3: Social Content Creation
            self.logger.info("Phase 3: Creating social media content")
            social_prompt = custom_prompts.get("social", "social-media-content-creator")
            social_content = self.content_creator.process(
                url,
                business_intel=business_intel,
                design_analysis=design_analysis,
                prompt_file=social_prompt
            )
            workflow_results["phases"]["social_content"] = {
                "status": "completed" if "error" not in social_content else "failed",
                "prompt_file": social_prompt,
                "data": social_content
            }

            # Phase 4: Instagram Prompt Generation
            self.logger.info("Phase 4: Generating Instagram prompts")
            instagram_prompt = custom_prompts.get("instagram", "instagram-prompt-generator")
            instagram_prompts = self.prompt_generator.process(
                url,
                social_content=social_content,
                prompt_file=instagram_prompt
            )
            workflow_results["phases"]["instagram_prompts"] = {
                "status": "completed" if "error" not in instagram_prompts else "failed",
                "prompt_file": instagram_prompt,
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
                "prompt_file": "N/A (uses pre-generated prompts)",
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
    
    def run_single_agent(self, agent_name: str, url: str, prompt_file: str = None, **kwargs) -> Dict[str, Any]:
        """
        Run a single agent with optional custom prompts.

        Args:
            agent_name: Name of the agent to run
            url: Website URL to analyze
            prompt_file: Optional custom prompt file for the agent
            **kwargs: Additional arguments passed to the agent

        Returns:
            Agent execution results
        """

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

        # Add prompt_file to kwargs if provided
        if prompt_file:
            kwargs["prompt_file"] = prompt_file

        return agent.process(url, **kwargs)

    def process(self, url: str, **kwargs) -> Dict[str, Any]:
        """
        Process URL using the complete workflow (required by BaseAgent).

        Args:
            url: Website URL to analyze
            **kwargs: Additional arguments including prompt_file and custom_prompts

        Returns:
            Complete workflow results
        """
        return self.run_complete_workflow(url, **kwargs)

    def get_output_filename(self, domain: str) -> str:
        """Generate output filename for workflow orchestrator (required by BaseAgent)."""
        return f"{domain}-workflow-results-{self.get_timestamp()}.json"


def main():
    """Main entry point for CLI usage."""
    import argparse

    parser = argparse.ArgumentParser(description="Claude Life Brand Workflow with Dynamic Prompts")
    parser.add_argument("url", help="Website URL to analyze")
    parser.add_argument("--agent", choices=["screenshot", "business", "content", "prompts", "images", "complete"],
                       default="complete", help="Which agent to run (default: complete workflow)")
    parser.add_argument("--prompt-file", help="Custom prompt file name for single agents")
    parser.add_argument("--business-prompt", help="Custom prompt file for business intelligence agent")
    parser.add_argument("--screenshot-prompt", help="Custom prompt file for screenshot analyzer")
    parser.add_argument("--social-prompt", help="Custom prompt file for social content creator")
    parser.add_argument("--instagram-prompt", help="Custom prompt file for Instagram prompt generator")

    args = parser.parse_args()

    orchestrator = BrandWorkflowOrchestrator()

    if args.agent == "complete":
        # Build custom prompts dictionary
        custom_prompts = {}
        if args.business_prompt:
            custom_prompts["business"] = args.business_prompt
        if args.screenshot_prompt:
            custom_prompts["screenshot"] = args.screenshot_prompt
        if args.social_prompt:
            custom_prompts["social"] = args.social_prompt
        if args.instagram_prompt:
            custom_prompts["instagram"] = args.instagram_prompt

        results = orchestrator.run_complete_workflow(args.url, custom_prompts=custom_prompts)
    else:
        results = orchestrator.run_single_agent(args.agent, args.url, prompt_file=args.prompt_file)

    # Print summary
    print(f"\n=== Results for {args.url} ===")
    if args.agent == "complete":
        print(f"Workflow Status: {results['workflow_status']}")
        print(f"Instructions Source: {results['workflow_config']['instructions_source']}")
        for phase, data in results["phases"].items():
            prompt_info = f" (using {data['prompt_file']})" if 'prompt_file' in data else ""
            print(f"  {phase}: {data['status']}{prompt_info}")
    else:
        print(f"Agent: {args.agent}")
        print(f"Status: {'success' if 'error' not in results else 'failed'}")
        if args.prompt_file:
            print(f"Custom Prompt File: {args.prompt_file}")

    print(f"\nDetailed results saved to metrics/ directory")


if __name__ == "__main__":
    main()