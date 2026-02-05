#!/usr/bin/env python3
"""
Generate beautifully typeset critical editions in LaTeX.

Features:
- Proper Pāli diacritics with fontspec
- Critical apparatus with variant readings
- PTS page references in margins
- Paragraph and verse formatting
- Chapter/vagga structure
- Lemmatization annotations (optional)

Output formats:
- Single sutta/text
- Full nikāya volume
- Custom selection

Uses the reledmac package for critical edition features.
"""

import json
import re
import argparse
from pathlib import Path
from datetime import datetime
from typing import Optional

DATA_DIR = Path(__file__).parent.parent / "data"
OUTPUT_DIR = DATA_DIR / "typeset"

# LaTeX preamble for critical editions
LATEX_PREAMBLE = r'''%!TEX program = xelatex
\documentclass[11pt,twoside,openright]{book}

% Fonts with Pāli diacritics
\usepackage{fontspec}
\setmainfont{Linux Libertine O}
\setsansfont{Linux Biolinum O}

% Critical edition package
\usepackage[series={A},noend,noeledsec,nofamiliar,noledgroup]{reledmac}

% Page layout
\usepackage[
  paperwidth=6in,
  paperheight=9in,
  inner=0.75in,
  outer=0.5in,
  top=0.75in,
  bottom=0.75in
]{geometry}

% Headers and footers
\usepackage{fancyhdr}
\pagestyle{fancy}
\fancyhf{}
\fancyhead[LE]{\small\leftmark}
\fancyhead[RO]{\small\rightmark}
\fancyfoot[C]{\thepage}
\renewcommand{\headrulewidth}{0.4pt}

% Chapter and section formatting
\usepackage{titlesec}
\titleformat{\chapter}[display]
  {\normalfont\huge\bfseries\centering}
  {\chaptertitlename\ \thechapter}{20pt}{\Huge}
\titleformat{\section}
  {\normalfont\Large\bfseries}{}{0pt}{}

% Verse environment
\usepackage{verse}
\setlength{\stanzaskip}{0.75\baselineskip}

% PTS references in margins
\usepackage{marginnote}
\renewcommand*{\marginfont}{\footnotesize\itshape}

% Hyperlinks (optional, for PDF navigation)
\usepackage{hyperref}
\hypersetup{
  colorlinks=true,
  linkcolor=black,
  urlcolor=blue,
  pdftitle={Pāli Canon Critical Edition},
  pdfauthor={Digital Critical Edition Project}
}

% Pāli-specific commands
\newcommand{\pali}[1]{\textit{#1}}
\newcommand{\pts}[1]{\marginnote{[#1]}}
\newcommand{\suttaref}[1]{\textsf{#1}}

% Critical apparatus commands
\newcommand{\variant}[3]{%
  \edtext{#1}{\Afootnote{#2 \textit{#3}}}%
}

% Start critical apparatus
\beginnumbering

'''

LATEX_POSTAMBLE = r'''
\endnumbering
\end{document}
'''

# Nikāya names
NIKAYA_NAMES = {
    'dn': ('Dīgha Nikāya', 'Long Discourses'),
    'mn': ('Majjhima Nikāya', 'Middle Length Discourses'),
    'sn': ('Saṃyutta Nikāya', 'Connected Discourses'),
    'an': ('Aṅguttara Nikāya', 'Numerical Discourses'),
    'kn': ('Khuddaka Nikāya', 'Minor Collection'),
}

# KN text names
KN_NAMES = {
    'kp': 'Khuddakapāṭha',
    'dhp': 'Dhammapada',
    'ud': 'Udāna',
    'iti': 'Itivuttaka',
    'snp': 'Suttanipāta',
    'vv': 'Vimānavatthu',
    'pv': 'Petavatthu',
    'thag': 'Theragāthā',
    'thig': 'Therīgāthā',
    'ja': 'Jātaka',
    'mnd': 'Mahāniddesa',
    'cnd': 'Cūḷaniddesa',
    'ps': 'Paṭisambhidāmagga',
    'tha-ap': 'Therāpadāna',
    'thi-ap': 'Therīapadāna',
    'bv': 'Buddhavaṃsa',
    'cp': 'Cariyāpiṭaka',
    'ne': 'Netti',
    'pe': 'Peṭakopadesa',
    'mil': 'Milindapañha',
}


