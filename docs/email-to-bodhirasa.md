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

As part of this work, I used DPD (version 0.3.20260202) to lemmatize the entire SuttaCentral corpus—approximately 1.6 million word tokens representing 127,033 unique word forms.

## Lemmatization Results

The results were excellent:

- **Coverage: 97.5%** (123,859 of 127,033 unique words identified)
- Sandhi decompositions: 42,440
- Metrical variant normalizations: 2,133
- DPPN proper noun matches: 21

This is a testament to the comprehensiveness of DPD!

## Unknown Words

I identified **3,758 unique word forms** that weren't found in DPD's lookup table. Interestingly, **97% of these come from the Khuddaka Nikāya**—particularly the Jātaka, Apadāna, Therīgāthā, and other verse texts.

The main categories appear to be:

1. **Pronoun-verb fusions** (11 words)
   Examples: `sakyaputtiyāmhā`, `nibbānādhimuttohama`, `anupādānohama`

2. **Jhāna compound forms** (3 words)
   `paṭhamajhāna`, `dutiyajhāna`, `tatiyajhāna`

3. **Metrical variants** (~110 words)
   Final vowel lengthening in verse: `atāpī`, `kusalāyātikā`, `anvāvisiṭṭhā`

4. **Long compounds** (~10 words)
   `sokaparidevadukkhadomanassupāyāsaā`, `ubbhegauttāsabhayāpanūdano`

5. **Story titles** from Jātaka/Apadāna (4 words)
   `kumbaghosakaseṭṭhivatthu`, `patipūjikakumārivatthu`

6. **Potential new headwords** (~157 words)
   Various forms not matching any normalization strategy

## How Can I Help?

I'd be happy to contribute this data to DPD if it would be useful. Before preparing a formal submission, I wanted to ask:

1. **What format would be most helpful?** (CSV, JSON, plain text list?)
2. **What information should I include?** (word form, suggested lemma, part of speech, location in canon?)
3. **Should I separate the categories** (sandhi forms vs. potential new headwords)?
4. **Are there any categories you'd prefer I exclude?** (e.g., obvious OCR errors, English words from markup)

I can provide the words with their locations in the canon (e.g., "found in Jātaka 1.234") and, where determinable, suggested parts of speech.

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
