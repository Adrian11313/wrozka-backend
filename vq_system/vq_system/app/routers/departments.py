from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.department import DepartmentCreate, DepartmentOut
from app.services.department_service import DepartmentService
from app.core.deps import get_current_user

router = APIRouter(prefix="/api/departments", tags=["departments"])
svc = DepartmentService()

@router.get("/", response_model=list[DepartmentOut])
def list_departments(db: Session = Depends(get_db), _user = Depends(get_current_user)):
    return svc.list(db)

@router.post("/", response_model=DepartmentOut)
def create_department(payload: DepartmentCreate, db: Session = Depends(get_db), _user = Depends(get_current_user)):
    return svc.create(db, payload.name)
