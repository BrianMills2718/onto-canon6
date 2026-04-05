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

.PHONY: test test-quick check dev-setup verify-setup smoke

test:  ## Run full test suite
	@$(PYTHON) -m pytest -q

test-quick:  ## Run tests (no traceback)
	@$(PYTHON) -m pytest -q --tb=no

check:  ## Run tests + type check + source lint
	@echo "Running tests..."
	@$(PYTHON) -m pytest -q --tb=short
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

verify-setup:  ## Verify Python deps, donor assets, and canonical proof artifacts
	@$(PYTHON) scripts/verify_setup.py

smoke:  ## Run the canonical no-LLM smoke workflow over proved local artifacts
	@$(PYTHON) scripts/e2e_integration_test.py

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

govern:  ## Full auto pipeline: accept-all → promote-all → resolve identities
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

auto-resolve:  ## Run automated entity resolution (uses config default strategy)
	@$(CLI) auto-resolve-identities \
		--review-db-path $(DB_PATH) \
		--output $(OUTPUT)

resolve:  ## Alias for auto-resolve — run entity resolution with config strategy
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

.PHONY: experiment baseline schema scale-test scale-baseline

experiment:  ## Run prompt_eval extraction experiment (CASES=4, RUNS=1)
	@$(CLI) run-extraction-prompt-experiment \
		--case-limit $(or $(CASES),4) --n-runs $(or $(RUNS),1) \
		--comparison-method none --output $(OUTPUT)

baseline:  ## Run baseline SPO comparison (CASES=5)
	@$(PYTHON) scripts/baseline_extraction_comparison.py \
		--case-limit $(or $(CASES),5) --budget 0.10

scale-test:  ## Run the governed entity-resolution value proof (STRATEGY=exact|fuzzy|llm)
	@$(PYTHON) scripts/run_scale_test.py \
		--strategy $(or $(STRATEGY),exact) \
		--db-dir $(or $(DB_DIR),var/scale_test)

scale-baseline:  ## Run the bare entity-extraction baseline on the synthetic corpus
	@$(PYTHON) scripts/run_bare_entity_baseline.py \
		--budget $(or $(BUDGET),0.10)

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

# ─── Full pipeline (cross-project) ──────────────────────────────────────────

pipeline:  ## Full pipeline: research_v3 graph.yaml → onto-canon6 → DIGIMON export
ifndef INPUT
	$(error INPUT is required: make pipeline INPUT=path/to/graph.yaml)
endif
	@$(PYTHON) scripts/full_pipeline_e2e.py --graph $(INPUT) --output-dir var/pipeline_run --strategy $(or $(STRATEGY),exact)

pipeline-rv3-memo:  ## Full pipeline: research_v3 memo.yaml → shared claims → onto-canon6 → DIGIMON export
ifndef INPUT
	$(error INPUT is required: make pipeline-rv3-memo INPUT=path/to/memo.yaml)
endif
	@$(PYTHON) scripts/full_pipeline_e2e.py --memo $(INPUT) --output-dir var/pipeline_memo_run --strategy $(or $(STRATEGY),exact)

pipeline-gr:  ## Full pipeline: grounded-research handoff.json → onto-canon6 → DIGIMON export
ifndef INPUT
	$(error INPUT is required: make pipeline-gr INPUT=path/to/handoff.json)
endif
	@$(PYTHON) scripts/full_pipeline_e2e.py --handoff $(INPUT) --output-dir var/pipeline_gr_run --strategy $(or $(STRATEGY),exact)

