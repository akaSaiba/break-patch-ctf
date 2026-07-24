from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from api import COOKIE_NAME, router as api_router
from database import (
    get_user_by_id,
    init_db,
    make_session_token,
    parse_session_token,
    verify_credentials,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Seed the SQLite database when the app starts."""
    init_db()
    yield


app = FastAPI(
    title="Security Engineering Student Portal",
    description="Intentionally vulnerable CTF challenge application.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {
            "name": "API",
            "description": "JSON API endpoints used by the portal frontend and CTF checks.",
        },
    ],
    swagger_ui_parameters={"defaultModelsExpandDepth": -1},
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

app.include_router(api_router)


def get_session_user_optional(request: Request) -> dict | None:
    """Return the logged-in user for HTML pages, or None if not authenticated."""
    user_id = parse_session_token(request.cookies.get(COOKIE_NAME))
    if user_id is None:
        return None
    return get_user_by_id(user_id)


def require_page_user(request: Request):
    """Require a logged-in user for HTML pages; otherwise redirect to /login."""
    user = get_session_user_optional(request)
    if user is None:
        return RedirectResponse(url="/login", status_code=303)
    return user


@app.get("/", include_in_schema=False)
def root():
    """Redirect the site root to the login page."""
    return RedirectResponse(url="/login")


@app.get("/login", include_in_schema=False)
def login_page(request: Request):
    """Render the login page, or redirect to dashboard if already logged in."""
    if get_session_user_optional(request):
        return RedirectResponse(url="/dashboard", status_code=303)
    return templates.TemplateResponse(request, "login.html")


@app.post("/login", include_in_schema=False)
async def login_page_fallback(request: Request):
    """Handle HTML form login against the database and set the session cookie."""
    form = await request.form()
    username = str(form.get("username", "")).strip()
    password = str(form.get("password", ""))

    user = verify_credentials(username, password)
    if user is None:
        return templates.TemplateResponse(
            request,
            "login.html",
            {"error": "Invalid username or password"},
        )

    response = RedirectResponse(url="/dashboard", status_code=303)
    response.set_cookie(
        key=COOKIE_NAME,
        value=make_session_token(user),
        httponly=True,
    )
    return response


@app.get("/dashboard", include_in_schema=False)
def dashboard(request: Request):
    """Render the student dashboard page."""
    user = require_page_user(request)
    if isinstance(user, RedirectResponse):
        return user
    return templates.TemplateResponse(request, "dashboard.html", {"user": user})


@app.get("/results", include_in_schema=False)
def results_page(request: Request):
    """Render the assignment results page."""
    user = require_page_user(request)
    if isinstance(user, RedirectResponse):
        return user
    return templates.TemplateResponse(request, "results.html", {"user": user})


@app.get("/classmates", include_in_schema=False)
def classmates_page(request: Request):
    """Render the classmates directory page."""
    user = require_page_user(request)
    if isinstance(user, RedirectResponse):
        return user
    return templates.TemplateResponse(request, "classmates.html", {"user": user})


@app.get("/notes", include_in_schema=False)
def notes_page(request: Request):
    """Render the private notes page."""
    user = require_page_user(request)
    if isinstance(user, RedirectResponse):
        return user
    return templates.TemplateResponse(request, "notes.html", {"user": user})


@app.get("/profile", include_in_schema=False)
def profile_page(request: Request):
    """Render the profile edit page."""
    user = require_page_user(request)
    if isinstance(user, RedirectResponse):
        return user
    return templates.TemplateResponse(request, "profile.html", {"user": user})


@app.get("/logout", include_in_schema=False)
def logout():
    """Clear the session cookie and redirect to login."""
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie(COOKIE_NAME)
    return response
