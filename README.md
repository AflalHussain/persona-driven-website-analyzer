# Automated Website Analysis Agent
## Overview

The Automated Website Analysis Agent is designed to analyze websites from the perspective of defined user personas. It provides detailed reports on the user experience, focusing on both textual and visual elements of the website.

## Features

* Persona-Driven Navigation: The agent navigates websites based on the interests, needs, and goals of a specified persona.
* Autonomous Website Exploration: The agent autonomously clicks links and buttons, mimicking human behavior.
* Combined Textual and Visual Analysis: The agent analyzes both the textual content and visual layout of each webpage.
* Detailed Report Generation: The agent generates comprehensive reports documenting the persona's journey through the website.

## Requirements

* Python 3.9 or higher
* Required libraries:
- playwright
- httpx
- PyYAML
- python-dotenv
- Pillow
- logging

## Installation

Clone the repository:

```bash
git clone https://github.com/your-repo/automated-website-analysis-agent.git
```

Install the required libraries:

```bash
pip install -r requirements.txt
```

Set up environment variables:

export ANTHROPIC_API_KEY=<your_api_key>

## Usage

### Example Websites for Testing

1. **Data/Analytics Platforms:**
   - Databricks (https://databricks.com)
   - Snowflake (https://snowflake.com)
   - Tableau (https://tableau.com)

2. **Cloud Services:**
   - AWS Analytics (https://aws.amazon.com/analytics)
   - Azure Data Services (https://azure.microsoft.com/solutions/data-platform)
   - Google Cloud Analytics (https://cloud.google.com/solutions/smart-analytics)

3. **Business Intelligence Tools:**
   - Power BI (https://powerbi.microsoft.com)
   - Looker (https://looker.com)
   - Sisense (https://sisense.com)

### Available Personas

1. **Data Engineer Dave**
   ```yaml
   interests:
     - Data Engineering
     - Machine Learning
     - Big Data Processing
     - Cloud Architecture
     - Data Pipelines
   needs:
     - Technical documentation
     - Platform capabilities
     - Integration details
     - Pricing information
     - Performance benchmarks
   goals:
     - Evaluate data processing capabilities
     - Understand MLOps features
     - Compare pricing tiers
     - Find implementation examples
     - Access technical specifications
   ```

2. **Business Analyst Bob**
   ```yaml
   interests:
     - Business Intelligence
     - Data Analytics
     - Market Research
     - Reporting Tools
     - Data-Driven Decision Making
   needs:
     - Dashboard tools
     - Reporting capabilities
     - Data integration solutions
     - User-friendly interfaces
     - Training resources
   goals:
     - Generate actionable insights
     - Create comprehensive reports
     - Analyze market trends
     - Support strategic planning
     - Improve operational efficiency
   ```

### Example Analysis Commands

1. Analyze Databricks from Data Engineer perspective:
```bash
python run_analysis --url https://databricks.com --persona data_engineer
```

2. Analyze Tableau from Business Analyst perspective:
```bash
python run_analysis --url https://tableau.com --persona business_analyst
```

3. Custom analysis of any website:
```bash
custom-analysis
# Follow prompts to create persona and enter website URL
```

### Sample Analysis Scenarios

1. **Technical Platform Evaluation:**
   ```bash
   python run_analysis --url https://databricks.com --persona data_engineer --max-pages 10
   ```
   This will analyze Databricks' technical capabilities, documentation, and implementation details.

2. **BI Tool Assessment:**
   ```bash
   python run_analysis --url https://powerbi.microsoft.com --persona business_analyst --max-pages 8
   ```
   This will evaluate Power BI's reporting capabilities, user interface, and business features.

## Report Generation
The agent generates a report in JSON format, saved in the reports directory. The report includes:
* Summary of the analysis
* Likes and dislikes
* Click reasons
* Next expectations
* Overall impression
* Visual analysis

## Logging
The agent uses the logging module to log its activities. Logs are saved in the console and can be redirected to a file if needed.

## Contributing
Contributions are welcome! Please fork the repository and submit a pull request with your changes.


## Contact
For any questions or issues, please contact [aflalibnhussain@gmail.com].
---
This README provides a comprehensive guide to setting up and using the Automated Website Analysis Agent. Adjust the content as necessary to fit your project's specifics.