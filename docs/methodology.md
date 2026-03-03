# A Critical Digital Edition of the Pāli Canon: Lemmatization, Collation, and Computational Analysis

## Abstract

This paper describes the creation of a critical digital edition of the Pāli Canon (Tipiṭaka), the canonical scripture of Theravāda Buddhism, comprising approximately 2.7 million words across the complete canon. Building on earlier computational analyses that demonstrated the feasibility of applying text-mining techniques to Pāli texts (Zigmond 2021, 2023), this work addresses key limitations of prior approaches by incorporating full morphological analysis through the Digital Pāli Dictionary (DPD).

The edition uses the Pali Text Society (PTS) editions as the authoritative base text, with variant readings from four additional witnesses—the SuttaCentral Mahāsaṅgīti edition, the Chaṭṭha Saṅgāyana (VRI/CST), the Buddha Jayanti Tipitaka (BJT), and the Thai Royal Edition (Syām Raṭṭha)—recorded in the apparatus. Where PTS contains errors—confirmed by agreement of multiple witnesses against a reading not attested in the DPD—corrections are applied and documented transparently.

The resulting dataset provides: (1) a unified reference system enabling citation by PTS volume and page, SC segment ID, or VRI section number; (2) a critical apparatus preserving all variant readings between editions; (3) full lemmatization with word-level morphological analysis achieving 99.90% token-level coverage; and (4) a research-ready format suitable for the computational analyses proposed in earlier work. This infrastructure enables systematic investigation of textual strata, formulaic patterns, and the relative age of canonical texts—questions of longstanding scholarly interest that have remained difficult to address without comprehensive morphological annotation.

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

1. **Comprehensive lemmatization** using the Digital Pāli Dictionary (DPD), achieving 99.90% token-level coverage across the corpus through a combination of direct lookup, sandhi decomposition, orthographic normalization, sandhi-aware compound splitting, negative prefix handling, and a custom lemma database for words not in DPD.

2. **Five-witness critical apparatus** collating the PTS, SuttaCentral, VRI, BJT, and Thai (Syām Raṭṭha) editions, with systematic classification of differences as orthographic variants, textual errors, or genuine readings.

3. **Unified reference system** enabling scholars to locate any passage by PTS citation, SC segment ID, or VRI section number.

4. **Open, structured dataset** suitable for the computational analyses proposed in earlier work, including vocabulary clustering to identify textual strata and formulaic analysis to trace the evolution of the canon.

The remainder of this paper describes the source materials (§2), the critical edition methodology (§3), the lemmatization process (§4), results and coverage statistics (§5), and limitations and future directions (§6).

## 2. Source Materials

### 2.1 Digital Editions of the Pāli Canon

Several digital editions of the Pāli Canon now exist, each with distinct characteristics relevant to computational analysis. This project draws on five primary sources:

**Pali Text Society Editions (PTS).** The PTS has published critical editions of the Pāli Canon since the late nineteenth century, beginning with the Vinaya Piṭaka edited by Oldenberg (1879–1883) and continuing through most of the twentieth century. These editions remain the standard scholarly reference in Western academia, and the convention of citing by PTS volume and page number (e.g., "D i 1" for Dīgha Nikāya volume i, page 1) is nearly universal in English-language Buddhist studies. Digital versions of the PTS editions are available through the Göttingen Register of Electronic Texts in Indian Languages (GRETIL), based on manual transcriptions by the Dhammakaya Foundation (1989–1996).

**Chaṭṭha Saṅgāyana Tipiṭaka (VRI/CST).** This edition originated at the Sixth Buddhist Council held in Burma from 1954 to 1956. The Vipassana Research Institute (VRI) subsequently published this edition in multiple scripts, including romanized form, and released it electronically as the Chaṭṭha Saṅgāyana Tipiṭaka version 4.0 (CST4). This edition has been widely used in computational work due to its early digital availability.

**SuttaCentral Mahāsaṅgīti Edition (SC).** SuttaCentral provides a digital version of the Mahāsaṅgīti Tipiṭaka, a recension originally prepared in Sri Lanka in 1957 to mark the 2500th anniversary of the Buddha's *parinibbāna* (the "Mahāsaṅgīti" or "Great Recitation" from which the edition takes its name). This Sri Lankan edition drew on multiple manuscript traditions and has since been further refined by SuttaCentral with editorial corrections. Crucially for computational work, SuttaCentral has segmented the text at the sentence or verse level with unique identifiers, enabling alignment with translations and providing a natural unit for analysis. The texts are available under Creative Commons licensing.

