"""Candidate listing/detail with role-scoped access."""

from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models import Candidate, Role, User
from repositories import repository
from schemas import CandidateDetail, CandidateOut
from services.serializers import candidate_dto


def _assigned_candidate_ids(db: Session, interviewer: User) -> set[int]:
    ids: set[int] = set()
    for interview in repository.interviews_for_interviewer(db, interviewer.id):
        app = interview.application
        if app is not None:
            ids.add(app.candidate_id)
    return ids


def list_candidates(db: Session, actor: User) -> list[CandidateOut]:
    if actor.role == Role.ADMIN:
        return [candidate_dto(c) for c in repository.list_candidates(db)]
    if actor.role == Role.INTERVIEWER:
        allowed = _assigned_candidate_ids(db, actor)
        return [candidate_dto(c) for c in repository.list_candidates(db) if c.id in allowed]
    return []


def get_candidate(db: Session, candidate_id: int, actor: User) -> CandidateDetail:
    candidate: Candidate | None = repository.get_candidate(db, candidate_id)
    if candidate is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Candidate not found")
    if actor.role == Role.INTERVIEWER and candidate_id not in _assigned_candidate_ids(db, actor):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Candidate not assigned to you")
    if actor.role not in (Role.ADMIN, Role.INTERVIEWER):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Insufficient role")
    return candidate_dto(candidate, detail=True)
