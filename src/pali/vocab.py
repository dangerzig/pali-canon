"""Vocabulary statistics and document-term matrices."""

from dataclasses import dataclass, field
from typing import Optional, Any
from pathlib import Path
from collections import Counter
import json

# Optional imports for data science functionality
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

try:
    import numpy as np
    from scipy import sparse
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False


@dataclass
class VocabularyStats:
    """Vocabulary statistics for a sutta or collection."""
    sutta_id: Optional[str]
    nikaya: Optional[str]
    unique_lemmas: int
    total_tokens: int
    coverage: float  # Proportion of tokens with known lemmas
    top_lemmas: list[tuple[str, int]] = field(default_factory=list)
    lemma_counts: dict[str, int] = field(default_factory=dict)
    pos_distribution: dict[str, int] = field(default_factory=dict)


class Vocabulary:
    """Vocabulary analysis for the Pāli Canon."""

    def __init__(self, data_dir: Path):
        """Initialize vocabulary analyzer.

        Args:
            data_dir: Path to data directory
        """
        self.data_dir = data_dir
        self.lemmatized_dir = data_dir / "lemmatized"

    def get_vocabulary(
        self,
        sutta_id: Optional[str] = None,
        nikaya: Optional[str] = None,
        top_n: int = 100,
        as_dataframe: bool = False,
    ) -> Any:
        """Get vocabulary statistics for a sutta or nikaya.

        Args:
            sutta_id: Specific sutta ID (e.g., "dn1")
            nikaya: Nikaya ID (e.g., "dn") - ignored if sutta_id provided
            top_n: Number of top lemmas to include
            as_dataframe: If True, return pandas DataFrame instead of VocabularyStats

        Returns:
            VocabularyStats object, or pandas DataFrame if as_dataframe=True

        Example:
            vocab = canon.get_vocabulary("dn1")
            print(f"Unique lemmas: {vocab.unique_lemmas}")
            print(f"Top 10: {vocab.top_lemmas[:10]}")
        """
        lemma_counts: Counter = Counter()
        pos_counts: Counter = Counter()
        total_tokens = 0
        tokens_with_lemma = 0

        if sutta_id:
            # Single sutta
            self._count_sutta(sutta_id, lemma_counts, pos_counts)
            total_tokens = sum(lemma_counts.values())
            tokens_with_lemma = total_tokens  # All counted tokens have lemmas
        elif nikaya:
            # Entire nikaya
            nikaya_dir = self.lemmatized_dir / nikaya
            if nikaya_dir.exists():
                for json_file in nikaya_dir.glob("*.json"):
                    if json_file.name.startswith("_"):
                        continue
                    self._count_file(json_file, nikaya, lemma_counts, pos_counts)
            total_tokens = sum(lemma_counts.values())
            tokens_with_lemma = total_tokens

        # Calculate coverage (proportion with known lemmas)
        coverage = tokens_with_lemma / total_tokens if total_tokens > 0 else 0.0

        top_lemmas = lemma_counts.most_common(top_n)

        stats = VocabularyStats(
            sutta_id=sutta_id,
            nikaya=nikaya,
            unique_lemmas=len(lemma_counts),
            total_tokens=total_tokens,
            coverage=coverage,
            top_lemmas=top_lemmas,
            lemma_counts=dict(lemma_counts),
            pos_distribution=dict(pos_counts),
        )

        if as_dataframe:
            if not HAS_PANDAS:
                raise ImportError("pandas is required for DataFrame output. Install with: pip install pandas")
            return self._stats_to_dataframe(stats)

        return stats

    def _stats_to_dataframe(self, stats: VocabularyStats) -> "pd.DataFrame":
        """Convert VocabularyStats to pandas DataFrame."""
        rows = []
        for lemma, count in stats.lemma_counts.items():
            rows.append({"lemma": lemma, "count": count})
        df = pd.DataFrame(rows)
        df = df.sort_values("count", ascending=False).reset_index(drop=True)
        return df

    def _count_sutta(self, sutta_id: str, lemma_counts: Counter, pos_counts: Counter) -> None:
        """Count lemmas in a single sutta."""
        # Import here to avoid circular imports
        from .store import Store, KN_TEXT_PREFIXES, NIKAYAS

        # Determine nikaya
        nikaya = None
        for prefix in KN_TEXT_PREFIXES:
            if sutta_id.startswith(prefix):
                nikaya = "kn"
                break
        if not nikaya:
            for n in NIKAYAS:
                if sutta_id.startswith(n):
                    nikaya = n
                    break

        if not nikaya:
            return

        store = Store(self.data_dir)
        sutta = store.get_sutta(sutta_id, lemmatized=True, include_tokens=True)
        if sutta:
            for segment in sutta.segments:
                if segment.tokens:
                    for token in segment.tokens:
                        if token.lemma:
                            lemma_counts[token.lemma] += 1
                            if token.pos:
                                pos_counts[token.pos] += 1

    def _count_file(self, json_file: Path, nikaya: str,
                   lemma_counts: Counter, pos_counts: Counter) -> None:
        """Count lemmas in a JSON file."""
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        if nikaya in ("dn", "mn"):
            self._count_segments(data.get("segments", []), lemma_counts, pos_counts)
        elif nikaya in ("sn", "an"):
            for sutta_data in data.get("suttas", []):
                self._count_segments(sutta_data.get("segments", []), lemma_counts, pos_counts)
        elif nikaya == "kn":
            if "items" in data:
                for item in data["items"]:
                    self._count_segments(item.get("segments", []), lemma_counts, pos_counts)
            else:
                self._count_segments(data.get("segments", []), lemma_counts, pos_counts)

    def _count_segments(self, segments: list, lemma_counts: Counter, pos_counts: Counter) -> None:
        """Count lemmas in a list of segments."""
        for segment in segments:
            for token in segment.get("tokens", []):
                lemma = token.get("lemma")
                if lemma:
                    lemma_counts[lemma] += 1
                    pos = token.get("pos")
                    if pos:
                        pos_counts[pos] += 1

    def document_term_matrix(
        self,
        nikaya: str,
        unit: str = "sutta",
        terms: str = "lemmas",
        min_df: int = 1,
        as_dataframe: bool = False,
    ) -> Any:
        """Generate a document-term matrix for analysis.

        Args:
            nikaya: Nikaya ID (dn, mn, sn, an, kn)
            unit: Document unit - "sutta" or "segment"
            terms: Term type - "lemmas" or "words"
            min_df: Minimum document frequency (exclude rare terms)
            as_dataframe: If True, return pandas DataFrame

        Returns:
            scipy.sparse.csr_matrix (or DataFrame if as_dataframe=True)
            Also returns (matrix, doc_ids, term_ids) tuple if not DataFrame

        Example:
            matrix, doc_ids, terms = canon.document_term_matrix("dn")
            # matrix[i, j] = count of terms[j] in doc_ids[i]
        """
        # Collect term counts per document
        doc_term_counts: dict[str, Counter] = {}
        term_doc_counts: Counter = Counter()  # For filtering by min_df

        nikaya_dir = self.lemmatized_dir / nikaya
        if not nikaya_dir.exists():
            if as_dataframe:
                if not HAS_PANDAS:
                    raise ImportError("pandas required")
                return pd.DataFrame()
            return (None, [], [])

        for json_file in sorted(nikaya_dir.glob("*.json")):
            if json_file.name.startswith("_"):
                continue
            self._collect_dtm_data(json_file, nikaya, unit, terms,
                                  doc_term_counts, term_doc_counts)

        # Filter terms by min_df
        valid_terms = {t for t, count in term_doc_counts.items() if count >= min_df}

        # Build vocabulary (sorted for consistency)
        term_list = sorted(valid_terms)
        term_to_idx = {t: i for i, t in enumerate(term_list)}

        # Build document list
        doc_list = sorted(doc_term_counts.keys())
        doc_to_idx = {d: i for i, d in enumerate(doc_list)}

        if as_dataframe:
            if not HAS_PANDAS:
                raise ImportError("pandas is required for DataFrame output")
            # Build DataFrame directly
            data = []
            for doc_id in doc_list:
                row = {"doc_id": doc_id}
                for term in term_list:
                    row[term] = doc_term_counts[doc_id].get(term, 0)
                data.append(row)
            df = pd.DataFrame(data)
            df = df.set_index("doc_id")
            return df

        # Build sparse matrix
        if not HAS_SCIPY:
            raise ImportError("scipy is required for sparse matrix output. Install with: pip install scipy")

        rows, cols, values = [], [], []
        for doc_id, term_counts in doc_term_counts.items():
            doc_idx = doc_to_idx[doc_id]
            for term, count in term_counts.items():
                if term in term_to_idx:
                    rows.append(doc_idx)
                    cols.append(term_to_idx[term])
                    values.append(count)

        matrix = sparse.csr_matrix(
            (values, (rows, cols)),
            shape=(len(doc_list), len(term_list)),
            dtype=np.int32
        )

        return (matrix, doc_list, term_list)

    def _collect_dtm_data(
        self,
        json_file: Path,
        nikaya: str,
        unit: str,
        terms: str,
        doc_term_counts: dict,
        term_doc_counts: Counter,
    ) -> None:
        """Collect document-term data from a JSON file."""
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        if nikaya in ("dn", "mn"):
            sutta_id = data["id"]
            if unit == "sutta":
                self._count_doc_terms(data.get("segments", []), sutta_id, terms,
                                     doc_term_counts, term_doc_counts)
            else:  # segment
                for segment in data.get("segments", []):
                    self._count_doc_terms([segment], segment["id"], terms,
                                         doc_term_counts, term_doc_counts)

        elif nikaya in ("sn", "an"):
            for sutta_data in data.get("suttas", []):
                sutta_id = sutta_data["id"]
                if unit == "sutta":
                    self._count_doc_terms(sutta_data.get("segments", []), sutta_id, terms,
                                         doc_term_counts, term_doc_counts)
                else:
                    for segment in sutta_data.get("segments", []):
                        self._count_doc_terms([segment], segment["id"], terms,
                                             doc_term_counts, term_doc_counts)

        elif nikaya == "kn":
            if "items" in data:
                for item in data["items"]:
                    item_id = item["id"]
                    if unit == "sutta":
                        self._count_doc_terms(item.get("segments", []), item_id, terms,
                                             doc_term_counts, term_doc_counts)
                    else:
                        for segment in item.get("segments", []):
                            self._count_doc_terms([segment], segment["id"], terms,
                                                 doc_term_counts, term_doc_counts)
            else:
                sutta_id = data["id"]
                if unit == "sutta":
                    self._count_doc_terms(data.get("segments", []), sutta_id, terms,
                                         doc_term_counts, term_doc_counts)
                else:
                    for segment in data.get("segments", []):
                        self._count_doc_terms([segment], segment["id"], terms,
                                             doc_term_counts, term_doc_counts)

    def _count_doc_terms(
        self,
        segments: list,
        doc_id: str,
        terms: str,
        doc_term_counts: dict,
        term_doc_counts: Counter,
    ) -> None:
        """Count terms in segments for a document."""
        if doc_id not in doc_term_counts:
            doc_term_counts[doc_id] = Counter()

        seen_terms = set()
        for segment in segments:
            for token in segment.get("tokens", []):
                if terms == "lemmas":
                    term = token.get("lemma")
                else:
                    term = token.get("word")

                if term:
                    doc_term_counts[doc_id][term] += 1
                    seen_terms.add(term)

        # Update document frequency counts
        for term in seen_terms:
            term_doc_counts[term] += 1

    def export_vocabulary(self, nikaya: str, output_path: str) -> None:
        """Export vocabulary to CSV.

        Args:
            nikaya: Nikaya ID
            output_path: Output file path (.csv)
        """
        stats = self.get_vocabulary(nikaya=nikaya, top_n=999999)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write("lemma,count\n")
            for lemma, count in sorted(stats.lemma_counts.items(),
                                      key=lambda x: -x[1]):
                # Escape commas in lemmas
                if "," in lemma:
                    lemma = f'"{lemma}"'
                f.write(f"{lemma},{count}\n")

    def export_dtm(
        self,
        nikaya: str,
        output_path: str,
        unit: str = "sutta",
        terms: str = "lemmas",
        min_df: int = 2,
    ) -> None:
        """Export document-term matrix to CSV.

        Args:
            nikaya: Nikaya ID
            output_path: Output file path (.csv)
            unit: Document unit ("sutta" or "segment")
            terms: Term type ("lemmas" or "words")
            min_df: Minimum document frequency
        """
        if not HAS_PANDAS:
            raise ImportError("pandas is required for CSV export")

        df = self.document_term_matrix(nikaya, unit, terms, min_df, as_dataframe=True)
        df.to_csv(output_path)
