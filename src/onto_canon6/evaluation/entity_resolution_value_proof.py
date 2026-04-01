"""Decision-grade value proof for cross-document entity resolution.

This module turns the synthetic-corpus scale harness into an honest evaluation
surface. It does not guess from aggregate identity counts. Instead it:

1. collects promoted entity observations with the names and source docs that
   actually appeared in promoted assertions;
2. matches those observations to the checked-in ground-truth registry using the
   same normalization logic as the auto-resolution subsystem;
3. computes pairwise clustering metrics over matched observations while keeping
   unmatched or ambiguous observations explicit; and
4. scores a fixed question fixture so the value-proof surface can report both
   cluster quality and question-oriented usefulness.
"""

from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path
import sqlite3
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from ..core.auto_resolution import _entity_types_compatible, _normalize_name
from ..core.identity_service import IdentityService

MatchStatus = Literal["matched", "ambiguous", "unmatched"]
QuestionKind = Literal["same_entity", "canonical_entity"]


class GroundTruthEntity(BaseModel):
    """One canonical entity in the official synthetic value-proof corpus."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    canonical_name: str = Field(min_length=1)
    type: str = Field(min_length=1)
    name_variants: tuple[str, ...] = ()
    appears_in_docs: tuple[str, ...] = ()
    note: str | None = None


class GroundTruthMergeExpectation(BaseModel):
    """One positive merge expectation from the fixture."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    entity: str = Field(min_length=1)
    description: str = Field(min_length=1)


class GroundTruthNonMergeExpectation(BaseModel):
    """One negative merge expectation from the fixture."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    entities: tuple[str, str]
    description: str = Field(min_length=1)


class EntityResolutionGroundTruth(BaseModel):
    """Top-level ground-truth fixture for the synthetic value-proof corpus."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    description: str = Field(min_length=1)
    entities: dict[str, GroundTruthEntity]
    expected_merges: tuple[GroundTruthMergeExpectation, ...] = ()
    expected_non_merges: tuple[GroundTruthNonMergeExpectation, ...] = ()


class ValueProofQuestion(BaseModel):
    """One fixed question used to score entity-resolution usefulness."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    question_id: str = Field(min_length=1)
    kind: QuestionKind
    prompt: str = Field(min_length=1)
    mention: str = Field(min_length=1)
    other_mention: str | None = None
    expected_answer: bool | None = None
    expected_ground_truth_entity_id: str | None = None

    def model_post_init(self, __context: object) -> None:
        """Fail loudly if the fixture mixes the two question contracts."""

        if self.kind == "same_entity":
            if self.other_mention is None or self.expected_answer is None:
                raise ValueError(
                    "same_entity questions require other_mention and expected_answer"
                )
            if self.expected_ground_truth_entity_id is not None:
                raise ValueError(
                    "same_entity questions must not set expected_ground_truth_entity_id"
                )
        if self.kind == "canonical_entity":
            if self.expected_ground_truth_entity_id is None:
                raise ValueError(
                    "canonical_entity questions require expected_ground_truth_entity_id"
                )
            if self.other_mention is not None or self.expected_answer is not None:
                raise ValueError(
                    "canonical_entity questions must not set other_mention or expected_answer"
                )


class ValueProofQuestionFixture(BaseModel):
    """Top-level fixed question fixture for the official corpus."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    description: str = Field(min_length=1)
    questions: tuple[ValueProofQuestion, ...] = ()


class EntityObservation(BaseModel):
    """One promoted entity observed in the durable graph."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    entity_id: str = Field(min_length=1)
    entity_type: str | None = None
    first_candidate_id: str = Field(min_length=1)
    predicted_cluster_id: str = Field(min_length=1)
    observed_names: tuple[str, ...] = ()
    source_refs: tuple[str, ...] = ()
    matched_ground_truth_entity_id: str | None = None
    match_status: MatchStatus
    match_reason: str = Field(min_length=1)
    candidate_ground_truth_entity_ids: tuple[str, ...] = ()


class EntityPairRecord(BaseModel):
    """One concrete pair used to explain a false merge or false split."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    left_entity_id: str = Field(min_length=1)
    right_entity_id: str = Field(min_length=1)
    left_ground_truth_entity_id: str = Field(min_length=1)
    right_ground_truth_entity_id: str = Field(min_length=1)
    left_names: tuple[str, ...] = ()
    right_names: tuple[str, ...] = ()
    left_source_refs: tuple[str, ...] = ()
    right_source_refs: tuple[str, ...] = ()
    predicted_same_cluster: bool
    reason: str = Field(min_length=1)


