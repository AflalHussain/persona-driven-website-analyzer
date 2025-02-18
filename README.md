# Automated Website Analysis Agent

## Overview

The Automated Website Analysis Agent is designed to analyze websites from multiple user perspectives. It supports both single persona analysis and virtual focus group analysis with multiple generated persona variations.

## Features

* Single Persona Analysis: Analyze websites from a specific persona's perspective
* Virtual Focus Group Analysis: Generate and analyze with multiple persona variations
* Autonomous Website Exploration: The agent autonomously navigates websites
* Combined Textual and Visual Analysis: Analyzes both content and layout
* Detailed Report Generation: Generates comprehensive individual and group reports
* REST API: Access all functionality through HTTP endpoints
* Asynchronous Processing: Long-running analyses are handled asynchronously


## Requirements

* Python 3.9 or higher
* Required libraries (install via `pip install -r requirements.txt`):
  - playwright
  - httpx
  - PyYAML
  - python-dotenv
  - Pillow
  - logging
  - fastapi
  - uvicorn

## Installation

1. Clone the repository:
```bash
git clone https://github.com/AflalHussain/Persona-driven-web-crawler-and-analyzer.git
```

2. Install the required libraries:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
export ANTHROPIC_API_KEY=<your_api_key>
```

## Usage
### 1. REST API

Start the API server:
```bash
uvicorn src.api.fast_api:app --host 0.0.0.0 --port 8000 --reload
```

#### API Endpoints:

1. Start Single Persona Analysis:
```bash
curl -X POST "http://localhost:8000/analyze/single" \
     -H "Content-Type: application/json" \
     -d '{
           "url": "https://www.w3schools.com",
           "persona_template": {
             "role": "Developer",
             "experience_level": "Senior",
             "primary_goal": "Find contract work",
             "context": "Looking for remote opportunities",
             "additional_details": {
               "preferred_stack": "Full-stack",
               "availability": "Part-time"
             }
           },
           "max_pages": 3
         }'
```

2. Start Focus Group Analysis:
```bash
curl -X POST "http://localhost:8000/analyze/focus-group" \
     -H "Content-Type: application/json" \
     -d '{
           "url": "https://www.w3schools.com",
           "persona_template": {
             "role": "Developer",
             "experience_level": "Senior",
             "primary_goal": "Find contract work",
             "context": "Looking for remote opportunities",
             "additional_details": {
               "preferred_stack": "Full-stack",
               "availability": "Part-time"
             }
           },
           "num_variations": 3,
           "max_pages": 3
         }'
```

3. Check Analysis Status:
```bash
curl "http://localhost:8000/analysis/{task_id}"
```

4. Health Check:
```bash
curl "http://localhost:8000/health"
```
### 2. Command Line Interface
#### 2.1. Single Persona Analysis

Analyze a website from a single predefined persona's perspective:

```bash
python run_analysis.py --url https://databricks.com --persona data_engineer
```

Options:
- `--url`: Target website URL (required)
- `--persona`: Name of predefined persona (required)
- `--max-pages`: Maximum pages to analyze (default: 5)

#### 2.2. Focus Group Analysis

Run analysis with multiple generated persona variations:

1. Create a persona template file (e.g., `templates/developer_template.yaml`):
```yaml
role: "Developer"
experience_level: "Senior"
primary_goal: "Find contract work"
context: "Looking for remote opportunities"
additional_details:
  preferred_stack: "Full-stack"
  availability: "Part-time"
```

2. Run the focus group analysis:
```bash
python run_focus_group_analysis.py --url  https://www.w3schools.com/ --template templates/developer_template.yaml --variations 2
```

Options:
- `--url`: Target website URL (required)
- `--template`: Path to persona template file (required)
- `--variations`: Number of persona variations to generate (default: 5)
- `--max-pages`: Maximum pages to analyze per persona (default: 5)

### Output Files

The tool generates several types of reports:

1. API Analysis Reports:
   ```
   reports/api/{task_id}.json              # Successful analysis results
   reports/api/{task_id}_error.json        # Error information for failed analyses
   ```

2. CLI Reports:
   1. Individual Analysis Reports:
   ```
   reports/{domain}_{persona_name}_{timestamp}.json
   ```

   2. Focus Group Reports:
   ```
   reports/focus_group_analysis_{timestamp}.json
   reports/focus_group/{persona_name}_{timestamp}.json
   ```

   3. Generated Personas:
   ```
   reports/personas/personas_{role}_{timestamp}.json
   ```

## Example Templates

### Developer Template
```yaml
role: "Developer"
experience_level: "Senior"
primary_goal: "Find contract work"
context: "Looking for remote opportunities"
additional_details:
  preferred_stack: "Full-stack"
  availability: "Part-time"
```

### Business Analyst Template
```yaml
role: "Business Analyst"
experience_level: "Mid-level"
primary_goal: "Evaluate analytics tools"
context: "Working in fintech"
additional_details:
  industry_focus: "Financial services"
  team_size: "Small team"
```

## Report Structure

1. Focus Group Analysis Report:
```json
{
  "url": "https://example.com",
  "timestamp": "20240217_143000",
  "num_personas": 5,
  "common_patterns": {
    "likes": [...],
    "dislikes": [...],
    "expectations": [...]
  },
  "individual_reports": [...],
  "summary": "..."
}
```

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request with your changes.

## Contact

For any questions or issues, please contact [aflalibnhussain@gmail.com].

---

This README provides comprehensive guidance for using both single persona and focus group analysis features. Adjust the content as necessary to fit your project's specifics.