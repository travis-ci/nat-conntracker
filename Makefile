PACKAGE := nat_conntracker
EXEC_PREFIX ?= /usr/local
CONFIG_PREFIX ?= /etc

GIT_DESCRIBE ?= $(shell git describe --always --dirty --tags)
DOCKER_TAG ?= travisci/nat-conntracker:$(GIT_DESCRIBE)

DOCKER ?= docker
PIP ?= pip3
PYTHON ?= python3

TESTDATA := tests/data/conntrack-events-sample.xml

.PHONY: all
all: clean deps fmt coverage

.PHONY: clean
clean:
	$(RM) -r $(TESTDATA) htmlcov .coverage

.PHONY: deps
deps: $(TESTDATA)
	$(PIP) install -r requirements.txt

.PHONY: fmt
fmt:
	yapf -i -vv $(shell git ls-files '*.py') bin/nat-conntracker

.PHONY: install
install:
	$(PIP) install --upgrade --ignore-installed $(PWD)

.PHONY: coverage
coverage: htmlcov/index.html

.PHONY: test
test:
	$(PYTHON) setup.py pytest --addopts="--cov=$(PACKAGE)"


htmlcov/index.html: .coverage
	coverage html

.coverage: test

# The sysinstall target is expected to be run by a user with write access to the
# CONFIG_PREFIX and EXEC_PREFIX sub-directories used below, as well as the
# ability to run systemctl commands, such as root. :scream_cat:
.PHONY: sysinstall
sysinstall: install
	touch $(CONFIG_PREFIX)/default/nat-conntracker
	cp -v ./misc/nat-conntracker.service $(CONFIG_PREFIX)/systemd/system/nat-conntracker.service
	cp -v ./misc/nat-conntracker-wrapper $(EXEC_PREFIX)/bin/nat-conntracker-wrapper
	systemctl enable nat-conntracker

.PHONY: docker-build
docker-build:
	$(DOCKER) build -t="$(DOCKER_TAG)" .

.PHONY: docker-login
docker-login:
	@echo "$(DOCKER_LOGIN_PASSWORD)" | \
		$(DOCKER) login --username "$(DOCKER_LOGIN_USERNAME)" --password-stdin

.PHONY: docker-push
docker-push:
	$(DOCKER) push "$(DOCKER_TAG)"

tests/data/conntrack-events-sample.xml: tests/data/conntrack-events-sample.xml.bz2
	bzcat $^ >$@
