"""Typed notebook-process registry and validation helpers.

This module implements the short-term executable-journey notebook process
locally for `onto-canon6` without waiting for wider `project-meta`
integration. The goal is narrow and explicit:

1. one canonical notebook per end-to-end journey;
2. auxiliary notebooks classified as deep dives or planning companions;
3. phase contracts stored outside the notebook in machine-readable form;
4. fail-loud validation that the registry and notebook files stay aligned.

The validator is intentionally conservative. It does not try to infer notebook
semantics from arbitrary prose. Instead, it checks the explicit registry, file
existence, basic notebook JSON structure, and whether the canonical journey
notebook actually mentions the declared phase ids.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from .config import get_config, repo_root

PhaseStatusValue = Literal["planned", "partial", "proven"]
ExecutionModeValue = Literal["planned", "stub", "fixture", "dry_run", "live"]
JourneyNotebookModeValue = Literal["planning", "proof", "mixed"]
AuxiliaryNotebookKindValue = Literal["deep_dive", "planning_companion"]


class NotebookProcessError(RuntimeError):
    """Raised when the notebook registry or notebook files are inconsistent."""


class JourneyPhaseContract(BaseModel):
    """One machine-readable phase contract for a canonical journey notebook.

    The short-term notebook rules require the phase contract to exist outside
    the notebook as well as inside it. This model is the external contract:
    it names the artifact boundary, maturity, execution mode, and linked code,
    tests, docs, and evidence for one phase.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    phase_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    purpose: str = Field(min_length=1)
    input_artifact: str = Field(min_length=1)
    output_artifact: str = Field(min_length=1)
    acceptance_criteria: tuple[str, ...] = Field(min_length=1)
    status: PhaseStatusValue
    execution_mode: ExecutionModeValue
    proof_critical: bool = False
    promotion_path: str | None = None
    related_code: tuple[str, ...] = ()
    related_tests: tuple[str, ...] = ()
    related_docs: tuple[str, ...] = ()
    related_evidence: tuple[str, ...] = ()


class JourneyNotebookEntry(BaseModel):
    """One canonical end-to-end journey notebook plus its phase contracts."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    journey_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    purpose: str = Field(min_length=1)
    notebook: str = Field(min_length=1)
    notebook_mode: JourneyNotebookModeValue
    status: PhaseStatusValue
    related_docs: tuple[str, ...] = ()
    related_tests: tuple[str, ...] = ()
    related_evidence: tuple[str, ...] = ()
    phases: tuple[JourneyPhaseContract, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def _validate_unique_phase_ids(self) -> "JourneyNotebookEntry":
        """Require phase ids to stay unique within one journey."""

        seen: set[str] = set()
        for phase in self.phases:
            if phase.phase_id in seen:
                raise ValueError(
                    f"duplicate phase_id '{phase.phase_id}' in journey '{self.journey_id}'"
                )
            seen.add(phase.phase_id)
        if self.status == "proven" and any(phase.status != "proven" for phase in self.phases):
            raise ValueError(
                f"journey '{self.journey_id}' cannot be marked proven while any phase is not proven"
            )
        return self

    def phase_ids(self) -> tuple[str, ...]:
        """Return the declared phase ids in order."""

        return tuple(phase.phase_id for phase in self.phases)

    def phase_by_id(self, phase_id: str) -> JourneyPhaseContract:
        """Return one phase contract or fail loudly if it does not exist."""

        for phase in self.phases:
            if phase.phase_id == phase_id:
                return phase
        raise NotebookProcessError(
            f"journey '{self.journey_id}' does not define phase_id '{phase_id}'"
        )


class AuxiliaryNotebookEntry(BaseModel):
    """One auxiliary notebook linked to a canonical journey.

    Auxiliary notebooks are allowed, but they must be explicit about what they
    are for. This keeps deep dives and planning companions visible without
    pretending they are separate end-to-end journeys.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    notebook_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    purpose: str = Field(min_length=1)
    kind: AuxiliaryNotebookKindValue
    notebook: str = Field(min_length=1)
    journey_id: str | None = None
    related_phase_ids: tuple[str, ...] = ()
    related_docs: tuple[str, ...] = ()
    related_tests: tuple[str, ...] = ()
    related_evidence: tuple[str, ...] = ()


class NotebookRegistry(BaseModel):
    """Top-level registry for canonical and auxiliary notebook artifacts."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    journeys: tuple[JourneyNotebookEntry, ...] = Field(min_length=1)
    auxiliary_notebooks: tuple[AuxiliaryNotebookEntry, ...] = ()

    @model_validator(mode="after")
    def _validate_unique_ids(self) -> "NotebookRegistry":
        """Require journey ids, auxiliary ids, and notebook paths to stay unique."""

        seen_journeys: set[str] = set()
        seen_notebook_paths: set[str] = set()
        for journey in self.journeys:
            if journey.journey_id in seen_journeys:
                raise ValueError(f"duplicate journey_id '{journey.journey_id}'")
            seen_journeys.add(journey.journey_id)
            if journey.notebook in seen_notebook_paths:
                raise ValueError(f"duplicate notebook path '{journey.notebook}'")
            seen_notebook_paths.add(journey.notebook)

        seen_auxiliary: set[str] = set()
        for notebook in self.auxiliary_notebooks:
            if notebook.notebook_id in seen_auxiliary:
                raise ValueError(f"duplicate auxiliary notebook_id '{notebook.notebook_id}'")
            seen_auxiliary.add(notebook.notebook_id)
            if notebook.notebook in seen_notebook_paths:
                raise ValueError(f"duplicate notebook path '{notebook.notebook}'")
            seen_notebook_paths.add(notebook.notebook)
        return self

    def journey_by_id(self, journey_id: str) -> JourneyNotebookEntry:
        """Return one journey entry or fail loudly if it does not exist."""

        for journey in self.journeys:
            if journey.journey_id == journey_id:
                return journey
        raise NotebookProcessError(f"journey_id '{journey_id}' is not defined")


class NotebookValidationReport(BaseModel):
    """Small validation summary for the local notebook process."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    registry_path: str = Field(min_length=1)
    journey_count: int = Field(ge=1)
    auxiliary_notebook_count: int = Field(ge=0)
    phase_count: int = Field(ge=1)
    validated_notebooks: tuple[str, ...] = Field(min_length=1)


