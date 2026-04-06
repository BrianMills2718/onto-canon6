"""pytest conftest for research_v3 path setup — not auto-loaded.

Imported by test_contract_boundaries.py to resolve research_v3's shared_export
module without hardcoding paths throughout every test method.
"""
from __future__ import annotations

import importlib
import importlib.util
import sys
from pathlib import Path

_RESEARCH_V3_ROOT = Path(__file__).resolve().parents[3] / "research_v3"


def load_shared_export():  # type: ignore[return]
    """Import research_v3.shared_export, adding its repo root to sys.path once."""
    if "shared_export" in sys.modules:
        return sys.modules["shared_export"]
    root = str(_RESEARCH_V3_ROOT)
    if root not in sys.path:
        sys.path.insert(0, root)
    return importlib.import_module("shared_export")


def research_v3_available() -> bool:
    """Return True if research_v3 shared_export can be imported."""
    spec = importlib.util.find_spec("shared_export") if str(_RESEARCH_V3_ROOT) in sys.path else None
    if spec is None:
        root = str(_RESEARCH_V3_ROOT)
        if root not in sys.path:
            sys.path.insert(0, root)
    try:
        importlib.import_module("shared_export")
        return True
    except ImportError:
        return False
