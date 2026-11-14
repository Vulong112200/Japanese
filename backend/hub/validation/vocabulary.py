"""Automated vocabulary validation rules (spec §11.2). Returns issues; never edits data."""
import re

from .kana import JAPANESE_RE, KANA_RE, KANJI_RE, kata_to_hira, romaji_matches

Issue = tuple[str, str, str, str | None]  # code, severity, message, suggestion
MOJIBAKE_RE = re.compile(r"�|Ã[\u0080-¿]|â€|ã[\u0080-¿]{2}")
ALT_SPLIT = re.compile(r"\s*[/／]\s*")


def reading_variants(reading: str) -> list[str]:
    """'なに / なん' -> ['なに','なん'];  'てんきん [～します]' -> ['てんきん'] (bracketed usage note dropped)."""
    core = re.sub(r"\s*[\[［].*?[\]］]", "", reading)
    return [r for r in ALT_SPLIT.split(core) if r]


def kanji_count(word: str) -> int:
    return len(KANJI_RE.findall(word))


def validate(v: dict) -> list[Issue]:
    issues: list[Issue] = []
    word, reading = v.get("word") or "", v.get("reading") or ""
    for f in ("word", "reading", "meaning_vi"):
        if not (v.get(f) or "").strip():
            issues.append(("missing_field", "error", f"Thiếu trường bắt buộc: {f}", None))
    for f, val in v.items():
        if isinstance(val, str) and MOJIBAKE_RE.search(val):
            issues.append(("encoding", "error", f"Trường {f} có ký tự lỗi mã hoá", None))
    if word and not JAPANESE_RE.search(word):
        issues.append(("latin_word", "info", "Từ viết bằng chữ Latin (vd. CD); dựa vào cách đọc kana", None))

    variants = reading_variants(reading) if reading else []
    bad = [r for r in variants if not KANA_RE.match(r)]
    if bad:
        issues.append(("reading_not_kana", "error", f"Cách đọc có ký tự không phải kana: {reading}", None))
    elif variants and v.get("romaji"):
        romaji_variants = ALT_SPLIT.split(re.sub(r"\s*[\[［].*?[\]］]", "", v["romaji"]))
        if len(variants) == len(romaji_variants):
            pairs = zip(variants, romaji_variants)
        else:
            pairs = [(variants[0], v["romaji"])]
        if not all(romaji_matches(r, ro) for r, ro in pairs):
            issues.append(("romaji_mismatch", "warning",
                           f"Romaji '{v['romaji']}' không khớp cách đọc '{reading}'", None))
    if word and KANA_RE.match(word) and variants and not bad:
        w = kata_to_hira(word.replace(" ", "").replace("　", ""))
        if not any(kata_to_hira(r.replace(" ", "")) == w for r in variants):
            issues.append(("kana_word_reading_differs", "warning",
                           f"Từ viết bằng kana nhưng khác cách đọc: {word} / {reading}", None))

    hv = v.get("han_viet")
    n_kanji = kanji_count(word)
    if hv:
        alternatives = ALT_SPLIT.split(hv)
        counts = [len([t for t in re.split(r"[\s,\-–—]+", a.strip("() ")) if t]) for a in alternatives]
        if n_kanji == 0:
            issues.append(("han_viet_without_kanji", "info",
                           f"Từ viết bằng kana nhưng có Hán-Việt '{hv}' (của chữ Hán gốc?) — cần kiểm tra", None))
        elif n_kanji not in counts and not (len(alternatives) > 1 and all(c == 1 for c in counts) and n_kanji == 1):
            issues.append(("han_viet_count", "warning",
                           f"Hán-Việt '{hv}' có {counts[0]} âm tiết nhưng từ có {n_kanji} chữ kanji", None))
    elif n_kanji:
        issues.append(("han_viet_missing", "info", "Từ có kanji nhưng chưa có Hán-Việt", None))
    if v.get("part_of_speech") == "verb" and not v.get("verb_group"):
        issues.append(("needs_dictionary_form", "info",
                       "Động từ chỉ có thể ます; cần thể từ điển để xác định nhóm (không suy từ ます)", None))
    return issues


def status_for(issues: list[Issue]) -> str:
    return "needs_review" if any(s in ("error", "warning") for _, s, _, _ in issues) else "normalized"
