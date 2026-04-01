"""Deterministic tests for the entity-resolution value-proof evaluator."""

from __future__ import annotations

from onto_canon6.evaluation.entity_resolution_value_proof import (
    EntityObservation,
    EntityResolutionGroundTruth,
    ValueProofQuestionFixture,
    compute_pairwise_metrics,
    match_observations_to_ground_truth,
    score_value_proof_questions,
)


def _ground_truth() -> EntityResolutionGroundTruth:
    """Build a compact ground-truth registry for deterministic tests."""

    return EntityResolutionGroundTruth.model_validate(
        {
            "description": "test fixture",
            "entities": {
                "E001": {
                    "canonical_name": "General John Smith",
                    "type": "oc:person",
                    "name_variants": ["Gen. Smith", "Gen. J. Smith"],
                    "appears_in_docs": ["doc_01", "doc_02"],
                },
                "E011": {
                    "canonical_name": "James Smith",
                    "type": "oc:person",
                    "name_variants": ["J. Smith"],
                    "appears_in_docs": ["doc_15", "doc_20"],
                },
                "E012": {
                    "canonical_name": "Washington D.C.",
                    "type": "oc:location",
                    "name_variants": ["Washington"],
                    "appears_in_docs": ["doc_08"],
                },
                "E013": {
                    "canonical_name": "George Washington University",
                    "type": "oc:educational_institution",
                    "name_variants": ["Washington", "GWU"],
                    "appears_in_docs": ["doc_11"],
                },
                "E006": {
                    "canonical_name": "Central Intelligence Agency",
                    "type": "oc:government_organization",
                    "name_variants": ["CIA", "Central Intelligence Agency", "the Agency"],
                    "appears_in_docs": ["doc_04", "doc_07", "doc_11"],
                },
            },
            "expected_merges": [],
            "expected_non_merges": [],
        }
    )


def test_match_observations_uses_type_guard_for_ambiguous_name() -> None:
    """Type compatibility should resolve normalized-name collisions honestly."""

    observations = (
        EntityObservation(
            entity_id="ent_01",
            entity_type="oc:educational_institution",
            first_candidate_id="cand_01",
            predicted_cluster_id="cluster_a",
            observed_names=("Washington",),
            source_refs=("doc_11",),
            matched_ground_truth_entity_id=None,
            match_status="unmatched",
            match_reason="not run",
            candidate_ground_truth_entity_ids=(),
        ),
    )

    matched = match_observations_to_ground_truth(
        observations,
        ground_truth=_ground_truth(),
    )

    assert matched[0].match_status == "matched"
    assert matched[0].matched_ground_truth_entity_id == "E013"
    assert matched[0].match_reason == "unique normalized name + type match"


def test_match_observations_accepts_person_like_rank_mentions() -> None:
    """Rank-typed titled names should still match person ground truth."""

    observations = (
        EntityObservation(
            entity_id="ent_rank",
            entity_type="oc:military_rank",
            first_candidate_id="cand_rank",
            predicted_cluster_id="cluster_rank",
            observed_names=("Gen. Smith",),
            source_refs=("doc_01",),
            matched_ground_truth_entity_id=None,
            match_status="unmatched",
            match_reason="not run",
            candidate_ground_truth_entity_ids=(),
        ),
    )

    matched = match_observations_to_ground_truth(
        observations,
        ground_truth=_ground_truth(),
    )

    assert matched[0].match_status == "matched"
    assert matched[0].matched_ground_truth_entity_id == "E001"


def test_match_observations_accepts_university_family_mentions() -> None:
    """University-typed mentions should match institution ground truth."""

    observations = (
        EntityObservation(
            entity_id="ent_university",
            entity_type="oc:university",
            first_candidate_id="cand_university",
            predicted_cluster_id="cluster_university",
            observed_names=("George Washington University",),
            source_refs=("doc_11",),
            matched_ground_truth_entity_id=None,
            match_status="unmatched",
            match_reason="not run",
            candidate_ground_truth_entity_ids=(),
        ),
    )

    matched = match_observations_to_ground_truth(
        observations,
        ground_truth=_ground_truth(),
    )

    assert matched[0].match_status == "matched"
    assert matched[0].matched_ground_truth_entity_id == "E013"


