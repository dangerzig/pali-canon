#!/usr/bin/env python3
"""
Lemmatize the entire Pāli Canon using the Digital Pali Dictionary.

Processes all canonical files and creates lemmatized versions with:
- Word-level tokenization
- Lemma (dictionary headword)
- Part of speech
- Verbal root (where applicable)
- Sandhi decomposition for compound words
"""

import json
import re
import sqlite3
from pathlib import Path
from collections import Counter
from dataclasses import dataclass
from typing import Optional

DATA_DIR = Path(__file__).parent.parent / "data"
CANONICAL_DIR = DATA_DIR / "canonical"
LEMMATIZED_DIR = DATA_DIR / "lemmatized"
DPD_DB = DATA_DIR / "dpd/dpd.db"
DPPN_FILE = DATA_DIR / "dppn/proper_names.json"

# Import custom lemmas for words not in DPD
try:
    from pali.custom_lemmas import get_custom_lemma
except ImportError:
    # Fallback for running script directly
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from custom_lemmas import get_custom_lemma

# Common enclitics/particles that join via sandhi
SANDHI_PARTICLES = {
    'ca': {'lemma': 'ca', 'pos': 'ind'},      # and
    'pi': {'lemma': 'api', 'pos': 'ind'},     # also, even
    'pī': {'lemma': 'api', 'pos': 'ind'},     # also (lengthened)
    'va': {'lemma': 'va', 'pos': 'ind'},      # or, like
    'vā': {'lemma': 'vā', 'pos': 'ind'},      # or
    'ti': {'lemma': 'ti', 'pos': 'ind'},      # quotation marker
    'tī': {'lemma': 'ti', 'pos': 'ind'},      # quotation (lengthened)
    'tu': {'lemma': 'tu', 'pos': 'ind'},      # but
    'tū': {'lemma': 'tu', 'pos': 'ind'},      # but (lengthened)
}

# Short pronoun variants (with -n/-m instead of -ṃ)
SHORT_PRONOUN_VARIANTS = {
    'm': {'lemma': 'ahaṃ', 'pos': 'pron'},         # accusative of ahaṃ (single letter)
    'man': {'lemma': 'ahaṃ', 'pos': 'pron'},       # accusative of ahaṃ
    'maṃ': {'lemma': 'ahaṃ', 'pos': 'pron'},       # accusative of ahaṃ
    'tan': {'lemma': 'so', 'pos': 'pron'},         # accusative neuter of so
    'taṃ': {'lemma': 'so', 'pos': 'pron'},         # accusative neuter of so
    'yan': {'lemma': 'ya', 'pos': 'pron'},         # accusative neuter of ya
    'yaṃ': {'lemma': 'ya', 'pos': 'pron'},         # accusative neuter of ya
    'kin': {'lemma': 'kiṃ', 'pos': 'pron'},        # accusative of kiṃ
    'kiṃ': {'lemma': 'kiṃ', 'pos': 'pron'},        # accusative of kiṃ
}

# Sandhi patterns ending in -ñcā (word + ṃ + ca with lengthening)
# e.g., abhisamparāyañcā = abhisamparāyaṃ + ca
SANDHI_NCA_PATTERN = re.compile(r'^(.+)ñcā$')

# Pre-compiled regex patterns for tokenization and normalization
HTML_TAG_PATTERN = re.compile(r'<[^>]+>')
PALI_TOKEN_PATTERN = re.compile(r'[^a-zA-ZāīūṭḍṇṅñṃḷĀĪŪṬḌṆṄÑṂḶ]+')
LEMMA_VERSION_PATTERN = re.compile(r'\s+\d+(\.\d+)?$')

# English words that appear in SuttaCentral placeholder segments
# These should be skipped during lemmatization (marked as 'eng')
ENGLISH_WORDS = {
    'on', 'display', 'title', 'of', 'section', 'only',  # "On Display: Title of Section Only"
}

# Metrical lengthening: long vowel → short vowel
METRICAL_NORMALIZATIONS = {
    'ā': 'a',
    'ī': 'i',
    'ū': 'u',
}

# Pronoun patterns that fuse with verbs
# Pattern: (prefix_to_remove, replacement_for_word, pronoun_info)
PRONOUN_VERB_PATTERNS = [
    # ahaṃ/aham at start: ahamanusāsissāmī → ahaṃ + anusāsissāmi
    (r'^aham', 'ahaṃ', {'lemma': 'ahaṃ', 'pos': 'pron'}),
    # asmi/mhi at end: brāhmaṇosmī → brāhmaṇo + asmi
    (r"[oa]smi[ī]?$", None, {'lemma': 'attā', 'pos': 'pron'}),  # treated specially
    (r"[oa]mhi[ī]?$", None, {'lemma': 'attā', 'pos': 'pron'}),  # treated specially
]

# First person verb ending normalizations (metrical lengthening)
VERB_ENDING_NORMALIZATIONS = [
    ('āmā', 'āma'),   # 1st person plural -āmā → -āma
    ('āmī', 'āmi'),   # 1st person singular -āmī → -āmi
    ('essāmī', 'essāmi'),  # future 1sg
    ('issāmī', 'issāmi'),  # future 1sg
    ('essāmā', 'essāma'),  # future 1pl
    ('issāmā', 'issāma'),  # future 1pl
]

# Minimum word length to attempt compound splitting
# Shorter words are unlikely to be decomposable compounds
MIN_COMPOUND_LENGTH = 15

