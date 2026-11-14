"""Rule-based JLPT-style vocabulary questions built from verified vocabulary (spec §11.5). Pure functions, no DB.

Two mondai of 言語知識（文字・語彙）:
  kanji_reading (問題1): word in kanji, choose its reading. Distractors are the classic N5 traps (voicing, small っ,
      long vowel, small ゃゅょ) applied only to the part read from kanji, and never equal a dictionary reading.
  orthography (問題2): word in hiragana, choose its spelling. Distractors swap one kanji for an N5 kanji that has
      exactly the reading this kanji takes in the word (同音異字), and must not be a real word (会う/合う rejected).
A question is produced only when 3 distinct, unambiguous distractors exist; otherwise the word is skipped.
"""
import random
import re

KANJI = re.compile(r"[一-鿿々]")
HIRA_ONLY = re.compile(r"^[ぁ-ゖー]+$")
WORD_OK = re.compile(r"^[一-鿿々ぁ-ゖー]+$")      # no ～, spaces, latin, digits, katakana

VOICE = ["かが", "きぎ", "くぐ", "けげ", "こご", "さざ", "しじ", "すず", "せぜ", "そぞ", "ただ", "てで", "とど",
         "はば", "ひび", "ふぶ", "へべ", "ほぼ", "はぱ", "ひぴ", "ふぷ", "へぺ", "ほぽ"]
GEMINATE_BEFORE = set("かきくけこさしすせそたちつてとぱぴぷぺぽ")
O_ROW = set("おこごそぞとどのほぼぽもよろょ")
E_ROW = set("えけげせぜてでねへべぺめれ")
U_ROW = set("うくぐすずつぬふぶぷむゆるゅ")
I_ROW = set("きぎしじちにひびぴみり")
SMALL = {"ゃ": "や", "ゅ": "ゆ", "ょ": "よ"}
BIG = {v: k for k, v in SMALL.items()}
RENDAKU = dict(zip("かきくけこさしすせそたちつてとはひふへほ", "がぎぐげござじずぜぞだぢづでどばびぶべぼ"))
HANDAKU = dict(zip("はひふへほ", "ぱぴぷぺぽ"))

TRAP_VI = {
    "voicing": "nhầm âm đục/âm trong (dakuten ゛/゜)",
    "add_geminate": "thừa âm ngắt っ",
    "drop_geminate": "thiếu âm ngắt っ",
    "add_long": "thừa trường âm",
    "drop_long": "thiếu trường âm",
    "small_to_big": "âm ghép phải viết nhỏ (ゃ・ゅ・ょ)",
    "big_to_small": "không phải âm ghép, や・ゆ・よ viết to",
}


def align(word: str, reading: str) -> list[tuple[int, int, str]] | None:
    """Spans of the reading covered by each kanji run of the word: [(start, end, kanji_run)], or None.
    Kana in the word (okurigana, ご-prefix) must appear literally in the reading."""
    runs = re.findall(r"[一-鿿々]+|[^一-鿿々]+", word)
    m = re.fullmatch("".join("(.+?)" if KANJI.match(r) else f"({re.escape(r)})" for r in runs), reading)
    if not m:
        return None
    return [(m.start(i), m.end(i), r) for i, r in enumerate(runs, 1) if KANJI.match(r)]


def reading_variants(reading: str, allowed: set[int] | None = None) -> dict[str, str]:
    """Every single-edit JLPT trap of a hiragana reading -> trap code. Only positions in `allowed` (the part read
    from kanji) may change, so okurigana and prefixes stay intact. None = whole reading."""
    s, out = reading, {}
    ok = (lambda i: i in allowed) if allowed is not None else (lambda i: 0 <= i < len(s))

    def add(v: str, code: str) -> None:
        if v != s and v not in out and HIRA_ONLY.match(v) and not v.startswith(("っ", "ゃ", "ゅ", "ょ", "ー")) \
                and not v.endswith("っ") and "っっ" not in v:
            out[v] = code

    def insert_ok(p: int) -> bool:          # inserting at p stays inside the kanji part
        return ok(p - 1) and (ok(p) or p == len(s))

    for i, ch in enumerate(s):
        nxt = s[i + 1] if i + 1 < len(s) else ""
        if ok(i):
            for pair in VOICE:
                if ch in pair:
                    add(s[:i] + pair[1 - pair.index(ch)] + s[i + 1:], "voicing")
            if ch == "っ":
                add(s[:i] + s[i + 1:], "drop_geminate")
            if ch in SMALL and i > 0:
                add(s[:i] + SMALL[ch] + s[i + 1:], "small_to_big")
            if ch in BIG and i > 0 and s[i - 1] in I_ROW:
                add(s[:i] + BIG[ch] + s[i + 1:], "big_to_small")
        if ch in GEMINATE_BEFORE and i > 0 and s[i - 1] not in "っん" and insert_ok(i):
            add(s[:i] + "っ" + s[i:], "add_geminate")
        if ch in O_ROW or ch in U_ROW:
            if nxt == "う" and ok(i + 1):
                add(s[:i + 1] + s[i + 2:], "drop_long")
            elif nxt not in "うおっ" and insert_ok(i + 1):
                add(s[:i + 1] + "う" + s[i + 1:], "add_long")
        if ch in E_ROW and nxt == "い" and ok(i + 1):
            add(s[:i + 1] + s[i + 2:], "drop_long")
    return out