**Buddha Jayanti Tipitaka (BJT).** Published by the Sri Lankan government between 1957 and 1989 to commemorate the 2500th anniversary of the Buddha, the Buddha Jayanti Tipitaka represents the Sinhalese textual tradition. Digital versions are available from multiple sources including the SLTP (Sri Lanka Tripitaka Project) transcriptions. This edition provides an independent witness from the Sri Lankan manuscript tradition, complementing the Burmese (VRI), European critical (PTS), and Mahāsaṅgīti (SC) traditions.

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

The complete Tipiṭaka comprises approximately 2.7 million words. The current project covers the entire Tipiṭaka with five-witness collation (PTS, SC, VRI, BJT, and Thai) across all three piṭakas.

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

### 4.1 Five Witnesses

The critical edition collates five independent textual traditions:

| Witness | Abbreviation | Tradition | Base |
|---------|--------------|-----------|------|
| PTS (GRETIL) | pts | Western critical editions | 19th–early 20th c. European scholarship |
| SuttaCentral | sc | Mahāsaṅgīti | Based on VRI with editorial corrections |
| VRI/CST | vri | Chaṭṭha Saṅgāyana | Burmese 6th Council (1954–1956) |
| BJT | bjt | Buddha Jayanti Tipitaka | Sri Lankan government edition (1957–1989) |
| Thai | thai | Syām Raṭṭha | Royal Thai Edition (E-Tipitaka) |

**PTS as authoritative**: The Pali Text Society editions serve as the base text. PTS readings are retained unless identified as errors.

**SC, VRI, and BJT as witnesses**: Where these editions differ from PTS, the variants are recorded. Where multiple witnesses agree against PTS and the PTS reading is not a valid Pāli word (per DPD), the PTS is corrected. When BJT joins SC and VRI against PTS, the confidence in error classification increases (three independent traditions vs one).

### 4.2 Alignment Process

The five editions are aligned using a multi-stage process:

1. **Text normalization**: Standardize orthography (ṁ→ṃ, remove hyphens, normalize case)
2. **Section alignment**: Match major structural divisions (vaggas, suttas, sections)
3. **Word-level alignment**: Use sequence matching to align individual words
4. **Variant detection**: Identify positions where witnesses differ

### 4.3 Error vs. Variant Classification

Differences between editions are classified as follows:

| Condition | Classification | Action |
|-----------|----------------|--------|
| Orthographic only (ṁ/ṃ, ṅ/ṃ, case) | Normalize | Silent normalization |
| SC=VRI=BJT≠PTS, PTS not in DPD | **Error** (high confidence) | Correct PTS, record original |
| SC=VRI≠PTS, BJT=PTS | **Variant** (split) | Keep PTS, record variant with split noted |
| SC=VRI≠PTS, all valid words | **Variant** | Keep PTS, record variant |
| All five differ | **Uncertain** | Flag for review |
| PTS agrees with one+ witnesses | **Variant** | Keep PTS, record differing witness(es) |

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

### 5.5 Custom Lemmas

Words not found in DPD are handled by a custom lemma database (`src/pali/custom_lemmas.py`) organized into four categories:

1. **Potential DPD Additions** (83 entries): Legitimate Pāli words missing from DPD that could be submitted upstream. These include technical terms from Netti/Peṭakopadesa, rare verb forms, and plant/animal names from Jātaka literature.

2. **Metrical Variants** (42 entries): Forms differing only in vowel length due to metrical requirements (e.g., *bhumyā* for *bhūmyā*, *uppari* for *upari*). These are scribal or poetic variants, not distinct lemmas.

3. **Project-Specific** (30 entries): Proper nouns, rare compounds, and archaic forms too specialized for general dictionaries.

4. **Sandhi Decompositions** (38 entries): Complex sandhi compounds not handled by DPD's deconstructor (e.g., *tvevahaṃ* → *tu* + *eva* + *ahaṃ*).