# >>> META-PROCESS WORKTREE TARGETS >>>
WORKTREE_CREATE_SCRIPT := scripts/meta/worktree-coordination/create_worktree.py
WORKTREE_REMOVE_SCRIPT := scripts/meta/worktree-coordination/safe_worktree_remove.py
WORKTREE_CLAIMS_SCRIPT := scripts/meta/worktree-coordination/../check_coordination_claims.py
WORKTREE_SESSION_START_SCRIPT := scripts/meta/worktree-coordination/../session_start.py
WORKTREE_SESSION_HEARTBEAT_SCRIPT := scripts/meta/worktree-coordination/../session_heartbeat.py
WORKTREE_SESSION_STATUS_SCRIPT := scripts/meta/worktree-coordination/../session_status.py
WORKTREE_SESSION_FINISH_SCRIPT := scripts/meta/worktree-coordination/../session_finish.py
WORKTREE_SESSION_CLOSE_SCRIPT := scripts/meta/worktree-coordination/../session_close.py
WORKTREE_DIR ?= $(shell python "$(WORKTREE_CREATE_SCRIPT)" --repo-root . --print-default-worktree-dir)
WORKTREE_START_POINT ?= HEAD
WORKTREE_PROJECT ?= $(notdir $(CURDIR))
WORKTREE_AGENT ?= $(shell if [ -n "$$CODEX_THREAD_ID" ]; then printf codex; elif [ -n "$$CLAUDE_SESSION_ID" ] || [ -n "$$CLAUDE_CODE_SSE_PORT" ]; then printf claude-code; elif [ -n "$$OPENCLAW_SESSION_ID" ] || [ -n "$$OPENCLAW_RUN_ID" ]; then printf openclaw; fi)
SESSION_GOAL ?=
SESSION_PHASE ?=
SESSION_NEXT ?=
SESSION_DEPENDS ?=
SESSION_STOP_CONDITIONS ?=
SESSION_NOTE ?=

.PHONY: worktree worktree-list worktree-remove session-start session-heartbeat session-status session-finish session-close

worktree:  ## Create claimed worktree (BRANCH=name TASK="..." [PLAN=N] [AGENT=name])
ifndef BRANCH
	$(error BRANCH is required. Usage: make worktree BRANCH=plan-42-feature TASK="Describe the task")
endif
ifndef TASK
	$(error TASK is required. Usage: make worktree BRANCH=plan-42-feature TASK="Describe the task")
endif
ifndef SESSION_GOAL
	$(error SESSION_GOAL is required. Name the broader objective, not the local branch)
endif
ifndef SESSION_PHASE
	$(error SESSION_PHASE is required. Describe the current execution phase)
endif
ifndef WORKTREE_AGENT
	$(error Unable to infer agent runtime. Set AGENT via WORKTREE_AGENT=codex|claude-code|openclaw)
