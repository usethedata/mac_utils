# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

A collection of utility scripts for macOS automation and various personal tasks. Scripts are primarily shell scripts, with some Python. This is the canonical source; scripts are installed to `~/bin` for use.

**GitHub**: https://github.com/usethedata/mac_utils (public repo — never commit secrets, credentials, API keys, tokens, or any personally identifying information.)

## Conventions

- Shell scripts: use `#!/usr/bin/env bash` shebang, target macOS/zsh environment
- Python scripts: use `#!/usr/bin/env python3`
- Installed scripts go in `~/bin` (ensure it is on `$PATH`)

Update this file as the repository grows to document any shared utilities, installation steps, or conventions that emerge.
