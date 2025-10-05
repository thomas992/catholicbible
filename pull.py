#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re, json, sys
from pathlib import Path

SRC = Path("pg1581.txt")
OUT = Path("bible.json")

# ---------- Canonical name map (Douay → standard) ----------
CANONICAL = {
    # OT
    "GENESIS":"Genesis","EXODUS":"Exodus","LEVITICUS":"Leviticus","NUMBERS":"Numbers","DEUTERONOMY":"Deuteronomy",
    "JOSUE":"Joshua","JOSHUA":"Joshua","JUDGES":"Judges","RUTH":"Ruth",
    "1 KINGS":"1 Kings","I KINGS":"1 Kings","FIRST BOOK OF KINGS":"1 Kings","1 SAMUEL":"1 Kings",
    "2 KINGS":"2 Kings","II KINGS":"2 Kings","SECOND BOOK OF KINGS":"2 Kings","2 SAMUEL":"2 Kings",
    "1 PARALIPOMENON":"1 Chronicles","I PARALIPOMENON":"1 Chronicles","1 CHRONICLES":"1 Chronicles",
    "2 PARALIPOMENON":"2 Chronicles","II PARALIPOMENON":"2 Chronicles","2 CHRONICLES":"2 Chronicles",
    "1 ESDRAS":"Ezra","ESDRAS 1":"Ezra","EZRA":"Ezra",
    "2 ESDRAS":"Nehemiah","ESDRAS 2":"Nehemiah","NEHEMIAS":"Nehemiah","NEHEMIAH":"Nehemiah",
    "TOBIAS":"Tobit","TOBIT":"Tobit","JUDITH":"Judith","ESTHER":"Esther","JOB":"Job",
    "PSALMS":"Psalms","PSALM":"Psalms","PROVERBS":"Proverbs","ECCLESIASTES":"Ecclesiastes",
    "ECCLESIASTICUS":"Sirach","SIRACH":"Sirach","WISDOM":"Wisdom",
    "CANTICLE OF CANTICLES":"Song of Solomon","CANTICLES":"Song of Solomon","SONG OF SOLOMON":"Song of Solomon",
    "ISAIAS":"Isaiah","ISAIAH":"Isaiah","JEREMIAS":"Jeremiah","JEREMIAH":"Jeremiah",
    "LAMENTATIONS":"Lamentations","BARUCH":"Baruch","EZECHIEL":"Ezekiel","EZEKIEL":"Ezekiel","DANIEL":"Daniel",
    "OSEE":"Hosea","HOSEA":"Hosea","JOEL":"Joel","AMOS":"Amos",
    "ABDIAS":"Obadiah","OBADIAH":"Obadiah","JONAS":"Jonah","JONAH":"Jonah",
    "MICHEAS":"Micah","MICAH":"Micah","NAHUM":"Nahum",
    "HABACUC":"Habakkuk","HABAKKUK":"Habakkuk","SOPHONIAS":"Zephaniah","ZEPHANIAH":"Zephaniah",
    "AGGEUS":"Haggai","HAGGAI":"Haggai","ZACHARIAS":"Zechariah","ZECHARIAH":"Zechariah","MALACHIAS":"Malachi","MALACHI":"Malachi",
    # Deuterocanon
    "1 MACHABEES":"1 Maccabees","1 MACCABEES":"1 Maccabees",
    "2 MACHABEES":"2 Maccabees","2 MACCABEES":"2 Maccabees",
    # NT
    "MATTHEW":"Matthew","MARK":"Mark","LUKE":"Luke","JOHN":"John",
    "ACTS":"Acts","ACTS OF THE APOSTLES":"Acts",
    "ROMANS":"Romans","1 CORINTHIANS":"1 Corinthians","2 CORINTHIANS":"2 Corinthians",
    "GALATIANS":"Galatians","EPHESIANS":"Ephesians","PHILIPPIANS":"Philippians","COLOSSIANS":"Colossians",
    "1 THESSALONIANS":"1 Thessalonians","2 THESSALONIANS":"2 Thessalonians",
    "1 TIMOTHY":"1 Timothy","2 TIMOTHY":"2 Timothy","TITUS":"Titus","PHILEMON":"Philemon",
    "HEBREWS":"Hebrews","JAMES":"James","1 PETER":"1 Peter","2 PETER":"2 Peter",
    "1 JOHN":"1 John","2 JOHN":"2 John","3 JOHN":"3 John","JUDE":"Jude",
    "APOCALYPSE":"Revelation","REVELATION":"Revelation",
}
CANONICAL.update({
    # Samuel/Kings dual naming (Douay often uses Kings; headings may say Samuel)
    "THE FIRST BOOK OF SAMUEL":"1 Kings",
    "THE SECOND BOOK OF SAMUEL":"2 Kings",
    "FIRST BOOK OF SAMUEL":"1 Kings",
    "SECOND BOOK OF SAMUEL":"2 Kings",

    # Kings explicitly
    "THE FIRST BOOK OF KINGS":"1 Kings",
    "THE SECOND BOOK OF KINGS":"2 Kings",

    # Paralipomenon (Chronicles)
    "THE FIRST BOOK OF PARALIPOMENON":"1 Chronicles",
    "THE SECOND BOOK OF PARALIPOMENON":"2 Chronicles",
    "FIRST BOOK OF PARALIPOMENON":"1 Chronicles",
    "SECOND BOOK OF PARALIPOMENON":"2 Chronicles",

    # Esdras (Ezra/Nehemiah)
    "THE FIRST BOOK OF ESDRAS":"Ezra",
    "THE SECOND BOOK OF ESDRAS":"Nehemiah",
    "FIRST BOOK OF ESDRAS":"Ezra",
    "SECOND BOOK OF ESDRAS":"Nehemiah",

    # Generic “THE BOOK OF …” safety (common in your file)
    "THE BOOK OF GENESIS":"Genesis",
    "THE BOOK OF EXODUS":"Exodus",
    "THE BOOK OF LEVITICUS":"Leviticus",
    "THE BOOK OF NUMBERS":"Numbers",
    "THE BOOK OF DEUTERONOMY":"Deuteronomy",
    "THE BOOK OF JOSUE":"Joshua",
    "THE BOOK OF JOSHUA":"Joshua",
    "THE BOOK OF JUDGES":"Judges",
    "THE BOOK OF RUTH":"Ruth",
    "THE BOOK OF NEHEMIAS":"Nehemiah",
    "THE BOOK OF NEHEMIAH":"Nehemiah",
    "THE BOOK OF TOBIAS":"Tobit",
    "THE BOOK OF TOBIT":"Tobit",
    "THE BOOK OF JUDITH":"Judith",
    "THE BOOK OF ESTHER":"Esther",
    "THE BOOK OF JOB":"Job",
    "THE BOOK OF PSALMS":"Psalms",
    "THE BOOK OF PROVERBS":"Proverbs",
    "THE BOOK OF WISDOM":"Wisdom",
    "THE BOOK OF ECCLESIASTES":"Ecclesiastes",
    "THE BOOK OF ECCLESIASTICUS":"Sirach",
    "THE BOOK OF ISAIAS":"Isaiah",
    "THE BOOK OF ISAIAH":"Isaiah",
    "THE BOOK OF JEREMIAS":"Jeremiah",
    "THE BOOK OF JEREMIAH":"Jeremiah",
    "THE BOOK OF LAMENTATIONS":"Lamentations",
    "THE BOOK OF BARUCH":"Baruch",
    "THE BOOK OF EZECHIEL":"Ezekiel",
    "THE BOOK OF EZEKIEL":"Ezekiel",
    "THE BOOK OF DANIEL":"Daniel",
    "THE BOOK OF OSEE":"Hosea",
    "THE BOOK OF HOSEA":"Hosea",
    "THE BOOK OF JOEL":"Joel",
    "THE BOOK OF AMOS":"Amos",
    "THE BOOK OF ABDIAS":"Obadiah",
    "THE BOOK OF OBADIAH":"Obadiah",
    "THE BOOK OF JONAS":"Jonah",
    "THE BOOK OF JONAH":"Jonah",
    "THE BOOK OF MICHEAS":"Micah",
    "THE BOOK OF MICAH":"Micah",
    "THE BOOK OF NAHUM":"Nahum",
    "THE BOOK OF HABACUC":"Habakkuk",
    "THE BOOK OF HABAKKUK":"Habakkuk",
    "THE BOOK OF SOPHONIAS":"Zephaniah",
    "THE BOOK OF ZEPHANIAH":"Zephaniah",
    "THE BOOK OF AGGEUS":"Haggai",
    "THE BOOK OF HAGGAI":"Haggai",
    "THE BOOK OF ZACHARIAS":"Zechariah",
    "THE BOOK OF ZECHARIAH":"Zechariah",
    "THE BOOK OF MALACHIAS":"Malachi",
    "THE BOOK OF MALACHI":"Malachi",
})

