PACKAGE := nat_conntracker
EXEC_PREFIX ?= /usr/local
CONFIG_PREFIX ?= /etc

.PHONY: all
all: deps lint test

.PHONY: deps
deps:
	pip install -r requirements.txt

.PHONY: lint
lint:
	git ls-files '*.py' | xargs flake8

.PHONY: install
install:
	python setup.py install

.PHONY: test
test:
	pytest --cov=$(PACKAGE) tests/

# The sysinstall target is expected to be run by a user with write access to the
# CONFIG_PREFIX and EXEC_PREFIX sub-directories used below, as well as the
# ability to run systemctl commands, such as root. :scream_cat:
.PHONY: sysinstall
sysinstall: install
	touch $(CONFIG_PREFIX)/default/nat-conntracker
	cp -v ./misc/nat-conntracker.service $(CONFIG_PREFIX)/systemd/system/nat-conntracker.service
	cp -v ./misc/nat-conntracker-wrapper $(EXEC_PREFIX)/bin/nat-conntracker-wrapper
	systemctl enable nat-conntracker
