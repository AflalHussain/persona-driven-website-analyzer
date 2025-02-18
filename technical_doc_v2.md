# Technical Documentation

## Recent Updates

### 1. Enhanced Cloudflare Detection
- Added robust detection of Cloudflare security challenges
- Immediate graceful exit when detected
- Clear error messaging for human verification requirements
```python
def _detect_cloudflare(self, page: pw.Page) -> bool:
    cloudflare_indicators = [
        "//h1[contains(text(), 'Verify you are human')]",
        "//iframe[contains(@src, 'challenges.cloudflare.com')]",
        "//*[contains(text(), 'needs to review the security of your connection')]",
        "//input[@name='cf_captcha']",
        "//*[@id='challenge-running']",
        "//*[@class='cf-browser-verification']"
    ]
```

### 2. Improved Screenshot Capture
- Added fallback mechanisms for network timeouts
- Two-stage loading strategy (networkidle → domcontentloaded)
- Grace period for additional content loading
```python
try:
    page.goto(url, wait_until='networkidle', timeout=30000)
except Exception:
    logger.warning("NetworkIdle timeout, falling back to domcontentloaded")
    page.goto(url, wait_until='domcontentloaded', timeout=30000)
    time.sleep(2)  # Grace period
```

### 3. Enhanced Navigation Decision Making
- Added visited page history to URL selection context
- Improved avoidance of previously visited pages
- Better context for LLM decision making
```python
visited_context = "Previously visited pages:\n"
for url in self.memory.visited_urls:
    summary = self.memory.page_summaries.get(url)
    impression = self.memory.overall_impressions.get(url)
    visited_context += f"- {url}\n  Summary: {summary}\n  Impression: {impression}\n"
```

### 4. Focus Group Analysis Improvements
- Sequential processing to respect rate limits
- Individual report saving during analysis
- Proper error handling and partial results preservation
```python
if report.get("error") == "cloudflare_detected":
    return {
        "error": "cloudflare_detected",
        "message": report['message'],
        "url": url,
        "timestamp": timestamp,
        "completed_analyses": reports,
        "status": "stopped"
    }
```

### 5. Persona Generation
- Added structured template system
- Improved variation generation
- Automatic saving of generated personas
```python
@dataclass
class PersonaTemplate:
    role: str
    experience_level: str
    primary_goal: str
    context: str
    additional_details: Optional[Dict[str, str]] = None
```

## System Architecture

### Core Components

1. **Persona Management**
   - `PersonaTemplate`: Base template for generating variations
   - `Persona`: Individual user profiles with interests, needs, and goals
   - `PersonaGenerator`: Creates diverse persona variations from templates

2. **Web Crawling**
   - `WebCrawler`: Handles page navigation and content extraction
   - Anti-detection measures for bot protection
   - Cloudflare detection and graceful handling
   - Screenshot capture with fallback mechanisms

3. **Analysis Engine**
   - `PersonaAgent`: Performs persona-specific analysis
   - `FocusGroupAnalyzer`: Coordinates multiple persona analyses
   - Memory management for tracking visited pages
   - Intelligent URL selection with context awareness

### Key Features

#### 1. Intelligent Navigation
- Context-aware URL selection using visited page history
- Avoids revisiting pages
- Uses previous page insights to guide exploration
- Fallback mechanisms for invalid selections

```python
def _choose_next_url(self, current_url: str, links: List[str], current_analysis: PageAnalysis) -> str:
    # Filters out same-page and visited links
    external_links = [
        link for link in links 
        if not is_same_page_link(link, current_url)
    ]
    
    # Uses visited page context for decision making
    visited_context = self._format_visited_pages_context()
    
    # Makes informed decision based on history
    prompt = f"""As {self.persona.name}, explain your navigation decision:
        Previously visited: {visited_context}
        Available unvisited links: {unvisited_links}
        ...
    """
```

#### 2. Bot Detection Handling
- Detects Cloudflare and similar security challenges
- Graceful error handling and reporting
- Preserves partial analysis results

```python
class CloudflareDetectedException(Exception):
    """Custom exception for Cloudflare detection"""
    pass

def _detect_cloudflare(self, page: pw.Page) -> bool:
    # Checks for security challenge indicators
    cloudflare_indicators = [
        "//h1[contains(text(), 'Verify you are human')]",
        "//iframe[contains(@src, 'challenges.cloudflare.com')]",
        ...
    ]
```

#### 3. Focus Group Analysis
- Sequential analysis with rate limit handling
- Individual and combined report generation
- Common pattern identification
- LLM-powered summary generation

