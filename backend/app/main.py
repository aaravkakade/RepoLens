from fastapi import FastAPI

app = FastAPI(title="RepoLens")


@app.get("/")
def root():
    return {"message": "RepoLens API"}


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "RepoLens"}
