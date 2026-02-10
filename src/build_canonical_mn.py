#!/usr/bin/env python3
"""
Build canonical MN (Majjhima Nikāya) with all metadata.
- Normalized Pāli text (SC base, ṃ for niggahīta)
- PTS page references
- Segment IDs for translation alignment
"""

import json
import re
from pathlib import Path

try:
    from pali.text import normalize_pali
except ImportError:
    def normalize_pali(text):
        text = text.replace('ṁ', 'ṃ')
        return re.sub(r'\s+', ' ', text).strip()

DATA_DIR = Path(__file__).parent.parent / "data"
SC_MN_DIR = DATA_DIR / "suttacentral-ms/root/pli/ms/sutta/mn"
OUTPUT_DIR = DATA_DIR / "canonical/mn"

# MN vagga assignments
# Mūlapaṇṇāsa (1-50)
MULAPANNASA_VAGGAS = {
    **{i: "Mūlapariyāyavagga" for i in range(1, 11)},
    **{i: "Sīhanādavagga" for i in range(11, 21)},
    **{i: "Opammavagga" for i in range(21, 31)},
    **{i: "Mahāyamakavagga" for i in range(31, 41)},
    **{i: "Cūḷayamakavagga" for i in range(41, 51)},
}

# Majjhimapaṇṇāsa (51-100)
MAJJHIMAPANNASA_VAGGAS = {
    **{i: "Gahapativagga" for i in range(51, 61)},
    **{i: "Bhikkhuvagga" for i in range(61, 71)},
    **{i: "Paribbājakavagga" for i in range(71, 81)},
    **{i: "Rājavagga" for i in range(81, 91)},
    **{i: "Brāhmaṇavagga" for i in range(91, 101)},
}

# Uparipaṇṇāsa (101-152)
UPARIPANNASA_VAGGAS = {
    **{i: "Devadahavagga" for i in range(101, 111)},
    **{i: "Anupadavagga" for i in range(111, 121)},
    **{i: "Suññatavagga" for i in range(121, 131)},
    **{i: "Vibhaṅgavagga" for i in range(131, 143)},
    **{i: "Saḷāyatanavagga" for i in range(143, 153)},
}

VAGGAS = {**MULAPANNASA_VAGGAS, **MAJJHIMAPANNASA_VAGGAS, **UPARIPANNASA_VAGGAS}

PANNASAS = {
    **{i: "Mūlapaṇṇāsa" for i in range(1, 51)},
    **{i: "Majjhimapaṇṇāsa" for i in range(51, 101)},
    **{i: "Uparipaṇṇāsa" for i in range(101, 153)},
}

