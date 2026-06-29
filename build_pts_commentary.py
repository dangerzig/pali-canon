#!/usr/bin/env python3
"""
Build a PTS-volume-organized edition of the Vinaya & Abhidhamma commentaries
(aṭṭhakathā), from the CST/VRI text, using the PTS volume structure as the
boundary reference. This is the CST TEXT segmented to PTS volume boundaries —
NOT the PTS edition's readings.

Coverage (10 volumes — the complete Vinaya & Abhidhamma aṭṭhakathā):

  Abhidhamma (3, each 1:1):
    abh01a -> Atthasālinī           (Dhammasaṅgaṇī comm., PTS 1 vol, Müller 1897)
    abh02a -> Sammohavinodanī       (Vibhaṅga comm.,      PTS 1 vol, Buddhadatta 1923)
    abh03a -> Pañcappakaraṇaṭṭhakathā(last 5 Abh. books,   PTS 1 vol, Buddhadatta 1956)

  Vinaya — Samantapāsādikā (CST 5 files -> PTS 7 vols, Takakusu & Nagai 1924–47):
    vin01a -> Vols I, II, III   (Suttavibhaṅga comm.: split at two CST section
                                 headers, located via GRETIL samp_1pu–3pu page
                                 markers — see below)
    vin02a1 -> Vol IV  (Pācittiya … Bhikkhunīvibhaṅga comm.)   1:1
    vin02a2 -> Vol V   (Mahāvagga-aṭṭhakathā)                  1:1
    vin02a3 -> Vol VI  (Cūḷavagga-aṭṭhakathā)                  1:1
    vin02a4 -> Vol VII (Parivāra-aṭṭhakathā)                   1:1

Boundary basis for the vin01a split (GRETIL gretil/2_pali/4_comm/samp_Npu.htm,
each file == one PTS volume, carrying [page N] markers):
    PTS Vol II opens at page 285 with the 2nd-Pārājika commentary
        (verse "Dutiyaṃ adutiyena…", then "…Rājagahe viharati")
        -> CST header "2. Dutiyapārājikaṃ".
    PTS Vol III opens at page 517 with the Saṅghādisesa commentary
        (verse "…terasakassāyam apubbapadavaṇṇanā", "Seyyasako")
        -> CST header "2. Saṅghādisesakaṇḍaṃ".
    PTS Vol IV opens at page 735 with the Pācittiya commentary
        ("…musāvādavaggassa… Hatthako") -> start of CST file vin02a1.
CST char shares of the three vin01a parts (37.7 / 31.2 / 31.1 %) track the PTS
page shares of Vols I–III within pp.1–734 (38.7 / 31.6 / 29.7 %).

The build asserts no text is lost and that every boundary anchor (split point or
1:1 colophon) is present and unique.
"""

import csv
import re
import unicodedata
from pathlib import Path

SRC = Path.home() / "pali-canon" / "data" / "vri-raw"
OUT = Path.home() / "pali-canon" / "data" / "pts-commentary"
TOK = re.compile(r"[^a-zA-ZāīūṭḍṇṅñṃḷĀĪŪṬḌṆṄÑṂḶ]+")


def words(text):
    return [t for t in TOK.split(text) if t]


def read(name):
    return unicodedata.normalize("NFC", (SRC / name).read_text(encoding="utf-8-sig"))


def write(out_name, text):
    (OUT / f"{out_name}.txt").write_text(text, encoding="utf-8")


# ---- 1:1 volumes: pts_id, source, out_name, label, basket, tail colophon ----
ONE_TO_ONE = [
    ("Atthasalini",        "abh01a.att.txt",  "Atthasalini",
     "Atthasālinī (Dhammasaṅgaṇī-aṭṭhakathā)", "abhidhamma",
     "Aṭṭhasālinī nāma"),
    ("Sammohavinodani",    "abh02a.att.txt",  "Sammohavinodani",
     "Sammohavinodanī (Vibhaṅga-aṭṭhakathā)", "abhidhamma",
     "Sammohavinodanī nāma vibhaṅga-aṭṭhakathā niṭṭhitā"),
    ("Pancappakaranatthakatha", "abh03a.att.txt", "Pancappakaranatthakatha",
     "Pañcappakaraṇaṭṭhakathā (Dhātukathā…Paṭṭhāna comm.)", "abhidhamma",
     "Abhidhammapiṭaka-aṭṭhakathā niṭṭhitā"),
    ("Samantapasadika.IV",  "vin02a1.att.txt", "Samantapasadika_IV_Pacittiya_Bhikkhunivibhanga",
     "Samantapāsādikā IV (Pācittiya…Bhikkhunīvibhaṅga-aṭṭhakathā)", "vinaya",
     "Ubhatovibhaṅgaṭṭhakathā niṭṭhitā"),
    ("Samantapasadika.V",   "vin02a2.att.txt", "Samantapasadika_V_Mahavagga",
     "Samantapāsādikā V (Mahāvagga-aṭṭhakathā)", "vinaya",
     "Mahāvagga-aṭṭhakathā niṭṭhitā"),
    ("Samantapasadika.VI",  "vin02a3.att.txt", "Samantapasadika_VI_Cullavagga",
     "Samantapāsādikā VI (Cūḷavagga-aṭṭhakathā)", "vinaya",
     "Cūḷavagga-aṭṭhakathā niṭṭhitā"),
    ("Samantapasadika.VII", "vin02a4.att.txt", "Samantapasadika_VII_Parivara",
     "Samantapāsādikā VII (Parivāra-aṭṭhakathā)", "vinaya",
     "Vinaya-aṭṭhakathā niṭṭhitā"),
]


