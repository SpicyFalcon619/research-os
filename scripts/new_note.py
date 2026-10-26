#!/usr/bin/env python3
"""Create a new paper note from notes/templates/paper-note.md.

Uses only the Python standard library. Never overwrites an existing note.
"""

import argparse
import datetime
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "notes" / "templates" / "paper-note.md"
OUT_DIR = ROOT / "notes" / "papers"

MAX_SLUG_WORDS = 6
MAX_SLUG_CHARS = 40
MIN_YEAR = 1900
MISSING = "[not provided]"
MISSING_YEAR = "[year not provided]"

EPILOG = """\
examples:
  python scripts/new_note.py "Attention Is All You Need" --authors "Vaswani et al." --year 2017 --venue NeurIPS --url "https://example.com/paper"
  python scripts/new_note.py "A Paper Whose Year I Do Not Know"

The note is saved as notes/papers/YYYY-firstauthor-short-title.md.
If the year is omitted the filename uses 'nd' (no date) and the note shows a
placeholder; the year is never guessed. If the file already exists the script
stops and leaves it untouched.
"""


def ascii_fold(text):
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")


def slugify(text, max_words=MAX_SLUG_WORDS, max_chars=MAX_SLUG_CHARS):
    """Lowercase ASCII words joined by hyphens; safe on Windows and Unix."""
    words = re.findall(r"[a-z0-9]+", ascii_fold(text).lower())[:max_words]
    slug = ""
    for word in words:
        candidate = f"{slug}-{word}" if slug else word
        if len(candidate) > max_chars:
            if not slug:
                slug = word[:max_chars]
            break
        slug = candidate
    return slug or "untitled"


def first_author_key(authors):
    """Short filesystem-safe key for the first author, or 'unknown'.

    Heuristic: take the first author (split on ';', ' and ', '&', or the first
    comma), drop 'et al.', and use the last word as the family name. A group
    name such as 'OpenAI' is kept as one word. Use --first-author to override.
    """
    if not authors or not authors.strip():
        return "unknown"
    first = re.split(r";|&|\band\b|,", authors.strip(), maxsplit=1, flags=re.IGNORECASE)[0]
    first = re.sub(r"\bet\.?\s*al\.?", "", first, flags=re.IGNORECASE).strip()
    words = re.findall(r"[^\s]+", first)
    if not words:
        return "unknown"
    key = slugify(words[-1], max_words=1, max_chars=20)
    return "unknown" if key == "untitled" else key


def clean_inline(value):
    """Collapse whitespace/control characters so a value stays on one line."""
    return re.sub(r"[\x00-\x1f\x7f\s]+", " ", value).strip()


def escape_markdown(value):
    """Backslash-escape characters that would accidentally format text."""
    value = re.sub(r"([\\`*_\[\]<>|])", r"\\\1", value)
    return re.sub(r"^(\s*)([#>+\-])", r"\1\\\2", value)


def parse_year(text):
    if not re.fullmatch(r"\d{4}", text.strip()):
        raise argparse.ArgumentTypeError(f"invalid year {text!r}: expected a four-digit year such as 2017")
    year = int(text)
    latest = datetime.date.today().year + 1
    if not MIN_YEAR <= year <= latest:
        raise argparse.ArgumentTypeError(f"invalid year {year}: expected {MIN_YEAR}-{latest}")
    return year


def fill_template(template, values):
    """Single-pass substitution so inserted text is never re-interpreted."""
    return re.sub(r"\{\{(\w+)\}\}", lambda m: values.get(m.group(1), m.group(0)), template)


def build_parser():
    parser = argparse.ArgumentParser(
        prog="new_note.py",
        description="Create a paper note in notes/papers/ from the paper-note template.",
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("title", help="paper title (quote it)")
    parser.add_argument("--authors", help='author list, e.g. "Vaswani et al."')
    parser.add_argument("--year", type=parse_year, help="four-digit publication year")
    parser.add_argument("--venue", help="venue, e.g. NeurIPS")
    parser.add_argument("--url", help="DOI or URL")
    parser.add_argument("--first-author", dest="first_author",
                        help="override the family-name key used in the filename")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)

    title = clean_inline(args.title)
    if not title:
        print("error: title must not be empty", file=sys.stderr)
        return 2
    url = clean_inline(args.url) if args.url else ""
    if re.search(r"\s", url):
        print("error: --url must not contain spaces", file=sys.stderr)
        return 2

    if not TEMPLATE.is_file():
        print(f"error: template not found: {TEMPLATE}\n"
              "Restore notes/templates/paper-note.md and try again.", file=sys.stderr)
        return 1

    if args.first_author:
        author_key = slugify(args.first_author, max_words=1, max_chars=20)
        author_key = "unknown" if author_key == "untitled" else author_key
    else:
        author_key = first_author_key(args.authors)

    year_part = str(args.year) if args.year else "nd"
    filename = f"{year_part}-{author_key}-{slugify(title)}.md"
    target = OUT_DIR / filename

    values = {
        "title": escape_markdown(title),
        "authors": escape_markdown(clean_inline(args.authors)) if args.authors and clean_inline(args.authors) else MISSING,
        "year": str(args.year) if args.year else MISSING_YEAR,
        "venue": escape_markdown(clean_inline(args.venue)) if args.venue and clean_inline(args.venue) else MISSING,
        "url": url or MISSING,
        "date": datetime.date.today().isoformat(),
    }

    try:
        content = fill_template(TEMPLATE.read_text(encoding="utf-8"), values)
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        # Mode "x" fails if the file exists, so an existing note is never overwritten.
        with open(target, "x", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
    except FileExistsError:
        print(f"error: note already exists, left untouched: {target}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"error: could not create note: {exc}", file=sys.stderr)
        return 1

    print(target)
    return 0


if __name__ == "__main__":
    sys.exit(main())
