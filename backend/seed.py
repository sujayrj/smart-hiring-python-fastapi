"""Load synthetic seed data from input-data.json into the in-memory DB.

Accepts the hackathon dataset schema: jobs with array must/nice-to-have and a
``weight`` object, a separate ``questions`` array with rubric bands, candidates
keyed by ``applied_id``/``user``, and lower-case user roles.
"""

from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy import select

from auth.security import hash_password
from config import settings
from database import SessionLocal
from models import (
    Application,
    Candidate,
    CandidateStatus,
    JobDescription,
    Question,
    User,
)

_ROLE_MAP = {"admin": "ADMIN", "candidate": "CANDIDATE", "interviewer": "INTERVIEWER"}


def _resolve(path: str) -> Path:
    p = Path(path)
    if not p.is_absolute():
        p = (Path(__file__).resolve().parent / path).resolve()
    return p


def _as_text(value) -> str:
    if isinstance(value, list):
        return ", ".join(str(v) for v in value)
    return str(value or "")


def _as_percent(weight: dict | None) -> dict:
    weight = weight or {}
    resume = float(weight.get("resume", 0.6) or 0)
    qa = float(weight.get("qa", 0.4) or 0)
    if resume <= 1 and qa <= 1:  # fractions -> percentages
        resume, qa = resume * 100, qa * 100
    return {"resume": round(resume, 2), "qa": round(qa, 2)}


def load_seed(path: str | None = None) -> bool:
    """Idempotent: only seeds when the users table is empty."""
    resolved = _resolve(path or settings.input_data_path)
    if not resolved.exists():
        return False

    data = json.loads(resolved.read_text(encoding="utf-8"))
    db = SessionLocal()
    try:
        if db.scalar(select(User).limit(1)) is not None:
            return False

        # 1. users
        users: dict[str, User] = {}
        for row in data.get("users", []):
            role = _ROLE_MAP.get(str(row.get("role", "")).lower(), str(row.get("role", "")).upper())
            user = User(
                username=row["username"],
                password_hash=hash_password(row["password"]),
                role=role,
                name=row.get("name", row["username"]),
                email=row.get("email", ""),
            )
            db.add(user)
            users[row["username"]] = user
        db.flush()

        # 2. job descriptions
        jds: dict[str, JobDescription] = {}
        for row in data.get("job_descriptions", []):
            jd = JobDescription(
                title=row["title"],
                location=row.get("location", ""),
                experience_years=str(row.get("experience_years", "")),
                education=row.get("education", ""),
                must_have=_as_text(row.get("must_have")),
                nice_to_have=_as_text(row.get("nice_to_have")),
                weights=_as_percent(row.get("weight") or row.get("weights")),
                pass_threshold=row.get("pass_threshold", 70),
                confidence_cutoff=row.get("confidence_cutoff", 0.6),
                summary=row.get("summary", ""),
            )
            db.add(jd)
            db.flush()
            jds[str(row["id"])] = jd
        db.flush()

        # 3. questions (separate array, linked by jd_id)
        for row in data.get("questions", []):
            jd = jds.get(str(row.get("jd_id")))
            if jd is None:
                continue
            db.add(
                Question(
                    jd_id=jd.id,
                    text=row["text"],
                    reference_answer=row.get("reference_answer", ""),
                    rubric=row.get("rubric", {}),
                )
            )
        db.flush()

        # 4. candidates + applications
        for row in data.get("candidates", []):
            jd = jds.get(str(row.get("applied_id"))) if row.get("applied_id") else None
            user = users.get(row.get("user")) if row.get("user") else None
            if user is not None:
                user.name = row.get("name", user.name)
                user.email = row.get("email", user.email)
            candidate = Candidate(
                user_id=user.id if user else None,
                name=row["name"],
                email=row.get("email", ""),
                applied_jd=jd.id if jd else None,
                experience_years=str(row.get("experience_years", "")),
                education=row.get("education", ""),
                location=row.get("location", ""),
                profile_type=row.get("profile_type", ""),
                resume=row.get("resume", ""),
                status=CandidateStatus.APPLIED,
            )
            db.add(candidate)
            db.flush()
            if jd is not None:
                db.add(
                    Application(
                        candidate_id=candidate.id,
                        jd_id=jd.id,
                        status=CandidateStatus.APPLIED,
                    )
                )

        db.commit()
        return True
    finally:
        db.close()