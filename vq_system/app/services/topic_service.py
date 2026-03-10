from sqlalchemy.orm import Session
from app.models.topic import Topic
from app.repositories.topic_repo import TopicRepository

class TopicService:
    def __init__(self) -> None:
        self.repo = TopicRepository()

    def list_by_project(self, db: Session, project_id: int) -> list[Topic]:
        return self.repo.list_by_project(db, project_id)

    def create(self, db: Session, project_id: int, title: str, description: str | None) -> Topic:
        t = Topic(project_id=project_id, title=title, description=description)
        return self.repo.create(db, t)
