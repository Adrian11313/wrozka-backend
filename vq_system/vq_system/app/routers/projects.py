from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.project import ProjectCreate, ProjectOut
from app.services.project_service import ProjectService
from app.core.deps import get_current_user

router = APIRouter(prefix="/api/projects", tags=["projects"])
svc = ProjectService()

@router.get("/", response_model=list[ProjectOut])
def list_projects(db: Session = Depends(get_db), _user = Depends(get_current_user)):
    return svc.list(db)

@router.post("/", response_model=ProjectOut)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db), _user = Depends(get_current_user)):
    return svc.create(db, payload.name)