def test_match_observations_accepts_government_agency_family_mentions() -> None:
    """Government-agency mentions should match government-organization ground truth."""

    observations = (
        EntityObservation(
            entity_id="ent_agency",
            entity_type="oc:government_agency",
            first_candidate_id="cand_agency",
            predicted_cluster_id="cluster_agency",
            observed_names=("the Agency",),
            source_refs=("doc_11",),
            matched_ground_truth_entity_id=None,
            match_status="unmatched",
            match_reason="not run",
            candidate_ground_truth_entity_ids=(),
        ),
    )

    matched = match_observations_to_ground_truth(
        observations,
        ground_truth=_ground_truth(),
    )

    assert matched[0].match_status == "matched"
    assert matched[0].matched_ground_truth_entity_id == "E006"


def test_match_observations_marks_ambiguous_when_type_and_docs_do_not_break_tie() -> None:
    """Ambiguous Smith-like collisions must remain explicit, not guessed."""

    observations = (
        EntityObservation(
            entity_id="ent_02",
            entity_type="oc:person",
            first_candidate_id="cand_02",
            predicted_cluster_id="cluster_b",
            observed_names=("J. Smith",),
            source_refs=("doc_99",),
            matched_ground_truth_entity_id=None,
            match_status="unmatched",
            match_reason="not run",
            candidate_ground_truth_entity_ids=(),
        ),
    )

    matched = match_observations_to_ground_truth(
        observations,
        ground_truth=_ground_truth(),
    )

    assert matched[0].match_status == "ambiguous"
    assert matched[0].matched_ground_truth_entity_id is None
    assert matched[0].candidate_ground_truth_entity_ids == ("E001", "E011")


def test_match_observations_does_not_use_doc_overlap_when_named_surface_misses() -> None:
    """Named observations must not fall back to doc overlap when no variant matches."""

    observations = (
        EntityObservation(
            entity_id="ent_overlap_only",
            entity_type="oc:organization",
            first_candidate_id="cand_overlap_only",
            predicted_cluster_id="cluster_overlap_only",
            observed_names=("special operations forces",),
            source_refs=("doc_04",),
            matched_ground_truth_entity_id=None,
            match_status="unmatched",
            match_reason="not run",
            candidate_ground_truth_entity_ids=(),
        ),
    )

    matched = match_observations_to_ground_truth(
        observations,
        ground_truth=_ground_truth(),
    )

    assert matched[0].match_status == "unmatched"
    assert matched[0].matched_ground_truth_entity_id is None
    assert matched[0].candidate_ground_truth_entity_ids == ()
    assert matched[0].match_reason == "no ground-truth variant match"


