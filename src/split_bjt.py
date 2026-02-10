#!/usr/bin/env python3
"""
Split BJT volume files into per-sutta files matching GRETIL naming conventions.

Usage:
    python split_bjt.py          # Split all nikāyas
    python split_bjt.py dn       # Split DN only
    python split_bjt.py mn sn    # Split MN and SN

Creates per-sutta files alongside existing volume files in data/bjt-parsed/.

Note: BJT sutta counts often differ from GRETIL/PTS because the BJT edition
expands peyyāla (abbreviated repetition series) that PTS keeps condensed.
The collation pipeline matches files by name and skips unmatched ones.
"""

import re
import sys
import json
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
BJT_DIR = DATA_DIR / "bjt-parsed"

try:
    from pali.text import PALI_WORD_PATTERN, tokenize
except ImportError:
    PALI_WORD_PATTERN = re.compile(r'[a-zāīūṭḍṇṅñṃḷ]+', re.IGNORECASE)
    def tokenize(text: str) -> list:
        return PALI_WORD_PATTERN.findall(text.lower())


def save_sutta(output_dir: Path, filename: str, sutta_id, text: str):
    """Save a per-sutta JSON file."""
    words = tokenize(text)
    data = {
        "sutta": sutta_id,
        "text": text.strip(),
        "word_count": len(words),
        "source": "bjt",
    }
    with open(output_dir / filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ==================== DN Splitting ====================

# DN sutta names for title matching (name → absolute DN number)
DN_NAMES = {
    'brahmajāla': 1, 'sāmaññaphala': 2, 'ambaṭṭha': 3,
    'soṇadaṇḍa': 4, 'kūṭadanta': 5, 'mahālī': 6,
    'jāliya': 7, 'sīhanāda': 8, 'kassapasīhanāda': 8,
    'poṭṭhapāda': 9, 'subha': 10,
    'kevaḍḍha': 11, 'kevaṭṭa': 11, 'lohicca': 12, 'tevijja': 13,
    'mahāpadāna': 14, 'mahānidāna': 15, 'mahāparinibbāna': 16,
    'mahāsudassana': 17, 'janavasabha': 18, 'mahāgovinda': 19,
    'mahāsamaya': 20, 'sakkapañha': 21,
    'mahāsatipaṭṭhāna': 22, 'pāyāsirājañña': 23, 'pāyāsi': 23,
    'pāthika': 24, 'udumbarika': 25,
    'cakkavattisīhanāda': 26, 'cakkavatatisīhanāda': 26,
    'aggañña': 27, 'sampasādanīya': 28, 'sampasādaniya': 28,
    'pāsādika': 29,
    'lakkhaṇa': 30, 'sigāla': 31,
    'āṭānāṭiya': 32, 'saṅgīti': 33, 'dasuttara': 34,
}

DN_VOL_RANGES = [(1, 13), (14, 23), (24, 34)]


def split_dn():
    """Split DN volumes using title markers.

    Uses three complementary patterns to find sutta boundaries:
    A) Number on its own line, followed by sutta title after newline(s)
    B) Number and sutta title on the same line
    C) Numberless sutta title (uses name lookup from DN_NAMES)
    """
    output_dir = BJT_DIR / "dn"
    print("Splitting DN...")

    total = 0
    for vol_idx, (sutta_start, sutta_end) in enumerate(DN_VOL_RANGES):
        vol_num = vol_idx + 1
        vol_file = output_dir / f"dn_vol{vol_num}.json"
        if not vol_file.exists():
            continue

        vol_data = json.loads(vol_file.read_text())
        text = vol_data['text']
        expected_count = sutta_end - sutta_start + 1

        starts = {}  # dn_num → position

        def add_start(dn_num, pos):
            if sutta_start <= dn_num <= sutta_end and dn_num not in starts:
                starts[dn_num] = pos

        def is_ending(pos):
            """Check if sutta title at pos is an ending marker (contains niṭṭhitaṃ)."""
            following = text[pos:pos + 120]
            return 'niṭṭhita' in following.lower()

        def num_to_dn(num):
            """Convert internal or absolute number to DN number."""
            if 1 <= num <= expected_count:
                return sutta_start + num - 1
            if sutta_start <= num <= sutta_end:
                return num  # absolute DN number
            return None

        # Pattern A: number on own line (period optional), newline(s), then title
        for m in re.finditer(
            r'^(\d+)\.?\s*\n+\s*.{0,80}?sutta',
            text, re.MULTILINE | re.IGNORECASE
        ):
            if is_ending(m.start()):
                continue
            dn_num = num_to_dn(int(m.group(1)))
            if dn_num:
                add_start(dn_num, m.start())

        # Pattern B: number and title on same line ("6. mahālisuttaṃ")
        for m in re.finditer(
            r'^(\d+)\.\s+.{0,80}?sutta',
            text, re.MULTILINE | re.IGNORECASE
        ):
            if is_ending(m.start()):
                continue
            dn_num = num_to_dn(int(m.group(1)))
            if dn_num:
                add_start(dn_num, m.start())

        # Pattern C: numberless sutta title (uses name lookup)
        for m in re.finditer(
            r'\n\n([\wāīūṭḍṇṅñṃḷ]+)sutta[ṃm]',
            text, re.IGNORECASE
        ):
            name = m.group(1).lower()
            dn_num = DN_NAMES.get(name)
            if dn_num and sutta_start <= dn_num <= sutta_end:
                if not is_ending(m.start() + 2):
                    add_start(dn_num, m.start() + 2)  # +2 to skip \n\n

        # Sort by position and extract text
        sorted_starts = sorted(starts.items(), key=lambda x: x[1])

        for i, (dn_num, start) in enumerate(sorted_starts):
            end = sorted_starts[i + 1][1] if i + 1 < len(sorted_starts) else len(text)
            save_sutta(output_dir, f"dn{dn_num}.json", dn_num, text[start:end])
            total += 1

        found = sorted(starts.keys())
        print(f"  Vol {vol_num}: {len(sorted_starts)} suttas "
              f"(DN {sutta_start}-{sutta_end}, found {found})")

    print(f"  Total: {total} per-sutta files")
    return total


# ==================== MN Splitting ====================

def split_mn():
    """Split MN volumes using paṇṇāsa.vagga.sutta numbering.

    Collects markers from all volumes before assigning MN numbers to handle
    vaggas with >10 suttas (notably Uparipaṇṇāsa vagga 4 = Vibhaṅgavagga
    has 12 suttas, which would cause formula-based numbering to collide).
    Also detects title-only boundaries where N.N.N markers are missing.
    """
    output_dir = BJT_DIR / "mn"
    print("Splitting MN...")

    # Collect all markers across volumes: (formula_mn_num, text_pos, vol_num)
    vol_texts = {}
    all_markers = []

    for vol_num in range(1, 4):
        vol_file = output_dir / f"mn_vol{vol_num}.json"
        if not vol_file.exists():
            continue

        vol_data = json.loads(vol_file.read_text())
        text = vol_data['text']
        vol_texts[vol_num] = text

        # Find sutta boundaries: N.N.N. followed by sutta title on next line
        boundaries = list(re.finditer(
            r'(\d+)\.(\d+)\.(\d+)\.?[ \t]*\n+\s*'
            r'[\(\[]?[\wāīūṭḍṇṅñṃḷĀĪŪṬḌṆÑṂḶ\s\*]+(?:sutta[ṃm]|sutra\w*)',
            text, re.MULTILINE | re.IGNORECASE
        ))

        # Also find the 2-number marker for first sutta in a vagga (N.N.)
        first_marker = re.search(r'^(\d+)\.(\d+)\.\s*$', text, re.MULTILINE)
        if first_marker:
            if not boundaries or first_marker.start() < boundaries[0].start():
                boundaries.insert(0, first_marker)

        # Compute formula-based MN number for each marker
        numbered = []
        for b in boundaries:
            if b == first_marker and b.lastindex == 2:
                p, v = int(b.group(1)), int(b.group(2))
                mn_num = (p - 1) * 50 + (v - 1) * 10 + 1
            else:
                p = int(b.group(1))
                v = int(b.group(2))
                s = int(b.group(3))
                mn_num = (p - 1) * 50 + (v - 1) * 10 + s
            numbered.append((mn_num, b.start(), vol_num))

        # Detect title-only boundaries (no N.N.N marker, just "XXX suttaṃ"
        # on its own line after previous sutta ends). This catches cases
        # like MN 69 where the BJT source omits the number marker.
        marker_positions = {b.start() for b in boundaries}
        title_only = re.finditer(
            r'^([\wāīūṭḍṇṅñṃḷĀĪŪṬḌṆÑṂḶ]'
            r'[\wāīūṭḍṇṅñṃḷĀĪŪṬḌṆÑṂḶ\s]*?sutta[ṃm])\s*$',
            text, re.MULTILINE | re.IGNORECASE
        )
        for tm in title_only:
            # Skip if this title is already part of a numbered marker
            if any(abs(tm.start() - mp) < 200 for mp in marker_positions):
                continue
            # A real sutta start is followed by "Evaṃ me sutaṃ" (nidāna);
            # a sutta-end summary title (like "Naḷakapāna suttaṃ aṭṭhamaṃ")
            # is NOT. Check the next 300 chars after the title.
            post = text[tm.end():tm.end() + 300].lower()
            if 'evaṃ me sutaṃ' in post:
                # This is a standalone title — assign MN number 0 (to be fixed)
                numbered.append((0, tm.start(), vol_num))

        all_markers.extend(numbered)

    # Sort all markers by (vol_num, text_position)
    all_markers.sort(key=lambda x: (x[2], x[1]))

    # Fix MN numbers: enforce strict monotonicity to handle vagga overflow
    # and assign numbers to title-only markers (mn_num=0)
    for i in range(len(all_markers)):
        mn_num, pos, vol = all_markers[i]
        if i > 0:
            prev_mn = all_markers[i - 1][0]
            if mn_num <= prev_mn:
                mn_num = prev_mn + 1
                all_markers[i] = (mn_num, pos, vol)
        elif mn_num == 0:
            all_markers[i] = (1, pos, vol)

    # Extract text and save files
    all_suttas = []
    vol_counts = {}

    for i, (mn_num, start, vol_num) in enumerate(all_markers):
        text = vol_texts[vol_num]

        # Find end: next marker in same volume, or end of volume text
        end = len(text)
        for j in range(i + 1, len(all_markers)):
            if all_markers[j][2] == vol_num:
                end = all_markers[j][1]
                break

        save_sutta(output_dir, f"mn{mn_num}.json", mn_num, text[start:end])
        all_suttas.append(mn_num)
        vol_counts.setdefault(vol_num, []).append(mn_num)

    for vol_num in sorted(vol_counts):
        nums = vol_counts[vol_num]
        print(f"  Vol {vol_num}: {len(nums)} suttas "
              f"(MN {min(nums)}-{max(nums)})")

    print(f"  Total: {len(all_suttas)} per-sutta files")
    return len(all_suttas)


# ==================== SN Splitting ====================

# Map from volume-internal saṃyutta numbers to absolute SN saṃyutta numbers
SN_VOL_OFFSETS = {
    1: 0,    # Vol 1 (Sagāthavagga): 1→1, 2→2, ..., 11→11
    2: 11,   # Vol 2 (Nidānavagga): 1→12, 2→13, ..., 10→21
    3: 21,   # Vol 3 (Khandhavagga): 1→22, 2→23, ..., 13→34
    4: 34,   # Vol 4 (Saḷāyatanavagga): 1→35, 2→36, ..., 10→44
    5: 44,   # Vol 5 (Mahāvagga): 1→45, 2→46, ..., 12→56
}

# Max local saṃyutta number per volume
SN_VOL_MAX = {1: 11, 2: 10, 3: 13, 4: 10, 5: 12}


def split_sn():
    """Split SN volumes using saṃyutta numbering.

    BJT often has more markers than GRETIL/PTS because it expands peyyāla
    (abbreviated repetition series) that PTS keeps condensed.
    """
    output_dir = BJT_DIR / "sn"
    print("Splitting SN...")

    all_suttas = []
    # Track sutta counter per absolute saṃyutta across ALL volumes
    # (prevents counter reset when a saṃyutta spans volume boundaries)
    samyutta_counters = {}

    for vol_num in range(1, 6):
        vol_file = output_dir / f"sn_vol{vol_num}.json"
        if not vol_file.exists():
            continue

        vol_data = json.loads(vol_file.read_text())
        text = vol_data['text']
        offset = SN_VOL_OFFSETS[vol_num]
        max_local = SN_VOL_MAX[vol_num]

        # Match sutta markers: 3-level "N. N. N" or 4-level "N. N. N. N"
        # Use [ ]+ (not \s+) between numbers to avoid matching across lines
        # Allow range markers like "1-12" in sutta number position (peyyāla)
        markers = list(re.finditer(
            r'^(\d+)\.[ ]+(\d+)\.[ ]+(\d+)(?:-\d+)?(?:\.[ ]+(\d+)(?:-\d+)?)?\.?[ ]*$',
            text, re.MULTILINE
        ))

        if not markers:
            continue

        # Filter: first number must be within expected saṃyutta range
        valid_markers = [m for m in markers if 1 <= int(m.group(1)) <= max_local]

        sutta_positions = []

        for m in valid_markers:
            local_samyutta = int(m.group(1))
            abs_samyutta = local_samyutta + offset

            if abs_samyutta not in samyutta_counters:
                samyutta_counters[abs_samyutta] = 1
            else:
                samyutta_counters[abs_samyutta] += 1

            sutta_id = f"sn{abs_samyutta}_{samyutta_counters[abs_samyutta]}"
            sutta_positions.append((sutta_id, m.start(), abs_samyutta))

        # Extract text between markers
        for i, (sutta_id, start, _) in enumerate(sutta_positions):
            end = sutta_positions[i + 1][1] if i + 1 < len(sutta_positions) else len(text)
            save_sutta(output_dir, f"{sutta_id}.json", sutta_id, text[start:end])
            all_suttas.append(sutta_id)

        samyuttas = sorted(set(s[2] for s in sutta_positions))
        print(f"  Vol {vol_num}: {len(sutta_positions)} suttas "
              f"(SN {min(samyuttas)}-{max(samyuttas)})")

    print(f"  Total: {len(all_suttas)} per-sutta files")
    return len(all_suttas)


# ==================== AN Splitting ====================

def split_an():
    """Split AN volumes using nipāta numbering.

    AN vols 1-5 use different numbering levels:
    - Short nipātas (1-3): 3-level "nipāta. vagga. sutta"
    - Long nipātas (4+): 4-level "nipāta. paṇṇāsa. vagga. sutta"

    BJT often has more markers than GRETIL/PTS because it expands peyyāla.
    """
    output_dir = BJT_DIR / "an"
    print("Splitting AN...")

    all_suttas = []
    # Track sutta counter per nipāta across ALL volumes
    # (prevents counter reset when a nipāta spans volume boundaries)
    nipata_counters = {}

    for vol_num in range(1, 6):
        vol_file = output_dir / f"an_vol{vol_num}.json"
        if not vol_file.exists():
            continue

        vol_data = json.loads(vol_file.read_text())
        text = vol_data['text']

        # Match 3-level and 4-level markers
        # Use [ ]+ (not \s+) between numbers to avoid matching across lines
        markers = list(re.finditer(
            r'^(\d+)\.[ ]+(\d+)\.[ ]+(\d+)(?:\.[ ]+(\d+))?\.?[ ]*$',
            text, re.MULTILINE
        ))

        if not markers:
            continue

        # Filter: first number (nipāta) must be valid (1-11)
        valid_markers = [m for m in markers if 1 <= int(m.group(1)) <= 11]

        sutta_positions = []

        for m in valid_markers:
            nipata = int(m.group(1))

            if nipata not in nipata_counters:
                nipata_counters[nipata] = 1
            else:
                nipata_counters[nipata] += 1

            sutta_id = f"an{nipata}_{nipata_counters[nipata]}"
            sutta_positions.append((sutta_id, m.start(), nipata))

        # Extract text between markers
        for i, (sutta_id, start, _) in enumerate(sutta_positions):
            end = sutta_positions[i + 1][1] if i + 1 < len(sutta_positions) else len(text)
            save_sutta(output_dir, f"{sutta_id}.json", sutta_id, text[start:end])
            all_suttas.append(sutta_id)

        nipatas = sorted(set(s[2] for s in sutta_positions))
        print(f"  Vol {vol_num}: {len(sutta_positions)} suttas "
              f"(AN nipātas {min(nipatas)}-{max(nipatas)})")

    print(f"  Total: {len(all_suttas)} per-sutta files")
    return len(all_suttas)


# ==================== Main ====================

def main():
    collections = sys.argv[1:] if len(sys.argv) > 1 else ['dn', 'mn', 'sn', 'an']

    totals = {}
    for coll in collections:
        if coll == 'dn':
            totals['dn'] = split_dn()
        elif coll == 'mn':
            totals['mn'] = split_mn()
        elif coll == 'sn':
            totals['sn'] = split_sn()
        elif coll == 'an':
            totals['an'] = split_an()
        else:
            print(f"Unknown collection: {coll}")
            continue
        print()

    print("=" * 50)
    print("Summary:")
    for coll, count in totals.items():
        print(f"  {coll.upper()}: {count} per-sutta files")
    grand = sum(totals.values())
    print(f"  Total: {grand} files")

    # Compare with GRETIL counts
    print("\nComparison with GRETIL per-sutta file counts:")
    print("  (BJT counts are higher for SN/AN due to expanded peyyāla sections)")
    for nikaya in ['dn', 'mn', 'sn', 'an']:
        gretil_dir = DATA_DIR / f"gretil-parsed/{nikaya}"
        gretil_files = [f for f in gretil_dir.glob(f"{nikaya}*.json")
                        if not f.name.startswith('_') and 'vol' not in f.name]
        bjt_files = [f for f in (BJT_DIR / nikaya).glob(f"{nikaya}*.json")
                     if not f.name.startswith('_') and 'vol' not in f.name]
        print(f"  {nikaya.upper()}: BJT {len(bjt_files)}, GRETIL {len(gretil_files)}")


if __name__ == "__main__":
    main()
