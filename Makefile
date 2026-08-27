PYTHON := uv run
WEB_DIR := apps/web
IMAGE_NAME ?= vericlose:dev
CONTAINER_NAME ?= vericlose-judge
PORT ?= 8000
BASE_URL ?= http://localhost:$(PORT)
export UV_CACHE_DIR := $(CURDIR)/.uv-cache

.PHONY: setup test lint format typecheck build-web verify generate import-batch dev dev-api dev-web health image judge smoke smoke-local smoke-container

SEED ?= 42
PAYMENTS ?= 120
SETTLEMENTS ?= 24
EXCEPTION_RATE ?= 0.40
GENERATED_OUTPUT ?= .data/synthetic/seed-$(SEED)

setup:
	uv sync --dev
	pnpm install --frozen-lockfile

test:
	$(PYTHON) pytest

lint:
	$(PYTHON) ruff check apps core synthetic evaluation tests scripts

format:
	$(PYTHON) ruff format apps core synthetic evaluation tests scripts
	$(PYTHON) ruff check --fix apps core synthetic evaluation tests scripts

typecheck:
	pnpm --filter @vericlose/web typecheck

build-web:
	pnpm --filter @vericlose/web build

verify: lint test typecheck build-web

generate:
	$(PYTHON) python -m synthetic.generate --seed $(SEED) --payments $(PAYMENTS) --settlements $(SETTLEMENTS) --exception-rate $(EXCEPTION_RATE) --output $(GENERATED_OUTPUT)

RUN_ID ?= import-seed-$(SEED)-v1
IMPORT_DATABASE ?= .data/vericlose.duckdb
IMPORT_DATA_DIR ?= .data/imports

import-batch:
	$(PYTHON) python -m scripts.import_batch --gateway $(GENERATED_OUTPUT)/inputs/gateway.csv --bank $(GENERATED_OUTPUT)/inputs/bank.csv --erp $(GENERATED_OUTPUT)/inputs/erp_gl.csv --run-id $(RUN_ID) --database $(IMPORT_DATABASE) --data-dir $(IMPORT_DATA_DIR)

dev:
	bash scripts/dev.sh

dev-api:
	$(PYTHON) uvicorn apps.api.app.main:app --host 0.0.0.0 --port 8000 --reload

dev-web:
	pnpm --filter @vericlose/web dev

health:
	curl --fail --silent --show-error $(BASE_URL)/health/ready

image:
	docker build --build-arg VERICLOSE_BUILD_COMMIT=local -t $(IMAGE_NAME) .

judge:
	docker run --rm --name $(CONTAINER_NAME) -p $(PORT):8000 -v "$(CURDIR)/.data:/app/data" $(IMAGE_NAME)

smoke:
	$(PYTHON) python scripts/smoke.py --base-url $(BASE_URL)

smoke-local:
	bash scripts/smoke_local.sh $(PORT)

smoke-container:
	bash scripts/smoke_container.sh $(PORT) $(IMAGE_NAME)
