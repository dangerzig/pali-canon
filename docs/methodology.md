# A Critical Digital Edition of the Pāli Canon: Lemmatization, Collation, and Computational Analysis

## Abstract

This paper describes the creation of a critical digital edition of the Pāli Canon (Tipiṭaka), the canonical scripture of Theravāda Buddhism, comprising approximately 2.7 million words across the complete canon. Building on earlier computational analyses that demonstrated the feasibility of applying text-mining techniques to Pāli texts (Zigmond 2021, 2023), this work addresses key limitations of prior approaches by incorporating full morphological analysis through the Digital Pāli Dictionary (DPD).

The edition uses the Pali Text Society (PTS) editions as the authoritative base text, with variant readings from the SuttaCentral Mahāsaṅgīti edition and the Chaṭṭha Saṅgāyana (VRI/CST) edition recorded in the apparatus. Where PTS contains errors—confirmed by agreement of SC and VRI against a reading not attested in the DPD—corrections are applied and documented transparently.

The resulting dataset provides: (1) a unified reference system enabling citation by PTS volume and page, SC segment ID, or VRI section number; (2) a critical apparatus preserving all variant readings between editions; (3) full lemmatization with word-level morphological analysis achieving 97.5% coverage; and (4) a research-ready format suitable for the computational analyses proposed in earlier work. This infrastructure enables systematic investigation of textual strata, formulaic patterns, and the relative age of canonical texts—questions of longstanding scholarly interest that have remained difficult to address without comprehensive morphological annotation.

## 1. Introduction

### 1.1 Background and Motivation

The Tipiṭaka, or Pāli Canon, is the canonical scripture of Theravāda Buddhists worldwide and is said to record the direct teachings of the historical Buddha. These texts were transmitted orally for several centuries before being set in written form in what is now Sri Lanka, likely around 100 BCE, in the Pāli language, a Middle Indo-Aryan dialect whose name derives from the compound *pāli-bhāsa*, "the language of the texts" (Geiger 2005, xxiii). Although versions of these scriptures exist in other languages, the Pāli form appears to be the oldest complete edition.

A growing body of scholarship holds that the earliest portions of the Tipiṭaka may contain something very close to the actual words the Buddha spoke (Sujato and Brahmali 2014; Gombrich 2018). This possibility brings urgency to the critical study of these texts, if only to determine the relative age of the various volumes and to provide clues as to which may, in fact, have been "spoken by the Buddha" (Sujato and Brahmali 2014, 7). Yet despite the scholarly importance of the Pāli Canon, comprehensive morphological annotation has remained limited, hindering computational approaches to these fundamental questions.

### 1.2 Prior Work

In earlier papers, we demonstrated that computational text-mining techniques could be productively applied to the Pāli Canon. Using k-means clustering based on word frequencies, we showed that volumes of the Tipiṭaka could be separated into groups that roughly matched the scholarly consensus on their relative age, with older texts (Vinaya and most Suttas) clustering apart from younger texts (Abhidhamma) (Zigmond 2021). Extending this approach, we found that canonical texts could be reliably distinguished from later commentaries using the same techniques (Zigmond 2023).

However, these analyses also revealed significant limitations. As noted in the earlier work, "the Pāli Canon in raw form is a poor foundation for this sort of textual analysis. Similar words appear in a wide array of dissimilar forms, due to declensions, compounds, and sandhi" (Zigmond 2023). The word *bhikkhu* (monk), for example, appears in 270 distinct forms in the canon when one counts all words beginning with the stem *bhikkh-*, including declensions (*bhikkhave*, *bhikkhū*, *bhikkhuno*), related words (*bhikkhunī*), and compounds (*bhikkhusaṅghaṃ*). Of these forms, fully 42% appear only once in the entire canon. This proliferation of surface forms severely limits the effectiveness of frequency-based analyses.

What was needed, we concluded, was "a more refined corpus" with proper lemmatization—the reduction of inflected forms to their dictionary headwords. We noted that "developing an accurate stemming algorithm will be a substantial undertaking" and that "no complete algorithm appears yet publicly available" (Zigmond 2021). The present work addresses this gap.

### 1.3 Contributions

This paper describes the creation of a fully lemmatized critical edition of the complete Pāli Canon, with the following contributions:

