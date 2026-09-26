"""Pydantic request/response DTOs."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


# ------------------------------------------------------------------ auth
class LoginRequest(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    name: str
    user_id: int


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    role: str
    name: str
    email: str = ""


# ------------------------------------------------------------------ JD
class QuestionCreate(BaseModel):
    text: str
    reference_answer: str = ""
    # rubric bands: {"score_5": [...], "score_3": [...], "score_0": [...]}
    rubric: dict[str, list[str]] = Field(default_factory=dict)


class QuestionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    text: str
    reference_answer: str = ""
    rubric: Any = Field(default_factory=dict)


class QuestionPublic(BaseModel):
    """Candidate-facing: no reference answer / rubric."""

    model_config = ConfigDict(from_attributes=True)
    id: int
    text: str


class JDBase(BaseModel):
    title: str
    location: str = ""
    experience_years: str = ""
    education: str = ""
    must_have: str = ""
    nice_to_have: str = ""
    weights: dict[str, float] = Field(default_factory=lambda: {"resume": 60, "qa": 40})
    pass_threshold: float = 70.0
    confidence_cutoff: float = 0.6
    summary: str = ""


class JDCreate(JDBase):
    questions: list[QuestionCreate] = Field(default_factory=list)


class JDUpdate(BaseModel):
    title: Optional[str] = None
    location: Optional[str] = None
    experience_years: Optional[str] = None
    education: Optional[str] = None
    must_have: Optional[str] = None
    nice_to_have: Optional[str] = None
    weights: Optional[dict[str, float]] = None
    pass_threshold: Optional[float] = None
    confidence_cutoff: Optional[float] = None
    summary: Optional[str] = None


class JDOut(JDBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    question_count: int = 0


class JDDetail(JDOut):
    questions: list[QuestionOut] = Field(default_factory=list)


# ------------------------------------------------------------------ candidates / applications
class CandidateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    email: str = ""
    applied_jd: Optional[int] = None
    experience_years: str = ""
    education: str = ""
    location: str = ""
    profile_type: str = ""
    status: str


class CandidateDetail(CandidateOut):
    resume: str = ""


class ApplicationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    candidate_id: int
    jd_id: int
    candidate_name: str = ""
    jd_title: str = ""
    resume_score: Optional[float] = None
    resume_confidence: Optional[float] = None
    qa_score: Optional[float] = None
    combined_score: Optional[float] = None
    band: Optional[str] = None
    status: str
    next_steps: str = ""
    interview_scheduled_at: Optional[datetime] = None
    interviewer_name: Optional[str] = None
    interview_status: Optional[str] = None
    decision: Optional[str] = None


class InterviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    application_id: int
    interviewer_id: int
    interviewer_name: str = ""
    scheduled_at: Optional[datetime] = None
    status: str
    decision: Optional[str] = None
    notes: str = ""


class AnswerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    question_id: int
    answer_text: str = ""
    score: Optional[int] = None
    confidence: Optional[float] = None
    rubric_hits: list[str] = Field(default_factory=list)
    time_spent_seconds: Optional[int] = None


class FlagOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    application_id: int
    type: str
    details: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class ApplicationDetail(ApplicationOut):
    answers: list[AnswerOut] = Field(default_factory=list)
    interview: Optional[InterviewOut] = None
    flags: list[FlagOut] = Field(default_factory=list)
    telemetry: dict[str, Any] = Field(default_factory=dict)


# ------------------------------------------------------------------ actions
class TelemetryItem(BaseModel):
    event_type: str
    details: dict[str, Any] = Field(default_factory=dict)


class AnswerSubmit(BaseModel):
    question_id: int
    answer_text: str = ""
    time_spent_seconds: Optional[int] = None
    telemetry: list[TelemetryItem] = Field(default_factory=list)


class AssignInterviewerRequest(BaseModel):
    interviewer_id: int
    scheduled_at: Optional[datetime] = None
    note: str = ""


class DecisionRequest(BaseModel):
    decision: str  # ACCEPTED | REJECTED | ON_HOLD | NO_SHOW
    notes: str = ""


class NoteRequest(BaseModel):
    note: str


class NextStepsRequest(BaseModel):
    next_steps: str


class MessageResponse(BaseModel):
    message: str
    event: str = ""


# ------------------------------------------------------------------ misc
class AuditOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    actor_id: Optional[int] = None
    actor_role: str = ""
    event_type: str
    entity_type: str = ""
    entity_id: Optional[int] = None
    details: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class DashboardStats(BaseModel):
    jds: int
    candidates: int
    in_screening: int
    open_flags: int
    recent: list[ApplicationOut] = Field(default_factory=list)


class ScreeningResultItem(BaseModel):
    application_id: int
    candidate_id: int
    candidate_name: str
    score: Optional[float]
    confidence: Optional[float]
    matched_skills: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
    outcome: str
    error: Optional[str] = None


class ScreeningResult(BaseModel):
    jd_id: int
    jd_title: str
    scored: int
    promoted: int
    archived: int
    errors: int
    results: list[ScreeningResultItem] = Field(default_factory=list)


class InterviewerAssignment(BaseModel):
    application_id: int
    candidate_id: int
    candidate_name: str
    jd_title: str
    status: str
    band: Optional[str] = None
    combined_score: Optional[float] = None
    scheduled_at: Optional[datetime] = None
    interview_status: Optional[str] = None
    decision: Optional[str] = None
