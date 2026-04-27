"""Renderer tests for the mcp_upstream check.

Covers the summary-line state and the detail-section nested-bullet shape.
"""

from __future__ import annotations

from system_status_check import render


def _host_with_mcp(check_dict: dict) -> dict:
    return {
        "alias": "orchestrator",
        "os": "ubuntu",
        "overall_status": check_dict.get("status", "ok"),
        "checks": {
            "reachability": {"status": "ok", "items": [], "counts": {}},
            "mcp_upstream": check_dict,
        },
    }


# ---------------------------------------------------------------------------
# Summary line
# ---------------------------------------------------------------------------

def test_summary_clean():
    host = _host_with_mcp({
        "status": "ok",
        "counts": {"repos_total": 2, "repos_with_updates": 0, "repos_unreachable": 0, "pending_remote": 0},
        "items": [],
    })
    line = render._summary_line(host)
    assert "MCP Upstream: no updates pending" in line


def test_summary_pending():
    host = _host_with_mcp({
        "status": "warn",
        "counts": {"repos_total": 2, "repos_with_updates": 1, "repos_unreachable": 0, "pending_remote": 3},
        "items": [],
    })
    line = render._summary_line(host)
    assert "MCP Upstream: *updates pending*" in line


def test_summary_unreachable_wins():
    host = _host_with_mcp({
        "status": "unreachable",
        "counts": {"repos_total": 2, "repos_with_updates": 1, "repos_unreachable": 1, "pending_remote": 3},
        "items": [],
    })
    line = render._summary_line(host)
    assert "MCP Upstream: ***unreachable***" in line


# ---------------------------------------------------------------------------
# Detail section
# ---------------------------------------------------------------------------

def test_detail_clean():
    lines = render._detail_mcp_upstream(
        "**MCP Upstream**",
        {
            "status": "ok",
            "counts": {"repos_total": 2, "repos_with_updates": 0, "repos_unreachable": 0, "pending_remote": 0},
            "items": [
                {"name": "a", "remote": "origin",   "branch": "main", "status": "ok", "pending_count": 0, "commits": []},
                {"name": "b", "remote": "upstream", "branch": "main", "status": "ok", "pending_count": 0, "commits": []},
            ],
        },
    )
    assert lines == ["- **MCP Upstream**: no updates pending"]


def test_detail_one_repo_with_updates():
    lines = render._detail_mcp_upstream(
        "**MCP Upstream**",
        {
            "status": "warn",
            "counts": {"repos_total": 2, "repos_with_updates": 1, "repos_unreachable": 0, "pending_remote": 2},
            "items": [
                {
                    "name": "fastmail-mcp", "remote": "origin", "branch": "main",
                    "status": "updates_pending", "pending_count": 2,
                    "commits": [
                        {"sha": "abc1234", "subject": "Bump dep"},
                        {"sha": "def5678", "subject": "Fix bug"},
                    ],
                },
                {"name": "other", "remote": "upstream", "branch": "main", "status": "ok", "pending_count": 0, "commits": []},
            ],
        },
    )
    assert lines[0] == "- **MCP Upstream**: 1 upstream with updates"
    assert lines[1] == "  - fastmail-mcp (origin/main): 2 commits pending"
    assert lines[2] == "    - `abc1234` Bump dep"
    assert lines[3] == "    - `def5678` Fix bug"
    assert len(lines) == 4  # clean repo not listed


def test_detail_two_repos_with_updates():
    lines = render._detail_mcp_upstream(
        "**MCP Upstream**",
        {
            "status": "warn",
            "counts": {"repos_total": 2, "repos_with_updates": 2, "repos_unreachable": 0, "pending_remote": 3},
            "items": [
                {
                    "name": "alpha", "remote": "origin", "branch": "main",
                    "status": "updates_pending", "pending_count": 1,
                    "commits": [{"sha": "111", "subject": "A1"}],
                },
                {
                    "name": "beta", "remote": "upstream", "branch": "main",
                    "status": "updates_pending", "pending_count": 2,
                    "commits": [
                        {"sha": "222", "subject": "B1"},
                        {"sha": "333", "subject": "B2"},
                    ],
                },
            ],
        },
    )
    assert lines[0] == "- **MCP Upstream**: 2 upstreams with updates"
    assert "  - alpha (origin/main): 1 commit pending" in lines
    assert "  - beta (upstream/main): 2 commits pending" in lines
    assert "    - `111` A1" in lines
    assert "    - `222` B1" in lines
    assert "    - `333` B2" in lines


def test_detail_one_unreachable_one_ok():
    lines = render._detail_mcp_upstream(
        "**MCP Upstream**",
        {
            "status": "unreachable",
            "counts": {"repos_total": 2, "repos_with_updates": 0, "repos_unreachable": 1, "pending_remote": 0},
            "items": [
                {
                    "name": "broken", "remote": "origin", "branch": None,
                    "status": "unreachable", "pending_count": 0, "commits": [],
                    "error": "git fetch origin rc=128: Could not resolve host",
                },
                {"name": "fine", "remote": "upstream", "branch": "main", "status": "ok", "pending_count": 0, "commits": []},
            ],
        },
    )
    assert lines[0] == "- **MCP Upstream**: ***1 unreachable***"
    assert lines[1].startswith("  - broken (origin): ***unreachable***")
    assert "Could not resolve host" in lines[1]
    assert len(lines) == 2  # clean repo not listed
