
import random
from typing import Dict, List, Optional
from core.logger import logger

class RLService:
    """
    Reinforcement Learning Service for selecting conversation personas.
    Uses an Epsilon-Greedy strategy to explore and exploit different styles.
    """
    
    def __init__(self):
        # Available personas and their base prompts
        self.personas = {
            "the_empathetic_friend": "You are a deeply empathetic friend. Focus on validation, emotional support, and active listening.",
            "the_humorous_friend": "You are a witty, humorous friend. Use lighthearted jokes and playfulness to lift the mood.",
            "the_direct_friend": "You are a direct, honest friend. Provide straightforward advice and practical perspectives.",
            "the_philosophical_friend": "You are a thoughtful, philosophical friend. Explore deeper meanings and offer existential wisdom.",
            "the_cheerleader_friend": "You are an ultra-supportive cheerleader. Focus on encouragement, positivity, and motivation."
        }
        
        # Epsilon for exploration (10% of the time we try a random persona)
        self.epsilon = 0.1
        
    async def select_persona(self, persona_stats: Dict[str, Dict]) -> str:
        """
        Selects the best persona using Epsilon-Greedy RL.
        persona_stats: { persona_name: { 'avg_score': float, 'count': int } }
        """
        # 1. Exploration: Randomly pick a persona
        if random.random() < self.epsilon or not persona_stats:
            persona = random.choice(list(self.personas.keys()))
            logger.info(f"RL: Exploring new persona: {persona}")
            return persona
            
        # 2. Exploitation: Pick the one with the highest average score
        best_persona = None
        highest_score = -float('inf')
        
        # We also want to ensure we don't just pick one that was lucky once
        # Simple weighted score: avg_score * (1 - 1/sqrt(count)) to favor more certain high scores
        for p_name, stats in persona_stats.items():
            if p_name not in self.personas:
                continue
            
            score = stats['avg_score']
            if score > highest_score:
                highest_score = score
                best_persona = p_name
                
        if not best_persona:
            best_persona = random.choice(list(self.personas.keys()))
            
        logger.info(f"RL: Exploiting best persona: {best_persona} (score: {highest_score:.2f})")
        return best_persona

    def get_persona_prompt(self, persona_name: str) -> str:
        """Returns the system prompt for a given persona."""
        return self.personas.get(persona_name, self.personas["the_empathetic_friend"])

    def format_experiences(self, experiences: List) -> str:
        """Formats successful past interactions as few-shot training examples."""
        if not experiences:
            return ""
            
        formatted = "\n--- LEARNED EXPERIENCES (High-Rated Past Interactions) ---\n"
        for exp in experiences:
            formatted += f"User: {exp.transcript}\n"
            formatted += f"AI (Successful Response): {exp.response_text}\n\n"
        
        formatted += "Follow the tone and success of these examples when responding.\n"
        return formatted

rl_service = RLService()