def build_one_to_one(manifest):
    total = 0
    for pid, src, out_name, label, basket, colophon in ONE_TO_ONE:
        text = read(src)
        tail = "".join(text.split())[-400:]
        assert "".join(colophon.split()) in tail, f"{src}: colophon not in tail"
        n = len(words(text))
        write(out_name, text)
        manifest.append([pid, label, basket, src,
                         "1:1 (CST file = PTS volume; colophon-confirmed)"])
        total += n
        print(f"  {pid:22} <- {src:15} ({n:>7,} words)  {label}")
    return total


def build_samantapasadika_I_III(manifest):
    """Split CST vin01a into PTS Samantapāsādikā Vols I, II, III.

    Cut at two CST section headers that the GRETIL samp_2pu / samp_3pu page
    markers identify as the PTS Vol II (p.285) and Vol III (p.517) openings.
    Each anchor must occur exactly once.
    """
    src = "vin01a.att.txt"
    text = read(src)
    anchors = [
        (r"\n\s*2\.\s*Dutiyapārājikaṃ", "Vol II start (2nd Pārājika, PTS p.285)"),
        (r"\n\s*2\.\s*Saṅghādisesakaṇḍaṃ", "Vol III start (Saṅghādisesa, PTS p.517)"),
    ]
    cuts = []
    for pat, desc in anchors:
        ms = list(re.finditer(pat, text))
        assert len(ms) == 1, f"vin01a: anchor {desc!r} matched {len(ms)} times (need 1)"
        cuts.append(ms[0].start())
    assert cuts[0] < cuts[1], "vin01a anchors out of order"

    parts = [
        ("Samantapasadika.I",   "Samantapasadika_I_Bahiranidana_Parajika_I",
         "Samantapāsādikā I (Bāhiranidāna + Pārājika I-aṭṭhakathā)",
         text[:cuts[0]]),
        ("Samantapasadika.II",  "Samantapasadika_II_Parajika_II-IV",
         "Samantapāsādikā II (Pārājika II–IV-aṭṭhakathā)",
         text[cuts[0]:cuts[1]]),
        ("Samantapasadika.III", "Samantapasadika_III_Sanghadisesa_Nissaggiya",
         "Samantapāsādikā III (Saṅghādisesa…Nissaggiya-aṭṭhakathā)",
         text[cuts[1]:]),
    ]
    # sanity: content checks on each part
    assert "2. Dutiyapārājikaṃ" in parts[1][3][:80], "Vol II must open at 2nd Pārājika"
    assert "Saṅghādisesakaṇḍaṃ" in parts[2][3][:120], "Vol III must open at Saṅghādisesa"
    vol3_tail = "".join(parts[2][3].split())[-400:]
    assert "Nissaggiyavaṇṇanāniṭṭhitā" in vol3_tail, "Vol III must end at Nissaggiya colophon"

    nw = 0
    for pid, out_name, label, chunk in parts:
        assert words(chunk), f"{pid}: empty"
        write(out_name, chunk.strip() + "\n")
        c = len(words(chunk))
        nw += c
        manifest.append([pid, label, "vinaya", src,
                         "split of vin01a at CST section header; PTS boundary from "
                         "GRETIL samp_{2,3}pu page markers (p.285 / p.517)"])
        print(f"  {pid:22} <- {src} [split] ({c:>7,} words)  {label}")
    assert nw == len(words(text)), f"vin01a split word loss: {nw} != {len(words(text))}"
    return nw


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = []
    print(f"Building PTS-organized commentary (Vin+Abh, 10 volumes) -> {OUT}\n")
    t1 = build_samantapasadika_I_III(manifest)
    t2 = build_one_to_one(manifest)

    # Sort manifest into a sensible reading order for the CSV.
    order = {pid: i for i, pid in enumerate([
        "Samantapasadika.I", "Samantapasadika.II", "Samantapasadika.III",
        "Samantapasadika.IV", "Samantapasadika.V", "Samantapasadika.VI",
        "Samantapasadika.VII", "Atthasalini", "Sammohavinodani",
        "Pancappakaranatthakatha"])}
    manifest.sort(key=lambda r: order.get(r[0], 99))
    with open(OUT / "MANIFEST.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["pts_id", "name", "basket", "cst_source", "boundary_basis"])
        w.writerows(manifest)

    # Global text-conservation check: output words == CST source words.
    src_files = ["vin01a", "vin02a1", "vin02a2", "vin02a3", "vin02a4",
                 "abh01a", "abh02a", "abh03a"]
    src_words = sum(len(words(read(f + ".att.txt"))) for f in src_files)
    out_words = sum(len(words(p.read_text(encoding="utf-8")))
                    for p in OUT.glob("*.txt"))
    print(f"\nWrote {len(manifest)} volumes + MANIFEST.csv")
    print(f"text conservation: {out_words:,} == {src_words:,}  {out_words == src_words}")
    assert out_words == src_words, "TEXT LOSS"


if __name__ == "__main__":
    main()
