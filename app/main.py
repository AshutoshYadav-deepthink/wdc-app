"""
WDC App — Main FastAPI Application
Entry point: `uvicorn app.main:app --reload`
"""
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

from .config import BASE_DIR, settings
from .routers import auth, public, student, admin, notifications

BASE_DIR = Path(__file__).resolve().parent.parent

app = FastAPI(
    title="WDC App — Women Development Cell",
    description="College WDC web app (Python + FastAPI + Firebase).",
    version="1.0.0",
)

# CORS
origins = ["*"] if settings.cors_origins == "*" else settings.cors_origins.split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static + templates
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "app" / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "app" / "templates"))

# API routers
app.include_router(auth.router)
app.include_router(public.router)
app.include_router(student.router)
app.include_router(admin.router)
app.include_router(notifications.router)


@app.on_event("startup")
def on_startup():
    """Auto-seed local DB on first run if it looks empty."""
    from .services import db
    if db.count("users") == 0:
        print("[WDC] Empty DB detected — running seed...")
        try:
            from .seed import run_seed
            run_seed()
            print("[WDC] Seed complete.")
        except Exception as e:
            print(f"[WDC] Seed failed (you can run scripts/seed_data.py manually): {e}")


# ---------- Page routes (HTML) ----------
@app.get("/", response_class=HTMLResponse)
def page_public_dashboard(request: Request):
    """Public WDC dashboard — opens first per requirements."""
    return templates.TemplateResponse("public_dashboard.html", {
        "request": request,
        "page": "public",
    })


@app.get("/login", response_class=HTMLResponse)
def page_login(request: Request):
    """Combined Student Login + Sign Up page."""
    return templates.TemplateResponse("auth.html", {
        "request": request,
        "page": "auth",
    })


@app.get("/student", response_class=HTMLResponse)
def page_student_dashboard(request: Request):
    return templates.TemplateResponse("student_dashboard.html", {
        "request": request,
        "page": "student",
    })


@app.get("/admin", response_class=HTMLResponse)
def page_admin_dashboard(request: Request):
    return templates.TemplateResponse("admin_dashboard.html", {
        "request": request,
        "page": "admin",
    })


@app.get("/favicon.ico")
def favicon():
    f = BASE_DIR / "app" / "static" / "img" / "favicon.ico"
    if f.exists():
        return FileResponse(f)
    return {"ok": False}


@app.get("/api/health")
def health():
    return {"ok": True, "service": "WDC App", "firebase": settings.use_firebase}
