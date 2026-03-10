from sqlalchemy.orm import Session
from app.models.department import Department

class DepartmentRepository:
    def list(self, db: Session) -> list[Department]:
        return db.query(Department).order_by(Department.name.asc()).all()

    def get_by_name(self, db: Session, name: str) -> Department | None:
        return db.query(Department).filter(Department.name == name).first()

    def create(self, db: Session, dep: Department) -> Department:
        db.add(dep)
        db.commit()
        db.refresh(dep)
        return dep
