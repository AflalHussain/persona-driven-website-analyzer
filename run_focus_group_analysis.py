import os
import sys
import yaml
import json
import argparse
from dotenv import load_dotenv
from urllib.parse import urlparse
from datetime import datetime
import asyncio

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.models.persona import Persona
from src.agents.persona_agent import PersonaAgent
from src.utils.logger import setup_logging
from src.models.persona_generator import PersonaGenerator, PersonaTemplate
from src.agents.focus_group_analyzer import FocusGroupAnalyzer
from src.llm.claude_client import RateLimitedLLM

def load_persona(persona_name: str) -> Persona:
    """Load persona configuration from YAML file"""
    with open('config/personas.yaml', 'r') as f:
        personas = yaml.safe_load(f)
        
    if persona_name not in personas['personas']:
        raise ValueError(f"Persona {persona_name} not found in configuration")
        
    persona_config = personas['personas'][persona_name]
    return Persona(
        name=persona_config['name'],
        interests=persona_config['interests'],
        needs=persona_config['needs'],
        goals=persona_config['goals']
    )

async def main():
    parser = argparse.ArgumentParser(description='Run website analysis with personas')
    parser.add_argument('--url', type=str, required=True, help='The URL of the site to analyze')
    parser.add_argument('--persona', type=str, help='The name of the persona to use for analysis')
    parser.add_argument('--template', type=str, help='Path to persona template file for focus group')
    parser.add_argument('--variations', type=int, default=5, help='Number of persona variations for focus group')
    parser.add_argument('--max-pages', type=int, default=5, help='Maximum number of pages to analyze')
    
    args = parser.parse_args()
    
    load_dotenv()
    logger = setup_logging()
    
    try:
        if args.template:
            # Run focus group analysis
            with open(args.template, 'r') as f:
                template = yaml.safe_load(f)
            
            generator = PersonaGenerator(RateLimitedLLM(os.getenv("ANTHROPIC_API_KEY")))
            personas = generator.generate_variations(
                PersonaTemplate(**template),
                num_variations=args.variations
            )
            
            analyzer = FocusGroupAnalyzer(personas)
            report = await analyzer.analyze_website(args.url, max_pages=args.max_pages)
            
            output_file = f"reports/focus_group_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
        else:
            # Run single persona analysis
            persona = load_persona(args.persona)
            agent = PersonaAgent(persona)
            report = await agent.navigate(args.url, max_pages=args.max_pages)
            
            domain = urlparse(args.url).netloc.replace('www.', '')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"reports/{domain}_{persona.name.lower().replace(' ', '_')}_{timestamp}.json"
        
        os.makedirs('reports', exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
            
        logger.info(f"Analysis completed. Report saved to {output_file}")
        
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())