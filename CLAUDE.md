# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

A collection of utility scripts for cross-platform *nix automation and various personal tasks. Scripts are primarily shell scripts, with some Python. This is the canonical source; cross-bear scripts install to `~/bin`, while scripts that are machine-local by design (e.g., the grizzledbear-only `system-status-check/`) install to `~/.local/bin`.

Content in this repo should work across all *nix systems Bruce runs (macOS, Ubuntu, Synology DSM). macOS-specific scripts belong in `Progs/Ongoing/Maintenance/mac-scripting/`, not here. A broader reorganization along that boundary is tracked in `Progs/TODO.md`.

**GitHub**: https://github.com/usethedata/mac_utils (public repo — never commit secrets, credentials, API keys, tokens, or any personally identifying information, including hostnames or IP addresses of Bruce's systems.)

## Conventions

- Shell scripts: `#!/usr/bin/env bash` shebang.
  - `zsh` is Bruce's interactive shell and he installs it on every bear (macOS default; installed on Ubuntu and Synology DSM), but it is **not** guaranteed to exist on a freshly provisioned *nix system. Scripts here must be bash-portable and must not rely on zsh being present.
- Python scripts: `#!/usr/bin/env python3`.
- Script install locations follow the convention in `Progs/CLAUDE.md`:
  - `~/bin/` for cross-bear scripts (target state: distributed via chezmoi)
  - `~/.local/bin/` for machine-local scripts
- Python virtual environments follow the target pattern in `Progs/CLAUDE.md`: `${XDG_DATA_HOME:-$HOME/.local/share}/python/envs/<project>/`.

Update this file as the repository grows to document any shared utilities, installation steps, or conventions that emerge.