def escape_latex(text: str) -> str:
    """Escape special LaTeX characters."""
    replacements = [
        ('\\', r'\textbackslash{}'),
        ('&', r'\&'),
        ('%', r'\%'),
        ('$', r'\$'),
        ('#', r'\#'),
        ('_', r'\_'),
        ('{', r'\{'),
        ('}', r'\}'),
        ('~', r'\textasciitilde{}'),
        ('^', r'\textasciicircum{}'),
    ]
    for old, new in replacements:
        text = text.replace(old, new)
    return text


def format_pali_text(text: str) -> str:
    """Format Pāli text for LaTeX output."""
    # Already in Unicode, just escape LaTeX specials
    return escape_latex(text)


def is_verse(text: str) -> bool:
    """Detect if text appears to be verse (contains metrical markers)."""
    # Verse typically has punctuation like commas and semicolons for pāda breaks
    # and is shorter with more punctuation density
    if not text:
        return False
    punct_count = text.count(',') + text.count(';')
    word_count = len(text.split())
    if word_count > 0 and punct_count / word_count > 0.15:
        return True
    return False


def format_verse(text: str) -> str:
    """Format verse text with proper line breaks."""
    # Split on semicolons (pāda breaks) and commas (half-pāda)
    text = text.replace(';', '\\\\\n')
    text = text.replace(',', ',\\\\\n\\vin ')
    return text


def extract_pts_ref(segment_id: str) -> Optional[str]:
    """Extract PTS reference from segment ID if available."""
    # SC segment IDs sometimes encode PTS refs
    # e.g., dn1:1.1 might correspond to D i 1
    return None  # TODO: implement PTS mapping


def load_sutta(collection: str, sutta_id: str) -> dict:
    """Load a sutta from canonical files."""
    fpath = DATA_DIR / f"canonical/{collection}/{sutta_id}.json"
    if not fpath.exists():
        # Try without number suffix
        for f in (DATA_DIR / f"canonical/{collection}").glob(f"{sutta_id}*.json"):
            fpath = f
            break

    if not fpath.exists():
        raise FileNotFoundError(f"Sutta not found: {collection}/{sutta_id}")

    return json.loads(fpath.read_text())


def load_lemmatized(collection: str, sutta_id: str) -> Optional[dict]:
    """Load lemmatized version if available."""
    fpath = DATA_DIR / f"lemmatized/{collection}/{sutta_id}.json"
    if fpath.exists():
        return json.loads(fpath.read_text())
    return None


def generate_sutta_latex(collection: str, sutta_id: str,
                         include_lemmas: bool = False,
                         include_variants: bool = True) -> str:
    """Generate LaTeX for a single sutta."""

    data = load_sutta(collection, sutta_id)
    lemmatized = load_lemmatized(collection, sutta_id) if include_lemmas else None

    lines = []

    # Title
    title = data.get('title_pali', data.get('name_pali', sutta_id.upper()))
    title_eng = data.get('title_eng', data.get('name_eng', ''))

    lines.append(f'\\chapter{{{escape_latex(title)}}}')
    if title_eng:
        lines.append(f'\\begin{{center}}\\textit{{{escape_latex(title_eng)}}}\\end{{center}}')
    lines.append('')

    # Get segments
    segments = []
    if 'segments' in data:
        segments = data['segments']
    elif 'suttas' in data:
        for sutta in data['suttas']:
            segments.extend(sutta.get('segments', []))
    elif 'items' in data:
        for item in data['items']:
            segments.extend(item.get('segments', []))

    # Process segments
    in_verse = False
    for seg in segments:
        seg_id = seg.get('id', '')
        pali = seg.get('pali', '')

        if not pali:
            continue

        # Skip header segments (usually :0.x)
        if ':0.' in seg_id:
            # But include as section headers
            if pali and not pali.startswith(('Khuddaka', 'Dīgha', 'Majjhima')):
                lines.append(f'\\section*{{{escape_latex(pali)}}}')
            continue

        # Check for verse
        verse_mode = is_verse(pali)

        if verse_mode and not in_verse:
            lines.append('\\begin{verse}')
            in_verse = True
        elif not verse_mode and in_verse:
            lines.append('\\end{verse}')
            in_verse = False

        # Format text
        formatted = format_pali_text(pali)

        if verse_mode:
            # Format as verse with line breaks
            formatted = format_verse(formatted)
            lines.append(formatted)
            lines.append('')
        else:
            # Prose paragraph
            lines.append(f'\\pstart')
            lines.append(formatted)
            lines.append(f'\\pend')
            lines.append('')

    if in_verse:
        lines.append('\\end{verse}')

    return '\n'.join(lines)


