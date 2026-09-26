from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from auth import require_role
from database import get_db
from models import Role
from repositories import repository
from schemas import AuditOut

router = APIRouter(prefix="/audit", tags=["audit"])
admin = require_role(Role.ADMIN)


@router.get("", response_model=list[AuditOut])
def list_audit(db: Session = Depends(get_db), _=Depends(admin)) -> list[AuditOut]:
    return [AuditOut.model_validate(event) for event in repository.list_audit(db)]
