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
        client_version: int,
        status: str | None = None,
        priority: str | None = None,
        owner: str | None = None,
        due_date: str | None = None,
    ) -> Position:
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
                status=status,
                priority=priority,
                owner=owner,
                due_date=due_date,
            )
            db.add(p)
            db.flush()  # p.id
            h = PositionHistory(
                position_id=p.id,
                old_content=None,
                new_content=p.content,
                old_version=0,
                new_version=p.version,
                changed_by=user_id,
                old_status=None,
                new_status=status,
                old_priority=None,
                new_priority=priority,
                old_owner=None,
                new_owner=owner,
                old_due_date=None,
                new_due_date=due_date,
            )
            db.add(h)
            db.commit()
            db.refresh(p)
            return p
        # CONFLICT
        if int(client_version) != int(p.version):
            raise ValueError("CONFLICT")
        # UPDATE
        old_content = p.content
        old_version = int(p.version)
        old_status = getattr(p, "status", None)
        old_priority = getattr(p, "priority", None)
        old_owner = getattr(p, "owner", None)
        old_due_date = getattr(p, "due_date", None)
        p.content = content
        p.status = status
        p.priority = priority
        p.owner = owner
        p.due_date = due_date
        p.version = old_version + 1
        h = PositionHistory(
            position_id=p.id,
            old_content=old_content,
            new_content=p.content,
            old_version=old_version,
            new_version=p.version,
            changed_by=user_id,
            old_status=old_status,
            new_status=status,
            old_priority=old_priority,
            new_priority=priority,
            old_owner=old_owner,
            new_owner=owner,
            old_due_date=old_due_date,
            new_due_date=due_date,
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
