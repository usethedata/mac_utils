"""Unit tests for the mcp_upstream check.

The check runs `git` subprocesses; tests inject a fake runner that returns
canned (rc, stdout, stderr) tuples per command, so the parser, per-repo
classification, and rollup logic are exercised without touching real repos.
"""

from __future__ import annotations

import os
from pathlib import Path
from unittest import mock

import pytest

from system_status_check.checks import mcp_upstream


def _make_runner(responses: dict[tuple, tuple[int, str, str]]):
    """Build a runner that returns the response keyed by argv tuple.

    Keys are the trailing argv slice after the leading `git -C <path>` prefix
    so tests don't have to bake in absolute paths. Unknown argv → AssertionError
    with a useful message, so a failed test points at exactly which call was
    unexpected.
    """
    def runner(argv, timeout):
        # Strip the leading `git -C <path>` prefix.
        assert argv[:2] == ["git", "-C"], f"unexpected argv prefix: {argv!r}"
        key = tuple(argv[3:])
        if key not in responses:
            raise AssertionError(f"unexpected git call: {key!r}")
        return responses[key]
    return runner


@pytest.fixture
def repo_dir(tmp_path: Path) -> Path:
    """A real-on-disk directory that looks like a git repo to the path check."""
    (tmp_path / ".git").mkdir()
    return tmp_path


# ---------------------------------------------------------------------------
# _check_repo: per-repo logic
# ---------------------------------------------------------------------------

def test_check_repo_clean(repo_dir):
    runner = _make_runner({
        ("fetch", "origin", "--quiet"): (0, "", ""),
        ("symbolic-ref", "--short", "refs/remotes/origin/HEAD"): (0, "origin/main\n", ""),
        ("rev-list", "--count", "HEAD..origin/main"): (0, "0\n", ""),
    })
    result = mcp_upstream._check_repo(
        {"name": "demo", "path": str(repo_dir), "remote": "origin"},
        runner=runner,
    )
    assert result["status"] == "ok"
    assert result["pending_count"] == 0
    assert result["commits"] == []
    assert result["branch"] == "main"


def test_check_repo_pending_commits(repo_dir):
    log_out = (
        "abc1234 Bump dep X to 2.0\n"
        "def5678 Fix race in cache eviction\n"
        "9012345 docs: add example for auth flow\n"
    )
    runner = _make_runner({
        ("fetch", "origin", "--quiet"): (0, "", ""),
        ("symbolic-ref", "--short", "refs/remotes/origin/HEAD"): (0, "origin/main\n", ""),
        ("rev-list", "--count", "HEAD..origin/main"): (0, "3\n", ""),
        ("log", "--pretty=format:%h %s", "HEAD..origin/main"): (0, log_out, ""),
    })
    result = mcp_upstream._check_repo(
        {"name": "demo", "path": str(repo_dir), "remote": "origin"},
        runner=runner,
    )
    assert result["status"] == "updates_pending"
    assert result["pending_count"] == 3
    assert result["branch"] == "main"
    assert result["commits"] == [
        {"sha": "abc1234", "subject": "Bump dep X to 2.0"},
        {"sha": "def5678", "subject": "Fix race in cache eviction"},
        {"sha": "9012345", "subject": "docs: add example for auth flow"},
    ]


def test_check_repo_uses_configured_remote(repo_dir):
    """A fork compares against `upstream/main`, not `origin/main`."""
    runner = _make_runner({
        ("fetch", "upstream", "--quiet"): (0, "", ""),
        ("symbolic-ref", "--short", "refs/remotes/upstream/HEAD"): (0, "upstream/main\n", ""),
        ("rev-list", "--count", "HEAD..upstream/main"): (0, "0\n", ""),
    })
    result = mcp_upstream._check_repo(
        {"name": "fork", "path": str(repo_dir), "remote": "upstream"},
        runner=runner,
    )
    assert result["status"] == "ok"
    assert result["remote"] == "upstream"


def test_check_repo_fetch_failure_is_unreachable(repo_dir):
    runner = _make_runner({
        ("fetch", "origin", "--quiet"): (128, "", "fatal: unable to access ...: Could not resolve host: github.com\n"),
    })
    result = mcp_upstream._check_repo(
        {"name": "demo", "path": str(repo_dir), "remote": "origin"},
        runner=runner,
    )
    assert result["status"] == "unreachable"
    assert "Could not resolve host" in result["error"]


def test_check_repo_missing_default_branch_hints_at_set_head(repo_dir):
    runner = _make_runner({
        ("fetch", "origin", "--quiet"): (0, "", ""),
        ("symbolic-ref", "--short", "refs/remotes/origin/HEAD"): (
            128, "", "fatal: ref refs/remotes/origin/HEAD is not a symbolic ref\n",
        ),
    })
    result = mcp_upstream._check_repo(
        {"name": "demo", "path": str(repo_dir), "remote": "origin"},
        runner=runner,
    )
    assert result["status"] == "unreachable"
    assert "set-head" in result["error"]