class PairwiseMetrics(BaseModel):
    """Pairwise clustering metrics over matched observations only."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    matched_observation_count: int = Field(ge=0)
    unmatched_observation_count: int = Field(ge=0)
    ambiguous_observation_count: int = Field(ge=0)
    predicted_positive_pairs: int = Field(ge=0)
    gold_positive_pairs: int = Field(ge=0)
    true_positive_pairs: int = Field(ge=0)
    false_positive_pairs: int = Field(ge=0)
    false_negative_pairs: int = Field(ge=0)
    precision: float = Field(ge=0.0, le=1.0)
    recall: float = Field(ge=0.0, le=1.0)
    false_merge_pairs: tuple[EntityPairRecord, ...] = ()
    false_split_pairs: tuple[EntityPairRecord, ...] = ()
    unmatched_observation_ids: tuple[str, ...] = ()
    ambiguous_observation_ids: tuple[str, ...] = ()


class QuestionScoreRecord(BaseModel):
    """One scored fixed question over the evaluated observation set."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    question_id: str = Field(min_length=1)
    kind: QuestionKind
    prompt: str = Field(min_length=1)
    answered: bool
    correct: bool
    predicted_answer: bool | None = None
    predicted_ground_truth_entity_id: str | None = None
    note: str = Field(min_length=1)


class QuestionScoreSummary(BaseModel):
    """Aggregate summary for the fixed question fixture."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    total_questions: int = Field(ge=0)
    answered_questions: int = Field(ge=0)
    correct_questions: int = Field(ge=0)
    answer_rate: float = Field(ge=0.0, le=1.0)
    accuracy_over_all_questions: float = Field(ge=0.0, le=1.0)
    accuracy_over_answered_questions: float = Field(ge=0.0, le=1.0)


class GroundTruthSummary(BaseModel):
    """Compact summary of the checked-in corpus registry."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    entity_count: int = Field(ge=0)
    expected_merge_count: int = Field(ge=0)
    expected_non_merge_count: int = Field(ge=0)