def canonize(name: str) -> str:
    key = re.sub(r'[^\w\s]', ' ', name).upper()
    key = re.sub(r'\s+', ' ', key).strip()

    # Trim common leading phrases
    key = re.sub(r'^(THE\s+BOOK\s+OF\s+)', '', key)
    key = re.sub(r'^(THE\s+FIRST\s+BOOK\s+OF\s+)', 'FIRST BOOK OF ', key)
    key = re.sub(r'^(THE\s+SECOND\s+BOOK\s+OF\s+)', 'SECOND BOOK OF ', key)

    return CANONICAL.get(key, key.title())


# ---------- Roman numerals ----------
ROMAN = {'I':1,'V':5,'X':10,'L':50,'C':100,'D':500,'M':1000}
def roman_to_int(s):
    s=s.upper(); total=0; prev=0
    for ch in reversed(s):
        v=ROMAN.get(ch,0)
        if v<prev: total-=v
        else: total+=v; prev=v
    return total

# ---------- Headings & verses ----------
# Your file has lines like: "Genesis Chapter 1"
# Accept book names starting with digits or words, with dashes/periods/spaces.
BOOK_CHAPTER_RE = re.compile(
    r'^\s*([A-Za-z0-9][A-Za-z0-9 \-\.]*?)\s+Chapter\s+([IVXLCDM]+|\d+)\s*$',
    re.IGNORECASE
)


