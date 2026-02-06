"""
Normalization rules for metrical variants and sandhi decomposition.

This module addresses two categories of unresolved forms:
1. Metrical variants (22%): Predictable spelling changes for verse meter
2. Unanalyzed sandhi (25%): Complex word boundary combinations

Together these could improve lemmatization coverage from ~97.7% to ~99%.
"""

import re
from typing import Optional, List, Tuple
from dataclasses import dataclass


@dataclass
class NormalizationResult:
    """Result of normalizing a form."""
    original: str
    normalized: str
    rule_applied: str
    components: Optional[List[str]] = None  # For sandhi decomposition


# =============================================================================
# METRICAL VARIANT NORMALIZATION
# =============================================================================

# Vowel lengthening patterns (short → long for meter)
VOWEL_LENGTHENING = [
    (r'a(?=[^āīūeo])', 'ā'),  # a → ā before consonant
    (r'i(?=[^āīūeo])', 'ī'),  # i → ī before consonant
    (r'u(?=[^āīūeo])', 'ū'),  # u → ū before consonant
]

# Vowel shortening patterns (long → short for meter)
VOWEL_SHORTENING = [
    (r'ā', 'a'),
    (r'ī', 'i'),
    (r'ū', 'u'),
]

# Consonant gemination (single → double for meter)
GEMINATION_CONSONANTS = 'kgcjṭḍtdpbymrlvshṅñṇn'

# Niggahīta (anusvara) variations
NIGGAHITA_RULES = [
    (r'ṃ(?=[kgṅ])', 'ṅ'),   # ṃ → ṅ before velars
    (r'ṃ(?=[cjñ])', 'ñ'),   # ṃ → ñ before palatals
    (r'ṃ(?=[ṭḍṇ])', 'ṇ'),   # ṃ → ṇ before retroflexes
    (r'ṃ(?=[tdnl])', 'n'),  # ṃ → n before dentals
    (r'ṃ(?=[pb])', 'm'),    # ṃ → m before labials
    # Reverse mappings
    (r'ṅ(?=[kgṅ])', 'ṃ'),
    (r'ñ(?=[cjñ])', 'ṃ'),
    (r'ṇ(?=[ṭḍṇ])', 'ṃ'),
    (r'n(?=[tdnl])', 'ṃ'),
    (r'm(?=[pb])', 'ṃ'),
]

# Common metrical spelling variants (specific words)
METRICAL_VARIANTS = {
    # Doubled consonants for meter
    'assa': 'asa',
    'amma': 'ama',
    'anna': 'ana',
    'appa': 'apa',
    'atta': 'ata',
    'adda': 'ada',
    'agga': 'aga',
    'akka': 'aka',
    'alla': 'ala',
    'issa': 'isa',
    'itta': 'ita',
    'inna': 'ina',
    'illa': 'ila',
    'ussa': 'usa',
    'utta': 'uta',
    'unna': 'una',
    'ulla': 'ula',
    # Lengthened vowels for meter
    'āsi': 'asi',
    'āhu': 'ahu',
    'īti': 'iti',
    'ūti': 'uti',
}


