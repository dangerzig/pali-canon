"""
Custom lemma mappings for forms not in DPD.

Organized into categories:
1. POTENTIAL_DPD_ADDITIONS - Legitimate words that could be submitted to DPD
2. METRICAL_VARIANTS - Vowel length changes for meter (not true lemmas)
3. SANDHI_DECOMPOSITIONS - Compound forms needing decomposition
4. PROJECT_SPECIFIC - Proper nouns, rare compounds, etc.
"""

from typing import Optional

# =============================================================================
# POTENTIAL DPD ADDITIONS
# =============================================================================
# These are legitimate Pāli words/forms that appear to be missing from DPD.
# They have clear lemmas and could benefit the broader Pāli studies community.
# Format: inflected_form -> (lemma, pos)

POTENTIAL_DPD_ADDITIONS = {
    # Technical terms from Netti Pakarana / Peṭakopadesa
    "samāropano": ("samāropana", "nt"),  # placing upon, attribution
    "otaraṇo": ("otaraṇa", "nt"),  # descending, application
    "vevacano": ("vevacana", "nt"),  # synonym, explanation
    "visajjanā": ("visajjana", "nt"),  # answering, solution
    "sīhavikkīḷito": ("sīhavikkīḷita", "nt"),  # lion's play (hermeneutic term)
    "paṭipassaddhiyā": ("paṭipassaddhi", "fem"),  # tranquillization

    # Nouns missing from DPD
    "ayokhilaṃ": ("ayokhīla", "masc"),  # iron stake/post
    "vodāno": ("vodāna", "nt"),  # purity, cleansing
    "sampakopo": ("sampakopa", "masc"),  # anger, agitation
    "byāpajjanā": ("byāpajjana", "nt"),  # malevolence
    "ādāye": ("ādāya", "nt"),  # taking up
    "natthattā": ("natthatta", "nt"),  # non-existence (abstract noun)
    "āsīsanā": ("āsīsana", "nt"),  # blessing, wish
    "sampatthanā": ("sampatthana", "nt"),  # wish, longing
    "pādaloliyena": ("pādaloliya", "nt"),  # foot-fickleness
    "pādaloliyā": ("pādaloliya", "nt"),

    # Plant/animal names (from Jātakas)
    "piyālāni": ("piyāla", "masc"),  # piyāla tree (Buchanania latifolia)
    "balajā": ("balaja", "fem"),  # a type of grass
    "hasulā": ("hasula", "fem"),  # a plant
    "kaṇḍakavārijaṃ": ("kaṇḍakavārija", "nt"),  # thorny water-plant
    "kaṇḍakavārijā": ("kaṇḍakavārija", "nt"),
    "agaḷuṃ": ("agaru", "masc"),  # aloe wood (variant spelling)

    # Adjectives/compounds
    "muñjarohitā": ("muñjarohita", "adj"),  # reed-red colored
    "yamalokikā": ("yamalokika", "adj"),  # pertaining to Yama's world
    "nekāsī": ("nekāsī", "adj"),  # not living alone
    "saparijjano": ("saparijana", "adj"),  # with retinue
    "evaṅkaro": ("evaṅkara", "adj"),  # one who does thus
    "adhigatapaṭisambhido": ("adhigatapaṭisambhida", "adj"),  # attained analytical knowledge
    "gatadiso": ("gatadisa", "adj"),  # gone in (that) direction
    "yaṃṭhānappatto": ("yaṃṭhānappatta", "adj"),  # having reached that place

    # Words from Cūḷaniddesa/Mahāniddesa (archaic)
    "jāgu": ("jāgu", "masc"),  # being, person (archaic vedic)
    "indagu": ("indagu", "masc"),  # person (archaic)

    # Verb forms missing from DPD
    "vicintayiṃ": ("vicinteti", "aor"),  # I considered (1sg aor)
    "vijigucchiṃ": ("vijigucchati", "aor"),  # I was disgusted (1sg aor)
    "sobhayiṃ": ("sobheti", "aor"),  # I made shine (1sg aor)
    "parimocayi": ("parimoceti", "aor"),  # he released (3sg aor)
    "abbhuggamī": ("abbhuggacchati", "aor"),  # he arose (3sg aor)
    "upasampādayī": ("upasampādeti", "aor"),  # he ordained (3sg aor caus)
    "upānayī": ("upāneti", "aor"),  # he brought (3sg aor)
    "nibbattayati": ("nibbatteti", "verb"),  # he produces (caus pres)
    "niddisiyati": ("niddisati", "verb"),  # is pointed out (passive)
    "sampamuñcassu": ("sampamuñcati", "imp"),  # let go! (2sg imp middle)
    "alimpamāno": ("alimpati", "prp"),  # not smearing (neg prp)
    "anibbattayamāno": ("nibbatteti", "prp"),  # not producing (neg prp)
    "osāriyamānāni": ("osāreti", "prp"),  # being handed down (prp pass)
    "dakkhamāno": ("dakkhati", "prp"),  # seeing (present participle)

    # Absolutives
    "chetva": ("chindati", "abs"),  # = chetvā, having cut
    "abhivādiya": ("abhivādeti", "abs"),  # having greeted

    # Past participles
    "khīḷito": ("kīḷita", "pp"),  # played, sported (khīḷ→kīḷ metrical)
    "byamhito": ("vamheti", "pp"),  # reviled (= vamhito)
    "jhāte": ("jhāta", "pp"),  # burnt (locative)
    "sayaṅkatāni": ("sayaṅkata", "pp"),  # self-made (pl)

    # Future passive participles
    "pātabyaṃ": ("pātabba", "fpp"),  # to be drunk/cast

    # Other nouns
    "abhivadanaṃ": ("abhivadana", "nt"),  # greeting
    "kaniṭṭhikā": ("kaniṭṭhikā", "fem"),  # little finger
    "tuṇḍiyā": ("tuṇḍī", "fem"),  # beak (instr)
    "mandālakehi": ("mandālaka", "masc"),  # circular ornament (instr pl)
    "varākiyā": ("varākī", "fem"),  # wretched woman
    "āpāsu": ("āpā", "fem"),  # water (loc pl, archaic)

    # Indeclinables
    "bahubbidhā": ("bahubbidhā", "ind"),  # in many ways
}

