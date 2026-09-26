from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from auth import require_role
from database import get_db
from models import Role
from schemas import CandidateDetail, CandidateOut
from services import candidate_service

router = APIRouter(prefix="/candidates", tags=["candidates"])
staff = require_role(Role.ADMIN, Role.INTERVIEWER)


@router.get("", response_model=list[CandidateOut])
def list_candidates(db: Session = Depends(get_db), user=Depends(staff)) -> list[CandidateOut]:
    return candidate_service.list_candidates(db, user)


@router.get("/{candidate_id}", response_model=CandidateDetail)
def get_candidate(
    candidate_id: int, db: Session = Depends(get_db), user=Depends(staff)
) -> CandidateDetail:
    return candidate_service.get_candidate(db, candidate_id, user)
