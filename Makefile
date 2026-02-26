BINDIR := $(HOME)/bin

.PHONY: all cron

all: $(BINDIR)/brew-nightly-update.sh $(BINDIR)/brew-monthly-inventory.sh cron

$(BINDIR)/brew-nightly-update.sh: brew-nightly-update.sh
	install -m 0755 brew-nightly-update.sh $(BINDIR)/brew-nightly-update.sh

$(BINDIR)/brew-monthly-inventory.sh: brew-monthly-inventory.sh
	install -m 0755 brew-monthly-inventory.sh $(BINDIR)/brew-monthly-inventory.sh

cron: cron.conf
	python3 install-cron.py
