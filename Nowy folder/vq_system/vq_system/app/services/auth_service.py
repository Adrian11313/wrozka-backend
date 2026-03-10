from sqlalchemy.orm import Session
from app.core.security import hash_password, verify_password, create_access_token
from app.models.user import User
from app.repositories.user_repo import UserRepository

class AuthService:
    def __init__(self) -> None:
        self.users = UserRepository()

    def register(self, db: Session, username: str, password: str, department_id: int | None, role: str) -> User:
        existing = self.users.get_by_username(db, username)
        if existing:
            raise ValueError("USERNAME_TAKEN")
        u = User(username=username, password_hash=hash_password(password), department_id=department_id, role=role)
        return self.users.create(db, u)

    def login(self, db: Session, username: str, password: str) -> str:
        u = self.users.get_by_username(db, username)
        if not u or not verify_password(password, u.password_hash):
            raise ValueError("INVALID_CREDENTIALS")
        token = create_access_token(subject=str(u.id), extra={"username": u.username, "role": u.role})
        return token
