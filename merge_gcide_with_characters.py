#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Create a combined dictionary: GCIDE (plain English) + a book's character list.
Writes a union .txt file, runs tab2opf to produce the OPF and HTML, then runs
kindlegen to produce the .mobi.

Usage:
  python merge_gcide_with_characters.py <book_folder>

  book_folder: e.g. speaker-for-the-dead (required)
  - Expects dictionaries/{book_folder}/speaker-characters.txt (or book-specific name)
  - Writes dictionaries/{book_folder}/{output_basename}.txt
  - Runs tab2opf so OPF/HTML are created in that folder
  - Runs kindlegen to produce .mobi
  - kindlegen: set KINDLEGEN env var to the path to kindlegen.exe, or have kindlegen on your PATH
"""

import os
import subprocess
import sys
from pathlib import Path
from shutil import which


def find_kindlegen():
    """Return path to kindlegen: KINDLEGEN env var, then PATH, then common Windows install."""
    env_path = os.environ.get('KINDLEGEN')
    if env_path:
        return env_path.strip()
    path = which('kindlegen')
    if path:
        return path
    if sys.platform == 'win32':
        local_app = os.environ.get('LOCALAPPDATA', '')
        for name in ('Kindle Previewer 3', 'Kindle Previewer'):
            exe = os.path.join(local_app, 'Amazon', name, 'lib', 'fc', 'bin', 'kindlegen.exe')
            if os.path.isfile(exe):
                return exe
    return None


# Book folder -> (character file name, combined output basename)
BOOK_CONFIG = {
    'speaker-for-the-dead': ('speaker-characters.txt', 'speaker-characters-and-gcide'),
    # Add more later: 'enders-game': ('enders-game-characters.txt', 'enders-game-characters-and-gcide'),
}


def main():
    base = Path(__file__).parent
    if len(sys.argv) < 2:
        print('Usage: python merge_gcide_with_characters.py <book_folder>')
        print('  book_folder: one of', list(BOOK_CONFIG.keys()))
        sys.exit(1)
    book_folder = sys.argv[1]

    if book_folder not in BOOK_CONFIG:
        print('Unknown book folder:', book_folder)
        print('Known:', list(BOOK_CONFIG.keys()))
        sys.exit(1)

    char_file_name, output_basename = BOOK_CONFIG[book_folder]
    gcide_path = base / 'dictionaries' / 'gcide' / 'gcide.txt'
    book_dir = base / 'dictionaries' / book_folder
    char_path = book_dir / char_file_name
    output_path = book_dir / f'{output_basename}.txt'

    if not gcide_path.exists():
        print('Error: GCIDE dictionary not found. Run gcide2tab.py first.')
        print('  Expected:', gcide_path)
        sys.exit(1)
    if not char_path.exists():
        print('Error: Character dictionary not found:', char_path)
        sys.exit(1)

    book_dir.mkdir(parents=True, exist_ok=True)

    print('Reading GCIDE...')
    gcide_lines = gcide_path.read_text(encoding='utf-8').strip().splitlines()
    print('  ', len(gcide_lines), 'entries')

    print('Reading', char_path.name, '...')
    char_lines = char_path.read_text(encoding='utf-8').strip().splitlines()
    char_lines = [ln for ln in char_lines if ln.strip()]
    print('  ', len(char_lines), 'entries')

    CHAR_TAG = '[Character] '
    print('Writing union to', output_path.name, '...')
    with open(output_path, 'w', encoding='utf-8') as out:
        for ln in gcide_lines:
            out.write(ln)
            out.write('\n')
        for ln in char_lines:
            if '\t' in ln:
                headword, definition = ln.split('\t', 1)
                out.write(headword)
                out.write('\t')
                out.write(CHAR_TAG)
                out.write(definition)
                out.write('\n')
            else:
                out.write(ln)
                out.write('\n')

    print('Running tab2opf...')
    tab2opf_script = base / 'tab2opf.py'
    result = subprocess.run(
        [sys.executable, str(tab2opf_script), output_path.name],
        cwd=str(book_dir),
    )
    if result.returncode != 0:
        print('tab2opf failed with exit code', result.returncode)
        sys.exit(result.returncode)

    opf_path = book_dir / f'{output_basename}.opf'
    if not opf_path.exists():
        print('Error: OPF not created:', opf_path)
        sys.exit(1)

    kindlegen = find_kindlegen()
    if not kindlegen:
        print('Error: kindlegen not found.')
        print('  Set KINDLEGEN to the full path to kindlegen.exe, or add kindlegen to your PATH.')
        print('  On Windows, Kindle Previewer installs it under %LOCALAPPDATA%\\Amazon\\Kindle Previewer 3\\lib\\fc\\bin\\')
        sys.exit(1)
    if os.environ.get('KINDLEGEN') and not Path(kindlegen).exists():
        print('Error: kindlegen not found at KINDLEGEN.')
        print('  KINDLEGEN:', kindlegen)
        sys.exit(1)

    print('Running kindlegen...')
    result = subprocess.run(
        [kindlegen, str(opf_path)],
        cwd=str(book_dir),
    )
    mobi_path = book_dir / f'{output_basename}.mobi'
    # kindlegen returns 1 when it builds with warnings (e.g. onclick, index); .mobi is still created
    if result.returncode not in (0, 1):
        print('kindlegen failed with exit code', result.returncode)
        sys.exit(result.returncode)
    if result.returncode == 1 and mobi_path.exists():
        print('  (kindlegen reported warnings but .mobi was built)')

    print('Done. Output:', output_path)
    print('  OPF/HTML/.mobi in', book_dir)


if __name__ == '__main__':
    main()
