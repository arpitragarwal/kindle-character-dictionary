# Kindle Character Dictionary

## Objective

Add the ability to look up character definitions (and a full English dictionary) on Kindle. You can use a combined dictionary: GCIDE (plain English) plus a book’s character list, so looking up a name shows a short character description tagged with `[Character]`, and normal words show standard definitions.

---

## Sources / Dependencies

- **tab2opf** – Converts tab-delimited dictionary files into OPF/HTML for Kindle. (Included; based on [Klokan Petr Přidal’s tab2opf](https://github.com/apeyser/tab2opf), migrated to Python 3.)
- **GCIDE** – [GNU Collaborative International Dictionary of English](https://savannah.gnu.org/projects/gcide/). Plain English definitions. You supply the GCIDE XML; the repo script `gcide2tab.py` converts it to tab format.
- **KindleGen** – Amazon’s command-line tool that builds `.mobi` from OPF. Install via [Kindle Previewer](https://www.amazon.com/Kindle-Previewer/b?node=21381691011) (kindlegen is in the app’s `lib/fc/bin/` folder). Set `KINDLEGEN` to the full path to `kindlegen.exe`, or add it to your PATH.
- **Python 3** – Required to run the scripts.

---

## How to run

### 1. One-time: build the GCIDE tab file

Download [GCIDE XML](https://www.ibiblio.org/webster/) and extract it under `dictionaries/gcide_xml-0.53/gcide_xml-0.53/` (or pass that folder as the first argument). Then:

```bash
python gcide2tab.py [path_to_gcide_xml_dir] [output.txt]
```

Default output: `dictionaries/gcide/gcide.txt`. You only need to do this once (or when you update GCIDE).

### 2. Per book: merge GCIDE + character list and build .mobi

Ensure the book has a tab-delimited character file in its folder, e.g. `dictionaries/speaker-for-the-dead/speaker-characters.txt` (format: `Character Name\tOne-line description`).

Run:

```bash
python merge_gcide_with_characters.py <book_folder>
```

Example:

```bash
python merge_gcide_with_characters.py speaker-for-the-dead
```

This script will:

1. Build a union file: all GCIDE entries + all character entries (character definitions are prefixed with `[Character] `).
2. Run tab2opf to generate OPF and HTML.
3. Run KindleGen to produce the `.mobi` in the same book folder.

Output files (e.g. for `speaker-for-the-dead`) appear in `dictionaries/<book_folder>/`:

- `speaker-characters-and-gcide.txt` (union)
- `speaker-characters-and-gcide.opf` / `.html`
- `speaker-characters-and-gcide.mobi`

Copy the `.mobi` to your Kindle’s `documents/dictionaries/` and set it as the dictionary (or an additional dictionary) in device settings.