# Known compound decompositions (jhāna compounds, etc.)
KNOWN_COMPOUNDS = {
    'paṭhamajhāna': ['paṭhama', 'jhāna'],
    'dutiyajhāna': ['dutiya', 'jhāna'],
    'tatiyajhāna': ['tatiya', 'jhāna'],
    'catutthajhāna': ['catuttha', 'jhāna'],
}

# Title/chapter patterns (vagga, vatthu endings are proper nouns)
TITLE_PATTERNS = [
    (r'vaggo$', 'vagga'),      # chapter title (masculine nominative)
    (r'vagga$', 'vagga'),      # chapter title (stem)
    (r'vatthu$', 'vatthu'),    # story title
]

# Apadāna title patterns: [name]thera/therī + apadāna
APADANA_PATTERN = re.compile(r'^(.+?)(thera|therī|therassa|therassā)(apadāna|apadānaṃ)$')

# Causative/intensive verb patterns for metrical variants
# These verbs have -ay-/-e- causative infix before -itvā/-etvā
CAUSATIVE_ABSOLUTIVE_PATTERNS = [
    # -ayitvā → look up base with -eti (causative)
    (r'(.+)ayitvā$', r'\1eti'),
    # -etvā → look up base with -eti
    (r'(.+)etvā$', r'\1eti'),
    # -āpetvā → look up base with -āpeti (causative)
    (r'(.+)āpetvā$', r'\1āpeti'),
]


@dataclass
class TokenInfo:
    """Information about a lemmatized token."""
    word: str
    lemma: Optional[str] = None
    pos: Optional[str] = None
    root: Optional[str] = None
    sandhi: Optional[list] = None
    components: Optional[list] = None

    def to_dict(self):
        """Convert to dict, excluding None values."""
        d = {"word": self.word}
        if self.lemma:
            d["lemma"] = self.lemma
        if self.pos:
            d["pos"] = self.pos
        if self.root:
            d["root"] = self.root
        if self.sandhi:
            d["sandhi"] = self.sandhi
            d["components"] = self.components
        return d


# =============================================================================
# Lookup Strategy Infrastructure
# =============================================================================

from abc import ABC, abstractmethod
from typing import Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Protocol


class LookupStrategy(ABC):
    """Base class for word lookup strategies.

    Each strategy attempts to resolve a word's lemma/sandhi information.
    Strategies are tried in order until one succeeds.
    """

    # Name used for stats tracking
    stat_key: str = ""

    @abstractmethod
    def try_lookup(self, word: str, token: 'TokenInfo', ctx: 'Lemmatizer') -> bool:
        """Attempt to look up the word.

        Args:
            word: The word to look up
            token: TokenInfo to populate if successful
            ctx: Lemmatizer instance for database access and helper methods

        Returns:
            True if lookup succeeded (token was modified), False otherwise
        """
        pass


class DPDLookupStrategy(LookupStrategy):
    """Direct DPD database lookup with normalization variants."""

    stat_key = ""  # Stats managed internally (normalized_variants, metrical_normalizations)

    def try_lookup(self, word: str, token: TokenInfo, ctx: 'Lemmatizer') -> bool:
        row = ctx._lookup_dpd(word)

        # Try normalized variant (-n/-m → -ṃ)
        if not ctx._has_useful_data(row):
            normalized = ctx._normalize_variant(word)
            if normalized != word:
                norm_row = ctx._lookup_dpd(normalized)
                if ctx._has_useful_data(norm_row):
                    row = norm_row
                    ctx.stats["normalized_variants"] += 1

        # Try metrical normalization (long → short vowel)
        if not ctx._has_useful_data(row):
            metrical_base = ctx._try_metrical_normalization(word)
            if metrical_base:
                met_row = ctx._lookup_dpd(metrical_base)
                if ctx._has_useful_data(met_row):
                    row = met_row
                    ctx.stats["metrical_normalizations"] += 1

        if ctx._has_useful_data(row):
            ctx._process_dpd_result(token, row)
            return True
        return False


class ShortPronounStrategy(LookupStrategy):
    """Handle short pronoun variants (m, man, tan, etc.)."""

    stat_key = "short_pronouns"

    def try_lookup(self, word: str, token: TokenInfo, ctx: 'Lemmatizer') -> bool:
        short_pron = ctx._try_short_pronoun(word)
        if short_pron:
            token.lemma = short_pron['lemma']
            token.pos = short_pron['pos']
            return True
        return False


class SandhiNcaStrategy(LookupStrategy):
    """Handle -ñcā sandhi pattern (wordṃ + ca)."""

    stat_key = "sandhi_nca"

    def try_lookup(self, word: str, token: TokenInfo, ctx: 'Lemmatizer') -> bool:
        nca_split = ctx._try_sandhi_nca(word)
        if nca_split:
            base, particle, particle_info = nca_split
            base_token = ctx.lookup_word(base)
            if base_token.lemma or base_token.sandhi:
                if base_token.sandhi:
                    token.sandhi = base_token.sandhi + [particle]
                    token.components = base_token.components + [particle_info]
                else:
                    token.sandhi = [base, particle]
                    token.components = [
                        {'lemma': base_token.lemma, 'pos': base_token.pos},
                        particle_info
                    ]
                return True
        return False


