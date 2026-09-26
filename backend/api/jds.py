from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from auth import require_role
from database import get_db
from models import Role
from repositories import repository
from schemas import JDCreate, JDDetail, JDOut, JDUpdate
from services import jd_service
from services.serializers import jd_dto

router = APIRouter(prefix="/jds", tags=["jds"])
admin = require_role(Role.ADMIN)


@router.get("", response_model=list[JDOut])
def list_jds(db: Session = Depends(get_db), _=Depends(admin)) -> list[JDOut]:
    return [jd_dto(jd) for jd in repository.list_jds(db)]


@router.post("", response_model=JDDetail, status_code=201)
def create_jd(
    payload: JDCreate, db: Session = Depends(get_db), user=Depends(admin)
) -> JDDetail:
    jd = jd_service.create_jd(db, payload, user)
    return jd_dto(jd, detail=True)


@router.get("/{jd_id}", response_model=JDDetail)
def get_jd(jd_id: int, db: Session = Depends(get_db), _=Depends(admin)) -> JDDetail:
    jd = repository.get_jd(db, jd_id)
    if jd is None:
        from fastapi import HTTPException, status

        raise HTTPException(status.HTTP_404_NOT_FOUND, "Job description not found")
    return jd_dto(jd, detail=True)


@router.put("/{jd_id}", response_model=JDDetail)
def update_jd(
    jd_id: int, payload: JDUpdate, db: Session = Depends(get_db), user=Depends(admin)
) -> JDDetail:
    jd = jd_service.update_jd(db, jd_id, payload, user)
    return jd_dto(jd, detail=True)


@router.delete("/{jd_id}", status_code=204)
def delete_jd(jd_id: int, db: Session = Depends(get_db), user=Depends(admin)) -> None:
    jd_service.delete_jd(db, jd_id, user)
