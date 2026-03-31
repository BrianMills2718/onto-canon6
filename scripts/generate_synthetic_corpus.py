"""Generate synthetic corpus for entity resolution scale test.

Produces 25 documents with overlapping entities using varied name forms.
Each document is a realistic paragraph about military/intelligence operations
that references 2-5 entities from the ground truth.

Usage:
    python scripts/generate_synthetic_corpus.py

Output: tests/fixtures/synthetic_corpus/doc_XX.txt (25 files)
"""

from __future__ import annotations

import json
from pathlib import Path

GROUND_TRUTH = Path("tests/fixtures/synthetic_corpus/ground_truth.json")
OUTPUT_DIR = Path("tests/fixtures/synthetic_corpus")

# Each document is a template with entity slots filled by name variants.
# The key design constraint: use DIFFERENT name variants across documents
# to test entity resolution.

DOCUMENTS: dict[str, str] = {
    "doc_01": (
        "In a recent briefing, {E001_v0} outlined the strategic priorities for "
        "{E002_v0} in the coming fiscal year. The command's focus on irregular "
        "warfare capabilities was emphasized, with {E001_v1} noting that special "
        "operations forces must adapt to emerging threats in the cyber domain."
    ),
    "doc_02": (
        "{E003_v0} served as the eighth commander of {E002_v1} from 2007 to 2011. "
        "During his tenure, {E003_v1} expanded the command's counterterrorism "
        "capabilities. {E001_v2} later succeeded him in a different capacity, "
        "bringing a focus on psychological operations."
    ),
    "doc_03": (
        "The {E004_v0}, headquartered at {E005_v0}, is responsible for planning "
        "and conducting military information support operations. {E002_v2} "
        "provides oversight for the group's activities across multiple theaters."
    ),
    "doc_04": (
        "{E003_v2} met with officials from the {E006_v0} at the agency's "
        "headquarters in {E012_v0}. The meeting focused on joint operations "
        "and intelligence sharing protocols between special operations forces "
        "and the intelligence community."
    ),
    "doc_05": (
        "Under the leadership of {E001_v3}, {E002_v3} launched several "
        "initiatives to modernize its force structure. The reforms included "
        "new training programs and equipment upgrades for deployed units."
    ),
    "doc_06": (
        "{E007_v0} assumed command of the {E004_v1} at {E005_v1} in a "
        "ceremony attended by senior military officials. The change of command "
        "marked a new chapter for the psychological operations community."
    ),
    "doc_07": (
        "{E008_v0}, a senior analyst at the {E006_v1}, published a classified "
        "assessment of information warfare capabilities. The report examined "
        "how {E002_v0} coordinates with the intelligence community on influence "
        "operations."
    ),
    "doc_08": (
        "{E001_v4} attended a joint conference with representatives from the "
        "{E009_v0} in {E012_v1}. The conference addressed signals intelligence "
        "support to special operations forces deployed overseas."
    ),
    "doc_09": (
        "{E010_v0} was appointed deputy commander of {E002_v0}. Working "
        "alongside {E003_v3}, he helped reshape the command's approach to "
        "partner force development in contested regions."
    ),
    "doc_10": (
        "At {E005_v2}, {E007_v1} led a training exercise involving the "
        "{E004_v2}. The exercise tested new psychological operations "
        "techniques developed in response to adversary information campaigns."
    ),
    "doc_11": (
        "{E008_v1} briefed {E006_v2} leadership on emerging threats "
        "in the information environment. She also lectured at "
        "{E013_v0} on intelligence analysis methodology."
    ),
    "doc_12": (
        "A joint task force led by {E001_v0} coordinated with the {E009_v1} "
        "on a sensitive collection operation. The operation demonstrated the "
        "growing integration between special operations and signals intelligence."
    ),
    "doc_13": (
        "{E007_v2} deployed the {E004_v3} to support combat operations. "
        "The group operated from a forward base near {E005_v0}, conducting "
        "influence campaigns targeting adversary decision-makers."
    ),
    "doc_14": (
        "{E010_v1} testified before Congress about {E002_v0}'s budget "
        "requirements. He emphasized the need for sustained investment in "
        "special operations capabilities across all service components."
    ),
    "doc_15": (
        "{E001_v1} and {E011_v0}, a civilian analyst, co-authored a strategy "
        "document for the {E006_v0}. Despite sharing a surname, the two brought "
        "complementary perspectives from military and civilian backgrounds."
    ),
    "doc_16": (
        "{E003_v0} retired to {E012_v2} after his service. In retirement, "
        "he advised several defense think tanks and remained active in the "
        "special operations policy community."
    ),
    "doc_17": (
        "The {E004_v0} under {E007_v3} developed new capabilities for "
        "operating in the digital information space. The unit's soldiers "
        "trained extensively in social media analysis and content creation."
    ),
    "doc_18": (
        "{E010_v2} directed a review of {E002_v1}'s force posture in "
        "the Pacific region. The review concluded that additional special "
        "operations forces were needed to counter growing regional threats."
    ),
    "doc_19": (
        "{E008_v2} collaborated with researchers at {E013_v1} and analysts "
        "from the {E009_v0} on a study of adversary influence operations. "
        "The {E006_v1} provided additional data for the research effort."
    ),
    "doc_20": (
        "{E011_v1} presented findings on social media manipulation at a "
        "conference where {E001_v2} was the keynote speaker. Their work "
        "highlighted different aspects of information warfare."
    ),
    "doc_21": (
        "New facilities at {E005_v0} were opened to support expanded "
        "training programs. The installation's role as the home of special "
        "operations psychological warfare continued to grow."
    ),
    "doc_22": (
        "{E010_v3} presided over a ceremony at {E002_v0} headquarters "
        "recognizing exceptional service by special operations personnel. "
        "The event highlighted the command's diverse mission set."
    ),
    "doc_23": (
        "Officials from the {E006_v0} and the Pentagon met in {E012_v0} "
        "to discuss interagency coordination for information operations. "
        "The meeting produced new guidelines for joint planning."
    ),
    "doc_24": (
        "The {E009_v1} expanded its support to special operations forces "
        "with new technical collection capabilities. The partnership "
        "between signals intelligence and special operations deepened."
    ),
    "doc_25": (
        "A comprehensive review of military psychological operations found "
        "that information support to military operations had become a "
        "critical component of modern warfare across all combatant commands."
    ),
}

