#!/usr/bin/env bash
# brew-nightly-update.sh
# Nightly cron job: update and upgrade all Homebrew packages.
# Suggested crontab entry:
#   0 3 * * * $HOME/bin/brew-nightly-update.sh

set -euo pipefail

PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"
export PATH

echo "=== Homebrew nightly update: $(date) ==="
echo

echo "--- brew update ---"
brew update

echo
echo "--- brew upgrade ---"
brew upgrade

echo
echo "--- brew cleanup ---"
brew cleanup

echo
echo "=== Done: $(date) ==="
