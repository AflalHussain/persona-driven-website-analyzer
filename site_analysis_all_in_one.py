from langchain.memory import ConversationBufferWindowMemory
from langchain_anthropic import ChatAnthropic
from typing import List, Dict, Any, Set
import playwright.sync_api as pw
import json
from dataclasses import dataclass, field
from PIL import Image
import io
import base64
import os
import logging
import time
from datetime import datetime
from urllib.parse import urlparse, urljoin
import validators
import random
from tenacity import retry, stop_after_attempt, wait_exponential 

# Set up logging
def setup_logging():
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Create a timestamp for the log file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = f'logs/persona_crawler_{timestamp}.log'
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger('PersonaCrawler')

logger = setup_logging()

@dataclass
class Persona:
    name: str
    interests: List[str]
    needs: List[str]
    goals: List[str]

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
    chat_memory: ConversationBufferWindowMemory = field(default_factory=lambda: ConversationBufferWindowMemory(k=5))
    visited_urls: List[str] = field(default_factory=list)
    page_summaries: Dict[str, str] = field(default_factory=dict)
    key_insights: Dict[str, List[str]] = field(default_factory=dict)
    topic_relevance: Dict[str, float] = field(default_factory=dict)
    navigation_path: List[Dict[str, str]] = field(default_factory=list)
    satisfaction_scores: Dict[str, float] = field(default_factory=dict)
    consecutive_irrelevant_pages: int = 0
    found_ctas: List[str] = field(default_factory=list)
    covered_topics: Set[str] = field(default_factory=set)
    
class RateLimitedLLM:
    def __init__(self, api_key: str, min_delay: float = 10.0, max_delay: float = 20.0):
        self.llm = ChatAnthropic(
            model="claude-3-5-sonnet-latest",
            temperature=0.7,
            anthropic_api_key=api_key
        )
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.last_call_time = 0
        self.retry_count = 0
        self.max_retries = 3

    def _wait_for_rate_limit(self):
        """Ensure minimum delay between API calls with exponential backoff"""
        current_time = time.time()
        elapsed = current_time - self.last_call_time
        
        # Calculate delay with exponential backoff if we've had retries
        if self.retry_count > 0:
            delay = min(300, self.min_delay * (2 ** self.retry_count))  # Max 5 minutes
        else:
            delay = random.uniform(self.min_delay, self.max_delay)
            
        if elapsed < delay:
            sleep_time = delay - elapsed
            logger.info(f"Waiting {sleep_time:.2f} seconds before next API call")
            time.sleep(sleep_time)
            
        self.last_call_time = time.time()

    def invoke(self, message: Dict[str, str], max_attempts: int = 3) -> str:
        """Make API call with built-in retry logic"""
        self.retry_count = 0
        last_error = None
        
        while self.retry_count < max_attempts:
            try:
                self._wait_for_rate_limit()
                logger.info(f"Attempt {self.retry_count + 1} of {max_attempts}")
                
                response = self.llm.invoke(message)
                self.retry_count = 0  # Reset counter on success
                return response.content
                
            except Exception as e:
                self.retry_count += 1
                last_error = e
                error_msg = str(e)
                
                if "rate_limit_error" in error_msg:
                    logger.warning(f"Rate limit hit on attempt {self.retry_count}, waiting longer...")
                    # Exponential backoff handled in _wait_for_rate_limit
                elif self.retry_count >= max_attempts:
                    logger.error(f"Max retries ({max_attempts}) reached. Last error: {error_msg}")
                    raise
                else:
                    logger.warning(f"Error on attempt {self.retry_count}: {error_msg}")
                    time.sleep(2 ** self.retry_count)  # Simple exponential backoff
        
        raise ValueError(f"Failed after {max_attempts} attempts. Last error: {str(last_error)}")


