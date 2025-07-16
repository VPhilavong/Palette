import os
from typing import Dict, Optional
from openai import OpenAI
import anthropic

from .prompts import UIPromptBuilder

class UIGenerator:
    """Core UI generation logic using LLM APIs"""
    
    def __init__(self, model: str = "gpt-4"):
        self.model = model
        self.prompt_builder = UIPromptBuilder()
        
        # Initialize API clients
        self.openai_client = None
        self.anthropic_client = None
        
        if os.getenv("OPENAI_API_KEY"):
            self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        if os.getenv("ANTHROPIC_API_KEY"):
            self.anthropic_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    
    def generate_component(self, prompt: str, context: Dict) -> str:
        """Generate a React component from a prompt and project context"""
        
        # Build UI-focused system prompt
        system_prompt = self.prompt_builder.build_ui_system_prompt(context)
        user_prompt = self.prompt_builder.build_user_prompt(prompt, context)
        
        # Choose API based on model
        if self.model.startswith("gpt"):
            return self._generate_with_openai(system_prompt, user_prompt)
        elif self.model.startswith("claude"):
            return self._generate_with_anthropic(system_prompt, user_prompt)
        else:
            raise ValueError(f"Unsupported model: {self.model}")
    
    def _generate_with_openai(self, system_prompt: str, user_prompt: str) -> str:
        """Generate component using OpenAI API"""
        
        if not self.openai_client:
            raise ValueError("OpenAI API key not configured")
        
        try:
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=2000,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")
    
    def _generate_with_anthropic(self, system_prompt: str, user_prompt: str) -> str:
        """Generate component using Anthropic API"""
        
        if not self.anthropic_client:
            raise ValueError("Anthropic API key not configured")
        
        try:
            response = self.anthropic_client.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=0.7,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )
            
            return response.content[0].text.strip()
            
        except Exception as e:
            raise Exception(f"Anthropic API error: {str(e)}")
    
    def clean_response(self, response: str) -> str:
        """Clean and extract code from LLM response"""
        
        # Remove markdown code blocks if present
        if "```" in response:
            # Extract content between first pair of triple backticks
            start_marker = response.find("```")
            if start_marker != -1:
                # Skip the opening ```tsx or ```javascript
                start_content = response.find("\n", start_marker) + 1
                end_marker = response.find("```", start_content)
                if end_marker != -1:
                    response = response[start_content:end_marker].strip()
        
        return response
    
    def validate_component(self, code: str) -> bool:
        """Basic validation of generated component code"""
        
        # Check for basic React component structure
        required_patterns = [
            "export",  # Should export the component
            "return",  # Should have a return statement
            "<",       # Should contain JSX
        ]
        
        for pattern in required_patterns:
            if pattern not in code:
                return False
        
        # Check for common syntax issues
        if code.count("(") != code.count(")"):
            return False
        
        if code.count("{") != code.count("}"):
            return False
        
        return True