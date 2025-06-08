"""
Tests for the StateModel and Field classes.
"""

from dataclasses import dataclass, field
import pytest
from stateagent.core.state import StateModel, Field
from stateagent.core.validation import ValidationError, create_email_validator


@dataclass
class DummyState(StateModel):
    """Dummy state model for unit tests."""

    name: str = field(default=None)
    email: str = field(default=None)
    age: int = field(default=None)
    notes: str = field(default="No notes")

    _field_info = {
        "name": Field(
            required=True,
            description="Person's name"
        ),
        "email": Field(
            required=True,
            validator=create_email_validator()
        ),
        "age": Field(
            required=False,
            description="Person's age"
        ),
        "notes": Field(
            required=False,
            default="No notes"
        )
    }

    def get_field_info(self, name: str):
        return self._field_info.get(name)


class TestStateModel:
    """Test cases for StateModel functionality."""
    
    def test_state_creation(self):
        """Test basic state model creation."""
        state = DummyState()
        assert state.name is None
        assert state.email is None
        assert state.age is None
        assert state.notes == "No notes"
    
    def test_set_field(self):
        """Test setting field values."""
        state = DummyState()
        
        state.set_field("name", "John Doe")
        assert state.name == "John Doe"
        
        state.set_field("age", "25")  # String should be converted to int
        assert state.age == 25
        assert isinstance(state.age, int)
    
    def test_set_field_validation(self):
        """Test field validation during set_field."""
        state = DummyState()
        
        # Valid email
        state.set_field("email", "test@example.com")
        assert state.email == "test@example.com"
        
        # Invalid email should raise ValidationError
        with pytest.raises(ValidationError):
            state.set_field("email", "invalid-email")
    
    def test_set_nonexistent_field(self):
        """Test setting a field that doesn't exist."""
        state = DummyState()
        
        with pytest.raises(ValidationError):
            state.set_field("nonexistent", "value")
    
    def test_validate(self):
        """Test state validation."""
        state = DummyState()
        
        # Initially missing required fields
        missing = state.validate()
        assert "name" in missing
        assert "email" in missing
        assert "age" not in missing  # Not required
        
        # Set required fields
        state.set_field("name", "John")
        state.set_field("email", "john@example.com")
        
        missing = state.validate()
        assert len(missing) == 0
    
    def test_snapshot(self):
        """Test state snapshot functionality."""
        state = DummyState()
        state.set_field("name", "John")
        state.set_field("email", "john@example.com")
        
        snapshot = state.snapshot()
        expected = {
            "name": "John",
            "email": "john@example.com", 
            "age": None,
            "notes": "No notes"
        }
        assert snapshot == expected
    
    def test_clear(self):
        """Test clearing state."""
        state = DummyState()
        state.set_field("name", "John")
        state.set_field("email", "john@example.com")
        
        state.clear()
        assert state.name is None
        assert state.email is None
        assert state.notes == "No notes"  # Should use default
    
    def test_string_representation(self):
        """Test string representation of state."""
        state = DummyState()
        state.set_field("name", "John")
        
        str_repr = str(state)
        assert "DummyState State:" in str_repr
        assert "✓ name: John" in str_repr
        assert "✓ email: (empty)" in str_repr
        assert "○ age: (empty)" in str_repr