def reading_distractors(reading: str, valid: set[str], rng: random.Random, n: int = 3,
                        allowed: set[int] | None = None) -> list[tuple[str, str]]:
    """n distinct traps [(text, code)] never equal to a valid reading, preferring different trap types."""
    cands = [(v, c) for v, c in reading_variants(reading, allowed).items() if v not in valid]
    rng.shuffle(cands)
    picked, codes = [], set()
    for v, c in cands:                          # one per trap type first, then fill
        if c not in codes:
            picked.append((v, c))
            codes.add(c)
    picked += [x for x in cands if x not in picked]
    return picked[:n] if len(picked) >= n else []


def surfaces(base: str) -> set[str]:
    """How a kanji reading can surface inside a compound: as is, voiced (rendaku), or geminated (がく -> がっ)."""
    out = {base}
    for table in (RENDAKU, HANDAKU):
        if base[0] in table:
            out.add(table[base[0]] + base[1:])
    if len(base) > 1 and base[-1] in "つくちき":
        out |= {x[:-1] + "っ" for x in list(out)}
    return out


def split_run(run: str, reading: str, readings_of) -> list[str] | None:
    """Base reading used by each kanji of a run, e.g. 学校/がっこう -> [がく, こう]; None if no dictionary split."""
    if not run:
        return [] if not reading else None
    for base in sorted(readings_of(run[0]) or (), key=len, reverse=True):
        for surf in surfaces(base):
            if reading.startswith(surf):
                rest = split_run(run[1:], reading[len(surf):], readings_of)
                if rest is not None:
                    return [base] + rest
    return None


def orthography_distractors(word: str, reading: str, readings_of, pool: dict[str, set[str]], is_word,
                            rng: random.Random, n: int = 3) -> list[tuple[str, str, str]]:
    """n distinct non-words [(text, original kanji, substitute)]: one kanji replaced by an N5 kanji (`pool`) that has
    exactly the reading this kanji takes in the word. Words read as a whole (今日 きょう) are skipped."""
    spans = align(word, reading)
    if not spans or "々" in word:
        return []
    cands, pos = [], 0
    for start, end, run in spans:
        pos = word.index(run, pos)
        bases = split_run(run, reading[start:end], readings_of)
        if bases is None:
            return []
        for j, (ch, base) in enumerate(zip(run, bases)):
            for other, rds in pool.items():
                if other != ch and other not in word and base in rds:
                    v = word[:pos + j] + other + word[pos + j + 1:]
                    if not is_word(v):
                        cands.append((v, ch, other))
        pos += len(run)
    cands = sorted(set(cands))
    rng.shuffle(cands)
    return cands[:n] if len(cands) >= n else []


def kanji_reading_set(onyomi: list[str], kunyomi: list[str]) -> set[str]:
    """KANJIDIC-style readings -> plain hiragana stems (ひと.つ -> ひと, -かい -> かい)."""
    out = set()
    for r in onyomi + kunyomi:
        r = "".join(chr(ord(c) - 0x60) if "ァ" <= c <= "ヶ" else c for c in r)
        r = r.split(".")[0].strip("-")
        if r:
            out.add(r)
    return out


def eligible(word: str, reading: str) -> bool:
    """Single words only: set phrases (どうぞお元気で, ほんの気持ちです) make poor 問題1/2 targets."""
    return bool(WORD_OK.match(word) and KANJI.search(word) and HIRA_ONLY.match(reading or "")
                and len(reading) >= 2 and len(word) <= 5)


