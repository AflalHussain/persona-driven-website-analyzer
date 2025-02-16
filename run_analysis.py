import os
import sys
import yaml
import json
import argparse
from dotenv import load_dotenv

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

def run_analysis(site_url: str, persona_name: str):
    # Load environment variables
    load_dotenv()
    
    # Set up logging
    logger = setup_logging()
    logger.info(f"Running analysis for {persona_name} on {site_url}") 
    try:
        # Load persona configuration
        persona = load_persona(persona_name)
        
        # Initialize agent
        agent = PersonaAgent(persona)
        
        # Start website analysis
        report = agent.navigate(site_url, max_pages=2)
        
        # Save report
        output_file = f"reports/analysis_report_{persona.name.lower().replace(' ', '_')}.json"
        os.makedirs('reports', exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
            
        logger.info(f"Analysis completed. Report saved to {output_file}")
        
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run website analysis with a specified persona.')
    parser.add_argument('site_url', type=str, help='The URL of the site to analyze')
    parser.add_argument('persona_name', type=str, help='The name of the persona to use for analysis')
    
    args = parser.parse_args()
    run_analysis(args.site_url, args.persona_name)