"""MCP upstream-update check.

For each configured MCP repository under ``Progs/ai/``, fetch the configured
remote and report unreviewed commits between local HEAD and the remote's
default branch. "Upstream" here is conceptual — it covers both the plain-clone
case (compare to ``origin``) and the divergent-fork case (compare to a
separately added ``upstream`` remote). The per-repo ``remote`` field selects
which.

Runs locally on the orchestrator host; no SSH involved. Each ``git fetch``
writes pack files into ``.git/objects/`` which Dropbox then syncs to the other
bears — that has been trouble-free for a decade per ``Progs/CLAUDE.md``, so no
guard is needed.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from typing import Callable


NAME = "mcp_upstream"


_FETCH_TIMEOUT = 30
_QUERY_TIMEOUT = 10
_LOG_TIMEOUT = 15
_MAX_ERR_CHARS = 500
_MAX_HINT_CHARS = 200


# Runner signature: (argv, timeout) -> (returncode, stdout, stderr).
RunnerFn = Callable[[list, int], "tuple[int, str, str]"]


def _default_runner(argv: list[str], timeout: int) -> tuple[int, str, str]:
    try:
        proc = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        return (124, exc.stdout or "", (exc.stderr or "") + f"\ntimed out after {timeout}s")
    except FileNotFoundError as exc:
        return (127, "", str(exc))
    return (proc.returncode, proc.stdout or "", proc.stderr or "")


def _unreachable(name: str, remote: str, reason: str, branch: str | None = None) -> dict:
    return {
        "name": name,
        "remote": remote,
        "branch": branch,
        "status": "unreachable",
        "pending_count": 0,
        "commits": [],
        "error": reason[:_MAX_ERR_CHARS],
    }


def _check_repo(repo_cfg: dict, runner: RunnerFn = _default_runner) -> dict:
    name = repo_cfg.get("name") or "(unnamed)"
    raw_path = repo_cfg.get("path") or ""
    path = os.path.expanduser(os.path.expandvars(raw_path))
    remote = repo_cfg.get("remote") or "origin"

    if not raw_path:
        return _unreachable(name, remote, "no path configured")

    if not os.path.isdir(os.path.join(path, ".git")):
        return _unreachable(name, remote, f"not a git repo: {path}")

    # Fetch.
    rc, _out, err = runner(
        ["git", "-C", path, "fetch", remote, "--quiet"],
        _FETCH_TIMEOUT,
    )
    if rc != 0:
        return _unreachable(
            name, remote,
            f"git fetch {remote} rc={rc}: {err.strip() or '(no stderr)'}",
        )

    # Resolve the remote's default branch (set by `git remote set-head <r> --auto`).
    rc, out, err = runner(
        ["git", "-C", path, "symbolic-ref", "--short",
         f"refs/remotes/{remote}/HEAD"],
        _QUERY_TIMEOUT,
    )
    if rc != 0:
        hint = err.strip()[:_MAX_HINT_CHARS] or "(no stderr)"
        return _unreachable(
            name, remote,
            f"could not resolve {remote}/HEAD: {hint}; "
            f"try `git -C {path} remote set-head {remote} --auto`",
        )
    full_ref = out.strip()
    branch = full_ref.split("/", 1)[1] if "/" in full_ref else full_ref

    # Count unreviewed commits.
    rc, out, err = runner(
        ["git", "-C", path, "rev-list", "--count", f"HEAD..{full_ref}"],
        _QUERY_TIMEOUT,
    )
    if rc != 0:
        return _unreachable(
            name, remote,
            f"git rev-list rc={rc}: {err.strip() or '(no stderr)'}",
            branch=branch,
        )
    try:
        count = int(out.strip())
    except ValueError:
        return _unreachable(
            name, remote,
            f"git rev-list returned non-integer: {out.strip()!r}",
            branch=branch,
        )

    if count == 0:
        return {
            "name": name,
            "remote": remote,
            "branch": branch,
            "status": "ok",
            "pending_count": 0,
            "commits": [],
        }

    # Pull commit subjects for the detail section. No --no-merges: that would
    # produce a list shorter than `pending_count` (which uses rev-list --count
    # over the same range), and the count/list mismatch would be confusing.
    commits: list[dict] = []
    rc, out, _err = runner(
        ["git", "-C", path, "log", "--pretty=format:%h %s",
         f"HEAD..{full_ref}"],
        _LOG_TIMEOUT,
    )
    if rc == 0:
        for line in out.splitlines():
            line = line.rstrip()
            if not line:
                continue
            sha, sep, subject = line.partition(" ")
            commits.append({
                "sha": sha,
                "subject": subject if sep else "",
            })

    return {
        "name": name,
        "remote": remote,
        "branch": branch,
        "status": "updates_pending",
        "pending_count": count,
        "commits": commits,
    }


def _rollup(items: list[dict]) -> tuple[str, dict]:
    repos_unreachable = sum(1 for i in items if i["status"] == "unreachable")
    repos_with_updates = sum(1 for i in items if i["status"] == "updates_pending")
    pending_remote = sum(int(i.get("pending_count") or 0) for i in items)

    if repos_unreachable:
        status = "unreachable"
    elif repos_with_updates:
        status = "warn"
    else:
        status = "ok"

    counts = {
        "repos_total": len(items),
        "repos_with_updates": repos_with_updates,
        "repos_unreachable": repos_unreachable,
        # `pending_remote` participates in the dispatcher's
        # updates_pending_total rollup (see dispatch._summarize).
        "pending_remote": pending_remote,
    }
    return status, counts


def run(host_cfg: dict, settings: dict, runner: RunnerFn | None = None) -> dict:
    cfg = host_cfg.get("mcp_upstream") or {}
    repos = cfg.get("repos") or []

    if not repos:
        return {
            "status": "error",
            "items": [],
            "counts": {},
            "error": "mcp_upstream check enabled but no repos configured",
        }

    if shutil.which("git") is None:
        return {
            "status": "error",
            "items": [],
            "counts": {},
            "error": "git not found on PATH",
        }

    use_runner = runner or _default_runner
    items = [_check_repo(r, runner=use_runner) for r in repos]
    status, counts = _rollup(items)
    return {
        "status": status,
        "counts": counts,
        "items": items,
    }