# Verse at line start:
#   "5:1. This is the book ..."  (chapter:verse)
#   "1. In the beginning ..."    (verse only)
LINE_VERSE_WITH_CH = re.compile(r'^\s*(\d{1,3})\s*:\s*(\d{1,3})\s*[\.\):,]?\s+(.*\S.*)$')
LINE_VERSE_SIMPLE  = re.compile(r'^\s*(\d{1,3})\s*[\.\):,]?\s+(.*\S.*)$')

MAX_VERSE_NUM = 200
MAX_JUMP = 4  # allow small gaps if some numerals are omitted in print

def parse_verses(body: str, chapter_num: int):
    # First: prefer line-start verse markers (robust, readable)
    verses=[]; cur_no=None; buf=[]
    for raw in body.splitlines():
        s = raw.strip()
        if not s:
            continue
        m = LINE_VERSE_WITH_CH.match(s)
        if m:
            ch = int(m.group(1)); v = int(m.group(2)); text = m.group(3).strip()
            if ch == chapter_num and 1 <= v <= MAX_VERSE_NUM:
                if cur_no is not None and buf:
                    verses.append({"number":cur_no, "text":" ".join(buf).strip()})
                cur_no, buf = v, [text]
                continue
        m2 = LINE_VERSE_SIMPLE.match(s)
        if m2:
            v = int(m2.group(1)); text = m2.group(2).strip()
            if 1 <= v <= MAX_VERSE_NUM:
                if cur_no is not None and buf:
                    verses.append({"number":cur_no, "text":" ".join(buf).strip()})
                cur_no, buf = v, [text]
                continue
        # continuation line
        if cur_no is not None:
            buf.append(s)
    if cur_no is not None and buf:
        verses.append({"number":cur_no, "text":" ".join(buf).strip()})
    if len(verses) > 1:
        return verses

    # Fallback: inline numbers with small forward jumps
    flat = re.sub(r'\s+', ' ', body).strip()
    if not flat:
        return []
    tokens = []
    for m in re.finditer(r'(\d{1,3})\s*[\.\):,]?\s+', flat):
        v = int(m.group(1))
        if 1 <= v <= MAX_VERSE_NUM:
            tokens.append((m.start(), v))
    if not tokens:
        return [{"number":1,"text":flat}]
    seq=[]; last=None
    for pos,v in tokens:
        if last is None or (v > last and v - last <= MAX_JUMP):
            seq.append((pos,v)); last=v
        elif v == last:
            continue
    if not seq:
        return [{"number":1,"text":flat}]
    seq.append((len(flat), None))
    out=[]
    for i in range(len(seq)-1):
        s, v = seq[i]; e, _ = seq[i+1]
        seg = re.sub(r'^\d{1,3}\s*[\.\):,]?\s+','', flat[s:e]).strip()
        if seg:
            out.append({"number":v,"text":seg})
    return out