def generate_metrical_variants(word: str) -> List[NormalizationResult]:
    """
    Generate possible metrical variant normalizations of a word.

    Returns list of possible normalized forms with the rule that was applied.
    """
    results = []
    word_lower = word.lower()

    # Try vowel shortening (most common: verse uses long vowels for meter)
    for pattern, replacement in VOWEL_SHORTENING:
        if re.search(pattern, word_lower):
            normalized = re.sub(pattern, replacement, word_lower, count=1)
            if normalized != word_lower:
                results.append(NormalizationResult(
                    original=word,
                    normalized=normalized,
                    rule_applied=f"vowel_shortening:{pattern}→{replacement}"
                ))

    # Try vowel lengthening (reverse: standard form has short vowel)
    for pattern, replacement in VOWEL_LENGTHENING:
        normalized = re.sub(pattern, replacement, word_lower, count=1)
        if normalized != word_lower:
            results.append(NormalizationResult(
                original=word,
                normalized=normalized,
                rule_applied=f"vowel_lengthening:{pattern}→{replacement}"
            ))

    # Try consonant degemination (verse doubles consonants for weight)
    for c in GEMINATION_CONSONANTS:
        doubled = c + c
        if doubled in word_lower:
            normalized = word_lower.replace(doubled, c, 1)
            results.append(NormalizationResult(
                original=word,
                normalized=normalized,
                rule_applied=f"degemination:{doubled}→{c}"
            ))

    # Try consonant gemination (reverse normalization)
    for c in GEMINATION_CONSONANTS:
        # Only geminate single consonants between vowels
        pattern = f'(?<=[aāiīuūeo]){c}(?=[aāiīuūeo])'
        if re.search(pattern, word_lower):
            normalized = re.sub(pattern, c + c, word_lower, count=1)
            results.append(NormalizationResult(
                original=word,
                normalized=normalized,
                rule_applied=f"gemination:{c}→{c}{c}"
            ))

    # Try niggahīta variations
    for pattern, replacement in NIGGAHITA_RULES:
        if re.search(pattern, word_lower):
            normalized = re.sub(pattern, replacement, word_lower)
            if normalized != word_lower:
                results.append(NormalizationResult(
                    original=word,
                    normalized=normalized,
                    rule_applied=f"niggahita:{pattern}→{replacement}"
                ))

    # Try known metrical variant mappings
    for variant, standard in METRICAL_VARIANTS.items():
        if variant in word_lower:
            normalized = word_lower.replace(variant, standard, 1)
            results.append(NormalizationResult(
                original=word,
                normalized=normalized,
                rule_applied=f"known_variant:{variant}→{standard}"
            ))
        # Also try reverse
        if standard in word_lower:
            normalized = word_lower.replace(standard, variant, 1)
            results.append(NormalizationResult(
                original=word,
                normalized=normalized,
                rule_applied=f"known_variant_reverse:{standard}→{variant}"
            ))

    return results


# =============================================================================
# SANDHI DECOMPOSITION
# =============================================================================

# Common sandhi patterns at word boundaries
SANDHI_PATTERNS = [
    # Vowel sandhi: final vowel + initial vowel
    (r"([aā])['']?([aā])", r"\1 \2", "a+a elision"),
    (r"([aā])['']?([iī])", r"\1 \2", "a+i elision"),
    (r"([aā])['']?([uū])", r"\1 \2", "a+u elision"),
    (r"([aā])['']?e", r"\1 e", "a+e elision"),
    (r"([aā])['']?o", r"\1 o", "a+o elision"),

    # Consonant assimilation patterns
    (r"([mṃ])([pbm])", r"\1 \2", "labial_assimilation"),
    (r"([nṇñṅ])([tdnṭḍṇcjñkg])", r"\1 \2", "nasal_assimilation"),

    # Specific common fusions
    (r"iti(?=\s|$)", "iti", "iti_quotative"),
]

# Common pronoun + verb sandhi patterns
PRONOUN_VERB_SANDHI = [
    # ahaṃ (I) combinations
    (r"(.+)ohama?$", [r"\1o", "ahaṃ"], "X+ahaṃ fusion"),
    (r"(.+)āhama?$", [r"\1ā", "ahaṃ"], "X+ahaṃ fusion"),
    (r"(.+)amhā?$", [r"\1aṃ", "ahaṃ"], "X+ahaṃ fusion"),
    (r"^mah(.+)", ["ahaṃ", r"\1"], "ahaṃ+X fusion"),

    # tvaṃ (you) combinations
    (r"(.+)osi$", [r"\1o", "asi"], "X+asi fusion"),
    (r"(.+)āsi$", [r"\1ā", "asi"], "X+asi fusion"),

    # so/sā (he/she) combinations
    (r"^so(.+)", ["so", r"\1"], "so+X fusion"),
    (r"^sā(.+)", ["sā", r"\1"], "sā+X fusion"),

    # Common verb prefixes that fuse
    (r"^sam(.+)", ["saṃ", r"\1"], "saṃ+X prefix"),
    (r"^san(.+)", ["saṃ", r"\1"], "saṃ+X prefix (assimilated)"),
    (r"^abhi(.+)", ["abhi", r"\1"], "abhi+X prefix"),
    (r"^upa(.+)", ["upa", r"\1"], "upa+X prefix"),
    (r"^pari(.+)", ["pari", r"\1"], "pari+X prefix"),
    (r"^vi(.+)", ["vi", r"\1"], "vi+X prefix"),
    (r"^pa(.+)", ["pa", r"\1"], "pa+X prefix"),
    (r"^anu(.+)", ["anu", r"\1"], "anu+X prefix"),
]

