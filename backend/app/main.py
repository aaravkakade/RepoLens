from dataclasses import dataclass
import os
import shutil
import subprocess
import tempfile
from urllib.parse import urlparse

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="RepoLens")

GITHUB_HOST = "github.com"
CLONE_TIMEOUT_SECONDS = 60


class ValidateRepoRequest(BaseModel):
    url: str


class ValidateRepoResponse(BaseModel):
    valid: bool
    owner: str | None = None
    repo: str | None = None
    canonical_url: str | None = None
    reason: str | None = None


class CloneRepoResponse(BaseModel):
    success: bool
    path: str | None = None
    file_count: int | None = None
    commit_sha: str | None = None
    owner: str | None = None
    repo: str | None = None
    canonical_url: str | None = None
    reason: str | None = None


@dataclass
class ParsedRepo:
    owner: str | None = None
    repo: str | None = None
    reason: str | None = None


@dataclass
class CloneResult:
    path: str | None = None
    file_count: int | None = None
    commit_sha: str | None = None
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


def count_files(directory: str) -> int:
    return sum(len(files) for _, _, files in os.walk(directory))


def clone_failure_reason(stderr: str) -> str:
    message = stderr.lower()
    if "not found" in message or "does not exist" in message:
        return "Repository not found or is private"
    if "could not read from remote repository" in message:
        return "Could not access repository"
    return "Failed to clone repository"


def clone_repo(canonical_url: str, owner: str, repo: str) -> CloneResult:
    dest = tempfile.mkdtemp(prefix=f"repolens-{owner}-{repo}-")
    try:
        result = subprocess.run(
            ["git", "clone", "--depth", "1", canonical_url, dest],
            capture_output=True,
            text=True,
            timeout=CLONE_TIMEOUT_SECONDS,
        )
        if result.returncode != 0:
            shutil.rmtree(dest, ignore_errors=True)
            return CloneResult(reason=clone_failure_reason(result.stderr))

        sha_result = subprocess.run(
            ["git", "-C", dest, "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        commit_sha = sha_result.stdout.strip() if sha_result.returncode == 0 else None

        return CloneResult(
            path=dest,
            file_count=count_files(dest),
            commit_sha=commit_sha,
        )
    except subprocess.TimeoutExpired:
        shutil.rmtree(dest, ignore_errors=True)
        return CloneResult(reason=f"Clone timed out after {CLONE_TIMEOUT_SECONDS} seconds")
    except OSError as exc:
        shutil.rmtree(dest, ignore_errors=True)
        return CloneResult(reason=f"Clone failed: {exc}")


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


@app.post("/repos/clone", response_model=CloneRepoResponse)
def clone_github_repo(request: ValidateRepoRequest) -> CloneRepoResponse:
    parsed = parse_github_url(request.url)
    if parsed.reason is not None:
        return CloneRepoResponse(success=False, reason=parsed.reason)

    canonical_url = f"https://github.com/{parsed.owner}/{parsed.repo}"
    result = clone_repo(canonical_url, parsed.owner, parsed.repo)
    if result.reason is not None:
        return CloneRepoResponse(
            success=False,
            owner=parsed.owner,
            repo=parsed.repo,
            canonical_url=canonical_url,
            reason=result.reason,
        )

    return CloneRepoResponse(
        success=True,
        path=result.path,
        file_count=result.file_count,
        commit_sha=result.commit_sha,
        owner=parsed.owner,
        repo=parsed.repo,
        canonical_url=canonical_url,
    )
