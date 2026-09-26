from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from auth import require_role
from database import get_db
from models import Role
from repositories import repository
from schemas import UserOut

router = APIRouter(prefix="/users", tags=["users"])
admin = require_role(Role.ADMIN)


@router.get("/interviewers", response_model=list[UserOut])
def list_interviewers(db: Session = Depends(get_db), _=Depends(admin)) -> list[UserOut]:
    return [UserOut.model_validate(u) for u in repository.list_interviewers(db)]
