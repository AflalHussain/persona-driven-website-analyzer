import os
import sys
import json
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models.persona import Persona
from src.agents.persona_agent import PersonaAgent
from src.utils.logger import setup_logging

def create_custom_persona() -> Persona:
    """Create a custom persona interactively"""
    print("\nCreate a Custom Persona")
    print("-" * 20)
    
    name = input("Enter persona name: ")
    
    print("\nEnter interests (one per line, empty line to finish):")
    interests = []
    while True:
        interest = input("> ")
        if not interest:
            break
        interests.append(interest)
    
    print("\nEnter needs (one per line, empty line to finish):")
    needs = []
    while True:
        need = input("> ")
        if not need:
            break
        needs.append(need)
    
    print("\nEnter goals (one per line, empty line to finish):")
    goals = []
    while True:
        goal = input("> ")
        if not goal:
            break
        goals.append(goal)
    
    return Persona(
        name=name,
        interests=interests,
        needs=needs,
        goals=goals
    )

def main():
    load_dotenv()
    logger = setup_logging()
    
    try:
        # Create custom persona
        persona = create_custom_persona()
        
        # Get target website
        website = input("\nEnter website URL to analyze: ")
        max_pages = int(input("Maximum number of pages to analyze (default 5): ") or "5")
        
        # Initialize agent and run analysis
        agent = PersonaAgent(persona)
        report = agent.navigate(website, max_pages=max_pages)
        
        # Save report
        output_file = f"reports/custom_analysis_{persona.name.lower().replace(' ', '_')}.json"
        os.makedirs('reports', exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
            
        logger.info(f"Analysis completed. Report saved to {output_file}")
        
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 