# MN Titles (Pāli and English)
TITLES = {
    1: ("Mūlapariyāyasutta", "The Root of All Things"),
    2: ("Sabbāsavasutta", "All the Taints"),
    3: ("Dhammadāyādasutta", "Heirs in the Dhamma"),
    4: ("Bhayabheravasutta", "Fear and Dread"),
    5: ("Anaṅgaṇasutta", "Without Blemishes"),
    6: ("Ākaṅkheyyasutta", "If a Bhikkhu Should Wish"),
    7: ("Vatthūpamasutta", "The Simile of the Cloth"),
    8: ("Sallekhasutta", "Effacement"),
    9: ("Sammādiṭṭhisutta", "Right View"),
    10: ("Satipaṭṭhānasutta", "The Foundations of Mindfulness"),
    11: ("Cūḷasīhanādasutta", "The Shorter Discourse on the Lion's Roar"),
    12: ("Mahāsīhanādasutta", "The Greater Discourse on the Lion's Roar"),
    13: ("Mahādukkhakkhandhasutta", "The Greater Discourse on the Mass of Suffering"),
    14: ("Cūḷadukkhakkhandhasutta", "The Shorter Discourse on the Mass of Suffering"),
    15: ("Anumānasutta", "Inference"),
    16: ("Cetokhilasutta", "The Wilderness in the Heart"),
    17: ("Vanapatthasutta", "Jungle Thickets"),
    18: ("Madhupiṇḍikasutta", "The Honeyball"),
    19: ("Dvedhāvitakkasutta", "Two Kinds of Thought"),
    20: ("Vitakkasaṇṭhānasutta", "The Removal of Distracting Thoughts"),
    21: ("Kakacūpamasutta", "The Simile of the Saw"),
    22: ("Alagaddūpamasutta", "The Simile of the Snake"),
    23: ("Vammikasutta", "The Ant-hill"),
    24: ("Rathavinītasutta", "The Relay Chariots"),
    25: ("Nivāpasutta", "The Bait"),
    26: ("Pāsarāsisutta", "The Noble Search"),
    27: ("Cūḷahatthipadopamasutta", "The Shorter Discourse on the Simile of the Elephant's Footprint"),
    28: ("Mahāhatthipadopamasutta", "The Greater Discourse on the Simile of the Elephant's Footprint"),
    29: ("Mahāsāropamasutta", "The Greater Discourse on the Simile of the Heartwood"),
    30: ("Cūḷasāropamasutta", "The Shorter Discourse on the Simile of the Heartwood"),
    31: ("Cūḷagosiṅgasutta", "The Shorter Discourse in Gosiṅga"),
    32: ("Mahāgosiṅgasutta", "The Greater Discourse in Gosiṅga"),
    33: ("Mahāgopālakasutta", "The Greater Discourse on the Cowherd"),
    34: ("Cūḷagopālakasutta", "The Shorter Discourse on the Cowherd"),
    35: ("Cūḷasaccakasutta", "The Shorter Discourse to Saccaka"),
    36: ("Mahāsaccakasutta", "The Greater Discourse to Saccaka"),
    37: ("Cūḷataṇhāsaṅkhayasutta", "The Shorter Discourse on the Destruction of Craving"),
    38: ("Mahātaṇhāsaṅkhayasutta", "The Greater Discourse on the Destruction of Craving"),
    39: ("Mahā-assapurasutta", "The Greater Discourse at Assapura"),
    40: ("Cūḷa-assapurasutta", "The Shorter Discourse at Assapura"),
    41: ("Sāleyyakasutta", "The Brahmins of Sālā"),
    42: ("Verañjakasutta", "The Brahmins of Verañjā"),
    43: ("Mahāvedallasutta", "The Greater Series of Questions and Answers"),
    44: ("Cūḷavedallasutta", "The Shorter Series of Questions and Answers"),
    45: ("Cūḷadhammasamādānasutta", "The Shorter Discourse on Ways of Undertaking Things"),
    46: ("Mahādhammasamādānasutta", "The Greater Discourse on Ways of Undertaking Things"),
    47: ("Vīmaṁsakasutta", "The Inquirer"),
    48: ("Kosambiyasutta", "The Kosambians"),
    49: ("Brahmanimantanikasutta", "The Invitation of Brahmā"),
    50: ("Māratajjanīyasutta", "The Rebuke to Māra"),
    51: ("Kandarakasutta", "To Kandaraka"),
    52: ("Aṭṭhakanāgarasutta", "The Man from Aṭṭhakanāgara"),
    53: ("Sekhasutta", "The Disciple in Higher Training"),
    54: ("Potaliyasutta", "To Potaliya"),
    55: ("Jīvakasutta", "To Jīvaka"),
    56: ("Upālisutta", "To Upāli"),
    57: ("Kukkuravatikasutta", "The Dog-duty Ascetic"),
    58: ("Abhayarājakumārasutta", "To Prince Abhaya"),
    59: ("Bahuvedanīyasutta", "The Many Kinds of Feeling"),
    60: ("Apaṇṇakasutta", "The Incontrovertible Teaching"),
    61: ("Ambalaṭṭhikārāhulovādasutta", "Advice to Rāhula at Ambalaṭṭhikā"),
    62: ("Mahārāhulovādasutta", "The Greater Discourse of Advice to Rāhula"),
    63: ("Cūḷamāluṅkyasutta", "The Shorter Discourse to Māluṅkyāputta"),
    64: ("Mahāmāluṅkyasutta", "The Greater Discourse to Māluṅkyāputta"),
    65: ("Bhaddālisutta", "To Bhaddāli"),
    66: ("Laṭukikopamasutta", "The Simile of the Quail"),
    67: ("Cātumāsutta", "At Cātumā"),
    68: ("Naḷakapānasutta", "At Naḷakapāna"),
    69: ("Gulissānisutta", "At Gulissāni"),
    70: ("Kīṭāgirisutta", "At Kīṭāgiri"),
    71: ("Tevijjavacchagottasutta", "To Vacchagotta on the Threefold True Knowledge"),
    72: ("Aggivacchagottasutta", "To Vacchagotta on Fire"),
    73: ("Mahāvacchagottasutta", "The Greater Discourse to Vacchagotta"),
    74: ("Dīghanakhasutta", "To Dīghanakha"),
    75: ("Māgaṇḍiyasutta", "To Māgaṇḍiya"),
    76: ("Sandakasutta", "To Sandaka"),
    77: ("Mahāsakuludāyisutta", "The Greater Discourse to Sakuludāyī"),
    78: ("Samaṇamaṇḍikāsutta", "Samaṇamaṇḍikā"),
    79: ("Cūḷasakuludāyisutta", "The Shorter Discourse to Sakuludāyī"),
    80: ("Vekhanassasutta", "To Vekhanassa"),
    81: ("Ghaṭīkārasutta", "Ghaṭīkāra"),
    82: ("Raṭṭhapālasutta", "On Raṭṭhapāla"),
    83: ("Makhādevasutta", "King Makhādeva"),
    84: ("Madhurāsutta", "At Madhurā"),
    85: ("Bodhirājakumārasutta", "To Prince Bodhi"),
    86: ("Aṅgulimālasutta", "On Aṅgulimāla"),
    87: ("Piyajātikasutta", "Born from Those Who Are Dear"),
    88: ("Bāhitikasutta", "The Cloak"),
    89: ("Dhammacetiyasutta", "Monuments to the Dhamma"),
    90: ("Kaṇṇakatthalasutta", "At Kaṇṇakatthala"),
    91: ("Brahmāyusutta", "Brahmāyu"),
    92: ("Selasutta", "To Sela"),
    93: ("Assalāyanasutta", "To Assalāyana"),
    94: ("Ghoṭamukhasutta", "To Ghoṭamukha"),
    95: ("Caṅkīsutta", "With Caṅkī"),
    96: ("Esukārīsutta", "To Esukārī"),
    97: ("Dhanañjānisutta", "To Dhanañjāni"),
    98: ("Vāseṭṭhasutta", "To Vāseṭṭha"),
    99: ("Subhasutta", "To Subha"),
    100: ("Saṅgāravasutta", "To Saṅgārava"),
    101: ("Devadahasutta", "At Devadaha"),
    102: ("Pañcattayasutta", "The Five and Three"),
    103: ("Kintisutta", "What Do You Think About Me?"),
    104: ("Sāmagāmasutta", "At Sāmagāma"),
    105: ("Sunakkhattasutta", "To Sunakkhatta"),
    106: ("Āneñjasappāyasutta", "The Way to the Imperturbable"),
    107: ("Gaṇakamoggallānasutta", "To Gaṇaka Moggallāna"),
    108: ("Gopakamoggallānasutta", "With Gopaka Moggallāna"),
    109: ("Mahāpuṇṇamasutta", "The Greater Discourse on the Full-moon Night"),
    110: ("Cūḷapuṇṇamasutta", "The Shorter Discourse on the Full-moon Night"),
    111: ("Anupādasutta", "One by One as They Occurred"),
    112: ("Chabbisodhānasutta", "The Sixfold Purity"),
    113: ("Sappurisasutta", "The True Man"),
    114: ("Sevitabbāsevitabbasutta", "To Be Cultivated and Not to Be Cultivated"),
    115: ("Bahudhātukasutta", "The Many Kinds of Elements"),
    116: ("Isigiliasutta", "Isigili"),
    117: ("Mahācattārīsakasutta", "The Great Forty"),
    118: ("Ānāpānassatisutta", "Mindfulness of Breathing"),
    119: ("Kāyagatāsatisutta", "Mindfulness of the Body"),
    120: ("Saṅkhārupapattisutta", "Reappearance by Aspiration"),
    121: ("Cūḷasuññatasutta", "The Shorter Discourse on Voidness"),
    122: ("Mahāsuññatasutta", "The Greater Discourse on Voidness"),
    123: ("Acchariyaabbhutasutta", "Wonderful and Marvellous"),
    124: ("Bākkulasutta", "Bakkula"),
    125: ("Dantabhūmisutta", "The Grade of the Tamed"),
    126: ("Bhūmijasutta", "Bhūmija"),
    127: ("Anuruddhasutta", "Anuruddha"),
    128: ("Upakkilesasutta", "Imperfections"),
    129: ("Bālapaṇḍitasutta", "Fools and Wise Men"),
    130: ("Devadūtasutta", "The Divine Messengers"),
    131: ("Bhaddekarattasutta", "One Fortunate Attachment"),
    132: ("Ānandabhaddekarattasutta", "Ānanda and One Fortunate Attachment"),
    133: ("Mahākaccānabhaddekarattasutta", "Mahā Kaccāna and One Fortunate Attachment"),
    134: ("Lomasakaṅgiyabhaddekarattasutta", "Lomasakaṅgiya and One Fortunate Attachment"),
    135: ("Cūḷakammavibhaṅgasutta", "The Shorter Exposition of Action"),
    136: ("Mahākammavibhaṅgasutta", "The Greater Exposition of Action"),
    137: ("Saḷāyatanavibhaṅgasutta", "The Exposition of the Sixfold Base"),
    138: ("Uddesavibhaṅgasutta", "The Exposition of a Summary"),
    139: ("Araṇavibhaṅgasutta", "The Exposition of Non-conflict"),
    140: ("Dhātuvibhaṅgasutta", "The Exposition of the Elements"),
    141: ("Saccavibhaṅgasutta", "The Exposition of the Truths"),
    142: ("Dakkhiṇāvibhaṅgasutta", "The Exposition of Offerings"),
    143: ("Anāthapiṇḍikovādasutta", "Advice to Anāthapiṇḍika"),
    144: ("Channovādasutta", "Advice to Channa"),
    145: ("Puṇṇovādasutta", "Advice to Puṇṇa"),
    146: ("Nandakovādasutta", "Advice from Nandaka"),
    147: ("Cūḷarāhulovādasutta", "The Shorter Discourse of Advice to Rāhula"),
    148: ("Chachakkasutta", "The Six Sets of Six"),
    149: ("Mahāsaḷāyatanikasutta", "The Great Sixfold Base"),
    150: ("Nagaravindeyyasutta", "To the Nagaravindans"),
    151: ("Piṇḍapātapārisuddhisutta", "The Purification of Almsfood"),
    152: ("Indriyabhāvanāsutta", "The Development of the Faculties"),
}

