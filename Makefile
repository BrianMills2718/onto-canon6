# onto-canon6 Makefile — project interface for agents and humans
#
# Standard targets (shared across ecosystem):
#   make test / make check / make cost / make errors
# Domain targets (onto-canon6 specific):
#   make extract / make candidates / make accept / make promote / make export
#
# Usage: make help

SHELL := /bin/bash
.DEFAULT_GOAL := help
PYTHON ?= $(if $(wildcard .venv/bin/python),$(CURDIR)/.venv/bin/python,python3)
CLI := $(PYTHON) -m onto_canon6
DAYS ?= 7
PROJECT ?= onto_canon6
LIMIT ?= 20

# Default extraction config
PROFILE_ID ?= psyop_seed
PROFILE_VERSION ?= 0.1.0
SUBMITTED_BY ?= agent:make
DB_PATH ?= var/review_state.sqlite3
OVERLAY_ROOT ?= var/ontology_overlays
GOAL ?= Extract all factual assertions directly supported by the source text.
OUTPUT ?= json

# ─── Shared: Testing ─────────────────────────────────────────────────────────

.PHONY: test test-quick check dev-setup

test:  ## Run full test suite
	@$(PYTHON) -m pytest tests/ -v \
		--ignore=tests/integration/test_notebook_process.py \
		--ignore=tests/adapters/test_digimon_export.py \
		--ignore=tests/integration/test_cli_flow.py

test-quick:  ## Run tests (no traceback)
	@$(PYTHON) -m pytest tests/ -q --tb=no \
		--ignore=tests/integration/test_notebook_process.py \
		--ignore=tests/adapters/test_digimon_export.py \
		--ignore=tests/integration/test_cli_flow.py

check:  ## Run tests + type check + source lint
	@echo "Running tests..."
	@$(PYTHON) -m pytest tests/ -q --tb=short \
		--ignore=tests/integration/test_notebook_process.py \
		--ignore=tests/adapters/test_digimon_export.py \
		--ignore=tests/integration/test_cli_flow.py
	@echo ""
	@echo "Running mypy..."
	@$(PYTHON) -m mypy src
	@echo ""
	@echo "Running ruff..."
	@$(PYTHON) -m ruff check src
	@echo ""
	@echo "All checks passed!"

dev-setup:  ## Install repo dev deps into the active interpreter
	@$(PYTHON) -m pip install -e ".[dev]"

# ─── Shared: Observability ───────────────────────────────────────────────────

.PHONY: cost errors summary

cost:  ## LLM spend for this project (DAYS=7)
	@$(PYTHON) -m llm_client cost --group-by task --days $(DAYS) --project $(PROJECT)

errors:  ## Recent extraction errors from observability DB (DAYS=7 LIMIT=20)
	@$(PYTHON) scripts/show_extraction_failures.py --days $(DAYS) --limit $(LIMIT)

summary:  ## Quick extraction stats from review DB
	@$(PYTHON) scripts/show_summary.py --db-path $(DB_PATH)

# ─── Shared: Git ─────────────────────────────────────────────────────────────

.PHONY: status

status:  ## Show git status
	@git status --short --branch

# ─── Domain: Extraction ──────────────────────────────────────────────────────

.PHONY: extract candidates accept reject promote export export-foundation auto-resolve import-rv3 evaluate-rules

extract:  ## Extract assertions from text (INPUT= required, GOAL= optional)
ifndef INPUT
	$(error INPUT is required. Usage: make extract INPUT=path/to/text.md GOAL="...")
endif
	@$(CLI) extract-text \
		--goal "$(GOAL)" \
		--input $(INPUT) \
		--profile-id $(PROFILE_ID) --profile-version $(PROFILE_VERSION) \
		--submitted-by $(SUBMITTED_BY) \
		--review-db-path $(DB_PATH) --overlay-root $(OVERLAY_ROOT) \
		--output $(OUTPUT)

candidates:  ## List pending candidates
	@$(CLI) list-candidates \
		--review-db-path $(DB_PATH) \
		--review-status pending_review \
		--output $(OUTPUT)

accept:  ## Accept a candidate (ID= required)
ifndef ID
	$(error ID is required. Usage: make accept ID=cand_abc123)
endif
	@$(CLI) review-candidate \
		--review-db-path $(DB_PATH) \
		--candidate-id $(ID) --decision accepted \
		--actor-id $(SUBMITTED_BY)

reject:  ## Reject a candidate (ID= required)
ifndef ID
	$(error ID is required. Usage: make reject ID=cand_abc123)
endif
	@$(CLI) review-candidate \
		--review-db-path $(DB_PATH) \
		--candidate-id $(ID) --decision rejected \
		--actor-id $(SUBMITTED_BY)

