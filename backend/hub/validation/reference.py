"""Authoritative reference lookups built from EDRDG dictionaries (data/reference/):
  - JMdict_e.gz     -> written form / reading / part of speech   (word + reading + verb group checks)
  - kanjidic2.xml.gz-> per-kanji Sino-Vietnamese (Hán-Việt) readings, on/kun, strokes, old JLPT level
License: CC BY-SA 4.0, Electronic Dictionary Research and Development Group (https://www.edrdg.org/).
The compact lookup DB (reference.sqlite) is built once by `python -m hub build-reference`.
"""
import gzip
import json
import re
import sqlite3
import unicodedata
from functools import lru_cache
from pathlib import Path

from ..db import ROOT
from .kana import KANJI_RE, kata_to_hira

REF_DIR = ROOT / "data" / "reference"
REF_DB = REF_DIR / "reference.sqlite"


EDRDG = "http://ftp.edrdg.org/pub/Nihongo/"


def build(ref_dir: Path = REF_DIR, out: Path = REF_DB) -> dict:
    import urllib.request
    ref_dir.mkdir(parents=True, exist_ok=True)
    for name in ("JMdict_e.gz", "kanjidic2.xml.gz"):
        if not (ref_dir / name).exists():
            urllib.request.urlretrieve(EDRDG + name, ref_dir / name)
    out.unlink(missing_ok=True)
    db = sqlite3.connect(out)
    db.executescript("""
      CREATE TABLE jm (written TEXT, reading TEXT, pos TEXT, common INTEGER);
      CREATE TABLE kd (kanji TEXT PRIMARY KEY, han_viet TEXT, onyomi TEXT, kunyomi TEXT, strokes INTEGER,
                       jlpt_old INTEGER, grade INTEGER, meanings_en TEXT);
    """)
    text = gzip.open(ref_dir / "JMdict_e.gz", "rt", encoding="utf-8").read()
    rows = []
    for entry in text.split("<entry>")[1:]:
        kebs = re.findall(r"<keb>(.*?)</keb>", entry)
        pos = " ".join(dict.fromkeys(re.findall(r"<pos>&(.*?);</pos>", entry)))   # JMdict order, unique
        common = int("_pri>" in entry)
        for r_ele in re.findall(r"<r_ele>(.*?)</r_ele>", entry, flags=re.S):
            reb = re.search(r"<reb>(.*?)</reb>", r_ele).group(1)
            restr = re.findall(r"<re_restr>(.*?)</re_restr>", r_ele)
            rows.append((reb, reb, pos, common))
            if "<re_nokanji/>" not in r_ele:
                rows.extend((k, reb, pos, common) for k in (restr or kebs))
    db.executemany("INSERT INTO jm VALUES (?,?,?,?)", rows)
    db.execute("CREATE INDEX jm_written ON jm(written)")

    text = gzip.open(ref_dir / "kanjidic2.xml.gz", "rt", encoding="utf-8").read()
    n = 0
    for ch in text.split("<character>")[1:]:
        g = lambda pat: re.findall(pat, ch)
        one = lambda pat: (int(m.group(1)) if (m := re.search(pat, ch)) else None)
        db.execute("INSERT OR IGNORE INTO kd VALUES (?,?,?,?,?,?,?,?)", (
            g(r"<literal>(.*?)</literal>")[0],
            json.dumps([v.upper() for v in g(r'r_type="vietnam">([^<]+)')], ensure_ascii=False),
            json.dumps(g(r'r_type="ja_on">([^<]+)'), ensure_ascii=False),
            json.dumps(g(r'r_type="ja_kun">([^<]+)'), ensure_ascii=False),
            one(r"<stroke_count>(\d+)"), one(r"<jlpt>(\d+)"), one(r"<grade>(\d+)"),
            json.dumps(g(r"<meaning>([^<]+)</meaning>"), ensure_ascii=False)))
        n += 1
    db.commit()
    stats = {"jmdict_rows": len(rows), "kanji": n}
    db.close()
    _db.cache_clear()
    return stats


@lru_cache(maxsize=1)
def _db() -> sqlite3.Connection | None:
    if not REF_DB.exists():
        return None
    return sqlite3.connect(f"file:{REF_DB.as_posix()}?mode=ro", uri=True, check_same_thread=False)


def available() -> bool:
    return _db() is not None


def _hira(s: str) -> str:
    return kata_to_hira(re.sub(r"[\s　・]", "", s))


def lookup(written: str) -> list[tuple[str, str, int]]:
    """[(reading, pos, common)] for an exact written form (kanji or kana)."""
    return _db().execute("SELECT reading, pos, common FROM jm WHERE written=?", (written,)).fetchall()


