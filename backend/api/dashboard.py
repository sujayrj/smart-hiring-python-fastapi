from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from auth import require_role
from database import get_db
from models import Role
from schemas import DashboardStats
from services import dashboard_service

router = APIRouter(prefix="/dashboard", tags=["dashboard"])
admin = require_role(Role.ADMIN)


@router.get("", response_model=DashboardStats)
def dashboard(db: Session = Depends(get_db), _=Depends(admin)) -> DashboardStats:
    return dashboard_service.stats(db)
