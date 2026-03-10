from sqlalchemy.orm import Session
from app.models.topic import Topic

class TopicRepository:
    def list_by_project(self, db: Session, project_id: int) -> list[Topic]:
        return db.query(Topic).filter(Topic.project_id == project_id).order_by(Topic.id.asc()).all()

    def get(self, db: Session, topic_id: int) -> Topic | None:
        return db.query(Topic).filter(Topic.id == topic_id).first()

    def create(self, db: Session, topic: Topic) -> Topic:
        db.add(topic)
        db.commit()
        db.refresh(topic)
        return topic