promote:  ## Promote accepted candidate to graph (ID= required)
ifndef ID
	$(error ID is required. Usage: make promote ID=cand_abc123)
endif
	@$(CLI) promote-candidate \
		--review-db-path $(DB_PATH) \
		--candidate-id $(ID) --actor-id $(SUBMITTED_BY)

accept-all:  ## Accept all pending candidates in batch
	@$(CLI) accept-all 		--review-db-path $(DB_PATH) 		--output $(OUTPUT)

promote-all:  ## Promote all accepted candidates to graph
	@$(CLI) promote-all 		--review-db-path $(DB_PATH) 		--output $(OUTPUT)

govern:  ## Full auto pipeline: accept-all → promote-all → auto-resolve
	@$(CLI) accept-all --review-db-path $(DB_PATH) --output $(OUTPUT)
	@$(CLI) promote-all --review-db-path $(DB_PATH) --output $(OUTPUT)
	@$(CLI) auto-resolve-identities --review-db-path $(DB_PATH) --output $(OUTPUT)

export:  ## Export governed bundle
	@$(CLI) export-governed-bundle \
		--review-db-path $(DB_PATH) \
		--output $(OUTPUT)

export-foundation:  ## Export as Foundation Assertion IR
	@$(PYTHON) -c "\
	import sys; sys.path.insert(0, 'src'); \
	from onto_canon6.adapters.foundation_assertion_export import export_foundation_assertions; \
	import json; \
	assertions = export_foundation_assertions('$(DB_PATH)'); \
	print(json.dumps([a.model_dump(exclude_none=True) for a in assertions], indent=2))"

auto-resolve:  ## Run automated entity resolution on promoted entities
	@$(CLI) auto-resolve-identities \
		--review-db-path $(DB_PATH) \
		--output $(OUTPUT)

import-rv3:  ## Import research_v3 graph.yaml (INPUT= required)
ifndef INPUT
	$(error INPUT is required. Usage: make import-rv3 INPUT=path/to/graph.yaml)
endif
	@$(CLI) import-research-v3 \
		--input $(INPUT) \
		--review-db-path $(DB_PATH) --overlay-root $(OVERLAY_ROOT) \
		--output $(OUTPUT)

import-rv3-memo:  ## Import research_v3 loop memo (INPUT= required, LIMIT= optional)
ifndef INPUT
	$(error INPUT is required. Usage: make import-rv3-memo INPUT=path/to/memo.yaml LIMIT=10)
endif
	@$(CLI) import-rv3-memo 		--input $(INPUT) 		$(if $(LIMIT),--limit $(LIMIT),) 		--review-db-path $(DB_PATH) --overlay-root $(OVERLAY_ROOT) 		--output $(OUTPUT)

evaluate-rules:  ## Evaluate ProbLog rules (RULES= required)
ifndef RULES
	$(error RULES is required. Usage: make evaluate-rules RULES=path/to/rules.pl)
endif
	@$(CLI) evaluate-rules \
		--review-db-path $(DB_PATH) \
		--rules-file $(RULES) \
		--output $(OUTPUT)

# ─── Domain: Experiment ──────────────────────────────────────────────────────

.PHONY: experiment baseline schema

experiment:  ## Run prompt_eval extraction experiment (CASES=4, RUNS=1)
	@$(CLI) run-extraction-prompt-experiment \
		--case-limit $(or $(CASES),4) --n-runs $(or $(RUNS),1) \
		--comparison-method none --output $(OUTPUT)

baseline:  ## Run baseline SPO comparison (CASES=5)
	@$(PYTHON) scripts/baseline_extraction_comparison.py \
		--case-limit $(or $(CASES),5) --budget 0.10

schema:  ## Print the extraction JSON schema
	@$(PYTHON) -c "\
	import sys, json; sys.path.insert(0, 'src'); \
	from onto_canon6.pipeline import TextExtractionResponse; \
	print(json.dumps(TextExtractionResponse.model_json_schema(), indent=2))"

# ─── Domain: Diagnostics ─────────────────────────────────────────────────────

.PHONY: failures diagnose

failures:  ## Show recent extraction failures with raw response + validation errors (DAYS=1)
	@$(PYTHON) scripts/show_extraction_failures.py --days $(DAYS) --limit $(LIMIT)

diagnose:  ## Diagnose a specific trace (TRACE= required)
ifndef TRACE
	$(error TRACE is required. Usage: make diagnose TRACE=extraction_abc123)
endif
	@$(PYTHON) scripts/show_extraction_failures.py --trace $(TRACE)

# ─── Help ────────────────────────────────────────────────────────────────────

.PHONY: help

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
