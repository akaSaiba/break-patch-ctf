from fastapi import FastAPI
import requests

app = FastAPI(title="CTF Dashboard & Scoring Engine")


@app.get("/")
def root():
    return {
        "message": "Welcome to CTF Dashboard & Scoring Engine. Check /docs for the API documentation."
    }


@app.get("/verify/a01/test-connection")
def test_connection():
    response = requests.get("http://broken-access-controls:5000/")
    return {
        "status_code": response.status_code,
        "target_response": response.json(),
    }
