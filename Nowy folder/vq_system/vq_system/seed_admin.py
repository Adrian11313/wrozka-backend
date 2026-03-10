from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.core.security import hash_password
from app.models.user import User

def run():
    db: Session = SessionLocal()
    try:
        username = "admin"
        existing = db.query(User).filter(User.username == username).first()
        if existing:
            print("Admin already exists:", existing.username)
            return
        u = User(username=username, password_hash=hash_password("admin123"), role="admin")
        db.add(u)
        db.commit()
        print("Created admin: admin / admin123")
    finally:
        db.close()

if __name__ == "__main__":
    run()