def test_compute_pairwise_metrics_reports_false_merges_and_false_splits() -> None:
    """Pairwise metrics should preserve concrete evidence for both error types."""

    observations = (
        EntityObservation(
            entity_id="ent_a",
            entity_type="oc:person",
            first_candidate_id="cand_a",
            predicted_cluster_id="cluster_tp",
            observed_names=("Gen. Smith",),
            source_refs=("doc_01",),
            matched_ground_truth_entity_id="E001",
            match_status="matched",
            match_reason="matched",
            candidate_ground_truth_entity_ids=("E001",),
        ),
        EntityObservation(
            entity_id="ent_b",
            entity_type="oc:person",
            first_candidate_id="cand_b",
            predicted_cluster_id="cluster_tp",
            observed_names=("General John Smith",),
            source_refs=("doc_02",),
            matched_ground_truth_entity_id="E001",
            match_status="matched",
            match_reason="matched",
            candidate_ground_truth_entity_ids=("E001",),
        ),
        EntityObservation(
            entity_id="ent_c",
            entity_type="oc:educational_institution",
            first_candidate_id="cand_c",
            predicted_cluster_id="cluster_fp",
            observed_names=("GWU",),
            source_refs=("doc_11",),
            matched_ground_truth_entity_id="E013",
            match_status="matched",
            match_reason="matched",
            candidate_ground_truth_entity_ids=("E013",),
        ),
        EntityObservation(
            entity_id="ent_d",
            entity_type="oc:location",
            first_candidate_id="cand_d",
            predicted_cluster_id="cluster_fp",
            observed_names=("Washington",),
            source_refs=("doc_08",),
            matched_ground_truth_entity_id="E012",
            match_status="matched",
            match_reason="matched",
            candidate_ground_truth_entity_ids=("E012",),
        ),
        EntityObservation(
            entity_id="ent_e",
            entity_type="oc:person",
            first_candidate_id="cand_e",
            predicted_cluster_id="cluster_split_left",
            observed_names=("James Smith",),
            source_refs=("doc_15",),
            matched_ground_truth_entity_id="E011",
            match_status="matched",
            match_reason="matched",
            candidate_ground_truth_entity_ids=("E011",),
        ),
        EntityObservation(
            entity_id="ent_f",
            entity_type="oc:person",
            first_candidate_id="cand_f",
            predicted_cluster_id="cluster_split_right",
            observed_names=("J. Smith",),
            source_refs=("doc_20",),
            matched_ground_truth_entity_id="E011",
            match_status="matched",
            match_reason="matched",
            candidate_ground_truth_entity_ids=("E011",),
        ),
        EntityObservation(
            entity_id="ent_g",
            entity_type="oc:person",
            first_candidate_id="cand_g",
            predicted_cluster_id="cluster_unmatched",
            observed_names=("Unknown Person",),
            source_refs=("doc_99",),
            matched_ground_truth_entity_id=None,
            match_status="unmatched",
            match_reason="no match",
            candidate_ground_truth_entity_ids=(),
        ),
    )

    metrics = compute_pairwise_metrics(observations)

    assert metrics.matched_observation_count == 6
    assert metrics.unmatched_observation_count == 1
    assert metrics.predicted_positive_pairs == 2
    assert metrics.gold_positive_pairs == 2
    assert metrics.true_positive_pairs == 1
    assert metrics.false_positive_pairs == 1
    assert metrics.false_negative_pairs == 1
    assert metrics.precision == 0.5
    assert metrics.recall == 0.5
    assert len(metrics.false_merge_pairs) == 1
    assert len(metrics.false_split_pairs) == 1
    assert metrics.false_merge_pairs[0].left_ground_truth_entity_id != metrics.false_merge_pairs[0].right_ground_truth_entity_id
    assert metrics.false_split_pairs[0].left_ground_truth_entity_id == metrics.false_split_pairs[0].right_ground_truth_entity_id


def test_score_value_proof_questions_tracks_answerability_and_correctness() -> None:
    """Question scoring should distinguish unanswered from incorrect cases."""

    questions = ValueProofQuestionFixture.model_validate(
        {
            "description": "questions",
            "questions": [
                {
                    "question_id": "q1",
                    "kind": "same_entity",
                    "prompt": "same?",
                    "mention": "Gen. Smith",
                    "other_mention": "General John Smith",
                    "expected_answer": True,
                },
                {
                    "question_id": "q2",
                    "kind": "canonical_entity",
                    "prompt": "canonical?",
                    "mention": "GWU",
                    "expected_ground_truth_entity_id": "E013",
                },
                {
                    "question_id": "q3",
                    "kind": "canonical_entity",
                    "prompt": "ambiguous?",
                    "mention": "J. Smith",
                    "expected_ground_truth_entity_id": "E011",
                },
            ],
        }
    )
    observations = (
        EntityObservation(
            entity_id="ent_a",
            entity_type="oc:person",
            first_candidate_id="cand_a",
            predicted_cluster_id="cluster_1",
            observed_names=("Gen. Smith", "General John Smith"),
            source_refs=("doc_01",),
            matched_ground_truth_entity_id="E001",
            match_status="matched",
            match_reason="matched",
            candidate_ground_truth_entity_ids=("E001",),
        ),
        EntityObservation(
            entity_id="ent_b",
            entity_type="oc:university",
            first_candidate_id="cand_b",
            predicted_cluster_id="cluster_2",
            observed_names=("George Washington University",),
            source_refs=("doc_11",),
            matched_ground_truth_entity_id="E013",
            match_status="matched",
            match_reason="matched",
            candidate_ground_truth_entity_ids=("E013",),
        ),
        EntityObservation(
            entity_id="ent_c",
            entity_type="oc:person",
            first_candidate_id="cand_c",
            predicted_cluster_id="cluster_3",
            observed_names=("J. Smith",),
            source_refs=("doc_15",),
            matched_ground_truth_entity_id=None,
            match_status="ambiguous",
            match_reason="ambiguous",
            candidate_ground_truth_entity_ids=("E001", "E011"),
        ),
    )

    scores = score_value_proof_questions(
        observations=observations,
        questions=questions,
    )

    assert scores[0].answered is True
    assert scores[0].correct is True
    assert scores[0].predicted_answer is True

    assert scores[1].answered is True
    assert scores[1].correct is True
    assert scores[1].predicted_ground_truth_entity_id == "E013"

    assert scores[2].answered is False
    assert scores[2].correct is False