# Common enclitics that fuse
# NOTE: Removed generic X+ti pattern as it creates false positives with verb forms
# (jānāti, hoti, passanti, etc.). Instead, specific quotatives are in COMMON_SANDHI_COMPOUNDS.
ENCLITIC_PATTERNS = [
    (r"(.+)pi$", [r"\1", "api"], "X+api"),
    (r"(.+)va$", [r"\1", "va/eva"], "X+va/eva"),
    (r"(.+)ca$", [r"\1", "ca"], "X+ca"),
    (r"(.+)ssa$", [r"\1", "assa"], "X+assa (genitive)"),
    (r"(.+)smi$", [r"\1", "asmiṃ"], "X+asmiṃ (locative)"),
    (r"(.+)mhi$", [r"\1", "asmiṃ"], "X+asmiṃ (locative)"),
]

# Very common sandhi compounds - these are the most frequent unresolved forms
# NOTE: Components should be LEMMAS (dictionary headwords) where possible
# so they match the known_lemmas set built from the corpus
COMMON_SANDHI_COMPOUNDS = {
    # eva combinations (extremely common)
    "evameva": ["evaṃ", "eva"],
    "evamevaṃ": ["evaṃ", "evaṃ"],
    "evampi": ["evaṃ", "api"],
    "evaṃpi": ["evaṃ", "api"],
    "ceva": ["ca", "eva"],
    "neva": ["na", "eva"],
    "yeva": ["ya", "eva"],
    "veva": ["vā", "eva"],
    "teva": ["ta", "eva"],
    "meva": ["ahaṃ", "eva"],  # me → ahaṃ (lemma)
    "deva": ["idaṃ", "eva"],
    "tveva": ["tu", "eva"],
    "tvevā": ["tu", "eva"],
    "diṭṭheva": ["diṭṭha", "eva"],

    # ca + X combinations (use lemmas for the second part)
    "caparaṃ": ["ca", "apara"],  # aparaṃ → apara (lemma)
    "capi": ["ca", "api"],
    "cāpi": ["ca", "api"],
    "cepi": ["ca", "api"],  # ce + pi = ca + api
    "cassa": ["ca", "assa"],
    "cāssa": ["ca", "assa"],
    "cāyaṃ": ["ca", "ayaṃ"],
    "cetaṃ": ["ca", "eta"],  # etaṃ → eta (lemma)
    "ceso": ["ca", "esa"],
    "cete": ["ca", "eta"],
    "tañca": ["ta", "ca"],  # taṃ + ca
    "yañca": ["ya", "ca"],  # yaṃ + ca
    "etañca": ["eta", "ca"],
    "idañca": ["idaṃ", "ca"],

    # idaṃ combinations (seyyathidaṃ, yadidaṃ, etc.)
    "yadidaṃ": ["ya", "idaṃ"],  # yad → ya (lemma)
    "tadidaṃ": ["ta", "idaṃ"],  # tad → ta (lemma)
    "etadidaṃ": ["eta", "idaṃ"],
    "seyyathidaṃ": ["seyyathā", "idaṃ"],
    "sudaṃ": ["su", "idaṃ"],
    "kudaṃ": ["ku", "idaṃ"],

    # na combinations
    "natthi": ["na", "atthi"],
    "nāpi": ["na", "api"],
    "nāssa": ["na", "assa"],
    "nāhaṃ": ["na", "ahaṃ"],
    "nāyaṃ": ["na", "ayaṃ"],
    "netaṃ": ["na", "eta"],  # etaṃ → eta (lemma)
    "neso": ["na", "esa"],
    "nete": ["na", "eta"],

    # hi combinations
    "hetaṃ": ["hi", "eta"],  # hi + etaṃ
    "hesa": ["hi", "esa"],
    "hete": ["hi", "eta"],

    # iti combinations
    "itissa": ["iti", "assa"],
    "itipi": ["iti", "api"],
    "itīti": ["iti", "iti"],

    # kathaṃ combinations
    "kathañca": ["kathaṃ", "ca"],
    "kathañci": ["kathaṃ", "ci"],

    # ayaṃ/api combinations
    "ayampi": ["ayaṃ", "api"],
    "idampi": ["idaṃ", "api"],
    "etampi": ["eta", "api"],

    # taṃ/enaṃ combinations
    "tamenaṃ": ["ta", "enaṃ"],
    "tametaṃ": ["ta", "eta"],

    # etad + X (quotative constructions)
    "etadahosi": ["eta", "ahosi"],
    "etadavoca": ["eta", "avoca"],
    "etamatthaṃ": ["eta", "attha"],

    # Common verb + iti fusions (quotative markers)
    "assāti": ["assa", "iti"],
    "hotīti": ["hoti", "iti"],
    "bhavissatīti": ["bhavissati", "iti"],
    "abhāsitthāti": ["abhāsittha", "iti"],
    "bhanteti": ["bhante", "iti"],
    "āvusoti": ["āvuso", "iti"],

    # kho combinations
    "khvassa": ["kho", "assa"],
    "khvāhaṃ": ["kho", "ahaṃ"],
    "khvāyaṃ": ["kho", "ayaṃ"],
    "khvetaṃ": ["kho", "eta"],
    "khvesa": ["kho", "esa"],

    # tu/pana combinations
    "tvassa": ["tu", "assa"],
    "panassa": ["pana", "assa"],
    "panāyaṃ": ["pana", "ayaṃ"],
    "panetaṃ": ["pana", "eta"],

    # ahaṃ combinations
    "ahampi": ["ahaṃ", "api"],
    "ahañca": ["ahaṃ", "ca"],
    "ahañhi": ["ahaṃ", "hi"],
    "mayhaṃ": ["ahaṃ"],  # mayhaṃ is genitive of ahaṃ, treat as single

    # yathā/tathā combinations
    "yathāpi": ["yathā", "api"],
    "tathāpi": ["tathā", "api"],
    "yatheva": ["yathā", "eva"],
    "tatheva": ["tathā", "eva"],

    # uddāna (summary verse markers)
    "tassuddānaṃ": ["ta", "uddāna"],
    "tesaṃuddānaṃ": ["ta", "uddāna"],

    # evaṃ + verb/noun combinations
    "evametaṃ": ["evaṃ", "eta"],
    "evamāha": ["evaṃ", "āha"],
    "evamassa": ["evaṃ", "assa"],
    "evañhi": ["evaṃ", "hi"],

    # taṃ/yaṃ + api/ca patterns
    "tampi": ["ta", "api"],
    "yampi": ["ya", "api"],
    "idampi": ["idaṃ", "api"],
    "etampi": ["eta", "api"],
    "parañca": ["para", "ca"],
    "katamañca": ["katama", "ca"],

    # tena/tasmā combinations - use "ta" as lemma
    "tenāha": ["ta", "āha"],
    "tasmātiha": ["ta", "iha"],  # Note: iha not in lemmas
    "tasmāpi": ["ta", "api"],

    # pana combinations
    "panāvuso": ["pana", "āvuso"],
    "panāhaṃ": ["pana", "ahaṃ"],
    "panāssa": ["pana", "assa"],

    # idaṃ + verb quotative patterns
    "idamavoca": ["idaṃ", "avoca"],
    "idamāha": ["idaṃ", "āha"],
    "idameva": ["idaṃ", "eva"],

    # vā combinations
    "vāpi": ["vā", "api"],

    # taṃ + ahaṃ patterns
    "tamahaṃ": ["ta", "ahaṃ"],

    # Additional common patterns with verified lemmas
    "tatheva": ["ta", "eva"],  # tathā not a lemma, use ta
    "yannūnāhaṃ": ["ya", "nu", "ahaṃ"],  # yan + nūna + ahaṃ

    # More verb+iti quotatives (only verified patterns, not generic X+ti)
    "bujjhantīti": ["bujjhati", "iti"],
    "evamāhaṃsu": ["evaṃ", "āhaṃsu"],  # evaṃ + āhaṃsu (they said thus)

    # hi + X combinations
    "hidaṃ": ["hi", "idaṃ"],
    "hetaṃ": ["hi", "eta"],

    # idha combinations
    "idhāvuso": ["idha", "āvuso"],
    "idheva": ["idha", "eva"],

    # tattha/tatra combinations
    "tattheva": ["tattha", "eva"],
    "tatreva": ["tatra", "eva"],

    # me/te + X combinations
    "metaṃ": ["ahaṃ", "eta"],  # me + etaṃ, use lemma forms
    "meso": ["ahaṃ", "esa"],
    "mete": ["ahaṃ", "eta"],
    "tetaṃ": ["tvaṃ", "eta"],
    "teso": ["tvaṃ", "esa"],

    # ya/yo + X combinations
    "yvāyaṃ": ["ya", "ayaṃ"],
    "yampidaṃ": ["ya", "api", "idaṃ"],

    # pubbe/pubba combinations
    "pubbeva": ["pubba", "eva"],

    # tassa/tena + eva
    "tasseva": ["ta", "eva"],
    "teneva": ["ta", "eva"],

    # Additional common patterns
    "cattārome": ["cattāro", "ima"],  # cattāro + ime
    "ṭhānametaṃ": ["ṭhāna", "eta"],
    "bhāsitampetaṃ": ["bhāsita", "api", "eta"],
    "vuttañhetaṃ": ["vutta", "hi", "eta"],

    # ayaṃ/taṃ/idaṃ + eva combinations
    "ayameva": ["ayaṃ", "eva"],
    "tameva": ["ta", "eva"],
    "idameva": ["idaṃ", "eva"],
    "sabbeva": ["sabba", "eva"],
    "appeva": ["api", "eva"],
    "yāvadeva": ["yāva", "eva"],
    "idametaṃ": ["idaṃ", "eta"],
    "yathayidaṃ": ["yathā", "idaṃ"],
    "vivicceva": ["vivicca", "eva"],

    # yena/tena + āyasmā combinations (use āyasmant as lemma)
    "yenāyasmā": ["ya", "āyasmant"],
    "tenāyasmā": ["ta", "āyasmant"],
    "ayamāyasmā": ["ima", "āyasmant"],
    "iccāyasmā": ["iti", "āyasmant"],

    # Reciprocal pronoun
    "aññamaññaṃ": ["añña", "añña"],

    # ca + ahaṃ/iti combinations
    "cāhaṃ": ["ca", "ahaṃ"],
    "cāti": ["ca", "iti"],

    # so + ahaṃ
    "sohaṃ": ["ta", "ahaṃ"],  # so is inflected form of ta

    # dve + ime (dve lemma might be dvi or dva)
    "dveme": ["dva", "ima"],

    # kiñca + etaṃ
    "kiñcetaṃ": ["ka", "ca", "eta"],

    # na + y + idaṃ (with liaison)
    "nayidaṃ": ["na", "idaṃ"],

    # sammā + eva
    "sammadeva": ["sammā", "eva"],

    # tatthetaṃ = tattha + etaṃ
    "tatthetaṃ": ["tattha", "eta"],

    # Additional X + idaṃ patterns
    "buddhapūjāyidaṃ": ["buddhapūjā", "idaṃ"],

    # hi + eva combinations
    "heva": ["hi", "eva"],
    "hevaṃ": ["hi", "evaṃ"],

    # tad + eva
    "tadeva": ["ta", "eva"],

    # aṭṭha + ime (numerals)
    "aṭṭhime": ["aṭṭha", "ima"],

    # idha + ahaṃ
    "idhāhaṃ": ["idha", "ahaṃ"],

    # na + cirassa + eva
    "nacirasseva": ["na", "cirassa", "eva"],

    # tāva + eva combinations
    "tāvadeva": ["tāva", "eva"],
}


