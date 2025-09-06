from dataclasses import dataclass, asdict
from typing import List, Dict, Optional
import logging
import json
import os
from datetime import datetime
import yaml

from .persona import Persona
from ..llm.claude_client import RateLimitedLLM

logger = logging.getLogger(__name__)

@dataclass
class PersonaTemplate:
    role: str
    experience_level: str
    primary_goal: str
    context: str
    additional_details: Optional[Dict[str, str]] = None

    def to_dict(self) -> Dict:
        """Convert template to dictionary"""
        return {
            "template": {
                "role": self.role,
                "experience_level": self.experience_level,
                "primary_goal": self.primary_goal,
                "context": self.context,
                "additional_details": self.additional_details
            }
        }

class PersonaGenerator:
    def __init__(self, llm: RateLimitedLLM):
        self.llm = llm
        
    def generate_variations(self, template: PersonaTemplate, num_variations: int = 5) -> List[Persona]:
        """Generate variations of a base persona and save details to file"""
        logger.info(f"Generating {num_variations} persona variations")
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        try:
            # Generate personas using existing logic
            personas = self._generate_personas(template, num_variations)
            
            # Prepare output directory
            output_dir = "reports/personas"
            os.makedirs(output_dir, exist_ok=True)
            
            # Create descriptive filename
            sanitized_role = template.role.lower().replace(' ', '_')
            filename = f"{output_dir}/personas_{sanitized_role}_{timestamp}.json"
            
            # Prepare data for saving
            output_data = {
                "timestamp": timestamp,
                "input_template": template.to_dict(),
                "generated_personas": [
                    {
                        "name": p.name,
                        "interests": p.interests,
                        "needs": p.needs,
                        "goals": p.goals
                    } for p in personas
                ]
            }
            
            # Save to file
            with open(filename, 'w') as f:
                json.dump(output_data, f, indent=2)
                
            logger.info(f"Saved persona details to {filename}")
            return personas
            
        except Exception as e:
            logger.error(f"Error in persona generation: {str(e)}")
            raise
            
    def _generate_personas(self, template: PersonaTemplate, num_variations: int) -> List[Persona]:
        """Internal method to generate personas"""
        prompt = f"""Create {num_variations} distinct but related persona variations for:

        Role: {template.role}
        Experience Level: {template.experience_level}
        Primary Goal: {template.primary_goal}
        Context: {template.context}
        
        Additional Details:
        {template.additional_details if template.additional_details else 'None'}

        For each variation, provide:
        1. Name
        2. 5 specific interests related to their role and context
        3. 5 concrete needs they have
        4. 5 goals they want to achieve
        
        Format each persona as YAML, like this example (do not include the example in output):
        name: "John Smith"
        interests:
          - "Cloud architecture"
          - "DevOps practices"
        needs:
          - "Flexible work hours"
          - "Remote collaboration tools"
        goals:
          - "Find remote contract work"
          - "Build portfolio"
        """
        
        try:
            response = self.llm.invoke(prompt)
            personas = []
            
            # Clean and split YAML sections
            yaml_sections = []
            current_section = []
            
            for line in response.strip().split('\n'):
                if line.strip() == '---':
                    if current_section:
                        yaml_sections.append('\n'.join(current_section))
                        current_section = []
                else:
                    current_section.append(line)
            
            # Add the last section if it exists
            if current_section:
                yaml_sections.append('\n'.join(current_section))
            
            # Parse each cleaned section
            for section in yaml_sections:
                try:
                    # Skip empty sections
                    if not section.strip():
                        continue
                        
                    persona_data = yaml.safe_load(section)
                    if not persona_data or not isinstance(persona_data, dict):
                        logger.warning(f"Invalid persona data format: {section}")
                        continue
                        
                    # Validate required fields
                    required_fields = ['name', 'interests', 'needs', 'goals']
                    if not all(field in persona_data for field in required_fields):
                        logger.warning(f"Missing required fields in persona data: {persona_data}")
                        continue
                        
                    personas.append(Persona(
                        name=persona_data['name'],
                        interests=persona_data['interests'],
                        needs=persona_data['needs'],
                        goals=persona_data['goals']
                    ))
                    logger.info(f"Successfully parsed persona: {persona_data['name']}")
                    
                except Exception as e:
                    logger.error(f"Error parsing persona data section: {str(e)}\nSection:\n{section}")
                    
            if not personas:
                raise ValueError("No valid personas could be generated from the response")
                
            return personas
            
        except Exception as e:
            logger.error(f"Error generating personas: {str(e)}")
            raise 