endif
	@if [ ! -f "$(WORKTREE_CREATE_SCRIPT)" ]; then \
		echo "Missing worktree coordination module: $(WORKTREE_CREATE_SCRIPT)"; \
		echo "Install or sync the sanctioned worktree-coordination module before using make worktree."; \
		exit 1; \
	fi
	@if [ ! -f "$(WORKTREE_CLAIMS_SCRIPT)" ]; then \
		echo "Missing worktree coordination module: $(WORKTREE_CLAIMS_SCRIPT)"; \
		echo "Install or sync the sanctioned worktree-coordination module before using make worktree."; \
		exit 1; \
	fi
	@if [ ! -f "$(WORKTREE_SESSION_START_SCRIPT)" ]; then \
		echo "Missing session lifecycle module: $(WORKTREE_SESSION_START_SCRIPT)"; \
		echo "Install or sync the sanctioned session lifecycle module before using make worktree."; \
		exit 1; \
	fi
	@python "$(WORKTREE_CLAIMS_SCRIPT)" --claim \
		--agent "$(WORKTREE_AGENT)" \
		--project "$(WORKTREE_PROJECT)" \
		--scope "$(BRANCH)" \
		--intent "$(TASK)" \
		--claim-type program \
		--branch "$(BRANCH)" \
		--worktree-path "$(WORKTREE_DIR)/$(BRANCH)" \
		$(if $(PLAN),--plan "Plan #$(PLAN)",)
	@mkdir -p "$(WORKTREE_DIR)"
	@if ! python "$(WORKTREE_CREATE_SCRIPT)" --repo-root . --path "$(WORKTREE_DIR)/$(BRANCH)" --branch "$(BRANCH)" --start-point "$(WORKTREE_START_POINT)"; then \
		python "$(WORKTREE_CLAIMS_SCRIPT)" --release --agent "$(WORKTREE_AGENT)" --project "$(WORKTREE_PROJECT)" --scope "$(BRANCH)" >/dev/null 2>&1 || true; \
		exit 1; \
	fi
	@if ! python "$(WORKTREE_SESSION_START_SCRIPT)" \
		--agent "$(WORKTREE_AGENT)" \
		--project "$(WORKTREE_PROJECT)" \
		--scope "$(BRANCH)" \
		--intent "$(TASK)" \
		--repo-root "$(CURDIR)" \
		--worktree-path "$(WORKTREE_DIR)/$(BRANCH)" \
		--branch "$(BRANCH)" \
		--broader-goal "$(SESSION_GOAL)" \
		--current-phase "$(SESSION_PHASE)" \
		$(if $(PLAN),--plan "Plan #$(PLAN)",) \
		$(if $(SESSION_NEXT),--next-phase "$(SESSION_NEXT)",) \
		$(if $(SESSION_DEPENDS),--depends-on "$(SESSION_DEPENDS)",) \
		$(if $(SESSION_STOP_CONDITIONS),--stop-condition "$(SESSION_STOP_CONDITIONS)",) \
		$(if $(SESSION_NOTE),--notes "$(SESSION_NOTE)",); then \
		git worktree remove --force "$(WORKTREE_DIR)/$(BRANCH)" >/dev/null 2>&1 || true; \
		git branch -D "$(BRANCH)" >/dev/null 2>&1 || true; \
		python "$(WORKTREE_CLAIMS_SCRIPT)" --release --agent "$(WORKTREE_AGENT)" --project "$(WORKTREE_PROJECT)" --scope "$(BRANCH)" >/dev/null 2>&1 || true; \
		exit 1; \
	fi
	@echo ""
	@echo "Worktree created at $(WORKTREE_DIR)/$(BRANCH)"
	@echo "Claim created for branch $(BRANCH)"
	@echo "Session contract started for $(SESSION_GOAL)"

session-start:  ## Create or refresh the active session contract for BRANCH=name
ifndef BRANCH
	$(error BRANCH is required. Usage: make session-start BRANCH=plan-42-feature TASK="..." SESSION_GOAL="..." SESSION_PHASE="...")
endif
ifndef TASK
	$(error TASK is required. Usage: make session-start BRANCH=plan-42-feature TASK="...")
endif
ifndef SESSION_GOAL
	$(error SESSION_GOAL is required. Name the broader objective, not the local branch)
endif
ifndef SESSION_PHASE
	$(error SESSION_PHASE is required. Describe the current execution phase)
endif
ifndef WORKTREE_AGENT
	$(error Unable to infer agent runtime. Set AGENT via WORKTREE_AGENT=codex|claude-code|openclaw)
endif
	@python "$(WORKTREE_SESSION_START_SCRIPT)" \
		--agent "$(WORKTREE_AGENT)" \
		--project "$(WORKTREE_PROJECT)" \
		--scope "$(BRANCH)" \
		--intent "$(TASK)" \
		--repo-root "$(CURDIR)" \
		--worktree-path "$(WORKTREE_DIR)/$(BRANCH)" \
		--branch "$(BRANCH)" \
		--broader-goal "$(SESSION_GOAL)" \
		--current-phase "$(SESSION_PHASE)" \
		$(if $(PLAN),--plan "Plan #$(PLAN)",) \
		$(if $(SESSION_NEXT),--next-phase "$(SESSION_NEXT)",) \
		$(if $(SESSION_DEPENDS),--depends-on "$(SESSION_DEPENDS)",) \
		$(if $(SESSION_STOP_CONDITIONS),--stop-condition "$(SESSION_STOP_CONDITIONS)",) \
		$(if $(SESSION_NOTE),--notes "$(SESSION_NOTE)",)

