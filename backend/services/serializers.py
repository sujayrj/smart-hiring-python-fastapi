"""ORM -> DTO serializers."""

from __future__ import annotations

from models import Application, Candidate, Interview, JobDescription
from schemas import (
    ApplicationDetail,
    ApplicationOut,
    CandidateDetail,
    CandidateOut,
    InterviewOut,
    JDDetail,
    JDOut,
    QuestionOut,
)


def candidate_dto(candidate: Candidate, detail: bool = False) -> CandidateOut:
    if detail:
        return CandidateDetail.model_validate(candidate)
    return CandidateOut.model_validate(candidate)


def jd_dto(jd: JobDescription, detail: bool = False) -> JDOut:
    base = {
        "id": jd.id,
        "title": jd.title,
        "location": jd.location,
        "experience_years": jd.experience_years,
        "education": jd.education,
        "must_have": jd.must_have,
        "nice_to_have": jd.nice_to_have,
        "weights": jd.weights,
        "pass_threshold": jd.pass_threshold,
        "confidence_cutoff": jd.confidence_cutoff,
        "summary": jd.summary,
        "created_at": jd.created_at,
        "question_count": len(jd.questions),
    }
    if detail:
        return JDDetail(**base, questions=[QuestionOut.model_validate(q) for q in jd.questions])
    return JDOut(**base)


def application_dto(application: Application) -> ApplicationOut:
    interview = application.interview
    return ApplicationOut(
        id=application.id,
        candidate_id=application.candidate_id,
        jd_id=application.jd_id,
        candidate_name=application.candidate.name if application.candidate else "",
        jd_title=application.jd.title if application.jd else "",
        resume_score=application.resume_score,
        resume_confidence=application.resume_confidence,
        qa_score=application.qa_score,
        combined_score=application.combined_score,
        band=application.band,
        status=application.status,
        next_steps=application.next_steps,
        interview_scheduled_at=interview.scheduled_at if interview else None,
        interviewer_name=(
            interview.interviewer.name
            if interview and interview.interviewer
            else None
        ),
        interview_status=interview.status if interview else None,
        decision=interview.decision if interview else None,
    )


def interview_dto(interview: Interview) -> InterviewOut:
    return InterviewOut(
        id=interview.id,
        application_id=interview.application_id,
        interviewer_id=interview.interviewer_id,
        interviewer_name=interview.interviewer.name if interview.interviewer else "",
        scheduled_at=interview.scheduled_at,
        status=interview.status,
        decision=interview.decision,
        notes=interview.notes,
    )


def application_detail_dto(
    application: Application, telemetry: dict | None = None
) -> ApplicationDetail:
    base = application_dto(application)
    return ApplicationDetail(
        **base.model_dump(),
        answers=list(application.answers),
        interview=interview_dto(application.interview) if application.interview else None,
        flags=list(application.flags),
        telemetry=telemetry or {},
    )