def default_notebook_registry_path() -> Path:
    """Return the config-backed notebook registry path."""

    return get_config().notebook_registry_path()


def load_notebook_registry(path: Path | None = None) -> NotebookRegistry:
    """Load the notebook registry and validate its schema eagerly."""

    registry_path = (path or default_notebook_registry_path()).resolve()
    if not registry_path.exists():
        raise NotebookProcessError(f"notebook registry not found: {registry_path}")

    raw = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise NotebookProcessError(
            f"notebook registry must decode to an object: {registry_path}"
        )
    return NotebookRegistry.model_validate(raw)


def validate_notebook_registry(path: Path | None = None) -> NotebookValidationReport:
    """Validate registry integrity and linked notebook/doc/test/code paths.

    The local short-term rules are intentionally mechanical:

    - registry file must exist and parse;
    - every referenced notebook/doc/test/code/evidence path must exist;
    - the canonical journey notebook must parse as notebook JSON;
    - each declared phase id must be explicitly present in that notebook.
    """

    registry_path = (path or default_notebook_registry_path()).resolve()
    registry = load_notebook_registry(registry_path)
    validated_notebooks: list[str] = []

    for journey in registry.journeys:
        notebook_path = _require_repo_path(journey.notebook)
        _validate_notebook_file(notebook_path)
        _validate_related_paths(
            journey.related_docs + journey.related_tests + journey.related_evidence
        )
        notebook_source = notebook_path.read_text(encoding="utf-8")
        _require_notebook_text(
            notebook_source=notebook_source,
            required_text=journey.journey_id,
            notebook_path=notebook_path,
            context=f"journey_id for {journey.journey_id}",
        )
        for phase in journey.phases:
            _require_notebook_text(
                notebook_source=notebook_source,
                required_text=phase.phase_id,
                notebook_path=notebook_path,
                context=f"phase_id {phase.phase_id}",
            )
            _validate_related_paths(
                phase.related_code
                + phase.related_tests
                + phase.related_docs
                + phase.related_evidence
            )
        validated_notebooks.append(str(notebook_path.relative_to(repo_root())))

    for notebook in registry.auxiliary_notebooks:
        notebook_path = _require_repo_path(notebook.notebook)
        _validate_notebook_file(notebook_path)
        _validate_related_paths(
            notebook.related_docs + notebook.related_tests + notebook.related_evidence
        )
        if notebook.journey_id is not None:
            journey = registry.journey_by_id(notebook.journey_id)
            for phase_id in notebook.related_phase_ids:
                journey.phase_by_id(phase_id)
        validated_notebooks.append(str(notebook_path.relative_to(repo_root())))

    return NotebookValidationReport(
        registry_path=str(registry_path.relative_to(repo_root())),
        journey_count=len(registry.journeys),
        auxiliary_notebook_count=len(registry.auxiliary_notebooks),
        phase_count=sum(len(journey.phases) for journey in registry.journeys),
        validated_notebooks=tuple(validated_notebooks),
    )


def _require_repo_path(relative_path: str) -> Path:
    """Resolve one repo-relative path and require that it exists."""

    path = (repo_root() / relative_path).resolve()
    if not path.exists():
        raise NotebookProcessError(f"referenced path does not exist: {relative_path}")
    return path


def _validate_related_paths(relative_paths: tuple[str, ...]) -> None:
    """Require each linked doc/code/test/evidence path to exist."""

    for relative_path in relative_paths:
        _require_repo_path(relative_path)


def _validate_notebook_file(path: Path) -> None:
    """Require that one notebook path parses as basic notebook JSON."""

    if path.suffix != ".ipynb":
        raise NotebookProcessError(f"notebook path must end with .ipynb: {path}")
    try:
        decoded = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise NotebookProcessError(f"invalid notebook JSON for {path}: {exc}") from exc
    cells = decoded.get("cells")
    if not isinstance(cells, list) or not cells:
        raise NotebookProcessError(f"notebook must contain cells: {path}")
    first_cell = cells[0]
    if not isinstance(first_cell, dict) or first_cell.get("cell_type") != "markdown":
        raise NotebookProcessError(
            f"notebook must begin with a markdown header cell: {path}"
        )


def _require_notebook_text(
    *,
    notebook_source: str,
    required_text: str,
    notebook_path: Path,
    context: str,
) -> None:
    """Require one literal marker to exist in the notebook JSON source."""

    if required_text not in notebook_source:
        raise NotebookProcessError(
            f"notebook {notebook_path.relative_to(repo_root())} does not mention {context}"
        )


__all__ = [
    "AuxiliaryNotebookEntry",
    "AuxiliaryNotebookKindValue",
    "ExecutionModeValue",
    "JourneyNotebookEntry",
    "JourneyNotebookModeValue",
    "JourneyPhaseContract",
    "NotebookProcessError",
    "NotebookRegistry",
    "NotebookValidationReport",
    "PhaseStatusValue",
    "default_notebook_registry_path",
    "load_notebook_registry",
    "validate_notebook_registry",
]