class WebCrawler:
    def __init__(self):
        logger.info("Initializing WebCrawler")
        self.browser = pw.sync_playwright().start().chromium.launch(headless=True)
        self.base_url = ""
        logger.info("Browser launched successfully")
    
    def capture_screenshot(self, url: str) -> str:
        logger.info(f"Capturing screenshot of {url}")
        try:
            page = self.browser.new_page()
            page.goto(url)
            screenshot = page.screenshot()
            page.close()
            logger.info("Screenshot captured successfully")
            return base64.b64encode(screenshot).decode()
        except Exception as e:
            logger.error(f"Error capturing screenshot: {str(e)}")
            
    def validate_url(self, url: str) -> str:
        """Validate and normalize URL"""
        logger.debug(f"Validating URL: {url}")
        
        try:
            # Check if URL is relative
            if url.startswith('/'):
                # You need to define a base URL for relative URLs
                base_url = "https://hsenidmobile.com"  # Replace with your actual base URL
                url = urljoin(base_url, url)
                logger.info(f"Converted relative URL to absolute: {url}")
            
            # Add protocol if missing
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
                logger.info(f"Added https protocol to URL: {url}")
            
            # Validate URL
            if not validators.url(url):
                raise ValueError(f"Invalid URL format: {url}")
            
            return url
            
        except Exception as e:
            logger.error(f"URL validation error: {str(e)}")
            raise ValueError(f"Invalid URL: {url}")
    
    def extract_content(self, url: str) -> Dict[str, Any]:
        logger.info(f"Extracting content from {url}")
        start_time = time.time()
        
        try:
            # Validate URL before processing
            validated_url = self.validate_url(url)
            logger.info(f"Validated URL: {validated_url}")
            
            page = self.browser.new_page()
            page.goto(validated_url, wait_until='networkidle')
            
            # Extract text content
            logger.debug("Extracting visible text")
            visible_text = page.evaluate("""
                () => {
                    return Array.from(document.querySelectorAll('body *'))
                        .filter(element => {
                            const style = window.getComputedStyle(element);
                            return style.display !== 'none' && style.visibility !== 'hidden';
                        })
                        .map(element => element.textContent)
                        .join('\\n');
                }
            """)
            
            # Extract and validate links
            logger.debug("Extracting links")
            raw_links = [link.get_attribute('href') for link in page.query_selector_all('a')]
            
            # Process and validate links
            valid_links = []
            for link in raw_links:
                if link:
                    try:
                        if link.startswith('/'):
                            full_link = urljoin(validated_url, link)
                        else:
                            full_link = link if link.startswith(('http://', 'https://')) else urljoin(validated_url, link)
                        
                        if validators.url(full_link):
                            valid_links.append(full_link)
                    except Exception as e:
                        logger.warning(f"Skipping invalid link {link}: {str(e)}")
            
            logger.info(f"Found {len(valid_links)} valid links on the page")
            
            # Capture screenshot
            screenshot = self.capture_screenshot(validated_url)
            
            page.close()
            
            execution_time = time.time() - start_time
            logger.info(f"Content extraction completed in {execution_time:.2f} seconds")
            
            return {
                'url': validated_url,
                'text_content': visible_text,
                'links': valid_links,
                'screenshot': screenshot
            }
        except Exception as e:
            logger.error(f"Error extracting content: {str(e)}")
            raise
            
            
            
