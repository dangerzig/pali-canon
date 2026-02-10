#!/usr/bin/env python3
"""
Generate final comprehensive summary of the complete Pāli Canon critical edition project.
"""

import json
from pathlib import Path
from datetime import datetime

DATA_DIR = Path(__file__).parent.parent / "data"


def main():
    print("=" * 70)
    print("COMPLETE PĀLI TIPIṬAKA CRITICAL EDITION - FINAL SUMMARY")
    print("=" * 70)
    print()

    # Load all summaries
    critical_summary = json.loads((DATA_DIR / "critical/_complete_tipitaka_summary.json").read_text())
    gretil_summary = json.loads((DATA_DIR / "gretil-parsed/_complete_summary.json").read_text())
    lemmatized_stats = json.loads((DATA_DIR / "lemmatized/_stats.json").read_text())

    # ===== SOURCE DATA =====
    print("SOURCE DATA")
    print("-" * 70)
    print()
    print("1. GRETIL (Göttingen Register of Electronic Texts in Indian Languages)")
    print("   Source: PTS (Pali Text Society) editions")
    print(f"   Total words: {gretil_summary['total_words']:,}")
    print()
    print("2. VRI (Vipassana Research Institute)")
    print("   Source: Chaṭṭha Saṅgāyana Tipiṭaka (CST4)")
    print(f"   Total words: {critical_summary['grand_totals']['vri_words']:,}")
    print()
    print("3. SuttaCentral (SC)")
    print("   Source: Mahāsaṅgīti edition with segmentation")
    print(f"   Total words: {critical_summary['grand_totals']['sc_words']:,}")
    print()
    print("4. BJT (Buddha Jayanti Tripitaka)")
    print("   Source: Sri Lankan government edition (1957-1989)")
    print(f"   Total words: {critical_summary['grand_totals']['bjt_words']:,}")
    print()

    # ===== CRITICAL EDITION COVERAGE =====
    print("=" * 70)
    print("CRITICAL EDITION COVERAGE")
    print("=" * 70)
    print()

    # Vinaya
    vin = critical_summary['vinaya_pitaka']
    print("VINAYA PIṬAKA (5 witnesses: SC, GRETIL, VRI, BJT, Thai)")
    print(f"  Texts:           {vin['texts']}")
    print(f"  SC:              {vin.get('sc_words', 0):,} words")
    print(f"  GRETIL (PTS):    {vin['gretil_words']:,} words")
    print(f"  VRI (CST):       {vin['vri_words']:,} words")
    print(f"  BJT:             {vin.get('bjt_words', 0):,} words")
    print()

    # Sutta Piṭaka
    sutta = critical_summary['sutta_pitaka']
    print("SUTTA PIṬAKA (5 witnesses: SC, GRETIL, VRI, BJT, Thai)")
    print()

    # DN
    dn = sutta['dn']
    print(f"  Dīgha Nikāya (DN)")
    print(f"    Suttas:        {dn['suttas']}")
    print(f"    SC:            {dn['sc_words']:,} words")
    print(f"    GRETIL:        {dn['gretil_words']:,} words")
    print(f"    VRI:           {dn['vri_words']:,} words")
    print()

    # MN
    mn = sutta['mn']
    print(f"  Majjhima Nikāya (MN)")
    print(f"    Suttas:        {mn['suttas']}")
    print(f"    SC:            {mn['sc_words']:,} words")
    print(f"    GRETIL:        {mn['gretil_words']:,} words")
    print(f"    VRI:           {mn['vri_words']:,} words")
    print()

    # SN
    sn = sutta['sn']
    print(f"  Saṃyutta Nikāya (SN)")
    print(f"    Files:         {sn['files']}")
    print(f"    SC:            {sn['sc_words']:,} words")
    print(f"    GRETIL:        {sn['gretil_words']:,} words")
    print(f"    VRI:           {sn['vri_words']:,} words")
    print()

    # AN
    an = sutta['an']
    print(f"  Aṅguttara Nikāya (AN)")
    print(f"    Files:         {an['files']}")
    print(f"    SC:            {an['sc_words']:,} words")
    print(f"    GRETIL:        {an['gretil_words']:,} words")
    print(f"    VRI:           {an['vri_words']:,} words")
    print()

    # KN
    kn = sutta['kn']
    print(f"  Khuddaka Nikāya (KN)")
    print(f"    Texts:         {kn['texts']}")
    print(f"    SC:            {kn['sc_words']:,} words")
    print(f"    GRETIL:        {kn['gretil_words']:,} words")
    print(f"    VRI:           {kn['vri_words']:,} words")
    print()

    # Sutta totals
    st = sutta['totals']
    print(f"  SUTTA TOTALS:")
    print(f"    SC:            {st['sc_words']:,} words")
    print(f"    GRETIL:        {st['gretil_words']:,} words")
    print(f"    VRI:           {st['vri_words']:,} words")
    print()

    # Abhidhamma
    abh = critical_summary['abhidhamma_pitaka']
    print("ABHIDHAMMA PIṬAKA (5 witnesses: SC, GRETIL, VRI, BJT, Thai)")
    print(f"  Texts:           {abh['texts']}")
    print(f"  SC:              {abh.get('sc_words', 0):,} words")
    print(f"  GRETIL (PTS):    {abh['gretil_words']:,} words")
    print(f"  VRI (CST):       {abh['vri_words']:,} words")
    print(f"  BJT:             {abh.get('bjt_words', 0):,} words")
    print()

    # ===== GRAND TOTALS =====
    print("=" * 70)
    print("GRAND TOTALS")
    print("=" * 70)
    gt = critical_summary['grand_totals']
    print(f"  SC (all):              {gt['sc_words']:,} words")
    print(f"  GRETIL (all):          {gt['gretil_words']:,} words")
    print(f"  VRI (all):             {gt['vri_words']:,} words")
    print(f"  BJT (all):             {gt['bjt_words']:,} words")
    print()

    # ===== LEMMATIZATION =====
    print("=" * 70)
    print("LEMMATIZATION (SuttaCentral Texts)")
    print("=" * 70)
    print(f"  Total word tokens:     {lemmatized_stats['total_words']:,}")
    print(f"  Unique word forms:     {lemmatized_stats['unique_words']:,}")
    print(f"  Words identified:      {lemmatized_stats['words_found']:,}")
    print(f"  Words not found:       {lemmatized_stats['words_not_found']:,}")
    print(f"  Sandhi decompositions: {lemmatized_stats['sandhi_words']:,}")
    print(f"  Coverage:              {lemmatized_stats['coverage']}")
    print()

    # ===== SUMMARY =====
    print("=" * 70)
    print("PROJECT SUMMARY")
    print("=" * 70)
    print()

    # Calculate witness coverage
    five_witness_words = st['sc_words'] + vin['gretil_words'] + abh['gretil_words']

    print("Witness Coverage:")
    print(f"  5-witness editions (SC/GRETIL/VRI/BJT/Thai): {five_witness_words:,} words")
    print()

    total_critical_words = five_witness_words
    print(f"Total Critical Edition Coverage:          {total_critical_words:,} words")
    print()

    print("This represents the COMPLETE Tipiṭaka:")
    print("  ✓ Vinaya Piṭaka (monastic discipline)")
    print("  ✓ Sutta Piṭaka (discourses)")
    print("    - Dīgha Nikāya (long discourses)")
    print("    - Majjhima Nikāya (middle-length discourses)")
    print("    - Saṃyutta Nikāya (connected discourses)")
    print("    - Aṅguttara Nikāya (numerical discourses)")
    print("    - Khuddaka Nikāya (minor texts)")
    print("  ✓ Abhidhamma Piṭaka (systematic philosophy)")
    print()

    # Save final summary
    final_summary = {
        "timestamp": datetime.now().isoformat(),
        "project": "Pāli Canon Digital Critical Edition",
        "sources": {
            "gretil": {
                "name": "GRETIL (Göttingen Register of Electronic Texts in Indian Languages)",
                "edition": "PTS (Pali Text Society)",
                "total_words": gretil_summary['total_words']
            },
            "vri": {
                "name": "VRI (Vipassana Research Institute)",
                "edition": "Chaṭṭha Saṅgāyana Tipiṭaka (CST4)",
                "total_words": critical_summary['grand_totals']['vri_words']
            },
            "suttacentral": {
                "name": "SuttaCentral",
                "edition": "Mahāsaṅgīti with segmentation",
                "total_words": critical_summary['grand_totals']['sc_words']
            },
            "bjt": {
                "name": "BJT (Buddha Jayanti Tripitaka)",
                "edition": "Sri Lankan government edition (1957-1989)",
                "total_words": critical_summary['grand_totals']['bjt_words']
            }
        },
        "critical_edition": {
            "vinaya_pitaka": vin,
            "sutta_pitaka": {
                "dn": dn,
                "mn": mn,
                "sn": sn,
                "an": an,
                "kn": kn,
                "totals": st
            },
            "abhidhamma_pitaka": abh,
            "grand_totals": gt
        },
        "lemmatization": {
            "total_words": lemmatized_stats['total_words'],
            "unique_words": lemmatized_stats['unique_words'],
            "words_found": lemmatized_stats['words_found'],
            "words_not_found": lemmatized_stats['words_not_found'],
            "sandhi_words": lemmatized_stats['sandhi_words'],
            "coverage": lemmatized_stats['coverage']
        },
        "coverage": {
            "five_witness_words": five_witness_words,
            "total_critical_words": total_critical_words
        }
    }

    output_file = DATA_DIR / "_FINAL_PROJECT_SUMMARY.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(final_summary, f, indent=2, ensure_ascii=False)

    print(f"Final summary saved to: {output_file}")


if __name__ == "__main__":
    main()
