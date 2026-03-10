from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.topic import Topic
from app.models.department import Department
from app.models.position import Position
from app.models.position_history import PositionHistory

from app.core.security import decode_token
from app.repositories.user_repo import UserRepository
from app.services.position_service import PositionService

templates = Jinja2Templates(directory="app/web/templates")
router = APIRouter()


def current_user_id_from_cookie(request: Request, db: Session) -> int | None:
    token = request.cookies.get("access_token")
    if not token:
        return None
    try:
        payload = decode_token(token)
        user_id = int(payload.get("sub"))
    except Exception:
        return None

    u = UserRepository().get_by_id(db, user_id)
    return u.id if u else None


def get_last_history_row(db: Session, position_id: int) -> PositionHistory | None:
    return (
        db.query(PositionHistory)
        .filter(PositionHistory.position_id == position_id)
        .order_by(PositionHistory.changed_at.desc(), PositionHistory.id.desc())
        .first()
    )


@router.get("/vq/{project_id}", response_class=HTMLResponse)
def vq_page(project_id: int, request: Request, db: Session = Depends(get_db)):
    if not request.cookies.get("access_token"):
        return RedirectResponse(url="/login", status_code=302)

    topics = db.query(Topic).filter(Topic.project_id == project_id).order_by(Topic.id.asc()).all()
    departments = db.query(Department).order_by(Department.name.asc()).all()

    topic_ids = [t.id for t in topics]
    positions = db.query(Position).filter(Position.topic_id.in_(topic_ids)).all() if topic_ids else []

    pos_map = {f"{p.topic_id}_{p.department_id}": p for p in positions}

    return templates.TemplateResponse(
        "vq_matrix.html",
        {"request": request, "topics": topics, "departments": departments, "pos_map": pos_map, "project_id": project_id},
    )


@router.get("/web/positions/by_cell/{topic_id}/{department_id}")
def web_get_by_cell(topic_id: int, department_id: int, request: Request, db: Session = Depends(get_db)):
    if not request.cookies.get("access_token"):
        return JSONResponse({"detail": "unauthorized"}, status_code=401)

    p = db.query(Position).filter(Position.topic_id == topic_id, Position.department_id == department_id).first()
    if not p:
        return None

    last = get_last_history_row(db, p.id)

    return {
        "id": p.id,
        "topic_id": p.topic_id,
        "department_id": p.department_id,
        "content": p.content,
        "version": p.version,
        "last_changed_at": last.changed_at.isoformat() if last and last.changed_at else None,
        "last_changed_by": last.changed_by if last else None,
    }


@router.get("/web/positions/history/by_cell/{topic_id}/{department_id}")
def web_history_by_cell(topic_id: int, department_id: int, request: Request, db: Session = Depends(get_db)):
    if not request.cookies.get("access_token"):
        return JSONResponse({"detail": "unauthorized"}, status_code=401)

    p = db.query(Position).filter(Position.topic_id == topic_id, Position.department_id == department_id).first()
    if not p:
        return []

    rows = (
        db.query(PositionHistory)
        .filter(PositionHistory.position_id == p.id)
        .order_by(PositionHistory.changed_at.desc(), PositionHistory.id.desc())
        .limit(20)
        .all()
    )

    return [
        {
            "id": r.id,
            "old_content": r.old_content,
            "new_content": r.new_content,
            "old_version": r.old_version,
            "new_version": r.new_version,
            "changed_by": r.changed_by,
            "changed_at": r.changed_at.isoformat() if r.changed_at else None,
        }
        for r in rows
    ]


@router.post("/web/positions/upsert")
def web_upsert(
    request: Request,
    topic_id: int = Form(...),
    department_id: int = Form(...),
    content: str = Form(""),
    client_version: int = Form(...),
    db: Session = Depends(get_db),
):
    user_id = current_user_id_from_cookie(request, db)
    if user_id is None:
        return JSONResponse({"detail": "unauthorized"}, status_code=401)

    svc = PositionService()
    try:
        p = svc.upsert(db, topic_id, department_id, content if content != "" else None, user_id, client_version)

        last = get_last_history_row(db, p.id)

        return {
            "id": p.id,
            "topic_id": p.topic_id,
            "department_id": p.department_id,
            "content": p.content,
            "version": p.version,
            "last_changed_at": last.changed_at.isoformat() if last and last.changed_at else None,
            "last_changed_by": last.changed_by if last else None,
        }
    except ValueError as e:
        if str(e) == "CONFLICT":
            return JSONResponse({"detail": "conflict"}, status_code=409)
        raise


@router.post("/web/positions/restore")
def web_restore(
    request: Request,
    topic_id: int = Form(...),
    department_id: int = Form(...),
    history_id: int = Form(...),
    client_version: int = Form(...),
    db: Session = Depends(get_db),
):
    user_id = current_user_id_from_cookie(request, db)
    if user_id is None:
        return JSONResponse({"detail": "unauthorized"}, status_code=401)

    p = db.query(Position).filter(
        Position.topic_id == topic_id,
        Position.department_id == department_id,
    ).first()
    if not p:
        return JSONResponse({"detail": "not_found"}, status_code=404)

    if int(client_version) != int(p.version):
        return JSONResponse({"detail": "conflict"}, status_code=409)

    h = db.query(PositionHistory).filter(PositionHistory.id == history_id).first()
    if not h or h.position_id != p.id:
        return JSONResponse({"detail": "bad_history"}, status_code=400)

    old_content = p.content
    old_version = p.version

    new_content = h.new_content
    p.content = new_content
    p.version = int(p.version) + 1

    db.add(
        PositionHistory(
            position_id=p.id,
            old_content=old_content,
            new_content=new_content,
            old_version=old_version,
            new_version=p.version,
            changed_by=user_id,
        )
    )

    db.commit()
    db.refresh(p)

    last = get_last_history_row(db, p.id)

    return {
        "id": p.id,
        "topic_id": p.topic_id,
        "department_id": p.department_id,
        "content": p.content,
        "version": p.version,
        "last_changed_at": last.changed_at.isoformat() if last and last.changed_at else None,
        "last_changed_by": last.changed_by if last else None,
    }