class ParticleSplitStrategy(LookupStrategy):
    """Split off trailing particles (ca, pi, va, etc.)."""

    stat_key = "particle_splits"

    def try_lookup(self, word: str, token: TokenInfo, ctx: 'Lemmatizer') -> bool:
        split = ctx._try_particle_split(word)
        if split:
            base, particle, particle_info = split
            base_token = ctx.lookup_word(base)
            if base_token.lemma or base_token.sandhi:
                if base_token.sandhi:
                    token.sandhi = base_token.sandhi + [particle]
                    token.components = base_token.components + [particle_info]
                else:
                    token.sandhi = [base, particle]
                    token.components = [
                        {'lemma': base_token.lemma, 'pos': base_token.pos},
                        particle_info
                    ]
                    if base_token.root:
                        token.components[0]['root'] = base_token.root
                return True
        return False


class DPPNStrategy(LookupStrategy):
    """Match proper nouns from DPPN dictionary."""

    stat_key = "dppn_matches"

    def try_lookup(self, word: str, token: TokenInfo, ctx: 'Lemmatizer') -> bool:
        dppn_match = ctx._try_dppn_match(word)
        if dppn_match:
            token.lemma = dppn_match['lemma']
            token.pos = dppn_match['pos']
            return True
        return False


class PronounVerbSplitStrategy(LookupStrategy):
    """Split pronoun-verb fusions (ahamanusāsissāmī → ahaṃ + anusāsissāmi)."""

    stat_key = "pronoun_verb_splits"

    def try_lookup(self, word: str, token: TokenInfo, ctx: 'Lemmatizer') -> bool:
        pv_split = ctx._try_pronoun_verb_split(word)
        if pv_split:
            verb_part, pronoun, pronoun_info = pv_split
            verb_token = ctx.lookup_word(verb_part)
            if verb_token.lemma or verb_token.sandhi:
                if verb_token.sandhi:
                    token.sandhi = [pronoun] + verb_token.sandhi
                    token.components = [pronoun_info] + verb_token.components
                else:
                    token.sandhi = [pronoun, verb_part]
                    token.components = [
                        pronoun_info,
                        {'lemma': verb_token.lemma, 'pos': verb_token.pos}
                    ]
                    if verb_token.root:
                        token.components[1]['root'] = verb_token.root
                return True
        return False


class VerbEndingStrategy(LookupStrategy):
    """Normalize verb endings (-āmā → -āma, -āmī → -āmi)."""

    stat_key = "verb_ending_normalizations"

    def try_lookup(self, word: str, token: TokenInfo, ctx: 'Lemmatizer') -> bool:
        verb_norm = ctx._try_verb_ending_normalization(word)
        if verb_norm:
            cursor = ctx.conn.execute("""
                SELECT headwords, deconstructor FROM lookup WHERE lookup_key = ?
            """, (verb_norm,))
            row = cursor.fetchone()
            if row and row['headwords']:
                try:
                    headword_ids = json.loads(row['headwords'])
                    if headword_ids:
                        hw_info = ctx._get_headword_by_id(headword_ids[0])
                        if hw_info:
                            token.lemma = hw_info.get('lemma')
                            token.pos = hw_info.get('pos')
                            token.root = hw_info.get('root')
                            return True
                except (json.JSONDecodeError, TypeError):
                    pass
        return False


class InternalMetricalStrategy(LookupStrategy):
    """Full internal metrical normalization (all long vowels → short)."""

    stat_key = "internal_metrical"

    def try_lookup(self, word: str, token: TokenInfo, ctx: 'Lemmatizer') -> bool:
        internal_norm = ctx._try_internal_metrical_normalization(word)
        if internal_norm:
            cursor = ctx.conn.execute("""
                SELECT headwords, deconstructor FROM lookup WHERE lookup_key = ?
            """, (internal_norm,))
            row = cursor.fetchone()
            if row and row['headwords']:
                try:
                    headword_ids = json.loads(row['headwords'])
                    if headword_ids:
                        hw_info = ctx._get_headword_by_id(headword_ids[0])
                        if hw_info:
                            token.lemma = hw_info.get('lemma')
                            token.pos = hw_info.get('pos')
                            token.root = hw_info.get('root')
                            return True
                except (json.JSONDecodeError, TypeError):
                    pass
        return False


class KnownCompoundStrategy(LookupStrategy):
    """Match known compound patterns (jhāna compounds, etc.)."""

    stat_key = "known_compounds"

    def try_lookup(self, word: str, token: TokenInfo, ctx: 'Lemmatizer') -> bool:
        known = ctx._try_known_compound(word)
        if known:
            token.sandhi = known['sandhi']
            token.components = known['components']
            return True
        return False


class TitleMatchStrategy(LookupStrategy):
    """Match title/chapter patterns (vagga, vatthu endings)."""

    stat_key = "title_matches"

    def try_lookup(self, word: str, token: TokenInfo, ctx: 'Lemmatizer') -> bool:
        title_match = ctx._try_title_match(word)
        if title_match:
            token.lemma = title_match['lemma']
            token.pos = title_match['pos']
            token.sandhi = title_match.get('sandhi')
            token.components = title_match.get('components')
            return True
        return False


class ApadanaTitleStrategy(LookupStrategy):
    """Match Apadāna title patterns."""

    stat_key = "apadana_titles"

    def try_lookup(self, word: str, token: TokenInfo, ctx: 'Lemmatizer') -> bool:
        apadana_match = ctx._try_apadana_title(word)
        if apadana_match:
            token.lemma = apadana_match['lemma']
            token.pos = apadana_match['pos']
            token.sandhi = apadana_match.get('sandhi')
            token.components = apadana_match.get('components')
            return True
        return False


