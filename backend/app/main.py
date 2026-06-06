from dataclasses import dataclass
from urllib.parse import urlparse

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="RepoLens")

GITHUB_HOST = "github.com"


class ValidateRepoRequest(BaseModel):
    url: str


class ValidateRepoResponse(BaseModel):
    valid: bool
    owner: str | None = None
    repo: str | None = None
    canonical_url: str | None = None
    reason: str | None = None


@dataclass
class ParsedRepo:
    owner: str | None = None
    repo: str | None = None
    reason: str | None = None


def parse_github_url(url: str) -> ParsedRepo:
    stripped = url.strip()
    if not stripped:
        return ParsedRepo(reason="URL is empty")
    if stripped.startswith("git@"):
        return ParsedRepo(reason="SSH URLs are not supported; use an HTTPS GitHub URL")

    parsed = urlparse(stripped)
    if parsed.scheme != "https":
        return ParsedRepo(reason="URL must use https://github.com/owner/repo")
    if parsed.netloc.lower() != GITHUB_HOST:
        return ParsedRepo(reason="URL must be a github.com repository link")

    path = parsed.path.strip("/")
    if not path:
        return ParsedRepo(reason="URL must include both an owner and a repository name")

    segments = path.split("/")
    if len(segments) > 2:
        return ParsedRepo(reason="URL must point to a repository root, not a sub-path")
    if len(segments) < 2:
        return ParsedRepo(reason="URL must include both an owner and a repository name")

    owner, repo_name = segments
    if repo_name.endswith(".git"):
        repo_name = repo_name[:-4]

    if not owner or not repo_name:
        return ParsedRepo(reason="URL must include both an owner and a repository name")

    return ParsedRepo(owner=owner, repo=repo_name)


@app.get("/")
def root():
    return {"message": "RepoLens API"}


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "RepoLens"}


@app.post("/repos/validate", response_model=ValidateRepoResponse)
def validate_repo(request: ValidateRepoRequest) -> ValidateRepoResponse:
    parsed = parse_github_url(request.url)
    if parsed.reason is not None:
        return ValidateRepoResponse(valid=False, reason=parsed.reason)

    return ValidateRepoResponse(
        valid=True,
        owner=parsed.owner,
        repo=parsed.repo,
        canonical_url=f"https://github.com/{parsed.owner}/{parsed.repo}",
    )
