"""Main orchestrator for running the complete brand workflow."""

import logging
from typing import Dict, Any
from pathlib import Path

from agents.base_agent import BaseAgent
from agents.business_intelligence_analyzer import BusinessIntelligenceAnalyzer
from agents.screenshot_analyzer import ScreenshotAnalyzer
from agents.social_content_creator import SocialContentCreator
from agents.instagram_prompt_generator import InstagramPromptGenerator
from agents.brand_image_generator import BrandImageGenerator

class BrandWorkflowOrchestrator(BaseAgent):
    """Orchestrates the complete brand analysis and content creation workflow."""

    def __init__(self):
        super().__init__("brand_workflow_orchestrator", "metrics")

        # Initialize all agents
        self.business_analyzer = BusinessIntelligenceAnalyzer()
        self.screenshot_analyzer = ScreenshotAnalyzer()
        self.content_creator = SocialContentCreator()
        self.prompt_generator = InstagramPromptGenerator()
        self.image_generator = BrandImageGenerator()

    def run_complete_workflow(self, url: str) -> Dict[str, Any]:
        """
        Run the complete brand workflow in sequential order.

        Workflow Steps:
        1. Business Intelligence Analysis (URL → business intel JSON)
        2. Design Style Analysis (URL → design analysis JSON)
        3. Social Content Strategy (business intel JSON → social content JSON)
        4. Instagram Prompt Generation (design + social JSON → prompts JSON)
        5. Brand Image Generation (prompts JSON → PNG images)

        Args:
            url: Website URL to analyze

        Returns:
            Complete workflow results with all phases
        """
        self.logger.info(f"Starting complete brand workflow for {url}")

        workflow_results = {
            "url": url,
            "workflow_status": "in_progress",
            "phases": {}
        }

        try:
            # Phase 1: Business Intelligence Analysis
            self.logger.info("Phase 1: Business intelligence analysis")
            business_intel = self.business_analyzer.process(url)
            workflow_results["phases"]["business_intelligence"] = {
                "status": "completed",
                "data": business_intel
            }

            # Phase 2: Screenshot & Design Analysis
            self.logger.info("Phase 2: Design style analysis")
            design_analysis = self.screenshot_analyzer.process(url)
            workflow_results["phases"]["design_analysis"] = {
                "status": "completed",
                "data": design_analysis
            }

            # Phase 3: Social Content Creation
            self.logger.info("Phase 3: Social media content creation")
            social_content = self.content_creator.process(
                url,
                business_intel=business_intel,
                design_analysis=design_analysis
            )
            workflow_results["phases"]["social_content"] = {
                "status": "completed",
                "data": social_content
            }

            # Phase 4: Instagram Prompt Generation
            self.logger.info("Phase 4: Instagram prompt generation")
            instagram_prompts = self.prompt_generator.process(
                url,
                social_content=social_content
            )
            workflow_results["phases"]["instagram_prompts"] = {
                "status": "completed",
                "data": instagram_prompts
            }

            # Phase 5: Brand Image Generation
            self.logger.info("Phase 5: Brand image generation")
            brand_images = self.image_generator.process(
                url,
                prompts_data=instagram_prompts
            )
            workflow_results["phases"]["brand_images"] = {
                "status": "completed",
                "data": brand_images
            }

            # Mark workflow as completed
            workflow_results["workflow_status"] = "completed"
            self.logger.info(f"Complete workflow finished successfully for {url}")

        except Exception as e:
            workflow_results["workflow_status"] = "failed"
            workflow_results["error"] = str(e)
            self.logger.error(f"Workflow failed for {url}: {e}")

        return workflow_results

    def process(self, url: str, **kwargs) -> Dict[str, Any]:
        """
        Process URL using the complete workflow (required by BaseAgent).

        Args:
            url: Website URL to analyze
            **kwargs: Additional arguments

        Returns:
            Complete workflow results
        """
        return self.run_complete_workflow(url)

    def get_output_filename(self, domain: str) -> str:
        """Generate output filename for workflow orchestrator (required by BaseAgent)."""
        return f"{domain}-workflow-results-{self.get_timestamp()}.json"

    def run_single_agent(self, agent_name: str, url: str) -> Dict[str, Any]:
        """
        Run a single agent instead of the complete workflow.
        
        Args:
            agent_name: Name of the agent to run
            url: Website URL to analyze
            
        Returns:
            Results from the specified agent
        """
        self.logger.info(f"Running single agent: {agent_name} for {url}")
        
        try:
            if agent_name == "business":
                return self.business_analyzer.process(url)
            elif agent_name == "founders":
                # Extract only founder details
                return self.business_analyzer.extract_founders_only(url)
            elif agent_name == "screenshot":
                return self.screenshot_analyzer.process(url)
            elif agent_name == "content":
                # Content creator needs business intel and design analysis
                business_intel = self.business_analyzer.process(url)
                design_analysis = self.screenshot_analyzer.process(url)
                return self.content_creator.process(url, business_intel=business_intel, design_analysis=design_analysis)
            elif agent_name == "prompts":
                # Prompt generator needs social content
                business_intel = self.business_analyzer.process(url)
                design_analysis = self.screenshot_analyzer.process(url)
                social_content = self.content_creator.process(url, business_intel=business_intel, design_analysis=design_analysis)
                return self.prompt_generator.process(url, social_content=social_content)
            elif agent_name == "images":
                # Image generator needs prompts
                business_intel = self.business_analyzer.process(url)
                design_analysis = self.screenshot_analyzer.process(url)
                social_content = self.content_creator.process(url, business_intel=business_intel, design_analysis=design_analysis)
                instagram_prompts = self.prompt_generator.process(url, social_content=social_content)
                return self.image_generator.process(url, prompts_data=instagram_prompts)
            else:
                raise ValueError(f"Unknown agent: {agent_name}")
                
        except Exception as e:
            self.logger.error(f"Error running {agent_name} agent: {e}")
            return {"error": str(e)}


def main():
    """Main entry point for CLI usage."""
    import argparse

    parser = argparse.ArgumentParser(description="Brand Workflow Orchestrator")
    parser.add_argument("url", help="Website URL to analyze")
    args = parser.parse_args()

    orchestrator = BrandWorkflowOrchestrator()
    results = orchestrator.run_complete_workflow(args.url)

    # Print summary
    print(f"\n=== Results for {args.url} ===")
    print(f"Workflow Status: {results['workflow_status']}")
    for phase, data in results["phases"].items():
        print(f"  {phase}: {data['status']}")

    print(f"\nDetailed results saved to metrics/ directory")


if __name__ == "__main__":
    main()