def clean_word(word: str) -> str:
    w = re.sub(r"[\[［（(].*?[\]］）)]", "", word)
    return re.sub(r"[\s　～〜~…。、？！?!.]", "", w)


I_TO_U = dict(zip("いきぎしちにびみり", "うくぐすつぬぶむる"))
U_TO_I = {u: i for i, u in I_TO_U.items()}


def masu_reading(dict_reading: str, pos: str) -> list[str]:
    """Polite (ます) readings a dictionary-form reading can produce, given its JMdict verb class."""
    r, out = _hira(dict_reading), []
    tags = pos.split()
    if any(t == "v1" or t.startswith("v1-") for t in tags):
        out.append(r[:-1] + "ます")
    if "v5aru" in tags:
        out.append(r[:-1] + "います")
    elif any(t.startswith("v5") for t in tags) and r[-1] in U_TO_I:
        out.append(r[:-1] + U_TO_I[r[-1]] + "ます")
    if "vk" in tags:
        out.append(r[:-2] + "きます")
    if "vs-i" in tags or "vs-s" in tags:
        out.append(r[:-2] + "します")
    return out


def verb_group(pos: str) -> int | None:
    tags = pos.split()
    groups = set()
    if any(t.startswith("v5") for t in tags):
        groups.add(1)
    if any(t == "v1" or t.startswith("v1-") for t in tags):
        groups.add(2)
    if any(t in ("vk", "vs-i", "vs-s") for t in tags):
        groups.add(3)
    return groups.pop() if len(groups) == 1 else None


def masu_candidates(word: str) -> list[tuple[str, str, int | None, int]]:
    """For a ます-form word: [(dictionary_form, expected_masu_reading, verb_group, common)] found in JMdict."""
    w = clean_word(word)
    if not w.endswith("ます") or len(w) < 3:
        return []
    stem = w[:-2]
    forms = {stem + "る"}
    if stem[-1] in I_TO_U:
        forms.add(stem[:-1] + I_TO_U[stem[-1]])
    if stem[-1] == "い":
        forms.add(stem[:-1] + "る")                       # くださいます -> くださる (v5aru)
    if stem in ("来", "き"):
        forms.add("来る")
    out = []
    for f in forms:
        for reading, pos, common in lookup(f):
            for mr in masu_reading(reading, pos):
                out.append((f, mr, verb_group(pos), common))
    if stem.endswith("し"):                                # noun + します / する itself
        base = stem[:-1]
        if not base:
            out.append(("する", "します", 3, 1))
        for reading, pos, common in lookup(base):
            if "vs" in pos.split() or "n" in pos.split():
                out.append((base + "する", _hira(reading) + "します", 3, common))
    return sorted(set(out), key=str)


def check_reading(word: str, reading: str) -> dict:
    """status: confirmed | mismatch | not_found. Adds dictionary form / verb group / POS when known.
    Only the first reading variant must be confirmed ('かい / がい': がい is a sound-change variant)."""
    w = clean_word(word)
    given = [_hira(clean_word(r)) for r in re.split(r"[/／]", reading) if clean_word(r)]
    if not w or not given:
        return {"status": "not_found"}
    direct = lookup(w)
    is_expression = any({"exp", "int"} & set(p.split()) and not verb_group(p) for _, p, _ in direct)
    cands = [] if is_expression else masu_candidates(word)
    if cands:
        match = [c for c in cands if c[1] == given[0]]
        if match:
            match = [c for c in match if c[3]] or match          # prefer common entries (借りる over 借る)
            groups = {c[2] for c in match}
            return {"status": "confirmed", "dictionary_form": sorted({c[0] for c in match})[0],
                    "verb_group": groups.pop() if len(groups) == 1 else None, "pos": "verb"}
        if not direct:
            return {"status": "mismatch", "expected": sorted({c[1] for c in cands}), "pos": "verb"}
    if direct:
        expected = sorted({_hira(r) for r, _, _ in direct})
        pos = next((p for r, p, _ in direct if _hira(r) == given[0]), direct[0][1])
        res = {"status": "confirmed" if given[0] in expected else "mismatch", "expected": expected,
               "pos": simple_pos(pos)}
        if res["pos"] == "verb" and verb_group(pos):
            res["verb_group"] = verb_group(pos)
            res["dictionary_form"] = w
        return res
    return {"status": "not_found"}


_TONES = {"̀", "́", "̃", "̉", "̣"}


