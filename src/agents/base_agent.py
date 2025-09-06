from abc import ABC, abstractmethod
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """Base class for website analysis agents"""
    
    @abstractmethod
    def analyze_page(self, url: str, content: Dict[str, Any]) -> Any:
        """Analyze a single webpage"""
        pass
        
    @abstractmethod
    def navigate(self, start_url: str, max_pages: int = 5) -> Dict[str, Any]:
        """Navigate through website starting from given URL"""
        pass
        
    @abstractmethod
    def should_exit(self, current_content: Dict[str, Any]) -> tuple[bool, str]:
        """Determine if website exploration should end"""
        pass 