def _options(correct: str, wrong: list[tuple[str, str]], rng: random.Random) -> tuple[list[dict], str, dict]:
    """Shuffle into options 1-4 -> (options, correct option_id, option explanations)."""
    items = [(correct, None)] + wrong
    rng.shuffle(items)
    opts, expl, answer = [], {}, ""
    for i, (text, why) in enumerate(items, 1):
        oid = str(i)
        opts.append({"option_id": oid, "text": text})
        if why is None:
            answer, expl[oid] = oid, "Đúng."
        else:
            expl[oid] = f"Sai: {why}."
    return opts, answer, expl


def make_questions(vocab: list[dict], valid_readings, readings_of, pool: dict[str, set[str]], is_word,
                   han_viet: dict[str, str] | None = None) -> list[dict]:
    """vocab rows: {id, word, reading, meaning_vi, lesson_number, example_jp}. valid_readings(word) -> hiragana
    readings accepted by the dictionary; readings_of(kanji) -> base readings (KANJIDIC2); pool: N5 kanji -> readings,
    the substitutes for orthography; is_word(text) -> True when the spelling exists in the dictionary."""
    han_viet = han_viet or {}
    hv = lambda k: f" ({han_viet[k]})" if han_viet.get(k) else ""
    seen, out = set(), []
    for v in sorted(vocab, key=lambda r: r["id"]):
        word, reading = v["word"], v["reading"]
        if not eligible(word, reading) or word in seen:
            continue
        seen.add(word)
        spans = align(word, reading)
        if not spans:
            continue
        ex = v.get("example_jp") or ""
        sentence = ex if word in ex else None
        base = {"section": "vocabulary", "section_id": "SEC_01", "lesson_number": v.get("lesson_number"),
                "target_entity": v["id"]}
        meaning = f" ({v['meaning_vi']})" if v.get("meaning_vi") else ""

        qid = f"Q_GEN_KR_{v['id']}"
        rng = random.Random(qid)
        allowed = {i for a, b, _ in spans for i in range(a, b)}
        wrong = reading_distractors(reading, valid_readings(word) | {reading}, rng, allowed=allowed)
        if wrong:
            opts, ans, expl = _options(reading, [(w, TRAP_VI[c]) for w, c in wrong], rng)
            out.append({**base, "question_id": qid, "mondai_no": 1, "mondai_type": "kanji_reading",
                        "question_text": sentence or word, "target": word, "options": opts, "correct_answer": [ans],
                        "option_explanations": expl, "explanation_vi": f"{word} đọc là {reading}{meaning}."})

        qid = f"Q_GEN_OR_{v['id']}"
        rng = random.Random(qid)
        wrong = orthography_distractors(word, reading, readings_of, pool, is_word, rng)
        if wrong:
            opts, ans, expl = _options(word, [(w, f"{s}{hv(s)} cùng âm nhưng không phải {o}{hv(o)}; không có từ {w}")
                                              for w, o, s in wrong], rng)
            out.append({**base, "question_id": qid, "mondai_no": 2, "mondai_type": "orthography",
                        "question_text": sentence.replace(word, reading, 1) if sentence else reading,
                        "target": reading, "options": opts, "correct_answer": [ans], "option_explanations": expl,
                        "explanation_vi": f"{reading} viết là {word}{meaning}."})
    return out


if __name__ == "__main__":
    r = random.Random(0)
    assert set(reading_variants("がっこう")) >= {"がこう", "かっこう", "がっこ"}
    assert align("咲きます", "さきます") == [(0, 1, "咲")] and align("ご家族", "ごかぞく") == [(1, 4, "家族")]
    assert all(v.endswith("きます") for v in reading_variants("さきます", {0}))
    assert all(v.startswith("ご") for v in reading_variants("ごかぞく", {1, 2, 3}))
    d = reading_distractors("がっこう", {"がっこう"}, r)
    assert len(d) == 3 and "がっこう" not in [x for x, _ in d]
    assert reading_distractors("ん", set(), r) == []
    rd = {"学": {"がく"}, "校": {"こう"}, "急": {"きゅう"}, "行": {"こう", "い", "ぎょう"}, "口": {"こう", "くち"}}
    assert split_run("学校", "がっこう", rd.get) == ["がく", "こう"]
    assert split_run("急行", "きゅうこう", rd.get) == ["きゅう", "こう"]
    assert split_run("今日", "きょう", {"今": {"いま", "こん"}, "日": {"ひ", "にち"}}.get) is None
    print("ok")
