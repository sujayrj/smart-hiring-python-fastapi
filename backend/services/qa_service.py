"""Timed Q&A: deliver questions, score answers, finalize fusion."""

from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from audit import record
from models import Answer, Application, Band, CandidateStatus, TelemetryEvent, User
from repositories import repository
from schemas import AnswerOut, AnswerSubmit, QuestionPublic
from services import flags_service, scoring_service


def get_questions(db: Session, application: Application) -> list[QuestionPublic]:
    questions = repository.list_questions(db, application.jd_id)
    return [QuestionPublic.model_validate(q) for q in questions]


def submit_answer(
    db: Session,
    application: Application,
    payload: AnswerSubmit,
    scorer,
    actor: User,
) -> AnswerOut:
    question = repository.get_question(db, payload.question_id)
    if question is None or question.jd_id != application.jd_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Question does not belong to this application")

    result = scorer.score(question, payload.answer_text)

    answer = repository.get_answer(db, application.id, question.id)
    if answer is None:
        answer = Answer(application_id=application.id, question_id=question.id)
        db.add(answer)
    answer.answer_text = payload.answer_text
    answer.score = result.score
    answer.confidence = result.confidence
    answer.justification = result.justification
    answer.rubric_hits = result.rubric_hits
    answer.time_spent_seconds = payload.time_spent_seconds
    db.flush()

    for event in payload.telemetry:
        db.add(
            TelemetryEvent(
                application_id=application.id,
                event_type=event.event_type,
                details=event.details,
            )
        )

    _finalize_if_complete(db, application)

    record(
        db,
        event_type="answer.scored",
        actor_id=actor.id,
        actor_role=actor.role,
        entity_type="Answer",
        entity_id=answer.id,
        details={"question_id": question.id, "score": result.score},
    )
    db.commit()
    db.refresh(answer)
    return AnswerOut.model_validate(answer)


def _finalize_if_complete(db: Session, application: Application) -> None:
    questions = repository.list_questions(db, application.jd_id)
    answers = repository.list_answers(db, application.id)
    if not questions or len(answers) < len(questions):
        return

    average = sum((a.score or 0) for a in answers) / len(answers)
    qa_normalized = scoring_service.normalize_qa(average)
    confidences = [a.confidence for a in answers if a.confidence is not None]

    application.qa_score = qa_normalized
    application.qa_confidence = round(sum(confidences) / len(confidences), 3) if confidences else None

    combined, band = scoring_service.fuse(
        application.resume_score,
        qa_normalized,
        application.jd.weights,
        application.jd.pass_threshold,
    )
    application.combined_score = combined
    application.band = band
    status_by_band = {
        Band.PASS: CandidateStatus.PASSED,
        Band.HOLD: CandidateStatus.HOLD,
        Band.REJECT: CandidateStatus.REJECTED,
    }
    new_status = status_by_band.get(band, CandidateStatus.PASSED)
    application.status = new_status
    if application.candidate:
        application.candidate.status = new_status
    application.next_steps = (
        "Awaiting interviewer review."
        if band in (Band.PASS, Band.HOLD)
        else "Thank you — your application is under review."
    )

    flags_service.evaluate(db, application, application.jd)
    flags_service.evaluate_telemetry(
        db, application.id, repository.telemetry_summary(db, application.id)
    )
    db.flush()
