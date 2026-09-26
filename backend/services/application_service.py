"""Post-screening application actions: Next Steps log + stubbed invitation."""

from __future__ import annotations

from sqlalchemy.orm import Session

from audit import record
from models import Application, User
from repositories import repository
from schemas import MessageResponse


def set_next_steps(db: Session, application: Application, text: str, actor: User) -> Application:
    application.next_steps = text
    db.flush()
    record(
        db,
        event_type="next_steps.updated",
        actor_id=actor.id,
        actor_role=actor.role,
        entity_type="Application",
        entity_id=application.id,
        details={"next_steps": text},
    )
    db.commit()
    db.refresh(application)
    return application


def send_invitation(db: Session, application: Application, actor: User) -> MessageResponse:
    """Stubbed invitation: records an audit event only (no real email/SMS)."""
    candidate_name = application.candidate.name if application.candidate else ""
    record(
        db,
        event_type="invitation.sent",
        actor_id=actor.id,
        actor_role=actor.role,
        entity_type="Application",
        entity_id=application.id,
        details={"candidate": candidate_name, "channel": "stubbed"},
    )
    db.commit()
    return MessageResponse(
        message=f"Invitation sent to {candidate_name} (stubbed — no real email).",
        event="invitation.sent",
    )