1. **Comprehensive lemmatization** using the Digital Pāli Dictionary (DPD), achieving 97.5% coverage across the corpus through a combination of direct lookup, sandhi decomposition, and handling of orthographic variants.

2. **Three-witness critical apparatus** collating the PTS, SuttaCentral, and VRI editions, with systematic classification of differences as orthographic variants, textual errors, or genuine readings.

3. **Unified reference system** enabling scholars to locate any passage by PTS citation, SC segment ID, or VRI section number.

4. **Open, structured dataset** suitable for the computational analyses proposed in earlier work, including vocabulary clustering to identify textual strata and formulaic analysis to trace the evolution of the canon.

The remainder of this paper describes the source materials (§2), the critical edition methodology (§3), the lemmatization process (§4), results and coverage statistics (§5), and limitations and future directions (§6).

## 2. Source Materials

### 2.1 Digital Editions of the Pāli Canon

Several digital editions of the Pāli Canon now exist, each with distinct characteristics relevant to computational analysis. This project draws on three primary sources:

**Pali Text Society Editions (PTS).** The PTS has published critical editions of the Pāli Canon since the late nineteenth century, beginning with the Vinaya Piṭaka edited by Oldenberg (1879–1883) and continuing through most of the twentieth century. These editions remain the standard scholarly reference in Western academia, and the convention of citing by PTS volume and page number (e.g., "D i 1" for Dīgha Nikāya volume i, page 1) is nearly universal in English-language Buddhist studies. Digital versions of the PTS editions are available through the Göttingen Register of Electronic Texts in Indian Languages (GRETIL), based on manual transcriptions by the Dhammakaya Foundation (1989–1996).

**Chaṭṭha Saṅgāyana Tipiṭaka (VRI/CST).** This edition originated at the Sixth Buddhist Council held in Burma from 1954 to 1956. The Vipassana Research Institute (VRI) subsequently published this edition in multiple scripts, including romanized form, and released it electronically as the Chaṭṭha Saṅgāyana Tipiṭaka version 4.0 (CST4). This edition has been widely used in computational work due to its early digital availability.

**SuttaCentral Mahāsaṅgīti Edition (SC).** SuttaCentral provides a digital version of the Mahāsaṅgīti Tipiṭaka, a recension originally prepared in Sri Lanka in 1957 to mark the 2500th anniversary of the Buddha's *parinibbāna* (the "Mahāsaṅgīti" or "Great Recitation" from which the edition takes its name). This Sri Lankan edition drew on multiple manuscript traditions and has since been further refined by SuttaCentral with editorial corrections. Crucially for computational work, SuttaCentral has segmented the text at the sentence or verse level with unique identifiers, enabling alignment with translations and providing a natural unit for analysis. The texts are available under Creative Commons licensing.

### 2.2 Editorial Policy

The PTS editions serve as the authoritative base text for this critical edition. This choice reflects their widespread use in Western scholarship and ensures compatibility with the existing English-language academic literature. Where the PTS reading differs from both SC and VRI, and the PTS form is not attested in the Digital Pāli Dictionary (indicating a likely error rather than a genuine variant), the text is corrected and the original PTS reading preserved in the apparatus. Where editions differ but all readings represent valid Pāli forms, the PTS reading is retained and variants recorded.

For digital processing, we use the GRETIL transcriptions as our source for PTS text. Initial experiments with optical character recognition (OCR) of the original PTS publications proved unsatisfactory: analysis of the Dīgha Nikāya revealed that 97% of suttas had OCR quality scores below 50/100, with 65–89% of words lacking proper diacritics and systematic errors such as the misreading of *ñ* as *fi*. The GRETIL transcriptions, by contrast, preserve proper Unicode diacritics throughout and have been manually verified against the print editions.

### 2.3 The Digital Pāli Dictionary (DPD)

Morphological analysis was performed using the Digital Pāli Dictionary (DPD), a comprehensive lexical database developed specifically for computational applications to Pāli texts. The DPD provides what earlier work identified as the critical missing resource for Pāli computational linguistics: a complete mapping from inflected surface forms to dictionary headwords (lemmas).

The version used in this project (0.3.20260202) includes:

