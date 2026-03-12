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
        description="A natural-language question about one or more countries.",
    )


class QueryResponse(BaseModel):
    answer: str = Field(..., description="The agent's answer.")
    countries: list[str] = Field(default_factory=list, description="Countries identified in the query.")
    fields: list[str] = Field(default_factory=list, description="Fields extracted from the query.")