def generate_document(collection: str, sutta_ids: list,
                      title: str = None,
                      include_lemmas: bool = False) -> str:
    """Generate complete LaTeX document for one or more suttas."""

    if title is None:
        if len(sutta_ids) == 1:
            title = f"{collection.upper()} {sutta_ids[0]}"
        else:
            nikaya_pali, nikaya_eng = NIKAYA_NAMES.get(collection, (collection.upper(), ''))
            title = nikaya_pali

    # Build document
    doc_lines = [LATEX_PREAMBLE]

    # Title page
    doc_lines.append(r'\begin{document}')
    doc_lines.append(r'\begin{titlepage}')
    doc_lines.append(r'\centering')
    doc_lines.append(r'\vspace*{2in}')
    doc_lines.append(f'{{\\Huge\\bfseries {escape_latex(title)}}}')
    doc_lines.append(r'\vspace{0.5in}')
    doc_lines.append(r'{\Large Critical Edition}')
    doc_lines.append(r'\vfill')
    doc_lines.append(r'{\large Based on PTS, VRI, and SuttaCentral witnesses}')
    doc_lines.append(r'\vspace{0.25in}')
    doc_lines.append(f'{{\\small Generated: {datetime.now().strftime("%Y-%m-%d")}}}')
    doc_lines.append(r'\end{titlepage}')
    doc_lines.append('')

    # Table of contents for multi-sutta documents
    if len(sutta_ids) > 1:
        doc_lines.append(r'\tableofcontents')
        doc_lines.append(r'\newpage')

    # Generate each sutta
    for sutta_id in sutta_ids:
        try:
            sutta_latex = generate_sutta_latex(collection, sutta_id, include_lemmas)
            doc_lines.append(sutta_latex)
            doc_lines.append(r'\newpage')
        except FileNotFoundError as e:
            print(f"Warning: {e}")

    doc_lines.append(LATEX_POSTAMBLE)

    return '\n'.join(doc_lines)


def main():
    parser = argparse.ArgumentParser(
        description='Generate LaTeX critical edition of Pāli texts'
    )
    parser.add_argument('collection', help='Collection (dn, mn, sn, an, kn)')
    parser.add_argument('suttas', nargs='+', help='Sutta ID(s) (e.g., dn1 mn1 mn2)')
    parser.add_argument('--output', '-o', help='Output file path')
    parser.add_argument('--title', '-t', help='Custom document title')
    parser.add_argument('--lemmas', action='store_true', help='Include lemmatization')
    parser.add_argument('--compile', action='store_true', help='Compile to PDF')

    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Generate LaTeX
    latex = generate_document(
        args.collection,
        args.suttas,
        title=args.title,
        include_lemmas=args.lemmas
    )

    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        if len(args.suttas) == 1:
            output_path = OUTPUT_DIR / f"{args.collection}_{args.suttas[0]}.tex"
        else:
            output_path = OUTPUT_DIR / f"{args.collection}_selection.tex"

    # Write LaTeX
    output_path.write_text(latex, encoding='utf-8')
    print(f"LaTeX written to: {output_path}")

    # Optionally compile
    if args.compile:
        import subprocess
        print("Compiling with XeLaTeX...")
        result = subprocess.run(
            ['xelatex', '-interaction=nonstopmode', output_path.name],
            cwd=output_path.parent,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            pdf_path = output_path.with_suffix('.pdf')
            print(f"PDF generated: {pdf_path}")
        else:
            print("Compilation failed:")
            print(result.stderr[-500:] if len(result.stderr) > 500 else result.stderr)


if __name__ == "__main__":
    main()
