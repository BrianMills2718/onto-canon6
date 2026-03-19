"""Typed repository configuration for onto-canon6.

This module keeps the bootstrap repo aligned with the workspace design rules:
configuration is loaded from `config/config.yaml`, validated eagerly, and used
as the single source of truth for repository-relative paths.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field

AcceptancePolicyValue = Literal["record_only", "apply_to_overlay"]
CLIOutputFormatValue = Literal["json", "text"]
MCPTransportValue = Literal["stdio"]
PromptEvalComparisonMethodValue = Literal["bootstrap", "welch"]


class ConfigError(RuntimeError):
    """Raised when the repository configuration file is missing or invalid."""


class ProjectConfig(BaseModel):
    """Project metadata used by packaging and repo-local tooling."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str = Field(min_length=1)
    package_name: str = Field(min_length=1)
    version: str = Field(min_length=1)


class PathsConfig(BaseModel):
    """Repository-relative paths used during the bootstrap phase."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    adr_root: str = Field(min_length=1)
    notebooks_root: str = Field(min_length=1)
    notebook_registry_path: str = Field(min_length=1)
    local_profiles_root: str = Field(min_length=1)
    local_ontology_packs_root: str = Field(min_length=1)
    donor_profiles_root: str = Field(min_length=1)
    donor_ontology_packs_root: str = Field(min_length=1)
    review_db_path: str = Field(min_length=1)
    overlay_root: str = Field(min_length=1)


class PipelineConfig(BaseModel):
    """Pipeline defaults for the current proving slice."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    default_acceptance_policy: AcceptancePolicyValue


class OntologyRuntimeConfig(BaseModel):
    """Ontology-runtime defaults that control local overlay behavior."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    overlay_pack_suffix: str = Field(min_length=1)


class ExtractionConfig(BaseModel):
    """Text-extraction defaults for the first llm_client-backed Phase 4 path.

    Explicit completion-token caps are intentionally excluded here. The
    extraction path relies on llm_client's model-aware defaults so structured
    outputs are not prematurely truncated by repo-local ceilings.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    selection_task: str = Field(min_length=1)
    prompt_template: str = Field(min_length=1)
    prompt_ref: str = Field(min_length=1)
    timeout_seconds: int = Field(ge=1)
    num_retries: int = Field(ge=0)
    max_budget_usd: float = Field(gt=0)


class ChunkingConfig(BaseModel):
    """Text-chunking defaults for real long-document extraction runs.

    The first real investigation showed that whole-report extraction can exceed
    the structured-output budget. These values keep the chunking helper
    explicit and repo-configured rather than hiding size limits inside the CLI.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    target_max_chars: int = Field(ge=200)
    min_chunk_chars: int = Field(ge=1)
    max_chunk_chars: int = Field(ge=200)


class EvaluationConfig(BaseModel):
    """Live-evaluation defaults for the Phase 5 benchmark slice."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    benchmark_fixture: str = Field(min_length=1)
    observability_dataset: str = Field(min_length=1)
    observability_phase: str = Field(min_length=1)
    judge_selection_task: str = Field(min_length=1)
    judge_prompt_template: str = Field(min_length=1)
    judge_prompt_ref: str = Field(min_length=1)
    judge_timeout_seconds: int = Field(ge=1)
    judge_num_retries: int = Field(ge=0)
    judge_max_budget_usd: float = Field(gt=0)
    judge_max_output_tokens: int = Field(ge=1)
    prompt_experiment: "PromptEvalExperimentConfig"


class PromptEvalVariantConfig(BaseModel):
    """One configured prompt variant for extraction-quality experiments.

    The experiment runner compares prompt templates over the same extraction
    benchmark fixture. Each variant keeps an explicit prompt reference for
    shared observability even though the templates still live in this repo's
    local `prompts/` directory. Variants may also narrow the candidate or
    evidence budget so prompt experiments can test smaller extraction asks
    without mutating the repo-wide defaults.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str = Field(min_length=1)
    prompt_template: str = Field(min_length=1)
    prompt_ref: str = Field(min_length=1)
    max_candidates_per_case: int | None = Field(default=None, ge=1)
    max_evidence_spans_per_candidate: int | None = Field(default=None, ge=1)


class PromptEvalExperimentConfig(BaseModel):
    """Configurable defaults for the extraction prompt-variant experiment.

    This slice is intentionally narrow: it runs prompt variants over one
    single-profile benchmark fixture, scores them deterministically, and logs
    the run family through shared `llm_client`/`prompt_eval` observability.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    experiment_name: str = Field(min_length=1)
    observability_dataset: str = Field(min_length=1)
    observability_phase: str = Field(min_length=1)
    selection_task: str = Field(min_length=1)
    n_runs: int = Field(ge=1)
    temperature: float = Field(ge=0.0)
    timeout_seconds: int = Field(ge=1)
    num_retries: int = Field(ge=0)
    max_budget_usd: float = Field(gt=0.0)
    baseline_variant_name: str = Field(min_length=1)
    comparison_method: PromptEvalComparisonMethodValue
    comparison_confidence: float = Field(gt=0.0, lt=1.0)
    max_candidates_per_case: int = Field(ge=1)
    max_evidence_spans_per_candidate: int = Field(ge=1)
    variants: tuple[PromptEvalVariantConfig, ...] = Field(min_length=2)


