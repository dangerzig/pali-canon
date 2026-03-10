"""
Custom lemma mappings for forms not in DPD.

Loads mappings from custom_lemmas.yaml for easy editing by non-programmers.

Categories:
1. POTENTIAL_DPD_ADDITIONS - Legitimate words that could be submitted to DPD
2. METRICAL_VARIANTS - Vowel length changes for meter (not true lemmas)
3. SANDHI_DECOMPOSITIONS - Compound forms needing decomposition
4. PROJECT_SPECIFIC - Proper nouns, rare compounds, etc.
"""

import warnings
from pathlib import Path
from typing import Optional

try:
    import yaml
except ImportError:
    yaml = None
    warnings.warn(
        "PyYAML not installed. Custom lemma support disabled. "
        "Install with: pip install pyyaml",
        ImportWarning
    )

# Load YAML configuration
_YAML_PATH = Path(__file__).parent / "custom_lemmas.yaml"

def _load_yaml() -> dict:
    """Load custom lemmas from YAML file.

    Returns empty dict if YAML file is missing or invalid,
    with a warning to help diagnose the issue.
    """
    if yaml is None:
        return {}

    if not _YAML_PATH.exists():
        warnings.warn(
            f"Custom lemmas file not found: {_YAML_PATH}. "
            "Custom lemma support disabled.",
            UserWarning
        )
        return {}

    try:
        with open(_YAML_PATH, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            return config if config else {}
    except yaml.YAMLError as e:
        warnings.warn(
            f"Error parsing custom_lemmas.yaml: {e}. "
            "Custom lemma support disabled.",
            UserWarning
        )
        return {}

_CONFIG = _load_yaml()

# =============================================================================
# Build lookup dictionaries from YAML
# =============================================================================

def _build_lemma_dict(section: str) -> dict[str, tuple[str, str]]:
    """Build a lemma dict from a YAML section."""
    result = {}
    data = _CONFIG.get(section, {})
    for word, info in data.items():
        if not isinstance(info, dict) or 'lemma' not in info or 'pos' not in info:
            continue
        result[word] = (info['lemma'], info['pos'])
    return result

def _build_sandhi_dict() -> dict[str, tuple[list, list]]:
    """Build sandhi dict from YAML."""
    result = {}
    data = _CONFIG.get('sandhi_decompositions', {})
    for word, info in data.items():
        if not isinstance(info, dict) or 'parts' not in info or 'components' not in info:
            continue
        result[word] = (info['parts'], info['components'])
    return result

# Build dictionaries at import time
POTENTIAL_DPD_ADDITIONS = _build_lemma_dict('potential_dpd_additions')
METRICAL_VARIANTS = _build_lemma_dict('metrical_variants')
PROJECT_SPECIFIC = _build_lemma_dict('project_specific')
SANDHI_DECOMPOSITIONS = _build_sandhi_dict()

# Merge all direct lemma dictionaries
CUSTOM_LEMMAS = {}
CUSTOM_LEMMAS.update(POTENTIAL_DPD_ADDITIONS)
CUSTOM_LEMMAS.update(METRICAL_VARIANTS)
CUSTOM_LEMMAS.update(PROJECT_SPECIFIC)

# Sandhi stays separate
CUSTOM_SANDHI = SANDHI_DECOMPOSITIONS


def get_custom_lemma(word: str) -> Optional[dict]:
    """
    Look up a word in custom lemmas.

    Returns dict with lemma info, or None if not found.
    """
    word_lower = word.lower()

    # Check direct lemmas first
    if word_lower in CUSTOM_LEMMAS:
        lemma, pos = CUSTOM_LEMMAS[word_lower]
        return {"lemma": lemma, "pos": pos}

    # Check sandhi decompositions
    if word_lower in CUSTOM_SANDHI:
        parts, components = CUSTOM_SANDHI[word_lower]
        return {
            "sandhi": parts,
            "components": components
        }

    return None


def get_all_custom_words() -> set:
    """Get all words covered by custom lemmas."""
    return set(CUSTOM_LEMMAS.keys()) | set(CUSTOM_SANDHI.keys())


def get_potential_dpd_additions() -> dict:
    """Get words that could be submitted to DPD."""
    return POTENTIAL_DPD_ADDITIONS.copy()


def reload_config() -> None:
    """Reload configuration from YAML file."""
    global _CONFIG, POTENTIAL_DPD_ADDITIONS, METRICAL_VARIANTS
    global PROJECT_SPECIFIC, SANDHI_DECOMPOSITIONS
    global CUSTOM_LEMMAS, CUSTOM_SANDHI

    _CONFIG = _load_yaml()
    POTENTIAL_DPD_ADDITIONS = _build_lemma_dict('potential_dpd_additions')
    METRICAL_VARIANTS = _build_lemma_dict('metrical_variants')
    PROJECT_SPECIFIC = _build_lemma_dict('project_specific')
    SANDHI_DECOMPOSITIONS = _build_sandhi_dict()

    CUSTOM_LEMMAS = {}
    CUSTOM_LEMMAS.update(POTENTIAL_DPD_ADDITIONS)
    CUSTOM_LEMMAS.update(METRICAL_VARIANTS)
    CUSTOM_LEMMAS.update(PROJECT_SPECIFIC)
    CUSTOM_SANDHI = SANDHI_DECOMPOSITIONS
