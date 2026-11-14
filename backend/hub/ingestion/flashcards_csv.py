"""Parse the user's flashcard CSV exports (front, back) into normalized vocabulary fields.

Three back-side formats exist in docs/N5/flashcards:
  A) "1. Đọc: びょういん - BỆNH VIỆN\n2. Rōmaji: ...\n3. Nghĩa: ...\n4. Ví dụ: ...\n5. Rōmaji ví dụ: ...\n6. Dịch ví dụ: ..."
  B) same six labelled lines without the numbers
  C) free-form question/answer (no labels) -> not vocabulary, kept RAW only
"""
import csv
import re
from pathlib import Path

LABELS = {
    "đọc": "reading_raw",
    "rōmaji": "romaji",
    "romaji": "romaji",
    "nghĩa": "meaning_vi",
    "ví dụ": "example_jp",
    "rōmaji ví dụ": "example_romaji",
    "romaji ví dụ": "example_romaji",
    "dịch ví dụ": "example_vi",
}
LINE_RE = re.compile(r"^\s*(?:\d+\.\s*)?([^:：]+)[:：]\s*(.*)$")


def read_rows(path: Path) -> list[list[str]]:
    with open(path, encoding="utf-8-sig", newline="") as f:
        return [r for r in csv.reader(f) if any(c.strip() for c in r)]


def deck_info(path: Path) -> tuple[str, int | None, list[str]]:
    """deck name, lesson number, topics — derived from the file name only."""
    stem = path.stem.removeprefix("flashcards_")
    m = re.fullmatch(r"Bai(\d+)", stem)
    if m:
        return stem, int(m.group(1)), []
    if "Kaiwa" in stem:
        return stem, None, ["kaiwa"]
    return stem, None, []


def split_reading(raw: str) -> tuple[str, str | None]:
    """'びょういん - BỆNH VIỆN' -> ('びょういん', 'BỆNH VIỆN'); 'おでかけですか (XUẤT)' -> (..., 'XUẤT')."""
    raw = raw.strip()
    # "サイズ (Không có âm Hán-Việt)" -> explicit "no Hán-Việt" note
    m = re.match(r"^(.*?)\s*[（(]\s*Không có[^)）]*[)）]\s*$", raw)
    if m:
        return m.group(1).strip(), None
    # "トイレ / おてあらい (お手洗い - THỦ TẨY)" -> dash lives inside the parentheses
    m = re.match(r"^([^(（]*?)\s*[（(]([^)）]*?\s[-–—]\s[^)）]*)[)）]\s*$", raw)
    if m:
        hv = m.group(2).split(" - ", 1)[1] if not re.match(r"^[A-ZĐÀ-Ỹ\s\-–—]+$", m.group(2)) else m.group(2)
        return m.group(1).strip(), hv.strip()
    m = re.match(r"^(.*?)\s+[-–—]\s+(.+)$", raw)
    if m:
        return m.group(1).strip(), m.group(2).strip()
    m = re.match(r"^(.*?)\s*[（(]([^)）]+)[)）]\s*$", raw)
    if m and m.group(2).isupper():
        return m.group(1).strip(), m.group(2).strip()
    return raw, None


def parse_back(back: str) -> dict | None:
    """Return labelled fields, or None if the text is not in the labelled format."""
    fields: dict[str, str] = {}
    for line in back.splitlines():
        m = LINE_RE.match(line)
        if not m:
            continue
        key = LABELS.get(m.group(1).strip().lower())
        if key and key not in fields:
            fields[key] = m.group(2).strip()
    if "reading_raw" not in fields or "meaning_vi" not in fields:
        return None
    reading, han_viet = split_reading(fields.pop("reading_raw"))
    fields["reading"] = reading
    fields["han_viet"] = None if han_viet in (None, "N/A", "-", "") else han_viet
    return fields


def guess_pos(word: str) -> str | None:
    """Only flags obvious ます-form verbs; anything else stays NULL (no guessing)."""
    if word.endswith("ます") and len(word) > 2:
        return "verb"
    return None