def decompose_sandhi(word: str) -> List[NormalizationResult]:
    """
    Attempt to decompose a word at sandhi boundaries.

    Returns list of possible decompositions with component parts.
    """
    results = []
    word_lower = word.lower()

    # First check common sandhi compounds (most reliable)
    if word_lower in COMMON_SANDHI_COMPOUNDS:
        components = COMMON_SANDHI_COMPOUNDS[word_lower]
        results.append(NormalizationResult(
            original=word,
            normalized=" + ".join(components),
            rule_applied="common_sandhi_compound",
            components=components
        ))
        # Return early for known compounds - these are definitive
        return results

    # Try pronoun + verb patterns
    for pattern, replacements, rule in PRONOUN_VERB_SANDHI:
        match = re.match(pattern, word_lower)
        if match:
            if isinstance(replacements, list):
                components = []
                for r in replacements:
                    if r.startswith('\\'):
                        components.append(match.expand(r))
                    else:
                        components.append(r)
                results.append(NormalizationResult(
                    original=word,
                    normalized=" + ".join(components),
                    rule_applied=f"sandhi:{rule}",
                    components=components
                ))

    # Try enclitic patterns
    for pattern, replacements, rule in ENCLITIC_PATTERNS:
        match = re.match(pattern, word_lower)
        if match:
            components = []
            for r in replacements:
                if r.startswith('\\'):
                    components.append(match.expand(r))
                else:
                    components.append(r)
            # Only add if first component is substantial
            if len(components[0]) >= 2:
                results.append(NormalizationResult(
                    original=word,
                    normalized=" + ".join(components),
                    rule_applied=f"sandhi:{rule}",
                    components=components
                ))

    # Try splitting at common boundaries (vowel sequences)
    vowel_boundaries = list(re.finditer(r'[aāiīuūeo][aāiīuūeo]', word_lower))
    for match in vowel_boundaries:
        pos = match.start() + 1
        if 2 <= pos <= len(word_lower) - 2:  # Ensure meaningful splits
            part1 = word_lower[:pos]
            part2 = word_lower[pos:]
            if len(part1) >= 2 and len(part2) >= 2:
                results.append(NormalizationResult(
                    original=word,
                    normalized=f"{part1} + {part2}",
                    rule_applied=f"vowel_boundary_split:{pos}",
                    components=[part1, part2]
                ))

    return results


