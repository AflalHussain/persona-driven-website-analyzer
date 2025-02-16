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

Running the Analysis

To run the analysis, use the run_analysis.py script. You can specify the site URL and persona name as command-line arguments.
Example:

```bash
python run_analysis.py https://example.com  persona1
```

## Available Personas
You can define personas in the config/personas.yaml file. Each persona should include:

* Name
* Interests
* Needs
* Goals

Example of a persona definition:

```yaml
Custom Personas
You can also create custom personas using the custom_persona.py script. This allows you to define a persona interactively.

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