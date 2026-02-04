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
from dataclasses import dataclass, asdict
from typing import Optional

DATA_DIR = Path(__file__).parent.parent / "data"
CANONICAL_DIR = DATA_DIR / "canonical"
LEMMATIZED_DIR = DATA_DIR / "lemmatized"
DPD_DB = DATA_DIR / "dpd/dpd.db"
DPPN_FILE = DATA_DIR / "dppn/proper_names.json"

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

# Metrical lengthening: long vowel → short vowel
METRICAL_NORMALIZATIONS = {
    'ā': 'a',
    'ī': 'i',
    'ū': 'u',
}


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
            "dppn_matches": 0,
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
        self.conn.close()

    def tokenize(self, text: str) -> list[str]:
        """Tokenize Pāli text into words."""
        # Normalize niggahīta
        text = text.replace('ṁ', 'ṃ')
        # Split on non-Pāli characters
        tokens = re.split(r'[^a-zA-ZāīūṭḍṇṅñṃḷĀĪŪṬḌṆṄÑṂḶ]+', text.lower())
        return [t for t in tokens if t]

    def _normalize_variant(self, word: str) -> str:
        """Normalize orthographic variants."""
        # -n is often a variant of -ṃ (niggahīta)
        if word.endswith('n'):
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

    def lookup_word(self, word: str) -> TokenInfo:
        """Look up a word and return its lemma info."""
        # Check cache first
        if word in self.cache:
            return self.cache[word]

        cursor = self.conn.execute("""
            SELECT headwords, deconstructor FROM lookup WHERE lookup_key = ?
        """, (word,))
        row = cursor.fetchone()

        # If not found, try normalized variant (-n → -ṃ)
        normalized = None
        if not row:
            normalized = self._normalize_variant(word)
            if normalized != word:
                cursor = self.conn.execute("""
                    SELECT headwords, deconstructor FROM lookup WHERE lookup_key = ?
                """, (normalized,))
                row = cursor.fetchone()
                if row:
                    self.stats["normalized_variants"] += 1

        # If still not found, try metrical normalization (long → short vowel)
        metrical_base = None
        if not row:
            metrical_base = self._try_metrical_normalization(word)
            if metrical_base:
                cursor = self.conn.execute("""
                    SELECT headwords, deconstructor FROM lookup WHERE lookup_key = ?
                """, (metrical_base,))
                row = cursor.fetchone()
                if row:
                    self.stats["metrical_normalizations"] += 1

        token = TokenInfo(word=word)

        if row:
            # Found in DPD - check for sandhi decomposition first
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
                except (json.JSONDecodeError, TypeError):
                    pass

            # Get headword info if not a sandhi word
            if not token.sandhi and row['headwords']:
                try:
                    headword_ids = json.loads(row['headwords'])
                    if headword_ids:
                        # Get first headword's info
                        hw_info = self._get_headword_by_id(headword_ids[0])
                        if hw_info:
                            token.lemma = hw_info.get('lemma')
                            token.pos = hw_info.get('pos')
                            token.root = hw_info.get('root')
                except (json.JSONDecodeError, TypeError):
                    pass

        # If not found in DPD, try particle splitting
        if not token.lemma and not token.sandhi:
            split = self._try_particle_split(word)
            if split:
                base, particle, particle_info = split
                base_token = self.lookup_word(base)  # Recursive lookup
                if base_token.lemma or base_token.sandhi:
                    # Successfully split!
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
                    self.stats["particle_splits"] += 1

        # If still not found, try DPPN proper noun matching
        if not token.lemma and not token.sandhi:
            dppn_match = self._try_dppn_match(word)
            if dppn_match:
                token.lemma = dppn_match['lemma']
                token.pos = dppn_match['pos']
                self.stats["dppn_matches"] += 1

        # Update stats
        if token.lemma or token.sandhi:
            self.stats["words_found"] += 1
            if token.lemma:
                self.stats["lemma_counts"][token.lemma] += 1
        else:
            self.stats["words_not_found"] += 1
            self.stats["unknown_words"][word] += 1

        self.cache[word] = token
        return token

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
                lemma = re.sub(r'\s+\d+(\.\d+)?$', '', lemma)

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
            "dppn_matches": self.stats["dppn_matches"],
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
    print(f"Metrical norm:       {stats['metrical_normalizations']:,}")
    print(f"DPPN matches:        {stats['dppn_matches']:,}")
    print(f"Coverage:            {stats['coverage']}")
    print(f"\nOutput saved to: {LEMMATIZED_DIR}")

    lemmatizer.close()


if __name__ == "__main__":
    main()
