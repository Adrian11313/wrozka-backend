from fastapi import APIRouter, Request, Depends, Form, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, FileResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import text, and_
from pathlib import Path

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


def attachments_count(db: Session, position_id: int) -> int:
    return int(
        db.execute(
            text("SELECT COUNT(1) FROM position_attachments WHERE position_id = :pid"),
            {"pid": position_id},
        ).scalar()
        or 0
    )


@router.get("/vq/{project_id}", response_class=HTMLResponse)
def vq_page(project_id: int, request: Request, db: Session = Depends(get_db)):
    if not request.cookies.get("access_token"):
        return RedirectResponse(url="/login", status_code=302)

    topics = (
        db.query(Topic).filter(Topic.project_id == project_id).order_by(Topic.id.asc()).all()
    )
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

    p = db.query(Position).filter(and_(Position.topic_id == topic_id, Position.department_id == department_id)).first()
    if not p:
        return None

    last = get_last_history_row(db, p.id)

    return {
        "id": p.id,
        "topic_id": p.topic_id,
        "department_id": p.department_id,
        "content": p.content,
        "version": p.version,
        "status": getattr(p, "status", None),
        "priority": getattr(p, "priority", None),
        "owner": getattr(p, "owner", None),
        "due_date": getattr(p, "due_date", None),
        "last_changed_at": last.changed_at.isoformat() if last and last.changed_at else None,
        "last_changed_by": last.changed_by if last else None,
        "attachments_count": attachments_count(db, p.id),
    }


