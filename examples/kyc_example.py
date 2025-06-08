"""
KYC (Know Your Customer) Agent Example

This example demonstrates a customer onboarding agent that collects
personal information with validation.
"""

import os
from dataclasses import dataclass, field
from stateagent import (
    StateModel, Field, StructuredAgent, OpenAIAdapter,
    create_email_validator, create_range_validator
)
import dotenv

# Load environment variables from .env if present
dotenv.load_dotenv()


# ───────────────────────────────────────────────────────────────
# State definition
# ───────────────────────────────────────────────────────────────
@dataclass
class KYCState(StateModel):
    """Customer information for KYC compliance."""

    # Actual data fields
    full_name: str = field(default=None)
    email: str = field(default=None)
    date_of_birth: str = field(default=None)
    phone: str = field(default=None)
    address: str = field(default=None)
    annual_income: int = field(default=None)

    # Metadata for each field
    _field_info = {
        "full_name": Field(
            required=True,
            description="Customer's full legal name"
        ),
        "email": Field(
            required=True,
            description="Customer's email address",
            validator=create_email_validator()
        ),
        "date_of_birth": Field(
            required=True,
            description="Date of birth in YYYY-MM-DD format"
        ),
        "phone": Field(
            required=False,
            description="Phone number (optional)"
        ),
        "address": Field(
            required=True,
            description="Full residential address"
        ),
        "annual_income": Field(
            required=True,
            description="Annual income in INR.",
            validator=create_range_validator(min_val=0, max_val=10_00_00_0000)
        ),
    }

    def get_field_info(self, name: str):
        """Return Field metadata for a given field name."""
        return self._field_info.get(name)


# ───────────────────────────────────────────────────────────────
# Hooks
# ───────────────────────────────────────────────────────────────
def on_field_set(state: KYCState, field_name: str):
    """Runs after each successful set_field()."""
    value = getattr(state, field_name)
    print(f"   📝 Updated {field_name}: {value}")


def on_kyc_complete(state: KYCState):
    """Called when all required information is collected."""
    print(f"\n📋 KYC Information Collected for {state.full_name}")
    print("=" * 50)
    print(f"Email: {state.email}")
    print(f"DOB: {state.date_of_birth}")
    print(f"Phone: {state.phone or 'Not provided'}")
    print(f"Address: {state.address}")
    print(f"Annual Income: ${state.annual_income:,}")
    print("\n✅ Ready for compliance review!")


# ───────────────────────────────────────────────────────────────
# Main runner
# ───────────────────────────────────────────────────────────────
def main():
    """Launch the interactive KYC agent."""
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Please set your OPENAI_API_KEY environment variable")
        return

    system_prompt = """You are a KYC compliance assistant. Your job is to collect verified customer details interactively.

Required fields:
- full_name
- email
- date_of_birth
- address
- annual_income

Optional:
- phone

INSTRUCTIONS:
1. Greet the user and explain what you'll collect.
2. After each user message, call validate_state() to find missing data.
3. Ask for ONE missing field at a time; be conversational.
4. Use set_field(field_name, value) to save each response.
5. Acknowledge each field when recorded.
6. Submit only when all required data is present.
7. Remain friendly and professional.
8. convert to number ,eg 10 lakh = 1000000

Begin with a greeting."""
    agent = StructuredAgent(
        state_cls=KYCState,
        llm=OpenAIAdapter(model="gpt-4o-mini"),
        hooks={
            "on_field_set": on_field_set,
            "on_submit": on_kyc_complete
        },
        system_prompt=system_prompt
    )

    print("🏦 Welcome to the KYC Information Collection System")
    print("I'll help you complete your customer onboarding.\n")

    agent.run_chat()


if __name__ == "__main__":
    main()