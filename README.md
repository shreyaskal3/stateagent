# stateagent

A lightweight Python framework to structure LLM conversations using a validated state model and a tool-based interaction design.

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [🏗️ Core Concepts](#️-core-concepts)
- [🎨 Advanced Features](#-advanced-features)
- [🧪 Built-in Validators](#-built-in-validators)
- [📚 Examples](#-examples)
- [🔧 Configuration](#-configuration)
- [🧪 Testing](#-testing)
- [📖 API Reference](#-api-reference)
- [📄 License](#-license)
- [📊 Roadmap](#-roadmap)

## Installation

```bash
pip install stateagent
```

## Quick Start

Here's a simple example to get you up and running:

### Example Conversation

```plaintext
🤖 Hi! I need to collect some contact information from you.

👤 My name is John Smith

🤖 Great! I've recorded your name as John Smith.
    Now, could you please provide your email address?

👤 john@company.com

🤖 Perfect! I've saved your email.
    Finally, what message would you like to send?

👤 I'm interested in learning more about your services.

🤖 Excellent! I have all the information I need:
    ✓ Name: John Smith
    ✓ Email: john@company.com
    ✓ Message: I'm interested in learning more about your services.

    Thank you for your submission!
```

## 🏗️ Core Concepts

### StateModel

Define your data structure with validation:

```python
from dataclasses import dataclass, field
from llm_structured_agent import StateModel, Field, create_range_validator

@dataclass
class UserProfile(StateModel):
    name: str = field(default=None)
    age: int = field(default=None)
    email: str = field(default=None)

    _field_info = {
        'name': Field(
            required=True,
            description="User's full name",
            validator=create_length_validator(min_length=2)
        ),
        'age': Field(
            required=True,
            description="User's age",
            validator=create_range_validator(min_val=13, max_val=120)
        ),
        'email': Field(
            required=True,
            description="Email address",
            validator=create_email_validator()
        )
    }
```

### CRUD Tools

The LLM automatically gets these tools to interact with state:

- **`set_field(field_name, value)`** - Update a field with validation
- **`validate_state()`** - Check if all required fields are complete
- **`get_state()`** - View current state snapshot
- **`clear_state()`** - Reset all fields to defaults

### Structured Agent

The main orchestrator that manages the conversation:

```python
agent = StructuredAgent(
    state_cls=UserProfile,
    llm=OpenAIAdapter(model="gpt-4o-mini"),
    hooks={
        "on_field_set": lambda state, field: print(f"Updated {field}"),
        "on_submit": lambda state: save_to_database(state.snapshot())
    },
    max_turns=20
)
```

## 🎨 Advanced Features

### Custom Validation

```python
import re
from llm_structured_agent import ValidationError

def validate_phone_number(value: str):
    if not re.match(r'^\+?[\d\s\-]+$', value):
        raise ValidationError("Invalid phone format")
    return value.strip()

@dataclass
class ContactInfo(StateModel):
    phone: str = field(default=None)

    _field_info = {
        'phone': Field(
            required=True,
            description="Phone number with country code",
            validator=validate_phone_number
        )
    }
```

### Conditional Logic

```python
@dataclass
class OrderForm(StateModel):
    item_type: str = field(default=None)
    shipping_address: str = field(default=None)
    gift_message: str = field(default=None)

    def validate(self) -> List[str]:
        missing = super().validate()

        # Gift message required for gift items
        if (self.item_type == "gift" and
            not self.gift_message):
            missing.append("gift_message")

        return missing
```

### Lifecycle Hooks

```python
def on_field_updated(state, field_name):
    print(f"📝 {field_name} updated to: {getattr(state, field_name)}")

def on_form_complete(state):
    # Save to database
    save_to_database(state.snapshot())

    # Send notification
    send_notification(state.email, "Form completed!")

    # Log completion
    logger.info(f"Form completed for {state.name}")

agent = StructuredAgent(
    state_cls=MyForm,
    llm=OpenAIAdapter(),
    hooks={
        "on_field_set": on_field_updated,
        "on_submit": on_form_complete
    }
)
```

### Multiple LLM Providers

```python
# OpenAI (default)
agent = StructuredAgent(
    state_cls=MyState,
    llm=OpenAIAdapter(model="gpt-4o-mini")
)

# Custom LLM provider
class CustomLLMAdapter(LLMAdapter):
    def chat(self, messages, tools=None):
        # Your implementation
        pass

    def extract_function_calls(self, response):
        # Your implementation
        pass

agent = StructuredAgent(
    state_cls=MyState,
    llm=CustomLLMAdapter()
)
```

### Non-Interactive Usage

```python
# For API endpoints or batch processing
agent = StructuredAgent(state_cls=ContactForm, llm=OpenAIAdapter())

# Process single message
result = agent.process_single_turn("My name is John and email is john@example.com")

if result["complete"]:
    print("Form completed:", result["state"])
else:
    print("Next response:", result["message"])
    print("Still missing:", result["missing_fields"])
```

## 🧪 Built-in Validators

The library includes common validators:

```python
from llm_structured_agent import (
    create_email_validator,
    create_range_validator,
    create_length_validator,
    create_regex_validator,
    create_choice_validator
)

# Email validation
email_validator = create_email_validator()

# Numeric range
age_validator = create_range_validator(min_val=18, max_val=100)

# String length
name_validator = create_length_validator(min_length=2, max_length=50)

# Regex pattern
phone_validator = create_regex_validator(
    pattern=r'^\+?[\d\s\-]+$',
    error_message="Invalid phone number format"
)

# Choice validation
department_validator = create_choice_validator([
    "Engineering", "Sales", "Marketing", "HR"
])
```

## 📚 Examples

The library includes complete examples:

### Customer Onboarding (KYC)

```bash

# Run the KYC example

python -m llm_structured_agent.examples.kyc_example

# Or if installed via pip

kyc-agent
```

### Employee Onboarding

```bash
# Run the employee onboarding example
python -m llm_structured_agent.examples.onboarding_example

# Or if installed via pip
onboarding-agent
```

## 🔧 Configuration

### Environment Variables

```bash

# Required for OpenAI

export OPENAI_API_KEY="your-openai-api-key"

# Optional: Custom model

export OPENAI_MODEL="gpt-4o-mini"

```

### Custom System Prompts

```python
custom_prompt = """You are a helpful assistant collecting user information.

Be conversational and friendly while systematically gathering:
- Name (required)
- Email (required)
- Phone (optional)

Use the provided tools to store information and check completeness."""

agent = StructuredAgent(
    state_cls=ContactForm,
    llm=OpenAIAdapter(),
    system_prompt=custom_prompt
)
```

## 🧪 Testing

```bash

# Install with dev dependencies

pip install stateagent[dev]

# Run tests

pytest

# Run with coverage

pytest --cov=llm_structured_agent

# Run specific test

pytest tests/test_state.py -v
```

## 📖 API Reference

### StateModel

Base class for defining structured state:

```python
class StateModel:
    def set_field(self, name: str, value: Any) -> None
    def validate(self) -> List[str]
    def snapshot(self) -> Dict[str, Any]
    def clear(self) -> None
    def get_field_info(self, name: str) -> Optional[Field]
```

### Field

Field definition with validation:

```python
class Field:
    def __init__(
        self,
        required: bool = False,
        description: str = "",
        validator: Optional[Callable] = None,
        default: Any = None
    )
```

### StructuredAgent

Main orchestration class:

```python
class StructuredAgent:
    def __init__(
        self,
        state_cls: type,
        llm: LLMAdapter,
        hooks: Optional[Dict[str, Callable]] = None,
        max_turns: int = 20,
        system_prompt: Optional[str] = None
    )

    def run_chat(self) -> None
    def process_single_turn(self, user_input: str) -> Dict[str, Any]
    def reset(self) -> None
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📊 Roadmap

- [ ] More LLM provider integrations
- [ ] FastAPI integration
- [ ] Streamlit demo interface
- [ ] Database persistence layer
- [ ] MCP Server

---

**Built with ❤️ for the AI community**