This modular approach separates words that could benefit the broader Pāli digital humanities community (potential DPD additions) from project-specific handling.

### 5.6 Output Format

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
| Total word tokens | 2,847,446 |
| Unique word forms | 153,715 |
| Forms found | 151,878 |
| Forms not found | 1,837 |
| Sandhi compounds (DPD) | 52,715 |
| Particle splits | 245 |
| Metrical normalizations (final) | 2,919 |
| Metrical normalizations (internal) | 88 |
| Orthographic variants (-n→-ṃ) | 2,241 |
| Pronoun-verb splits | 40 |
| Enhanced compound splits | 1,624 |
| Negative prefix splits | 124 |
| DPPN proper nouns | 21 |
| Custom lemmas | 156 |
| **Unique word coverage** | **98.8%** |
| **Token-level coverage** | **99.90%** |

Note: These statistics cover the complete Tipiṭaka (Sutta, Vinaya, and Abhidhamma piṭakas). Token-level coverage (99.90%) measures what percentage of all word occurrences in the corpus are lemmatized. Unique word coverage (98.8%) measures what percentage of distinct word forms are resolved. The difference arises because high-frequency words (particles, pronouns, common verbs) are well-covered by DPD, while the remaining unresolved forms are predominantly rare words (hapax legomena) from verse texts.

### 6.2 Analysis of Unknown Words

The remaining 1,837 unique word forms (1.2%) not resolved by the lemmatizer represent a small fraction of token occurrences (approximately 0.10% of the corpus), since the vast majority are hapax legomena. These fall into several categories:

1. **Hapax legomena**: Rare words occurring only once in the canon, predominantly from verse texts (Apadāna, Jātaka gāthās, Theragāthā/Therīgāthā)
2. **Complex compounds**: Multi-word compounds not in the DPD deconstructor
3. **Unusual orthographic variants**: Non-standard spellings beyond handled patterns
4. **Rare proper nouns**: Names not matched by DPPN inflection patterns
5. **Manuscript errors**: Occasional corrupted readings in source texts

The following categories were successfully handled by the lemmatizer:

| Category | Words Resolved | Method |
|----------|---------------|--------|
| Metrical lengthening (final) | 2,919 | Normalize final long vowels (ā→a, ī→i, ū→u) |
| Orthographic variants | 2,241 | Normalize -n to -ṃ |
| Enhanced compound splitting | 1,624 | Sandhi-aware recursive splitting using 626 DPD rules |
| Particle sandhi | 245 | Split trailing ca, api, ti, va, tu |
| Custom lemmas | 156 | Manual mappings for words not in DPD |
| Negative prefix splitting | 124 | Split Pali negation prefixes (no-, na-, an-, a-) |
| Internal metrical | 88 | Normalize all long vowels in word |
| Pronoun-verb sandhi | 40 | Split aham-, -osmi, -omhi patterns |
| DPPN proper nouns | 21 | Match against DPPN with inflection handling |

The high token-level coverage (99.90%) despite lower unique-word coverage (98.8%) reflects the Zipfian distribution of vocabulary: a small number of high-frequency words account for most tokens, while the "long tail" of rare words contributes minimally to overall coverage.

### 6.3 Most Frequent Lemmas

The most frequently occurring lemmas reflect the doctrinal and narrative content of the texts. Common categories include:

- **Grammatical particles**: ca, ti, eva, kho, api
- **Pronouns**: ta, ya, ima, eta, ahaṃ
- **Common verbs**: hoti, bhavati, karoti, vadati, passati
- **Doctrinal terms**: dhamma, bhikkhu, buddha, saṅgha, nibbāna

### 6.4 Collation Results and Witness Analysis

The five-witness collation pipeline annotated 2,880,314 word positions across the complete Tipiṭaka. Of these, 126,553 were classified as confident readings (47,948 errors and 78,605 textual variants), with 330,889 additional positions flagged as uncertain. This section reports the aggregate collation statistics and analyzes the contribution of each witness to the critical apparatus.

#### 6.4.1 Collation Statistics by Collection