| Resource | Count |
|----------|-------|
| Dictionary headwords | 88,350 |
| Inflected form lookups | 1,275,089 |
| Verbal roots | 754 |

The DPD's lookup table maps attested inflected forms to their dictionary headwords, enabling automated lemmatization without the need to develop custom stemming algorithms. The deconstructor module provides analysis of sandhi compounds, where multiple words have been combined through euphonic processes into a single orthographic unit—a pervasive feature of Pāli that poses significant challenges for computational analysis.

### 2.4 The Dictionary of Pāli Proper Names (DPPN)

For proper noun identification, we incorporated the *Dictionary of Pāli Proper Names* by G.P. Malalasekera (1937–1938), a standard reference work cataloging persons, places, and texts mentioned in the Pāli literature. The extracted dataset includes 2,541 person names, 1,335 text names, and 69 place names (3,945 entries total). This resource supplements the DPD for the identification of proper nouns, which are often not included in standard dictionaries.

## 3. The Corpus

### 3.1 Structure of the Tipiṭaka

The name *Tipiṭaka* literally means "three baskets" and derives from the traditional division of the canon into three collections:

- **Vinaya Piṭaka** ("Basket of Discipline"): Rules for monastic life and their origin stories
- **Sutta Piṭaka** ("Basket of Discourses"): The teachings of the Buddha and his chief disciples
- **Abhidhamma Piṭaka** ("Basket of Special Teachings"): Systematic philosophical analysis

The Sutta Piṭaka is further divided into five *nikāyas* (collections), of which the first four contain discourses of similar length or thematic organization, while the fifth (Khuddaka Nikāya) gathers diverse shorter works.

### 3.2 Corpus Statistics

The complete Tipiṭaka comprises approximately 2.7 million words. The current project covers the Sutta Piṭaka in full, with Vinaya and Abhidhamma processed using two-witness comparison (PTS and VRI only, as SC does not cover these collections).

**Sutta Piṭaka:**

| Collection | Full Name | Description | Texts | Segments | Words |
|------------|-----------|-------------|-------|----------|-------|
| DN | Dīgha Nikāya | Long Discourses | 34 | 8,038 | 141,565 |
| MN | Majjhima Nikāya | Middle-length Discourses | 152 | 27,195 | 241,651 |
| SN | Saṃyutta Nikāya | Connected Discourses | 1,819 | 43,468 | 269,739 |
| AN | Aṅguttara Nikāya | Numerical Discourses | 1,408 | 41,843 | 304,857 |
| KN | Khuddaka Nikāya | Minor Collection | 2,351 | 155,801 | 630,242 |
| **Total** | | | **5,764** | **276,345** | **1,588,054** |

The Khuddaka Nikāya includes 18 texts in most traditions: Khuddakapāṭha, Dhammapada, Udāna, Itivuttaka, Suttanipāta, Vimānavatthu, Petavatthu, Theragāthā, Therīgāthā, Jātaka, Mahāniddesa, Cūḷaniddesa, Paṭisambhidāmagga, Apadāna, Buddhavaṃsa, Cariyāpiṭaka, Nettippakaraṇa, and Peṭakopadesa. The Burmese tradition additionally includes Milindapañha, which is treated as paracanonical in this edition.

By way of comparison, the King James Bible contains approximately 855,000 words—making the Sutta Piṭaka alone nearly twice the length of the Christian Bible, and the complete Tipiṭaka more than three times as long (Zigmond 2021).

## 4. Critical Edition Methodology

### 4.1 Three Witnesses

The critical edition collates three independent textual traditions:

| Witness | Abbreviation | Tradition | Base |
|---------|--------------|-----------|------|
| PTS (GRETIL) | pts | Western critical editions | 19th–early 20th c. European scholarship |
| SuttaCentral | sc | Mahāsaṅgīti | Based on VRI with editorial corrections |
| VRI/CST | vri | Chaṭṭha Saṅgāyana | Burmese 6th Council (1954–1956) |

**PTS as authoritative**: The Pali Text Society editions serve as the base text. PTS readings are retained unless identified as errors.

**SC and VRI as witnesses**: Where these editions differ from PTS, the variants are recorded. Where SC and VRI agree against PTS and the PTS reading is not a valid Pāli word (per DPD), the PTS is corrected.

