from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from auth import require_role
from database import get_db
from models import Role
from repositories import repository
from schemas.dto import InterviewerAssignment

router = APIRouter(prefix="/interviewer", tags=["interviewer"])
interviewer = require_role(Role.INTERVIEWER)


@router.get("/assignments", response_model=list[InterviewerAssignment])
def assignments(db: Session = Depends(get_db), user=Depends(interviewer)) -> list[InterviewerAssignment]:
    out: list[InterviewerAssignment] = []
    for interview in repository.interviews_for_interviewer(db, user.id):
        application = interview.application
        if application is None:
            continue
        out.append(
            InterviewerAssignment(
                application_id=application.id,
                candidate_id=application.candidate_id,
                candidate_name=application.candidate.name if application.candidate else "",
                jd_title=application.jd.title if application.jd else "",
                status=application.status,
                band=application.band,
                combined_score=application.combined_score,
                scheduled_at=interview.scheduled_at,
                interview_status=interview.status,
                decision=interview.decision,
            )
        )
    return out
