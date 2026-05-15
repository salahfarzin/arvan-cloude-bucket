.PHONY: help install create-bucket list upload download presign

help:
	@echo "Usage: make <target> [ARGS='...']"
	@echo ""
	@echo "Targets:"
	@echo "  install                      Install Python dependencies"
	@echo "  create-bucket ARGS='<name>'  Create a new bucket"
	@echo "  list          [ARGS='<pfx>'] List objects (optional prefix filter)"
	@echo "  upload        ARGS='<file> [key]'  Upload a file"
	@echo "  download      ARGS='<key> [dest]'  Download an object"
	@echo "  presign       ARGS='<key> [secs]'  Generate a pre-signed URL"

install:
	pip install -r requirements.txt

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
