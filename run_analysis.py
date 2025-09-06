import os
import sys
import yaml
import json
import argparse
from dotenv import load_dotenv
from urllib.parse import urlparse
from datetime import datetime

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.models.persona import Persona
from src.agents.persona_agent import PersonaAgent
from src.utils.logger import setup_logging

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

def main():
    parser = argparse.ArgumentParser(description='Run website analysis with a specified persona.')
    parser.add_argument('--url', type=str, required=True, help='The URL of the site to analyze')
    parser.add_argument('--persona', type=str, required=True, help='The name of the persona to use for analysis')
    parser.add_argument('--max-pages', type=int, default=5, help='Maximum number of pages to analyze')
    
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv()
    
    # Set up logging
    logger = setup_logging()
    logger.info(f"Running analysis for {args.persona} on {args.url}")
    
    try:
        # Load persona configuration
        persona = load_persona(args.persona)
        
        # Initialize agent
        agent = PersonaAgent(persona)
        
        # Extract domain from URL for filename
        domain = urlparse(args.url).netloc.replace('www.', '')
        
        # Get timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Start website analysis
        report = agent.navigate(args.url, max_pages=args.max_pages)
        
        # Save report with new filename format
        output_file = f"reports/{domain}_{persona.name.lower().replace(' ', '_')}_{timestamp}.json"
        os.makedirs('reports', exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
            
        logger.info(f"Analysis completed. Report saved to {output_file}")
        
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()