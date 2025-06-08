"""
Employee Onboarding Agent Example

This example demonstrates an HR onboarding agent with conditional logic
and custom validation.
"""

import os
from dataclasses import dataclass, field
from typing import List
from stateagent import (
    StateModel, Field, StructuredAgent, OpenAIAdapter,
    create_email_validator, create_choice_validator
)
import dotenv

# Try to load .env file if it exists
try:
    dotenv.load_dotenv()
except:
    pass

@dataclass
class OnboardingState(StateModel):
    """Employee onboarding information."""
    
    employee_name: str = field(default=None)
    email: str = field(default=None)
    department: str = field(default=None)
    start_date: str = field(default=None)
    work_location: str = field(default=None)
    office_location: str = field(default=None)
    laptop_preference: str = field(default=None)
    manager_email: str = field(default=None)
    
    # Field metadata - separate from the actual field values
    _field_info = {
        'employee_name': Field(
            required=True,
            description="Employee's full name"
        ),
        'email': Field(
            required=True,
            description="Company email address",
            validator=create_email_validator()
        ),
        'department': Field(
            required=True,
            description="Department (Engineering, Sales, Marketing, HR, Finance)",
            validator=create_choice_validator(["Engineering", "Sales", "Marketing", "HR", "Finance"])
        ),
        'start_date': Field(
            required=True,
            description="Start date in YYYY-MM-DD format"
        ),
        'work_location': Field(
            required=True,
            description="Work location (Remote, Office, Hybrid)",
            validator=create_choice_validator(["Remote", "Office", "Hybrid"])
        ),
        'office_location': Field(
            required=False,
            description="Office location (required if not fully remote)"
        ),
        'laptop_preference': Field(
            required=False,
            description="Laptop preference (MacBook Pro, MacBook Air, ThinkPad, Dell XPS)"
        ),
        'manager_email': Field(
            required=True,
            description="Direct manager's email address",
            validator=create_email_validator()
        )
    }
    
    def get_field_info(self, name: str):
        """Get field information for a given field name."""
        return self._field_info.get(name)
    
    def validate(self) -> List[str]:
        """Custom validation with conditional logic."""
        missing = []
        
        # Check required fields
        for field_name, field_info in self._field_info.items():
            if field_info.required:
                value = getattr(self, field_name)
                if value is None or value == "":
                    missing.append(field_name)
        
        # Office location required if not fully remote
        if (self.work_location in ["Office", "Hybrid"] and 
            not self.office_location):
            missing.append("office_location")
        
        return missing


def on_field_set(state: OnboardingState, field_name: str):
    """Called whenever a field is updated."""
    value = getattr(state, field_name)
    print(f"   📝 Updated {field_name}: {value}")


def on_onboarding_complete(state: OnboardingState):
    """Called when onboarding is complete."""
    print(f"\n🎉 Onboarding Complete for {state.employee_name}!")
    print("=" * 60)
    print(f"📧 Email: {state.email}")
    print(f"🏢 Department: {state.department}")
    print(f"📅 Start Date: {state.start_date}")
    print(f"🏠 Work Location: {state.work_location}")
    
    if state.office_location:
        print(f"🏢 Office: {state.office_location}")
    
    if state.laptop_preference:
        print(f"💻 Laptop: {state.laptop_preference}")
    
    print(f"👤 Manager: {state.manager_email}")
    
    print("\n📋 Next Steps:")
    print("• IT will prepare laptop and accounts")
    print("• Manager will be notified")
    print("• Welcome package will be sent")
    print("• Calendar invite for first day sent")


def main():
    """Run the onboarding agent."""
    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Please set your OPENAI_API_KEY environment variable")
        print("Example: export OPENAI_API_KEY='your-api-key-here'")
        return
    
    # Custom system prompt for better guidance
    system_prompt = """You are an HR onboarding assistant. Your job is to collect employee information through conversation.

You need to collect these required fields:
- employee_name: Employee's full name
- email: Company email address  
- department: One of (Engineering, Sales, Marketing, HR, Finance)
- start_date: Start date in YYYY-MM-DD format
- work_location: One of (Remote, Office, Hybrid)
- manager_email: Direct manager's email address

Optional fields:
- office_location: Required only if work_location is Office or Hybrid
- laptop_preference: MacBook Pro, MacBook Air, ThinkPad, or Dell XPS

IMPORTANT INSTRUCTIONS:
1. Start by introducing yourself and explaining what information you need to collect
2. After each user message, use validate_state() to check what information is still missing
3. Ask for ONE missing field at a time in a conversational way
4. Use set_field(field_name, value) to store each piece of information
5. Acknowledge when you've recorded information
6. Only mark as complete when ALL required fields are collected
7. Be friendly and conversational, but systematic

Begin by greeting the user and explaining what information you need to collect."""
    
    # Create the agent with hooks
    agent = StructuredAgent(
        state_cls=OnboardingState,
        llm=OpenAIAdapter(model="gpt-4o-mini"),
        hooks={
            "on_field_set": on_field_set,
            "on_submit": on_onboarding_complete
        },
        system_prompt=system_prompt
    )
    
    print("🏢 Welcome to Employee Onboarding!")
    print("I'll help you collect all the necessary information for your first day.\n")
    
    # Run interactive chat
    agent.run_chat()


if __name__ == "__main__":
    main()
