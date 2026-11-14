"""Kana → Hepburn romaji, used only for the romaji consistency check (not shown to learners)."""
import re
import unicodedata

_BASE = {
    "あ": "a", "い": "i", "う": "u", "え": "e", "お": "o",
    "か": "ka", "き": "ki", "く": "ku", "け": "ke", "こ": "ko",
    "が": "ga", "ぎ": "gi", "ぐ": "gu", "げ": "ge", "ご": "go",
    "さ": "sa", "し": "shi", "す": "su", "せ": "se", "そ": "so",
    "ざ": "za", "じ": "ji", "ず": "zu", "ぜ": "ze", "ぞ": "zo",
    "た": "ta", "ち": "chi", "つ": "tsu", "て": "te", "と": "to",
    "だ": "da", "ぢ": "ji", "づ": "zu", "で": "de", "ど": "do",
    "な": "na", "に": "ni", "ぬ": "nu", "ね": "ne", "の": "no",
    "は": "ha", "ひ": "hi", "ふ": "fu", "へ": "he", "ほ": "ho",
    "ば": "ba", "び": "bi", "ぶ": "bu", "べ": "be", "ぼ": "bo",
    "ぱ": "pa", "ぴ": "pi", "ぷ": "pu", "ぺ": "pe", "ぽ": "po",
    "ま": "ma", "み": "mi", "む": "mu", "め": "me", "も": "mo",
    "や": "ya", "ゆ": "yu", "よ": "yo",
    "ら": "ra", "り": "ri", "る": "ru", "れ": "re", "ろ": "ro",
    "わ": "wa", "ゐ": "i", "ゑ": "e", "を": "o", "ん": "n", "ゔ": "vu",
    "ぁ": "a", "ぃ": "i", "ぅ": "u", "ぇ": "e", "ぉ": "o", "ゃ": "ya", "ゅ": "yu", "ょ": "yo", "ゎ": "wa",
}
_SMALL_Y = {"ゃ": "a", "ゅ": "u", "ょ": "o"}
_SMALL_V = {"ぁ": "a", "ぃ": "i", "ぅ": "u", "ぇ": "e", "ぉ": "o"}


def kata_to_hira(s: str) -> str:
    return "".join(chr(ord(c) - 0x60) if "ァ" <= c <= "ヶ" else c for c in s)


def to_romaji(kana: str) -> str:
    s = kata_to_hira(kana)
    out: list[str] = []
    i = 0
    while i < len(s):
        c = s[i]
        nxt = s[i + 1] if i + 1 < len(s) else ""
        if c == "っ":
            # double the next consonant (っち → tchi)
            r = to_romaji(s[i + 1:i + 3])[:1] if nxt else ""
            out.append("t" if r == "c" else r)
            i += 1
            continue
        if c == "ー":
            prev = "".join(out)
            out.append(next((ch for ch in reversed(prev) if ch in "aiueo"), ""))
            i += 1
            continue
        if c in _BASE and nxt in _SMALL_Y and c not in _SMALL_Y:
            base = _BASE[c]
            if base in ("shi", "chi", "ji"):
                out.append(base[:-1] + _SMALL_Y[nxt])
            else:
                out.append(base[:-1] + "y" + _SMALL_Y[nxt])
            i += 2
            continue
        if c in _BASE and nxt in _SMALL_V:   # katakana loan combos: ティ, ファ, ジェ ...
            base = _BASE[c]
            out.append(("t" if base == "te" else "d" if base == "de" else base[:-1]) + _SMALL_V[nxt])
            i += 2
            continue
        out.append(_BASE.get(c, c))
        i += 1
    return "".join(out)


_MACRONS = str.maketrans({"ā": "a", "ī": "i", "ū": "u", "ē": "e", "ō": "o", "â": "a", "î": "i", "û": "u", "ê": "e", "ô": "o"})


def normalize_romaji(s: str) -> str:
    """Lossy normalization applied to BOTH sides so spelling conventions don't count as errors
    (macrons vs ou, particle は=wa, へ=e, n', m before b/p)."""
    s = unicodedata.normalize("NFC", s.lower()).translate(_MACRONS)
    s = re.sub(r"[^a-z]", "", s)
    s = s.replace("tch", "cch").replace("mb", "nb").replace("mp", "np").replace("mm", "nm")
    for a, b in (("ha", "wa"), ("he", "e"), ("wo", "o"), ("ou", "o"), ("oo", "o"), ("uu", "u"), ("ei", "e"), ("ee", "e"), ("aa", "a"), ("ii", "i")):
        s = s.replace(a, b)
    return s


def romaji_matches(reading: str, romaji: str) -> bool:
    return normalize_romaji(to_romaji(reading)) == normalize_romaji(romaji)


KANA_RE = re.compile(r"^[぀-ゟ゠-ヿー\s　～〜・、。？！?!]+$")
KANJI_RE = re.compile(r"[一-鿿]")
JAPANESE_RE = re.compile(r"[぀-ヿ一-鿿]")


if __name__ == "__main__":
    assert to_romaji("がっこう") == "gakkou"
    assert to_romaji("きって") == "kitte"
    assert to_romaji("まっちゃ") == "matcha"
    assert to_romaji("びょういん") == "byouin"
    assert to_romaji("コーヒー") == "koohii"
    assert to_romaji("パーティー") == "paatii"
    assert romaji_matches("びょういん", "Byōin")
    assert romaji_matches("わたしは", "watashi wa")
    assert not romaji_matches("いえ", "ie desu")
    print("ok")