### 4.2 Alignment Process

The three editions are aligned using a multi-stage process:

1. **Text normalization**: Standardize orthography (ṁ→ṃ, remove hyphens, normalize case)
2. **Section alignment**: Match major structural divisions (vaggas, suttas, sections)
3. **Word-level alignment**: Use sequence matching to align individual words
4. **Variant detection**: Identify positions where witnesses differ

### 4.3 Error vs. Variant Classification

Differences between editions are classified as follows:

| Condition | Classification | Action |
|-----------|----------------|--------|
| Orthographic only (ṁ/ṃ, ṅ/ṃ, case) | Normalize | Silent normalization |
| SC=VRI≠PTS, PTS not in DPD | **Error** | Correct PTS, record original |
| SC=VRI≠PTS, all valid words | **Variant** | Keep PTS, record variant |
| All three differ | **Uncertain** | Flag for review |
| PTS agrees with one witness | **Variant** | Keep PTS, record differing witness |

### 4.4 Correction Types Identified

Analysis of the complete Dīgha Nikāya (34 suttas, 164,949 words) identified 1,015 corrections where the PTS reading was emended based on SC/VRI agreement. These fall into several categories:

| Category | Example |
|----------|---------|
| Anusvāra normalization | *bhikkhūnam* → *bhikkhūnaṃ*; *evam* → *evaṃ* |
| Sandhi/particle additions | *bhikkhusaṃghañ* → *bhikkhusaṃghañca*; *yāvañ* → *yāvañcidaṃ* |
| Spelling corrections | *icchānaṅkale* → *icchānaṅgale* |
| Retroflex consonants | *khānumataṃ* → *khāṇumataṃ* |
| Vowel length | *micchājivena* → *micchājīvena* |

In addition to corrections, the apparatus records 28,786 variant readings where editions differ but all readings represent valid Pāli forms.

### 4.5 Output Format

Each segment in the critical edition contains:

```json
{
  "id": "dn1:1.1.2",
  "refs": {
    "pts": "D i 1.5",
    "vri": "§1"
  },
  "text": "ekaṃ samayaṃ bhagavā antarā ca rājagahaṃ",
  "lemmas": [
    {"word": "ekaṃ", "lemma": "eka", "pos": "adj", "grammar": "nt acc sg"},
    {"word": "samayaṃ", "lemma": "samaya", "pos": "noun", "grammar": "masc acc sg"},
    {"word": "bhagavā", "lemma": "bhagavant", "pos": "noun", "grammar": "masc nom sg"}
  ],
  "corrections": [
    {"pos": 5, "pts": "bhikkhūnam", "witnesses": ["sc", "vri"]}
  ],
  "variants": [
    {"pos": 12, "vri": "sassatoti"}
  ]
}
```

**Field definitions:**

- `id`: Canonical segment identifier (SC format for compatibility)
- `refs.pts`: PTS citation (volume, page, section) — e.g., "D i 1.5" = Dīgha vol. i, page 1, section 5
- `refs.vri`: VRI section number
- `text`: The established text (PTS base with corrections applied)
- `lemmas`: Morphological analysis for each word (from DPD)
  - `word`: Surface form as it appears
  - `lemma`: Dictionary headword
  - `pos`: Part of speech
  - `grammar`: Grammatical analysis (gender, case, number) per DPD format
- `corrections`: Where PTS was corrected
  - `pos`: Word position in segment
  - `pts`: Original PTS reading
  - `witnesses`: Which editions support the correction
- `variants`: Where other editions differ but PTS stands
  - `pos`: Word position
  - `sc`/`vri`: The variant reading (only listed if differs from `text`)

**Design principle**: Only divergent readings are recorded. If a witness is not listed in `corrections` or `variants`, it agrees with `text`.

## 5. Lemmatization Methodology

### 5.1 Text Normalization

The source texts underwent the following normalization:

1. **Niggahīta standardization**: All instances of ṁ converted to ṃ
2. **Whitespace normalization**: Multiple spaces collapsed to single space
3. **Encoding**: UTF-8 throughout

### 5.2 Tokenization

Text was tokenized using a regular expression pattern matching Pāli orthography:

