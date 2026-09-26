"""Admin-only evidence flags (never auto-reject)."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from models import Application, Flag, JobDescription


def add_flag(db: Session, application_id: int, flag_type: str, details: dict) -> Flag:
    existing = db.scalars(
        select(Flag).where(Flag.application_id == application_id, Flag.type == flag_type)
    ).all()
    for flag in existing:
        if flag.details.get("signature") == details.get("signature"):
            return flag
    flag = Flag(application_id=application_id, type=flag_type, details=details)
    db.add(flag)
    db.flush()
    return flag


def evaluate(db: Session, application: Application, jd: JobDescription) -> list[Flag]:
    flags: list[Flag] = []

    if (
        application.resume_confidence is not None
        and application.resume_confidence < jd.confidence_cutoff
    ):
        flags.append(
            add_flag(
                db,
                application.id,
                "LOW_RESUME_CONFIDENCE",
                {
                    "confidence": application.resume_confidence,
                    "cutoff": jd.confidence_cutoff,
                    "signature": "resume",
                },
            )
        )

    if application.qa_confidence is not None and application.qa_confidence < 0.6:
        flags.append(
            add_flag(
                db,
                application.id,
                "LOW_QA_CONFIDENCE",
                {"confidence": application.qa_confidence, "cutoff": 0.6, "signature": "qa"},
            )
        )

    if (
        application.resume_score is not None
        and application.qa_score is not None
        and abs(application.resume_score - application.qa_score) > 30
    ):
        flags.append(
            add_flag(
                db,
                application.id,
                "SCORE_DISAGREEMENT",
                {
                    "resume_score": application.resume_score,
                    "qa_score": application.qa_score,
                    "threshold": 30,
                    "signature": "disagreement",
                },
            )
        )

    return flags


def evaluate_telemetry(db: Session, application_id: int, counts: dict) -> list[Flag]:
    """Anti-cheat telemetry flags (evidence only; never auto-reject)."""
    flags: list[Flag] = []
    if counts.get("tab_switches", 0) >= 3:
        flags.append(
            add_flag(
                db,
                application_id,
                "ANTI_CHEAT_TAB_SWITCH",
                {"tab_switches": counts["tab_switches"], "signature": "tab_switches"},
            )
        )
    if counts.get("copies", 0) >= 3:
        flags.append(
            add_flag(
                db,
                application_id,
                "ANTI_CHEAT_COPY_QUESTION",
                {"copies": counts["copies"], "signature": "copies"},
            )
        )
    if counts.get("pastes", 0) >= 5:
        flags.append(
            add_flag(
                db,
                application_id,
                "ANTI_CHEAT_PASTE",
                {"pastes": counts["pastes"], "signature": "pastes"},
            )
        )
    return flags
