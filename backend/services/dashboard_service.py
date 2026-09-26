"""Admin dashboard aggregates."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from models import Application, Candidate, CandidateStatus, JobDescription
from repositories import repository
from schemas import DashboardStats
from services.serializers import application_dto


def stats(db: Session) -> DashboardStats:
    in_screening = int(
        db.scalar(
            select(func.count())
            .select_from(Application)
            .where(Application.status == CandidateStatus.SCREENING)
        )
        or 0
    )
    recent_apps = repository.list_applications(db)
    recent = [application_dto(a) for a in recent_apps[-5:]]
    return DashboardStats(
        jds=repository.count(db, JobDescription),
        candidates=repository.count(db, Candidate),
        in_screening=in_screening,
        open_flags=repository.count_open_flags(db),
        recent=recent,
    )
