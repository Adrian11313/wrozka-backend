from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.position import PositionUpsert, PositionOut, PositionHistoryOut
from app.services.position_service import PositionService
from app.core.deps import get_current_user
from app.models.position import Position

router = APIRouter(prefix="/api/positions", tags=["positions"])
svc = PositionService()

@router.post("/upsert", response_model=PositionOut)
def upsert_position(payload: PositionUpsert, db: Session = Depends(get_db), user = Depends(get_current_user)):
    try:
        return svc.upsert(db, payload.topic_id, payload.department_id, payload.content, user.id, payload.client_version)
    except ValueError as e:
        if str(e) == "CONFLICT":
            raise HTTPException(status_code=409, detail="Version conflict")
        raise

@router.get("/{position_id}/history", response_model=list[PositionHistoryOut])
def position_history(position_id: int, db: Session = Depends(get_db), _user = Depends(get_current_user)):
    return svc.history(db, position_id)

@router.get("/by_cell/{topic_id}/{department_id}", response_model=PositionOut | None)
def get_by_cell(topic_id: int, department_id: int, db: Session = Depends(get_db), _user = Depends(get_current_user)):
    p = db.query(Position).filter(Position.topic_id == topic_id, Position.department_id == department_id).first()
    return p
