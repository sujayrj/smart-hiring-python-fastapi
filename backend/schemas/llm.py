"""Strict schemas for LLM structured output (validated before use)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ResumeMatchResult(BaseModel):
    score: int = Field(ge=0, le=100)
    matched_skills: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
    summary: str = ""
    confidence: float = Field(ge=0.0, le=1.0)


class AnswerScoreResult(BaseModel):
    score: int = Field(ge=0, le=5)
    justification: str = ""
    confidence: float = Field(ge=0.0, le=1.0)
    rubric_hits: list[str] = Field(default_factory=list)
