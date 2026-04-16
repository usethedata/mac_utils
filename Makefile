BINDIR := $(HOME)/bin
INFRA_DIR := $(BEWMAIN)/MainVault/Reference/Cyberinfrastructure

.PHONY: all install-scripts chezmoi-cache
# .PHONY: cron

all: install-scripts chezmoi-cache

install-scripts: $(BINDIR)/brew-nightly-update.sh $(BINDIR)/brew-monthly-inventory.sh \
                 $(BINDIR)/chezmoi-all $(BINDIR)/chezmoi-all-dryrun \
                 $(BINDIR)/rebuild-chezmoi-cache

$(BINDIR)/brew-nightly-update.sh: brew-nightly-update.sh
	install -m 0755 brew-nightly-update.sh $(BINDIR)/brew-nightly-update.sh

$(BINDIR)/brew-monthly-inventory.sh: brew-monthly-inventory.sh
	install -m 0755 brew-monthly-inventory.sh $(BINDIR)/brew-monthly-inventory.sh

$(BINDIR)/chezmoi-all: chezmoi-all
	install -m 0755 chezmoi-all $(BINDIR)/chezmoi-all

$(BINDIR)/chezmoi-all-dryrun: chezmoi-all-dryrun
	install -m 0755 chezmoi-all-dryrun $(BINDIR)/chezmoi-all-dryrun

$(BINDIR)/rebuild-chezmoi-cache: rebuild-chezmoi-cache
	install -m 0755 rebuild-chezmoi-cache $(BINDIR)/rebuild-chezmoi-cache

chezmoi-cache: config/chezmoi-hosts.json

config/chezmoi-hosts.json: $(INFRA_DIR)/README.md
	rebuild-chezmoi-cache

# cron: cron.conf
# 	python3 install-cron.py