class PersonaAgent:
    def __init__(self, persona: Persona):
        logger.info(f"Initializing PersonaAgent for persona: {persona.name}")
        self.persona = persona
        self.llm = RateLimitedLLM(os.getenv("ANTHROPIC_API_KEY"))
        # self.memory = ConversationBufferWindowMemory(k=5)
        self.crawler = WebCrawler()
        self.memory = NavigationMemory()
        self.exit_criteria = ExitCriteria()
        self.context_window = 3  # Number of previous pages to consider

        logger.info("PersonaAgent initialization completed")
        
    def _detect_cta(self, content: Dict[str, Any]) -> bool:
        """Detect if page contains relevant CTAs"""
        cta_keywords = ['contact', 'demo', 'trial', 'sign up', 'get started']
        text = content['text_content'].lower()
        
        for keyword in cta_keywords:
            if keyword in text:
                self.memory.found_ctas.append(keyword)
                return True
        return False

    def _calculate_information_coverage(self) -> float:
        """Calculate how much of persona's needs have been covered"""
        covered_topics = set()
        
        # Check coverage from all visited pages
        for insights in self.memory.key_insights.values():
            for insight in insights:
                for need in self.persona.needs:
                    if need.lower() in insight.lower():
                        covered_topics.add(need)
        
        coverage = len(covered_topics) / len(self.persona.needs)
        logger.info(f"Current information coverage: {coverage:.2f}")
        return coverage

    def should_exit(self, current_content: Dict[str, Any]) -> tuple[bool, str]:
        """Determine if browsing should end"""
        # Check for CTA
        # if self._detect_cta(current_content):
        #     return True, f"Found relevant CTA: {self.memory.found_ctas[-1]}"
        
        # Check information satisfaction
        if self._calculate_information_coverage() >= self.exit_criteria.min_information_coverage:
            return True, "Gathered sufficient information"
        
        # Check content relevance
        if self.memory.consecutive_irrelevant_pages >= self.exit_criteria.consecutive_irrelevant_threshold:
            return True, "Website lacks relevant content"
        
        return False, ""

    def _update_memory(self, url: str, analysis: PageAnalysis) -> None:
        """Update navigation memory with new page analysis"""
        self.memory.visited_urls.append(url)
        self.memory.page_summaries[url] = analysis.summary
        
        # Store key insights
        self.memory.key_insights[url] = [
            *analysis.likes,
            *analysis.dislikes,
            *analysis.click_reasons
        ]
        
        # Calculate and store topic relevance
        relevance_score = self._calculate_relevance(analysis)
        self.memory.topic_relevance[url] = relevance_score
        
        # Update navigation path
        self.memory.navigation_path.append({
            'url': url,
            'reason': 'Initial page' if not self.memory.navigation_path else analysis.click_reasons[0] if analysis.click_reasons else 'Continued exploration'
        })
        
        # Calculate satisfaction score
        satisfaction = len(analysis.likes) / (len(analysis.likes) + len(analysis.dislikes)) if analysis.likes or analysis.dislikes else 0.5
        self.memory.satisfaction_scores[url] = satisfaction

    def _calculate_relevance(self, analysis: PageAnalysis) -> float:
        """Calculate relevance score based on persona interests and needs"""
        score = 0.0
        text = f"{analysis.summary} {' '.join(analysis.likes)} {' '.join(analysis.click_reasons)}"
        text = text.lower()
        
        # Score based on interests
        for interest in self.persona.interests:
            if interest.lower() in text:
                score += 0.2
        
        # Score based on needs
        for need in self.persona.needs:
            if need.lower() in text:
                score += 0.2
        
        return min(1.0, score)

    def _get_context_summary(self) -> str:
        """Generate summary of recent navigation history"""
        recent_pages = self.memory.visited_urls[-self.context_window:]
        context_summary = []
        
        for url in recent_pages:
            summary = self.memory.page_summaries.get(url, '')
            insights = self.memory.key_insights.get(url, [])
            relevance = self.memory.topic_relevance.get(url, 0.0)
            
            context_summary.append(f"""
            URL: {url}
            Relevance Score: {relevance:.2f}
            Summary: {summary}
            Key Insights: {', '.join(insights[:3])}
            """)
        
        return "\n".join(context_summary)
    
    def _encode_image_for_claude(self, base64_image: str) -> str:
        """Prepare base64 image for Claude's image analysis"""
        return f"<image>{base64_image}</image>"
    
    def _preprocess_content(self, text_content: str, max_length: int = 2000) -> str:
        """Clean and optimize text content to reduce tokens"""
        # Remove extra whitespace
        text = ' '.join(text_content.split())
        
        # Remove duplicate paragraphs
        seen_paragraphs = set()
        unique_paragraphs = []
        for paragraph in text.split('\n'):
            if paragraph.strip() and paragraph not in seen_paragraphs:
                seen_paragraphs.add(paragraph)
                unique_paragraphs.append(paragraph)
        
        # Join and truncate
        cleaned_text = '\n'.join(unique_paragraphs)
        return cleaned_text[:max_length]

    def _extract_headers(self, content: str) -> str:
        """Extract main headers from content"""
        lines = content.split('\n')
        headers = []
        for line in lines:
            # Basic heuristic for headers - can be improved
            if len(line.strip()) < 100 and any(char.isupper() for char in line):
                headers.append(line.strip())
        return '\n'.join(headers[:5])  # Return top 5 headers

    def _extract_main_content(self, content: str) -> str:
        """Extract most relevant content sections"""
        # Look for content matching persona interests
        relevant_paragraphs = []
        importance_score = {}
        
        paragraphs = content.split('\n\n')
        for idx, para in enumerate(paragraphs):
            score = 0
            # Score based on interest matches
            for interest in self.persona.interests:
                if interest.lower() in para.lower():
                    score += 2
            # Score based on needs matches
            for need in self.persona.needs:
                if need.lower() in para.lower():
                    score += 2
            # Prioritize earlier paragraphs
            score += max(0, (len(paragraphs) - idx) / len(paragraphs))
            
            importance_score[para] = score
        
        # Get top scoring paragraphs
        sorted_paras = sorted(importance_score.items(), key=lambda x: x[1], reverse=True)
        selected_content = '\n\n'.join(para for para, _ in sorted_paras[:3])
        
        return selected_content

    def analyze_page(self, url: str, content: Dict[str, Any]) -> PageAnalysis:
        logger.info(f"Starting page analysis for {url}")
        start_time = time.time()
        
        try:
            logger.info("Content extracted successfully")

            # Preprocess content to reduce tokens
            cleaned_content = self._preprocess_content(content['text_content'])
            
            # Extract key sections if they exist
            headers = self._extract_headers(cleaned_content)
            main_content = self._extract_main_content(cleaned_content)
            
            # Only encode screenshot if needed (based on persona goals)
            if any(goal.lower().find('visual') >= 0 for goal in self.persona.goals):
                image_content = self._encode_image_for_claude(content['screenshot'])
            else:
                image_content = "[Screenshot analysis skipped based on persona goals]"
            
            # Create focused prompt based on persona
            interests_str = ', '.join(self.persona.interests[:3])  # Limit to top 3
            needs_str = ', '.join(self.persona.needs[:3])
            goals_str = ', '.join(self.persona.goals[:3])
            
            # Create a more concise prompt
            prompt = f"""Analyze this webpage for {self.persona.name}:
        
                Key Interests: {interests_str}
                Primary Needs: {needs_str}
                Main Goals: {goals_str}
                
                Page Headers:
                {headers}
                
                Main Content:
                {main_content}
                
                Visual:
                {image_content}
                
                Provide CONCISE analysis:

                VISUAL BRIEF
                - Key layout elements
                - Main visual features
                - Navigation elements
                
                CONTENT SUMMARY
                - Relevance to persona
                - Key information
                - Content quality
                
                FINAL ASSESSMENT
                
                Summary: [Brief overview]
                Likes:
                - [Based on both Visual Brief and Content summary in a ratio of 1:2 .Top 3 only]
                Dislikes:
                - [Based on both Visual Brief and Content summary in a ratio of 1:2 .Top 3 only]
                Click Reasons:
                - [Max 2 points]
                Next Expectations:
                - [Max 2 points]
                Overall Impression: [One sentence impression]
                """
            
            logger.info("Sending optimized analysis request")
            try:
                # Try with a shorter timeout first
                response = self.llm.invoke(prompt, max_attempts=2)
            except Exception as e:
                logger.warning(f"Initial analysis attempt failed: {str(e)}")
                # If it fails, try with more aggressive content reduction
                logger.info("Reducing content and retrying...")
                
                # Reduce content length
                main_content = self._extract_main_content(cleaned_content)[:1000]
                headers = self._extract_headers(cleaned_content)[:200]
                
                # Update message with reduced content
                prompt["content"] = prompt["content"].replace(
                    f"Main Content:\n{main_content}",
                    f"Main Content:\n{main_content[:1000]}"
                )
                
                # Try again with reduced content
                response = self.llm.invoke(prompt, max_attempts=3)
                
            analysis_response = response
            logger.info("Received analysis response")
            logger.info(f"Raw analysis:\n{analysis_response}")
            
            # Parse the unified response
            sections = analysis_response.split('\n\n')
            parsed = {
                'summary': '',
                'likes': [],
                'dislikes': [],
                'click_reasons': [],
                'next_expectations': [],
                'overall_impression': ''
            }
            
            current_section = None
            for section in sections:
                if 'FINAL ASSESSMENT' in section:
                    current_section = 'final'
                    continue
                    
                if current_section == 'final':
                    if section.startswith('Summary:'):
                        logger.info(section)
                        summary_content = section.replace('Summary:', '').strip()
                        parsed['summary'] = summary_content
                        logger.info(f"Found standalone summary: {summary_content}")
                    elif section.startswith('Likes:'):
                        parsed['likes'] = [x.strip('- ') for x in section.replace('Likes:', '').strip().split('\n') if x.strip()]
                    elif section.startswith('Dislikes:'):
                        parsed['dislikes'] = [x.strip('- ') for x in section.replace('Dislikes:', '').strip().split('\n') if x.strip()]
                    elif section.startswith('Click Reasons:'):
                        parsed['click_reasons'] = [x.strip('- ') for x in section.replace('Click Reasons:', '').strip().split('\n') if x.strip()]
                    elif section.startswith('Next Expectations:'):
                        parsed['next_expectations'] = [x.strip('- ') for x in section.replace('Next Expectations:', '').strip().split('\n') if x.strip()]
                    elif section.startswith('Overall Impression:'):
                        parsed['overall_impression'] = section.replace('Overall Impression:', '').strip()
            
            execution_time = time.time() - start_time
            logger.info(f"Page analysis completed in {execution_time:.2f} seconds")
            logger.info("Parsed analysis:")
            logger.info(json.dumps(parsed, indent=4))
            
            return PageAnalysis(
                url=url,
                summary=parsed.get('summary', ''),
                likes=parsed.get('likes', []),
                dislikes=parsed.get('dislikes', []),
                click_reasons=parsed.get('click_reasons', []),
                next_expectations=parsed.get('next_expectations', []),
                overall_impression=parsed.get('overall_impression', '')
            )
            
        except Exception as e:
            logger.error(f"Error in page analysis: {str(e)}")
            return PageAnalysis(
                url=url,
                summary=f"Error in analysis: {str(e)}",
                likes=[],
                dislikes=[],
                click_reasons=[],
                next_expectations=[],
                overall_impression="Analysis failed"
            )
    
    def navigate(self, start_url: str, max_pages: int = 5) -> Dict[str, Any]:
        self.crawler.base_url = start_url
        logger.info(f"Starting navigation from {start_url} with max_pages={max_pages}")
        visited_pages = []
        current_url = start_url
        
        for page_num in range(max_pages):
            logger.info(f"Processing page {page_num + 1} of {max_pages}: {current_url}")
            
            # Extract links and choose next page
            content = self.crawler.extract_content(current_url)
            
            # Check exit conditions
            should_stop, exit_reason = self.should_exit(content)
            if should_stop:
                logger.info(f"Exiting navigation: {exit_reason}")
                break
            
            # Analyze current page
            analysis = self.analyze_page(current_url, content)
            self._update_memory(current_url, analysis)
            visited_pages.append(analysis)
            
            # Update consecutive irrelevant pages counter
            if self.memory.topic_relevance.get(current_url, 0) < 0.3:
                self.memory.consecutive_irrelevant_pages += 1
            else:
                self.memory.consecutive_irrelevant_pages = 0
            
            
            if not content['links']:
                logger.info("No links found on page. Ending navigation.")
                break
                
            # Choose next URL
            next_url = self._choose_next_url(current_url, content['links'], analysis)
            if not next_url:
                logger.info("No suitable next URL found. Ending navigation.")
                break
                
            logger.info(f"Selected next URL: {next_url}")
            current_url = next_url
        
        logger.info("Navigation completed. Generating report.")
        return self._generate_report(visited_pages, exit_reason)
    
    def _choose_next_url(self, current_url: str, links: List[str], current_analysis: PageAnalysis) -> str:
        logger.info("Choosing next URL with context")
        
        # Get navigation history context
        context_summary = self._get_context_summary()
        
        prompt = f"""As {self.persona.name}, choose the next most relevant link considering the navigation history:

        Your interests are: {', '.join(self.persona.interests)}
        Your goals are: {', '.join(self.persona.goals)}
        
        Navigation History:
        {context_summary}
        
        Current URL: {current_url}
        Current Page Summary: {current_analysis.summary}
        
        Available links:
        {json.dumps(links[:50], indent=2)}
        
        Based on the navigation history and your goals, choose the most relevant unvisited link.
        Consider:
        1. Links that complement previously gained information
        2. Topics not yet explored but relevant to your goals
        3. Avoid revisiting similar content
        
        Explain your choice considering the navigation history, then provide just the chosen URL on a new line.
        """
        
        try:
            response = self.llm.invoke(prompt)
            url = response.strip().split('\n')[-1].strip()
            
            if url in links and url not in self.memory.visited_urls:
                logger.info(f"Selected new URL: {url}")
                return url
            else:
                logger.warning("Selected URL invalid or already visited")
                
                # Find first unvisited valid link
                for link in links:
                    if link not in self.memory.visited_urls:
                        return link
                        
        except Exception as e:
            logger.error(f"Error in URL selection: {str(e)}")
            
        return None
    
    def _generate_report(self, page_analyses: List[PageAnalysis], exit_reason: str) -> Dict[str, Any]:
        """Generate enhanced report with journey insights"""
        report = {
            "persona": {
                "name": self.persona.name,
                "interests": self.persona.interests,
                "needs": self.persona.needs,
                "goals": self.persona.goals
            },
            "journey": [
                {
                    "url": analysis.url,
                    "summary": analysis.summary,
                    "likes": analysis.likes,
                    "dislikes": analysis.dislikes,
                    "click_reasons": analysis.click_reasons,
                    "next_expectations": analysis.next_expectations,
                    "overall_impression": analysis.overall_impression,
                    "relevance_score": self.memory.topic_relevance.get(analysis.url, 0.0),
                    "satisfaction_score": self.memory.satisfaction_scores.get(analysis.url, 0.0)
                }
                for analysis in page_analyses
            ],
            "navigation_insights": {
                "exit_reason": exit_reason,
                "path": self.memory.navigation_path,
                "found_ctas": self.memory.found_ctas,
                "information_coverage": self._calculate_information_coverage(),
                "average_relevance": sum(self.memory.topic_relevance.values()) / len(self.memory.topic_relevance) if self.memory.topic_relevance else 0,
                "average_satisfaction": sum(self.memory.satisfaction_scores.values()) / len(self.memory.satisfaction_scores) if self.memory.satisfaction_scores else 0,
                "exploration_coverage": len(self.memory.visited_urls) / (len(self.memory.visited_urls) + len(set(self.persona.interests) - set(self.memory.key_insights.keys())))
            }
        }
        
        return report
