"""Job Description CRUD."""

from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from audit import record
from models import JobDescription, Question, User
from repositories import repository
from schemas import JDCreate, JDUpdate


def create_jd(db: Session, payload: JDCreate, actor: User) -> JobDescription:
    _validate_config(payload.weights, payload.pass_threshold, payload.confidence_cutoff)
    jd = JobDescription(
        title=payload.title,
        location=payload.location,
        experience_years=payload.experience_years,
        education=payload.education,
        must_have=payload.must_have,
        nice_to_have=payload.nice_to_have,
        weights=payload.weights,
        pass_threshold=payload.pass_threshold,
        confidence_cutoff=payload.confidence_cutoff,
        summary=payload.summary,
    )
    repository.add_jd(db, jd)
    for q in payload.questions:
        db.add(
            Question(
                jd_id=jd.id,
                text=q.text,
                reference_answer=q.reference_answer,
                rubric=q.rubric,
            )
        )
    db.flush()
    record(
        db,
        event_type="jd.created",
        actor_id=actor.id,
        actor_role=actor.role,
        entity_type="JobDescription",
        entity_id=jd.id,
        details={"title": jd.title},
    )
    db.commit()
    db.refresh(jd)
    return jd


def update_jd(db: Session, jd_id: int, payload: JDUpdate, actor: User) -> JobDescription:
    jd = repository.get_jd(db, jd_id)
    if jd is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Job description not found")

    data = payload.model_dump(exclude_unset=True, exclude_none=True)
    if "weights" in data or "pass_threshold" in data or "confidence_cutoff" in data:
        _validate_config(
            data.get("weights", jd.weights),
            data.get("pass_threshold", jd.pass_threshold),
            data.get("confidence_cutoff", jd.confidence_cutoff),
        )
    for key, value in data.items():
        setattr(jd, key, value)
    db.flush()
    record(
        db,
        event_type="jd.updated",
        actor_id=actor.id,
        actor_role=actor.role,
        entity_type="JobDescription",
        entity_id=jd.id,
        details={"fields": sorted(data.keys())},
    )
    db.commit()
    db.refresh(jd)
    return jd


def delete_jd(db: Session, jd_id: int, actor: User) -> None:
    jd = repository.get_jd(db, jd_id)
    if jd is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Job description not found")
    repository.delete_jd(db, jd)
    record(
        db,
        event_type="jd.deleted",
        actor_id=actor.id,
        actor_role=actor.role,
        entity_type="JobDescription",
        entity_id=jd_id,
        details={"title": jd.title},
    )
    db.commit()


def _validate_config(weights: dict | None, pass_threshold: float, confidence_cutoff: float) -> None:
    weights = weights or {}
    resume = float(weights.get("resume", 60) or 0)
    qa = float(weights.get("qa", 40) or 0)
    if resume < 0 or qa < 0:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Weights must be non-negative")
    if resume + qa <= 0:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Weights must total more than 0")
    if not 0 <= pass_threshold <= 100:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Threshold must be 0-100")
    if not 0 <= confidence_cutoff <= 1:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Confidence cutoff must be 0-1")
