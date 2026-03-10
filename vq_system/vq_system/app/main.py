from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.session import engine
from app.db.base import Base

from app.routers.auth import router as auth_router
from app.routers.projects import router as projects_router
from app.routers.topics import router as topics_router
from app.routers.departments import router as departments_router
from app.routers.positions import router as positions_router
from app.routers.vq import router as vq_router

from app.web.pages import router as web_router
from app.web.vq_page import router as vq_page_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.APP_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(projects_router)
app.include_router(topics_router)
app.include_router(departments_router)
app.include_router(positions_router)
app.include_router(vq_router)

app.include_router(web_router)
app.include_router(vq_page_router)

@app.get("/health")
def health():
    return {"ok": True, "env": settings.ENV}