def hv_key(syllable: str) -> tuple[str, str]:
    """Compare Hán-Việt syllables ignoring case, tone-mark placement (HOÀ/HÒA) and i/y spelling (KỶ/KỈ)."""
    d = unicodedata.normalize("NFD", syllable.upper().strip())
    tone = "".join(c for c in d if c in _TONES)
    base = unicodedata.normalize("NFC", "".join(c for c in d if c not in _TONES)).replace("Y", "I")
    return base, tone


# Standard readings used in Vietnamese Japanese-teaching materials that KANJIDIC2 lacks or gets wrong
# (mostly shinjitai forms mapped to the wrong hanzi). Reviewed by hand; see docs/ARCHITECTURE.md ADR-012.
HV_OVERRIDES = {
    "鶏": ["KÊ"], "着": ["TRƯỚC"], "晩": ["VÃN"], "両": ["LƯỠNG"], "桜": ["ANH"], "伝": ["TRUYỀN"],
    "払": ["PHẤT"], "県": ["HUYỆN"], "住": ["TRÚ"], "画": ["HỌA"], "政": ["CHÍNH"], "領": ["LÃNH"],
}


DIGITS = {d: k for ds in ("0123456789", "０１２３４５６７８９") for d, k in zip(ds, "〇一二三四五六七八九")}


def kanji_han_viet(kanji: str) -> list[str]:
    r = _db().execute("SELECT han_viet FROM kd WHERE kanji=?", (kanji,)).fetchone()
    return HV_OVERRIDES.get(kanji, []) + (json.loads(r[0]) if r else [])


def kanji_sequence(word: str, expand_repeat: bool = True) -> list[str]:
    """Kanji of a word in order; 々 repeats the previous kanji (when expand_repeat)."""
    out = []
    for c in clean_word(word):
        if c == "々" and out:
            if expand_repeat:
                out.append(out[-1])
        elif KANJI_RE.match(c):
            out.append(c)
        elif c in DIGITS:
            out.append(DIGITS[c])
    return out


def check_han_viet(word: str, han_viet: str | None) -> dict:
    """status: ok | mismatch | missing | no_kanji | unverifiable. per_kanji lists the allowed readings."""
    kanji = kanji_sequence(word)
    if not kanji:
        return {"status": "no_kanji"}
    per = [{"kanji": k, "allowed": kanji_han_viet(k)} for k in kanji]
    if not han_viet:
        return {"status": "missing", "per_kanji": per}
    tokens = [t for t in re.split(r"[\s,\-–—/／()（）]+", han_viet) if t]
    if len(kanji) == 1 and len(tokens) > 1:                 # "LẠC / NHẠC": alternatives for a single kanji
        ok = all(hv_key(t) in {hv_key(x) for x in per[0]["allowed"]} for t in tokens)
        return {"status": "ok" if ok else "mismatch", "reason": "reading", "wrong_for": [] if ok else kanji,
                "per_kanji": per}
    if len(tokens) != len(kanji):
        short = kanji_sequence(word, expand_repeat=False)   # 時々 = THỜI is accepted
        if len(tokens) != len(short):
            return {"status": "mismatch", "reason": "count", "per_kanji": per}
        kanji = short
    allowed = [kanji_han_viet(k) for k in kanji]
    bad = [k for k, a, t in zip(kanji, allowed, tokens) if a and hv_key(t) not in {hv_key(x) for x in a}]
    if bad:
        return {"status": "mismatch", "reason": "reading", "wrong_for": bad, "per_kanji": per}
    if any(not a for a in allowed):
        return {"status": "unverifiable", "per_kanji": per}
    return {"status": "ok", "per_kanji": per}


POS_NAMES = {"adj-i": "i_adjective", "adj-ix": "i_adjective", "adj-na": "na_adjective", "adv": "adverb",
             "adv-to": "adverb", "n": "noun", "pn": "pronoun", "ctr": "counter", "conj": "conjunction",
             "int": "interjection", "prt": "particle", "exp": "expression", "suf": "suffix", "n-suf": "suffix",
             "pref": "prefix", "n-pref": "prefix", "adj-no": "noun", "adj-pn": "prenominal", "num": "numeral"}
VERB_CLASS = re.compile(r"^(v1|v5|vk|vz|vs-[is])")      # conjugation classes; vt/vi/vs alone are not verbs


def simple_pos(pos: str) -> str | None:
    """Primary part of speech = first JMdict tag we can name (勉強: n vs vt → noun; 分かる: v5r vi → verb)."""
    for tag in pos.split():
        if VERB_CLASS.match(tag):
            return "verb"
        if tag in POS_NAMES:
            return POS_NAMES[tag]
    return None
