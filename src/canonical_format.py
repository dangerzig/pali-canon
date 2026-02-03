#!/usr/bin/env python3
"""
Proposed canonical format for Pāli texts.

Each segment has:
- id: SuttaCentral segment ID (for alignment with translations)
- text: Canonical Pāli text (SC/VRI consensus, normalized)
- pts: PTS volume.page reference
- variants: Dict of edition -> variant reading (only where different)
"""

import json

# Example: DN 1 opening segments
canonical_dn1 = {
    "meta": {
        "id": "dn1",
        "title": "Brahmajālasutta",
        "collection": "dn",
        "pts_volume": "D i",
        "editions_compared": ["sc", "vri", "pts"]
    },
    "segments": [
        {
            "id": "dn1:0.1",
            "text": "Dīgha Nikāya 1",
            "pts": None,
            "variants": {}
        },
        {
            "id": "dn1:0.2", 
            "text": "Brahmajālasutta",
            "pts": None,
            "variants": {
                "vri": "Brahmajālasuttaṃ"
            }
        },
        {
            "id": "dn1:1.1.1",
            "text": "Evaṃ me sutaṃ—",
            "pts": "D i 1",
            "variants": {
                "pts": "Evam me sutam."  # missing diacritics
            }
        },
        {
            "id": "dn1:1.1.2",
            "text": "ekaṃ samayaṃ bhagavā antarā ca rājagahaṃ antarā ca nāḷandaṃ addhānamaggappaṭipanno hoti mahatā bhikkhusaṅghena saddhiṃ pañcamattehi bhikkhusatehi.",
            "pts": "D i 1",
            "variants": {
                "pts": "Ekam samayam Bhagavā antarā ca Rājagahaṃ antarā ca Nālandaṃ addhāna-magga-paṭipanno hoti mahatā bhikkhu-saṅghena saddhiṃ pañcamattehi bhikkhu-satehi."
                # Note: PTS uses hyphens in compounds, different capitalization
            }
        },
        {
            "id": "dn1:1.1.3",
            "text": "Suppiyopi kho paribbājako antarā ca rājagahaṃ antarā ca nāḷandaṃ addhānamaggappaṭipanno hoti saddhiṃ antevāsinā brahmadattena māṇavena.",
            "pts": "D i 1",
            "variants": {}  # SC, VRI, PTS all agree on this content
        }
    ]
}

print(json.dumps(canonical_dn1, indent=2, ensure_ascii=False))
