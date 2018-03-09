PACKAGE := nat_conntracker
EXEC_PREFIX ?= /usr/local
CONFIG_PREFIX ?= /etc

PIP ?= pip3
PYTHON ?= python3

TESTDATA := tests/data/conntrack-events-sample.xml

.PHONY: all
all: deps lint test

.PHONY: clean
clean:
	rm -f $(TESTDATA)

.PHONY: deps
deps: $(TESTDATA)
	$(PIP) install -r requirements.txt

.PHONY: lint
lint:
	$(PYTHON) setup.py flake8

.PHONY: install
install:
	$(PIP3) install --upgrade --ignore-installed $(PWD)

.PHONY: test
test:
	$(PYTHON) setup.py pytest --addopts="--cov=$(PACKAGE)"

# The sysinstall target is expected to be run by a user with write access to the
# CONFIG_PREFIX and EXEC_PREFIX sub-directories used below, as well as the
# ability to run systemctl commands, such as root. :scream_cat:
.PHONY: sysinstall
sysinstall: install
	touch $(CONFIG_PREFIX)/default/nat-conntracker
	cp -v ./misc/nat-conntracker.service $(CONFIG_PREFIX)/systemd/system/nat-conntracker.service
	cp -v ./misc/nat-conntracker-wrapper $(EXEC_PREFIX)/bin/nat-conntracker-wrapper
	systemctl enable nat-conntracker

tests/data/conntrack-events-sample.xml: tests/data/conntrack-events-sample.xml.bz2
	bzcat $^ >$@