@router.get("/web/positions/history/by_cell/{topic_id}/{department_id}")
def web_history_by_cell(topic_id: int, department_id: int, request: Request, db: Session = Depends(get_db)):
    if not request.cookies.get("access_token"):
        return JSONResponse({"detail": "unauthorized"}, status_code=401)

    p = db.query(Position).filter(and_(Position.topic_id == topic_id, Position.department_id == department_id)).first()
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
            "old_status": getattr(r, "old_status", None),
            "new_status": getattr(r, "new_status", None),
            "old_priority": getattr(r, "old_priority", None),
            "new_priority": getattr(r, "new_priority", None),
            "old_owner": getattr(r, "old_owner", None),
            "new_owner": getattr(r, "new_owner", None),
            "old_due_date": getattr(r, "old_due_date", None),
            "new_due_date": getattr(r, "new_due_date", None),
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
    status: str | None = Form(None),
    priority: str | None = Form(None),
    owner: str | None = Form(None),
    due_date: str | None = Form(None),
    db: Session = Depends(get_db),
):
    user_id = current_user_id_from_cookie(request, db)
    if user_id is None:
        return JSONResponse({"detail": "unauthorized"}, status_code=401)

    svc = PositionService()
    try:
        p = svc.upsert(
            db,
            topic_id,
            department_id,
            content if content != "" else None,
            user_id,
            client_version,
            status=status,
            priority=priority,
            owner=owner,
            due_date=due_date,
        )

        last = get_last_history_row(db, p.id)

        return {
            "id": p.id,
            "topic_id": p.topic_id,
            "department_id": p.department_id,
            "content": p.content,
            "version": p.version,
            "status": getattr(p, "status", None),
            "priority": getattr(p, "priority", None),
            "owner": getattr(p, "owner", None),
            "due_date": getattr(p, "due_date", None),
            "last_changed_at": last.changed_at.isoformat() if last and last.changed_at else None,
            "last_changed_by": last.changed_by if last else None,
            "attachments_count": attachments_count(db, p.id),
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

    p = db.query(Position).filter(and_(Position.topic_id == topic_id, Position.department_id == department_id)).first()
    if not p:
        return JSONResponse({"detail": "not_found"}, status_code=404)

    if int(client_version) != int(p.version):
        return JSONResponse({"detail": "conflict"}, status_code=409)

    h = db.query(PositionHistory).filter(PositionHistory.id == history_id).first()
    if not h or h.position_id != p.id:
        return JSONResponse({"detail": "bad_history"}, status_code=400)

    old_content = p.content
    old_version = p.version
    old_status = getattr(p, "status", None)
    old_priority = getattr(p, "priority", None)
    old_owner = getattr(p, "owner", None)
    old_due_date = getattr(p, "due_date", None)

    new_content = h.new_content
    new_status = getattr(h, "new_status", None)
    new_priority = getattr(h, "new_priority", None)
    new_owner = getattr(h, "new_owner", None)
    new_due_date = getattr(h, "new_due_date", None)

    p.content = new_content
    p.status = new_status
    p.priority = new_priority
    p.owner = new_owner
    p.due_date = new_due_date
    p.version = int(p.version) + 1

    db.add(
        PositionHistory(
            position_id=p.id,
            old_content=old_content,
            new_content=new_content,
            old_version=old_version,
            new_version=p.version,
            changed_by=user_id,
            old_status=old_status,
            new_status=new_status,
            old_priority=old_priority,
            new_priority=new_priority,
            old_owner=old_owner,
            new_owner=new_owner,
            old_due_date=old_due_date,
            new_due_date=new_due_date,
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
        "status": getattr(p, "status", None),
        "priority": getattr(p, "priority", None),
        "owner": getattr(p, "owner", None),
        "due_date": getattr(p, "due_date", None),
        "last_changed_at": last.changed_at.isoformat() if last and last.changed_at else None,
        "last_changed_by": last.changed_by if last else None,
        "attachments_count": attachments_count(db, p.id),
    }


@router.post("/web/positions/attachments/upload")
def web_upload_attachment(
    request: Request,
    topic_id: int = Form(...),
    department_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    user_id = current_user_id_from_cookie(request, db)
    if user_id is None:
        return JSONResponse({"detail": "unauthorized"}, status_code=401)

    p = db.query(Position).filter(and_(Position.topic_id == topic_id, Position.department_id == department_id)).first()
    if not p:
        return JSONResponse({"detail": "not_found"}, status_code=404)

    import uuid
    from datetime import datetime as _dt

    up_dir = Path("uploads/positions")
    up_dir.mkdir(parents=True, exist_ok=True)

    ext = ""
    if file.filename and "." in file.filename:
        ext = "." + file.filename.split(".")[-1].lower()

    fname = str(uuid.uuid4()) + ext
    fpath = up_dir / fname

    data = file.file.read()
    fpath.write_bytes(data)

    db.execute(
        text(
            "INSERT INTO position_attachments(position_id, file_path, original_name, mime_type, uploaded_by, uploaded_at) "
            "VALUES (:pid, :fp, :on, :mt, :ub, :ua)"
        ),
        {
            "pid": p.id,
            "fp": str(fpath).replace("\\", "/"),
            "on": file.filename,
            "mt": file.content_type,
            "ub": user_id,
            "ua": _dt.utcnow().isoformat(),
        },
    )
    db.commit()

    return {"ok": True, "attachments_count": attachments_count(db, p.id)}


@router.get("/web/positions/attachments/by_cell/{topic_id}/{department_id}")
def web_list_attachments(topic_id: int, department_id: int, request: Request, db: Session = Depends(get_db)):
    if not request.cookies.get("access_token"):
        return JSONResponse({"detail": "unauthorized"}, status_code=401)

    p = db.query(Position).filter(and_(Position.topic_id == topic_id, Position.department_id == department_id)).first()
    if not p:
        return []

    rows = db.execute(
        text(
            "SELECT id, file_path, original_name, mime_type, uploaded_by, uploaded_at "
            "FROM position_attachments WHERE position_id = :pid ORDER BY id DESC LIMIT 50"
        ),
        {"pid": p.id},
    ).fetchall()

    return [
        {
            "id": r[0],
            "file_path": r[1],
            "original_name": r[2],
            "mime_type": r[3],
            "uploaded_by": r[4],
            "uploaded_at": r[5],
            "url": "/web/positions/attachments/" + str(r[0]),
        }
        for r in rows
    ]


@router.get("/web/positions/attachments/{attachment_id}")
def web_get_attachment(attachment_id: int, request: Request, db: Session = Depends(get_db)):
    if not request.cookies.get("access_token"):
        return JSONResponse({"detail": "unauthorized"}, status_code=401)

    row = db.execute(
        text("SELECT file_path, mime_type, original_name FROM position_attachments WHERE id = :id"),
        {"id": attachment_id},
    ).fetchone()
    if not row:
        return JSONResponse({"detail": "not_found"}, status_code=404)

    fp, mt, on = row[0], row[1], row[2]
    if not Path(fp).exists():
        return JSONResponse({"detail": "file_missing"}, status_code=404)

    return FileResponse(fp, media_type=mt or "application/octet-stream", filename=on or Path(fp).name)

