"""
State management for structured LLM agents.

This module provides the StateModel base class and Field definition system
for creating declarative state schemas with validation and introspection.
"""

from dataclasses import dataclass, fields, asdict
from typing import Any, Dict, List, Optional, Callable, get_type_hints
import json
from .validation import ValidationError


class Field:
    """Field definition for StateModel attributes."""
    
    def __init__(
        self,
        required: bool = False,
        description: str = "",
        validator: Optional[Callable[[Any], Any]] = None,
        default: Any = None
    ):
        self.required = required
        self.description = description
        self.validator = validator
        self.default = default


class StateModelMeta(type):
    """Metaclass that adds schema introspection to StateModel classes."""
    
    def __new__(cls, name, bases, namespace, **kwargs):
        # Create the class
        new_class = super().__new__(cls, name, bases, namespace, **kwargs)
        
        # Add schema method
        def schema(cls_self):
            """Generate JSON schema for this state model."""
            schema_dict = {
                "type": "object",
                "properties": {},
                "required": []
            }
            
            # Get field info from _field_info if available, otherwise from dataclass fields
            if hasattr(cls_self, '_field_info'):
                for field_name, field_info in cls_self._field_info.items():
                    prop = {
                        "type": "string",  # Default to string for simplicity
                        "description": field_info.description
                    }
                    schema_dict["properties"][field_name] = prop
                    
                    if field_info.required:
                        schema_dict["required"].append(field_name)
            else:
                for field_obj in fields(cls_self):
                    field_info = getattr(cls_self, field_obj.name, Field())
                    if isinstance(field_info, Field):
                        prop = {
                            "type": cls_self._python_type_to_json_type(field_obj.type),
                            "description": field_info.description
                        }
                        schema_dict["properties"][field_obj.name] = prop
                        
                        if field_info.required:
                            schema_dict["required"].append(field_obj.name)
            
            return schema_dict
        
        new_class.schema = classmethod(schema)
        return new_class
    
    @staticmethod
    def _python_type_to_json_type(python_type):
        """Convert Python type to JSON schema type."""
        type_mapping = {
            str: "string",
            int: "integer", 
            float: "number",
            bool: "boolean",
            list: "array",
            dict: "object"
        }
        return type_mapping.get(python_type, "string")


@dataclass
class StateModel(metaclass=StateModelMeta):
    """Base class for structured state models."""
    
    def set_field(self, name: str, value: Any) -> None:
        """Set a field value with validation."""
        if not hasattr(self, name):
            raise ValidationError(f"Field '{name}' does not exist")
        
        # Get field info
        field_info = self.get_field_info(name)
        
        # Apply validator if present
        if field_info and field_info.validator:
            try:
                value = field_info.validator(value)
            except Exception as e:
                raise ValidationError(f"Validation failed for field '{name}': {str(e)}")
        
        # Type coercion
        field_type = self._get_field_type(name)
        if field_type and value is not None:
            try:
                if field_type == int and isinstance(value, str):
                    value = int(value)
                elif field_type == float and isinstance(value, (str, int)):
                    value = float(value)
                elif field_type == bool and isinstance(value, str):
                    value = value.lower() in ('true', '1', 'yes', 'on')
            except (ValueError, TypeError):
                raise ValidationError(f"Cannot convert '{value}' to {field_type.__name__}")
        
        setattr(self, name, value)
    
    def validate(self) -> List[str]:
        """Validate the current state and return list of missing/invalid fields."""
        missing = []
        
        # Use _field_info if available, otherwise fall back to dataclass fields
        if hasattr(self, '_field_info'):
            for field_name, field_info in self._field_info.items():
                if field_info.required:
                    current_value = getattr(self, field_name)
                    if current_value is None or current_value == "":
                        missing.append(field_name)
        else:
            for field_obj in fields(self):
                field_info = self.get_field_info(field_obj.name)
                current_value = getattr(self, field_obj.name)
                
                # Check required fields
                if field_info and field_info.required:
                    if current_value is None or current_value == "":
                        missing.append(field_obj.name)
        
        return missing
    
    def snapshot(self) -> Dict[str, Any]:
        """Return a dictionary snapshot of the current state."""
        return asdict(self)
    
    def clear(self) -> None:
        """Reset all fields to their default values."""
        for field_obj in fields(self):
            field_info = self.get_field_info(field_obj.name)
            default_value = field_info.default if field_info else None
            setattr(self, field_obj.name, default_value)
    
    def get_field_info(self, name: str) -> Optional[Field]:
        """Get field information for a given field name."""
        # Check if class has _field_info dictionary
        if hasattr(self, '_field_info'):
            return self._field_info.get(name)
        
        # Fall back to checking class attributes
        field_info = getattr(self.__class__, name, None)
        return field_info if isinstance(field_info, Field) else None
    
    def _get_field_type(self, name: str):
        """Get the type annotation for a field."""
        type_hints = get_type_hints(self.__class__)
        return type_hints.get(name)
    
    def __str__(self) -> str:
        """String representation showing current state."""
        lines = [f"{self.__class__.__name__} State:"]
        for field_obj in fields(self):
            value = getattr(self, field_obj.name)
            field_info = self.get_field_info(field_obj.name)
            required_marker = "✓" if field_info and field_info.required else "○"
            display_value = value if value not in [None, ""] else "(empty)"
            lines.append(f"  {required_marker} {field_obj.name}: {display_value}")
        return "\n".join(lines)
