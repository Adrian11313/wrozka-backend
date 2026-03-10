from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.project_service import ProjectService
from app.services.auth_service import AuthService
from app.services.topic_service import TopicService
from app.services.department_service import DepartmentService

templates = Jinja2Templates(directory="app/web/templates")
router = APIRouter(tags=["web"])

def require_login(request: Request):
    if not request.cookies.get("access_token"):
        return RedirectResponse(url="/login", status_code=302)
    return None

@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": None})

@router.post("/login")
def login_action(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    svc = AuthService()
    try:
        token = svc.login(db, username, password)
        resp = RedirectResponse(url="/projects", status_code=302)
        # HttpOnly cookie so browser sends it automatically
        resp.set_cookie("access_token", token, httponly=True)
        return resp
    except Exception:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Bdny login/haso"})

@router.get("/logout")
def logout():
    resp = RedirectResponse(url="/", status_code=302)
    resp.delete_cookie("access_token")
    return resp

@router.get("/projects", response_class=HTMLResponse)
def projects_page(request: Request, db: Session = Depends(get_db)):
    redir = require_login(request)
    if redir: return redir

    ps = ProjectService()
    projects = ps.list(db)
    return templates.TemplateResponse("projects.html", {"request": request, "projects": projects})

@router.post("/projects/create")
def projects_create(request: Request, name: str = Form(...), db: Session = Depends(get_db)):
    redir = require_login(request)
    if redir: return redir

    ps = ProjectService()
    ps.create(db, name)
    return RedirectResponse(url="/projects", status_code=302)

@router.get("/departments", response_class=HTMLResponse)
def departments_page(request: Request, db: Session = Depends(get_db)):
    redir = require_login(request)
    if redir: return redir

    ds = DepartmentService()
    deps = ds.list(db)
    return templates.TemplateResponse("departments.html", {"request": request, "departments": deps})

@router.post("/departments/create")
def departments_create(request: Request, name: str = Form(...), db: Session = Depends(get_db)):
    redir = require_login(request)
    if redir: return redir

    ds = DepartmentService()
    ds.create(db, name)
    return RedirectResponse(url="/departments", status_code=302)

@router.get("/topics/{project_id}", response_class=HTMLResponse)
def topics_page(project_id: int, request: Request, db: Session = Depends(get_db)):
    redir = require_login(request)
    if redir: return redir

    ts = TopicService()
    topics = ts.list_by_project(db, project_id)
    return templates.TemplateResponse("topics.html", {"request": request, "project_id": project_id, "topics": topics})

@router.post("/topics/{project_id}/create")
def topics_create(project_id: int, request: Request, title: str = Form(...), description: str = Form(""), db: Session = Depends(get_db)):
    redir = require_login(request)
    if redir: return redir

    ts = TopicService()
    ts.create(db, project_id, title, description if description else None)
    return RedirectResponse(url=f"/topics/{project_id}", status_code=302)