def test_score_value_proof_questions_ignores_unmatched_duplicate_mentions() -> None:
    """Mention lookup should follow the matched-observation scoring contract."""

    questions = ValueProofQuestionFixture.model_validate(
        {
            "description": "questions",
            "questions": [
                {
                    "question_id": "q1",
                    "kind": "same_entity",
                    "prompt": "same?",
                    "mention": "Gen. Smith",
                    "other_mention": "General John Smith",
                    "expected_answer": True,
                },
                {
                    "question_id": "q2",
                    "kind": "same_entity",
                    "prompt": "different?",
                    "mention": "General John Smith",
                    "other_mention": "James Smith",
                    "expected_answer": False,
                },
            ],
        }
    )
    observations = (
        EntityObservation(
            entity_id="ent_person",
            entity_type="oc:person",
            first_candidate_id="cand_person",
            predicted_cluster_id="cluster_e001",
            observed_names=("Gen. Smith", "General John Smith"),
            source_refs=("doc_01", "doc_02"),
            matched_ground_truth_entity_id="E001",
            match_status="matched",
            match_reason="matched",
            candidate_ground_truth_entity_ids=("E001",),
        ),
        EntityObservation(
            entity_id="ent_rank_noise",
            entity_type="oc:military_rank",
            first_candidate_id="cand_rank",
            predicted_cluster_id="cluster_rank_noise",
            observed_names=("Gen. Smith",),
            source_refs=("doc_01",),
            matched_ground_truth_entity_id=None,
            match_status="unmatched",
            match_reason="incompatible type",
            candidate_ground_truth_entity_ids=("E001",),
        ),
        EntityObservation(
            entity_id="ent_james",
            entity_type="oc:person",
            first_candidate_id="cand_james",
            predicted_cluster_id="cluster_e011",
            observed_names=("James Smith",),
            source_refs=("doc_15",),
            matched_ground_truth_entity_id="E011",
            match_status="matched",
            match_reason="matched",
            candidate_ground_truth_entity_ids=("E011",),
        ),
        EntityObservation(
            entity_id="ent_john_noise",
            entity_type=None,
            first_candidate_id="cand_john_noise",
            predicted_cluster_id="cluster_noise",
            observed_names=("John Smith",),
            source_refs=("doc_05",),
            matched_ground_truth_entity_id=None,
            match_status="unmatched",
            match_reason="incompatible type",
            candidate_ground_truth_entity_ids=("E001",),
        ),
    )

    scores = score_value_proof_questions(
        observations=observations,
        questions=questions,
    )

    assert scores[0].answered is True
    assert scores[0].correct is True
    assert scores[0].predicted_answer is True
    assert scores[1].answered is True
    assert scores[1].correct is True
    assert scores[1].predicted_answer is False
