"""Thin data-access layer (SQLAlchemy). Keeps services free of query details."""

from __future__ import annotations

from typing import Optional, Sequence

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from models import (
    Answer,
    Application,
    AuditLog,
    Candidate,
    Flag,
    Interview,
    JobDescription,
    Question,
    TelemetryEvent,
    User,
)


# ------------------------------------------------------------------ users
def get_user(db: Session, user_id: int) -> Optional[User]:
    return db.get(User, user_id)


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    return db.scalar(select(User).where(User.username == username))


def list_interviewers(db: Session) -> Sequence[User]:
    return db.scalars(select(User).where(User.role == "INTERVIEWER").order_by(User.name)).all()


# ------------------------------------------------------------------ JDs
def list_jds(db: Session) -> Sequence[JobDescription]:
    return db.scalars(select(JobDescription).order_by(JobDescription.id)).all()


def get_jd(db: Session, jd_id: int) -> Optional[JobDescription]:
    return db.get(JobDescription, jd_id)


def add_jd(db: Session, jd: JobDescription) -> JobDescription:
    db.add(jd)
    db.flush()
    return jd


def delete_jd(db: Session, jd: JobDescription) -> None:
    db.delete(jd)
    db.flush()


# ------------------------------------------------------------------ questions
def list_questions(db: Session, jd_id: int) -> Sequence[Question]:
    return db.scalars(
        select(Question).where(Question.jd_id == jd_id).order_by(Question.id)
    ).all()


def get_question(db: Session, question_id: int) -> Optional[Question]:
    return db.get(Question, question_id)


# ------------------------------------------------------------------ candidates
def list_candidates(db: Session) -> Sequence[Candidate]:
    return db.scalars(select(Candidate).order_by(Candidate.id)).all()


def get_candidate(db: Session, candidate_id: int) -> Optional[Candidate]:
    return db.get(Candidate, candidate_id)


def candidates_for_jd(db: Session, jd_id: int) -> Sequence[Candidate]:
    return db.scalars(
        select(Candidate).where(Candidate.applied_jd == jd_id).order_by(Candidate.id)
    ).all()


# ------------------------------------------------------------------ applications
def list_applications(db: Session) -> Sequence[Application]:
    return db.scalars(select(Application).order_by(Application.id)).all()


def get_application(db: Session, application_id: int) -> Optional[Application]:
    return db.get(Application, application_id)


def get_application_for(db: Session, candidate_id: int, jd_id: int) -> Optional[Application]:
    return db.scalar(
        select(Application).where(
            Application.candidate_id == candidate_id, Application.jd_id == jd_id
        )
    )


def applications_for_jd(db: Session, jd_id: int) -> Sequence[Application]:
    return db.scalars(
        select(Application).where(Application.jd_id == jd_id).order_by(Application.id)
    ).all()


def add_application(db: Session, application: Application) -> Application:
    db.add(application)
    db.flush()
    return application


# ------------------------------------------------------------------ answers
def list_answers(db: Session, application_id: int) -> Sequence[Answer]:
    return db.scalars(
        select(Answer).where(Answer.application_id == application_id).order_by(Answer.id)
    ).all()


def get_answer(db: Session, application_id: int, question_id: int) -> Optional[Answer]:
    return db.scalar(
        select(Answer).where(
            Answer.application_id == application_id, Answer.question_id == question_id
        )
    )


# ------------------------------------------------------------------ interviews
def get_interview(db: Session, application_id: int) -> Optional[Interview]:
    return db.scalar(select(Interview).where(Interview.application_id == application_id))


def interviews_for_interviewer(db: Session, interviewer_id: int) -> Sequence[Interview]:
    return db.scalars(
        select(Interview)
        .where(Interview.interviewer_id == interviewer_id)
        .order_by(Interview.id)
    ).all()


# ------------------------------------------------------------------ audit / flags
def list_audit(db: Session, limit: int = 200) -> Sequence[AuditLog]:
    return db.scalars(
        select(AuditLog).order_by(AuditLog.created_at.desc(), AuditLog.id.desc()).limit(limit)
    ).all()


def list_flags(db: Session) -> Sequence[Flag]:
    return db.scalars(select(Flag).order_by(Flag.id.desc())).all()


def count_open_flags(db: Session) -> int:
    return int(db.scalar(select(func.count()).select_from(Flag)) or 0)


def count(db: Session, model) -> int:
    return int(db.scalar(select(func.count()).select_from(model)) or 0)


def telemetry_for(db: Session, application_id: int) -> Sequence[TelemetryEvent]:
    return db.scalars(
        select(TelemetryEvent)
        .where(TelemetryEvent.application_id == application_id)
        .order_by(TelemetryEvent.id)
    ).all()


def telemetry_summary(db: Session, application_id: int) -> dict[str, int]:
    counts: dict[str, int] = {}
    for event in telemetry_for(db, application_id):
        counts[event.event_type] = counts.get(event.event_type, 0) + 1
    return {
        "tab_switches": counts.get("visibility_change", 0),
        "pastes": counts.get("paste", 0),
        "copies": counts.get("copy", 0),
    }
