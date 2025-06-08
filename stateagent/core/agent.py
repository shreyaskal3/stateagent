"""
Main orchestration agent for structured LLM interactions.

This module provides the StructuredAgent class that manages the conversation
loop between the LLM, state updates, and user interactions.
"""

from typing import Dict, Any, List, Optional, Callable
import json
from .state import StateModel
from .llm import LLMAdapter
from .tools import ToolRegistry, apply_tool


class StructuredAgent:
    """Main agent that orchestrates structured LLM conversations."""
    
    def __init__(
        self,
        state_cls: type,
        llm: LLMAdapter,
        hooks: Optional[Dict[str, Callable]] = None,
        max_turns: int = 20,
        system_prompt: Optional[str] = None
    ):
        self.state_cls = state_cls
        self.state = state_cls()
        self.llm = llm
        self.hooks = hooks or {}
        self.max_turns = max_turns
        self.system_prompt = system_prompt or self._default_system_prompt()
        self.conversation_history = []
    
    def _default_system_prompt(self) -> str:
        """Generate default system prompt based on state schema."""
        field_descriptions = []
        
        # Check if class has _field_info dictionary
        if hasattr(self.state_cls, '_field_info'):
            for field_name, field_info in self.state_cls._field_info.items():
                required = "required" if field_info.required else "optional"
                field_descriptions.append(f"- {field_name} ({required}): {field_info.description}")
        else:
            for field_obj in self.state_cls.__dataclass_fields__.values():
                field_info = getattr(self.state_cls, field_obj.name, None)
                if hasattr(field_info, 'description') and field_info.description:
                    required = "required" if getattr(field_info, 'required', False) else "optional"
                    field_descriptions.append(f"- {field_obj.name} ({required}): {field_info.description}")
        
        fields_text = "\n".join(field_descriptions) if field_descriptions else "No field descriptions available."
        
        return f"""You are a helpful assistant that collects structured information through conversation.

Your goal is to gather the following information:
{fields_text}

You have access to these tools:
- set_field(field_name, value): Update a field with a value
- validate_state(): Check if all required fields are complete
- get_state(): View current state
- clear_state(): Reset all fields

Guidelines:
1. Be conversational and friendly
2. Ask for missing required fields one at a time
3. Use set_field() to store information as you collect it
4. Use validate_state() to check completeness
5. Confirm with the user before finalizing
6. Only ask for information that isn't already provided

Start by greeting the user and explaining what information you need to collect."""
    
    def _build_messages(self, user_input: str = "") -> List[Dict[str, str]]:
        """Build the message list for the LLM."""
        messages = [{"role": "system", "content": self.system_prompt}]
        
        # Add conversation history
        messages.extend(self.conversation_history)
        
        # Add current state context
        state_summary = self._format_state_summary()
        if state_summary:
            messages.append({
                "role": "system", 
                "content": f"Current state:\n{state_summary}\n\nAfter each user message, you MUST check what information is still missing using validate_state() and ask for it."
            })
        
        # Add user input if provided
        if user_input.strip():
            messages.append({"role": "user", "content": user_input})
        
        return messages
    
    def _format_state_summary(self) -> str:
        """Format current state for display."""
        lines = []
        for field_obj in self.state_cls.__dataclass_fields__.values():
            value = getattr(self.state, field_obj.name)
            field_info = self.state.get_field_info(field_obj.name)
            
            if field_info and field_info.required:
                status = "✓" if value not in [None, ""] else "✗"
            else:
                status = "○"
            
            display_value = value if value not in [None, ""] else "(empty)"
            lines.append(f"{status} {field_obj.name}: {display_value}")
        
        return "\n".join(lines)
    
    def process_single_turn(self, user_input: str) -> Dict[str, Any]:
        """Process a single turn of conversation."""
        # Build messages
        messages = self._build_messages(user_input)
        
        # Get tools schema
        tools = ToolRegistry.get_tools_schema(self.state_cls)
        
        # Call LLM
        response = self.llm.chat(messages, tools)
        
        if response.get("error"):
            return {
                "error": response["error"],
                "complete": False
            }
        
        # Extract and execute function calls
        function_calls = self.llm.extract_function_calls(response)
        tool_results = []
        
        for call in function_calls:
            result = apply_tool(call, self.state)
            tool_results.append(result)
            
            # Trigger hooks
            if call["name"] == "set_field" and "on_field_set" in self.hooks:
                self.hooks["on_field_set"](self.state, call["arguments"]["field_name"])
            
            # If the model called validate_state, check if we're complete
            if call["name"] == "validate_state":
                if result.get("valid", False) and "on_submit" in self.hooks:
                    self.hooks["on_submit"](self.state)
        
        # Update conversation history
        self.conversation_history.append({"role": "user", "content": user_input})
        if response.get("content"):
            self.conversation_history.append({"role": "assistant", "content": response["content"]})
        
        # Check if state is complete
        missing_fields = self.state.validate()
        is_complete = len(missing_fields) == 0
        
        # If no tool calls were made but we have a response, make sure we follow up
        if not function_calls and response.get("content") and not is_complete:
            # Force a validate_state call to ensure we keep the conversation going
            validate_result = apply_tool({"name": "validate_state", "arguments": {}}, self.state)
            tool_results.append(validate_result)
        
        return {
            "message": response.get("content", ""),
            "tool_results": tool_results,
            "state": self.state.snapshot(),
            "missing_fields": missing_fields,
            "complete": is_complete,
            "error": None
        }
    
    def run_chat(self, io_fn: Callable[[str], str] = input, print_fn: Callable[[str], None] = print):
        """Run an interactive chat session."""
        print_fn("🤖 " + self.system_prompt.split('\n')[0])
        print_fn()
        
        # Start with an initial message from the assistant
        initial_result = self.process_single_turn("")
        if initial_result.get("message"):
            print_fn(f"🤖 {initial_result['message']}")
        
        for turn in range(self.max_turns):
            try:
                # Get user input
                user_input = io_fn("👤 ")
                if not user_input.strip():
                    continue
                
                # Process turn
                result = self.process_single_turn(user_input)
                
                if result.get("error"):
                    print_fn(f"❌ Error: {result['error']}")
                    continue
                
                # Show tool results (state updates)
                if result["tool_results"]:
                    for tool_result in result["tool_results"]:
                        if tool_result.get("success"):
                            print_fn(f"   ✓ {tool_result['message']}")
                        elif tool_result.get("error"):
                            print_fn(f"   ❌ {tool_result['error']}")
                
                # Show assistant response
                if result["message"]:
                    print_fn(f"🤖 {result['message']}")
                else:
                    # If no message but we have missing fields, prompt for them
                    if result["missing_fields"]:
                        missing = ", ".join(result["missing_fields"])
                        print_fn(f"🤖 I still need to collect: {missing}")
                
                # Check completion
                if result["complete"]:
                    print_fn("\n🎉 All information collected successfully!")
                    print_fn("\nFinal state:")
                    print_fn(str(self.state))
                    break
                
                print_fn()
                
            except KeyboardInterrupt:
                print_fn("\n👋 Goodbye!")
                break
            except Exception as e:
                print_fn(f"❌ Unexpected error: {str(e)}")
                break
        
        else:
            print_fn(f"\n⏰ Reached maximum turns ({self.max_turns})")
    
    def reset(self):
        """Reset the agent state and conversation history."""
        self.state = self.state_cls()
        self.conversation_history = []