```python
class FocusGroupAnalyzer:
    def analyze_website(self, url: str, max_pages: int = 5) -> Dict[str, Any]:
        # Sequential analysis with delays
        for persona in self.personas:
            report = self._analyze_with_persona(url, persona, max_pages)
            # Handle Cloudflare detection
            if report.get("error") == "cloudflare_detected":
                return self._generate_error_report(report)
```

### Data Structures

#### 1. Navigation Memory
```python
@dataclass
class NavigationMemory:
    visited_urls: Set[str]
    page_summaries: Dict[str, str]
    overall_impressions: Dict[str, str]
    key_insights: Dict[str, List[str]]
    navigation_path: List[str]
```

#### 2. Analysis Reports
```python
@dataclass
class PageAnalysis:
    url: str
    summary: str
    likes: List[str]
    dislikes: List[str]
    click_reasons: List[str]
    next_expectations: List[str]
    visual_analysis: List[str]
    overall_impression: str
```

### Error Handling

1. **Cloudflare Detection**
   - Early detection and graceful exit
   - Preserves partial analysis results
   - Clear error messaging

2. **Network Issues**
   - Fallback mechanisms for timeouts
   - Screenshot capture resilience
   - Retry logic with exponential backoff

3. **Content Extraction**
   - Handles dynamic content loading
   - Fallback to basic content when needed
   - Preserves partial extractions

### Rate Limiting

1. **Focus Group Analysis**
   - 30-second delays between persona analyses
   - Sequential processing to avoid API limits
   - Proper cleanup and resource management

2. **LLM Interactions**
   - Rate-limited API client
   - Error handling for API limits
   - Graceful degradation

### Output Files

1. **Individual Reports**
```
reports/focus_group/{persona_name}_{timestamp}.json
```

2. **Combined Analysis**
```
reports/focus_group_analysis_{timestamp}.json
```

3. **Generated Personas**
```
reports/personas/personas_{role}_{timestamp}.json
```

4. **Screenshots**
```
reports/screenshots/{domain}_{timestamp}.jpg
```

### Future Improvements

1. **Performance Optimization**
   - Implement caching for repeated requests
   - Optimize content extraction
   - Reduce token usage in prompts

2. **Enhanced Analysis**
   - Sentiment analysis integration
   - Competitive analysis features
   - A/B testing support

3. **Resilience**
   - Proxy rotation support
   - Advanced bot detection avoidance
   - CAPTCHA solving integration

4. **Reporting**
   - Interactive visualization
   - Trend analysis
   - Comparative reporting 

## Output Structure

### 1. Generated Persona File
```json
{
    "timestamp": "20240217_143000",
    "input_template": {
        "template": {
            "role": "Developer",
            "experience_level": "Senior",
            "primary_goal": "Find contract work",
            "context": "Looking for remote opportunities",
            "additional_details": {
                "preferred_stack": "Full-stack",
                "availability": "Part-time"
            }
        }
    },
    "generated_personas": [
        {
            "name": "John Doe",
            "interests": [...],
            "needs": [...],
            "goals": [...]
        }
    ]
}
```

### 2. Cloudflare Error Report
```json
{
    "error": "cloudflare_detected",
    "message": "Cloudflare security check detected at {url}. Unable to proceed with automated analysis.",
    "url": "https://example.com",
    "timestamp": "2024-02-18T10:27:09.950Z",
    "pages_analyzed": ["https://example.com/page1", ...],
    "status": "incomplete"
}
```

## Known Limitations

1. **Bot Detection**
   - Cannot bypass Cloudflare human verification
   - Some sites may still detect automation
   - Manual intervention required for protected sites

2. **Network Handling**
   - Maximum timeout of 60 seconds for initial page load
   - Fallback content may be incomplete
   - Some dynamic content may be missed

3. **Rate Limits**
   - 30-second delay between focus group analyses
   - API rate limits may affect analysis speed
   - Sequential processing can be time-consuming

## Best Practices

1. **URL Selection**
   - Start with less protected pages
   - Avoid known Cloudflare-protected sites
   - Use appropriate delays between requests

2. **Persona Generation**
   - Provide detailed templates
   - Include specific context
   - Define clear goals and needs

3. **Analysis Configuration**
   - Adjust max_pages based on site size
   - Configure appropriate timeouts
   - Monitor rate limits

## Future Roadmap

1. **Short Term**
   - Implement proxy support
   - Add request caching
   - Improve error recovery

2. **Medium Term**
   - Add competitive analysis
   - Implement A/B testing
   - Enhanced reporting features

3. **Long Term**
   - ML-based content analysis
   - Advanced bot detection avoidance
   - Interactive visualization tools 