class CausativeAbsolutiveStrategy(LookupStrategy):
    """Match causative absolutive forms (-ayitvā, -etvā, -āpetvā)."""

    stat_key = "causative_forms"

    def try_lookup(self, word: str, token: TokenInfo, ctx: 'Lemmatizer') -> bool:
        causative_base = ctx._try_causative_absolutive(word)
        if causative_base:
            hw_info = ctx._get_headword_info(causative_base)
            if hw_info:
                token.lemma = hw_info.get('lemma')
                token.pos = 'abs'
                token.root = hw_info.get('root')
                return True
        return False


class CompoundSplitStrategy(LookupStrategy):
    """Split long words into compound components."""

    stat_key = "compound_splits"

    def try_lookup(self, word: str, token: TokenInfo, ctx: 'Lemmatizer') -> bool:
        if len(word) <= MIN_COMPOUND_LENGTH:
            return False
        parts = ctx._try_compound_split(word)
        if parts and len(parts) > 1:
            token.sandhi = parts
            token.components = []
            for part in parts:
                comp_info = ctx._get_headword_info(part)
                if comp_info:
                    token.components.append(comp_info)
                else:
                    token.components.append({"word": part})
            return True
        return False


class CustomLemmaStrategy(LookupStrategy):
    """Look up words in custom lemma database."""

    stat_key = "custom_lemmas"

    def try_lookup(self, word: str, token: TokenInfo, ctx: 'Lemmatizer') -> bool:
        custom = get_custom_lemma(word)
        if custom:
            if "sandhi" in custom:
                token.sandhi = custom["sandhi"]
                token.components = custom["components"]
            else:
                token.lemma = custom.get("lemma")
                token.pos = custom.get("pos")
            return True
        return False


# Default strategy pipeline - order matters!
DEFAULT_STRATEGIES: list[LookupStrategy] = [
    DPDLookupStrategy(),
    ShortPronounStrategy(),
    SandhiNcaStrategy(),
    ParticleSplitStrategy(),
    DPPNStrategy(),
    PronounVerbSplitStrategy(),
    VerbEndingStrategy(),
    InternalMetricalStrategy(),
    KnownCompoundStrategy(),
    TitleMatchStrategy(),
    ApadanaTitleStrategy(),
    CausativeAbsolutiveStrategy(),
    CompoundSplitStrategy(),
    CustomLemmaStrategy(),
]


