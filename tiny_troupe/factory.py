from typing import List, Optional, Dict
import json
from .tiny_person import TinyPerson

class TinyPersonFactory:
    def __init__(self, llm_client):
        self.llm_client = llm_client
        self.conversation_history = []
        
    def should_end_conversation(self, response: str) -> bool:
        """
        Analyze the response to determine if conversation should end.
        
        Args:
            response: The last response from the tiny person
            
        Returns:
            bool: True if conversation should end, False otherwise
        """
        # Keywords indicating conversation completion
        end_indicators = [
            "thank you for your time",
            "goodbye",
            "that's all",
            "i have nothing more to add",
            "this concludes",
            "end of conversation"
        ]
        
        # Check for conclusive statements
        response_lower = response.lower()
        if any(indicator in response_lower for indicator in end_indicators):
            return True
            
        # Check for question answering completion
        if "?" not in response and len(self.conversation_history) > 3:
            last_responses = [msg["content"].lower() for msg in self.conversation_history[-3:]]
            if all(len(resp) < 50 for resp in last_responses):
                return True
                
        return False

    def create_tiny_person(self, 
                          persona: str,
                          name: Optional[str] = None,
                          context: Optional[str] = None) -> TinyPerson:
        """
        Create a new tiny person with the given persona.
        
        Args:
            persona: Description of the tiny person's background and traits
            name: Optional name for the tiny person
            context: Optional additional context about the scenario
            
        Returns:
            TinyPerson: A new tiny person instance
        """
        system_prompt = f"""You are roleplaying as a person with the following traits:
{persona}

Your responses should always stay in character and reflect your background and personality.
"""
        if context:
            system_prompt += f"\nContext: {context}"
            
        return TinyPerson(
            llm_client=self.llm_client,
            system_prompt=system_prompt,
            name=name,
            factory=self
        )
        
    def process_response(self, response: str) -> Dict:
        """
        Process a response and track conversation history.
        
        Args:
            response: The response from the tiny person
            
        Returns:
            Dict with processed response and whether conversation should end
        """
        self.conversation_history.append({
            "role": "assistant",
            "content": response
        })
        
        should_end = self.should_end_conversation(response)
        
        return {
            "response": response,
            "should_end": should_end
        }