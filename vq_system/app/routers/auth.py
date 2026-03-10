from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.user import UserCreate, UserOut, TokenOut
from app.services.auth_service import AuthService
from app.core.deps import require_role

router = APIRouter(prefix="/api/auth", tags=["auth"])
svc = AuthService()

@router.post("/register", response_model=UserOut)
def register(payload: UserCreate, db: Session = Depends(get_db), _admin = Depends(require_role("admin"))):
    try:
        return svc.register(db, payload.username, payload.password, payload.department_id, payload.role)
    except ValueError as e:
        if str(e) == "USERNAME_TAKEN":
            raise HTTPException(status_code=409, detail="Username already taken")
        raise

@router.post("/login", response_model=TokenOut)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    try:
        token = svc.login(db, form.username, form.password)
        return TokenOut(access_token=token)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid credentials")
