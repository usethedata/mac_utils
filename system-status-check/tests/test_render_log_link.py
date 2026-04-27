"""Tests for the Mac-side path translation in _log_link."""

from __future__ import annotations

from pathlib import Path
from unittest import mock

from system_status_check import render


def test_log_link_translates_dropbox_path_to_mac_side():
    with mock.patch.object(render.Path, "home", return_value=Path("/home/alice")):
        link = render._log_link("/home/alice/Dropbox/BEWMain/Data/logs/run.log")
    assert link == (
        "[run.log](vscode://file/Users/alice/Library/"
        "CloudStorage/Dropbox/BEWMain/Data/logs/run.log)"
    )


def test_log_link_leaves_non_dropbox_paths_alone():
    with mock.patch.object(render.Path, "home", return_value=Path("/home/alice")):
        link = render._log_link("/var/log/syslog")
    assert link == "[syslog](vscode://file/var/log/syslog)"
