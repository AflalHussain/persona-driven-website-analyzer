import os
import sys
import yaml
import json
from dotenv import load_dotenv

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models.persona import Persona
from src.agents.persona_agent import PersonaAgent
from src.utils.logger import setup_logging

def load_persona(persona_name: str) -> Persona:
    """Load persona configuration from YAML file"""
    with open('../config/personas.yaml', 'r') as f:
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
    # Load environment variables
    load_dotenv()
    
    # Set up logging
    logger = setup_logging()
    
    try:
        # Load persona configuration
        persona = load_persona('data_engineer')
        
        # Initialize agent
        agent = PersonaAgent(persona)
        
        # Start website analysis
        report = agent.navigate('https://databricks.com', max_pages=5)
        
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
    main() 