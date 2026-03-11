"""
schemas.py — Pydantic models for the Vishwa HTTP API layer.
"""

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=3,
        max_length=500,
        examples=["What is the population of Germany?"],
        description="A natural-language question about a country.",
    )


class QueryResponse(BaseModel):
    answer: str = Field(..., description="The agent's answer.")
    country: str | None = Field(None, description="Country identified in the query.")
    fields: list[str] = Field(default_factory=list, description="Fields extracted from the query.")
