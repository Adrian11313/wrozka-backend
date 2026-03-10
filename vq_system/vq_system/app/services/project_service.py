from sqlalchemy.orm import Session
from app.models.project import Project
from app.repositories.project_repo import ProjectRepository

class ProjectService:
    def __init__(self) -> None:
        self.repo = ProjectRepository()

    def list(self, db: Session) -> list[Project]:
        return self.repo.list(db)

    def create(self, db: Session, name: str) -> Project:
        p = Project(name=name)
        return self.repo.create(db, p)
