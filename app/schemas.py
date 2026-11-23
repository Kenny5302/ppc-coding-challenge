"""Pydantic request/response schemas with validation."""
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

from app.states import normalize_state

Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
Age = Annotated[int, Field(ge=0, le=150, strict=True)]


class UserBase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Name
    age: Age
    birth_state: str = Field(description="U.S. state: 2-letter code or full name", examples=["OH"])

    @field_validator("birth_state")
    @classmethod
    def _validate_state(cls, v: str) -> str:
        return normalize_state(v)


class UserCreate(UserBase):
    pass


class UserUpdate(UserBase):
    """PUT replaces the full resource, so all fields are required."""


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    age: int
    birth_state: str
