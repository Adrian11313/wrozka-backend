import re
from pathlib import Path
from datetime import datetime
p = Path("app/web/vq_page.py")
src = p.read_text(encoding="utf-8")
bak = p.with_suffix(p.suffix + ".bak_meta_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
bak.write_text(src, encoding="utf-8")
print("Backup:", bak)
out = src
# 1) import UploadFile/File jeśli brakuje
if "UploadFile" not in out or "File" not in out:
    out = out.replace(
        "from fastapi import APIRouter, Request, Depends, Form",
        "from fastapi import APIRouter, Request, Depends, Form, UploadFile, File"
    )
# 2) web_upsert: dopisz Form pola meta i przekaż do service
if "status:" not in out and '"/web/positions/upsert"' in out:
    out = re.sub(
        r"def web_upsert\(\s*request: Request,\s*topic_id: int = Form\(\.\.\.\),\s*department_id: int = Form\(\.\.\.\),\s*content: str = Form\(\"\"\),\s*client_version: int = Form\(\.\.\.\),",
        "def web_upsert(\n"
        "    request: Request,\n"
        "    topic_id: int = Form(...),\n"
        "    department_id: int = Form(...),\n"
        "    content: str = Form(\"\"),\n"
        "    client_version: int = Form(...),\n"
        "    status: str | None = Form(None),\n"
        "    priority: str | None = Form(None),\n"
        "    owner: str | None = Form(None),\n"
        "    due_date: str | None = Form(None),\n",
        out,
        count=1
    )
out = re.sub(
    r"svc\.upsert\(\s*db,\s*topic_id,\s*department_id,\s*content if content != \"\" else None,\s*user_id,\s*client_version\s*\)",
    "svc.upsert(db, topic_id, department_id, content if content != \"\" else None, user_id, client_version, status=status, priority=priority, owner=owner, due_date=due_date)",
    out,
    count=1
)
# 3) do return w upsert/by_cell dopnij meta + attachments_count (jeśli nie ma)
if '"status"' not in out:
    out = out.replace(
        '"content": p.content,\n            "version": p.version,',
        '"content": p.content,\n            "version": p.version,\n            "status": getattr(p, "status", None),\n            "priority": getattr(p, "priority", None),\n            "owner": getattr(p, "owner", None),\n            "due_date": getattr(p, "due_date", None),'
    )
if "attachments_count" not in out:
    out = out.replace(
        '"last_changed_by": last.changed_by if last else None,',
        '"last_changed_by": last.changed_by if last else None,\n            "attachments_count": db.execute("SELECT COUNT(1) FROM position_attachments WHERE position_id = :pid", {"pid": p.id}).scalar() or 0,'
    )
# 4) dopisz restore + upload/list/get jeśli nie istnieje
if '"/web/positions/restore"' not in out:
    out += """
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
        Position.department_id == department_id
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
    db.add(PositionHistory(
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
    ))
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
        "attachments_count": db.execute("SELECT COUNT(1) FROM position_attachments WHERE position_id = :pid", {"pid": p.id}).scalar() or 0,
    }
"""
if '"/web/positions/attachments/upload"' not in out:
    out += """
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
    p = db.query(Position).filter(Position.topic_id == topic_id, Position.department_id == department_id).first()
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
        "INSERT INTO position_attachments(position_id, file_path, original_name, mime_type, uploaded_by, uploaded_at) "
        "VALUES (:pid, :fp, :on, :mt, :ub, :ua)",
        {
            "pid": p.id,
            "fp": str(fpath).replace("\\\\", "/"),
            "on": file.filename,
            "mt": file.content_type,
            "ub": user_id,
            "ua": _dt.utcnow().isoformat(),
        }
    )
    db.commit()
    cnt = db.execute("SELECT COUNT(1) FROM position_attachments WHERE position_id = :pid", {"pid": p.id}).scalar() or 0
    return {"ok": True, "attachments_count": cnt}
@router.get("/web/positions/attachments/by_cell/{topic_id}/{department_id}")
def web_list_attachments(topic_id: int, department_id: int, request: Request, db: Session = Depends(get_db)):
    if not request.cookies.get("access_token"):
        return JSONResponse({"detail": "unauthorized"}, status_code=401)
    p = db.query(Position).filter(Position.topic_id == topic_id, Position.department_id == department_id).first()
    if not p:
        return []
    rows = db.execute(
        "SELECT id, file_path, original_name, mime_type, uploaded_by, uploaded_at "
        "FROM position_attachments WHERE position_id = :pid ORDER BY id DESC LIMIT 50",
        {"pid": p.id}
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
        "SELECT file_path, mime_type, original_name FROM position_attachments WHERE id = :id",
        {"id": attachment_id}
    ).fetchone()
    if not row:
        return JSONResponse({"detail": "not_found"}, status_code=404)
    from fastapi.responses import FileResponse
    fp, mt, on = row[0], row[1], row[2]
    if not Path(fp).exists():
        return JSONResponse({"detail": "file_missing"}, status_code=404)
    return FileResponse(fp, media_type=mt or "application/octet-stream", filename=on or Path(fp).name)
"""
p.write_text(out, encoding="utf-8")
print("DONE router patch")
