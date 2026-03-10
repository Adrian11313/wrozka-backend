from sqlalchemy.orm import Session
from app.models.position import Position
from app.models.position_history import PositionHistory

class PositionRepository:
    def get_by_topic_department(self, db: Session, topic_id: int, department_id: int) -> Position | None:
        return db.query(Position).filter(
            Position.topic_id == topic_id,
            Position.department_id == department_id
        ).first()

    def create(self, db: Session, pos: Position) -> Position:
        db.add(pos)
        db.commit()
        db.refresh(pos)
        return pos

    def list_history(self, db: Session, position_id: int) -> list[PositionHistory]:
        return db.query(PositionHistory).filter(
            PositionHistory.position_id == position_id
        ).order_by(PositionHistory.id.desc()).all()

    def update_with_optimistic_lock(
        self,
        db: Session,
        pos: Position,
        new_content: str | None,
        user_id: int | None,
        client_version: int
    ) -> Position:
        if pos.version != client_version:
            raise ValueError("CONFLICT")

        hist = PositionHistory(
            position_id=pos.id,
            old_content=pos.content,
            new_content=new_content,
            old_version=pos.version,
            new_version=pos.version + 1,
            changed_by=user_id
        )
        db.add(hist)

        pos.content = new_content
        pos.version = pos.version + 1
        pos.last_updated_by = user_id

        db.commit()
        db.refresh(pos)
        return pos
