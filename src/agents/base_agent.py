"""Base agent class for all Claude Life agents."""

import os
import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

class BaseAgent(ABC):
    """Base class for all agents in the Claude Life system."""
    
    def __init__(self, name: str, output_dir: str = "metrics"):
        self.name = name
        self.output_dir = Path(output_dir)
        self.logger = self._setup_logger()
        self._load_environment()
    
    def _setup_logger(self) -> logging.Logger:
        """Set up logging for the agent."""
        logger = logging.getLogger(self.name)
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _load_environment(self) -> None:
        """Load environment variables from .env file."""
        env_file = Path('.env')
        if env_file.exists():
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        os.environ[key] = value
    
    def save_json(self, data: Dict[Any, Any], filename: str, subdir: str = "") -> str:
        """Save data as JSON file."""
        output_path = self.output_dir
        if subdir:
            output_path = output_path / subdir
        
        output_path.mkdir(parents=True, exist_ok=True)
        
        filepath = output_path / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Saved {filename} to {filepath}")
        return str(filepath)
    
    def load_json(self, filepath: str) -> Optional[Dict[Any, Any]]:
        """Load JSON data from file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            self.logger.error(f"File not found: {filepath}")
            return None
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON decode error in {filepath}: {e}")
            return None
    
    def get_timestamp(self) -> str:
        """Get current timestamp in YYYY-MM-DD format."""
        return datetime.now().strftime("%Y-%m-%d")
    
    def sanitize_domain(self, url: str) -> str:
        """Extract and sanitize domain name from URL."""
        domain = url.replace('https://', '').replace('http://', '')
        domain = domain.replace('www.', '').split('/')[0]
        return domain.replace('.', '-')
    
    @abstractmethod
    def process(self, url: str, **kwargs) -> Dict[str, Any]:
        """Process the given URL and return results."""
        pass
    
    @abstractmethod
    def get_output_filename(self, domain: str) -> str:
        """Generate output filename for the domain."""
        pass