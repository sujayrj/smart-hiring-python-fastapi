from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from auth import require_role
from database import get_db
from models import Role
from repositories import repository
from schemas import FlagOut

router = APIRouter(prefix="/flags", tags=["flags"])
admin = require_role(Role.ADMIN)


@router.get("", response_model=list[FlagOut])
def list_flags(db: Session = Depends(get_db), _=Depends(admin)) -> list[FlagOut]:
    return [FlagOut.model_validate(flag) for flag in repository.list_flags(db)]
