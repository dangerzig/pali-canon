#!/usr/bin/env python3
"""
Build a PTS-volume-organized edition of the canonical Tipiṭaka (mūla),
from the CST/VRI text, using GRETIL's PTS volume structure as the boundary
reference. This is the CST TEXT segmented to PTS volume boundaries — NOT the
PTS edition's text.

Coverage here (canon mūla):
  - Vinaya: 5 CST files -> 5 PTS volumes (1:1, reordered).
  - Abhidhamma single-volume books: 4 CST files -> 4 PTS volumes (1:1).
  - Abhidhamma Yamaka: CST m4+m5+m6 -> 2 PTS volumes, split at the 8th yamaka
    (Cittayamaka), where GRETIL's PTS Yamaka Vol II begins.
  - Sutta: already done in pali-commentary/data/raw-pts (added at assembly).

TODO (harder multi-volume books, separate step): Kathāvatthu (1 CST -> 2 PTS
vols, split at the page where Vol II begins), Paṭṭhāna (5 CST -> several PTS
volumes). Both need GRETIL page-marker boundary location.

Every output records its provenance (source file(s) + boundary basis) in a
manifest, and the build asserts no text is lost (output words == input words).
"""

import csv
import re
from pathlib import Path

SRC = Path.home() / "pali-canon" / "data" / "vri-raw"
SUTTA_PTS = Path.home() / "pali-commentary" / "data" / "raw-pts"  # already PTS-organized
OUT = Path.home() / "pali-canon" / "data" / "pts-canon"
TOK = re.compile(r"[^a-zA-ZāīūṭḍṇṅñṃḷĀĪŪṬḌṆṄÑṂḶ]+")


def words(text):
    return [t for t in TOK.split(text) if t]


def read(name):
    return (SRC / name).read_text(encoding="utf-8-sig")


# 1:1 maps: PTS volume id -> (source file, PTS name, basket)
ONE_TO_ONE = [
    # Vinaya (PTS volume order)
    ("Vin.I",   "vin02m2.mul.txt", "Vinaya I (Mahāvagga)",        "vinaya"),
    ("Vin.II",  "vin02m3.mul.txt", "Vinaya II (Cullavagga)",      "vinaya"),
    ("Vin.III", "vin01m.mul.txt",  "Vinaya III (Suttavibhaṅga, Pārājika)", "vinaya"),
    ("Vin.IV",  "vin02m1.mul.txt", "Vinaya IV (Suttavibhaṅga, Pācittiya)", "vinaya"),
    ("Vin.V",   "vin02m4.mul.txt", "Vinaya V (Parivāra)",         "vinaya"),
    # Abhidhamma single-volume books
    ("Abh.Dhs", "abh01m.mul.txt",  "Dhammasaṅgaṇī",   "abhidhamma"),
    ("Abh.Vbh", "abh02m.mul.txt",  "Vibhaṅga",        "abhidhamma"),
    ("Abh.Dhk", "abh03m1.mul.txt", "Dhātukathā",      "abhidhamma"),
    ("Abh.Pug", "abh03m2.mul.txt", "Puggalapaññatti", "abhidhamma"),
    # Kathāvatthu: PTS paginates it continuously (GRETIL has it as one file,
    # pages 1-628); the 2-volume PTS binding split is not a content boundary,
    # so it is kept as a single unit here.
    ("Abh.Kvu", "abh03m3.mul.txt", "Kathāvatthu", "abhidhamma"),
]

# Paṭṭhāna mapping (TODO, next step). CST: m7,m8=Tikapaṭṭhāna; m9,m10=Duka-
# paṭṭhāna; m11=the combined paṭṭhānas (tikatika, tikaduka, dukatika, dukaduka).
# GRETIL/PTS: Tikapaṭṭhāna Parts I-III + Dukapaṭṭhāna. The Tika I/II/III
# boundaries fall mid-CST and must be located via GRETIL page markers, and the
# m11 combined paṭṭhānas placed; both need verification before emitting.


def split_yamaka(manifest):
    """CST Yamaka (m4+m5+m6) -> PTS Vol I (yamakas 1-7) + Vol II (8-10).

    GRETIL's PTS Yamaka Vol II begins with the Cittayamaka (the 8th yamaka),
    which falls inside CST file abh03m5. Concatenate the three files and split
    at the Cittayamaka heading.
    """
    text = "\n".join(read(f) for f in
                     ("abh03m4.mul.txt", "abh03m5.mul.txt", "abh03m6.mul.txt"))
    # Heading that opens the 8th yamaka. CST marks it '8. Cittayamaka' /
    # 'Cittayamakaṃ'. Split at the first such occurrence.
    m = re.search(r"\n\s*8\s*\.\s*Cittayamak", text) or re.search(r"Cittayamakaṃ", text)
    assert m, "Cittayamaka boundary not found"
    vol1, vol2 = text[:m.start()], text[m.start():]
    assert words(vol1) and words(vol2)
    (OUT / "Yamaka_I.txt").write_text(vol1.strip() + "\n", encoding="utf-8")
    (OUT / "Yamaka_II.txt").write_text(vol2.strip() + "\n", encoding="utf-8")
    # verify no text lost
    assert len(words(vol1)) + len(words(vol2)) == len(words(text)), "Yamaka word loss"
    manifest.append(["Abh.Yam.I", "Yamaka I (yamakas 1-7)", "abhidhamma",
                     "abh03m4+abh03m5", "split before Cittayamaka (GRETIL Vol II start)"])
    manifest.append(["Abh.Yam.II", "Yamaka II (yamakas 8-10)", "abhidhamma",
                     "abh03m5+abh03m6", "Cittayamaka onward"])
    return len(words(text))


