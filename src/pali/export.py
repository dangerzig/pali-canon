"""Export functionality for LaTeX and PDF generation.

This is the library API for LaTeX export, used through the Canon class:
    from pali import Canon
    canon = Canon("data")
    canon.export_latex("dn1", "output.tex")

For standalone CLI usage, see src/typeset_critical.py.
Both share the same LaTeX preamble for consistency.
"""

import subprocess
import re
from pathlib import Path
from datetime import datetime
from typing import Optional, Union

from .store import Store
from .text import parse_sutta_id


# LaTeX preamble for critical editions
LATEX_PREAMBLE = r'''%!TEX program = xelatex
\documentclass[11pt,twoside,openright]{book}

% Fonts with Pāli diacritics
\usepackage{fontspec}
\setmainfont{Linux Libertine}
\setsansfont{Linux Libertine}

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

% Hyperlinks
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

'''

LATEX_POSTAMBLE = r'''
\endnumbering
\end{document}'''

# Nikāya names — derived from Store.NIKAYAS to avoid duplication
def _get_nikaya_names() -> dict:
    from .store import NIKAYAS
    return {k: (v["name_pali"], v["name_eng"]) for k, v in NIKAYAS.items()}
NIKAYA_NAMES = _get_nikaya_names()


def escape_latex(text: str) -> str:
    """Escape special LaTeX characters."""
    if not text:
        return ""
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


def is_verse(text: str) -> bool:
    """Detect if text appears to be verse."""
    if not text:
        return False
    punct_count = text.count(',') + text.count(';')
    word_count = len(text.split())
    if word_count > 0 and punct_count / word_count > 0.15:
        return True
    return False


def format_verse(text: str) -> str:
    """Format verse text with proper line breaks."""
    text = text.replace(';', '\\\\\n')
    text = text.replace(',', ',\\\\\n\\vin ')
    return text


class Exporter:
    """Export suttas to LaTeX and PDF."""

    def __init__(self, data_dir: Path):
        """Initialize exporter.

        Args:
            data_dir: Path to data directory
        """
        self.data_dir = data_dir
        self._store = Store(data_dir)

    def to_latex(
        self,
        sutta_ids: Union[str, list[str]],
        title: Optional[str] = None,
    ) -> str:
        """Generate LaTeX for one or more suttas.

        Args:
            sutta_ids: Single sutta ID or list of IDs
            title: Custom document title

        Returns:
            Complete LaTeX document as string

        Example:
            latex = canon.to_latex("dn1")
            latex = canon.to_latex(["dn1", "dn2"], title="Selected Suttas")
        """
        if isinstance(sutta_ids, str):
            sutta_ids = [sutta_ids]

        # Determine collection from first sutta
        collection = self._get_collection(sutta_ids[0])

        if title is None:
            if len(sutta_ids) == 1:
                sutta = self._store.get_sutta(sutta_ids[0])
                if sutta and sutta.title_pali:
                    title = sutta.title_pali
                else:
                    title = sutta_ids[0].upper()
            else:
                nikaya_pali, _ = NIKAYA_NAMES.get(collection, (collection.upper(), ''))
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
        doc_lines.append(r'\beginnumbering')
        doc_lines.append('')

        # Table of contents for multi-sutta documents
        if len(sutta_ids) > 1:
            doc_lines.append(r'\tableofcontents')
            doc_lines.append(r'\newpage')

        # Generate each sutta
        for sutta_id in sutta_ids:
            sutta_latex = self._generate_sutta_latex(sutta_id)
            if sutta_latex:
                doc_lines.append(sutta_latex)
                doc_lines.append(r'\newpage')

        doc_lines.append(LATEX_POSTAMBLE)

        return '\n'.join(doc_lines)

    def _get_collection(self, sutta_id: str) -> str:
        """Get collection (nikaya) from sutta ID."""
        return parse_sutta_id(sutta_id) or "unknown"

    def _generate_sutta_latex(self, sutta_id: str) -> Optional[str]:
        """Generate LaTeX for a single sutta."""
        sutta = self._store.get_sutta(sutta_id, include_tokens=False)
        if not sutta:
            return None

        lines = []

        # Title
        title = sutta.title_pali or sutta_id.upper()
        title_eng = sutta.title_eng

        lines.append(f'\\chapter{{{escape_latex(title)}}}')
        if title_eng:
            lines.append(f'\\begin{{center}}\\textit{{{escape_latex(title_eng)}}}\\end{{center}}')
        lines.append('')

        # Process segments
        in_verse = False
        for segment in sutta.segments:
            pali = segment.pali
            seg_id = segment.id

            if not pali:
                continue

            # Skip header segments (usually :0.x)
            if ':0.' in seg_id:
                # Include as section headers if meaningful
                if pali and not any(pali.startswith(x) for x in
                                   ('Khuddaka', 'Dīgha', 'Majjhima', 'Saṃyutta', 'Aṅguttara')):
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
            formatted = escape_latex(pali)

            if verse_mode:
                formatted = format_verse(formatted)
                lines.append(formatted)
                lines.append('')
            else:
                lines.append(f'\\pstart')
                lines.append(formatted)
                lines.append(f'\\pend')
                lines.append('')

        if in_verse:
            lines.append('\\end{verse}')

        return '\n'.join(lines)

    def export_latex(
        self,
        sutta_ids: Union[str, list[str]],
        output_path: str,
        title: Optional[str] = None,
    ) -> None:
        """Export sutta(s) to LaTeX file.

        Args:
            sutta_ids: Single sutta ID or list of IDs
            output_path: Output file path (.tex)
            title: Custom document title

        Example:
            canon.export_latex("dn1", "dn1.tex")
            canon.export_latex(["dn1", "dn2"], "dn_selection.tex")
        """
        latex = self.to_latex(sutta_ids, title)
        Path(output_path).write_text(latex, encoding='utf-8')

    def export_pdf(
        self,
        sutta_ids: Union[str, list[str]],
        output_path: str,
        title: Optional[str] = None,
        keep_tex: bool = False,
    ) -> bool:
        """Export sutta(s) to PDF.

        Requires XeLaTeX to be installed.

        Args:
            sutta_ids: Single sutta ID or list of IDs
            output_path: Output file path (.pdf)
            title: Custom document title
            keep_tex: If True, keep the intermediate .tex file

        Returns:
            True if PDF generation succeeded, False otherwise

        Example:
            canon.export_pdf("dn1", "dn1.pdf")
        """
        output_path = Path(output_path)
        tex_path = output_path.with_suffix('.tex')

        # Generate LaTeX
        latex = self.to_latex(sutta_ids, title)
        tex_path.write_text(latex, encoding='utf-8')

        # Compile with XeLaTeX (run twice for ToC)
        success = False
        try:
            for _ in range(2):
                result = subprocess.run(
                    ['xelatex', '-interaction=nonstopmode', tex_path.name],
                    cwd=tex_path.parent,
                    capture_output=True,
                    text=True,
                    timeout=120,
                )
                if result.returncode != 0:
                    print(f"XeLaTeX error: {result.stderr[-500:]}")
                    return False

            success = output_path.exists()
            return success

        except FileNotFoundError:
            print("XeLaTeX not found. Please install a TeX distribution.")
            return False
        except subprocess.TimeoutExpired:
            print("XeLaTeX compilation timed out.")
            return False
        finally:
            # Clean up auxiliary files
            for ext in ['.aux', '.log', '.out', '.toc']:
                aux_file = output_path.with_suffix(ext)
                if aux_file.exists():
                    aux_file.unlink()
            if not keep_tex and tex_path.exists():
                tex_path.unlink()
