"""Tests for the parameterized enforcement config (Plan #187 Step 5).

Verifies that:
- Default config preserves oc: behavior (oc:limit_capability fires, cc:foo does not)
- When enforcement config is overridden to cc:foo, the guard fires on cc:foo and
  not on oc:limit_capability
"""

from __future__ import annotations

import pytest

from onto_canon6.config import ExtractionEnforcementConfig, get_config


class TestExtractionEnforcementConfig:
    """Unit tests for ExtractionEnforcementConfig defaults and override behavior."""

    def test_default_limit_capability_predicate(self) -> None:
        """Default limit_capability_predicate must be oc:limit_capability."""
        cfg = ExtractionEnforcementConfig()
        assert cfg.limit_capability_predicate == "oc:limit_capability"

    def test_default_membership_predicate(self) -> None:
        """Default membership_predicate must be oc:belongs_to_organization."""
        cfg = ExtractionEnforcementConfig()
        assert cfg.membership_predicate == "oc:belongs_to_organization"

    def test_override_limit_capability_predicate(self) -> None:
        """Overriding limit_capability_predicate changes the value."""
        cfg = ExtractionEnforcementConfig(limit_capability_predicate="cc:limit_scope")
        assert cfg.limit_capability_predicate == "cc:limit_scope"
        assert cfg.membership_predicate == "oc:belongs_to_organization"  # unchanged

    def test_override_membership_predicate(self) -> None:
        """Overriding membership_predicate changes the value."""
        cfg = ExtractionEnforcementConfig(membership_predicate="cc:member_of")
        assert cfg.membership_predicate == "cc:member_of"
        assert cfg.limit_capability_predicate == "oc:limit_capability"  # unchanged

    def test_extra_fields_forbidden(self) -> None:
        """extra='forbid' must reject unknown fields."""
        with pytest.raises(Exception):
            ExtractionEnforcementConfig(nonexistent_field="x")  # type: ignore[call-arg]

    def test_live_config_has_enforcement_field(self) -> None:
        """The live config.yaml must load successfully with the enforcement field."""
        config = get_config()
        assert hasattr(config.extraction, "enforcement")
        assert config.extraction.enforcement.limit_capability_predicate == "oc:limit_capability"
        assert config.extraction.enforcement.membership_predicate == "oc:belongs_to_organization"

    def test_enforcement_guard_logic_default_oc(self) -> None:
        """Simulates: default config fires on oc:limit_capability, not on cc:train_model."""
        cfg = ExtractionEnforcementConfig()
        # Simulate what text_extraction.py does:
        test_predicate = "oc:limit_capability"
        fires = test_predicate == cfg.limit_capability_predicate
        assert fires, "Guard should fire for oc:limit_capability with default config"

        test_predicate_cc = "cc:train_model"
        fires_cc = test_predicate_cc == cfg.limit_capability_predicate
        assert not fires_cc, "Guard must NOT fire for cc:train_model with default config"

    def test_enforcement_guard_logic_code_core_override(self) -> None:
        """Simulates: cc: override fires on cc:limit_scope, not on oc:limit_capability."""
        cfg = ExtractionEnforcementConfig(limit_capability_predicate="cc:limit_scope")

        fires_cc = "cc:limit_scope" == cfg.limit_capability_predicate
        assert fires_cc, "Guard should fire for cc:limit_scope when overridden"

        fires_oc = "oc:limit_capability" == cfg.limit_capability_predicate
        assert not fires_oc, "Guard must NOT fire for oc:limit_capability when overridden to cc:"