def build_patthana(manifest):
    """Paṭṭhāna -> three clean major divisions.

    The full PTS Paṭṭhāna further subdivides the Tikapaṭṭhāna into Parts I–III
    (and organizes the Duka and the combined paṭṭhānas across volumes); those
    fine PTS sub-volume boundaries fall mid-CST and are intricate, so they are
    FLAGGED for expert verification rather than guessed. Here we emit the three
    unambiguous CST-grounded divisions, losing no text.
    """
    groups = [
        ("Abh.Pat.Tika", "Tikapaṭṭhāna", ["abh03m7.mul.txt", "abh03m8.mul.txt"]),
        ("Abh.Pat.Duka", "Dukapaṭṭhāna", ["abh03m9.mul.txt", "abh03m10.mul.txt"]),
        ("Abh.Pat.Comb", "Paṭṭhāna (combined: tikatika, tikaduka, dukatika, dukaduka)",
         ["abh03m11.mul.txt"]),
    ]
    total = 0
    for pid, name, files in groups:
        text = "\n".join(read(f) for f in files)
        out = name.split("(")[0].strip().replace(" ", "_") + ".txt"
        (OUT / out).write_text(text.strip() + "\n", encoding="utf-8")
        total += len(words(text))
        manifest.append([pid, name, "abhidhamma", "+".join(files),
                         "CST major division; PTS sub-volume split PENDING expert review"])
    return total


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = []
    print(f"Building PTS-organized canon (mūla) -> {OUT}\n")
    for vid, src, name, basket in ONE_TO_ONE:
        text = read(src)
        out_name = name.split("(")[0].strip().replace(" ", "_") + ".txt"
        (OUT / out_name).write_text(text, encoding="utf-8")
        manifest.append([vid, name, basket, src, "1:1 (CST file = PTS volume)"])
        print(f"  {vid:9} <- {src:18} ({len(words(text)):>7,} words)  {name}")
    yam_words = split_yamaka(manifest)
    print(f"  Abh.Yam.* <- abh03m4/5/6      ({yam_words:>7,} words)  Yamaka I+II")
    pat_words = build_patthana(manifest)
    print(f"  Abh.Pat.* <- abh03m7..m11     ({pat_words:>7,} words)  Paṭṭhāna (3 divisions)")

    # Sutta basket: already PTS-organized CST text in raw-pts (.mul = canon).
    sutta_words = 0
    sutta_files = sorted(SUTTA_PTS.glob("*.mul.txt"))
    for f in sutta_files:
        text = f.read_text(encoding="utf-8")
        (OUT / f.name).write_text(text, encoding="utf-8")
        sutta_words += len(words(text))
        manifest.append([f.stem, f.stem, "sutta", f"raw-pts/{f.name}",
                         "PTS-organized Sutta (from reorganise_pts.py)"])
    print(f"  Sutta     <- raw-pts (.mul)   ({sutta_words:>7,} words)  "
          f"{len(sutta_files)} volumes")

    with open(OUT / "MANIFEST.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["pts_id", "name", "basket", "cst_source", "boundary_basis"])
        w.writerows(manifest)

    # Text-conservation check per basket (no text lost in reorganization).
    # Vin+Abh: our reorganized output (non-.mul.txt files) vs the CST source.
    cst_vinabh = ["vin01m", "vin02m1", "vin02m2", "vin02m3", "vin02m4",
                  "abh01m", "abh02m", "abh03m1", "abh03m2", "abh03m3",
                  "abh03m4", "abh03m5", "abh03m6",
                  "abh03m7", "abh03m8", "abh03m9", "abh03m10", "abh03m11"]
    src_vinabh = sum(len(words(read(f + ".mul.txt"))) for f in cst_vinabh)
    out_vinabh = sum(len(words(p.read_text(encoding="utf-8")))
                     for p in OUT.glob("*.txt") if not p.name.endswith(".mul.txt"))
    # Sutta: output copies vs raw-pts source.
    src_sutta = sum(len(words(p.read_text(encoding="utf-8")))
                    for p in SUTTA_PTS.glob("*.mul.txt"))
    out_sutta = sum(len(words(p.read_text(encoding="utf-8")))
                    for p in OUT.glob("*.mul.txt"))
    print(f"\nWrote {len(manifest)} volumes + MANIFEST.csv")
    print(f"text conservation  Vin+Abh: {out_vinabh:,} == {src_vinabh:,}  "
          f"{out_vinabh == src_vinabh}")
    print(f"text conservation  Sutta:   {out_sutta:,} == {src_sutta:,}  "
          f"{out_sutta == src_sutta}")
    assert out_vinabh == src_vinabh and out_sutta == src_sutta, "TEXT LOSS"


if __name__ == "__main__":
    main()
