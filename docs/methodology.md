# Lemmatized Pāli Canon: Methodology and Results

## Abstract

This document describes the creation of a fully lemmatized digital edition of the Pāli Canon (Tipiṭaka), comprising approximately 1.6 million words across 5,764 individual texts. Using the SuttaCentral Mahāsaṅgīti edition as the base text and the Digital Pāli Dictionary (DPD) for morphological analysis, we achieved 94.3% coverage in identifying dictionary headwords (lemmas) for all word tokens. The resulting dataset includes word-level tokenization, lemmatization, part-of-speech tagging, verbal root identification, and sandhi decomposition.

## 1. Introduction

The Pāli Canon represents the oldest complete collection of Buddhist scriptures, preserved in the Pāli language. While digital editions of the canon have existed for decades, comprehensive morphological annotation has remained limited. This project aims to create a fully lemmatized version of the canon suitable for computational analysis, concordance generation, and linguistic research.

## 2. Source Materials

### 2.1 Available Text Sources

Four digital editions of the Pāli Canon were assembled for this project:

| Source | Description | Location |
|--------|-------------|----------|
| SuttaCentral (SC) | Mahāsaṅgīti Tipiṭaka Buddhavasse 2500, segmented | `data/suttacentral-ms/` |
| PTS Text | Pali Text Society romanized editions | `data/pts-text/` |
| PTS PDFs | Pali Text Society original publications | `data/pts-pdf/` |
| VRI/CST | Chaṭṭha Saṅgāyana Tipiṭaka (Vipassana Research Institute) | `data/vri-raw/` |

### 2.2 Base Text Selection

The SuttaCentral Mahāsaṅgīti edition was selected as the base text for several reasons:

- **Scholarly reliability**: Based on the Sixth Council (Chaṭṭha Saṅgāyana) edition with corrections
- **Segmentation**: Pre-segmented at the sentence/verse level with unique identifiers
- **Open access**: Available under Creative Commons licensing
- **Translation alignment**: Segment IDs enable alignment with translations

Source repository: `github.com/suttacentral/bilara-data`

### 2.3 PTS References for Academic Citation

Each text includes PTS (Pali Text Society) volume and page references to enable citation in standard academic format. For example:

- DN 1 → D i 1–46 (Dīgha Nikāya, volume i, pages 1–46)
- MN 1 → M i 1–6 (Majjhima Nikāya, volume i, pages 1–6)
- SN 22.59 → S iii 66–68

This allows scholars to locate passages in the authoritative PTS editions while working with the digital text.

### 2.4 Editorial Policy (Future Work)

The current release uses the SuttaCentral Mahāsaṅgīti edition as its base text for practical reasons (pre-segmented, openly licensed). However, the intended editorial policy for future releases is:

- **PTS as authoritative**: The Pali Text Society editions should serve as the primary authority for text-critical decisions
- **Variant apparatus**: Readings from SC, VRI/CST, and other editions should be recorded as variants
- **Transparent documentation**: All editorial choices should be documented and traceable

Scripts were developed to compare readings across editions (`src/compare_editions.py`, `src/find_variants.py`), identifying words that differ between SC, VRI, and PTS sources. This work is preliminary; systematic variant apparatus was not incorporated into the current release.

### 2.2 Dictionary: Digital Pāli Dictionary (DPD)

