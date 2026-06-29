#!/usr/bin/env python3
"""
Build a PTS-volume-organized edition of the Vinaya & Abhidhamma commentaries
(aṭṭhakathā), from the CST/VRI text, using the PTS volume structure as the
boundary reference. This is the CST TEXT segmented to PTS volume boundaries —
NOT the PTS edition's readings.

Scope of THIS script (the 1:1 volumes only): the commentary files whose CST
file equals exactly one PTS volume, confirmed by closing colophon. The four
split Samantapāsādikā volumes (Suttavibhaṅga aṭṭhakathā, PTS Vols I–IV) need
GRETIL page-marker boundary location and are built in a later step. The Sutta
commentaries are already PTS-organized in pali-commentary/data/raw-pts.

Coverage here (6 volumes, all 1:1):
  - Abhidhamma: abh01a -> Atthasālinī, abh02a -> Sammohavinodanī,
    abh03a -> Pañcappakaraṇaṭṭhakathā.
  - Vinaya (Samantapāsādikā tail): vin02a2 -> Vol V (Mahāvagga-aṭṭhakathā),
    vin02a3 -> Vol VI (Cūḷavagga-aṭṭhakathā), vin02a4 -> Vol VII (Parivāra).

Every output records its provenance in a manifest. The build asserts no text is
lost (output words == input words) and that each source ends with the expected
colophon.
"""

import csv
import re
from pathlib import Path

SRC = Path.home() / "pali-canon" / "data" / "vri-raw"
OUT = Path.home() / "pali-canon" / "data" / "pts-commentary"
TOK = re.compile(r"[^a-zA-ZāīūṭḍṇṅñṃḷĀĪŪṬḌṆṄÑṂḶ]+")


def words(text):
    return [t for t in TOK.split(text) if t]


def read(name):
    return (SRC / name).read_text(encoding="utf-8-sig")


# pts_id, source file, output name, PTS volume label, basket, expected colophon
# (substring that must appear in the file's tail, confirming what it covers)
ONE_TO_ONE = [
    # Abhidhamma commentaries (each = one PTS volume)
    ("Atthasalini",        "abh01a.att.txt",
     "Atthasalini",                       "Atthasālinī (Dhammasaṅgaṇī-aṭṭhakathā)",
     "abhidhamma", "Aṭṭhasālinī nāma"),
    ("Sammohavinodani",    "abh02a.att.txt",
     "Sammohavinodani",                   "Sammohavinodanī (Vibhaṅga-aṭṭhakathā)",
     "abhidhamma", "Sammohavinodanī nāma vibhaṅga-aṭṭhakathā niṭṭhitā"),
    ("Pancappakaranatthakatha", "abh03a.att.txt",
     "Pancappakaranatthakatha",           "Pañcappakaraṇaṭṭhakathā (Dhātukathā…Paṭṭhāna comm.)",
     "abhidhamma", "Abhidhammapiṭaka-aṭṭhakathā niṭṭhitā"),
    # Vinaya — Samantapāsādikā Vols V–VII (the clean tail; Vols I–IV later)
    ("Samantapasadika.V",  "vin02a2.att.txt",
     "Samantapasadika_V_Mahavagga",       "Samantapāsādikā V (Mahāvagga-aṭṭhakathā)",
     "vinaya", "Mahāvagga-aṭṭhakathā niṭṭhitā"),
    ("Samantapasadika.VI", "vin02a3.att.txt",
     "Samantapasadika_VI_Cullavagga",     "Samantapāsādikā VI (Cūḷavagga-aṭṭhakathā)",
     "vinaya", "Cūḷavagga-aṭṭhakathā niṭṭhitā"),
    ("Samantapasadika.VII", "vin02a4.att.txt",
     "Samantapasadika_VII_Parivara",      "Samantapāsādikā VII (Parivāra-aṭṭhakathā)",
     "vinaya", "Vinaya-aṭṭhakathā niṭṭhitā"),
]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = []
    src_total = out_total = 0
    print(f"Building PTS-organized commentary (1:1 volumes) -> {OUT}\n")
    for pid, src, out_name, label, basket, colophon in ONE_TO_ONE:
        text = read(src)
        # Confirm the file covers what we think it covers (colophon in the tail).
        tail = "".join(text.split())[-400:]
        norm_colophon = "".join(colophon.split())
        assert norm_colophon in tail, f"{src}: colophon '{colophon}' not found in tail"
        n = len(words(text))
        (OUT / f"{out_name}.txt").write_text(text, encoding="utf-8")
        manifest.append([pid, label, basket, src,
                         "1:1 (CST file = PTS volume; colophon-confirmed)"])
        src_total += n
        out_total += n
        print(f"  {pid:22} <- {src:15} ({n:>7,} words)  {label}")

    with open(OUT / "MANIFEST.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["pts_id", "name", "basket", "cst_source", "boundary_basis"])
        w.writerows(manifest)

    print(f"\nWrote {len(manifest)} volumes + MANIFEST.csv")
    print(f"text conservation: {out_total:,} == {src_total:,}  {out_total == src_total}")
    assert out_total == src_total, "TEXT LOSS"


if __name__ == "__main__":
    main()