# =============================================================================
# COMBINED NORMALIZATION
# =============================================================================

def normalize_form(word: str, known_lemmas: Optional[set] = None) -> List[NormalizationResult]:
    """
    Try all normalization strategies on a word.

    Args:
        word: The word to normalize
        known_lemmas: Optional set of known lemmas to validate against

    Returns:
        List of possible normalizations, sorted by likelihood
    """
    all_results = []

    # Try metrical variants
    all_results.extend(generate_metrical_variants(word))

    # Try sandhi decomposition
    all_results.extend(decompose_sandhi(word))

    # If we have known lemmas, filter to only valid ones
    if known_lemmas:
        validated = []
        for result in all_results:
            if result.components:
                # For sandhi, check if all components are known
                if all(comp in known_lemmas for comp in result.components):
                    validated.append(result)
            else:
                # For metrical variants, check if normalized form is known
                if result.normalized in known_lemmas:
                    validated.append(result)
        return validated

    return all_results


def analyze_unresolved_forms(unresolved: List[str], known_lemmas: set) -> dict:
    """
    Analyze a list of unresolved forms and categorize them.

    Args:
        unresolved: List of forms that couldn't be lemmatized
        known_lemmas: Set of known lemmas from DPD

    Returns:
        Dict with categories and their forms
    """
    categories = {
        'metrical_fixable': [],      # Can be fixed by metrical normalization
        'sandhi_fixable': [],        # Can be fixed by sandhi decomposition
        'still_unresolved': [],      # Neither approach works
    }

    for form in unresolved:
        results = normalize_form(form, known_lemmas)

        if not results:
            categories['still_unresolved'].append(form)
            continue

        # Check what type of fix worked
        metrical_fixes = [r for r in results if 'sandhi' not in r.rule_applied]
        sandhi_fixes = [r for r in results if 'sandhi' in r.rule_applied]

        if metrical_fixes:
            categories['metrical_fixable'].append((form, metrical_fixes[0]))
        elif sandhi_fixes:
            categories['sandhi_fixable'].append((form, sandhi_fixes[0]))
        else:
            categories['still_unresolved'].append(form)

    return categories


# =============================================================================
# TESTING
# =============================================================================

def test_normalizer():
    """Test the normalization functions."""
    print("Testing metrical variant normalization...")

    # Test cases: word -> expected normalized form
    metrical_tests = [
        ("sukhā", "sukha"),       # Long vowel → short
        ("buddhassa", "buddhasa"), # Gemination
        ("mayhaṃ", "mayhaṃ"),     # Should stay same or try niggahita
    ]

    for word, expected in metrical_tests:
        results = generate_metrical_variants(word)
        found = any(r.normalized == expected for r in results)
        print(f"  {word} → {expected}: {'✓' if found else '✗'}")
        if results:
            print(f"    Generated: {[r.normalized for r in results[:3]]}")

    print("\nTesting sandhi decomposition...")

    sandhi_tests = [
        ("nibbānādhimuttohama", ["nibbānādhimutto", "ahaṃ"]),
        ("dhammopi", ["dhammo", "api"]),
        ("etadavoca", ["etad", "avoca"]),
    ]

    for word, expected_parts in sandhi_tests:
        results = decompose_sandhi(word)
        print(f"  {word}:")
        for r in results[:3]:
            print(f"    → {r.components} ({r.rule_applied})")


if __name__ == "__main__":
    test_normalizer()
