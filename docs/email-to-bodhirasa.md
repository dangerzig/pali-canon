# Email to Bodhirasa (DPD Author)

**To:** digitalpalidictionary@gmail.com
**Subject:** Potential contribution: Unknown words from Pāli Canon critical edition project

---

Dear Venerable Bodhirasa,

I hope this message finds you well. I'm writing to share some findings from a digital critical edition project I've been working on, which may be useful for the Digital Pāli Dictionary.

## About the Project

I've been developing a computational critical edition of the complete Pāli Tipiṭaka, collating three independent textual witnesses:

- **GRETIL** (PTS edition transcriptions)
- **VRI** (Chaṭṭha Saṅgāyana CST4)
- **SuttaCentral** (Mahāsaṅgīti edition)

As part of this work, I used DPD (version 0.3.20260202) to lemmatize the entire SuttaCentral corpus—approximately 1.6 million word tokens representing 127,032 unique word forms.

## Lemmatization Results

The results were excellent:

- **Coverage: 97.7%** (124,104 of 127,032 unique words identified)
- Sandhi decompositions: 42,441
- Orthographic variant normalizations (-n/-m → -ṃ): 1,553
- Metrical variant normalizations: 2,133+
- DPPN proper noun matches: 21

This is a testament to the comprehensiveness of DPD!

### Additional Patterns We Handled

Beyond DPD's built-in lookup, our lemmatizer handles several predictable patterns:

| Pattern | Count | Examples |
|---------|-------|----------|
| Jhāna compounds | 3 | paṭhamajhāna, dutiyajhāna |
| Chapter/story titles | 23 | haṃcivagga, sereyyavagga |
| Apadāna titles | 144 | koraṇḍapupphiyattheraapadāna |
| Causative absolutives | 79 | abhinivajjayitvā, avatthāpetvā |
| Pronoun-verb fusions | 23 | dubbalohamasmi, āyāhamasmi |
| Short pronoun variants | 3 | m→maṃ, tan→taṃ |

## Unknown Words

After filtering handled patterns, **3,002 unique word forms** remain unidentified. These appear to be genuine candidates for DPD consideration.

### Distribution

**96% come from the Khuddaka Nikāya** (2,889 words):
- Cūḷaniddesa/Mahāniddesa: technical commentary terms
- Jātaka: narrative vocabulary, proper nouns
- Apadāna: verse forms, hagiographic terms
- Milindapañha: philosophical/debate vocabulary
- Netti/Peṭakopadesa: hermeneutical technical terms

Only 113 unknowns from DN/MN/SN/AN combined.

### Examples of Potential New Headwords

From **Netti/Peṭakopadesa** (technical terms):
- `samāropano` (36x) - technical term
- `otaraṇo` (26x) - technical term
- `vevacano` (23x) - synonym/gloss marker

From **Cūḷaniddesa/Mahāniddesa**:
- `iccā` (22x) - possibly iti+ca sandhi
- `dakkhamāno` (8x) - verb form

From **Milindapañha**:
- `visajjanā` (16x) - answering/response
- `khīḷito` (12x) - played/sported

From **Jātaka/Apadāna**:
- `yamalokikā` (11x) - relating to the realm of Yama
- `nekāsī` (10x) - verb form
- `varākiyā` (9x) - adjective form

From **Nikāyas** (rare but interesting):
- `tipissa` (55x in SN) - appears in specific contexts
- `ayokhilaṃ` (25x across AN/KN) - iron stake
- `osāriyamānāni` (7x in DN) - being led away

## How Can I Help?

I'd be happy to contribute this data to DPD if it would be useful. Before preparing a formal submission, I wanted to ask:

1. **What format would be most helpful?** (CSV, JSON, plain text list?)
2. **What information should I include?** (word form, suggested lemma, part of speech, location in canon?)
3. **Should I prioritize certain categories?** (high-frequency words? Nikāya words over KN?)
4. **Are there any categories you'd prefer I exclude?** (e.g., extremely long compounds, obvious proper nouns)

I can provide the words with their locations in the canon and, where determinable, suggested parts of speech based on morphological analysis.

## Project Details

The project is open source and available at:
https://github.com/dangerzig/pali-canon

It includes ~9,400 lines of Python code for parsing, collating, and lemmatizing the texts.

Thank you for creating such a valuable resource for Pāli studies. DPD has been indispensable for this work.

With mettā,

Rev. Dan Zigmond
Independent Scholar
Palo Alto, California
djz@shmonk.com

---

*P.S. I also noticed that the jhāna compounds (`paṭhamajhāna`, `dutiyajhāna`, `tatiyajhāna`) are quite common in meditation texts but weren't found in the lookup. We've handled them in our lemmatizer, but they might be worth adding to DPD if not already planned.*
