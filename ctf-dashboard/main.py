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


@app.get("/", include_in_schema=False)
def root(request: Request):
    return templates.TemplateResponse(request, "index.html")


@app.get(
    "/verify/a01/test-connection",
    tags=["Verification"],
    summary="Test target connectivity",
)
def test_connection():
    response = requests.get("http://broken-access-controls:5000/api/ping")
    return {
        "status_code": response.status_code,
        "target_response": response.json(),
    }
