website-analyzer/
├── config/
│   ├── __init__.py
│   ├── logging_config.yaml        # Logging configuration
│   └── personas.yaml             # Predefined personas
├── src/
│   ├── __init__.py
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── persona_agent.py      # PersonaAgent class
│   │   └── base_agent.py         # Base agent class with common functionality
│   ├── crawlers/
│   │   ├── __init__.py
│   │   └── web_crawler.py        # WebCrawler class
│   ├── models/
│   │   ├── __init__.py
│   │   ├── persona.py            # Persona dataclass
│   │   ├── analysis.py           # PageAnalysis and related dataclasses
│   │   └── report.py             # Report generation models
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── logger.py             # Logging setup
│   │   ├── rate_limiter.py       # Rate limiting functionality
│   │   └── url_validator.py      # URL validation utilities
│   └── llm/
│       ├── __init__.py
│       └── claude_client.py      # Claude API client
├── tests/
│   ├── __init__.py
│   ├── test_persona_agent.py
│   ├── test_web_crawler.py
│   └── test_url_validator.py
├── examples/
│   ├── basic_analysis.py
│   └── custom_persona.py
├── reports/                      # Directory for generated reports
├── logs/                         # Directory for log files
├── requirements.txt
├── setup.py
└── README.md 