# =============================================================================
# METRICAL VARIANTS
# =============================================================================
# Forms that differ only in vowel length due to metrical requirements.
# These map to existing DPD lemmas but with vowel changes.
# Not candidates for DPD addition - just scribal/metrical variants.

METRICAL_VARIANTS = {
    # Short for long vowels
    "khīḷitā": ("kīḷita", "pp"),  # khīḷ → kīḷ (aspirated to unaspirated) + ā → a
    "bhumyā": ("bhūmi", "fem"),  # ū → u
    "atāpī": ("ātāpī", "adj"),  # ā → a (initial)
    "varī": ("vārī", "nt"),  # ā → a
    "viṇā": ("vīṇā", "fem"),  # ī → i
    "makāsi": ("mākāsi", "aor"),  # ā → a
    "piḷayi": ("pīḷeti", "aor"),  # ī → i

    # Geminated consonants (metrical lengthening)
    "uppādiyati": ("upādiyati", "verb"),  # pp for p
    "uppari": ("upari", "ind"),  # pp for p
    "upparito": ("uparito", "ind"),  # pp for p

    # Long for short (ū for u before consonant cluster)
    "uhacca": ("ūhacca", "abs"),  # u → ū

    # Niggahīta variants
    "haṃci": ("hañci", "ind"),  # ṃ → ñ before c
}

# =============================================================================
# PROJECT-SPECIFIC MAPPINGS
# =============================================================================
# Proper nouns, rare compounds, archaic forms specific to this corpus.
# Not candidates for DPD - too specialized or context-dependent.