# Map entity+variant index to actual name strings
VARIANT_MAP: dict[str, dict[str, str]] = {
    "E001": {
        "v0": "Gen. Smith", "v1": "General Smith", "v2": "General John Smith",
        "v3": "John Smith", "v4": "Gen. J. Smith",
    },
    "E002": {
        "v0": "USSOCOM", "v1": "U.S. Special Operations Command",
        "v2": "US Special Operations Command", "v3": "Special Operations Command",
    },
    "E003": {
        "v0": "Adm. Olson", "v1": "Admiral Olson", "v2": "Eric Olson",
        "v3": "Adm. Eric Olson",
    },
    "E004": {
        "v0": "4th PSYOP Group", "v1": "4th POG", "v2": "4th Psychological Operations Group",
        "v3": "4th POG(A)",
    },
    "E005": {
        "v0": "Fort Bragg", "v1": "Ft. Bragg", "v2": "Fort Liberty",
    },
    "E006": {
        "v0": "CIA", "v1": "Central Intelligence Agency", "v2": "the Agency",
    },
    "E007": {
        "v0": "Col. Rodriguez", "v1": "Colonel Rodriguez",
        "v2": "James Rodriguez", "v3": "Col. James Rodriguez",
    },
    "E008": {
        "v0": "Dr. Chen", "v1": "Sarah Chen", "v2": "Dr. Sarah Chen",
    },
    "E009": {
        "v0": "NSA", "v1": "National Security Agency",
    },
    "E010": {
        "v0": "Lt. Gen. Torres", "v1": "General Torres",
        "v2": "Michael Torres", "v3": "Lt. Gen. Michael Torres",
    },
    "E011": {
        "v0": "James Smith", "v1": "J. Smith",
    },
    "E012": {
        "v0": "Washington", "v1": "Washington D.C.", "v2": "D.C.",
    },
    "E013": {
        "v0": "George Washington University", "v1": "GWU",
    },
}


def generate() -> None:
    """Generate all synthetic documents."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for doc_id, template in DOCUMENTS.items():
        text = template
        # Replace all {EXXX_vY} placeholders with actual name variants
        for entity_id, variants in VARIANT_MAP.items():
            for variant_key, variant_name in variants.items():
                placeholder = f"{{{entity_id}_{variant_key}}}"
                text = text.replace(placeholder, variant_name)

        output_path = OUTPUT_DIR / f"{doc_id}.txt"
        output_path.write_text(text, encoding="utf-8")
        print(f"Generated {output_path} ({len(text)} chars)")

    print(f"\nGenerated {len(DOCUMENTS)} documents in {OUTPUT_DIR}")


if __name__ == "__main__":
    generate()