class Lemmatizer:
    """Lemmatizer using the Digital Pali Dictionary."""

    def __init__(self, db_path: Path = DPD_DB, dppn_path: Path = DPPN_FILE):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.cache = {}  # word -> TokenInfo
        self.stats = {
            "total_words": 0,
            "unique_words": set(),
            "words_found": 0,
            "words_not_found": 0,
            "sandhi_words": 0,
            "normalized_variants": 0,
            "particle_splits": 0,
            "metrical_normalizations": 0,
            "pronoun_verb_splits": 0,
            "verb_ending_normalizations": 0,
            "internal_metrical": 0,
            "compound_splits": 0,
            "dppn_matches": 0,
            "known_compounds": 0,
            "title_matches": 0,
            "apadana_titles": 0,
            "causative_forms": 0,
            "short_pronouns": 0,
            "sandhi_nca": 0,
            "english_words": 0,
            "custom_lemmas": 0,
            "unknown_words": Counter(),
            "lemma_counts": Counter(),
        }

        # Load DPPN proper names
        self.dppn = {}
        self.dppn_stems = {}  # stem -> (name, category)
        if dppn_path.exists():
            with open(dppn_path, 'r', encoding='utf-8') as f:
                dppn_data = json.load(f)
            # Build lookup by normalized name
            for entry in dppn_data.get('entries', []):
                name = entry['normalized']
                category = entry['category']
                # Store single-word names
                if ' ' not in name:
                    self.dppn[name] = category
                    # Also store common stems for inflection matching
                    if name.endswith('a'):
                        self.dppn_stems[name[:-1]] = (name, category)
                    elif name.endswith('ā'):
                        self.dppn_stems[name[:-1]] = (name, category)

    def close(self):
        """Close the database connection."""
        self.conn.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensures connection is closed."""
        self.close()
        return False

    def tokenize(self, text: str) -> list[str]:
        """Tokenize Pāli text into words."""
        # Strip HTML tags (e.g., <b>, </b>, <i>, </i>)
        text = HTML_TAG_PATTERN.sub(' ', text)
        # Normalize niggahīta
        text = text.replace('ṁ', 'ṃ')
        # Split on non-Pāli characters
        tokens = PALI_TOKEN_PATTERN.split(text.lower())
        return [t for t in tokens if t]

    def _normalize_variant(self, word: str) -> str:
        """Normalize orthographic variants."""
        # -n and -m are often variants of -ṃ (niggahīta)
        if word.endswith('n'):
            return word[:-1] + 'ṃ'
        if word.endswith('m') and len(word) > 1:
            return word[:-1] + 'ṃ'
        return word

    def _try_particle_split(self, word: str) -> Optional[tuple]:
        """Try to split off trailing particles (ca, pi, ti, etc.)."""
        for particle, particle_info in SANDHI_PARTICLES.items():
            if word.endswith(particle) and len(word) > len(particle) + 1:
                base = word[:-len(particle)]
                # Handle sandhi: ñca → ṃ + ca, etc.
                if base.endswith('ñ') and particle == 'ca':
                    base = base[:-1] + 'ṃ'
                elif base.endswith('ñ') and particle in ('ci', 'ce'):
                    base = base[:-1] + 'ṃ'
                return (base, particle, particle_info)
        return None

    def _try_metrical_normalization(self, word: str) -> Optional[str]:
        """Try normalizing metrical lengthening (final long vowel → short)."""
        if word and word[-1] in METRICAL_NORMALIZATIONS:
            return word[:-1] + METRICAL_NORMALIZATIONS[word[-1]]
        return None

    def _try_dppn_match(self, word: str) -> Optional[dict]:
        """Try to match word against DPPN proper names."""
        # Direct match
        if word in self.dppn:
            return {'lemma': word, 'pos': 'name', 'category': self.dppn[word]}

        # Try stem matching for inflected forms
        # Common noun endings: -ssa (gen), -ṃ (acc), -ena (inst), -āya (dat)
        endings = [
            ('ssa', 2),   # genitive -ssa, stem ends in -a
            ('āya', 2),   # dative -āya
            ('ena', 2),   # instrumental -ena
            ('ehi', 2),   # instrumental plural
            ('ānaṃ', 2),  # genitive plural
            (' āsu', 2),  # locative plural
            ('aṃ', 1),    # accusative -aṃ
            ('ā', 1),     # nominative plural / vocative
            ('e', 1),     # locative / vocative
            ('o', 1),     # nominative / vocative
        ]

        for ending, stem_add in endings:
            if word.endswith(ending) and len(word) > len(ending) + 2:
                stem = word[:-len(ending)]
                if stem in self.dppn_stems:
                    name, category = self.dppn_stems[stem]
                    return {'lemma': name, 'pos': 'name', 'category': category}
                # Try with -a ending
                stem_a = stem + 'a'
                if stem_a in self.dppn:
                    return {'lemma': stem_a, 'pos': 'name', 'category': self.dppn[stem_a]}

        return None

    def _try_known_compound(self, word: str) -> Optional[dict]:
        """Check if word is a known compound (jhāna compounds, etc.)."""
        if word in KNOWN_COMPOUNDS:
            parts = KNOWN_COMPOUNDS[word]
            return {
                'sandhi': parts,
                'components': [self._get_headword_info(p) or {'word': p} for p in parts]
            }
        return None

    def _try_title_match(self, word: str) -> Optional[dict]:
        """Check if word is a chapter/story title (vagga, vatthu endings)."""
        for pattern, base_word in TITLE_PATTERNS:
            if re.search(pattern, word):
                # Extract the title name part
                title_name = re.sub(pattern, '', word)
                if title_name:
                    return {
                        'lemma': word,
                        'pos': 'title',
                        'sandhi': [title_name, base_word],
                        'components': [
                            {'word': title_name, 'pos': 'name'},
                            {'lemma': base_word, 'pos': 'masc'}
                        ]
                    }
        return None

    def _try_apadana_title(self, word: str) -> Optional[dict]:
        """Check if word is an Apadāna title (e.g., koraṇḍapupphiyattheraapadāna)."""
        match = APADANA_PATTERN.match(word)
        if match:
            name_part = match.group(1)
            thera_part = match.group(2)
            apadana_part = match.group(3)
            return {
                'lemma': word,
                'pos': 'title',
                'sandhi': [name_part, thera_part, apadana_part],
                'components': [
                    {'word': name_part, 'pos': 'name'},
                    {'lemma': 'thera' if 'ther' in thera_part else 'therī', 'pos': 'masc' if 'ther' in thera_part else 'fem'},
                    {'lemma': 'apadāna', 'pos': 'nt'}
                ]
            }
        return None

    def _try_causative_absolutive(self, word: str) -> Optional[str]:
        """Try to find the base verb for causative absolutive forms (-ayitvā, -etvā, -āpetvā)."""
        for pattern, replacement in CAUSATIVE_ABSOLUTIVE_PATTERNS:
            match = re.match(pattern, word)
            if match:
                # Try looking up the causative verb form
                base_verb = re.sub(pattern, replacement, word)
                if self._is_valid_word(base_verb):
                    return base_verb
                # Try without the causative marker
                stem = match.group(1)
                if len(stem) > 3:
                    # Try common verb endings
                    for ending in ['ati', 'eti', 'oti', 'āti']:
                        if self._is_valid_word(stem + ending):
                            return stem + ending
        return None

    def _try_short_pronoun(self, word: str) -> Optional[dict]:
        """Check if word is a short pronoun variant (m, man, tan, etc.)."""
        if word in SHORT_PRONOUN_VARIANTS:
            return SHORT_PRONOUN_VARIANTS[word]
        return None

    def _try_sandhi_nca(self, word: str) -> Optional[tuple]:
        """Check for -ñcā sandhi pattern (word + ṃ + ca with lengthening)."""
        match = SANDHI_NCA_PATTERN.match(word)
        if match:
            base = match.group(1) + 'ṃ'  # Restore the niggahīta
            return (base, 'ca', {'lemma': 'ca', 'pos': 'ind'})
        return None

    def _try_pronoun_verb_split(self, word: str) -> Optional[tuple]:
        """Try to split pronoun from verb (e.g., ahamanusāsissāmī → ahaṃ + anusāsissāmi)."""
        # Check for aham- prefix
        if word.startswith('aham') and len(word) > 6:
            verb_part = word[4:]  # Remove 'aham'
            return (verb_part, 'ahaṃ', {'lemma': 'ahaṃ', 'pos': 'pron'})

        # Check for -osmi/-omhi/-asmi/-amhi suffix (verb "to be" fused with noun/adj)
        for suffix in ['osmī', 'osmi', 'omhī', 'omhi', 'asmī', 'asmi', 'amhī', 'amhi']:
            if word.endswith(suffix) and len(word) > len(suffix) + 2:
                base = word[:-len(suffix)]
                # Restore the -o or -a ending on the base
                if suffix.startswith('o'):
                    base = base + 'o'
                else:
                    base = base + 'a'
                verb_lemma = 'asmi' if 'sm' in suffix else 'amhi'
                return (base, suffix, {'lemma': 'attā', 'pos': 'pron', 'verb': verb_lemma})

        return None

    def _try_verb_ending_normalization(self, word: str) -> Optional[str]:
        """Try normalizing verb endings (e.g., -āmā → -āma, -āmī → -āmi)."""
        for long_ending, short_ending in VERB_ENDING_NORMALIZATIONS:
            if word.endswith(long_ending):
                return word[:-len(long_ending)] + short_ending
        return None

    def _try_internal_metrical_normalization(self, word: str) -> Optional[str]:
        """Try normalizing internal long vowels (full metrical normalization)."""
        # Replace all long vowels with short ones
        normalized = word
        for long_v, short_v in METRICAL_NORMALIZATIONS.items():
            normalized = normalized.replace(long_v, short_v)
        if normalized != word:
            return normalized
        return None

    def _is_valid_word(self, word: str) -> bool:
        """Check if a word exists in the DPD lookup table."""
        cursor = self.conn.execute(
            "SELECT 1 FROM lookup WHERE lookup_key = ? LIMIT 1", (word,))
        return cursor.fetchone() is not None

    def _try_compound_split(self, word: str, max_depth: int = 8, is_final: bool = True) -> Optional[list]:
        """
        Try to split a long compound into component words.
        Uses greedy longest-match with backtracking.
        Returns list of component words if successful, None otherwise.
        """
        if max_depth <= 0:
            return None

        # Normalize long vowels for lookup (metrical lengthening in compounds)
        normalized = word
        for long_v, short_v in METRICAL_NORMALIZATIONS.items():
            normalized = normalized.replace(long_v, short_v)

        # Minimum component length to avoid splitting on case endings
        MIN_PART_LEN = 4

        # Common case endings that might appear at the end of compounds
        CASE_ENDINGS = ['assa', 'ānaṃ', 'ena', 'āya', 'ssa', 'aṃ', 'ehi', 'āsu', 'esu', 'ā']

        # For final word in compound, try stripping case endings
        if is_final and len(word) > MIN_PART_LEN + 3:
            for ending in CASE_ENDINGS:
                if word.endswith(ending) or normalized.endswith(ending):
                    stem = word[:-len(ending)]
                    stem_norm = normalized[:-len(ending)]
                    # Check if stem + standard nominative 'a' is valid
                    if self._is_valid_word(stem) or self._is_valid_word(stem_norm):
                        return [word]  # Return the inflected form as-is
                    if self._is_valid_word(stem + 'a') or self._is_valid_word(stem_norm + 'a'):
                        return [word]  # Return the inflected form as-is

        # For short words, just check if valid
        if len(word) < MIN_PART_LEN * 2:
            if self._is_valid_word(word) or self._is_valid_word(normalized):
                return [word]
            return None

        # Try to find longest valid prefix
        for prefix_len in range(len(word) - MIN_PART_LEN, MIN_PART_LEN - 1, -1):
            prefix = word[:prefix_len]
            prefix_norm = normalized[:prefix_len]
            remainder = word[prefix_len:]

            # Check if prefix is a valid word (original or normalized)
            prefix_valid = self._is_valid_word(prefix) or self._is_valid_word(prefix_norm)

            if prefix_valid:
                if len(remainder) == 0:
                    return [prefix]

                if len(remainder) >= MIN_PART_LEN:
                    remainder_split = self._try_compound_split(remainder, max_depth - 1, is_final)
                    if remainder_split is not None:
                        return [prefix] + remainder_split

            # Try sandhi junction: doubled consonant at boundary
            if len(remainder) >= 2 and remainder[0] == remainder[1] and remainder[0] not in 'aeiouāīū':
                prefix_with_consonant = prefix + remainder[0]
                prefix_wc_norm = prefix_norm + remainder[0]
                if self._is_valid_word(prefix_with_consonant) or self._is_valid_word(prefix_wc_norm):
                    new_remainder = remainder[1:]
                    if len(new_remainder) >= MIN_PART_LEN:
                        remainder_split = self._try_compound_split(new_remainder, max_depth - 1, is_final)
                        if remainder_split is not None:
                            return [prefix_with_consonant] + remainder_split

            # Try with 'a' added to prefix (compound junction vowel)
            if not prefix.endswith('a') and len(remainder) >= MIN_PART_LEN:
                prefix_a = prefix + 'a'
                if self._is_valid_word(prefix_a):
                    remainder_split = self._try_compound_split(remainder, max_depth - 1, is_final)
                    if remainder_split is not None:
                        return [prefix_a] + remainder_split

        # If word itself is valid (or normalized form), return as single component
        if self._is_valid_word(word) or self._is_valid_word(normalized):
            return [word]

        return None

    def lookup_word(self, word: str, strategies: list[LookupStrategy] = None) -> TokenInfo:
        """Look up a word and return its lemma info.

        Uses a pipeline of lookup strategies, trying each in order until
        one succeeds. Strategies are defined in DEFAULT_STRATEGIES.

        Args:
            word: The word to look up
            strategies: Optional custom strategy list (defaults to DEFAULT_STRATEGIES)

        Returns:
            TokenInfo with lemma/sandhi information
        """
        # Check cache first
        if word in self.cache:
            return self.cache[word]

        # Skip English words (from SuttaCentral placeholder segments)
        if word in ENGLISH_WORDS:
            token = TokenInfo(word=word, lemma=word, pos='eng')
            self.cache[word] = token
            self.stats["english_words"] += 1
            return token

        token = TokenInfo(word=word)

        # Try each strategy in order until one succeeds
        if strategies is None:
            strategies = DEFAULT_STRATEGIES

        for strategy in strategies:
            # Skip if we already have a result
            if token.lemma or token.sandhi:
                break

            if strategy.try_lookup(word, token, self):
                # Update stats for successful strategy
                if strategy.stat_key:
                    self.stats[strategy.stat_key] += 1

        # Update overall stats
        if token.lemma or token.sandhi:
            self.stats["words_found"] += 1
            if token.lemma:
                self.stats["lemma_counts"][token.lemma] += 1
        else:
            self.stats["words_not_found"] += 1
            self.stats["unknown_words"][word] += 1

        self.cache[word] = token
        return token

    def _has_useful_data(self, row) -> bool:
        """Check if a DPD lookup row has useful data (not just a stub entry)."""
        return row and (row['headwords'] or row['deconstructor'])

    def _lookup_dpd(self, word: str):
        """Look up a word in the DPD lookup table."""
        cursor = self.conn.execute("""
            SELECT headwords, deconstructor FROM lookup WHERE lookup_key = ?
        """, (word,))
        return cursor.fetchone()

    def _apply_headword_to_token(self, token: TokenInfo, row) -> bool:
        """Apply headword info from a DPD row to a token. Returns True if successful."""
        if not row or not row['headwords']:
            return False
        try:
            headword_ids = json.loads(row['headwords'])
            if headword_ids:
                hw_info = self._get_headword_by_id(headword_ids[0])
                if hw_info:
                    token.lemma = hw_info.get('lemma')
                    token.pos = hw_info.get('pos')
                    token.root = hw_info.get('root')
                    return True
        except (json.JSONDecodeError, TypeError):
            pass
        return False

    def _process_dpd_result(self, token: TokenInfo, row) -> None:
        """Process a DPD lookup result and update the token.

        Handles both sandhi decompositions and direct headword lookups.
        """
        # Check for sandhi decomposition first
        if row['deconstructor']:
            try:
                deconstructions = json.loads(row['deconstructor'])
                if deconstructions:
                    # Use first deconstruction
                    parts = deconstructions[0].replace(' ', '').split('+')
                    token.sandhi = parts
                    token.components = []
                    for part in parts:
                        comp_info = self._get_headword_info(part)
                        if comp_info:
                            token.components.append(comp_info)
                        else:
                            token.components.append({"word": part})
                    self.stats["sandhi_words"] += 1
                    return
            except (json.JSONDecodeError, TypeError):
                pass

        # Get headword info if not a sandhi word
        self._apply_headword_to_token(token, row)

    def _get_headword_info(self, word: str) -> Optional[dict]:
        """Get headword info for a word (used for sandhi components)."""
        cursor = self.conn.execute("""
            SELECT headwords FROM lookup WHERE lookup_key = ?
        """, (word,))
        row = cursor.fetchone()
        if row and row['headwords']:
            try:
                headword_ids = json.loads(row['headwords'])
                if headword_ids:
                    return self._get_headword_by_id(headword_ids[0])
            except (json.JSONDecodeError, TypeError):
                pass
        return None

    def _get_headword_by_id(self, hw_id: int) -> Optional[dict]:
        """Get headword details by ID."""
        cursor = self.conn.execute("""
            SELECT lemma_1, pos, root_key FROM dpd_headwords WHERE id = ?
        """, (hw_id,))
        row = cursor.fetchone()
        if row:
            # Clean lemma (remove version numbers like "dhamma 1.01" -> "dhamma")
            lemma = row['lemma_1']
            if lemma:
                lemma = LEMMA_VERSION_PATTERN.sub('', lemma)

            result = {"lemma": lemma, "pos": row['pos']}
            if row['root_key']:
                result["root"] = f"√{row['root_key']}"
            return result
        return None

    def lemmatize_segment(self, segment: dict) -> dict:
        """Lemmatize a single segment."""
        pali_text = segment.get("pali", "")
        tokens = self.tokenize(pali_text)

        token_infos = []
        for word in tokens:
            self.stats["total_words"] += 1
            self.stats["unique_words"].add(word)
            token_info = self.lookup_word(word)
            token_infos.append(token_info.to_dict())

        return {
            "id": segment["id"],
            "pali": pali_text,
            "tokens": token_infos
        }

    def get_stats(self) -> dict:
        """Get current statistics."""
        return {
            "total_words": self.stats["total_words"],
            "unique_words": len(self.stats["unique_words"]),
            "words_found": self.stats["words_found"],
            "words_not_found": self.stats["words_not_found"],
            "sandhi_words": self.stats["sandhi_words"],
            "normalized_variants": self.stats["normalized_variants"],
            "particle_splits": self.stats["particle_splits"],
            "metrical_normalizations": self.stats["metrical_normalizations"],
            "pronoun_verb_splits": self.stats["pronoun_verb_splits"],
            "verb_ending_normalizations": self.stats["verb_ending_normalizations"],
            "internal_metrical": self.stats["internal_metrical"],
            "compound_splits": self.stats["compound_splits"],
            "dppn_matches": self.stats["dppn_matches"],
            "known_compounds": self.stats["known_compounds"],
            "title_matches": self.stats["title_matches"],
            "apadana_titles": self.stats["apadana_titles"],
            "causative_forms": self.stats["causative_forms"],
            "short_pronouns": self.stats["short_pronouns"],
            "sandhi_nca": self.stats["sandhi_nca"],
            "custom_lemmas": self.stats["custom_lemmas"],
            "coverage": f"{self.stats['words_found'] / max(1, len(self.stats['unique_words'])) * 100:.1f}%",
            "top_lemmas": self.stats["lemma_counts"].most_common(100),
            "unknown_words": self.stats["unknown_words"].most_common(500),
        }


def process_dn_mn_file(input_path: Path, output_path: Path, lemmatizer: Lemmatizer):
    """Process DN or MN file (flat segments array)."""
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Lemmatize each segment
    lemmatized_segments = []
    for segment in data.get("segments", []):
        lemmatized_segments.append(lemmatizer.lemmatize_segment(segment))

    # Create output with same metadata
    output = {k: v for k, v in data.items() if k != "segments"}
    output["segments"] = lemmatized_segments

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)


def process_sn_an_file(input_path: Path, output_path: Path, lemmatizer: Lemmatizer):
    """Process SN or AN file (nested suttas array)."""
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Lemmatize each sutta's segments
    lemmatized_suttas = []
    for sutta in data.get("suttas", []):
        lemmatized_segments = []
        for segment in sutta.get("segments", []):
            lemmatized_segments.append(lemmatizer.lemmatize_segment(segment))

        lemmatized_sutta = {k: v for k, v in sutta.items() if k != "segments"}
        lemmatized_sutta["segments"] = lemmatized_segments
        lemmatized_suttas.append(lemmatized_sutta)

    # Create output with same metadata
    output = {k: v for k, v in data.items() if k != "suttas"}
    output["suttas"] = lemmatized_suttas

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)


def process_kn_file(input_path: Path, output_path: Path, lemmatizer: Lemmatizer):
    """Process KN file (nested items array)."""
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Lemmatize each item's segments
    lemmatized_items = []
    for item in data.get("items", []):
        lemmatized_segments = []
        for segment in item.get("segments", []):
            lemmatized_segments.append(lemmatizer.lemmatize_segment(segment))

        lemmatized_item = {k: v for k, v in item.items() if k != "segments"}
        lemmatized_item["segments"] = lemmatized_segments
        lemmatized_items.append(lemmatized_item)

    # Create output with same metadata
    output = {k: v for k, v in data.items() if k != "items"}
    output["items"] = lemmatized_items

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)


def process_collection(collection: str, lemmatizer: Lemmatizer):
    """Process all files in a collection."""
    input_dir = CANONICAL_DIR / collection
    output_dir = LEMMATIZED_DIR / collection

    # Get all JSON files (excluding index)
    files = sorted([f for f in input_dir.glob("*.json") if not f.name.startswith("_")])

    for i, input_path in enumerate(files):
        output_path = output_dir / input_path.name

        if collection in ("dn", "mn"):
            process_dn_mn_file(input_path, output_path, lemmatizer)
        elif collection in ("sn", "an"):
            process_sn_an_file(input_path, output_path, lemmatizer)
        elif collection == "kn":
            process_kn_file(input_path, output_path, lemmatizer)

        print(f"  [{i+1}/{len(files)}] {input_path.name}")


def main():
    print("=" * 60)
    print("Lemmatizing the Pāli Canon")
    print("=" * 60)

    lemmatizer = Lemmatizer()

    collections = ["dn", "mn", "sn", "an", "kn"]

    for collection in collections:
        print(f"\nProcessing {collection.upper()}...")
        process_collection(collection, lemmatizer)

    # Generate and save statistics
    stats = lemmatizer.get_stats()

    LEMMATIZED_DIR.mkdir(parents=True, exist_ok=True)
    with open(LEMMATIZED_DIR / "_stats.json", 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)

    print(f"\n{'=' * 60}")
    print("COMPLETE")
    print(f"{'=' * 60}")
    print(f"Total words:         {stats['total_words']:,}")
    print(f"Unique words:        {stats['unique_words']:,}")
    print(f"Words found:         {stats['words_found']:,}")
    print(f"Words not found:     {stats['words_not_found']:,}")
    print(f"Sandhi words:        {stats['sandhi_words']:,}")
    print(f"Normalized (-n→-ṃ):  {stats['normalized_variants']:,}")
    print(f"Particle splits:     {stats['particle_splits']:,}")
    print(f"Metrical (final):    {stats['metrical_normalizations']:,}")
    print(f"Metrical (internal): {stats['internal_metrical']:,}")
    print(f"Pronoun-verb splits: {stats['pronoun_verb_splits']:,}")
    print(f"Verb ending norm:    {stats['verb_ending_normalizations']:,}")
    print(f"Compound splits:     {stats['compound_splits']:,}")
    print(f"DPPN matches:        {stats['dppn_matches']:,}")
    print(f"Known compounds:     {stats['known_compounds']:,}")
    print(f"Title matches:       {stats['title_matches']:,}")
    print(f"Apadāna titles:      {stats['apadana_titles']:,}")
    print(f"Causative forms:     {stats['causative_forms']:,}")
    print(f"Short pronouns:      {stats['short_pronouns']:,}")
    print(f"Sandhi -ñcā:         {stats['sandhi_nca']:,}")
    print(f"Custom lemmas:       {stats['custom_lemmas']:,}")
    print(f"Coverage:            {stats['coverage']}")
    print(f"\nOutput saved to: {LEMMATIZED_DIR}")

    lemmatizer.close()


if __name__ == "__main__":
    main()
