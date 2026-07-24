from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import requests

app = FastAPI(title="CTF Dashboard & Scoring Engine")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/")
def root(request: Request):
    return templates.TemplateResponse(request, "index.html")


@app.get("/verify/a01/test-connection")
def test_connection():
    response = requests.get("http://broken-access-controls:5000/api/ping")
    return {
        "status_code": response.status_code,
        "target_response": response.json(),
    }
