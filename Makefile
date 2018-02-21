PACKAGE := nat_conntracker

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
