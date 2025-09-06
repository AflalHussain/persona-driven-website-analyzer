from typing import Dict, Any, List, Optional
import logging
from datetime import datetime
import asyncio
import os

from ..models.persona import Persona
from ..models.persona_generator import PersonaGenerator, PersonaTemplate
from ..agents.focus_group_analyzer import FocusGroupAnalyzer
from ..agents.persona_agent import PersonaAgent
from ..llm.claude_client import RateLimitedLLM

logger = logging.getLogger(__name__)

class WebsiteAnalysisAPI:
    """API for website analysis using personas"""
    
    def __init__(self):
        self.llm = RateLimitedLLM(os.getenv("ANTHROPIC_API_KEY"))
    
    async def analyze_with_persona(self, 
        url: str,
        persona_template: Dict[str, Any],
        max_pages: int = 5
    ) -> Dict[str, Any]:
        """
        Analyze website with a single persona generated from template
        
        Args:
            url: Website URL to analyze
            persona_template: Dict containing persona template data
            max_pages: Maximum pages to analyze
            
        Returns:
            Dict containing analysis results
        """
        try:
            # Generate single persona from template
            generator = PersonaGenerator(self.llm)
            personas = generator.generate_variations(
                PersonaTemplate(**persona_template),
                num_variations=1
            )
            
            if not personas:
                raise ValueError("Failed to generate persona from template")
                
            # Run analysis with single persona
            agent = PersonaAgent(personas[0])
            report = await agent.navigate(url, max_pages=max_pages)
            
            return {
                "status": "success",
                "timestamp": datetime.now().isoformat(),
                "url": url,
                "persona": personas[0].name,
                "report": report
            }
            
        except Exception as e:
            logger.error(f"Single persona analysis failed: {str(e)}")
            return {
                "status": "error",
                "timestamp": datetime.now().isoformat(),
                "url": url,
                "error": str(e)
            }

    async def analyze_with_focus_group(self,
        url: str,
        persona_template: Dict[str, Any],
        num_variations: int = 5,
        max_pages: int = 5
    ) -> Dict[str, Any]:
        """
        Analyze website with multiple generated personas
        
        Args:
            url: Website URL to analyze
            persona_template: Dict containing persona template data
            num_variations: Number of persona variations to generate
            max_pages: Maximum pages to analyze per persona
            
        Returns:
            Dict containing combined and individual analysis results
        """
        try:
            # Generate persona variations
            generator = PersonaGenerator(self.llm)
            personas = generator.generate_variations(
                PersonaTemplate(**persona_template),
                num_variations=num_variations
            )
            
            if not personas:
                raise ValueError("Failed to generate personas from template")
                
            # Run focus group analysis
            analyzer = FocusGroupAnalyzer(personas)
            report = await analyzer.analyze_website(url, max_pages=max_pages)
            
            return {
                "status": "success",
                "timestamp": datetime.now().isoformat(),
                "url": url,
                "num_personas": len(personas),
                "report": report
            }
            
        except Exception as e:
            logger.error(f"Focus group analysis failed: {str(e)}")
            return {
                "status": "error",
                "timestamp": datetime.now().isoformat(),
                "url": url,
                "error": str(e)
            }

    def validate_persona_template(self, template: Dict[str, Any]) -> bool:
        """
        Validate persona template format
        
        Args:
            template: Dict containing template data
            
        Returns:
            bool indicating if template is valid
        """
        required_fields = ['role', 'experience_level', 'primary_goal', 'context']
        return all(field in template for field in required_fields) 