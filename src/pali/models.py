"""Data models for the Pāli Canon library.

Uses slots=True for ~40% memory reduction when processing millions of tokens.
Requires Python 3.10+.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass(slots=True)
class Token:
    """A single lemmatized token."""
    word: str
    lemma: Optional[str] = None
    pos: Optional[str] = None
    root: Optional[str] = None
    sandhi: Optional[list[str]] = None
    components: Optional[list[dict]] = None


@dataclass(slots=True)
class Segment:
    """A single text segment (roughly a sentence)."""
    id: str
    pali: str
    tokens: Optional[list[Token]] = None

    @classmethod
    def from_dict(cls, data: dict, include_tokens: bool = True) -> "Segment":
        """Create Segment from JSON dict."""
        tokens = None
        if include_tokens and "tokens" in data:
            tokens = [
                Token(
                    word=t["word"],
                    lemma=t.get("lemma"),
                    pos=t.get("pos"),
                    root=t.get("root"),
                    sandhi=t.get("sandhi"),
                    components=t.get("components"),
                )
                for t in data["tokens"]
            ]
        return cls(
            id=data["id"],
            pali=data["pali"],
            tokens=tokens,
        )


@dataclass(slots=True)
class Sutta:
    """A complete sutta/discourse."""
    id: str
    title_pali: Optional[str] = None
    title_eng: Optional[str] = None
    collection: Optional[str] = None
    vagga: Optional[str] = None
    pts: Optional[str] = None
    segments: list[Segment] = field(default_factory=list)

    @property
    def segment_count(self) -> int:
        """Number of segments."""
        return len(self.segments)

    @property
    def word_count(self) -> int:
        """Total word count."""
        count = 0
        for seg in self.segments:
            if seg.tokens:
                count += len(seg.tokens)
            else:
                # Rough estimate from text
                count += len(seg.pali.split())
        return count

    @property
    def text(self) -> str:
        """Full text as single string."""
        return "\n".join(seg.pali for seg in self.segments)

    @classmethod
    def from_dict(cls, data: dict, include_tokens: bool = True) -> "Sutta":
        """Create Sutta from JSON dict."""
        segments = [
            Segment.from_dict(s, include_tokens=include_tokens)
            for s in data.get("segments", [])
        ]
        return cls(
            id=data["id"],
            title_pali=data.get("title_pali"),
            title_eng=data.get("title_eng"),
            collection=data.get("collection"),
            vagga=data.get("vagga"),
            pts=data.get("pts"),
            segments=segments,
        )


@dataclass(slots=True)
class SuttaInfo:
    """Summary info for a sutta (without full text)."""
    id: str
    title_pali: Optional[str] = None
    title_eng: Optional[str] = None
    vagga: Optional[str] = None
    pts: Optional[str] = None
    segment_count: Optional[int] = None


@dataclass(slots=True)
class NikayaInfo:
    """Summary info for a nikāya collection."""
    id: str
    name_pali: str
    name_eng: str
    sutta_count: int
    segment_count: int
