"""
Validation utilities for state fields.

This module provides common validators and utilities for validating
field values in StateModel instances.
"""

import re
from typing import Any, Callable


class ValidationError(Exception):
    """Exception raised when field validation fails."""
    pass


def create_email_validator() -> Callable[[str], str]:
    """Create an email validation function."""
    email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    
    def validate_email(value: str) -> str:
        if not isinstance(value, str):
            raise ValidationError("Email must be a string")
        
        value = value.strip()
        if not email_pattern.match(value):
            raise ValidationError("Invalid email format")
        
        return value
    
    return validate_email


def create_range_validator(min_val: float = None, max_val: float = None) -> Callable[[Any], Any]:
    """Create a numeric range validation function."""
    
    def validate_range(value: Any) -> Any:
        if isinstance(value, str):
            try:
                value = float(value)
            except ValueError:
                raise ValidationError(f"Cannot convert '{value}' to number")
        
        if not isinstance(value, (int, float)):
            raise ValidationError("Value must be a number")
        
        if min_val is not None and value < min_val:
            raise ValidationError(f"Value must be at least {min_val}")
        
        if max_val is not None and value > max_val:
            raise ValidationError(f"Value must be at most {max_val}")
        
        return value
    
    return validate_range


def create_length_validator(min_length: int = None, max_length: int = None) -> Callable[[str], str]:
    """Create a string length validation function."""
    
    def validate_length(value: str) -> str:
        if not isinstance(value, str):
            raise ValidationError("Value must be a string")
        
        length = len(value.strip())
        
        if min_length is not None and length < min_length:
            raise ValidationError(f"Value must be at least {min_length} characters long")
        
        if max_length is not None and length > max_length:
            raise ValidationError(f"Value must be at most {max_length} characters long")
        
        return value.strip()
    
    return validate_length


def create_regex_validator(pattern: str, error_message: str = "Invalid format") -> Callable[[str], str]:
    """Create a regex validation function."""
    compiled_pattern = re.compile(pattern)
    
    def validate_regex(value: str) -> str:
        if not isinstance(value, str):
            raise ValidationError("Value must be a string")
        
        if not compiled_pattern.match(value):
            raise ValidationError(error_message)
        
        return value
    
    return validate_regex


def create_choice_validator(choices: list) -> Callable[[Any], Any]:
    """Create a choice validation function."""
    
    def validate_choice(value: Any) -> Any:
        if value not in choices:
            raise ValidationError(f"Value must be one of: {', '.join(map(str, choices))}")
        
        return value
    
    return validate_choice
