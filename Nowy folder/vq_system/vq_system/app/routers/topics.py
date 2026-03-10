from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.topic import TopicCreate, TopicOut
from app.services.topic_service import TopicService
from app.core.deps import get_current_user

router = APIRouter(prefix="/api/topics", tags=["topics"])
svc = TopicService()

@router.get("/by_project/{project_id}", response_model=list[TopicOut])
def list_topics(project_id: int, db: Session = Depends(get_db), _user = Depends(get_current_user)):
    return svc.list_by_project(db, project_id)

@router.post("/", response_model=TopicOut)
def create_topic(payload: TopicCreate, db: Session = Depends(get_db), _user = Depends(get_current_user)):
    return svc.create(db, payload.project_id, payload.title, payload.description)
