from sqlalchemy.orm import Session
from app.models.project import Project

class ProjectRepository:
    def list(self, db: Session) -> list[Project]:
        return db.query(Project).order_by(Project.id.desc()).all()

    def get(self, db: Session, project_id: int) -> Project | None:
        return db.query(Project).filter(Project.id == project_id).first()

    def create(self, db: Session, project: Project) -> Project:
        db.add(project)
        db.commit()
        db.refresh(project)
        return project