def test_check_repo_missing_path():
    """Configured path that doesn't exist → unreachable, no crash, no fetch attempted."""
    def fail_runner(argv, timeout):
        raise AssertionError(f"runner should not be called when path is missing: {argv!r}")

    result = mcp_upstream._check_repo(
        {"name": "ghost", "path": "/nonexistent/path/to/repo", "remote": "origin"},
        runner=fail_runner,
    )
    assert result["status"] == "unreachable"
    assert "not a git repo" in result["error"]


def test_check_repo_no_path_configured():
    def fail_runner(argv, timeout):
        raise AssertionError("runner should not be called")

    result = mcp_upstream._check_repo(
        {"name": "broken", "remote": "origin"},
        runner=fail_runner,
    )
    assert result["status"] == "unreachable"
    assert "no path" in result["error"].lower()


# ---------------------------------------------------------------------------
# _rollup: check-level status from per-repo items
# ---------------------------------------------------------------------------

def test_rollup_all_clean():
    items = [
        {"name": "a", "status": "ok", "pending_count": 0},
        {"name": "b", "status": "ok", "pending_count": 0},
    ]
    status, counts = mcp_upstream._rollup(items)
    assert status == "ok"
    assert counts == {
        "repos_total": 2,
        "repos_with_updates": 0,
        "repos_unreachable": 0,
        "pending_remote": 0,
    }


def test_rollup_some_pending_no_unreachable():
    items = [
        {"name": "a", "status": "updates_pending", "pending_count": 3},
        {"name": "b", "status": "ok", "pending_count": 0},
    ]
    status, counts = mcp_upstream._rollup(items)
    assert status == "warn"
    assert counts["repos_with_updates"] == 1
    assert counts["pending_remote"] == 3


def test_rollup_unreachable_wins_over_pending():
    items = [
        {"name": "a", "status": "updates_pending", "pending_count": 5},
        {"name": "b", "status": "unreachable", "pending_count": 0},
    ]
    status, counts = mcp_upstream._rollup(items)
    assert status == "unreachable"
    assert counts["repos_unreachable"] == 1
    assert counts["repos_with_updates"] == 1
    # Pending counts are still surfaced even though the rollup is unreachable —
    # the daily brief can decide what to do with that.
    assert counts["pending_remote"] == 5


# ---------------------------------------------------------------------------
# run: end-to-end with injected runner
# ---------------------------------------------------------------------------

def test_run_no_repos_configured_is_an_error():
    result = mcp_upstream.run({}, {})
    assert result["status"] == "error"
    assert "no repos" in result["error"].lower()


def test_run_two_repos_one_pending_one_clean(repo_dir, tmp_path):
    other = tmp_path / "other"
    other.mkdir()
    (other / ".git").mkdir()

    log_out = "abc1234 Bump dep\ndef5678 Fix bug\n"

    def runner(argv, timeout):
        assert argv[:2] == ["git", "-C"]
        path = argv[2]
        rest = tuple(argv[3:])
        if path == str(repo_dir):
            return {
                ("fetch", "origin", "--quiet"): (0, "", ""),
                ("symbolic-ref", "--short", "refs/remotes/origin/HEAD"): (0, "origin/main\n", ""),
                ("rev-list", "--count", "HEAD..origin/main"): (0, "2\n", ""),
                ("log", "--pretty=format:%h %s", "HEAD..origin/main"): (0, log_out, ""),
            }[rest]
        if path == str(other):
            return {
                ("fetch", "upstream", "--quiet"): (0, "", ""),
                ("symbolic-ref", "--short", "refs/remotes/upstream/HEAD"): (0, "upstream/main\n", ""),
                ("rev-list", "--count", "HEAD..upstream/main"): (0, "0\n", ""),
            }[rest]
        raise AssertionError(f"unexpected path: {path}")

    host_cfg = {
        "mcp_upstream": {
            "repos": [
                {"name": "alpha", "path": str(repo_dir), "remote": "origin"},
                {"name": "beta",  "path": str(other),    "remote": "upstream"},
            ],
        },
    }
    # shutil.which("git") still needs to succeed for run() to proceed.
    with mock.patch.object(mcp_upstream.shutil, "which", return_value="/usr/bin/git"):
        result = mcp_upstream.run(host_cfg, {}, runner=runner)

    assert result["status"] == "warn"
    assert result["counts"]["repos_total"] == 2
    assert result["counts"]["repos_with_updates"] == 1
    assert result["counts"]["pending_remote"] == 2
    names = [i["name"] for i in result["items"]]
    assert names == ["alpha", "beta"]
    alpha = result["items"][0]
    assert alpha["status"] == "updates_pending"
    assert len(alpha["commits"]) == 2


def test_run_skips_when_git_missing():
    host_cfg = {
        "mcp_upstream": {"repos": [{"name": "x", "path": "/tmp", "remote": "origin"}]},
    }
    with mock.patch.object(mcp_upstream.shutil, "which", return_value=None):
        result = mcp_upstream.run(host_cfg, {})
    assert result["status"] == "error"
    assert "git" in result["error"].lower()
