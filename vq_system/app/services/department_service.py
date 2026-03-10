from sqlalchemy.orm import Session
from app.models.department import Department
from app.repositories.department_repo import DepartmentRepository

class DepartmentService:
    def __init__(self) -> None:
        self.repo = DepartmentRepository()

    def list(self, db: Session) -> list[Department]:
        return self.repo.list(db)

    def create(self, db: Session, name: str) -> Department:
        existing = self.repo.get_by_name(db, name)
        if existing:
            return existing
        d = Department(name=name)
        return self.repo.create(db, d)
