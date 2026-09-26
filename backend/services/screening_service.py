"""Résumé screening: on-demand, per-JD batch scoring."""

from __future__ import annotations

from sqlalchemy.orm import Session

from ai.llm_client import LLMError
from audit import record
from models import Application, CandidateStatus, JobDescription, User
from repositories import repository
from schemas import ScreeningResult, ScreeningResultItem
from services import flags_service


class ScreeningService:
    def __init__(self, db: Session, matcher):
        self.db = db
        self.matcher = matcher

    def run_for_jd(self, jd: JobDescription, actor: User) -> ScreeningResult:
        candidates = repository.candidates_for_jd(self.db, jd.id)
        results: list[ScreeningResultItem] = []
        promoted = archived = errors = 0

        for candidate in candidates:
            application = repository.get_application_for(self.db, candidate.id, jd.id)
            if application is None:
                application = Application(
                    candidate_id=candidate.id, jd_id=jd.id, status=CandidateStatus.APPLIED
                )
                repository.add_application(self.db, application)

            try:
                match = self.matcher.match(jd, candidate.resume)
            except LLMError as exc:
                errors += 1
                self.db.commit()
                record(
                    self.db,
                    event_type="screening.error",
                    actor_id=actor.id,
                    actor_role=actor.role,
                    entity_type="Application",
                    entity_id=application.id,
                    details={"error": str(exc)},
                )
                self.db.commit()
                results.append(
                    ScreeningResultItem(
                        application_id=application.id,
                        candidate_id=candidate.id,
                        candidate_name=candidate.name,
                        score=None,
                        confidence=None,
                        outcome="ERROR",
                        error=str(exc),
                    )
                )
                continue

            # Persist successful scoring BEFORE changing status (spec §13).
            application.resume_score = match.score
            application.resume_confidence = match.confidence
            application.resume_evidence = {
                "matched_skills": match.matched_skills,
                "gaps": match.gaps,
                "summary": match.summary,
            }
            self.db.flush()

            if match.score >= jd.pass_threshold:
                application.status = CandidateStatus.SCREENING
                candidate.status = CandidateStatus.SCREENING
                application.next_steps = "Complete the timed Q&A."
                outcome = "PROMOTED"
                promoted += 1
            else:
                application.status = CandidateStatus.ARCHIVED
                candidate.status = CandidateStatus.ARCHIVED
                application.next_steps = ""
                application.resume_evidence["archive_reason"] = (
                    f"Résumé score {match.score} below threshold {jd.pass_threshold}."
                )
                outcome = "ARCHIVED"
                archived += 1

            flags_service.evaluate(self.db, application, jd)
            record(
                self.db,
                event_type="screening.scored",
                actor_id=actor.id,
                actor_role=actor.role,
                entity_type="Application",
                entity_id=application.id,
                details={"score": match.score, "outcome": outcome},
            )
            self.db.commit()

            results.append(
                ScreeningResultItem(
                    application_id=application.id,
                    candidate_id=candidate.id,
                    candidate_name=candidate.name,
                    score=match.score,
                    confidence=match.confidence,
                    matched_skills=match.matched_skills,
                    gaps=match.gaps,
                    outcome=outcome,
                )
            )

        record(
            self.db,
            event_type="screening.run",
            actor_id=actor.id,
            actor_role=actor.role,
            entity_type="JobDescription",
            entity_id=jd.id,
            details={"scored": len(results) - errors, "promoted": promoted, "archived": archived},
        )
        self.db.commit()

        return ScreeningResult(
            jd_id=jd.id,
            jd_title=jd.title,
            scored=len(results) - errors,
            promoted=promoted,
            archived=archived,
            errors=errors,
            results=results,
        )
