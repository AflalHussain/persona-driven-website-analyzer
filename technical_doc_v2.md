# Technical Documentation v2

## Major Updates from v1

### 1. Async Architecture Implementation
- Converted to async/await pattern for better performance
- Implemented proper async context managers
- Added graceful cleanup of async resources
```python
async with WebCrawler() as crawler:
    self.crawler = crawler
    # Async navigation and content extraction
```

### 2. Enhanced Bot Detection & Handling
- Added comprehensive Cloudflare detection
- Implemented graceful exit with partial results
- Added detailed error reporting for bot detection
```python
cloudflare_indicators = [
    "//h1[contains(text(), 'Verify you are human')]",
    "//iframe[contains(@src, 'challenges.cloudflare.com')]",
    "//*[contains(text(), 'needs to review the security of your connection')]"
]
```

### 3. Improved Content Extraction
- Two-stage loading strategy (networkidle → domcontentloaded)
- Added grace periods for dynamic content
- Better handling of lazy-loaded content
- Section-aware content extraction
```python
try:
    await page.goto(url, wait_until='networkidle', timeout=30000)
except Exception:
    await page.goto(url, wait_until='domcontentloaded', timeout=30000)
    await asyncio.sleep(2)  # Grace period
```

### 4. Smarter Navigation
- Context-aware URL selection using visit history
- Added memory of page impressions and summaries
- Improved duplicate avoidance
```python
visited_context = "Previously visited pages:\n"
for url in self.memory.visited_urls:
    summary = self.memory.page_summaries.get(url)
    impression = self.memory.overall_impressions.get(url)
```

### 5. Focus Group Analysis
- Added structured persona templates
- Implemented parallel persona generation
- Added combined analysis reporting
```python
@dataclass
class PersonaTemplate:
    role: str
    experience_level: str
    primary_goal: str
    context: str
```

### 6. Enhanced Error Handling
- Added partial results preservation
- Implemented graceful degradation
- Better error reporting and logging
```python
if report.get("error") == "cloudflare_detected":
    return {
        "error": "cloudflare_detected",
        "message": report['message'],
        "completed_analyses": reports,
        "status": "stopped"
    }
```

### 7. Improved File Organization
- Added structured report directories
- Implemented timestamp-based naming
- Added screenshot management
```
reports/
├── focus_group/
├── personas/
└── screenshots/
```

## New Features

1. **Screenshot Management**
   - Automatic screenshot directory creation
   - Timestamp-based naming
   - Quality optimization
   - Full-page capture support

2. **Section Analysis**
   - Detection of page sections
   - Section content extraction
   - Section-aware navigation

3. **Partial Results**
   - Preservation of completed analyses
   - Incomplete analysis reporting
   - Progress tracking

4. **Rate Limiting**
   - Added delays between analyses
   - API rate limit handling
   - Resource cleanup

5. **Template System**
   - Structured persona templates
   - Template validation
   - Automatic persona generation

## Enhanced Components

### WebCrawler
- Added async support
- Improved bot detection
- Better content extraction
- Screenshot management

### PersonaAgent
- Context-aware navigation
- Better memory management
- Improved decision making
- Async operation

### FocusGroupAnalyzer
- Parallel analysis support
- Combined reporting
- Better error handling
- Progress tracking

## New Data Structures

### 1. Section Content
```python
section_links: Dict[str, str] = {
    '#section-id': 'Section content...',
    '#another-section': 'More content...'
}
```

### 2. Partial Results
```python
partial_report: Dict[str, Any] = {
    'completed_analyses': [...],
    'status': 'incomplete',
    'error': error_type,
    'timestamp': timestamp
}
```

## New Configuration Options

1. **Screenshot Settings**
   - Quality control
   - Directory management
   - Naming conventions

2. **Rate Limiting**
   - Delay configuration
   - Retry settings
   - Timeout values

3. **Template Options**
   - Role definitions
   - Experience levels
   - Context settings

## Future Enhancements

1. **Performance**
   - Request caching
   - Parallel processing
   - Resource optimization

2. **Analysis**
   - Sentiment analysis
   - Competitive analysis
   - A/B testing

3. **Resilience**
   - Proxy support
   - Advanced bot avoidance
   - CAPTCHA handling

4. **Reporting**
   - Interactive visualizations
   - Trend analysis
   - Comparative reports

[Previous sections from v1 remain unchanged...] 