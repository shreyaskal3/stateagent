"""
CRUD tools for state manipulation.

This module provides the generic tools that LLMs can use to interact with
StateModel instances through function calling.
"""

from typing import Dict, Any, List, Callable
import json
from .state import StateModel


class ToolRegistry:
    """Registry for CRUD tools that operate on StateModel instances."""
    
    @staticmethod
    def get_tools_schema(state_cls: type) -> List[Dict[str, Any]]:
        """Generate OpenAI function calling schema for CRUD tools."""
        # Get valid field names from the state class
        field_names = [f.name for f in state_cls.__dataclass_fields__.values()]
        
        return [
            {
                "type": "function",
                "function": {
                    "name": "set_field",
                    "description": "Set or update a field in the state",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "field_name": {
                                "type": "string",
                                "enum": field_names,
                                "description": "Name of the field to set"
                            },
                            "value": {
                                "type": "string",
                                "description": "Value to set for the field"
                            }
                        },
                        "required": ["field_name", "value"]
                    }
                }
            },
            {
                "type": "function", 
                "function": {
                    "name": "validate_state",
                    "description": "Check if the current state is complete and valid",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_state",
                    "description": "Get the current state snapshot",
                    "parameters": {
                        "type": "object", 
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "clear_state",
                    "description": "Reset all fields to their default values",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            }
        ]


def apply_tool(tool_call: Dict[str, Any], state: StateModel) -> Dict[str, Any]:
    """Apply a tool call to a state instance and return the result."""
    function_name = tool_call.get("name")
    arguments = tool_call.get("arguments", {})
    
    try:
        if function_name == "set_field":
            field_name = arguments.get("field_name")
            value = arguments.get("value")
            
            if not field_name:
                return {"error": "field_name is required"}
            
            state.set_field(field_name, value)
            return {
                "success": True,
                "message": f"Set {field_name} = {value}",
                "state": state.snapshot()
            }
        
        elif function_name == "validate_state":
            missing_fields = state.validate()
            if missing_fields:
                return {
                    "valid": False,
                    "missing_fields": missing_fields,
                    "message": f"Missing required fields: {', '.join(missing_fields)}"
                }
            else:
                return {
                    "valid": True,
                    "message": "State is complete and valid",
                    "state": state.snapshot()
                }
        
        elif function_name == "get_state":
            return {
                "state": state.snapshot(),
                "message": "Current state retrieved"
            }
        
        elif function_name == "clear_state":
            state.clear()
            return {
                "success": True,
                "message": "State cleared",
                "state": state.snapshot()
            }
        
        else:
            return {"error": f"Unknown function: {function_name}"}
    
    except Exception as e:
        return {"error": f"Tool execution failed: {str(e)}"}
