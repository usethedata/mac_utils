BINDIR := $(HOME)/bin

.PHONY: all brew-nightly-update brew-monthly-inventory

all: brew-nightly-update brew-monthly-inventory

brew-nightly-update:
	install -m 0755 brew-nightly-update.sh $(BINDIR)/brew-nightly-update.sh

brew-monthly-inventory:
	install -m 0755 brew-monthly-inventory.sh $(BINDIR)/brew-monthly-inventory.sh
