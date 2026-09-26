"""SQLAlchemy ORM entities for SmartHire (7 core entities + flags/telemetry)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


# Status / band constants
class Role:
    ADMIN = "ADMIN"
    CANDIDATE = "CANDIDATE"
    INTERVIEWER = "INTERVIEWER"


class CandidateStatus:
    APPLIED = "APPLIED"
    SCREENING = "SCREENING"
    PASSED = "PASSED"
    HOLD = "HOLD"
    REJECTED = "REJECTED"
    INTERVIEW = "INTERVIEW"
    ACCEPTED = "ACCEPTED"
    ON_HOLD = "ON_HOLD"
    NO_SHOW = "NO_SHOW"
    ARCHIVED = "ARCHIVED"


class Band:
    PASS = "PASS"
    HOLD = "HOLD"
    REJECT = "REJECT"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(128))
    role: Mapped[str] = mapped_column(String(20))
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(160), default="")


class JobDescription(Base):
    __tablename__ = "job_descriptions"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(160))
    location: Mapped[str] = mapped_column(String(120), default="")
    experience_years: Mapped[str] = mapped_column(String(40), default="")
    education: Mapped[str] = mapped_column(String(240), default="")
    must_have: Mapped[str] = mapped_column(Text, default="")
    nice_to_have: Mapped[str] = mapped_column(Text, default="")
    weights: Mapped[dict] = mapped_column(JSON, default=lambda: {"resume": 60, "qa": 40})
    pass_threshold: Mapped[float] = mapped_column(Float, default=70.0)
    confidence_cutoff: Mapped[float] = mapped_column(Float, default=0.6)
    summary: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    questions: Mapped[list["Question"]] = relationship(
        back_populates="jd", cascade="all, delete-orphan"
    )
    applications: Mapped[list["Application"]] = relationship(back_populates="jd")


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(primary_key=True)
    jd_id: Mapped[int] = mapped_column(ForeignKey("job_descriptions.id"), index=True)
    text: Mapped[str] = mapped_column(Text)
    reference_answer: Mapped[str] = mapped_column(Text, default="")
    rubric: Mapped[list] = mapped_column(JSON, default=list)

    jd: Mapped[JobDescription] = relationship(back_populates="questions")


class Candidate(Base):
    __tablename__ = "candidates"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(160), index=True)
    applied_jd: Mapped[Optional[int]] = mapped_column(ForeignKey("job_descriptions.id"), nullable=True)
    experience_years: Mapped[str] = mapped_column(String(40), default="")
    education: Mapped[str] = mapped_column(String(200), default="")
    location: Mapped[str] = mapped_column(String(120), default="")
    profile_type: Mapped[str] = mapped_column(String(80), default="")
    resume: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(20), default=CandidateStatus.APPLIED)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    applications: Mapped[list["Application"]] = relationship(back_populates="candidate")


class Application(Base):
    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(primary_key=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("candidates.id"), index=True)
    jd_id: Mapped[int] = mapped_column(ForeignKey("job_descriptions.id"), index=True)
    resume_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    resume_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    resume_evidence: Mapped[dict] = mapped_column(JSON, default=dict)
    qa_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # normalized 0-100
    qa_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    combined_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    band: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default=CandidateStatus.APPLIED)
    next_steps: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    candidate: Mapped[Candidate] = relationship(back_populates="applications")
    jd: Mapped[JobDescription] = relationship(back_populates="applications")
    answers: Mapped[list["Answer"]] = relationship(
        back_populates="application", cascade="all, delete-orphan"
    )
    interview: Mapped[Optional["Interview"]] = relationship(
        back_populates="application", uselist=False, cascade="all, delete-orphan"
    )
    flags: Mapped[list["Flag"]] = relationship(
        back_populates="application", cascade="all, delete-orphan"
    )


class Answer(Base):
    __tablename__ = "answers"

    id: Mapped[int] = mapped_column(primary_key=True)
    application_id: Mapped[int] = mapped_column(ForeignKey("applications.id"), index=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"))
    answer_text: Mapped[str] = mapped_column(Text, default="")
    score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    justification: Mapped[str] = mapped_column(Text, default="")
    rubric_hits: Mapped[list] = mapped_column(JSON, default=list)
    time_spent_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    application: Mapped[Application] = relationship(back_populates="answers")


class Interview(Base):
    __tablename__ = "interviews"

    id: Mapped[int] = mapped_column(primary_key=True)
    application_id: Mapped[int] = mapped_column(
        ForeignKey("applications.id"), unique=True, index=True
    )
    interviewer_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="SCHEDULED")
    decision: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    application: Mapped[Application] = relationship(back_populates="interview")
    interviewer: Mapped[Optional["User"]] = relationship(foreign_keys=[interviewer_id])


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    actor_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    actor_role: Mapped[str] = mapped_column(String(20), default="")
    event_type: Mapped[str] = mapped_column(String(60))
    entity_type: Mapped[str] = mapped_column(String(40), default="")
    entity_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Flag(Base):
    __tablename__ = "flags"

    id: Mapped[int] = mapped_column(primary_key=True)
    application_id: Mapped[int] = mapped_column(ForeignKey("applications.id"), index=True)
    type: Mapped[str] = mapped_column(String(40))
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    application: Mapped[Application] = relationship(back_populates="flags")


class TelemetryEvent(Base):
    __tablename__ = "telemetry_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    application_id: Mapped[int] = mapped_column(ForeignKey("applications.id"), index=True)
    event_type: Mapped[str] = mapped_column(String(40))
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