class EntityResolutionValueProofReport(BaseModel):
    """Typed report for one decision-grade entity-resolution run."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    generated_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    state_ref: str = Field(min_length=1)
    strategy: str = Field(min_length=1)
    corpus_description: str = Field(min_length=1)
    scoring_rules: tuple[str, ...] = ()
    ground_truth_summary: GroundTruthSummary
    observations: tuple[EntityObservation, ...] = ()
    pairwise_metrics: PairwiseMetrics
    question_summary: QuestionScoreSummary
    question_scores: tuple[QuestionScoreRecord, ...] = ()


def load_entity_resolution_ground_truth(
    path: Path | str,
) -> EntityResolutionGroundTruth:
    """Load the official ground-truth registry from disk."""

    fixture_path = Path(path)
    return EntityResolutionGroundTruth.model_validate_json(
        fixture_path.read_text(encoding="utf-8")
    )


def load_value_proof_questions(path: Path | str) -> ValueProofQuestionFixture:
    """Load the fixed question fixture for the official value-proof corpus."""

    fixture_path = Path(path)
    return ValueProofQuestionFixture.model_validate_json(
        fixture_path.read_text(encoding="utf-8")
    )


def build_entity_resolution_value_proof_report(
    *,
    db_path: Path,
    ground_truth: EntityResolutionGroundTruth,
    questions: ValueProofQuestionFixture,
    strategy: str,
) -> EntityResolutionValueProofReport:
    """Build a typed value-proof report from one promoted-graph database."""

    observations = collect_entity_observations(db_path=db_path)
    return build_value_proof_report_from_observations(
        state_ref=str(db_path),
        observations=observations,
        ground_truth=ground_truth,
        questions=questions,
        strategy=strategy,
    )


def build_value_proof_report_from_observations(
    *,
    state_ref: str,
    observations: tuple[EntityObservation, ...],
    ground_truth: EntityResolutionGroundTruth,
    questions: ValueProofQuestionFixture,
    strategy: str,
) -> EntityResolutionValueProofReport:
    """Build a typed value-proof report from already-collected observations."""

    matched_observations = match_observations_to_ground_truth(
        observations=observations,
        ground_truth=ground_truth,
    )
    pairwise_metrics = compute_pairwise_metrics(matched_observations)
    question_scores = score_value_proof_questions(
        observations=matched_observations,
        questions=questions,
    )
    return EntityResolutionValueProofReport(
        state_ref=state_ref,
        strategy=strategy,
        corpus_description=ground_truth.description,
        scoring_rules=(
            "Ground-truth matching uses auto-resolution name normalization plus source-doc overlap as a tiebreaker.",
            "Pairwise precision/recall are computed only over observations that match the ground-truth registry uniquely.",
            "Observations with no unique ground-truth match remain explicit as unmatched or ambiguous and are not silently discarded.",
            "Questions are scored against the matched observation set; unanswered questions lower answer rate and overall accuracy.",
        ),
        ground_truth_summary=GroundTruthSummary(
            entity_count=len(ground_truth.entities),
            expected_merge_count=len(ground_truth.expected_merges),
            expected_non_merge_count=len(ground_truth.expected_non_merges),
        ),
        observations=matched_observations,
        pairwise_metrics=pairwise_metrics,
        question_summary=_summarize_question_scores(question_scores),
        question_scores=question_scores,
    )


def collect_entity_observations(*, db_path: Path) -> tuple[EntityObservation, ...]:
    """Collect promoted entity observations with names, docs, and cluster ids."""

    identity_service = IdentityService(db_path=db_path)
    entity_to_cluster_id = {
        membership.entity_id: bundle.identity.identity_id
        for bundle in identity_service.list_identities()
        for membership in bundle.memberships
    }

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        entity_rows = conn.execute(
            """
            SELECT entity_id, entity_type, first_candidate_id
            FROM promoted_graph_entities
            ORDER BY entity_id
            """
        ).fetchall()
        assertion_rows = conn.execute(
            """
            SELECT
                pa.normalized_body_json,
                ca.source_ref
            FROM promoted_graph_assertions pa
            JOIN candidate_assertions ca
              ON ca.candidate_id = pa.source_candidate_id
            ORDER BY pa.promoted_at, pa.assertion_id
            """
        ).fetchall()

    names_by_entity: dict[str, set[str]] = {
        str(row["entity_id"]): set() for row in entity_rows
    }
    docs_by_entity: dict[str, set[str]] = {
        str(row["entity_id"]): set() for row in entity_rows
    }

    for row in assertion_rows:
        normalized_body = json.loads(str(row["normalized_body_json"]))
        source_ref = str(row["source_ref"])
        roles = normalized_body.get("roles")
        if not isinstance(roles, dict):
            continue
        for fillers in roles.values():
            if not isinstance(fillers, list):
                continue
            for filler in fillers:
                if not isinstance(filler, dict):
                    continue
                if filler.get("kind") != "entity":
                    continue
                entity_id = filler.get("entity_id")
                name = filler.get("name")
                if isinstance(entity_id, str) and entity_id in names_by_entity:
                    docs_by_entity[entity_id].add(source_ref)
                    if isinstance(name, str) and name.strip():
                        names_by_entity[entity_id].add(name.strip())

    observations: list[EntityObservation] = []
    for row in entity_rows:
        entity_id = str(row["entity_id"])
        observations.append(
            EntityObservation(
                entity_id=entity_id,
                entity_type=str(row["entity_type"]) if row["entity_type"] is not None else None,
                first_candidate_id=str(row["first_candidate_id"]),
                predicted_cluster_id=entity_to_cluster_id.get(entity_id, entity_id),
                observed_names=tuple(sorted(names_by_entity[entity_id])),
                source_refs=tuple(sorted(docs_by_entity[entity_id])),
                matched_ground_truth_entity_id=None,
                match_status="unmatched",
                match_reason="ground-truth matching not yet run",
                candidate_ground_truth_entity_ids=(),
            )
        )
    return tuple(observations)


def match_observations_to_ground_truth(
    observations: tuple[EntityObservation, ...],
    *,
    ground_truth: EntityResolutionGroundTruth,
) -> tuple[EntityObservation, ...]:
    """Attach one explicit ground-truth match status to each observation."""

    name_index = _build_ground_truth_name_index(ground_truth)
    matched: list[EntityObservation] = []
    for observation in observations:
        candidate_ids = _candidate_ground_truth_entity_ids(
            observation=observation,
            name_index=name_index,
            ground_truth=ground_truth,
        )
        if not candidate_ids:
            matched.append(
                observation.model_copy(
                    update={
                        "match_status": "unmatched",
                        "match_reason": "no ground-truth variant match",
                        "candidate_ground_truth_entity_ids": (),
                    }
                )
            )
            continue

        type_filtered_ids = tuple(
            candidate_id
            for candidate_id in candidate_ids
            if _entity_type_matches(
                observation,
                ground_truth_entity=ground_truth.entities[candidate_id],
            )
        )
        if not type_filtered_ids:
            matched.append(
                observation.model_copy(
                    update={
                        "match_status": "unmatched",
                        "match_reason": "name matched only ground-truth entities with incompatible types",
                        "candidate_ground_truth_entity_ids": candidate_ids,
                    }
                )
            )
            continue

        if len(type_filtered_ids) == 1:
            matched.append(
                observation.model_copy(
                    update={
                        "matched_ground_truth_entity_id": type_filtered_ids[0],
                        "match_status": "matched",
                        "match_reason": "unique normalized name + type match",
                        "candidate_ground_truth_entity_ids": type_filtered_ids,
                    }
                )
            )
            continue

        overlap_scores = {
            candidate_id: len(
                set(observation.source_refs) & set(ground_truth.entities[candidate_id].appears_in_docs)
            )
            for candidate_id in type_filtered_ids
        }
        best_score = max(overlap_scores.values())
        best_ids = tuple(
            candidate_id
            for candidate_id, score in overlap_scores.items()
            if score == best_score
        )
        if best_score > 0 and len(best_ids) == 1:
            matched.append(
                observation.model_copy(
                    update={
                        "matched_ground_truth_entity_id": best_ids[0],
                        "match_status": "matched",
                        "match_reason": "resolved by source-doc overlap after multi-entity name collision",
                        "candidate_ground_truth_entity_ids": type_filtered_ids,
                    }
                )
            )
            continue

        matched.append(
            observation.model_copy(
                update={
                    "match_status": "ambiguous",
                    "match_reason": "multiple ground-truth candidates remain after type and doc-overlap checks",
                    "candidate_ground_truth_entity_ids": type_filtered_ids,
                }
            )
        )
    return tuple(matched)


def compute_pairwise_metrics(
    observations: tuple[EntityObservation, ...],
) -> PairwiseMetrics:
    """Compute pairwise clustering metrics over uniquely matched observations."""

    matched = tuple(
        observation
        for observation in observations
        if observation.match_status == "matched"
        and observation.matched_ground_truth_entity_id is not None
    )
    predicted_pairs: dict[tuple[str, str], EntityPairRecord] = {}
    gold_pairs: dict[tuple[str, str], EntityPairRecord] = {}

    for index, left in enumerate(matched):
        for right in matched[index + 1:]:
            left_entity_id, right_entity_id = sorted((left.entity_id, right.entity_id))
            pair_key = (left_entity_id, right_entity_id)
            assert left.matched_ground_truth_entity_id is not None
            assert right.matched_ground_truth_entity_id is not None
            predicted_same = left.predicted_cluster_id == right.predicted_cluster_id
            gold_same = (
                left.matched_ground_truth_entity_id
                == right.matched_ground_truth_entity_id
            )
            pair = EntityPairRecord(
                left_entity_id=left.entity_id,
                right_entity_id=right.entity_id,
                left_ground_truth_entity_id=left.matched_ground_truth_entity_id,
                right_ground_truth_entity_id=right.matched_ground_truth_entity_id,
                left_names=left.observed_names,
                right_names=right.observed_names,
                left_source_refs=left.source_refs,
                right_source_refs=right.source_refs,
                predicted_same_cluster=predicted_same,
                reason=_pair_reason(
                    predicted_same=predicted_same,
                    gold_same=gold_same,
                ),
            )
            if predicted_same:
                predicted_pairs[pair_key] = pair
            if gold_same:
                gold_pairs[pair_key] = pair

    true_positive_keys = set(predicted_pairs) & set(gold_pairs)
    false_positive_keys = set(predicted_pairs) - set(gold_pairs)
    false_negative_keys = set(gold_pairs) - set(predicted_pairs)
    predicted_positive_pairs = len(predicted_pairs)
    gold_positive_pairs = len(gold_pairs)
    true_positive_pairs = len(true_positive_keys)
    false_positive_pairs = len(false_positive_keys)
    false_negative_pairs = len(false_negative_keys)
    precision = (
        true_positive_pairs / predicted_positive_pairs
        if predicted_positive_pairs > 0
        else 1.0
    )
    recall = (
        true_positive_pairs / gold_positive_pairs
        if gold_positive_pairs > 0
        else 1.0
    )

    return PairwiseMetrics(
        matched_observation_count=len(matched),
        unmatched_observation_count=sum(
            1 for observation in observations if observation.match_status == "unmatched"
        ),
        ambiguous_observation_count=sum(
            1 for observation in observations if observation.match_status == "ambiguous"
        ),
        predicted_positive_pairs=predicted_positive_pairs,
        gold_positive_pairs=gold_positive_pairs,
        true_positive_pairs=true_positive_pairs,
        false_positive_pairs=false_positive_pairs,
        false_negative_pairs=false_negative_pairs,
        precision=precision,
        recall=recall,
        false_merge_pairs=tuple(predicted_pairs[key] for key in sorted(false_positive_keys)),
        false_split_pairs=tuple(gold_pairs[key] for key in sorted(false_negative_keys)),
        unmatched_observation_ids=tuple(
            observation.entity_id
            for observation in observations
            if observation.match_status == "unmatched"
        ),
        ambiguous_observation_ids=tuple(
            observation.entity_id
            for observation in observations
            if observation.match_status == "ambiguous"
        ),
    )


def score_value_proof_questions(
    *,
    observations: tuple[EntityObservation, ...],
    questions: ValueProofQuestionFixture,
) -> tuple[QuestionScoreRecord, ...]:
    """Score the fixed question fixture over the matched observation set."""

    mention_index = _build_observation_mention_index(observations)
    results: list[QuestionScoreRecord] = []
    for question in questions.questions:
        if question.kind == "same_entity":
            assert question.other_mention is not None
            assert question.expected_answer is not None
            left_cluster_ids = _cluster_ids_for_mention(mention_index, question.mention)
            right_cluster_ids = _cluster_ids_for_mention(mention_index, question.other_mention)
            if len(left_cluster_ids) != 1 or len(right_cluster_ids) != 1:
                results.append(
                    QuestionScoreRecord(
                        question_id=question.question_id,
                        kind=question.kind,
                        prompt=question.prompt,
                        answered=False,
                        correct=False,
                        predicted_answer=None,
                        note="could not resolve one or both mentions to a unique predicted cluster",
                    )
                )
                continue
            predicted_answer = left_cluster_ids == right_cluster_ids
            results.append(
                QuestionScoreRecord(
                    question_id=question.question_id,
                    kind=question.kind,
                    prompt=question.prompt,
                    answered=True,
                    correct=predicted_answer == question.expected_answer,
                    predicted_answer=predicted_answer,
                    note="scored from unique predicted cluster ids for both mentions",
                )
            )
            continue

        assert question.expected_ground_truth_entity_id is not None
        predicted_ground_truth_ids = _ground_truth_ids_for_mention(
            mention_index,
            question.mention,
        )
        if len(predicted_ground_truth_ids) != 1:
            results.append(
                QuestionScoreRecord(
                    question_id=question.question_id,
                    kind=question.kind,
                    prompt=question.prompt,
                    answered=False,
                    correct=False,
                    predicted_ground_truth_entity_id=None,
                    note="could not resolve mention to a unique matched ground-truth entity",
                )
            )
            continue
        predicted_ground_truth_entity_id = next(iter(predicted_ground_truth_ids))
        results.append(
            QuestionScoreRecord(
                question_id=question.question_id,
                kind=question.kind,
                prompt=question.prompt,
                answered=True,
                correct=(
                    predicted_ground_truth_entity_id
                    == question.expected_ground_truth_entity_id
                ),
                predicted_ground_truth_entity_id=predicted_ground_truth_entity_id,
                note="scored from uniquely matched promoted observation(s)",
            )
        )
    return tuple(results)


def _build_ground_truth_name_index(
    ground_truth: EntityResolutionGroundTruth,
) -> dict[str, tuple[str, ...]]:
    """Build normalized-name to ground-truth entity ids index."""

    index: dict[str, set[str]] = {}
    for entity_id, entity in ground_truth.entities.items():
        variants = {entity.canonical_name, *entity.name_variants}
        for variant in variants:
            normalized = _normalize_name(variant)
            index.setdefault(normalized, set()).add(entity_id)
    return {
        normalized: tuple(sorted(entity_ids))
        for normalized, entity_ids in sorted(index.items())
    }


def _candidate_ground_truth_entity_ids(
    *,
    observation: EntityObservation,
    name_index: dict[str, tuple[str, ...]],
    ground_truth: EntityResolutionGroundTruth,
) -> tuple[str, ...]:
    """Return candidate ground-truth entity ids based on normalized names."""

    candidate_ids: set[str] = set()
    for name in observation.observed_names:
        normalized = _normalize_name(name)
        candidate_ids.update(name_index.get(normalized, ()))
    if candidate_ids:
        return tuple(sorted(candidate_ids))

    # Fall back to ground-truth doc overlap only if the observation has no names.
    if not observation.source_refs:
        return ()
    for entity_id, entity in ground_truth.entities.items():
        if set(observation.source_refs) & set(entity.appears_in_docs):
            candidate_ids.add(entity_id)
    return tuple(sorted(candidate_ids))


def _entity_type_matches(
    observation: EntityObservation,
    *,
    ground_truth_entity: GroundTruthEntity,
) -> bool:
    """Return whether the observed entity type is compatible with ground truth."""

    observed_type = observation.entity_type
    if observed_type is None:
        return True
    representative_name = observation.observed_names[0] if observation.observed_names else None
    return _entity_types_compatible(
        observed_type,
        ground_truth_entity.type,
        left_name=representative_name,
        right_name=ground_truth_entity.canonical_name,
    )


def _pair_reason(*, predicted_same: bool, gold_same: bool) -> str:
    """Return a stable human-readable explanation for one pair state."""

    if predicted_same and gold_same:
        return "true positive pair"
    if predicted_same and not gold_same:
        return "false merge pair"
    if not predicted_same and gold_same:
        return "false split pair"
    return "true negative pair"


def _build_observation_mention_index(
    observations: tuple[EntityObservation, ...],
) -> dict[str, tuple[EntityObservation, ...]]:
    """Index observations by normalized observed mention."""

    index: dict[str, list[EntityObservation]] = {}
    for observation in observations:
        for name in observation.observed_names:
            normalized = _normalize_name(name)
            index.setdefault(normalized, []).append(observation)
    return {
        mention: tuple(observation_list)
        for mention, observation_list in sorted(index.items())
    }


def _cluster_ids_for_mention(
    mention_index: dict[str, tuple[EntityObservation, ...]],
    mention: str,
) -> set[str]:
    """Return the predicted cluster ids for one mention."""

    normalized = _normalize_name(mention)
    return {
        observation.predicted_cluster_id
        for observation in mention_index.get(normalized, ())
        if observation.match_status == "matched"
        and observation.matched_ground_truth_entity_id is not None
    }


def _ground_truth_ids_for_mention(
    mention_index: dict[str, tuple[EntityObservation, ...]],
    mention: str,
) -> set[str]:
    """Return uniquely matched ground-truth ids for one mention."""

    normalized = _normalize_name(mention)
    return {
        observation.matched_ground_truth_entity_id
        for observation in mention_index.get(normalized, ())
        if observation.match_status == "matched"
        and observation.matched_ground_truth_entity_id is not None
    }


def _summarize_question_scores(
    question_scores: tuple[QuestionScoreRecord, ...],
) -> QuestionScoreSummary:
    """Aggregate question score totals into one stable summary."""

    total_questions = len(question_scores)
    answered_questions = sum(1 for record in question_scores if record.answered)
    correct_questions = sum(1 for record in question_scores if record.correct)
    answer_rate = answered_questions / total_questions if total_questions else 0.0
    accuracy_over_all_questions = (
        correct_questions / total_questions if total_questions else 0.0
    )
    accuracy_over_answered_questions = (
        correct_questions / answered_questions if answered_questions else 0.0
    )
    return QuestionScoreSummary(
        total_questions=total_questions,
        answered_questions=answered_questions,
        correct_questions=correct_questions,
        answer_rate=answer_rate,
        accuracy_over_all_questions=accuracy_over_all_questions,
        accuracy_over_answered_questions=accuracy_over_answered_questions,
    )
