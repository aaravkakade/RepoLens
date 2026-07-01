from app.main import parse_github_url


def test_valid_plain_https_url():
    result = parse_github_url("https://github.com/pallets/click")

    assert result.reason is None
    assert result.owner == "pallets"
    assert result.repo == "click"
    assert result.canonical_url == "https://github.com/pallets/click"


def test_valid_url_with_git_suffix():
    result = parse_github_url("https://github.com/pallets/click.git")

    assert result.reason is None
    assert result.owner == "pallets"
    assert result.repo == "click"
    assert result.canonical_url == "https://github.com/pallets/click"


def test_valid_url_with_trailing_slash():
    result = parse_github_url("https://github.com/pallets/click/")

    assert result.reason is None
    assert result.owner == "pallets"
    assert result.repo == "click"
    assert result.canonical_url == "https://github.com/pallets/click"


def test_invalid_empty_string():
    result = parse_github_url("")

    assert result.reason == "URL is empty"
    assert result.owner is None
    assert result.repo is None
    assert result.canonical_url is None


def test_invalid_ssh_url():
    result = parse_github_url("git@github.com:pallets/click.git")

    assert result.reason == "SSH URLs are not supported; use an HTTPS GitHub URL"
    assert result.owner is None
    assert result.repo is None


def test_invalid_non_https_scheme():
    result = parse_github_url("http://github.com/pallets/click")

    assert result.reason == "URL must use https://github.com/owner/repo"
    assert result.owner is None
    assert result.repo is None


def test_invalid_non_github_host():
    result = parse_github_url("https://gitlab.com/pallets/click")

    assert result.reason == "URL must be a github.com repository link"
    assert result.owner is None
    assert result.repo is None


def test_invalid_subpath_url():
    result = parse_github_url("https://github.com/pallets/click/tree/main/src")

    assert result.reason == "URL must point to a repository root, not a sub-path"
    assert result.owner is None
    assert result.repo is None


def test_invalid_owner_only():
    result = parse_github_url("https://github.com/pallets")

    assert result.reason == "URL must include both an owner and a repository name"
    assert result.owner is None
    assert result.repo is None
