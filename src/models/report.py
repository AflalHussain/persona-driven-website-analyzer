from dataclasses import dataclass, field
from typing import List, Dict
from datetime import datetime
from .analysis import PageAnalysis

@dataclass
class AnalysisReport:
    persona_name: str
    start_url: str
    timestamp: datetime = field(default_factory=datetime.now)
    pages_analyzed: List[PageAnalysis] = field(default_factory=list)
    navigation_path: List[Dict[str, str]] = field(default_factory=list)
    exit_reason: str = ""
    information_coverage: float = 0.0
    found_ctas: List[str] = field(default_factory=list)
    final_conclusion: str = ""
    
    def __init__(self, 
                 persona_name: str,
                 start_url: str,
                 pages_analyzed: List[PageAnalysis],
                 navigation_path: List[Dict[str, str]],
                 exit_reason: str,
                 information_coverage: float,
                 found_ctas: List[str],
                 final_conclusion: str = None):
        self.persona_name = persona_name
        self.start_url = start_url
        self.pages_analyzed = pages_analyzed
        self.navigation_path = navigation_path
        self.exit_reason = exit_reason
        self.information_coverage = information_coverage
        self.found_ctas = found_ctas
        self.final_conclusion = final_conclusion
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def to_dict(self) -> Dict:
        """Convert report to dictionary format for JSON serialization"""
        return {
            "persona_name": self.persona_name,
            "start_url": self.start_url,
            "timestamp": self.timestamp,
            "pages_analyzed": [
                {
                    "url": page.url,
                    "summary": page.summary,
                    "likes": page.likes,
                    "dislikes": page.dislikes,
                    "click_reasons": page.click_reasons,
                    "next_expectations": page.next_expectations,
                    "visual_analysis": page.visual_analysis,
                    "overall_impression": page.overall_impression
                }
                for page in self.pages_analyzed
            ],
            "navigation_path": self.navigation_path,
            "exit_reason": self.exit_reason,
            "information_coverage": self.information_coverage,
            "found_ctas": self.found_ctas,
            "final_conclusion": self.final_conclusion
        } 