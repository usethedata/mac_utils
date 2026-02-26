#!/usr/bin/env python3
# install-cron.py
# Reads cron.conf and installs any missing crontab entries.
# Copy cron.conf.example to cron.conf and edit before running.

import configparser
import os
import subprocess
import sys


def get_crontab():
    result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
    # Exit code 1 with "no crontab" message means empty — not an error
    if result.returncode != 0 and "no crontab for" not in result.stderr:
        print(f"Error reading crontab: {result.stderr}", file=sys.stderr)
        sys.exit(1)
    return result.stdout


def set_crontab(content):
    subprocess.run(["crontab", "-"], input=content, text=True, check=True)


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(here, "cron.conf")

    if not os.path.exists(config_path):
        print("cron.conf not found — copy cron.conf.example to cron.conf and edit it.")
        sys.exit(0)

    config = configparser.ConfigParser()
    config.read(config_path)

    bindir = os.path.expanduser("~/bin")
    crontab = get_crontab()
    new_entries = []

    for script, section in config.items():
        if script == "DEFAULT":
            continue
        schedule = section.get("schedule")
        if not schedule:
            print(f"Warning: no schedule for {script}, skipping.")
            continue
        command = os.path.join(bindir, script)
        entry = f"{schedule} {command}"
        if script in crontab:
            print(f"Already installed: {script}")
        else:
            new_entries.append(entry)
            print(f"Adding: {entry}")

    if new_entries:
        updated = crontab.rstrip("\n")
        if updated:
            updated += "\n"
        updated += "\n".join(new_entries) + "\n"
        set_crontab(updated)
        print(f"Crontab updated ({len(new_entries)} entr{'y' if len(new_entries) == 1 else 'ies'} added).")
    else:
        print("No changes needed.")


if __name__ == "__main__":
    main()
