"""Validate one assertion payload against a loaded ontology profile.

This module is the first local validation slice in `onto-canon6`. It proves
that the successor can evaluate assertion payloads against real donor
pack/profile data without importing the old workflow runtime.

The scope is intentionally narrow:

- normalize simple legacy entity-filler shapes;
- enforce basic assertion structure;
- resolve unknown predicates through ontology policy;
- apply donor predicate rules for required roles, cardinality, role types, and
  value kinds.

It does not attempt persistence, review workflow orchestration, or overlay
writeback. Those remain separate concerns.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Literal, Mapping

from pydantic import BaseModel, ConfigDict, Field

from .contracts import ProposalRequest
from .loaders import LoadedProfile
from .policy import build_proposal_request, decide_unknown_item

FindingSeverity = Literal["hard", "soft"]


class ValidationFinding(BaseModel):
    """One validation result with stable machine-readable identity.

    Findings are returned with their resolved severity so downstream layers do
    not need to re-interpret profile severity maps.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    code: str = Field(min_length=1)
    message: str = Field(min_length=1)
    path: str = Field(min_length=1)
    severity: FindingSeverity


class ValidationOutcome(BaseModel):
    """Grouped validation output for one assertion payload.

    The first slice separates hard errors, soft violations, and generated
    proposal requests so notebook probes and tests can inspect each concern
    directly.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    hard_errors: tuple[ValidationFinding, ...] = ()
    soft_violations: tuple[ValidationFinding, ...] = ()
    proposal_requests: tuple[ProposalRequest, ...] = ()
    type_checks_total: int = Field(default=0, ge=0)
    type_checks_unknown: int = Field(default=0, ge=0)

    @property
    def has_hard_errors(self) -> bool:
        """Return `True` when validation found any hard errors."""

        return bool(self.hard_errors)

    @property
    def has_soft_violations(self) -> bool:
        """Return `True` when validation found any soft violations."""

        return bool(self.soft_violations)

    @property
    def has_proposal_requests(self) -> bool:
        """Return `True` when validation generated ontology proposals."""

        return bool(self.proposal_requests)

    @property
    def all_findings(self) -> tuple[ValidationFinding, ...]:
        """Return hard and soft findings in one deterministic tuple."""

        return self.hard_errors + self.soft_violations


@dataclass(frozen=True)
class _FindingDraft:
    """Stage one finding before severity resolution."""

    code: str
    message: str
    path: str
    default_severity: FindingSeverity


@dataclass(frozen=True)
class _TypeCheckResult:
    """Internal result for one role entity-type comparison."""

    ok: bool
    code: str | None
    message: str | None


def canonical_assertion_body(payload: Mapping[str, object]) -> dict[str, object]:
    """Return a normalized assertion body without persistence-only fields.

    The successor will likely add stable assertion identifiers later. The first
    slice strips known persistence fields so validation focuses on semantic
    payload content.
    """

    normalized = normalize_assertion_payload(payload)
    return {
        key: value
        for key, value in normalized.items()
        if key not in {"assertion_id", "confidence"}
    }


def normalize_assertion_payload(payload: Mapping[str, object]) -> dict[str, object]:
    """Normalize light legacy variants into the current filler structure.

    Today this only upgrades entity fillers that omit `kind` but already carry
    an `entity_id`. The function is intentionally conservative so the first
    slice does not hide malformed payloads behind broad rewrites.
    """

    normalized: dict[str, object] = dict(payload)
    roles_obj = payload.get("roles")
    if not isinstance(roles_obj, Mapping):
        return normalized

    normalized_roles: dict[str, object] = {}
    for role_name_raw, fillers_obj in roles_obj.items():
        role_name = str(role_name_raw)
        if not isinstance(fillers_obj, list):
            normalized_roles[role_name] = fillers_obj
            continue
        normalized_roles[role_name] = [_normalize_filler(filler) for filler in fillers_obj]
    normalized["roles"] = normalized_roles
    return normalized


def validate_assertion_payload(
    payload: Mapping[str, object],
    *,
    profile: LoadedProfile,
    severity_overrides: Mapping[str, FindingSeverity] | None = None,
) -> ValidationOutcome:
    """Validate one assertion payload against a loaded donor profile.

    This function is intentionally deterministic. It does not perform storage,
    proposal persistence, or review workflow actions. It only reports what the
    current ontology runtime can conclude locally from one payload and one
    loaded profile.
    """

    body = canonical_assertion_body(payload)
    drafts: list[_FindingDraft] = []
    proposals: list[ProposalRequest] = []
    type_checks_total = 0
    type_checks_unknown = 0

    predicate_obj = body.get("predicate")
    predicate: str
    if not isinstance(predicate_obj, str) or not predicate_obj.strip():
        predicate = ""
        drafts.append(
            _FindingDraft(
                code="oc:hard_missing_predicate",
                message="predicate must be a non-empty string",
                path="predicate",
                default_severity="hard",
            )
        )
    else:
        predicate = predicate_obj.strip()

    roles_obj = body.get("roles")
    roles: Mapping[str, object]
    if not isinstance(roles_obj, Mapping) or not roles_obj:
        roles = {}
        drafts.append(
            _FindingDraft(
                code="oc:hard_missing_roles",
                message="roles must be a non-empty object",
                path="roles",
                default_severity="hard",
            )
        )
    else:
        roles = {str(role_name): value for role_name, value in roles_obj.items()}
        for role_name, fillers in sorted(roles.items()):
            _validate_role_fillers(role_name=role_name, fillers=fillers, drafts=drafts)

    if predicate and roles:
        proposals.extend(
            _apply_profile_rules(
                predicate=predicate,
                roles=roles,
                profile=profile,
                drafts=drafts,
            )
        )
        type_checks_total, type_checks_unknown = _apply_type_and_value_checks(
            predicate=predicate,
            roles=roles,
            profile=profile,
            drafts=drafts,
        )

    return _resolve_outcome(
        drafts=drafts,
        proposals=proposals,
        profile=profile,
        severity_overrides=severity_overrides,
        type_checks_total=type_checks_total,
        type_checks_unknown=type_checks_unknown,
    )


def _normalize_filler(filler: object) -> object:
    if not isinstance(filler, Mapping):
        return filler
    if "kind" in filler or "entity_id" not in filler:
        return dict(filler)

    normalized: dict[str, object] = {
        "kind": "entity",
        "entity_id": filler.get("entity_id"),
    }
    for optional_key in ("name", "entity_type", "alias_ids"):
        if optional_key in filler:
            normalized[optional_key] = filler[optional_key]
    return normalized


def _validate_role_fillers(
    *,
    role_name: str,
    fillers: object,
    drafts: list[_FindingDraft],
) -> None:
    if not isinstance(fillers, list) or not fillers:
        drafts.append(
            _FindingDraft(
                code="oc:hard_missing_role_fillers",
                message="role must contain at least one filler",
                path=f"roles.{role_name}",
                default_severity="hard",
            )
        )
        return

    for index, filler in enumerate(fillers):
        base_path = f"roles.{role_name}[{index}]"
        if not isinstance(filler, Mapping):
            drafts.append(
                _FindingDraft(
                    code="oc:hard_invalid_role_filler",
                    message="role filler must be an object",
                    path=base_path,
                    default_severity="hard",
                )
            )
            continue

        filler_kind = filler.get("kind")
        if filler_kind == "value":
            continue
        entity_id = filler.get("entity_id")
        if not isinstance(entity_id, str) or not entity_id.strip():
            drafts.append(
                _FindingDraft(
                    code="oc:hard_missing_entity_id",
                    message="entity_id must be a non-empty string",
                    path=f"{base_path}.entity_id",
                    default_severity="hard",
                )
            )
            continue
        if not entity_id.startswith("ent:"):
            drafts.append(
                _FindingDraft(
                    code="oc:soft_noncanonical_entity_id",
                    message="entity_id should start with ent:",
                    path=f"{base_path}.entity_id",
                    default_severity="soft",
                )
            )


def _apply_profile_rules(
    *,
    predicate: str,
    roles: Mapping[str, object],
    profile: LoadedProfile,
    drafts: list[_FindingDraft],
) -> list[ProposalRequest]:
    proposals: list[ProposalRequest] = []
    allowed_predicates = profile.allowed_predicates
    if allowed_predicates is not None and predicate not in allowed_predicates:
        decision = decide_unknown_item(
            policy=profile.ontology_policy,
            kind="predicate",
            value=predicate,
        )
        if decision.action == "allow":
            return proposals
        if decision.action == "propose":
            message = (
                f"predicate '{predicate}' is not declared in profile {profile.profile_id}; "
                "mixed ontology mode routes it as a proposal"
            )
            proposals.append(build_proposal_request(decision))
        else:
            message = f"predicate '{predicate}' is not allowed by profile {profile.profile_id}"
        drafts.append(
            _FindingDraft(
                code="oc:profile_unknown_predicate",
                message=message,
                path="predicate",
                default_severity="hard",
            )
        )
        return proposals

    rule = profile.predicate_rules.get(predicate)
    if rule is None:
        return proposals

    role_names = set(roles.keys())
    if rule.allowed_roles:
        for role_name in sorted(role_names):
            if role_name not in rule.allowed_roles:
                drafts.append(
                    _FindingDraft(
                        code="oc:profile_disallowed_role",
                        message=f"role '{role_name}' is not allowed for predicate '{predicate}'",
                        path=f"roles.{role_name}",
                        default_severity="hard",
                    )
                )

    for required_role in rule.required_roles:
        fillers = roles.get(required_role)
        if not isinstance(fillers, list) or not fillers:
            drafts.append(
                _FindingDraft(
                    code="oc:profile_missing_required_role",
                    message=f"missing required role '{required_role}' for predicate '{predicate}'",
                    path=f"roles.{required_role}",
                    default_severity="hard",
                )
            )

    for role_name, cardinality in sorted(rule.role_cardinality.items()):
        fillers = roles.get(role_name)
        count = len(fillers) if isinstance(fillers, list) else 0
        too_few = count < cardinality.min_count
        too_many = cardinality.max_count is not None and count > cardinality.max_count
        if not too_few and not too_many:
            continue
        max_text = "*" if cardinality.max_count is None else str(cardinality.max_count)
        drafts.append(
            _FindingDraft(
                code="oc:profile_role_cardinality_violation",
                message=(
                    f"role '{role_name}' for predicate '{predicate}' has {count} fillers, "
                    f"expected {cardinality.min_count}..{max_text}"
                ),
                path=f"roles.{role_name}",
                default_severity="soft",
            )
        )

    return proposals


def _apply_type_and_value_checks(
    *,
    predicate: str,
    roles: Mapping[str, object],
    profile: LoadedProfile,
    drafts: list[_FindingDraft],
) -> tuple[int, int]:
    rule = profile.predicate_rules.get(predicate)
    if rule is None:
        return 0, 0

    type_checks_total = 0
    type_checks_unknown = 0

    for role_name, expected_type in sorted(rule.role_filler_types.items()):
        fillers = roles.get(role_name)
        if not isinstance(fillers, list):
            continue
        for index, filler in enumerate(fillers):
            base_path = f"roles.{role_name}[{index}]"
            if not isinstance(filler, Mapping):
                continue
            if filler.get("kind") == "value":
                continue

            entity_type = filler.get("entity_type")
            if not isinstance(entity_type, str) or not entity_type.strip():
                drafts.append(
                    _FindingDraft(
                        code="oc:profile_missing_entity_type",
                        message=(
                            f"role '{role_name}' for predicate '{predicate}' requires entity_type "
                            f"compatible with '{expected_type}'"
                        ),
                        path=f"{base_path}.entity_type",
                        default_severity="hard",
                    )
                )
                continue

            if profile.type_check_policy == "skip":
                continue

            type_checks_total += 1
            if profile.type_check_policy == "exact":
                if entity_type != expected_type:
                    drafts.append(
                        _FindingDraft(
                            code="oc:profile_role_type_violation",
                            message=(
                                f"role '{role_name}' for predicate '{predicate}' has type "
                                f"'{entity_type}', expected exact type '{expected_type}'"
                            ),
                            path=f"{base_path}.entity_type",
                            default_severity="hard",
                        )
                    )
                continue

            if profile.type_check_policy != "hierarchical":
                raise ValueError(
                    f"unsupported type_check_policy for validation: {profile.type_check_policy}"
                )
            type_result = _check_hierarchical_type(
                actual_type=entity_type,
                expected_type=expected_type,
                profile=profile,
            )
            if type_result.ok:
                continue
            if type_result.code == "oc:profile_role_type_unknown_relationship":
                type_checks_unknown += 1
            drafts.append(
                _FindingDraft(
                    code=type_result.code or "oc:profile_role_type_violation",
                    message=type_result.message
                    or (
                        f"role '{role_name}' for predicate '{predicate}' has type "
                        f"'{entity_type}', expected '{expected_type}'"
                    ),
                    path=f"{base_path}.entity_type",
                    default_severity=(
                        "soft"
                        if type_result.code == "oc:profile_role_type_unknown_relationship"
                        else "hard"
                    ),
                )
            )

    for role_name, expected_value_kind in sorted(rule.role_value_kinds.items()):
        fillers = roles.get(role_name)
        if not isinstance(fillers, list):
            continue
        for index, filler in enumerate(fillers):
            base_path = f"roles.{role_name}[{index}]"
            if not isinstance(filler, Mapping):
                continue
            if filler.get("kind") != "value":
                drafts.append(
                    _FindingDraft(
                        code="oc:profile_role_value_kind_violation",
                        message=(
                            f"role '{role_name}' for predicate '{predicate}' requires value kind "
                            f"'{expected_value_kind}'"
                        ),
                        path=f"{base_path}.kind",
                        default_severity="hard",
                    )
                )
                continue
            value_kind = filler.get("value_kind")
            if not isinstance(value_kind, str) or not value_kind.strip():
                drafts.append(
                    _FindingDraft(
                        code="oc:profile_missing_value_kind",
                        message=(
                            f"role '{role_name}' for predicate '{predicate}' requires value_kind "
                            f"'{expected_value_kind}'"
                        ),
                        path=f"{base_path}.value_kind",
                        default_severity="hard",
                    )
                )
                continue
            if value_kind != expected_value_kind:
                drafts.append(
                    _FindingDraft(
                        code="oc:profile_role_value_kind_violation",
                        message=(
                            f"role '{role_name}' for predicate '{predicate}' has value kind "
                            f"'{value_kind}', expected '{expected_value_kind}'"
                        ),
                        path=f"{base_path}.value_kind",
                        default_severity="hard",
                    )
                )

    return type_checks_total, type_checks_unknown


def _check_hierarchical_type(
    *,
    actual_type: str,
    expected_type: str,
    profile: LoadedProfile,
) -> _TypeCheckResult:
    if actual_type == expected_type:
        return _TypeCheckResult(ok=True, code=None, message=None)

    type_parents = _effective_type_parents(profile)
    if _is_same_or_subtype(
        actual_type=actual_type,
        expected_type=expected_type,
        type_parents=type_parents,
    ):
        return _TypeCheckResult(ok=True, code=None, message=None)

    known_types = _known_types(profile=profile, type_parents=type_parents)
    if actual_type not in known_types and expected_type not in known_types:
        return _TypeCheckResult(
            ok=False,
            code="oc:profile_role_type_unknown_relationship",
            message=(
                f"role filler type '{actual_type}' could not be related to expected type "
                f"'{expected_type}' with the currently loaded hierarchy"
            ),
        )

    return _TypeCheckResult(
        ok=False,
        code="oc:profile_role_type_violation",
        message=f"role filler type '{actual_type}' is not compatible with '{expected_type}'",
    )


def _effective_type_parents(profile: LoadedProfile) -> dict[str, tuple[str, ...]]:
    merged: dict[str, set[str]] = {}
    if profile.pack is not None and profile.type_adapter == "ontology_pack":
        for child, parents in profile.pack.type_parents.items():
            merged.setdefault(child, set()).update(parents)
    for child, parents in profile.type_hierarchy_overrides.items():
        merged.setdefault(child, set()).update(parents)
    return {
        child: tuple(sorted(parent_set))
        for child, parent_set in sorted(merged.items())
    }


def _known_types(
    *,
    profile: LoadedProfile,
    type_parents: Mapping[str, tuple[str, ...]],
) -> frozenset[str]:
    known: set[str] = set()
    for child, parents in type_parents.items():
        known.add(child)
        known.update(parents)
    for rule in profile.predicate_rules.values():
        known.update(rule.role_filler_types.values())
    return frozenset(known)


def _is_same_or_subtype(
    *,
    actual_type: str,
    expected_type: str,
    type_parents: Mapping[str, tuple[str, ...]],
) -> bool:
    if actual_type == expected_type:
        return True

    queue: deque[str] = deque([actual_type])
    seen: set[str] = {actual_type}
    while queue:
        current = queue.popleft()
        for parent in type_parents.get(current, ()):
            if parent == expected_type:
                return True
            if parent in seen:
                continue
            seen.add(parent)
            queue.append(parent)
    return False


def _resolve_outcome(
    *,
    drafts: list[_FindingDraft],
    proposals: list[ProposalRequest],
    profile: LoadedProfile,
    severity_overrides: Mapping[str, FindingSeverity] | None,
    type_checks_total: int,
    type_checks_unknown: int,
) -> ValidationOutcome:
    effective_overrides: dict[str, FindingSeverity] = {}
    for code, severity in profile.severity_by_code.items():
        if severity == "hard":
            effective_overrides[code] = "hard"
            continue
        if severity == "soft":
            effective_overrides[code] = "soft"
            continue
        raise ValueError(f"unsupported severity in loaded profile for {code}: {severity}")
    if severity_overrides is not None:
        effective_overrides.update(severity_overrides)

    hard_errors: list[ValidationFinding] = []
    soft_violations: list[ValidationFinding] = []
    for draft in _sorted_drafts(drafts):
        severity = effective_overrides.get(draft.code, draft.default_severity)
        if severity not in {"hard", "soft"}:
            raise ValueError(f"unsupported severity for {draft.code}: {severity}")
        finding = ValidationFinding(
            code=draft.code,
            message=draft.message,
            path=draft.path,
            severity=severity,
        )
        if severity == "hard":
            hard_errors.append(finding)
        else:
            soft_violations.append(finding)

    sorted_proposals = tuple(
        sorted(
            proposals,
            key=lambda proposal: (
                proposal.kind,
                proposal.value,
                proposal.reason,
                proposal.target_pack.pack_id if proposal.target_pack is not None else "",
                proposal.target_pack.pack_version if proposal.target_pack is not None else "",
            ),
        )
    )
    return ValidationOutcome(
        hard_errors=tuple(hard_errors),
        soft_violations=tuple(soft_violations),
        proposal_requests=sorted_proposals,
        type_checks_total=type_checks_total,
        type_checks_unknown=type_checks_unknown,
    )


def _sorted_drafts(drafts: list[_FindingDraft]) -> tuple[_FindingDraft, ...]:
    return tuple(sorted(drafts, key=lambda item: (item.code, item.path, item.message)))


__all__ = [
    "FindingSeverity",
    "ValidationFinding",
    "ValidationOutcome",
    "canonical_assertion_body",
    "normalize_assertion_payload",
    "validate_assertion_payload",
]