def read_core_lines(text: str) -> list[str]:
    m1 = re.search(r'\*\*\*\s*START OF (THIS|THE) PROJECT GUTENBERG EBOOK', text, re.IGNORECASE)
    m2 = re.search(r'\*\*\*\s*END OF (THIS|THE) PROJECT GUTENBERG EBOOK', text, re.IGNORECASE)
    core = text[m1.end():m2.start()] if (m1 and m2) else text
    return core.splitlines()

def main():
    if not SRC.exists():
        print("pg1581.txt not found.", file=sys.stderr)
        sys.exit(1)

    txt = SRC.read_text(encoding="utf-8", errors="ignore")
    lines = read_core_lines(txt)
    print(f"Using local {SRC} ({len(txt):,} bytes).")

    # Find all "Book Chapter N" headings (this edition’s style)
    markers = []  # (line_idx, book_canonical, chap_num)
    for i, ln in enumerate(lines):
        m = BOOK_CHAPTER_RE.match(ln)
        if not m:
            continue
        raw_book = m.group(1).strip().replace('.', '')
        chap_lab = m.group(2)
        chap_num = int(chap_lab) if chap_lab.isdigit() else roman_to_int(chap_lab)
        book = canonize(raw_book)
        markers.append((i, book, chap_num))

    if not markers:
        print("No 'Book Chapter N' headings found. Dumping a few candidates (showing lines with 'Chapter'):")
        shown = 0
        for i, ln in enumerate(lines):
            if re.search(r'\bChapter\b', ln, re.IGNORECASE):
                print(f"  {i}: {ln[:120]}")
                shown += 1
                if shown >= 30: break
        OUT.write_text(json.dumps({"books":[]}, indent=2), encoding="utf-8")
        return

    # Build chapters by slicing from each heading to the next heading
    books=[]
    cur_book=None
    cur_chapters=[]
    for idx, (line_idx, book, chap_num) in enumerate(markers):
        start = line_idx + 1
        end   = markers[idx+1][0] if idx+1 < len(markers) else len(lines)
        body  = "\n".join(lines[start:end]).strip()

        verses = parse_verses(body, chap_num)
        if not verses:
            continue

        # Book switch?
        if cur_book is None:
            cur_book = book
            cur_chapters = []
        elif book != cur_book:
            if cur_chapters:
                books.append({"name": cur_book, "chapters": cur_chapters})
            cur_book = book
            cur_chapters = []

        cur_chapters.append({"number": chap_num, "verses": verses})

    # Flush last book
    if cur_book and cur_chapters:
        books.append({"name": cur_book, "chapters": cur_chapters})

    data = {"books": books}
    OUT.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    tb=len(books); tc=sum(len(b["chapters"]) for b in books); tv=sum(len(c["verses"]) for b in books for c in b["chapters"])
    print(f"Done. Books: {tb}, Chapters: {tc}, Verses: {tv}")
    if tb:
        print("First 10 books:", [b["name"] for b in books[:10]])
        print("Last 5 books:", [b["name"] for b in books[-5:]])

if __name__ == "__main__":
    main()
