from dataclasses import dataclass, field
from typing import List, Dict, Set
from datetime import datetime

@dataclass
class PageAnalysis:
    url: str
    summary: str
    likes: List[str]
    dislikes: List[str]
    click_reasons: List[str]
    next_expectations: List[str]
    overall_impression: str

@dataclass
class ExitCriteria:
    """Define criteria for ending website exploration"""
    found_cta: bool = False
    information_satisfied: bool = False
    content_irrelevant: bool = False
    satisfaction_threshold: float = 0.7
    min_information_coverage: float = 0.8
    max_irrelevant_pages: int = 3
    consecutive_irrelevant_threshold: int = 3

@dataclass
class NavigationMemory:
    """Memory management for navigation"""
    visited_urls: List[str] = field(default_factory=list)
    page_summaries: Dict[str, str] = field(default_factory=dict)
    key_insights: Dict[str, List[str]] = field(default_factory=dict)
    topic_relevance: Dict[str, float] = field(default_factory=dict)
    navigation_path: List[Dict[str, str]] = field(default_factory=list)
    satisfaction_scores: Dict[str, float] = field(default_factory=dict)
    consecutive_irrelevant_pages: int = 0
    found_ctas: List[str] = field(default_factory=list)
    covered_topics: Set[str] = field(default_factory=set) 