PROJECT_SPECIFIC = {
    # Proper nouns
    "rucā": ("rucā", "name"),  # Princess Rucā
    "aḷārapamhā": ("aḷārapamha", "name"),  # place name

    # Archaic verse forms with unusual endings
    "masaṃ": ("masa", "masc"),  # lentil/month (archaic acc)
    "tehaṃ": ("ta", "pron"),  # to them (archaic dative)
    "athuṇhaṃ": ("athuṇha", "adj"),  # not hot (hapax?)
    "tīṇānisaṃse": ("ānisaṃsa", "masc"),  # three benefits (compound)

    # evaṃ- compounds (not in DPD as separate entries)
    "evaṅkamanīyo": ("evaṅkamanīya", "adj"),  # so lovely
    "evaṃrajanīyo": ("evaṃrajanīya", "adj"),
    "evaṃmadanīyo": ("evaṃmadanīya", "adj"),
    "evambandhanīyo": ("evambandhanīya", "adj"),
    "evaṃmucchanīyo": ("evaṃmucchanīya", "adj"),

    # Nibbāna-related compounds
    "sopādisesā": ("sa-upādisesa", "adj"),  # with remainder

    # Long compounds
    "thinamiddhapariyuṭṭhitassa": ("thinamiddhapariyuṭṭhita", "pp"),
    "ticattārīsasahassāni": ("cattālīsa", "card"),  # 43,000

    # -āsa compounds (X + āsā "desire")
    "gandhāsā": ("gandhāsa", "masc"),  # scent-desire
    "rasāsā": ("rasāsa", "masc"),  # taste-desire
    "phoṭṭhabbāsā": ("phoṭṭhabbāsa", "masc"),  # touch-desire
    "puttāsā": ("puttāsa", "masc"),  # child-desire

    # Miscellaneous rare forms
    "anācaraṃ": ("anācāra", "masc"),  # misconduct
    "maṃmivā": ("maṃ", "pron"),  # emphatic "me"
}

# =============================================================================
# SANDHI DECOMPOSITIONS
# =============================================================================
# Complex sandhi that DPD doesn't decompose.
# Format: form -> ([parts], [component_info])

