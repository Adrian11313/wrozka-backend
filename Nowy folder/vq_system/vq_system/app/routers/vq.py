from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.deps import get_current_user
from app.models.topic import Topic
from app.models.department import Department
from app.models.position import Position

router = APIRouter(prefix="/api/vq", tags=["vq"])

@router.get("/{project_id}")
def get_vq_matrix(project_id: int, db: Session = Depends(get_db), _user = Depends(get_current_user)):
    topics = db.query(Topic).filter(Topic.project_id == project_id).order_by(Topic.id.asc()).all()
    departments = db.query(Department).order_by(Department.name.asc()).all()
    positions = db.query(Position).all()

    return {
        "topics": topics,
        "departments": departments,
        "positions": positions
    }
