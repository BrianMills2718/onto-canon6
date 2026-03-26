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
PYTHON := /home/brian/projects/.venv/bin/python
CLI := $(PYTHON) -m onto_canon6
DAYS ?= 7
PROJECT ?= onto_canon6

# Default extraction config
PROFILE_ID ?= psyop_seed
PROFILE_VERSION ?= 0.1.0
SUBMITTED_BY ?= agent:make
DB_PATH ?= var/review_state.sqlite3
OVERLAY_ROOT ?= var/ontology_overlays
GOAL ?= Extract all factual assertions directly supported by the source text.
OUTPUT ?= json

# ─── Shared: Testing ─────────────────────────────────────────────────────────

.PHONY: test test-quick check

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

check:  ## Run tests + type check
	@echo "Running tests..."
	@$(PYTHON) -m pytest tests/ -q --tb=short \
		--ignore=tests/integration/test_notebook_process.py \
		--ignore=tests/adapters/test_digimon_export.py \
		--ignore=tests/integration/test_cli_flow.py
	@echo ""
	@echo "All checks passed!"

# ─── Shared: Observability ───────────────────────────────────────────────────

.PHONY: cost errors summary

cost:  ## LLM spend for this project (DAYS=7)
	@$(PYTHON) -m llm_client cost --group-by task --days $(DAYS) --project $(PROJECT)

errors:  ## Error breakdown (DAYS=7)
	@$(PYTHON) -m llm_client cost --group-by model --days $(DAYS) --project $(PROJECT)

summary:  ## Quick extraction stats from review DB
	@$(PYTHON) -c "\
	import sqlite3; \
	conn = sqlite3.connect('$(DB_PATH)'); \
	total = conn.execute('SELECT COUNT(*) FROM candidate_assertions').fetchone()[0]; \
	accepted = conn.execute(\"SELECT COUNT(*) FROM candidate_assertions WHERE review_status='accepted'\").fetchone()[0]; \
	rejected = conn.execute(\"SELECT COUNT(*) FROM candidate_assertions WHERE review_status='rejected'\").fetchone()[0]; \
	pending = conn.execute(\"SELECT COUNT(*) FROM candidate_assertions WHERE review_status='pending_review'\").fetchone()[0]; \
	promoted = conn.execute('SELECT COUNT(*) FROM promoted_graph_assertions').fetchone()[0] if conn.execute(\"SELECT name FROM sqlite_master WHERE type='table' AND name='promoted_graph_assertions'\").fetchone() else 0; \
	print(f'Candidates: {total} (accepted={accepted}, rejected={rejected}, pending={pending})'); \
	print(f'Promoted:   {promoted}'); \
	rate = f'{100*accepted/total:.0f}%' if total else 'n/a'; \
	print(f'Acceptance: {rate}')"

# ─── Shared: Git ─────────────────────────────────────────────────────────────

.PHONY: status

status:  ## Show git status
	@git status --short --branch

# ─── Domain: Extraction ──────────────────────────────────────────────────────

.PHONY: extract candidates accept reject promote export export-foundation

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

# ─── Help ────────────────────────────────────────────────────────────────────

.PHONY: help

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
