"""Tests for pali.models — data model classes."""

import pytest
from pali.models import Token, Segment, Sutta, SuttaInfo, NikayaInfo


# =========================================================================
# Token
# =========================================================================

class TestToken:
    def test_minimal_construction(self):
        t = Token(word="dhamma")
        assert t.word == "dhamma"
        assert t.lemma is None
        assert t.pos is None
        assert t.root is None
        assert t.sandhi is None
        assert t.components is None

    def test_full_construction(self):
        t = Token(word="dhammaṃ", lemma="dhamma", pos="noun",
                  root="√dhar", sandhi=None, components=None)
        assert t.lemma == "dhamma"
        assert t.pos == "noun"
        assert t.root == "√dhar"

    def test_to_dict_minimal(self):
        t = Token(word="me")
        d = t.to_dict()
        assert d == {"word": "me"}
        assert "lemma" not in d
        assert "pos" not in d

    def test_to_dict_full(self):
        t = Token(word="dhammaṃ", lemma="dhamma", pos="noun", root="√dhar")
        d = t.to_dict()
        assert d == {"word": "dhammaṃ", "lemma": "dhamma", "pos": "noun", "root": "√dhar"}

    def test_to_dict_sandhi(self):
        t = Token(
            word="dhammañca",
            sandhi=["dhammaṃ", "ca"],
            components=[
                {"word": "dhammaṃ", "lemma": "dhamma", "pos": "noun"},
                {"word": "ca", "lemma": "ca", "pos": "ind"},
            ]
        )
        d = t.to_dict()
        assert "sandhi" in d
        assert "components" in d
        assert d["sandhi"] == ["dhammaṃ", "ca"]
        assert len(d["components"]) == 2

    def test_to_dict_excludes_none(self):
        t = Token(word="evaṃ", lemma="evaṃ", pos="ind")
        d = t.to_dict()
        assert "root" not in d
        assert "sandhi" not in d
        assert "components" not in d


# =========================================================================
# Segment
# =========================================================================

class TestSegment:
    def test_construction(self):
        s = Segment(id="dn1:1.1", pali="Evaṃ me sutaṃ.")
        assert s.id == "dn1:1.1"
        assert s.pali == "Evaṃ me sutaṃ."
        assert s.tokens is None

    def test_from_dict_no_tokens(self):
        data = {"id": "dn1:1.1", "pali": "Evaṃ me sutaṃ."}
        s = Segment.from_dict(data, include_tokens=False)
        assert s.id == "dn1:1.1"
        assert s.pali == "Evaṃ me sutaṃ."
        assert s.tokens is None

    def test_from_dict_with_tokens(self):
        data = {
            "id": "dn1:1.1",
            "pali": "Evaṃ me sutaṃ.",
            "tokens": [
                {"word": "evaṃ", "lemma": "evaṃ", "pos": "ind"},
                {"word": "me", "lemma": "ahaṃ", "pos": "pron"},
                {"word": "sutaṃ", "lemma": "suṇāti", "pos": "pp"},
            ]
        }
        s = Segment.from_dict(data, include_tokens=True)
        assert len(s.tokens) == 3
        assert s.tokens[0].word == "evaṃ"
        assert s.tokens[1].lemma == "ahaṃ"

    def test_from_dict_include_tokens_but_none_present(self):
        data = {"id": "dn1:1.1", "pali": "Evaṃ me sutaṃ."}
        s = Segment.from_dict(data, include_tokens=True)
        assert s.tokens is None

    def test_from_dict_skip_tokens(self):
        data = {
            "id": "dn1:1.1",
            "pali": "text",
            "tokens": [{"word": "text", "lemma": "text"}]
        }
        s = Segment.from_dict(data, include_tokens=False)
        assert s.tokens is None


# =========================================================================
# Sutta
# =========================================================================

class TestSutta:
    def test_defaults(self):
        s = Sutta(id="dn1")
        assert s.title_pali is None
        assert s.title_eng is None
        assert s.collection is None
        assert s.vagga is None
        assert s.pts is None
        assert s.segments == []

    def test_segment_count(self):
        s = Sutta(
            id="dn1",
            segments=[
                Segment(id="dn1:1.1", pali="A"),
                Segment(id="dn1:1.2", pali="B"),
            ]
        )
        assert s.segment_count == 2

    def test_word_count_with_tokens(self):
        s = Sutta(
            id="dn1",
            segments=[
                Segment(
                    id="dn1:1.1",
                    pali="Evaṃ me sutaṃ",
                    tokens=[
                        Token(word="evaṃ"),
                        Token(word="me"),
                        Token(word="sutaṃ"),
                    ]
                ),
            ]
        )
        assert s.word_count == 3

    def test_word_count_without_tokens(self):
        s = Sutta(
            id="dn1",
            segments=[
                Segment(id="dn1:1.1", pali="Evaṃ me sutaṃ"),
            ]
        )
        # Falls back to split-based counting
        assert s.word_count == 3

    def test_text_property(self):
        s = Sutta(
            id="dn1",
            segments=[
                Segment(id="dn1:1.1", pali="Line one."),
                Segment(id="dn1:1.2", pali="Line two."),
            ]
        )
        assert s.text == "Line one.\nLine two."

    def test_from_dict(self):
        data = {
            "id": "dn1",
            "title_pali": "Brahmajālasutta",
            "title_eng": "The Net of Views",
            "collection": "dn",
            "vagga": "Sīlakkhandhavagga",
            "pts": "DN i 1",
            "segments": [
                {"id": "dn1:1.1", "pali": "Evaṃ me sutaṃ."}
            ]
        }
        s = Sutta.from_dict(data)
        assert s.id == "dn1"
        assert s.title_pali == "Brahmajālasutta"
        assert s.title_eng == "The Net of Views"
        assert s.collection == "dn"
        assert s.vagga == "Sīlakkhandhavagga"
        assert s.pts == "DN i 1"
        assert len(s.segments) == 1

    def test_from_dict_minimal(self):
        data = {"id": "test1", "segments": []}
        s = Sutta.from_dict(data)
        assert s.id == "test1"
        assert s.segments == []


# =========================================================================
# SuttaInfo and NikayaInfo
# =========================================================================

class TestSuttaInfo:
    def test_construction(self):
        si = SuttaInfo(id="dn1", title_pali="Brahmajālasutta")
        assert si.id == "dn1"
        assert si.title_pali == "Brahmajālasutta"
        assert si.title_eng is None
        assert si.segment_count is None

    def test_all_fields(self):
        si = SuttaInfo(
            id="dn1",
            title_pali="Brahmajālasutta",
            title_eng="The Net of Views",
            vagga="Sīlakkhandhavagga",
            pts="DN i 1",
            segment_count=662,
        )
        assert si.segment_count == 662


class TestNikayaInfo:
    def test_construction(self):
        ni = NikayaInfo(
            id="dn",
            name_pali="Dīgha Nikāya",
            name_eng="Long Discourses",
            sutta_count=34,
            segment_count=10000,
        )
        assert ni.id == "dn"
        assert ni.name_pali == "Dīgha Nikāya"
        assert ni.sutta_count == 34