session-heartbeat:  ## Refresh heartbeat and optional phase for BRANCH=name
ifndef BRANCH
	$(error BRANCH is required. Usage: make session-heartbeat BRANCH=plan-42-feature)
endif
ifndef WORKTREE_AGENT
	$(error Unable to infer agent runtime. Set AGENT via WORKTREE_AGENT=codex|claude-code|openclaw)
endif
	@python "$(WORKTREE_SESSION_HEARTBEAT_SCRIPT)" \
		--agent "$(WORKTREE_AGENT)" \
		--project "$(WORKTREE_PROJECT)" \
		--scope "$(BRANCH)" \
		--branch "$(BRANCH)" \
		$(if $(SESSION_PHASE),--current-phase "$(SESSION_PHASE)",)

session-status:  ## Show live session summaries for this repo
	@python "$(WORKTREE_SESSION_STATUS_SCRIPT)" --project "$(WORKTREE_PROJECT)"

session-finish:  ## Finish the session for BRANCH=name; blocks if the worktree is dirty
ifndef BRANCH
	$(error BRANCH is required. Usage: make session-finish BRANCH=plan-42-feature)
endif
ifndef WORKTREE_AGENT
	$(error Unable to infer agent runtime. Set AGENT via WORKTREE_AGENT=codex|claude-code|openclaw)
endif
	@python "$(WORKTREE_SESSION_FINISH_SCRIPT)" \
		--agent "$(WORKTREE_AGENT)" \
		--project "$(WORKTREE_PROJECT)" \
		--scope "$(BRANCH)" \
		--worktree-path "$(WORKTREE_DIR)/$(BRANCH)" \
		$(if $(SESSION_NOTE),--note "$(SESSION_NOTE)",)

session-close:  ## Close the claimed lane for BRANCH=name: cleanup worktree + branch + claim together
ifndef BRANCH
	$(error BRANCH is required. Usage: make session-close BRANCH=plan-42-feature)
endif
ifndef WORKTREE_AGENT
	$(error Unable to infer agent runtime. Set AGENT via WORKTREE_AGENT=codex|claude-code|openclaw)
endif
	@python "$(WORKTREE_SESSION_CLOSE_SCRIPT)" \
		--agent "$(WORKTREE_AGENT)" \
		--project "$(WORKTREE_PROJECT)" \
		--scope "$(BRANCH)" \
		--worktree-path "$(WORKTREE_DIR)/$(BRANCH)" \
		--branch "$(BRANCH)" \
		$(if $(SESSION_NOTE),--note "$(SESSION_NOTE)",)

worktree-list:  ## Show claimed worktree coordination status
	@if [ ! -f "$(WORKTREE_CLAIMS_SCRIPT)" ]; then \
		echo "Missing worktree coordination module: $(WORKTREE_CLAIMS_SCRIPT)"; \
		echo "Install or sync the sanctioned worktree-coordination module before using make worktree-list."; \
		exit 1; \
	fi
	@python "$(WORKTREE_CLAIMS_SCRIPT)" --list

worktree-remove:  ## Safely remove worktree for BRANCH=name
ifndef BRANCH
	$(error BRANCH is required. Usage: make worktree-remove BRANCH=plan-42-feature)
endif
	@if [ ! -f "$(WORKTREE_SESSION_CLOSE_SCRIPT)" ]; then \
		echo "Missing session lifecycle module: $(WORKTREE_SESSION_CLOSE_SCRIPT)"; \
		echo "Install or sync the sanctioned session lifecycle module before using make worktree-remove."; \
		exit 1; \
	fi
	@$(MAKE) session-close BRANCH="$(BRANCH)" $(if $(SESSION_NOTE),SESSION_NOTE="$(SESSION_NOTE)",)
# <<< META-PROCESS WORKTREE TARGETS <<<
