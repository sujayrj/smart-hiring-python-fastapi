from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from auth import get_current_user, require_role
from database import get_db
from models import Application, Role, User
from repositories import repository
from schemas import (
    AnswerOut,
    AnswerSubmit,
    ApplicationDetail,
    ApplicationOut,
    AssignInterviewerRequest,
    DecisionRequest,
    InterviewOut,
    MessageResponse,
    NextStepsRequest,
    NoteRequest,
    QuestionPublic,
    TelemetryItem,
)
from services import application_service, interview_service, qa_service
from services.serializers import application_detail_dto, application_dto, interview_dto

router = APIRouter(prefix="/applications", tags=["applications"])
admin = require_role(Role.ADMIN)
candidate_only = require_role(Role.CANDIDATE)
interviewer_only = require_role(Role.INTERVIEWER)
staff = require_role(Role.ADMIN, Role.INTERVIEWER)


def _get_application(db: Session, application_id: int) -> Application:
    application = repository.get_application(db, application_id)
    if application is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Application not found")
    return application


def _authorize_view(db: Session, application: Application, user: User) -> None:
    if user.role == Role.ADMIN:
        return
    if user.role == Role.CANDIDATE and application.candidate.user_id == user.id:
        return
    if user.role == Role.INTERVIEWER:
        interview = repository.get_interview(db, application.id)
        if interview and interview.interviewer_id == user.id:
            return
    raise HTTPException(status.HTTP_403_FORBIDDEN, "Not authorized for this application")


def _authorize_owner(application: Application, user: User) -> None:
    if application.candidate.user_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not your application")


@router.get("", response_model=list[ApplicationOut])
def list_applications(db: Session = Depends(get_db), _=Depends(admin)) -> list[ApplicationOut]:
    return [application_dto(a) for a in repository.list_applications(db)]


@router.get("/mine", response_model=list[ApplicationOut])
def my_applications(db: Session = Depends(get_db), user=Depends(candidate_only)) -> list[ApplicationOut]:
    mine = [
        a
        for a in repository.list_applications(db)
        if a.candidate is not None and a.candidate.user_id == user.id
    ]
    return [application_dto(a) for a in mine]


@router.get("/{application_id}", response_model=ApplicationDetail)
def get_application(
    application_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)
) -> ApplicationDetail:
    application = _get_application(db, application_id)
    _authorize_view(db, application, user)
    return application_detail_dto(
        application, repository.telemetry_summary(db, application.id)
    )


@router.get("/{application_id}/questions", response_model=list[QuestionPublic])
def get_questions(
    application_id: int, db: Session = Depends(get_db), user=Depends(candidate_only)
) -> list[QuestionPublic]:
    application = _get_application(db, application_id)
    _authorize_owner(application, user)
    return qa_service.get_questions(db, application)


@router.post("/{application_id}/answers", response_model=AnswerOut)
def submit_answer(
    application_id: int,
    payload: AnswerSubmit,
    db: Session = Depends(get_db),
    user=Depends(candidate_only),
) -> AnswerOut:
    application = _get_application(db, application_id)
    _authorize_owner(application, user)
    from ai import AnswerScorer, build_client

    return qa_service.submit_answer(db, application, payload, AnswerScorer(build_client()), user)


@router.post("/{application_id}/telemetry", status_code=202)
def record_telemetry(
    application_id: int,
    events: list[TelemetryItem],
    db: Session = Depends(get_db),
    user=Depends(candidate_only),
) -> dict:
    application = _get_application(db, application_id)
    _authorize_owner(application, user)
    from models import TelemetryEvent

    for event in events:
        db.add(
            TelemetryEvent(
                application_id=application.id, event_type=event.event_type, details=event.details
            )
        )
    db.commit()
    return {"recorded": len(events)}


@router.post("/{application_id}/assign-interviewer", response_model=InterviewOut)
def assign_interviewer(
    application_id: int,
    payload: AssignInterviewerRequest,
    db: Session = Depends(get_db),
    user=Depends(admin),
) -> InterviewOut:
    application = _get_application(db, application_id)
    return interview_service.assign_interviewer(db, application, payload, user)


@router.post("/{application_id}/decision", response_model=InterviewOut)
def record_decision(
    application_id: int,
    payload: DecisionRequest,
    db: Session = Depends(get_db),
    user=Depends(interviewer_only),
) -> InterviewOut:
    application = _get_application(db, application_id)
    return interview_service.record_decision(db, application, payload, user)


@router.post("/{application_id}/notes", response_model=InterviewOut)
def add_note(
    application_id: int,
    payload: NoteRequest,
    db: Session = Depends(get_db),
    user=Depends(staff),
) -> InterviewOut:
    application = _get_application(db, application_id)
    if user.role == Role.INTERVIEWER:
        interview = repository.get_interview(db, application.id)
        if interview is None or interview.interviewer_id != user.id:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Not your assigned interview")
    return interview_service.add_note(db, application, payload.note, user)


@router.post("/{application_id}/next-steps", response_model=ApplicationOut)
def set_next_steps(
    application_id: int,
    payload: NextStepsRequest,
    db: Session = Depends(get_db),
    user=Depends(admin),
) -> ApplicationOut:
    application = _get_application(db, application_id)
    updated = application_service.set_next_steps(db, application, payload.next_steps, user)
    return application_dto(updated)


@router.post("/{application_id}/invite", response_model=MessageResponse)
def send_invitation(
    application_id: int, db: Session = Depends(get_db), user=Depends(admin)
) -> MessageResponse:
    """Stubbed invitation (in-app toast + logged event; no real email)."""
    application = _get_application(db, application_id)
    return application_service.send_invitation(db, application, user)