class CLIConfig(BaseModel):
    """CLI defaults for the first operational surface.

    The CLI still allows explicit user overrides at the command line, but the
    default output style and source-kind labeling should remain repo-configured
    rather than hidden in parser code.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    default_output_format: CLIOutputFormatValue
    file_source_kind: str = Field(min_length=1)


class MCPConfig(BaseModel):
    """MCP defaults for the first richer agent-facing surface."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    transport: MCPTransportValue


class WhyGameAdapterConfig(BaseModel):
    """Configurable defaults for the narrow WhyGame relationship adapter."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    default_profile_id: str = Field(min_length=1)
    default_profile_version: str = Field(min_length=1)
    source_kind: str = Field(min_length=1)
    register_artifact_by_default: bool


class AdaptersConfig(BaseModel):
    """Adapter defaults for the current successor slice."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    whygame: WhyGameAdapterConfig
    research_agent: "ResearchAgentAdapterConfig"


class ResearchAgentAdapterConfig(BaseModel):
    """Configurable defaults for the narrow research-agent producer helper."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    default_relationship_confidence: float = Field(gt=0.0, le=1.0)


class AppConfig(BaseModel):
    """Validated application configuration for onto-canon6."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    project: ProjectConfig
    paths: PathsConfig
    pipeline: PipelineConfig
    ontology_runtime: OntologyRuntimeConfig
    extraction: ExtractionConfig
    chunking: ChunkingConfig
    evaluation: EvaluationConfig
    cli: CLIConfig
    mcp: MCPConfig
    adapters: AdaptersConfig

    def resolve_repo_path(self, relative_path: str) -> Path:
        """Resolve a repository-relative path declared in config."""
        return (repo_root() / relative_path).resolve()

    def adr_dir(self) -> Path:
        """Return the configured ADR directory."""
        return self.resolve_repo_path(self.paths.adr_root)

    def notebooks_dir(self) -> Path:
        """Return the configured notebooks directory."""
        return self.resolve_repo_path(self.paths.notebooks_root)

    def donor_profiles_dir(self) -> Path:
        """Return the configured donor profiles directory."""

        return self.resolve_repo_path(self.paths.donor_profiles_root)

    def local_profiles_dir(self) -> Path:
        """Return the configured repo-local profiles directory."""

        return self.resolve_repo_path(self.paths.local_profiles_root)

    def notebook_registry_path(self) -> Path:
        """Return the configured notebook-registry path."""

        return self.resolve_repo_path(self.paths.notebook_registry_path)

    def donor_ontology_packs_dir(self) -> Path:
        """Return the configured donor ontology-pack directory."""

        return self.resolve_repo_path(self.paths.donor_ontology_packs_root)

    def local_ontology_packs_dir(self) -> Path:
        """Return the configured repo-local ontology-pack directory."""

        return self.resolve_repo_path(self.paths.local_ontology_packs_root)

    def profile_search_roots(self) -> tuple[Path, ...]:
        """Return the search order for profiles: local first, donor second."""

        return (
            self.local_profiles_dir(),
            self.donor_profiles_dir(),
        )

    def ontology_pack_search_roots(self) -> tuple[Path, ...]:
        """Return the search order for ontology packs: local first, donor second."""

        return (
            self.local_ontology_packs_dir(),
            self.donor_ontology_packs_dir(),
        )

    def review_db_path(self) -> Path:
        """Return the configured review-state SQLite database path."""

        return self.resolve_repo_path(self.paths.review_db_path)

    def overlay_root(self) -> Path:
        """Return the configured local ontology-overlay root directory."""

        return self.resolve_repo_path(self.paths.overlay_root)

    def extraction_prompt_template(self) -> Path:
        """Return the configured text-extraction prompt template path."""

        return self.resolve_repo_path(self.extraction.prompt_template)

    def evaluation_benchmark_fixture(self) -> Path:
        """Return the configured benchmark fixture path for live evaluation."""

        return self.resolve_repo_path(self.evaluation.benchmark_fixture)

    def evaluation_judge_prompt_template(self) -> Path:
        """Return the configured reasonableness-judge prompt template path."""

        return self.resolve_repo_path(self.evaluation.judge_prompt_template)

    def evaluation_prompt_experiment_variant_template(self, relative_path: str) -> Path:
        """Return the configured extraction prompt-experiment template path."""

        return self.resolve_repo_path(relative_path)


EvaluationConfig.model_rebuild()
AdaptersConfig.model_rebuild()


def repo_root() -> Path:
    """Return the repository root for onto-canon6."""
    return Path(__file__).resolve().parents[2]


def default_config_path() -> Path:
    """Return the required repository configuration path."""
    return repo_root() / "config" / "config.yaml"


@lru_cache(maxsize=1)
def get_config() -> AppConfig:
    """Load and cache the repository configuration.

    This fails loudly on missing files, non-object YAML, or schema violations so
    configuration drift cannot masquerade as defaults.
    """

    path = default_config_path()
    if not path.exists():
        raise ConfigError(f"configuration file not found: {path}")

    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ConfigError(f"configuration file must decode to an object: {path}")

    return AppConfig.model_validate(raw)


def clear_config_cache() -> None:
    """Clear the cached config for tests that mutate repository files."""

    get_config.cache_clear()


__all__ = [
    "AcceptancePolicyValue",
    "AppConfig",
    "CLIOutputFormatValue",
    "ConfigError",
    "MCPTransportValue",
    "clear_config_cache",
    "default_config_path",
    "get_config",
    "repo_root",
]
