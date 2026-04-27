# system-status-check

Nightly orchestrator that reports the update status of every computer it's configured for.
Descriptive only — does not apply any updates.

Runs on the orchestrator host as a systemd user timer (04:00 local). Emits a JSON report and a rendered Markdown report into the configured `report_dir` for the daily brief to consume.

Authoritative plan: `Progs/Ongoing/Maintenance/system-status-check-plan.md` (outside this public repo, because it names real hosts).

## Scope

- Per-host reachability
- chezmoi drift (local, source-repo, pending remote)
- Homebrew outdated (macOS)
- apt upgradable (Ubuntu)
- Synology DSM package + OS updates
- MCP upstream changes for locally hosted MCP clones

## Installation

```bash
./install.sh
```

Creates the venv at `${XDG_DATA_HOME:-$HOME/.local/share}/python/envs/system-status-check/`, installs dependencies, writes the launcher to `~/.local/bin/system-status-check`, and seeds `~/.config/system-status-check/hosts.yaml` from `hosts.yaml.example` if the real file does not exist yet.

See `Progs/CLAUDE.md` for the conventions this follows (script install locations, venv target pattern).

## Usage

```bash
system-status-check                 # full run, writes the canonical daily report
system-status-check --dry-run       # full run, writes to /tmp/ instead
system-status-check --host <alias>
system-status-check --check chezmoi
```
