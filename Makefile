PYTHON := uv run
WEB_DIR := apps/web
IMAGE_NAME ?= vericlose:dev
CONTAINER_NAME ?= vericlose-judge
HOST_UID ?= $(shell id -u)
HOST_GID ?= $(shell id -g)
PORT ?= 8000
BASE_URL ?= http://localhost:$(PORT)
SMOKE_OUTPUT ?=
JUDGE_MODEL_ENV := $(if $(VERICLOSE_MODEL_API_KEY),-e VERICLOSE_MODEL_API_KEY) $(if $(VERICLOSE_MODEL_NAME),-e VERICLOSE_MODEL_NAME) $(if $(VERICLOSE_MODEL_BASE_URL),-e VERICLOSE_MODEL_BASE_URL) $(if $(VERICLOSE_MODEL_TIMEOUT_SECONDS),-e VERICLOSE_MODEL_TIMEOUT_SECONDS)
export UV_CACHE_DIR := $(CURDIR)/.uv-cache

.PHONY: setup test lint format typecheck build-web verify generate import-batch reconcile benchmark benchmark-submission examples review-pack review-analyze demo dev dev-api dev-web health image judge smoke smoke-local smoke-container

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

CLOSE_RUN_ID ?= close-seed-$(SEED)-v1
EXCEPTIONS_OUTPUT ?= .data/reconciliation/$(CLOSE_RUN_ID)-exceptions.json

reconcile:
	$(PYTHON) python -m scripts.reconcile --gateway $(GENERATED_OUTPUT)/inputs/gateway.csv --bank $(GENERATED_OUTPUT)/inputs/bank.csv --erp $(GENERATED_OUTPUT)/inputs/erp_gl.csv --run-id $(CLOSE_RUN_ID) --seed $(SEED) --database $(IMPORT_DATABASE) --data-dir $(IMPORT_DATA_DIR) --exceptions-output $(EXCEPTIONS_OUTPUT)

BENCHMARK_OUTPUT ?= evaluation/reports/benchmark-latest

benchmark:
	$(PYTHON) python -m evaluation.benchmark --output-prefix $(BENCHMARK_OUTPUT)

benchmark-submission:
	$(PYTHON) python -m evaluation.benchmark --submission --output-prefix $(BENCHMARK_OUTPUT)

EXAMPLES_OUTPUT ?= docs/examples
BUILD_COMMIT ?= local

examples: benchmark
	$(PYTHON) python -m scripts.generate_examples --output $(EXAMPLES_OUTPUT) --build-commit $(BUILD_COMMIT)

REVIEW_PACK ?= docs/practitioner/review_01
REVIEW_PRIVATE ?= .data/practitioner/review_01/private

review-pack:
	$(PYTHON) python -m evaluation.practitioner_review build --output $(REVIEW_PACK) --private $(REVIEW_PRIVATE)

review-analyze:
	$(PYTHON) python -m evaluation.practitioner_review analyze --pack $(REVIEW_PACK) --private $(REVIEW_PRIVATE) --report docs/domain/DOMAIN_REVIEW_01.md --golden evaluation/golden/practitioner_review_01.json

demo:
	bash scripts/dev.sh

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
	docker run --rm --name $(CONTAINER_NAME) --user "$(HOST_UID):$(HOST_GID)" -p $(PORT):8000 -v "$(CURDIR)/.data:/app/data:Z" $(JUDGE_MODEL_ENV) $(IMAGE_NAME)

smoke:
	$(PYTHON) python scripts/smoke.py --base-url $(BASE_URL) $(if $(SMOKE_OUTPUT),--output $(SMOKE_OUTPUT),)

smoke-local:
	bash scripts/smoke_local.sh $(PORT) $(SMOKE_OUTPUT)

smoke-container:
	bash scripts/smoke_container.sh $(PORT) $(IMAGE_NAME) $(SMOKE_OUTPUT)
