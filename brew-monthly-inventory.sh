#!/usr/bin/env bash
# brew-monthly-inventory.sh
# Monthly cron job: report all installed Homebrew formulae and casks with versions.
# Suggested crontab entry:
#   0 8 1 * * $HOME/bin/brew-monthly-inventory.sh

PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"
export PATH

echo "=== Homebrew inventory: $(date) ==="
echo

echo "--- Formulae ---"
brew list --formula --versions | sort

echo
echo "--- Casks ---"
brew list --cask --versions | sort

echo
echo "=== End of inventory ==="
