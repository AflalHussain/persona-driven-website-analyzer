import asyncio
import logging
from typing import List, Dict, Any
from datetime import datetime
import json
import os
import time

from ..models.persona import Persona
from ..models.report import AnalysisReport
from .persona_agent import PersonaAgent
from ..llm.claude_client import RateLimitedLLM


logger = logging.getLogger(__name__)

class FocusGroupAnalyzer:
    def __init__(self, personas: List[Persona]):
        self.personas = personas
        self.llm = RateLimitedLLM(os.getenv("ANTHROPIC_API_KEY"))
        self.semaphore = asyncio.Semaphore(2)  # Limit concurrent LLM calls
        
    async def analyze_website(self, url: str, max_pages: int = 5) -> Dict[str, Any]:
        """Run parallel analysis with all personas while respecting rate limits"""
        logger.info(f"Starting focus group analysis of {url} with {len(self.personas)} personas")
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        tasks = []
        reports = []
        
        # Create analysis tasks
        for persona in self.personas:
            task = self._analyze_with_persona_rate_limited(url, persona, max_pages, timestamp)
            tasks.append(task)
        
        # Run analyses with rate limiting
        try:
            reports = await asyncio.gather(*tasks)
        except Exception as e:
            logger.error(f"Error during focus group analysis: {str(e)}")
            return self._generate_error_report(url, timestamp, reports, str(e))
            
        # Generate combined report
        return self._generate_combined_report(url, reports, timestamp)
    
    async def _analyze_with_persona_rate_limited(self, url: str, persona: Persona, max_pages: int, timestamp: str) -> Dict[str, Any]:
        """Run single persona analysis with rate limiting"""
        async with self.semaphore:  # Limit concurrent executions
            try:
                logger.info(f"Starting analysis with persona: {persona.name}")
                agent = PersonaAgent(persona)
                report = await agent.navigate(url, max_pages=max_pages)
                
                # Save individual report
                self._save_individual_report(report, persona, timestamp)
                
                # Add delay for rate limiting
                await asyncio.sleep(30)  # 30 seconds between analyses
                
                return report
                
            except Exception as e:
                logger.error(f"Analysis failed for persona {persona.name}: {str(e)}")
                return {
                    "error": "analysis_failed",
                    "persona": persona.name,
                    "message": str(e)
                }
    
    def _save_individual_report(self, report: Dict[str, Any], persona: Persona, timestamp: str):
        """Save individual persona report"""
        try:
            os.makedirs('reports/focus_group', exist_ok=True)
            filename = f"reports/focus_group/{persona.name.lower().replace(' ', '_')}_{timestamp}.json"
            with open(filename, 'w') as f:
                json.dump(report, f, indent=2)
            logger.info(f"Saved individual report for {persona.name}")
        except Exception as e:
            logger.error(f"Error saving report for {persona.name}: {str(e)}")
    
    def _generate_error_report(self, url: str, timestamp: str, completed_reports: List[Dict[str, Any]], error: str) -> Dict[str, Any]:
        """Generate error report with partial results"""
        return {
            "error": "focus_group_analysis_failed",
            "message": error,
            "url": url,
            "timestamp": timestamp,
            "completed_analyses": completed_reports,
            "status": "partial"
        }
        
    def _generate_combined_report(self, url: str, individual_reports: List[Dict[str, Any]], 
                                timestamp: str) -> Dict[str, Any]:
        """Generate a comprehensive report combining all persona insights"""
        
        # Analyze common patterns
        all_likes = []
        all_dislikes = []
        all_expectations = []
        
        for report in individual_reports:
            for page in report['pages_analyzed']:
                all_likes.extend(page['likes'])
                all_dislikes.extend(page['dislikes'])
                all_expectations.extend(page['next_expectations'])
        
        from collections import Counter
        
        common_likes = Counter(all_likes).most_common(5)
        common_dislikes = Counter(all_dislikes).most_common(5)
        common_expectations = Counter(all_expectations).most_common(5)
        
        # Generate summary using LLM
        summary_prompt = f"""Analyze these focus group results for {url}:
        
        Number of Participants: {len(individual_reports)}
        
        Common Likes:
        {json.dumps(common_likes, indent=2)}
        
        Common Dislikes:
        {json.dumps(common_dislikes, indent=2)}
        
        Common Expectations:
        {json.dumps(common_expectations, indent=2)}
        
        Provide a concise summary of:
        1. Key patterns across personas
        2. Notable differences between personas
        3. Main recommendations
        """
        
        summary = self._generate_summary(summary_prompt)
        
        # Generate and return combined report
        return {
            'url': url,
            'timestamp': timestamp,
            'num_personas': len(individual_reports),
            'common_patterns': {
                'likes': common_likes,
                'dislikes': common_dislikes,
                'expectations': common_expectations
            },
            'individual_reports': individual_reports,
            'summary': summary
        } 
    
    def _generate_summary(self, prompt: str) -> str:
        """Generate a summary using LLM"""
        try:
            response = self.llm.invoke(prompt)
            return response.strip()
        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
            return "Error generating summary"