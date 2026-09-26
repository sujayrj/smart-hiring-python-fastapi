"""Interview assignment, notes, and decisions."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from audit import record
from models import Application, CandidateStatus, Interview, Role, User
from repositories import repository
from schemas import AssignInterviewerRequest, DecisionRequest, InterviewOut
from services.serializers import interview_dto


def _append_note(existing: str, actor: User, note: str) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
    line = f"{stamp} · {actor.username}: {note.strip()}"
    return f"{existing}\n{line}".strip() if existing else line


def assign_interviewer(
    db: Session,
    application: Application,
    payload: AssignInterviewerRequest,
    actor: User,
) -> InterviewOut:
    interviewer = repository.get_user(db, payload.interviewer_id)
    if interviewer is None or interviewer.role != Role.INTERVIEWER:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid interviewer")

    interview = repository.get_interview(db, application.id)
    if interview is None:
        interview = Interview(application_id=application.id, interviewer_id=interviewer.id)
        db.add(interview)
    interview.interviewer_id = interviewer.id
    interview.scheduled_at = payload.scheduled_at
    interview.status = "SCHEDULED"
    if payload.note:
        interview.notes = _append_note(interview.notes, actor, payload.note)

    application.status = CandidateStatus.INTERVIEW
    if application.candidate:
        application.candidate.status = CandidateStatus.INTERVIEW
    application.next_steps = f"Interview scheduled with {interviewer.name}."
    db.flush()

    record(
        db,
        event_type="interview.assigned",
        actor_id=actor.id,
        actor_role=actor.role,
        entity_type="Application",
        entity_id=application.id,
        details={"interviewer_id": interviewer.id, "scheduled_at": str(payload.scheduled_at)},
    )
    db.commit()
    db.refresh(interview)
    dto = interview_dto(interview)
    dto.interviewer_name = interviewer.name
    return dto


def add_note(db: Session, application: Application, note: str, actor: User) -> InterviewOut:
    interview = repository.get_interview(db, application.id)
    if interview is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No interview scheduled yet")
    interview.notes = _append_note(interview.notes, actor, note)
    db.flush()
    record(
        db,
        event_type="note.added",
        actor_id=actor.id,
        actor_role=actor.role,
        entity_type="Application",
        entity_id=application.id,
        details={"note": note.strip()},
    )
    db.commit()
    db.refresh(interview)
    return interview_dto(interview)


_DECISION_STATUS = {
    "ACCEPTED": CandidateStatus.ACCEPTED,
    "REJECTED": CandidateStatus.REJECTED,
    "ON_HOLD": CandidateStatus.ON_HOLD,
    "NO_SHOW": CandidateStatus.NO_SHOW,
}


def record_decision(
    db: Session,
    application: Application,
    payload: DecisionRequest,
    actor: User,
) -> InterviewOut:
    interview = repository.get_interview(db, application.id)
    if interview is None or interview.interviewer_id != actor.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not your assigned interview")

    decision = payload.decision.upper()
    if decision not in _DECISION_STATUS:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Decision must be one of ACCEPTED, REJECTED, ON_HOLD, NO_SHOW",
        )

    interview.decision = decision
    interview.status = "COMPLETED"
    if payload.notes:
        interview.notes = _append_note(interview.notes, actor, payload.notes)

    application.status = _DECISION_STATUS[decision]
    if application.candidate:
        application.candidate.status = _DECISION_STATUS[decision]
    application.next_steps = f"Interview outcome: {decision.replace('_', ' ').title()}."
    db.flush()

    record(
        db,
        event_type="decision.recorded",
        actor_id=actor.id,
        actor_role=actor.role,
        entity_type="Application",
        entity_id=application.id,
        details={"decision": decision},
    )
    db.commit()
    db.refresh(interview)
    return interview_dto(interview)
