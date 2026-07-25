from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import requests

app = FastAPI(
    title="CTF Dashboard & Scoring Engine",
    description="Dashboard for verifying and scoring Broken Access Control challenges.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {
            "name": "Verification",
            "description": "Connectivity and challenge verification endpoints.",
        },
    ],
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

PAGE_BY_PATH = {
    "/": "introduction",
    "/broken-access-control": "broken-access-control",
    "/mishandling-exceptional-conditions": "mishandling-exceptional-conditions",
}


def render_dashboard(request: Request, page: str):
    """Render the SPA shell with the given initial sidebar page."""
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {"initial_page": page},
    )


@app.get("/", include_in_schema=False)
def introduction(request: Request):
    """Serve the dashboard on the Introduction tab."""
    return render_dashboard(request, "introduction")


@app.get("/broken-access-control", include_in_schema=False)
def broken_access_control(request: Request):
    """Serve the dashboard on the Broken Access Control tab."""
    return render_dashboard(request, "broken-access-control")


@app.get("/mishandling-exceptional-conditions", include_in_schema=False)
def mishandling_exceptional_conditions(request: Request):
    """Serve the dashboard on the Mishandling tab."""
    return render_dashboard(request, "mishandling-exceptional-conditions")


@app.get(
    "/verify/a01/test-connection",
    tags=["Verification"],
    summary="Test target connectivity",
)
def test_connection():
    """Ping the challenge-app target over Docker networking."""
    response = requests.get("http://challenge-app:5000/api/ping")
    return {
        "status_code": response.status_code,
        "target_response": response.json(),
    }
