"""
LLM Structured Agent - A library for building reliable, state-driven LLM workflows.

This library implements the State+CRUD pattern for LLM interactions, providing
deterministic control flow and structured data collection through conversational interfaces.
"""

from .core.state import StateModel, Field
from .core.agent import StructuredAgent
from .core.llm import LLMAdapter, OpenAIAdapter
from .core.validation import (
    ValidationError,
    create_email_validator,
    create_range_validator,
    create_length_validator,
    create_regex_validator,
    create_choice_validator
)
from .core.tools import ToolRegistry, apply_tool

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

__all__ = [
    "StateModel",
    "Field", 
    "StructuredAgent",
    "LLMAdapter",
    "OpenAIAdapter",
    "ValidationError",
    "create_email_validator",
    "create_range_validator", 
    "create_length_validator",
    "create_regex_validator",
    "create_choice_validator",
    "ToolRegistry",
    "apply_tool"
]
