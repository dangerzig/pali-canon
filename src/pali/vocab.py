"""Vocabulary statistics and document-term matrices."""

import csv
from dataclasses import dataclass, field
from typing import Optional, Any
from pathlib import Path
from collections import Counter
import json

from .text import parse_sutta_id, iter_file_segments
from .store import Store, NIKAYAS

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
        self._store = Store(data_dir)

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
        token_stats = {"total": 0, "with_lemma": 0}

        if sutta_id:
            # Single sutta
            self._count_sutta(sutta_id, lemma_counts, pos_counts, token_stats)
        elif nikaya:
            # Entire nikaya
            nikaya_dir = self.lemmatized_dir / nikaya
            if nikaya_dir.exists():
                for json_file in nikaya_dir.glob("*.json"):
                    if json_file.name.startswith("_"):
                        continue
                    self._count_file(json_file, nikaya, lemma_counts, pos_counts, token_stats)

        total_tokens = token_stats["total"]
        tokens_with_lemma = token_stats["with_lemma"]

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

    def _count_sutta(self, sutta_id: str, lemma_counts: Counter, pos_counts: Counter,
                     token_stats: dict) -> None:
        """Count lemmas in a single sutta."""
        nikaya = parse_sutta_id(sutta_id)
        if not nikaya:
            return

        sutta = self._store.get_sutta(sutta_id, lemmatized=True, include_tokens=True)
        if sutta:
            for segment in sutta.segments:
                if segment.tokens:
                    for token in segment.tokens:
                        token_stats["total"] += 1
                        if token.lemma:
                            token_stats["with_lemma"] += 1
                            lemma_counts[token.lemma] += 1
                            if token.pos:
                                pos_counts[token.pos] += 1
                        elif token.sandhi or token.components:
                            # Sandhi-decomposed tokens are also resolved
                            token_stats["with_lemma"] += 1
                            if token.components:
                                for comp in token.components:
                                    comp_lemma = comp.get("lemma")
                                    if comp_lemma:
                                        lemma_counts[comp_lemma] += 1
                                        comp_pos = comp.get("pos")
                                        if comp_pos:
                                            pos_counts[comp_pos] += 1

    def _count_file(self, json_file: Path, nikaya: str,
                   lemma_counts: Counter, pos_counts: Counter,
                   token_stats: dict) -> None:
        """Count lemmas in a JSON file."""
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        for _doc_id, segments in iter_file_segments(data, nikaya):
            self._count_segments(segments, lemma_counts, pos_counts, token_stats)

    def _count_segments(self, segments: list, lemma_counts: Counter, pos_counts: Counter,
                       token_stats: dict) -> None:
        """Count lemmas in a list of segments."""
        for segment in segments:
            for token in segment.get("tokens", []):
                token_stats["total"] += 1
                lemma = token.get("lemma")
                if lemma:
                    token_stats["with_lemma"] += 1
                    lemma_counts[lemma] += 1
                    pos = token.get("pos")
                    if pos:
                        pos_counts[pos] += 1
                elif token.get("sandhi") or token.get("components"):
                    # Sandhi-decomposed tokens are also resolved
                    token_stats["with_lemma"] += 1
                    # Count lemmas from components
                    for comp in token.get("components", []):
                        comp_lemma = comp.get("lemma")
                        if comp_lemma:
                            lemma_counts[comp_lemma] += 1
                            comp_pos = comp.get("pos")
                            if comp_pos:
                                pos_counts[comp_pos] += 1

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
            raise ValueError(f"Lemmatized data not found for nikaya '{nikaya}' at {nikaya_dir}")

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

        for doc_id, segments in iter_file_segments(data, nikaya):
            if unit == "sutta":
                self._count_doc_terms(segments, doc_id, terms,
                                     doc_term_counts, term_doc_counts)
            else:  # segment
                for segment in segments:
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

        with open(output_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["lemma", "count"])
            for lemma, count in sorted(stats.lemma_counts.items(),
                                      key=lambda x: -x[1]):
                writer.writerow([lemma, count])

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

    # -------------------------------------------------------------------------
    # Tipitaka R package export methods
    # -------------------------------------------------------------------------

    def export_tipitaka_raw(self, output_path: str, use_lemmas: bool = True) -> None:
        """Export data in tipitaka_raw format (text per nikaya).

        Creates CSV with columns: text, book, book_name
        One row per nikaya with full text.

        Args:
            output_path: Output CSV path
            use_lemmas: If True, use lemmatized text
        """
        store = Store(self.data_dir)
        rows = []

        nikaya_names = {
            "dn": "Digha Nikaya",
            "mn": "Majjhima Nikaya",
            "sn": "Samyutta Nikaya",
            "an": "Anguttara Nikaya",
            "kn": "Khuddaka Nikaya",
        }

        for nikaya in ["dn", "mn", "sn", "an", "kn"]:
            texts = []
            for sutta_info in store.list_suttas(nikaya, lemmatized=use_lemmas):
                sutta = store.get_sutta(sutta_info.id, lemmatized=use_lemmas, include_tokens=False)
                if sutta:
                    texts.append(sutta.text)

            full_text = "\n\n".join(texts)
            rows.append({
                "book": nikaya,
                "book_name": nikaya_names.get(nikaya, nikaya.upper()),
                "text": full_text,
            })

        with open(output_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["book", "book_name", "text"])
            for row in rows:
                writer.writerow([row["book"], row["book_name"], row["text"]])

    def export_tipitaka_long(
        self,
        output_path: str,
        use_lemmas: bool = True,
        by_sutta: bool = False,
    ) -> None:
        """Export data in tipitaka_long format (word frequencies).

        Creates CSV with columns: word, n, total, freq, book
        - word: the word/lemma
        - n: count of this word in this book
        - total: total words in this book
        - freq: n/total
        - book: nikaya or sutta ID

        Args:
            output_path: Output CSV path
            use_lemmas: If True, count lemmas instead of surface forms
            by_sutta: If True, group by sutta; otherwise by nikaya
        """
        rows = []

        for nikaya in ["dn", "mn", "sn", "an", "kn"]:
            nikaya_dir = self.lemmatized_dir / nikaya
            if not nikaya_dir.exists():
                continue

            if by_sutta:
                # Count per sutta
                doc_counts: dict[str, Counter] = {}
                for json_file in sorted(nikaya_dir.glob("*.json")):
                    if json_file.name.startswith("_"):
                        continue
                    self._collect_tipitaka_counts(json_file, nikaya, use_lemmas, doc_counts, by_sutta=True)

                for doc_id, word_counts in doc_counts.items():
                    total = sum(word_counts.values())
                    for word, n in word_counts.items():
                        rows.append({
                            "word": word,
                            "n": n,
                            "total": total,
                            "freq": n / total if total > 0 else 0,
                            "book": doc_id,
                        })
            else:
                # Count per nikaya
                word_counts: Counter = Counter()
                for json_file in sorted(nikaya_dir.glob("*.json")):
                    if json_file.name.startswith("_"):
                        continue
                    self._collect_tipitaka_counts(json_file, nikaya, use_lemmas, {"_": word_counts}, by_sutta=False)

                total = sum(word_counts.values())
                for word, n in word_counts.items():
                    rows.append({
                        "word": word,
                        "n": n,
                        "total": total,
                        "freq": n / total if total > 0 else 0,
                        "book": nikaya,
                    })

        with open(output_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["word", "n", "total", "freq", "book"])
            for row in rows:
                writer.writerow([row["word"], row["n"], row["total"],
                                f'{row["freq"]:.10f}', row["book"]])

    def export_tipitaka_wide(
        self,
        output_path: str,
        use_lemmas: bool = True,
        by_sutta: bool = False,
        min_freq: int = 5,
    ) -> None:
        """Export data in tipitaka_wide format (word frequency matrix).

        Creates CSV with books as rows and words as columns.
        Cell values are word frequencies (count / total).

        Args:
            output_path: Output CSV path
            use_lemmas: If True, count lemmas instead of surface forms
            by_sutta: If True, one row per sutta; otherwise per nikaya
            min_freq: Minimum total frequency to include word
        """
        # Collect all counts
        doc_counts: dict[str, Counter] = {}
        doc_totals: dict[str, int] = {}

        for nikaya in ["dn", "mn", "sn", "an", "kn"]:
            nikaya_dir = self.lemmatized_dir / nikaya
            if not nikaya_dir.exists():
                continue

            if by_sutta:
                for json_file in sorted(nikaya_dir.glob("*.json")):
                    if json_file.name.startswith("_"):
                        continue
                    self._collect_tipitaka_counts(json_file, nikaya, use_lemmas, doc_counts, by_sutta=True)
            else:
                if nikaya not in doc_counts:
                    doc_counts[nikaya] = Counter()
                for json_file in sorted(nikaya_dir.glob("*.json")):
                    if json_file.name.startswith("_"):
                        continue
                    self._collect_tipitaka_counts(json_file, nikaya, use_lemmas, {nikaya: doc_counts[nikaya]}, by_sutta=False)

        # Calculate totals
        for doc_id, counts in doc_counts.items():
            doc_totals[doc_id] = sum(counts.values())

        # Find words meeting minimum frequency
        all_word_counts: Counter = Counter()
        for counts in doc_counts.values():
            all_word_counts.update(counts)

        vocab = sorted([w for w, c in all_word_counts.items() if c >= min_freq])

        # Write wide format
        with open(output_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["book"] + vocab)

            for doc_id in sorted(doc_counts.keys()):
                total = doc_totals[doc_id]
                row = [doc_id]
                for word in vocab:
                    count = doc_counts[doc_id].get(word, 0)
                    freq = count / total if total > 0 else 0
                    row.append(f"{freq:.10f}")
                writer.writerow(row)

    def export_tipitaka_suttas_long(self, output_path: str, use_lemmas: bool = True) -> None:
        """Export sutta-level word frequencies (new format for critical edition).

        Creates CSV with columns: word, n, total, freq, sutta, nikaya

        Args:
            output_path: Output CSV path
            use_lemmas: If True, count lemmas instead of surface forms
        """
        rows = []

        for nikaya in ["dn", "mn", "sn", "an", "kn"]:
            nikaya_dir = self.lemmatized_dir / nikaya
            if not nikaya_dir.exists():
                continue

            doc_counts: dict[str, Counter] = {}
            for json_file in sorted(nikaya_dir.glob("*.json")):
                if json_file.name.startswith("_"):
                    continue
                self._collect_tipitaka_counts(json_file, nikaya, use_lemmas, doc_counts, by_sutta=True)

            for sutta_id, word_counts in doc_counts.items():
                total = sum(word_counts.values())
                for word, n in word_counts.items():
                    rows.append({
                        "word": word,
                        "n": n,
                        "total": total,
                        "freq": n / total if total > 0 else 0,
                        "sutta": sutta_id,
                        "nikaya": nikaya,
                    })

        with open(output_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["word", "n", "total", "freq", "sutta", "nikaya"])
            for row in rows:
                writer.writerow([row["word"], row["n"], row["total"],
                                f'{row["freq"]:.10f}', row["sutta"], row["nikaya"]])

    def _collect_tipitaka_counts(
        self,
        json_file: Path,
        nikaya: str,
        use_lemmas: bool,
        doc_counts: dict,
        by_sutta: bool,
    ) -> None:
        """Collect word/lemma counts from a JSON file."""
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        def count_segments(segments: list, target_counter: Counter) -> None:
            for segment in segments:
                for token in segment.get("tokens", []):
                    term = token.get("lemma") if use_lemmas else token.get("word")
                    if term:
                        target_counter[term] += 1

        for doc_id, segments in iter_file_segments(data, nikaya):
            if by_sutta:
                if doc_id not in doc_counts:
                    doc_counts[doc_id] = Counter()
                count_segments(segments, doc_counts[doc_id])
            else:
                target = list(doc_counts.values())[0]
                count_segments(segments, target)
