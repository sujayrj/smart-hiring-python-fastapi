from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ai import build_client
from auth import require_role
from database import get_db
from models import Role
from repositories import repository
from schemas import ScreeningResult
from services import ScreeningService

router = APIRouter(prefix="/jds", tags=["screening"])
admin = require_role(Role.ADMIN)


@router.post("/{jd_id}/resume-score", response_model=ScreeningResult)
def run_resume_screening(
    jd_id: int, db: Session = Depends(get_db), user=Depends(admin)
) -> ScreeningResult:
    jd = repository.get_jd(db, jd_id)
    if jd is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Job description not found")
    service = ScreeningService(db, matcher=__import__("ai").ResumeMatcher(build_client()))
    return service.run_for_jd(jd, user)