Morphological analysis was performed using the Digital Pāli Dictionary (https://digitalpalidictionary.github.io), version 0.3.20260202. The DPD provides:

| Resource | Count |
|----------|-------|
| Dictionary headwords | 88,350 |
| Inflected form lookups | 1,275,089 |
| Verbal roots | 754 |

The DPD's lookup table maps all attested inflected forms to their dictionary headwords, enabling automated lemmatization. The deconstructor module provides analysis of sandhi (euphonic combination) compounds.

### 2.3 Dictionary of Pāli Proper Names (DPPN)

For proper noun identification, we have incorporated the Dictionary of Pāli Proper Names by G.P. Malalasekera, available at https://www.aimwell.org/DPPN/. The extracted data includes:

| Category | Count |
|----------|-------|
| Person names | 2,541 |
| Text names | 1,335 |
| Place names | 69 |
| **Total entries** | **3,945** |

This resource will be used in future work to improve identification of proper nouns not covered by the DPD.

## 3. Corpus Description

The Pāli Canon comprises five major collections (nikāyas):

| Collection | Full Name | Description | Texts | Segments | Words |
|------------|-----------|-------------|-------|----------|-------|
| DN | Dīgha Nikāya | Long Discourses | 34 | 8,038 | 141,565 |
| MN | Majjhima Nikāya | Middle-length Discourses | 152 | 27,195 | 241,651 |
| SN | Saṃyutta Nikāya | Connected Discourses | 1,819 | 43,468 | 269,739 |
| AN | Aṅguttara Nikāya | Numerical Discourses | 1,408 | 41,843 | 304,857 |
| KN | Khuddaka Nikāya | Minor Collection | 2,351 | 155,801 | 630,242 |
| **Total** | | | **5,764** | **276,345** | **1,588,054** |

The Khuddaka Nikāya includes 20 distinct texts:

- Khuddakapāṭha, Dhammapada, Udāna, Itivuttaka, Suttanipāta
- Vimānavatthu, Petavatthu, Theragāthā, Therīgāthā
- Jātaka, Mahāniddesa, Cūḷaniddesa, Paṭisambhidāmagga
- Apadāna (Therāpadāna, Therīapadāna), Buddhavaṃsa, Cariyāpiṭaka
- Nettippakaraṇa, Peṭakopadesa, Milindapañha

## 4. Methodology

### 4.1 Text Normalization

The source texts underwent the following normalization:

1. **Niggahīta standardization**: All instances of ṁ converted to ṃ
2. **Whitespace normalization**: Multiple spaces collapsed to single space
3. **Encoding**: UTF-8 throughout

### 4.2 Tokenization

Text was tokenized using a regular expression pattern matching Pāli orthography:

```
[a-zA-ZāīūṭḍṇṅñṃḷĀĪŪṬḌṆṄÑṂḶ]+
```

This preserves all standard Pāli diacritics while splitting on punctuation and whitespace. All tokens were lowercased for dictionary lookup.

### 4.3 Lemmatization Process

For each token, the following process was applied:

1. **Direct lookup**: Query the DPD lookup table for the word form
2. **Sandhi check**: If the deconstructor field contains data, the word is a sandhi compound
3. **Headword retrieval**: For non-sandhi words, retrieve the first matching headword entry
4. **Component analysis**: For sandhi words, recursively lemmatize each component

### 4.4 Sandhi Handling

Pāli exhibits extensive sandhi (euphonic combination) where word boundaries are obscured. Examples:

| Surface Form | Components | Analysis |
|--------------|------------|----------|
| suppiyopi | suppiyo + api | proper noun + particle |
| etadavoca | etad + avoca | pronoun + verb |
| bhaborūpaṃ | bhava + arūpaṃ | noun + adjective |

The DPD deconstructor provides pre-analyzed sandhi splits for attested compounds. When a word has deconstructor data, we:

1. Parse the compound into components
2. Lemmatize each component separately
3. Store both the surface form and component analysis

### 4.5 Output Format

Each segment is annotated with token-level information:

```json
{
  "id": "dn1:1.1.3",
  "pali": "Suppiyopi kho paribbājako...",
  "tokens": [
    {
      "word": "suppiyopi",
      "sandhi": ["suppiyo", "api"],
      "components": [
        {"lemma": "suppiya", "pos": "masc", "root": "√pī"},
        {"lemma": "api", "pos": "ind"}
      ]
    },
    {
      "word": "kho",
      "lemma": "kho",
      "pos": "ind"
    },
    {
      "word": "paribbājako",
      "lemma": "paribbājaka",
      "pos": "masc",
      "root": "√vaj"
    }
  ]
}
```

Token fields:
- `word`: Surface form as it appears in the text
- `lemma`: Dictionary headword (null if sandhi compound)
- `pos`: Part of speech
- `root`: Verbal root with √ prefix (where applicable)
- `sandhi`: Component words (only for sandhi compounds)
- `components`: Lemma information for each sandhi component

## 5. Results

### 5.1 Coverage Statistics

| Metric | Value |
|--------|-------|
| Total word tokens | 1,618,486 |
| Unique word forms | 127,033 |
| Forms found | 123,493 |
| Forms not found | 4,100 |
| Sandhi compounds (DPD) | 42,440 |
| Particle splits | 84 |
| Metrical normalizations | 2,043 |
| Orthographic variants (-n→-ṃ) | 1,546 |
| DPPN proper nouns | 21 |
| **Lemmatization coverage** | **97.2%** |

### 5.2 Analysis of Unknown Words

The remaining 4,100 word forms (3.2%) not resolved by the lemmatizer fall into these categories:

1. **Hapax legomena**: Rare words occurring only once in the canon
2. **Complex compounds**: Multi-word compounds not in the DPD deconstructor
3. **Unusual orthographic variants**: Non-standard spellings beyond simple -n/-ṃ variation
4. **Rare proper nouns**: Names not matched by DPPN inflection patterns

The following categories were successfully handled by the improved lemmatizer:

| Category | Words Resolved | Method |
|----------|---------------|--------|
| Metrical lengthening | 2,043 | Normalize final long vowels (ā→a, ī→i, ū→u) |
| Orthographic variants | 1,546 | Normalize -n to -ṃ |
| Particle sandhi | 84 | Split trailing ca, api, ti, va, tu |
| Proper nouns | 21 | Match against DPPN with inflection handling |

**Note on DPPN matching**: The DPPN provides 3,945 proper name entries. Current matching handles common case endings (-ssa, -āya, -ena, -aṃ, etc.) but many proper nouns remain unmatched due to:
- Complex compound formations
- Unusual declension patterns
- Names not in DPPN

### 5.3 Most Frequent Lemmas

The most frequently occurring lemmas reflect the doctrinal and narrative content of the texts. Common categories include:

- **Grammatical particles**: ca, ti, eva, kho, api
- **Pronouns**: ta, ya, ima, eta, ahaṃ
- **Common verbs**: hoti, bhavati, karoti, vadati, passati
- **Doctrinal terms**: dhamma, bhikkhu, buddha, saṅgha, nibbāna

## 6. Data Availability

The complete corpus is available in JSON format:

```
data/
├── canonical/          # Normalized source texts (SC-based)
│   ├── dn/            # 34 suttas
│   ├── mn/            # 152 suttas
│   ├── sn/            # 56 saṃyuttas (1,819 suttas)
│   ├── an/            # 11 nipātas (1,408 suttas)
│   └── kn/            # 20 texts (2,351 items)
├── lemmatized/        # Annotated texts with lemmas
│   ├── dn/
│   ├── mn/
│   ├── sn/
│   ├── an/
│   ├── kn/
│   └── _stats.json    # Corpus statistics
├── suttacentral-ms/   # Raw SuttaCentral source
├── pts-text/          # PTS digitized editions
├── pts-pdf/           # PTS original PDFs
├── vri-raw/           # Chaṭṭha Saṅgāyana (VRI)
└── dpd/               # Digital Pāli Dictionary (SQLite)
```

## 7. Limitations and Future Work

### 7.1 Current Limitations

1. **Single base text**: Uses SuttaCentral edition only; variants from PTS/VRI not systematically incorporated
2. **Ambiguity resolution**: When multiple lemmas are possible, only the first DPD entry is used
3. **Context independence**: Lemmatization does not consider sentential context
4. **Vinaya and Abhidhamma**: This release covers only the Sutta Piṭaka
5. **PTS page-level only**: References are to page ranges, not precise line numbers

### 7.2 Future Directions

The goal is a **complete lemmatized Tipiṭaka based on PTS editions with variant apparatus**.

**Phase 1: Complete Tipiṭaka Coverage**

Currently only the Sutta Piṭaka is processed. The remaining piṭakas must be added:

| Piṭaka | Available Sources | Work Required |
|--------|-------------------|---------------|
| Vinaya | PTS (5 vols), VRI (5 files) | Parse, segment, align with PTS pages |
| Abhidhamma | PTS (12 vols), VRI (13 files) | Parse, segment, align with PTS pages |

Steps:
1. Parse VRI Vinaya/Abhidhamma mūla texts into segments
2. Create segment IDs based on PTS volume.page.line references
3. Run lemmatization pipeline on new texts
4. Integrate into unified corpus

**Phase 2: PTS as Authoritative Base**

The current release uses SuttaCentral (based on Chaṭṭha Saṅgāyana) as the base text. Future releases should:

1. **Adopt PTS as primary text**: Use PTS editions as the authoritative source
2. **Fine-grained citations**: Map every segment to PTS volume.page.line (e.g., D i 1.5)
3. **Retain SC segment IDs**: Maintain compatibility with SuttaCentral translations
4. **Document editorial choices**: Record where PTS was followed over other editions

**Phase 3: Variant Apparatus**

Record textual variants from multiple editions:

1. **Sources to collate**: PTS, VRI/CST (Chaṭṭha Saṅgāyana), BJT (Buddha Jayanti), SC
2. **Variant classification**:
   - Orthographic (spelling differences, e.g., -n/-ṃ)
   - Substantive (different words/readings)
   - Omissions/additions
   - Word order
3. **Machine-readable format**: Store variants in structured JSON alongside lemmatized text
4. **Preference rules**: Document which edition to prefer when they disagree

**Phase 4: Improving Lemmatization Coverage**

Current coverage is 95.5%. To reach higher coverage:

1. **Dictionary of Pali Proper Names**: Integrate G.P. Malalasekera's DPPN for person/place identification
2. **Orthographic normalization**: Expand variant handling beyond -n/-ṃ (e.g., -ṃ/-ŋ, doubled consonants)
3. **Hapax analysis**: Morphological analysis for rare words not in DPD
4. **Context-aware disambiguation**: When multiple lemmas are possible, use context to select

**Phase 5: Additional Enhancements**

1. **Syntactic annotation**: Add dependency parsing and phrase structure
2. **Translation alignment**: Link lemmatized Pāli segments to English translations
3. **Searchable interface**: Build web/CLI tools for querying the lemmatized corpus
4. **API access**: Provide programmatic access to lemma lookups and text search

## 8. Technical Implementation

Processing scripts are available in the `src/` directory:

| Script | Function |
|--------|----------|
| `build_canonical_*.py` | Generate normalized canonical texts |
| `dpd_lookup.py` | DPD interface module |
| `lemmatize_canon.py` | Full corpus lemmatization |

## 9. Acknowledgments

This work relies on the contributions of:

- **SuttaCentral** for the Mahāsaṅgīti digital edition and segmentation
- **Digital Pāli Dictionary** project for the comprehensive morphological database
- The broader community of Pāli digital humanities scholars

## 10. References

Digital Pāli Dictionary. (2026). Version 0.3.20260202. https://digitalpalidictionary.github.io

SuttaCentral. (n.d.). Bilara translation data. https://github.com/suttacentral/bilara-data

Mahāsaṅgīti Tipiṭaka Buddhavasse 2500. (1957). Sixth Buddhist Council edition.

---

*Document generated: February 2026*
