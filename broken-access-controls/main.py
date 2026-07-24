from fastapi import FastAPI

app = FastAPI(title="CorpNet University Portal - Target App")


@app.get("/")
def root():
    return {
        "message": "Welcome to CorpNet University Portal - Target App. Check /docs for the API documentation."
    }
