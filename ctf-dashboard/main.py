import importlib.util
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import requests

VERIFY_DIR = Path(__file__).parent / "verify-patch-apis"


def _load_verify_module(module_name: str, filename: str):
    path = VERIFY_DIR / filename
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


bac_verify = _load_verify_module(
    "broken_access_control_api",
    "broken-access-control-api.py",
)
mec_verify = _load_verify_module(
    "mishandling_exceptional_conditions_api",
    "mishandling-exceptional-conditions-api.py",
)

BAC_CHALLENGE_TESTS = {
    1: bac_verify.test_challenge_1,
    2: bac_verify.test_challenge_2,
    3: bac_verify.test_challenge_3,
    4: bac_verify.test_challenge_4,
}

MEC_CHALLENGE_TESTS = {
    1: mec_verify.test_challenge_1,
    2: mec_verify.test_challenge_2,
    3: mec_verify.test_challenge_3,
}

app = FastAPI(
    title="CTF Dashboard & Scoring Engine",
    description="Dashboard for verifying and scoring CTF challenge patches.",
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

Path("static").mkdir(exist_ok=True)
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
    """Ping the broken-access-controls target over Docker networking."""
    response = requests.get("http://broken-access-controls:5000/api/ping")
    return {
        "status_code": response.status_code,
        "target_response": response.json(),
    }


@app.post(
    "/verify/a01/challenge/{challenge_num}",
    tags=["Verification"],
    summary="Verify a Broken Access Control patch",
)
def verify_bac_challenge(challenge_num: int):
    """Run automated patch checks for BAC challenge 1–4."""
    test_fn = BAC_CHALLENGE_TESTS.get(challenge_num)
    if test_fn is None:
        raise HTTPException(status_code=404, detail="Unknown challenge number")
    return test_fn()


@app.post(
    "/verify/a10/challenge/{challenge_num}",
    tags=["Verification"],
    summary="Verify a Mishandling of Exceptional Conditions patch",
)
def verify_mec_challenge(challenge_num: int):
    """Run automated patch checks for MEC challenge 1–3."""
    test_fn = MEC_CHALLENGE_TESTS.get(challenge_num)
    if test_fn is None:
        raise HTTPException(status_code=404, detail="Unknown challenge number")
    return test_fn()