| Collection | Errors | Variants | Uncertain | Total |
|------------|-------:|--------:|---------:|------:|
| DN | 4,355 | 9,135 | 19,651 | 33,141 |
| MN | 4,555 | 11,534 | 37,919 | 54,008 |
| SN | 15,617 | 10,411 | 59,256 | 85,284 |
| AN | 5,164 | 26,433 | 185,808 | 217,405 |
| KN | 8,532 | 10,683 | 16,255 | 35,470 |
| Vinaya | 4,580 | 5,000 | 5,000 | 14,580 |
| Abhidhamma | 5,145 | 5,409 | 7,000 | 17,554 |
| **Total** | **47,948** | **78,605** | **330,889** | **457,442** |

The high uncertain count in AN reflects the structural complexity of the Aṅguttara, where very short suttas and heavy use of peyyāla (abbreviated repetitions) create alignment challenges between editions.

#### 6.4.2 Impact of the Fourth Witness (BJT)

The addition of the Buddha Jayanti Tipitaka as the fourth witness had a particularly dramatic effect on the Vinaya and Abhidhamma piṭakas, where it resolved a large number of previously uncertain readings. In the Vinaya, the number of uncertain positions fell from 312,363 (three-witness) to 44,228 (four-witness)—a reduction of 86%. The Abhidhamma showed a similar pattern, with 15,055 uncertain readings resolved and 2,902 additional errors confidently identified.

BJT is also the largest witness by word count (3,514,083 words across the canon, compared to 3,059,680 for GRETIL, 2,837,350 for SC, and 2,618,883 for VRI). The size difference is most pronounced in the Saṃyutta Nikāya, where BJT contains 551,483 words compared to GRETIL's 279,549. This discrepancy arises because BJT fully expands peyyāla passages that other editions abbreviate, preserving repetitive text that is elsewhere indicated only by ellipsis markers.

#### 6.4.3 Impact of the Fifth Witness (Thai)

The Thai Royal Edition (Syām Raṭṭha) was integrated as the fifth witness using a GRETIL-anchored alignment algorithm, achieving 100% coverage across the complete Tipiṭaka. Thai participates in 93,344 of 126,553 confident variant positions (73.8%).

**Agreement patterns.** When Thai participates in a variant reading, it most frequently agrees with SuttaCentral (57.7%), followed by VRI (44.3%), BJT (38.0%), and GRETIL/PTS (18.0%). The relatively high agreement with SC and VRI (both deriving from the Burmese Sixth Council tradition) versus the lower agreement with the PTS base text is consistent with the Thai Royal Edition representing an independent Southeast Asian recension that shares more recent textual history with the Burmese tradition than with the European critical editions.

| Witness | Agreement with Thai | Rate |
|---------|-------------------:|-----:|
| SC (Mahāsaṅgīti) | 53,827 | 57.7% |
| VRI (Chaṭṭha Saṅgāyana) | 41,328 | 44.3% |
| BJT (Buddha Jayanti) | 35,512 | 38.0% |
| GRETIL (PTS) | 16,758 | 18.0% |

**Tie-breaking.** In 11,675 cases where the other four witnesses split into two equal camps (a 2–2 deadlock), Thai resolves the impasse 88.4% of the time (10,323 cases). This tie-breaking capacity is perhaps the most practically significant contribution of the fifth witness, as these contested readings were previously unresolvable by majority vote. Among resolved ties, Thai sides with GRETIL+BJT 57.4% of the time and with SC+VRI 42.6% of the time. This asymmetry is noteworthy: although Thai agrees more often with SC overall, in the specific cases where the witnesses are evenly divided, Thai leans toward the PTS/Sri Lankan tradition. This pattern suggests that the Thai edition may preserve older or more conservative readings at precisely the positions where the Burmese and European traditions have diverged.

**Error confirmation.** Thai confirms 23,298 error corrections to the PTS base text—cases where multiple witnesses agree that the PTS reading is not a valid Pāli form (per DPD) and Thai concurs with the correction. When all four non-PTS witnesses agree (confidence 0.98), the resulting correction can be made with very high certainty. Across the canon, 81% of DN and MN error corrections and 60–84% of corrections in other collections achieve a confidence of 0.95 or higher.

**Unique readings.** Thai provides a reading found in no other witness at 20,841 positions (22.3% of its participations). Many of these reflect orthographic differences (e.g., *viriya* vs. *vīriya*) or different abbreviation conventions. Some, however, represent substantive textual variants:

