.PHONY: help install install-dev install-hooks format lint security check create-bucket list upload download presign

help:
	@echo "Usage: make <target> [ARGS='...']"
	@echo ""
	@echo "Targets:"
	@echo "  install                      Install Python dependencies"
	@echo "  install-dev                  Install dev dependencies (ruff, bandit)"
	@echo "  install-hooks                Install git pre-push hook"
	@echo "  format                       Auto-format code with ruff"
	@echo "  lint                         Lint code with ruff"
	@echo "  security                     Run security checks with bandit"
	@echo "  check                        Run lint + security together"
	@echo "  create-bucket ARGS='<name>'  Create a new bucket"
	@echo "  list          [ARGS='<pfx>'] List objects (optional prefix filter)"
	@echo "  upload        ARGS='<file> [key]'  Upload a file"
	@echo "  download      ARGS='<key> [dest]'  Download an object"
	@echo "  presign       ARGS='<key> [secs]'  Generate a pre-signed URL"

install:
	python3 -m pip install -r requirements.txt

install-dev:
	python3 -m pip install -r requirements-dev.txt

install-hooks:
	cp hooks/pre-push .git/hooks/pre-push
	chmod +x .git/hooks/pre-push
	@echo "pre-push hook installed."

format:
	python3 -m ruff format .

lint:
	python3 -m ruff check .

security:
	python3 -m bandit -r . -c pyproject.toml

check: lint security

create-bucket:
	python3 create_bucket.py $(ARGS)

list:
	python3 list_objects.py $(ARGS)

upload:
	python3 upload.py $(ARGS)

download:
	python3 download.py $(ARGS)

presign:
	python3 presign.py $(ARGS)
