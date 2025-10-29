"""Facebook scraper agent using Bright Data API."""

import os
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import requests
from pathlib import Path

from agents.base_agent import BaseAgent


class FacebookScraper(BaseAgent):
    """Facebook scraper using Bright Data API to extract posts from Facebook profiles."""

    def __init__(self):
        super().__init__("facebook_scraper", "metrics")
        
        # Bright Data API configuration
        self.api_key = os.getenv("BRIGHT_DATA_API_KEY")
        self.dataset_id = os.getenv("BRIGHT_DATA_DATASET_ID")
        self.base_url = "https://api.brightdata.com/datasets/v3"
        
        if not self.api_key:
            self.logger.warning("BRIGHT_DATA_API_KEY not found in environment variables")
        
        if not self.dataset_id:
            self.logger.warning("BRIGHT_DATA_DATASET_ID not found in environment variables")
    
    def _get_date_range(self) -> tuple[str, str]:
        """Get start and end dates for scraping (2 months ago to today)."""
        today = datetime.now()
        two_months_ago = today - timedelta(days=60)  # Approximately 2 months
        
        # Format dates as YYYY-MM-DD
        end_date = today.strftime("%Y-%m-%d")
        start_date = two_months_ago.strftime("%Y-%m-%d")
        
        return start_date, end_date
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for Bright Data API requests."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def trigger_data_collection(self, facebook_url: str, num_posts: int = 5) -> Optional[str]:
        """
        Step 1: Trigger data collection API.
        
        Args:
            facebook_url: Facebook profile URL
            num_posts: Number of posts to scrape (default: 5)
            
        Returns:
            Snapshot ID if successful, None otherwise
        """
        self.logger.info(f"Triggering data collection for {facebook_url}")
        
        # Get date range (2 months ago to today)
        start_date, end_date = self._get_date_range()
        
        # Use payload format with date range and post limit
        payload = [{
            "url": facebook_url,
            "num_of_posts": num_posts,
            "start_date": start_date,
            "end_date": end_date
        }]
        
        url = f"{self.base_url}/trigger"
        params = {
            "dataset_id": self.dataset_id,
            "include_errors": "true"
        }
        
        try:
            response = requests.post(
                url,
                headers=self._get_headers(),
                json=payload,
                params=params,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            self.logger.info(f"Data collection triggered successfully: {result}")
            
            # Extract snapshot ID from response
            # API can return either a dict with snapshot_id or a list of dicts
            if isinstance(result, dict) and "snapshot_id" in result:
                snapshot_id = result["snapshot_id"]
                self.logger.info(f"Snapshot ID: {snapshot_id}")
                return snapshot_id
            elif isinstance(result, list) and len(result) > 0:
                snapshot_id = result[0].get("snapshot_id")
                if snapshot_id:
                    self.logger.info(f"Snapshot ID: {snapshot_id}")
                    return snapshot_id
            
            self.logger.error("No snapshot ID found in response")
            return None
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to trigger data collection: {e}")
            return None
    
    def monitor_progress(self, snapshot_id: str, max_wait_time: int = 300) -> bool:
        """
        Step 2: Monitor progress of data collection.
        
        Args:
            snapshot_id: Snapshot ID from step 1
            max_wait_time: Maximum time to wait in seconds
            
        Returns:
            True if completed successfully, False otherwise
        """
        self.logger.info(f"Monitoring progress for snapshot {snapshot_id}")
        
        url = f"{self.base_url}/progress/{snapshot_id}"
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            try:
                response = requests.get(url, headers=self._get_headers(), timeout=30)
                response.raise_for_status()
                
                result = response.json()
                self.logger.info(f"Progress status: {result}")
                
                # Check if collection is complete
                status = result.get("status", "").lower()
                if status in ["completed", "done", "finished", "ready"]:
                    self.logger.info("Data collection completed successfully")
                    return True
                elif status in ["failed", "error"]:
                    self.logger.error(f"Data collection failed: {result}")
                    return False
                
                # Wait before next check
                time.sleep(10)
                
            except requests.exceptions.RequestException as e:
                self.logger.error(f"Error monitoring progress: {e}")
                time.sleep(10)
        
        self.logger.error(f"Timeout waiting for data collection to complete")
        return False
    
    def get_delivery_data(self, snapshot_id: str) -> Optional[Dict[str, Any]]:
        """
        Step 3: Get delivery data (scraped posts).
        
        Args:
            snapshot_id: Snapshot ID from step 1
            
        Returns:
            Scraped data if successful, None otherwise
        """
        self.logger.info(f"Retrieving delivery data for snapshot {snapshot_id}")
        
        url = f"{self.base_url}/snapshot/{snapshot_id}"
        params = {"format": "json"}
        
        try:
            response = requests.get(
                url,
                headers=self._get_headers(),
                params=params,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            self.logger.info(f"Successfully retrieved {len(result) if isinstance(result, list) else 'data'} posts")
            
            return result
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to retrieve delivery data: {e}")
            return None
    
    def scrape_facebook_posts(self, facebook_url: str, num_posts: int = 5) -> Dict[str, Any]:
        """
        Complete Facebook scraping process using all 3 steps.
        
        Args:
            facebook_url: Facebook profile URL
            num_posts: Number of posts to scrape
            
        Returns:
            Scraping results with posts data
        """
        self.logger.info(f"Starting Facebook scraping for {facebook_url}")
        
        if not self.api_key:
            return {
                "error": "BRIGHT_DATA_API_KEY not configured",
                "status": "failed"
            }
        
        # Step 1: Trigger data collection
        snapshot_id = self.trigger_data_collection(facebook_url, num_posts)
        if not snapshot_id:
            return {
                "error": "Failed to trigger data collection",
                "status": "failed"
            }
        
        # Step 2: Monitor progress
        if not self.monitor_progress(snapshot_id):
            return {
                "error": "Data collection failed or timed out",
                "status": "failed",
                "snapshot_id": snapshot_id
            }
        
        # Step 3: Get delivery data
        posts_data = self.get_delivery_data(snapshot_id)
        if not posts_data:
            return {
                "error": "Failed to retrieve scraped data",
                "status": "failed",
                "snapshot_id": snapshot_id
            }
        
        # Prepare results
        results = {
            "status": "success",
            "facebook_url": facebook_url,
            "snapshot_id": snapshot_id,
            "num_posts_requested": num_posts,
            "num_posts_retrieved": len(posts_data) if isinstance(posts_data, list) else 1,
            "scraped_at": datetime.now().isoformat(),
            "posts": posts_data
        }
        
        self.logger.info(f"Facebook scraping completed successfully for {facebook_url}")
        return results
    
    def process(self, facebook_url: str, **kwargs) -> Dict[str, Any]:
        """
        Process Facebook URL (required by BaseAgent).
        
        Args:
            facebook_url: Facebook profile URL
            **kwargs: Additional arguments (num_posts, original_url, etc.)
            
        Returns:
            Scraping results
        """
        num_posts = kwargs.get("num_posts", 5)
        original_url = kwargs.get("original_url", facebook_url)  # Use original URL for domain if provided
        results = self.scrape_facebook_posts(facebook_url, num_posts)
        
        # Save results to metrics folder if scraping was successful
        if results.get("status") == "success":
            # Use original URL domain for directory structure, not Facebook URL
            domain = self.sanitize_domain(original_url)
            filename = self.get_output_filename(domain)
            # Save to facebook-posts/{company-name}/ directory structure
            saved_path = self.save_json(results, filename, f"facebook-posts/{domain}")
            results["saved_path"] = saved_path
            self.logger.info(f"Facebook scraping results saved to {saved_path}")
        
        return results
    
    def get_output_filename(self, domain: str) -> str:
        """Generate output filename for Facebook scraper (required by BaseAgent)."""
        return f"{domain}-facebook-posts-{self.get_timestamp()}.json"
    