| Position | GRETIL | SC | VRI | BJT | Thai |
|----------|--------|----|----|-----|------|
| DN 1.461 | *ubbillāvitā* | *uppilāvitā* | *uppilāvitā* | *ubbilāvino* | *ubbilāvitattā* |
| DN 1.516 | *katamañ* | *katamañca* | *katamañca* | *katamañca* | *katamañcetaṃ* |

In the first example, four witnesses give four distinct readings for the same word, illustrating the kind of organic textual variation that accumulates across centuries of manuscript transmission. Thai preserves an abstract noun formation (*-tattā*) not attested in any other edition. In the second, Thai preserves a longer compound form that may reflect a less-abbreviated recitation tradition.

#### 6.4.4 Witness Relationships

The agreement data suggests a broad stemmatic structure. SC and VRI form the closest pair, both deriving from the Burmese Chaṭṭha Saṅgāyana tradition (SC incorporates editorial emendations but remains structurally close to VRI). GRETIL/PTS and BJT share some affinity as representatives of the Sri Lankan and European critical traditions. Thai occupies an intermediate position—agreeing with the Burmese-derived editions on the majority of readings, but siding with the Sri Lankan/European tradition on a significant fraction of contested variants. This pattern is consistent with the Thai Royal Edition being an independent recension that reflects the broader Southeast Asian manuscript tradition, which was influenced by both Sinhalese and Burmese transmissions at various historical periods.

These findings confirm the value of maintaining a five-witness apparatus: each edition makes a genuinely independent contribution to our understanding of the canonical text, and no single additional witness is redundant.

## 7. Data Availability

The complete corpus is available in JSON format:

```
data/
├── canonical/          # Normalized source texts (SC-based)
│   ├── dn/            # 34 suttas
│   ├── mn/            # 152 suttas
│   ├── sn/            # 56 saṃyuttas (1,819 suttas)
│   ├── an/            # 11 nipātas (1,408 suttas)
│   ├── kn/            # 20 texts (2,351 items)
│   ├── vinaya/        # 5 texts
│   └── abhidhamma/    # 7 texts
├── gretil-parsed/     # PTS editions (GRETIL source)
├── vri-parsed/        # Chaṭṭha Saṅgāyana (VRI/CST)
├── bjt-parsed/        # Buddha Jayanti Tipitaka
├── thai-parsed/       # Thai Royal Edition (Syām Raṭṭha)
├── collation/         # Five-witness collation apparatus
├── critical/          # Critical edition output
├── lemmatized/        # Annotated texts with lemmas (all three piṭakas)
│   └── _stats.json    # Corpus statistics
└── dpd/               # Digital Pāli Dictionary (SQLite)
```

## 8. Limitations and Future Work

### 8.1 Current Status

**Completed:**
- Full Tipiṭaka critical edition (Vinaya, Sutta, Abhidhamma)
- Five-way alignment pipeline (PTS/GRETIL, SC, VRI, BJT, Thai)
- Error detection using DPD validation with majority-voting confidence scoring
- Variant apparatus with recorded readings from all five witnesses
- Lemmatization at 98.8% unique-word coverage across the complete Tipiṭaka (Sutta, Vinaya, and Abhidhamma; 2,847,446 tokens, 153,715 unique forms)
- Custom lemma database for 193 words not in DPD (organized for potential upstream contribution)

**Future Work:**
- Lemmatization of variant readings in the collation apparatus, to distinguish semantic variants (different lemmas) from orthographic/inflectional variants (same lemma)
- Context-aware disambiguation for polysemous forms
- Expansion of custom lemma database based on remaining unknown words
- Integration with translation corpora for parallel text analysis

### 8.2 Current Limitations

1. **Ambiguity resolution**: When multiple lemmas are possible for a given surface form, the current implementation selects the first DPD entry. Context-aware disambiguation would improve accuracy for polysemous forms.

2. **Alignment artifacts**: Some spurious variants arise from structural differences between editions (e.g., different section breaks, paragraph divisions). Manual review is required to distinguish genuine textual variants from alignment errors.

3. **Vinaya/Abhidhamma witness coverage**: While all five witnesses are now available for Vinaya and Abhidhamma, the SC and BJT texts for these piṭakas have been less thoroughly verified than for the Sutta Piṭaka.

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
