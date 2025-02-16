from dataclasses import dataclass
from typing import List

@dataclass
class Persona:
    name: str
    interests: List[str]
    needs: List[str]
    goals: List[str] 