# PTS Volume/Page references (approximate ranges)
PTS_REFS = {
    1: "M i 1–6", 2: "M i 6–12", 3: "M i 12–16", 4: "M i 16–24", 5: "M i 24–31",
    6: "M i 31–36", 7: "M i 36–40", 8: "M i 40–46", 9: "M i 46–55", 10: "M i 55–63",
    11: "M i 63–68", 12: "M i 68–83", 13: "M i 83–90", 14: "M i 91–95", 15: "M i 95–100",
    16: "M i 101–104", 17: "M i 104–108", 18: "M i 108–114", 19: "M i 114–118", 20: "M i 118–122",
    21: "M i 122–129", 22: "M i 130–142", 23: "M i 142–145", 24: "M i 145–151", 25: "M i 151–160",
    26: "M i 160–175", 27: "M i 175–184", 28: "M i 184–191", 29: "M i 192–197", 30: "M i 197–200",
    31: "M i 205–211", 32: "M i 212–219", 33: "M i 220–225", 34: "M i 225–227", 35: "M i 227–237",
    36: "M i 237–251", 37: "M i 251–256", 38: "M i 256–271", 39: "M i 271–280", 40: "M i 281–284",
    41: "M i 285–290", 42: "M i 290–293", 43: "M i 292–298", 44: "M i 299–305", 45: "M i 305–310",
    46: "M i 310–316", 47: "M i 317–320", 48: "M i 320–325", 49: "M i 326–331", 50: "M i 332–338",
    51: "M i 339–349", 52: "M i 349–353", 53: "M i 353–359", 54: "M i 359–368", 55: "M i 368–371",
    56: "M i 371–387", 57: "M i 387–392", 58: "M i 392–396", 59: "M i 396–400", 60: "M i 400–413",
    61: "M i 414–420", 62: "M i 420–426", 63: "M i 426–432", 64: "M i 432–437", 65: "M i 437–447",
    66: "M i 447–456", 67: "M i 456–462", 68: "M i 462–469", 69: "M i 469–473", 70: "M i 473–481",
    71: "M i 481–483", 72: "M i 483–489", 73: "M i 489–497", 74: "M i 497–501", 75: "M i 501–513",
    76: "M i 513–524", 77: "M ii 1–22", 78: "M ii 22–29", 79: "M ii 29–39", 80: "M ii 40–42",
    81: "M ii 45–54", 82: "M ii 54–74", 83: "M ii 74–83", 84: "M ii 83–90", 85: "M ii 91–97",
    86: "M ii 97–105", 87: "M ii 106–112", 88: "M ii 112–118", 89: "M ii 118–125", 90: "M ii 125–133",
    91: "M ii 133–146", 92: "M ii 146–157", 93: "M ii 147–157", 94: "M ii 157–162", 95: "M ii 164–177",
    96: "M ii 177–184", 97: "M ii 184–196", 98: "M ii 196–209", 99: "M ii 209–213", 100: "M ii 209–213",
    101: "M ii 214–228", 102: "M ii 228–238", 103: "M ii 238–243", 104: "M ii 243–251", 105: "M ii 252–261",
    106: "M ii 261–266", 107: "M iii 1–7", 108: "M iii 7–15", 109: "M iii 15–20", 110: "M iii 20–24",
    111: "M iii 25–29", 112: "M iii 29–37", 113: "M iii 37–45", 114: "M iii 45–64", 115: "M iii 61–67",
    116: "M iii 68–71", 117: "M iii 71–78", 118: "M iii 78–88", 119: "M iii 88–99", 120: "M iii 99–103",
    121: "M iii 104–109", 122: "M iii 109–118", 123: "M iii 118–124", 124: "M iii 124–128", 125: "M iii 128–134",
    126: "M iii 138–142", 127: "M iii 144–152", 128: "M iii 152–162", 129: "M iii 163–178", 130: "M iii 178–187",
    131: "M iii 187–189", 132: "M iii 189–191", 133: "M iii 192–195", 134: "M iii 195–199", 135: "M iii 202–206",
    136: "M iii 207–215", 137: "M iii 215–219", 138: "M iii 223–228", 139: "M iii 230–237", 140: "M iii 237–247",
    141: "M iii 248–252", 142: "M iii 253–257", 143: "M iii 258–263", 144: "M iii 263–266", 145: "M iii 267–270",
    146: "M iii 270–277", 147: "M iii 277–280", 148: "M iii 280–287", 149: "M iii 287–290", 150: "M iii 290–293",
    151: "M iii 293–297", 152: "M iii 298–302",
}