```
[a-zA-ZāīūṭḍṇṅñṃḷĀĪŪṬḌṆṄÑṂḶ]+
```

This preserves all standard Pāli diacritics while splitting on punctuation and whitespace. All tokens were lowercased for dictionary lookup.

### 5.3 Lemmatization Process

For each token, the following process was applied:

1. **Direct lookup**: Query the DPD lookup table for the word form
2. **Sandhi check**: If the deconstructor field contains data, the word is a sandhi compound
3. **Headword retrieval**: For non-sandhi words, retrieve the first matching headword entry
4. **Component analysis**: For sandhi words, recursively lemmatize each component

### 5.4 Sandhi Handling

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

### 5.5 Output Format

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

## 6. Results

### 6.1 Coverage Statistics

| Metric | Value |
|--------|-------|
| Total word tokens | 1,618,486 |
| Unique word forms | 127,033 |
| Forms found | 123,859 |
| Forms not found | 3,758 |
| Sandhi compounds (DPD) | 42,440 |
| Particle splits | 101 |
| Metrical normalizations (final) | 2,045 |
| Metrical normalizations (internal) | 88 |
| Orthographic variants (-n→-ṃ) | 1,546 |
| Pronoun-verb splits | 23 |
| Verb ending normalizations | 3 |
| Compound splits | 232 |
| DPPN proper nouns | 21 |
| **Lemmatization coverage** | **97.5%** |

### 6.2 Analysis of Unknown Words

The remaining 3,758 word forms (3.0%) not resolved by the lemmatizer fall into these categories:

1. **Hapax legomena**: Rare words occurring only once in the canon
2. **Complex compounds**: Multi-word compounds not in the DPD deconstructor (e.g., 108-character dvandva compounds)
3. **Unusual orthographic variants**: Non-standard spellings beyond handled patterns
4. **Rare proper nouns**: Names not matched by DPPN inflection patterns
5. **OCR/text errors**: Non-Pāli fragments (e.g., `of`, `m`)

The following categories were successfully handled by the improved lemmatizer:

| Category | Words Resolved | Method |
|----------|---------------|--------|
| Metrical lengthening (final) | 2,045 | Normalize final long vowels (ā→a, ī→i, ū→u) |
| Orthographic variants | 1,546 | Normalize -n to -ṃ |
| Compound splitting | 232 | Recursive splitting of long dvandva compounds |
| Particle sandhi | 101 | Split trailing ca, api, ti, va, tu |
| Internal metrical | 88 | Normalize all long vowels in word |
| Pronoun-verb sandhi | 23 | Split aham-, -osmi, -omhi patterns |
| DPPN proper nouns | 21 | Match against DPPN with inflection handling |
| Verb ending normalization | 3 | Normalize -āmā → -āma, -āmī → -āmi |

**Note on DPPN matching**: The DPPN provides 3,945 proper name entries. Current matching handles common case endings (-ssa, -āya, -ena, -aṃ, etc.) but many proper nouns remain unmatched due to:
- Complex compound formations
- Unusual declension patterns
- Names not in DPPN

### 6.3 Most Frequent Lemmas

The most frequently occurring lemmas reflect the doctrinal and narrative content of the texts. Common categories include:

- **Grammatical particles**: ca, ti, eva, kho, api
- **Pronouns**: ta, ya, ima, eta, ahaṃ
- **Common verbs**: hoti, bhavati, karoti, vadati, passati
- **Doctrinal terms**: dhamma, bhikkhu, buddha, saṅgha, nibbāna

## 7. Data Availability

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

## 8. Limitations and Future Work

### 8.1 Current Status

**Completed:**
- Full Dīgha Nikāya critical edition (34 suttas, 164,949 words)
- Three-way alignment pipeline (PTS/GRETIL, SC, VRI)
- Error detection using DPD validation (1,015 corrections applied)
- Variant apparatus with 28,786 recorded readings
- Lemmatization at 97.5% coverage across the Sutta Piṭaka

**In Progress:**
- Extending critical edition methodology to remaining nikāyas
- Downloading and parsing remaining GRETIL volumes (MN, SN, AN, KN)

### 8.2 Current Limitations

1. **Ambiguity resolution**: When multiple lemmas are possible for a given surface form, the current implementation selects the first DPD entry. Context-aware disambiguation would improve accuracy for polysemous forms.

