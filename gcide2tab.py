#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Convert GCIDE XML dictionary to tab-delimited text (word \\t definition)
for use with tab2opf.py and Kindle dictionary build.

Usage:
  python gcide2tab.py [path_to_gcide_xml_dir] [output.txt]

  Default: reads from dictionaries/gcide_xml-0.53/gcide_xml-0.53/
           writes to dictionaries/gcide/gcide.txt
"""

import re
import sys
import html
from pathlib import Path


def strip_tags(text):
    """Remove XML/HTML tags from text."""
    return re.sub(r'<[^>]+>', '', text)


def decode_entities(text):
    """Decode XML/HTML entities."""
    text = html.unescape(text)
    # GCIDE custom entities (Latin diacritics) - common ones
    replacements = [
        ('&ebreve_;', '\u0115'),   # e with breve
        ('&emacr;', '\u0113'),     # e with macron
        ('&ocirc;', '\u00f4'),     # o with circumflex
        ('&eitalic_;', '\u00e9'),  # e acute (guess)
        ('&omacr;', '\u014d'),    # o with macron
        ('&ubreve_;', '\u016d'),   # u with breve
        ('&ibreve_;', '\u012d'),   # i with breve
        ('&abreve_;', '\u0103'),   # a with breve
    ]
    for ent, char in replacements:
        text = text.replace(ent, char)
    return text


def extract_def_content(entry_text, start):
    """Extract content between <def> and matching </def> starting at start.
    Handles nested tags inside <def>...</def>.
    Returns (definition_text, end_position).
    """
    depth = 0
    i = start
    begin = None
    while i < len(entry_text):
        if entry_text[i:i+5] == '<def>':
            if depth == 0:
                begin = i + 5
            depth += 1
            i += 5
            continue
        if entry_text[i:i+6] == '</def>':
            depth -= 1
            if depth == 0:
                return entry_text[begin:i], i + 6
            i += 6
            continue
        i += 1
    return None, start


def extract_entry(entry_text):
    """Extract (headword, definition) from a single <p>...</p> entry block.
    Returns None if no <hw> and <def> found.
    """
    hw_match = re.search(r'<hw>([^<]*)</hw>', entry_text)
    if not hw_match:
        return None
    headword = hw_match.group(1).strip()

    defs = []
    pos = 0
    while True:
        idx = entry_text.find('<def>', pos)
        if idx == -1:
            break
        def_content, end_pos = extract_def_content(entry_text, idx)
        if def_content is not None:
            plain = strip_tags(def_content)
            plain = re.sub(r'\s+', ' ', plain).strip()
            if plain:
                defs.append(plain)
        pos = end_pos

    if not defs:
        return None
    headword = decode_entities(headword)
    definition = '; '.join(defs)
    definition = decode_entities(definition)
    # Replace tab and newline in definition so output is one line per entry
    definition = definition.replace('\t', ' ').replace('\n', ' ').replace('\r', ' ')
    definition = re.sub(r'\s+', ' ', definition).strip()
    return (headword, definition)


def process_file(path, out_entries):
    """Process one GCIDE XML letter file and add (word, def) to out_entries."""
    text = path.read_text(encoding='utf-8', errors='replace')
    # Split into entry blocks: <p><ent>... or <p> with <hw>
    blocks = re.split(r'<p>\s*<ent>', text)
    for block in blocks:
        if '<hw>' not in block or '<def>' not in block:
            continue
        # Wrap back so we have full <p> content
        entry_text = '<p><ent>' + block
        result = extract_entry(entry_text)
        if result:
            headword, definition = result
            # Merge if same headword appears in multiple entries (e.g. noun vs verb)
            if headword not in out_entries:
                out_entries[headword] = definition
            else:
                out_entries[headword] = out_entries[headword] + '; ' + definition


def main():
    if len(sys.argv) >= 2:
        xml_dir = Path(sys.argv[1])
    else:
        xml_dir = Path(__file__).parent / 'dictionaries' / 'gcide_xml-0.53' / 'gcide_xml-0.53'

    if len(sys.argv) >= 3:
        output_path = Path(sys.argv[2])
    else:
        output_path = Path(__file__).parent / 'dictionaries' / 'gcide' / 'gcide.txt'

    if not xml_dir.is_dir():
        print('Error: GCIDE XML directory not found:', xml_dir)
        sys.exit(1)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Letter files only (a-z)
    letter_files = []
    for c in 'abcdefghijklmnopqrstuvwxyz':
        f = xml_dir / f'gcide_{c}.xml'
        if f.exists():
            letter_files.append(f)

    if not letter_files:
        print('Error: No gcide_[a-z].xml files found in', xml_dir)
        sys.exit(1)

    entries = {}
    for f in sorted(letter_files):
        print('Processing', f.name, '...')
        process_file(f, entries)

    print('Total entries:', len(entries))

    with open(output_path, 'w', encoding='utf-8') as out:
        for headword in sorted(entries.keys()):
            defn = entries[headword]
            # Tab in headword would break format; replace if any
            h = headword.replace('\t', ' ').replace('\n', ' ').strip()
            out.write(h)
            out.write('\t')
            out.write(defn)
            out.write('\n')

    print('Wrote', output_path)


if __name__ == '__main__':
    main()
