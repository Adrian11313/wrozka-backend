from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.position import Position
from app.models.position_history import PositionHistory

class PositionService:
    def upsert(
        self,
        db: Session,
        topic_id: int,
        department_id: int,
        content: str | None,
        user_id: int,
        client_version: int
    ):
        p = db.query(Position).filter(
            and_(Position.topic_id == topic_id, Position.department_id == department_id)
        ).first()

        # CREATE
        if p is None:
            p = Position(
                topic_id=topic_id,
                department_id=department_id,
                content=content,
                version=1,
            )
            db.add(p)
            db.flush()  # ensures p.id is available

            h = PositionHistory(
                position_id=p.id,
                old_content=None,
                new_content=p.content,
                old_version=0,
                new_version=p.version,
                changed_by=user_id,
            )
            db.add(h)

            db.commit()
            db.refresh(p)
            return p

        # CONFLICT CHECK
        if int(client_version) != int(p.version):
            raise ValueError("CONFLICT")

        # UPDATE
        old_content = p.content
        old_version = int(p.version)

        p.content = content
        p.version = old_version + 1

        h = PositionHistory(
            position_id=p.id,
            old_content=old_content,
            new_content=p.content,
            old_version=old_version,
            new_version=p.version,
            changed_by=user_id,
        )
        db.add(h)

        db.commit()
        db.refresh(p)
        return p

    def history(self, db: Session, position_id: int, limit: int = 20):
        return (
            db.query(PositionHistory)
            .filter(PositionHistory.position_id == position_id)
            .order_by(PositionHistory.changed_at.desc(), PositionHistory.id.desc())
            .limit(limit)
            .all()
        )
