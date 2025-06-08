"""
LLM adapter interfaces and implementations.

This module provides the base LLMAdapter class and concrete implementations
for different LLM providers like OpenAI.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import json
import os


class LLMAdapter(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    def chat(self, messages: List[Dict[str, str]], tools: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """Send a chat request and return the response."""
        pass
    
    @abstractmethod
    def extract_function_calls(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract function calls from the LLM response."""
        pass


class OpenAIAdapter(LLMAdapter):
    """OpenAI API adapter with function calling support."""
    
    def __init__(self, model: str = "gpt-4o-mini", api_key: Optional[str] = None):
        self.model = model
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable.")
        
        try:
            import openai
            self.client = openai.OpenAI(api_key=self.api_key)
        except ImportError:
            raise ImportError("openai package is required. Install with: pip install openai")
    
    def chat(self, messages: List[Dict[str, str]], tools: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """Send a chat request to OpenAI API."""
        try:
            kwargs = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.1
            }
            
            if tools:
                kwargs["tools"] = tools
                kwargs["tool_choice"] = "auto"
            
            response = self.client.chat.completions.create(**kwargs)
            
            return {
                "content": response.choices[0].message.content,
                "tool_calls": response.choices[0].message.tool_calls,
                "finish_reason": response.choices[0].finish_reason
            }
        
        except Exception as e:
            return {
                "error": f"OpenAI API error: {str(e)}",
                "content": None,
                "tool_calls": None
            }
    
    def extract_function_calls(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract function calls from OpenAI response."""
        if response.get("error"):
            return []
        
        tool_calls = response.get("tool_calls", [])
        if not tool_calls:
            return []
        
        function_calls = []
        for tool_call in tool_calls:
            if tool_call.type == "function":
                try:
                    arguments = json.loads(tool_call.function.arguments)
                    function_calls.append({
                        "name": tool_call.function.name,
                        "arguments": arguments
                    })
                except json.JSONDecodeError:
                    # Handle malformed JSON
                    continue
        
        return function_calls


class MockLLMAdapter(LLMAdapter):
    """Mock LLM adapter for testing purposes."""
    
    def __init__(self, responses: List[Dict[str, Any]] = None):
        self.responses = responses or []
        self.call_count = 0
    
    def chat(self, messages: List[Dict[str, str]], tools: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """Return a mock response."""
        if self.call_count < len(self.responses):
            response = self.responses[self.call_count]
            self.call_count += 1
            return response
        
        return {
            "content": "Mock response",
            "tool_calls": None,
            "finish_reason": "stop"
        }
    
    def extract_function_calls(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract function calls from mock response."""
        return response.get("function_calls", [])
