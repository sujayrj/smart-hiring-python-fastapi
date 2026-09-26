"""Audit event recorder."""

from __future__ import annotations

from typing import Any, Optional

from sqlalchemy.orm import Session

from models import AuditLog


def record(
    db: Session,
    *,
    event_type: str,
    actor_id: Optional[int] = None,
    actor_role: str = "",
    entity_type: str = "",
    entity_id: Optional[int] = None,
    details: Optional[dict[str, Any]] = None,
) -> AuditLog:
    event = AuditLog(
        actor_id=actor_id,
        actor_role=actor_role,
        event_type=event_type,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details or {},
    )
    db.add(event)
    db.flush()
    return event
