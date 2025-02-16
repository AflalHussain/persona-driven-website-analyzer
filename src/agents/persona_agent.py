import os
import logging
from typing import Dict, Any, List, Tuple
import json
from datetime import datetime
import time

from ..models.persona import Persona
from ..models.analysis import PageAnalysis, NavigationMemory, ExitCriteria
from ..models.report import AnalysisReport
from ..crawlers.web_crawler import WebCrawler
from ..llm.claude_client import RateLimitedLLM
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

class PersonaAgent(BaseAgent):
    def __init__(self, persona: Persona):
        logger.info(f"Initializing PersonaAgent for persona: {persona.name}")
        self.persona = persona
        self.llm = RateLimitedLLM(os.getenv("ANTHROPIC_API_KEY"))
        self.crawler = WebCrawler()
        self.memory = NavigationMemory()
        self.exit_criteria = ExitCriteria()
        self.context_window = 3
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
        
        for insights in self.memory.key_insights.values():
            for insight in insights:
                for need in self.persona.needs:
                    if need.lower() in insight.lower():
                        covered_topics.add(need)
        
        coverage = len(covered_topics) / len(self.persona.needs)
        logger.info(f"Current information coverage: {coverage:.2f}")
        return coverage

    def should_exit(self, current_content: Dict[str, Any]) -> Tuple[bool, str]:
        """Determine if browsing should end"""
        # if self._detect_cta(current_content):
        #     return True, f"Found relevant CTA: {self.memory.found_ctas[-1]}"
        
        if self._calculate_information_coverage() >= self.exit_criteria.min_information_coverage:
            return True, "Gathered sufficient information"
        
        if self.memory.consecutive_irrelevant_pages >= self.exit_criteria.consecutive_irrelevant_threshold:
            return True, "Website lacks relevant content"
        
        return False, ""

    def _update_memory(self, url: str, analysis: PageAnalysis) -> None:
        """Update navigation memory with new page analysis"""
        self.memory.visited_urls.append(url)
        self.memory.page_summaries[url] = analysis.summary
        self.memory.overall_impressions[url] = analysis.overall_impression
        self.memory.next_expectations[url] = analysis.next_expectations
        self.memory.visual_analysis[url] = analysis.visual_analysis
        self.memory.key_insights[url] = [
            *analysis.likes,
            *analysis.dislikes,
            *analysis.click_reasons
        ]
        
        relevance_score = self._calculate_relevance(analysis)
        self.memory.topic_relevance[url] = relevance_score
        
        self.memory.navigation_path.append({
            'url': url,
            'reason': 'Initial page' if not self.memory.navigation_path else analysis.click_reasons[0] if analysis.click_reasons else 'Continued exploration'
        })
        
        satisfaction = len(analysis.likes) / (len(analysis.likes) + len(analysis.dislikes)) if analysis.likes or analysis.dislikes else 0.5
        self.memory.satisfaction_scores[url] = satisfaction

    def _calculate_relevance(self, analysis: PageAnalysis) -> float:
        """Calculate relevance score based on persona interests and needs"""
        score = 0.0
        text = f"{analysis.summary} {' '.join(analysis.likes)} {' '.join(analysis.click_reasons)}"
        text = text.lower()
        
        for interest in self.persona.interests:
            if interest.lower() in text:
                score += 0.2
        
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
            next_expectations = self.memory.next_expectations.get(url, [])
            overall_impression = self.memory.overall_impressions.get(url, '')
            insights = self.memory.key_insights.get(url, [])
            visual_analysis = self.memory.visual_analysis.get(url, [])
            relevance = self.memory.topic_relevance.get(url, 0.0)
            
            context_summary.append(f"""
            URL: {url}
            Relevance Score: {relevance:.2f}
            Summary: {summary}
            Key Insights: {', '.join(insights[:3])}
            Visual Analysis: {', '.join(visual_analysis)}
            Overall Impression: {overall_impression}
            """)
        
        return "\n".join(context_summary)
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
                - Main visual features like color, font, etc
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
                'visual_analysis': [],
                'overall_impression': ''
            }
            
            current_section = None
            for section in sections:
                if section.startswith('VISUAL BRIEF'):
                    # Skip the "VISUAL BRIEF" header and just take the content
                    parsed['visual_analysis'] = [x.strip('- ') for x in section.split('\n')[1:] if x.strip()]
                     
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
                visual_analysis=parsed.get('visual_analysis', []),
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

    def navigate(self, start_url: str, max_pages: int = 100) -> Dict[str, Any]:
        """Navigate through website and generate analysis report"""
        logger.info(f"Starting navigation from {start_url}")
        self.crawler.base_url = start_url
        current_url = start_url
        exit_reason = ""
        
        try:
            for page_num in range(max_pages):
                logger.info(f"Processing page {page_num + 1} of {max_pages}: {current_url}")
                
                content = self.crawler.extract_content(current_url)
                should_stop, exit_reason = self.should_exit(content)
                
                analysis = self.analyze_page(current_url, content)
                self._update_memory(current_url, analysis)
                
                if should_stop:
                    logger.info(f"Exiting navigation: {exit_reason}")
                    break
                
                # Update consecutive irrelevant pages counter
                if self.memory.topic_relevance.get(current_url, 0) < 0.3:
                    self.memory.consecutive_irrelevant_pages += 1
                else:
                    self.memory.consecutive_irrelevant_pages = 0
                
                if not content['links']:
                    logger.info("No links found on page. Ending navigation.")
                    exit_reason = "No further links to explore"
                    break
                    
                next_url = self._choose_next_url(current_url, content['links'], analysis)
                if not next_url:
                    logger.info("No suitable next URL found. Ending navigation.")
                    exit_reason = "No relevant links to explore"
                    break
                    
                current_url = next_url
                
        except Exception as e:
            logger.error(f"Error during navigation: {str(e)}")
            exit_reason = f"Error: {str(e)}"
            
        finally:
            final_conclusion = self._generate_final_conclusion()
            # Generate report even if navigation was incomplete
            report = AnalysisReport(
                persona_name=self.persona.name,
                start_url=start_url,
                pages_analyzed=[PageAnalysis(
                    url=url,
                    summary=self.memory.page_summaries.get(url, ''),
                    likes=self.memory.key_insights.get(url, [])[:3],
                    dislikes=self.memory.key_insights.get(url, [])[3:6],
                    click_reasons=self.memory.key_insights.get(url, [])[6:8],
                    next_expectations=self.memory.next_expectations.get(url, []),
                    visual_analysis=self.memory.visual_analysis.get(url, []),
                    overall_impression=self.memory.overall_impressions.get(url, ''),
                ) for url in self.memory.visited_urls],
                navigation_path=self.memory.navigation_path,
                exit_reason=exit_reason,
                information_coverage=self._calculate_information_coverage(),
                found_ctas=self.memory.found_ctas,
                final_conclusion=final_conclusion
            )
            
            return report.to_dict() 
        
    def _log_decision(self, decision_type: str, context: str, reasoning: str) -> Dict[str, str]:
        """Log a decision with context and reasoning"""
        decision = {
            "timestamp": datetime.now().isoformat(),
            "type": decision_type,
            "context": context,
            "reasoning": reasoning,
            "persona_attributes": {
                "interests": self.persona.interests,
                "needs": self.persona.needs,
                "goals": self.persona.goals
            }
        }
        self.memory.decisions.append(decision)
        return decision

    def _choose_next_url(self, current_url: str, links: List[str], current_analysis: PageAnalysis) -> str:
        logger.info("Choosing next URL with context")
        
        prompt = f"""As {self.persona.name}, explain your navigation decision:

        Your Profile:
        - Interests: {', '.join(self.persona.interests)}
        - Goals: {', '.join(self.persona.goals)}
        
        Current Page Analysis:
        - URL: {current_url}
        - Summary: {current_analysis.summary}
        - Likes: {', '.join(current_analysis.likes)}
        - Dislikes: {', '.join(current_analysis.dislikes)}
        
        Available links:
        {json.dumps(links[:50], indent=2)}
        
        1. First explain your reasoning considering:
           - How the current page meets your needs
           - What information you're still looking for
           - Why certain links appear promising
        
        2. Then provide just the chosen URL on a new line.
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

    def _encode_image_for_claude(self, base64_image: str) -> str:
        """Prepare base64 image for Claude's image analysis"""
        return f"<image>{base64_image}</image>"

    def _generate_final_conclusion(self) -> str:
        """Generate a final conclusion summarizing the persona's experience"""
        logger.info("Generating final conclusion")
        
        # Prepare summary data
        visited_pages = len(self.memory.visited_urls)
        coverage = self._calculate_information_coverage()
        avg_satisfaction = sum(self.memory.satisfaction_scores.values()) / len(self.memory.satisfaction_scores) if self.memory.satisfaction_scores else 0
        
        prompt = f"""As {self.persona.name}, provide a concise final conclusion about your experience analyzing this website.

        Your Profile:
        - Interests: {', '.join(self.persona.interests)}
        - Needs: {', '.join(self.persona.needs)}
        - Goals: {', '.join(self.persona.goals)}

        Analysis Summary:
        - Pages Analyzed: {visited_pages}
        - Information Coverage: {coverage:.2%}
        - Average Satisfaction: {avg_satisfaction:.2%}
        - Found CTAs: {', '.join(self.memory.found_ctas) if self.memory.found_ctas else 'None'}

        Key Insights:
        {json.dumps(dict(list(self.memory.key_insights.items())[:3]), indent=2)}

        Provide a 3-4 sentence conclusion that:
        1. Evaluates how well the website meets your needs and goals
        2. Highlights key strengths and weaknesses
        3. Makes a final recommendation
        """

        try:
            conclusion = self.llm.invoke(prompt)
            logger.info("Generated final conclusion")
            return conclusion.strip()
        except Exception as e:
            logger.error(f"Error generating conclusion: {str(e)}")
            return "Error generating conclusion"