# Define persona
        # tech_bob = Persona(
        #     name="Tech-Savvy Bob",
        #     interests=["Latest technology", "Software development", "AI"],
        #     needs=["Efficient solutions", "Detailed technical specifications"],
        #     goals=["Find cutting-edge tools", "Understand technical details"]
        # )
def main():
    logger.info("Starting persona web crawler")
    agent = None
    
    try:
        # Define persona
        data_engineer_persona = Persona(
            name="Data Engineer Dave",
            interests=[
                "Data Engineering",
                "Machine Learning",
                "Big Data Processing",
                "Cloud Architecture",
                "Data Pipelines"
            ],
            needs=[
                "Technical documentation",
                "Platform capabilities",
                "Integration details",
                "Pricing information",
                "Performance benchmarks"
            ],
            goals=[
                "Evaluate data processing capabilities",
                "Understand MLOps features",
                "Compare pricing tiers",
                "Find implementation examples",
                "Access technical specifications"
            ],
        )
        
        logger.info(f"Created persona: {data_engineer_persona.name}")
        
        # Create agent
        agent = PersonaAgent(data_engineer_persona)
        
        # Run navigation
        try:
            report = agent.navigate("https://databricks.com")
        except Exception as nav_error:
            logger.error(f"Navigation error: {str(nav_error)}")
            # Generate partial report with available data
            if agent and hasattr(agent, 'memory'):
                report = agent._generate_report(
                    agent.memory.visited_urls, 
                    f"Error during navigation: {str(nav_error)}"
                )
            else:
                report = {
                    "error": str(nav_error),
                    "status": "Failed during navigation"
                }
            
    except Exception as e:
        logger.error(f"Error in main execution: {str(e)}")
        # Generate basic report even if agent creation fails
        report = {
            "error": str(e),
            "status": "Failed during initialization",
            "timestamp": datetime.now().isoformat()
        }
    
    finally:
        # Always try to save whatever report we have
        try:
            output_file = f"persona_analysis_report_databricks_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            # If we don't have a report yet, create a minimal one
            if not report:
                report = {
                    "status": "Failed with no data",
                    "timestamp": datetime.now().isoformat()
                }
            
            # Add error handling metadata
            report["metadata"] = {
                "completion_status": "partial" if "error" in report else "complete",
                "timestamp": datetime.now().isoformat(),
                "pages_analyzed": len(agent.memory.visited_urls) if agent and hasattr(agent, 'memory') else 0
            }
            
            # Save report
            with open(output_file, "w") as f:
                json.dump(report, f, indent=2)
                
            logger.info(f"Report saved to {output_file}")
            
        except Exception as save_error:
            logger.error(f"Error saving report: {str(save_error)}")
            # Last resort: try to save to a simple text file
            try:
                with open("emergency_report_dump.txt", "w") as f:
                    f.write(str(report))
                logger.info("Emergency report dump saved")
            except:
                logger.error("Failed to save even emergency report dump")

if __name__ == "__main__":
    main()