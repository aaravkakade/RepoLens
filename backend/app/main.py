from fastapi import FastAPI

app = FastAPI(title="RepoLens")


@app.get("/")
def root():
    return {"message": "RepoLens API"}
