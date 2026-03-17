"""Load donor ontology packs and profiles for the first successor slice.

This module deliberately ports only the narrow pack/profile loading surface
needed by the `onto-canon6` bootstrap. It avoids importing the old
`onto-canon5` runtime directly so the successor can own its contracts while
still proving them against real donor data.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Mapping, cast
import json
import re

import yaml

from ..config import get_config
from .contracts import OntologyMode, OntologyPolicy, PackRef, ProposalPolicy
from .overlays import load_overlay_predicate_additions, overlay_pack_ref_for

_PACK_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
_PACK_VERSION_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
_TYPE_CHECK_POLICY_VALUES = frozenset({"skip", "exact", "hierarchical"})
_TYPE_ADAPTER_VALUES = frozenset({"null", "dm2", "ontology_pack"})
_SEVERITY_VALUES = frozenset({"hard", "soft"})
_REQUIRED_CONTENT_KEYS = (
    "entity_types",
    "predicate_types",
    "role_types",
    "value_types",
    "hierarchy_edges",
    "predicate_role_edges",
    "source_mappings",
    "aliases",
    "constraints",
)


class OntologyPackLoadError(ValueError):
    """Raised when a donor ontology pack is missing or malformed."""


class ProfileLoadError(ValueError):
    """Raised when a donor validation profile is missing or malformed."""


@dataclass(frozen=True)
class PackRoleCardinality:
    """Declare min/max filler counts derived from donor pack content."""

    min_count: int
    max_count: int | None


@dataclass(frozen=True)
class PackPredicateRule:
    """Runtime predicate rule derived from donor pack role edges and constraints."""

    allowed_roles: tuple[str, ...]
    required_roles: tuple[str, ...]
    role_cardinality: Mapping[str, PackRoleCardinality]
    role_filler_types: Mapping[str, str]
    role_value_kinds: Mapping[str, str]


@dataclass
class PackPredicateRuleBuilder:
    """Mutable builder for constructing one immutable pack predicate rule."""

    allowed_roles: list[str]
    required_roles: list[str]
    role_cardinality: dict[str, PackRoleCardinality]
    role_filler_types: dict[str, str]
    role_value_kinds: dict[str, str]

    def add_role(
        self,
        *,
        runtime_name: str,
        required: bool,
        min_count: int,
        max_count: int | None,
    ) -> None:
        """Merge one role-edge declaration into the builder."""

        if runtime_name not in self.allowed_roles:
            self.allowed_roles.append(runtime_name)
        if required and runtime_name not in self.required_roles:
            self.required_roles.append(runtime_name)
        self.role_cardinality[runtime_name] = PackRoleCardinality(
            min_count=min_count,
            max_count=max_count,
        )

    def build(self) -> PackPredicateRule:
        """Freeze the current builder state into an immutable rule."""

        return PackPredicateRule(
            allowed_roles=tuple(sorted(self.allowed_roles)),
            required_roles=tuple(sorted(self.required_roles)),
            role_cardinality=dict(self.role_cardinality),
            role_filler_types=dict(self.role_filler_types),
            role_value_kinds=dict(self.role_value_kinds),
        )


@dataclass(frozen=True)
class LoadedOntologyPack:
    """Loaded donor ontology pack with runtime-facing validation views."""

    pack_ref: PackRef
    name: str
    description: str
    path: Path
    predicate_ids: frozenset[str]
    predicate_rules: Mapping[str, PackPredicateRule]
    type_parents: Mapping[str, tuple[str, ...]]


@dataclass(frozen=True)
class LoadedProfile:
    """Loaded donor profile summary for the first successor slice."""

    profile_id: str
    profile_version: str
    name: str
    ontology_version: str
    rule_version: str
    ontology_source: str
    normalization_policy: str
    ontology_policy: OntologyPolicy
    pack_ref: PackRef | None
    pack: LoadedOntologyPack | None
    type_adapter: str
    type_check_policy: str
    type_hierarchy_overrides: Mapping[str, tuple[str, ...]]
    allowed_predicates: frozenset[str] | None
    predicate_rules: Mapping[str, PackPredicateRule]
    severity_by_code: Mapping[str, str]
    active_overlay_predicates: frozenset[str]


def donor_profiles_root() -> Path:
    """Return the configured donor profiles directory."""

    return get_config().donor_profiles_dir()


def donor_ontology_packs_root() -> Path:
    """Return the configured donor ontology-packs directory."""

    return get_config().donor_ontology_packs_dir()


def clear_loader_caches() -> None:
    """Clear loader caches for tests and local iteration."""

    _load_pack_cached.cache_clear()
    _load_profile_cached.cache_clear()


def load_ontology_pack(
    pack_id: str,
    pack_version: str,
    *,
    packs_root: Path | None = None,
) -> LoadedOntologyPack:
    """Load one donor ontology pack from disk.

    This is the first real donor import surface for `onto-canon6`. It validates
    the small runtime subset the successor needs today: predicate ids, pack
    predicate rules, and type hierarchy parents.
    """

    if not _PACK_ID_RE.match(pack_id):
        raise OntologyPackLoadError(f"invalid pack_id: {pack_id!r}")
    if not _PACK_VERSION_RE.match(pack_version):
        raise OntologyPackLoadError(f"invalid pack_version: {pack_version!r}")
    root = (packs_root or donor_ontology_packs_root()).resolve()
    return _load_pack_cached(str(root), pack_id, pack_version)


def load_profile(
    profile_id: str,
    profile_version: str,
    *,
    profiles_root: Path | None = None,
    packs_root: Path | None = None,
) -> LoadedProfile:
    """Load one donor profile and merge any pack-derived vocabulary views."""

    normalized_profile_id = _required_token(profile_id, "profile_id", error_cls=ProfileLoadError)
    normalized_profile_version = _required_token(
        profile_version,
        "profile_version",
        error_cls=ProfileLoadError,
    )
    profile_root = (profiles_root or donor_profiles_root()).resolve()
    pack_root = (packs_root or donor_ontology_packs_root()).resolve()
    return _load_profile_cached(
        str(profile_root),
        str(pack_root),
        normalized_profile_id,
        normalized_profile_version,
    )


def load_effective_profile(
    profile_id: str,
    profile_version: str,
    *,
    profiles_root: Path | None = None,
    packs_root: Path | None = None,
    overlay_root: Path | None = None,
) -> LoadedProfile:
    """Load one donor profile plus any currently applied local overlay additions.

    Base donor profile loading remains cached. Overlay additions are loaded from
    disk on each call so explicit writeback becomes visible without cache
    invalidation magic.
    """

    base_profile = load_profile(
        profile_id,
        profile_version,
        profiles_root=profiles_root,
        packs_root=packs_root,
    )
    overlay_target = base_profile.ontology_policy.overlay_target
    if overlay_target is None:
        return base_profile

    overlay_additions = load_overlay_predicate_additions(
        overlay_target,
        overlay_root_path=overlay_root,
    )
    overlay_predicates = frozenset(addition.predicate_id for addition in overlay_additions)
    if not overlay_predicates:
        return base_profile

    effective_allowed_predicates = frozenset(
        set(base_profile.allowed_predicates or frozenset()) | set(overlay_predicates)
    )
    return LoadedProfile(
        profile_id=base_profile.profile_id,
        profile_version=base_profile.profile_version,
        name=base_profile.name,
        ontology_version=base_profile.ontology_version,
        rule_version=base_profile.rule_version,
        ontology_source=base_profile.ontology_source,
        normalization_policy=base_profile.normalization_policy,
        ontology_policy=base_profile.ontology_policy,
        pack_ref=base_profile.pack_ref,
        pack=base_profile.pack,
        type_adapter=base_profile.type_adapter,
        type_check_policy=base_profile.type_check_policy,
        type_hierarchy_overrides=base_profile.type_hierarchy_overrides,
        allowed_predicates=effective_allowed_predicates,
        predicate_rules=base_profile.predicate_rules,
        severity_by_code=base_profile.severity_by_code,
        active_overlay_predicates=overlay_predicates,
    )


@lru_cache(maxsize=32)
def _load_pack_cached(root: str, pack_id: str, pack_version: str) -> LoadedOntologyPack:
    pack_dir = Path(root) / pack_id / pack_version
    manifest_path = pack_dir / "manifest.yaml"
    if not manifest_path.exists():
        raise OntologyPackLoadError(f"ontology pack manifest missing: {manifest_path}")

    manifest = _load_yaml_object(manifest_path, error_cls=OntologyPackLoadError)
    pack_block = _required_object(manifest.get("pack"), "pack", error_cls=OntologyPackLoadError)
    content_block = _required_object(
        manifest.get("content"),
        "content",
        error_cls=OntologyPackLoadError,
    )

    manifest_pack_id = _required_token(
        pack_block.get("id"),
        "pack.id",
        error_cls=OntologyPackLoadError,
    )
    manifest_pack_version = _required_token(
        pack_block.get("version"),
        "pack.version",
        error_cls=OntologyPackLoadError,
    )
    if manifest_pack_id != pack_id:
        raise OntologyPackLoadError(
            f"{manifest_path}: pack.id={manifest_pack_id!r} does not match {pack_id!r}"
        )
    if manifest_pack_version != pack_version:
        raise OntologyPackLoadError(
            f"{manifest_path}: pack.version={manifest_pack_version!r} does not match {pack_version!r}"
        )

    content_paths = _resolve_content_paths(pack_dir, content_block)
    role_runtime_names = _load_role_runtime_names(content_paths["role_types"])
    predicate_ids = _load_predicate_ids(content_paths["predicate_types"])
    type_parents = _load_type_parents(content_paths["hierarchy_edges"])
    predicate_rules = _load_predicate_rules(
        predicate_role_edges_path=content_paths["predicate_role_edges"],
        constraints_path=content_paths["constraints"],
        role_runtime_names=role_runtime_names,
        predicate_ids=predicate_ids,
    )

    return LoadedOntologyPack(
        pack_ref=PackRef(pack_id=pack_id, pack_version=pack_version),
        name=_required_token(pack_block.get("name"), "pack.name", error_cls=OntologyPackLoadError),
        description=_required_token(
            pack_block.get("description"),
            "pack.description",
            error_cls=OntologyPackLoadError,
        ),
        path=pack_dir,
        predicate_ids=predicate_ids,
        predicate_rules=predicate_rules,
        type_parents=type_parents,
    )


@lru_cache(maxsize=64)
def _load_profile_cached(
    profiles_root: str,
    packs_root: str,
    profile_id: str,
    profile_version: str,
) -> LoadedProfile:
    profile_dir = Path(profiles_root) / profile_id / profile_version
    manifest_path = profile_dir / "manifest.yaml"
    severity_path = profile_dir / "severity.yaml"
    if not manifest_path.exists():
        raise ProfileLoadError(f"profile manifest missing: {manifest_path}")
    if not severity_path.exists():
        raise ProfileLoadError(f"profile severity mapping missing: {severity_path}")

    manifest = _load_yaml_object(manifest_path, error_cls=ProfileLoadError)
    severity_doc = _load_yaml_object(severity_path, error_cls=ProfileLoadError)
    _validate_profile_identity(manifest, profile_id, profile_version, manifest_path)
    _validate_profile_identity(severity_doc, profile_id, profile_version, severity_path)

    profile_block = _required_object(
        manifest.get("profile"),
        "profile",
        error_cls=ProfileLoadError,
    )
    ontology_block = _optional_object(
        manifest.get("ontology"),
        "ontology",
        error_cls=ProfileLoadError,
    )
    validation_block = _optional_object(
        manifest.get("validation"),
        "validation",
        error_cls=ProfileLoadError,
    )
    severity_block = _optional_object(
        severity_doc.get("severity"),
        "severity",
        error_cls=ProfileLoadError,
    )

    ontology_source = _required_token(
        ontology_block.get("source"),
        "ontology.source",
        error_cls=ProfileLoadError,
    ).lower()
    normalization_policy = _required_token(
        ontology_block.get("normalization_policy"),
        "ontology.normalization_policy",
        error_cls=ProfileLoadError,
    ).lower()

    proposal_policy = _parse_proposal_policy(ontology_block.get("proposal_policy"))
    mode = _parse_ontology_mode(ontology_block.get("mode"))

    pack_ref = _parse_pack_ref(ontology_block)
    pack = (
        load_ontology_pack(
            pack_ref.pack_id,
            pack_ref.pack_version,
            packs_root=Path(packs_root),
        )
        if pack_ref is not None
        else None
    )

    type_adapter = _required_token(
        validation_block.get("type_adapter", "null"),
        "validation.type_adapter",
        error_cls=ProfileLoadError,
    ).lower()
    if type_adapter not in _TYPE_ADAPTER_VALUES:
        raise ProfileLoadError(
            f"validation.type_adapter must be one of {sorted(_TYPE_ADAPTER_VALUES)}"
        )

    type_check_policy = _required_token(
        validation_block.get("type_check_policy", "skip"),
        "validation.type_check_policy",
        error_cls=ProfileLoadError,
    ).lower()
    if type_check_policy not in _TYPE_CHECK_POLICY_VALUES:
        raise ProfileLoadError(
            "validation.type_check_policy must be one of "
            f"{sorted(_TYPE_CHECK_POLICY_VALUES)}"
        )

    explicit_allowed_predicates = _parse_allowed_predicates(validation_block.get("allowed_predicates"))
    explicit_predicate_rules = _parse_predicate_rules(validation_block.get("predicate_rules"))
    type_hierarchy_overrides = _parse_type_hierarchy_overrides(
        validation_block.get("type_hierarchy_overrides")
    )
    severity_by_code = _parse_severity_map(severity_block)

    effective_allowed_predicates = explicit_allowed_predicates
    effective_predicate_rules = explicit_predicate_rules
    if pack is not None:
        effective_allowed_predicates = explicit_allowed_predicates or pack.predicate_ids
        merged = dict(pack.predicate_rules)
        merged.update(explicit_predicate_rules)
        effective_predicate_rules = merged

    overlay_target = _derive_overlay_target(pack_ref=pack_ref, proposal_policy=proposal_policy)
    ontology_policy = OntologyPolicy(
        mode=mode,
        proposal_policy=proposal_policy,
        overlay_target=overlay_target,
    )
    _validate_loaded_profile_consistency(
        profile_id=profile_id,
        ontology_policy=ontology_policy,
        effective_allowed_predicates=effective_allowed_predicates,
        severity_by_code=severity_by_code,
        type_adapter=type_adapter,
        pack_ref=pack_ref,
    )

    return LoadedProfile(
        profile_id=profile_id,
        profile_version=profile_version,
        name=_required_token(profile_block.get("name"), "profile.name", error_cls=ProfileLoadError),
        ontology_version=_required_token(
            profile_block.get("ontology_version"),
            "profile.ontology_version",
            error_cls=ProfileLoadError,
        ),
        rule_version=_required_token(
            profile_block.get("rule_version"),
            "profile.rule_version",
            error_cls=ProfileLoadError,
        ),
        ontology_source=ontology_source,
        normalization_policy=normalization_policy,
        ontology_policy=ontology_policy,
        pack_ref=pack_ref,
        pack=pack,
        type_adapter=type_adapter,
        type_check_policy=type_check_policy,
        type_hierarchy_overrides=type_hierarchy_overrides,
        allowed_predicates=effective_allowed_predicates,
        predicate_rules=effective_predicate_rules,
        severity_by_code=severity_by_code,
        active_overlay_predicates=frozenset(),
    )


def _load_yaml_object(path: Path, *, error_cls: type[ValueError]) -> dict[str, object]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        raise error_cls(f"YAML file must decode to an object: {path}")
    return cast(dict[str, object], raw)


def _validate_profile_identity(
    doc: Mapping[str, object],
    profile_id: str,
    profile_version: str,
    source: Path,
) -> None:
    profile = _required_object(doc.get("profile"), "profile", error_cls=ProfileLoadError)
    doc_id = _required_token(profile.get("id"), "profile.id", error_cls=ProfileLoadError)
    doc_version = _required_token(
        profile.get("version"),
        "profile.version",
        error_cls=ProfileLoadError,
    )
    if doc_id != profile_id:
        raise ProfileLoadError(f"{source}: profile.id={doc_id!r} does not match {profile_id!r}")
    if doc_version != profile_version:
        raise ProfileLoadError(
            f"{source}: profile.version={doc_version!r} does not match {profile_version!r}"
        )


def _parse_pack_ref(raw: Mapping[str, object]) -> PackRef | None:
    pack_id_raw = raw.get("pack_id")
    pack_version_raw = raw.get("pack_version")
    if pack_id_raw is None and pack_version_raw is None:
        return None
    return PackRef(
        pack_id=_required_token(pack_id_raw, "ontology.pack_id", error_cls=ProfileLoadError),
        pack_version=_required_token(
            pack_version_raw,
            "ontology.pack_version",
            error_cls=ProfileLoadError,
        ),
    )


def _derive_overlay_target(
    *,
    pack_ref: PackRef | None,
    proposal_policy: ProposalPolicy,
) -> PackRef | None:
    """Return the local overlay target implied by the donor profile shape."""

    if pack_ref is None or proposal_policy != "allow":
        return None
    return overlay_pack_ref_for(pack_ref)


def _parse_allowed_predicates(raw: object) -> frozenset[str] | None:
    if raw in (None, []):
        return None
    if not isinstance(raw, list):
        raise ProfileLoadError("validation.allowed_predicates must be a list")
    parsed = [
        _required_token(value, "validation.allowed_predicates[]", error_cls=ProfileLoadError)
        for value in raw
    ]
    return frozenset(parsed)


def _parse_predicate_rules(raw: object) -> Mapping[str, PackPredicateRule]:
    if raw in (None, {}):
        return {}
    if not isinstance(raw, dict):
        raise ProfileLoadError("validation.predicate_rules must be an object")

    parsed: dict[str, PackPredicateRule] = {}
    for predicate_raw, rule_raw in raw.items():
        predicate = _required_token(
            predicate_raw,
            "validation.predicate_rules key",
            error_cls=ProfileLoadError,
        )
        rule_obj = _required_object(
            rule_raw,
            f"validation.predicate_rules[{predicate}]",
            error_cls=ProfileLoadError,
        )
        parsed[predicate] = PackPredicateRule(
            allowed_roles=_parse_str_tuple(rule_obj.get("allowed_roles"), "allowed_roles"),
            required_roles=_parse_str_tuple(rule_obj.get("required_roles"), "required_roles"),
            role_cardinality=_parse_role_cardinality_map(rule_obj.get("role_cardinality"), predicate),
            role_filler_types=_parse_string_map(rule_obj.get("role_filler_types"), predicate, "role_filler_types"),
            role_value_kinds=_parse_string_map(
                rule_obj.get("role_value_kinds"),
                predicate,
                "role_value_kinds",
            ),
        )
    return parsed


def _parse_severity_map(raw: Mapping[str, object]) -> Mapping[str, str]:
    parsed: dict[str, str] = {}
    for code_raw, severity_raw in raw.items():
        code = _required_token(code_raw, "severity key", error_cls=ProfileLoadError)
        severity = _required_token(severity_raw, f"severity[{code}]", error_cls=ProfileLoadError).lower()
        if severity not in _SEVERITY_VALUES:
            raise ProfileLoadError(f"severity[{code}] must be one of {sorted(_SEVERITY_VALUES)}")
        parsed[code] = severity
    return parsed


def _parse_type_hierarchy_overrides(raw: object) -> Mapping[str, tuple[str, ...]]:
    if raw in (None, {}):
        return {}
    if not isinstance(raw, dict):
        raise ProfileLoadError("validation.type_hierarchy_overrides must be an object")

    parsed: dict[str, tuple[str, ...]] = {}
    for child_raw, parents_raw in raw.items():
        child = _required_token(
            child_raw,
            "validation.type_hierarchy_overrides key",
            error_cls=ProfileLoadError,
        )
        if not isinstance(parents_raw, list) or not parents_raw:
            raise ProfileLoadError(
                f"validation.type_hierarchy_overrides[{child}] must be a non-empty list"
            )
        parents: list[str] = []
        seen: set[str] = set()
        for parent_raw in parents_raw:
            parent = _required_token(
                parent_raw,
                f"validation.type_hierarchy_overrides[{child}][]",
                error_cls=ProfileLoadError,
            )
            if parent in seen:
                continue
            seen.add(parent)
            parents.append(parent)
        parsed[child] = tuple(parents)
    return parsed


def _parse_str_tuple(raw: object, field_name: str) -> tuple[str, ...]:
    if raw in (None, []):
        return ()
    if not isinstance(raw, list):
        raise ProfileLoadError(f"{field_name} must be a list")
    parsed = [
        _required_token(value, field_name, error_cls=ProfileLoadError)
        for value in raw
    ]
    return tuple(sorted(parsed))


def _parse_role_cardinality_map(
    raw: object,
    predicate: str,
) -> Mapping[str, PackRoleCardinality]:
    if raw in (None, {}):
        return {}
    if not isinstance(raw, dict):
        raise ProfileLoadError(f"{predicate}.role_cardinality must be an object")

    parsed: dict[str, PackRoleCardinality] = {}
    for role_raw, cardinality_raw in raw.items():
        role = _required_token(
            role_raw,
            f"{predicate}.role_cardinality key",
            error_cls=ProfileLoadError,
        )
        cardinality_obj = _required_object(
            cardinality_raw,
            f"{predicate}.role_cardinality[{role}]",
            error_cls=ProfileLoadError,
        )
        min_raw = cardinality_obj.get("min", 0)
        max_raw = cardinality_obj.get("max")
        min_count = _coerce_nonnegative_int(min_raw, f"{predicate}.{role}.min", error_cls=ProfileLoadError)
        max_count = _coerce_optional_nonnegative_int(
            max_raw,
            f"{predicate}.{role}.max",
            error_cls=ProfileLoadError,
        )
        if max_count is not None and min_count > max_count:
            raise ProfileLoadError(f"{predicate}.{role}: min cannot be greater than max")
        parsed[role] = PackRoleCardinality(min_count=min_count, max_count=max_count)
    return parsed


def _parse_string_map(raw: object, predicate: str, field_name: str) -> Mapping[str, str]:
    if raw in (None, {}):
        return {}
    if not isinstance(raw, dict):
        raise ProfileLoadError(f"{predicate}.{field_name} must be an object")
    parsed: dict[str, str] = {}
    for key_raw, value_raw in raw.items():
        key = _required_token(
            key_raw,
            f"{predicate}.{field_name} key",
            error_cls=ProfileLoadError,
        )
        parsed[key] = _required_token(
            value_raw,
            f"{predicate}.{field_name}[{key}]",
            error_cls=ProfileLoadError,
        )
    return parsed


def _validate_loaded_profile_consistency(
    *,
    profile_id: str,
    ontology_policy: OntologyPolicy,
    effective_allowed_predicates: frozenset[str] | None,
    severity_by_code: Mapping[str, str],
    type_adapter: str,
    pack_ref: PackRef | None,
) -> None:
    unknown_predicate_severity = severity_by_code.get("oc:profile_unknown_predicate")
    if ontology_policy.mode == "open" and ontology_policy.proposal_policy != "reject":
        raise ProfileLoadError("open mode requires proposal_policy='reject'")
    if ontology_policy.mode in {"closed", "mixed"} and effective_allowed_predicates is None:
        raise ProfileLoadError(
            f"{profile_id}: {ontology_policy.mode} mode requires a non-empty predicate allowlist"
        )
    if ontology_policy.mode == "closed" and unknown_predicate_severity != "hard":
        raise ProfileLoadError("closed mode requires oc:profile_unknown_predicate severity=hard")
    if ontology_policy.mode == "mixed" and unknown_predicate_severity != "soft":
        raise ProfileLoadError("mixed mode requires oc:profile_unknown_predicate severity=soft")
    if type_adapter == "ontology_pack" and pack_ref is None:
        raise ProfileLoadError("validation.type_adapter=ontology_pack requires a referenced pack")


def _resolve_content_paths(
    pack_dir: Path,
    content_block: Mapping[str, object],
) -> dict[str, Path]:
    resolved: dict[str, Path] = {}
    for key in _REQUIRED_CONTENT_KEYS:
        value = _required_token(
            content_block.get(key),
            f"content.{key}",
            error_cls=OntologyPackLoadError,
        )
        path = (pack_dir / value).resolve()
        if not path.exists():
            raise OntologyPackLoadError(f"ontology pack content missing: {path}")
        resolved[key] = path
    return resolved


def _load_jsonl(path: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        normalized = line.strip()
        if not normalized:
            continue
        try:
            parsed = json.loads(normalized)
        except json.JSONDecodeError as err:
            raise OntologyPackLoadError(f"{path}:{line_number}: invalid JSONL: {err.msg}") from err
        if not isinstance(parsed, dict):
            raise OntologyPackLoadError(f"{path}:{line_number}: JSONL rows must be objects")
        rows.append(cast(dict[str, object], parsed))
    return rows


def _load_role_runtime_names(path: Path) -> Mapping[str, str]:
    runtime_names: dict[str, str] = {}
    for row in _load_jsonl(path):
        role_id = _required_token(row.get("role_id"), "role_types[].role_id", error_cls=OntologyPackLoadError)
        runtime_name = _required_token(
            row.get("runtime_name"),
            f"role_types[{role_id}].runtime_name",
            error_cls=OntologyPackLoadError,
        )
        runtime_names[role_id] = runtime_name
    return runtime_names


def _load_predicate_ids(path: Path) -> frozenset[str]:
    predicate_ids: set[str] = set()
    for row in _load_jsonl(path):
        predicate_id = _required_token(
            row.get("predicate_id"),
            "predicate_types[].predicate_id",
            error_cls=OntologyPackLoadError,
        )
        status = str(row.get("status", "active")).strip().lower()
        if status == "active":
            predicate_ids.add(predicate_id)
    return frozenset(sorted(predicate_ids))


def _load_type_parents(path: Path) -> Mapping[str, tuple[str, ...]]:
    parents: dict[str, list[str]] = {}
    for row in _load_jsonl(path):
        edge_type = str(row.get("edge_type", "")).strip()
        if edge_type != "subtype_of":
            continue
        child_id = _required_token(
            row.get("child_id"),
            "hierarchy_edges[].child_id",
            error_cls=OntologyPackLoadError,
        )
        parent_id = _required_token(
            row.get("parent_id"),
            "hierarchy_edges[].parent_id",
            error_cls=OntologyPackLoadError,
        )
        parent_list = parents.setdefault(child_id, [])
        if parent_id not in parent_list:
            parent_list.append(parent_id)
    return {child: tuple(parent_list) for child, parent_list in parents.items()}


def _load_predicate_rules(
    *,
    predicate_role_edges_path: Path,
    constraints_path: Path,
    role_runtime_names: Mapping[str, str],
    predicate_ids: frozenset[str],
) -> Mapping[str, PackPredicateRule]:
    builders: dict[str, PackPredicateRuleBuilder] = {}
    for row in _load_jsonl(predicate_role_edges_path):
        predicate_id = _required_token(
            row.get("predicate_id"),
            "predicate_role_edges[].predicate_id",
            error_cls=OntologyPackLoadError,
        )
        if predicate_id not in predicate_ids:
            raise OntologyPackLoadError(
                f"predicate_role_edges references undeclared predicate_id: {predicate_id}"
            )
        role_id = _required_token(
            row.get("role_id"),
            "predicate_role_edges[].role_id",
            error_cls=OntologyPackLoadError,
        )
        runtime_name = role_runtime_names.get(role_id)
        if runtime_name is None:
            raise OntologyPackLoadError(
                f"predicate_role_edges references unknown role_id: {role_id}"
            )
        builder = builders.setdefault(
            predicate_id,
            PackPredicateRuleBuilder(
                allowed_roles=[],
                required_roles=[],
                role_cardinality={},
                role_filler_types={},
                role_value_kinds={},
            ),
        )
        required = _coerce_bool(
            row.get("required", False),
            "predicate_role_edges[].required",
            error_cls=OntologyPackLoadError,
        )
        min_count = _coerce_nonnegative_int(
            row.get("min_count", 0),
            "predicate_role_edges[].min_count",
            error_cls=OntologyPackLoadError,
        )
        max_count = _coerce_optional_nonnegative_int(
            row.get("max_count"),
            "predicate_role_edges[].max_count",
            error_cls=OntologyPackLoadError,
        )
        builder.add_role(
            runtime_name=runtime_name,
            required=required,
            min_count=min_count,
            max_count=max_count,
        )

    for row in _load_jsonl(constraints_path):
        constraint_type = _required_token(
            row.get("constraint_type"),
            "constraints[].constraint_type",
            error_cls=OntologyPackLoadError,
        )
        predicate_id = _required_token(
            row.get("predicate_id"),
            "constraints[].predicate_id",
            error_cls=OntologyPackLoadError,
        )
        role_id = _required_token(
            row.get("role_id"),
            "constraints[].role_id",
            error_cls=OntologyPackLoadError,
        )
        constraint_builder = builders.get(predicate_id)
        if constraint_builder is None:
            raise OntologyPackLoadError(
                f"constraints references predicate without role edges: {predicate_id}"
            )
        runtime_name = role_runtime_names.get(role_id)
        if runtime_name is None:
            raise OntologyPackLoadError(f"constraints references unknown role_id: {role_id}")
        if constraint_type == "role_expected_entity_type":
            expected_type = _required_token(
                row.get("expected_type"),
                "constraints[].expected_type",
                error_cls=OntologyPackLoadError,
            )
            constraint_builder.role_filler_types[runtime_name] = expected_type
        elif constraint_type == "role_expected_value_kind":
            expected_value_kind = _required_token(
                row.get("expected_value_kind"),
                "constraints[].expected_value_kind",
                error_cls=OntologyPackLoadError,
            )
            constraint_builder.role_value_kinds[runtime_name] = expected_value_kind

    return {predicate_id: builders[predicate_id].build() for predicate_id in sorted(builders)}


def _required_object(
    raw: object,
    field_name: str,
    *,
    error_cls: type[ValueError],
) -> Mapping[str, object]:
    if not isinstance(raw, dict):
        raise error_cls(f"{field_name} must be an object")
    return cast(Mapping[str, object], raw)


def _optional_object(
    raw: object,
    field_name: str,
    *,
    error_cls: type[ValueError],
) -> dict[str, object]:
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        raise error_cls(f"{field_name} must be an object")
    return cast(dict[str, object], raw)


def _required_token(
    raw: object,
    field_name: str,
    *,
    error_cls: type[ValueError],
) -> str:
    if not isinstance(raw, str) or not raw.strip():
        raise error_cls(f"{field_name} must be a non-empty string")
    return raw.strip()


def _parse_ontology_mode(raw: object) -> OntologyMode:
    mode = _required_token(raw, "ontology.mode", error_cls=ProfileLoadError).lower()
    if mode not in {"open", "closed", "mixed"}:
        raise ProfileLoadError("ontology.mode must be one of ['closed', 'mixed', 'open']")
    return cast(OntologyMode, mode)


def _parse_proposal_policy(raw: object) -> ProposalPolicy:
    proposal_policy = _required_token(
        raw,
        "ontology.proposal_policy",
        error_cls=ProfileLoadError,
    ).lower()
    if proposal_policy not in {"reject", "allow"}:
        raise ProfileLoadError("ontology.proposal_policy must be one of ['allow', 'reject']")
    return cast(ProposalPolicy, proposal_policy)


def _coerce_bool(raw: object, field_name: str, *, error_cls: type[ValueError]) -> bool:
    if isinstance(raw, bool):
        return raw
    raise error_cls(f"{field_name} must be a boolean")


def _coerce_nonnegative_int(
    raw: object,
    field_name: str,
    *,
    error_cls: type[ValueError],
) -> int:
    if isinstance(raw, bool) or not isinstance(raw, int) or raw < 0:
        raise error_cls(f"{field_name} must be a non-negative integer")
    return raw


def _coerce_optional_nonnegative_int(
    raw: object,
    field_name: str,
    *,
    error_cls: type[ValueError],
) -> int | None:
    if raw is None:
        return None
    return _coerce_nonnegative_int(raw, field_name, error_cls=error_cls)


__all__ = [
    "LoadedOntologyPack",
    "LoadedProfile",
    "OntologyPackLoadError",
    "PackPredicateRule",
    "PackRoleCardinality",
    "ProfileLoadError",
    "clear_loader_caches",
    "donor_ontology_packs_root",
    "donor_profiles_root",
    "load_ontology_pack",
    "load_profile",
]