def build_sutta(n):
    """Build canonical sutta file."""
    filepath = SC_MN_DIR / f"mn{n}_root-pli-ms.json"
    with open(filepath, 'r', encoding='utf-8') as f:
        sc_data = json.load(f)

    pali_title, eng_title = TITLES.get(n, (f"MN {n}", ""))

    sutta = {
        "id": f"mn{n}",
        "title_pali": pali_title,
        "title_eng": eng_title,
        "collection": "mn",
        "pannasa": PANNASAS[n],
        "vagga": VAGGAS[n],
        "pts": PTS_REFS.get(n, ""),
        "segments": []
    }

    for seg_id, text in sc_data.items():
        sutta["segments"].append({
            "id": seg_id,
            "pali": normalize_pali(text)
        })

    return sutta

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    index = {
        "collection": "Majjhima Nikāya",
        "description": "The Middle Length Discourses of the Buddha",
        "source": "SuttaCentral Mahāsaṅgīti edition",
        "normalized": "niggahīta standardized to ṃ",
        "suttas": []
    }

    total_segs = 0
    for n in range(1, 153):
        sutta = build_sutta(n)

        with open(OUTPUT_DIR / f"mn{n}.json", 'w', encoding='utf-8') as f:
            json.dump(sutta, f, indent=2, ensure_ascii=False)

        seg_count = len(sutta["segments"])
        total_segs += seg_count

        index["suttas"].append({
            "id": sutta["id"],
            "title_pali": sutta["title_pali"],
            "title_eng": sutta["title_eng"],
            "pannasa": sutta["pannasa"],
            "vagga": sutta["vagga"],
            "pts": sutta["pts"],
            "segments": seg_count
        })

        print(f"MN {n:3d}: {sutta['title_pali']:40s} ({seg_count:4d} segments)")

    index["total_segments"] = total_segs

    with open(OUTPUT_DIR / "_index.json", 'w', encoding='utf-8') as f:
        json.dump(index, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*70}")
    print(f"Total: 152 suttas, {total_segs:,} segments")
    print(f"Saved to: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
