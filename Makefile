BINDIR := $(HOME)/bin
CONFDIR := $(HOME)/.config/chezmoi-all
INFRA_DIR := $(BEWMAIN)/MainVault/Reference/Cyberinfrastructure

.PHONY: all install-scripts chezmoi-cache install-config

all: install-scripts chezmoi-cache install-config

install-scripts: $(BINDIR)/chezmoi-all \
                 $(BINDIR)/rebuild-chezmoi-cache

$(BINDIR)/chezmoi-all: chezmoi-all
	install -m 0755 chezmoi-all $(BINDIR)/chezmoi-all

$(BINDIR)/rebuild-chezmoi-cache: rebuild-chezmoi-cache
	install -m 0755 rebuild-chezmoi-cache $(BINDIR)/rebuild-chezmoi-cache

chezmoi-cache: config/chezmoi-hosts.json

config/chezmoi-hosts.json: $(INFRA_DIR)/README.md
	rebuild-chezmoi-cache

# Install a local copy of the host cache. Originally added so launchd-
# triggered runs of chezmoi-all-dryrun didn't need Full Disk Access on the
# CloudStorage/Dropbox path; that launchd job has been retired (replaced by
# system-status-check on grizzledbear). Local cache stays useful for
# interactive chezmoi-all runs that happen before Dropbox finishes syncing.
install-config: $(CONFDIR)/chezmoi-hosts.json

$(CONFDIR)/chezmoi-hosts.json: config/chezmoi-hosts.json
	mkdir -p $(CONFDIR)
	install -m 0644 config/chezmoi-hosts.json $(CONFDIR)/chezmoi-hosts.json
