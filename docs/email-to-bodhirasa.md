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

- **Coverage: 97.5%** (123,869 of 127,032 unique words identified)
- Sandhi decompositions: 42,441
- Orthographic variant normalizations (-n/-m → -ṃ): 1,553
- Metrical variant normalizations: 2,133
- DPPN proper noun matches: 21

This is a testament to the comprehensiveness of DPD!

## Unknown Words

I identified **3,235 unique word forms** that weren't found in DPD's lookup table. After filtering out English noise from source markup and analyzing the patterns, the breakdown is:

| Category | Count | Notes |
|----------|-------|-------|
| Potential new headwords | 2,830 | Genuine candidates for DPD |
| Long compounds (25+ chars) | 192 | Complex dvandva/bahuvrīhi |
| Metrical variants | 175 | Unusual verbal forms |
| Story/section titles | 21 | vatthu, vagga endings |
| Pronoun-verb fusions | 9 | -osmi/-amhi sandhi |
| Jhāna compounds | 3 | paṭhamajhāna, etc. |

**96% of the potential new headwords (2,733 of 2,830) come from the Khuddaka Nikāya**—particularly the Jātaka, Apadāna, Milindapañha, Netti, and verse texts.

### Examples of Potential New Headwords

From **Netti/Peṭakopadesa** (technical terms):
- `samāropano` (36x) - appears to be a technical term
- `otaraṇo` (26x) - technical term
- `vevacano` (23x) - synonym/gloss marker

From **Milindapañha**:
- `visajjanā` (16x) - answering/response
- `khīḷito` (12x) - played/sported

From **Jātaka/Apadāna**:
- `yamalokikā` (11x) - relating to the realm of Yama
- `nekāsī` (10x) - verb form
- `haṃcivagga`, `sereyyavagga`, etc. - chapter titles

From **Nikāyas** (rare but interesting):
- `tipissa` (55x in SN) - appears in specific contexts
- `abhisamparāyañcā` (27x in AN) - compound form
- `ayokhilaṃ` (25x across AN/KN) - iron stake

## How Can I Help?

I'd be happy to contribute this data to DPD if it would be useful. Before preparing a formal submission, I wanted to ask:

1. **What format would be most helpful?** (CSV, JSON, plain text list?)
2. **What information should I include?** (word form, suggested lemma, part of speech, location in canon?)
3. **Should I separate the categories** (technical terms vs. verse forms vs. titles)?
4. **Are there any categories you'd prefer I exclude?** (e.g., chapter titles, extremely long compounds)

I can provide the words with their locations in the canon (e.g., "found in Ja 470") and, where determinable, suggested parts of speech based on morphological analysis.

## Project Details

The project is open source and available at:
https://github.com/dangerzig/pali-canon

It includes ~9,200 lines of Python code for parsing, collating, and lemmatizing the texts.

Thank you for creating such a valuable resource for Pāli studies. DPD has been indispensable for this work.

With mettā,

Rev. Dan Zigmond
Independent Scholar
Palo Alto, California
djz@shmonk.com

---

*P.S. I also noticed that the jhāna compounds (`paṭhamajhāna`, `dutiyajhāna`, `tatiyajhāna`) are quite common in meditation texts but weren't found in the lookup. These might be quick additions if they're not already planned.*
