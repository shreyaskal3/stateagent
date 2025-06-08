from dataclasses import dataclass, field
from stateagent.core.state import StateModel, Field

@dataclass
class SimpleState(StateModel):
    name: str = field(default=None)
    email: str = field(default=None)
    notes: str = field(default=None)

    _field_info = {
        "name": Field(required=True),
        "email": Field(required=True),
        "notes": Field(required=False),
    }

    def get_field_info(self, name: str):
        return self._field_info.get(name)