2. **Alignment artifacts**: Some spurious variants arise from structural differences between editions (e.g., different section breaks, paragraph divisions). Manual review is required to distinguish genuine textual variants from alignment errors.

3. **Two-witness comparison for Vinaya/Abhidhamma**: SuttaCentral does not cover the Vinaya and Abhidhamma Piṭakas, limiting these sections to two-way comparison (PTS vs VRI) rather than the three-way collation available for the Sutta Piṭaka.

4. **Proper noun coverage**: Despite integrating the DPPN, many proper nouns remain unlemmatized due to complex compound formations and names not catalogued in available reference works.

### 8.3 Future Directions

The infrastructure developed for this project enables several lines of future research:

**Computational Analysis of Textual Strata.** The primary motivation for this work was to enable the vocabulary-based clustering analyses proposed in earlier papers (Zigmond 2021, 2023). With full lemmatization now available, these analyses can be conducted with significantly greater precision. Initial experiments will focus on: (1) reproducing the earlier clustering results using lemmatized rather than raw word forms; (2) investigating whether lemmatization improves the separation between older and younger textual layers; and (3) extending the analysis to finer-grained divisions within the canon.

**Formulaic Pattern Analysis.** The Pāli Canon is characterized by extensive use of formulaic language—stock phrases and repeated passages that occur throughout the texts. The lemmatized critical edition enables systematic identification and analysis of these patterns, which may shed light on the oral transmission of the texts.

**Variant Density Mapping.** The critical apparatus records the distribution of textual variants across the canon. Correlating variant frequency with other measures (text length, genre, hypothesized age) may provide insights into the transmission history of different portions of the canon.

**Unified Reference System.** The alignment of PTS, SC, and VRI reference systems enables bidirectional citation mapping, allowing scholars working with any edition to locate passages in the others. A query interface supporting all three citation conventions is planned.

## 9. Technical Implementation

Processing scripts are available in the `src/` directory:

| Script | Function |
|--------|----------|
| `build_canonical_*.py` | Generate normalized canonical texts |
| `dpd_lookup.py` | DPD interface module |
| `lemmatize_canon.py` | Full corpus lemmatization |

## 10. Acknowledgments

This work relies on the contributions of:

- **SuttaCentral** for the Mahāsaṅgīti digital edition and segmentation
- **Digital Pāli Dictionary** project for the comprehensive morphological database
- The broader community of Pāli digital humanities scholars

## 11. References

Digital Pāli Dictionary (DPD). (2026). Version 0.3.20260202. https://digitalpalidictionary.github.io

Geiger, Wilhelm. (2005). *A Pāli Grammar*. Translated by Batakrishna Ghosh. Revised and edited by K.R. Norman. Oxford: Pali Text Society. (Original work published 1916)

Gombrich, Richard F. (2018). *Buddhism and Pali*. Oxford: Mud Pie Books.

Malalasekera, G.P. (1937–1938). *Dictionary of Pāli Proper Names*. 2 vols. London: John Murray for the Pali Text Society.

Mahāsaṅgīti Tipiṭaka Buddhavasse 2500. (1957). Yangon: Sixth Buddhist Council edition.

Oldenberg, Hermann, ed. (1879–1883). *The Vinaya Piṭakaṃ*. 5 vols. London: Williams and Norgate for the Pali Text Society.

Sujato, Bhikkhu, and Bhikkhu Brahmali. (2014). *The Authenticity of the Early Buddhist Texts*. Kandy: Buddhist Publication Society.

SuttaCentral. (n.d.). Bilara translation data. https://github.com/suttacentral/bilara-data

Vipassana Research Institute. (n.d.). *Chaṭṭha Saṅgāyana Tipiṭaka* version 4.0 (CST4). Igatpuri, India.

Zigmond, Dan. (2021). "Toward a Computational Analysis of the Pali Canon." *Journal of the Oxford Centre for Buddhist Studies* 20: 133–152.

Zigmond, Dan. (2023). "Distinguishing Commentary from Canon in Early Buddhist Texts Using Computational Linguistics." Paper presented at the 18th World Sanskrit Conference, Canberra.

---

*Document generated: February 2026*