SANDHI_DECOMPOSITIONS = {
    # X + iti (quotative marker)
    "akkusaloti": (["akusalo", "iti"], [
        {"lemma": "akusala", "pos": "adj"},
        {"lemma": "iti", "pos": "ind"}
    ]),
    "vosajjatīti": (["vosajjati", "iti"], [
        {"lemma": "vosajjati", "pos": "verb"},
        {"lemma": "iti", "pos": "ind"}
    ]),
    "pettivisayikoti": (["pettivisayiko", "iti"], [
        {"lemma": "pettivisayika", "pos": "adj"},
        {"lemma": "iti", "pos": "ind"}
    ]),
    "otaraṇoti": (["otaraṇo", "iti"], [
        {"lemma": "otaraṇa", "pos": "nt"},
        {"lemma": "iti", "pos": "ind"}
    ]),

    # X + assa/asmi (genitive/verb)
    "tipissa": (["tipi", "assa"], [
        {"lemma": "api", "pos": "ind"},
        {"lemma": "assa", "pos": "pron"}
    ]),
    "sukhamasmī": (["sukhaṃ", "asmi"], [
        {"lemma": "sukha", "pos": "nt"},
        {"lemma": "atthi", "pos": "verb"}
    ]),
    "tumhaṃmhi": (["tumhaṃ", "amhi"], [
        {"lemma": "tumha", "pos": "pron"},
        {"lemma": "atthi", "pos": "verb"}
    ]),
    "vaggulissa": (["vagguli", "assa"], [
        {"lemma": "vagguli", "pos": "masc"},
        {"lemma": "assa", "pos": "pron"}
    ]),
    "jāgussa": (["jāgu", "assa"], [
        {"lemma": "jāgu", "pos": "masc"},
        {"lemma": "assa", "pos": "pron"}
    ]),

    # Negation sandhi
    "nosi": (["no", "asi"], [
        {"lemma": "na", "pos": "ind"},
        {"lemma": "atthi", "pos": "verb"}
    ]),

    # Particle combinations
    "iccā": (["iti", "ca"], [
        {"lemma": "iti", "pos": "ind"},
        {"lemma": "ca", "pos": "ind"}
    ]),
    "yañcāha": (["yaṃ", "ca", "āha"], [
        {"lemma": "ya", "pos": "pron"},
        {"lemma": "ca", "pos": "ind"},
        {"lemma": "āha", "pos": "verb"}
    ]),
    "cīdha": (["ca", "idha"], [
        {"lemma": "ca", "pos": "ind"},
        {"lemma": "idha", "pos": "ind"}
    ]),

    # Pronoun combinations
    "tetaṃ": (["te", "etaṃ"], [
        {"lemma": "ta", "pos": "pron"},
        {"lemma": "eta", "pos": "pron"}
    ]),
    "menaṃ": (["me", "enaṃ"], [
        {"lemma": "ahaṃ", "pos": "pron"},
        {"lemma": "eta", "pos": "pron"}
    ]),
    "mameta": (["mama", "eta"], [
        {"lemma": "ahaṃ", "pos": "pron"},
        {"lemma": "eta", "pos": "pron"}
    ]),
    "tvevahaṃ": (["tu", "eva", "ahaṃ"], [
        {"lemma": "tu", "pos": "ind"},
        {"lemma": "eva", "pos": "ind"},
        {"lemma": "ahaṃ", "pos": "pron"}
    ]),

    # Pronoun + verb sandhi
    "mabhibhāsasi": (["maṃ", "abhibhāsasi"], [
        {"lemma": "ahaṃ", "pos": "pron"},
        {"lemma": "abhibhāsati", "pos": "verb"}
    ]),

    # Prefix compounds (pari-, pa-, abhi-)
    "paridhaṃsati": (["pari", "dhaṃsati"], [
        {"lemma": "pari", "pos": "prefix"},
        {"lemma": "dhaṃsati", "pos": "verb"}
    ]),
    "paridameti": (["pari", "dameti"], [
        {"lemma": "pari", "pos": "prefix"},
        {"lemma": "dameti", "pos": "verb"}
    ]),
    "paridametvā": (["pari", "dametvā"], [
        {"lemma": "pari", "pos": "prefix"},
        {"lemma": "dameti", "pos": "abs"}
    ]),
    "pariyāyitvā": (["pari", "āyitvā"], [
        {"lemma": "pari", "pos": "prefix"},
        {"lemma": "āyāti", "pos": "abs"}
    ]),
    "parikeḷanā": (["pari", "keḷanā"], [
        {"lemma": "pari", "pos": "prefix"},
        {"lemma": "keḷanā", "pos": "fem"}
    ]),
    "pahitvāna": (["pa", "hitvāna"], [
        {"lemma": "pa", "pos": "prefix"},
        {"lemma": "jahati", "pos": "abs"}
    ]),
    "pavārayi": (["pa", "vārayi"], [
        {"lemma": "pa", "pos": "prefix"},
        {"lemma": "vāreti", "pos": "aor"}
    ]),

    # Complex compounds
    "svajjekova": (["sva", "ajja", "eko", "iva"], [
        {"lemma": "sa", "pos": "pron"},
        {"lemma": "ajja", "pos": "ind"},
        {"lemma": "eka", "pos": "card"},
        {"lemma": "iva", "pos": "ind"}
    ]),
}

# =============================================================================
# Combined lookup dictionary (built at import time)
# =============================================================================

# Merge all direct lemma dictionaries
CUSTOM_LEMMAS = {}
CUSTOM_LEMMAS.update(POTENTIAL_DPD_ADDITIONS)
CUSTOM_LEMMAS.update(METRICAL_VARIANTS)
CUSTOM_LEMMAS.update(PROJECT_SPECIFIC)

# Sandhi stays separate
CUSTOM_SANDHI = SANDHI_DECOMPOSITIONS


def get_custom_lemma(word: str) -> Optional[dict]:
    """
    Look up a word in custom lemmas.

    Returns dict with lemma info, or None if not found.
    """
    word_lower = word.lower()

    # Check direct lemmas first
    if word_lower in CUSTOM_LEMMAS:
        lemma, pos = CUSTOM_LEMMAS[word_lower]
        return {"lemma": lemma, "pos": pos}

    # Check sandhi decompositions
    if word_lower in CUSTOM_SANDHI:
        parts, components = CUSTOM_SANDHI[word_lower]
        return {
            "sandhi": parts,
            "components": components
        }

    return None


def get_all_custom_words() -> set:
    """Get all words covered by custom lemmas."""
    return set(CUSTOM_LEMMAS.keys()) | set(CUSTOM_SANDHI.keys())


def get_potential_dpd_additions() -> dict:
    """Get words that could be submitted to DPD."""
    return POTENTIAL_DPD_ADDITIONS.copy()
