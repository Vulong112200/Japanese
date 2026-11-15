"""Readings of numbers, counters and dates (ADR-029), as pure rules.

`expected_readings(jp, category)` derives every accepted reading of e.g. 三本 / 八日 / 四時 from phonology
(gemination いっ/ろっ/はっ/じゅっ, h→p/b, 階 さんがい) plus a small table of lexicalised forms (ひとつ, ついたち,
はたち…). It is written independently of data/normalized/numbers/numbers.json and is used to check that file and to
prove quiz distractors wrong.
"""
import re

DIGIT = dict(zip("一二三四五六七八九", range(1, 10)))
STD = {1: "いち", 2: "に", 3: "さん", 4: "よん", 5: "ご", 6: "ろく", 7: "なな", 8: "はち", 9: "きゅう"}
ALT = {4: {"よん", "し"}, 7: {"なな", "しち"}, 9: {"きゅう", "く"}}          # standalone digits

# category -> (counter kana, sound class, {digit: readings used before this counter})
# class: plain | k (gemination 1,6,8,10,100) | s (gemination 1,8,10) | h (1,6,8,10,100 → っp; 3/何 → b)
COUNTERS = {
    "nin": ("にん", "plain", {4: {"よ"}, 7: {"なな", "しち"}}),
    "mai": ("まい", "plain", {}), "dai": ("だい", "plain", {}),
    "hon": ("ほん", "h", {}), "hiki": ("ひき", "h", {}), "hai": ("はい", "h", {}),
    "fun": ("ふん", "h", {}),
    "satsu": ("さつ", "s", {}), "sai": ("さい", "s", {}), "shuukan": ("しゅうかん", "s", {}),
    "ko": ("こ", "k", {}), "kai": ("かい", "k", {}), "kai_floor": ("かい", "k", {}), "kagetsu": ("かげつ", "k", {}),
    "ji": ("じ", "plain", {4: {"よ"}, 7: {"しち", "なな"}, 9: {"く"}}),
    "jikan": ("じかん", "plain", {4: {"よ"}, 7: {"しち", "なな"}, 9: {"く"}}),
    "gatsu": ("がつ", "plain", {4: {"し"}, 7: {"しち"}, 9: {"く"}}),
    "nichi": ("にち", "plain", {7: {"しち"}, 9: {"く"}}),
    "nen": ("ねん", "plain", {4: {"よ"}, 7: {"なな", "しち"}, 9: {"きゅう", "く"}}),
    "en": ("えん", "plain", {4: {"よ"}}),
}
SUFFIX = {"nin": "人", "mai": "枚", "dai": "台", "hon": "本", "hiki": "匹", "hai": "杯", "fun": "分", "satsu": "冊",
          "sai": "歳", "shuukan": "週間", "ko": "個", "kai": "回", "kai_floor": "階", "kagetsu": "か月", "ji": "時",
          "jikan": "時間", "gatsu": "月", "nichi": "日", "nen": "年", "en": "円", "tsu": "つ"}
B_ON_THREE = {"hon", "hiki", "hai"}                       # 三本 さんぼん, 何本 なんぼん
P_ON_THREE_FOUR = {"fun"}                                 # 三分 さんぷん, 四分 よんぷん, 何分 なんぷん

LEXICAL = {
    "tsu": {1: {"ひとつ"}, 2: {"ふたつ"}, 3: {"みっつ"}, 4: {"よっつ"}, 5: {"いつつ"}, 6: {"むっつ"}, 7: {"ななつ"},
            8: {"やっつ"}, 9: {"ここのつ"}, 10: {"とお"}},
    "nin": {1: {"ひとり"}, 2: {"ふたり"}},
    "nichi": {1: {"ついたち"}, 2: {"ふつか"}, 3: {"みっか"}, 4: {"よっか"}, 5: {"いつか"}, 6: {"むいか"}, 7: {"なのか"},
              8: {"ようか"}, 9: {"ここのか"}, 10: {"とおか"}, 14: {"じゅうよっか"}, 20: {"はつか"},
              24: {"にじゅうよっか"}},
    "sai": {20: {"はたち", "にじゅっさい", "にじっさい"}},
}
YOUBI = {"月曜日": "げつようび", "火曜日": "かようび", "水曜日": "すいようび", "木曜日": "もくようび",
         "金曜日": "きんようび", "土曜日": "どようび", "日曜日": "にちようび", "何曜日": "なんようび"}
WORDS = {"半": {"はん"}, "いくつ": {"いくつ"}, "いくら": {"いくら"}}

VOICED = dict(zip("かきくけこさしすせそたちつてとはひふへほ", "がぎぐげござじずぜぞだぢづでどばびぶべぼ"))
HALF = dict(zip("はひふへほ", "ぱぴぷぺぽ"))
GEM = (("いち", "いっ"), ("ろく", "ろっ"), ("はち", "はっ"), ("じゅう", "じゅっ"), ("じゅう", "じっ"), ("ひゃく", "ひゃっ"))


def parse_number(s: str) -> int | None:
    """Kanji numeral (一…九, 十, 百, 千, 万) → int; None if not a numeral."""
    if not s or any(c not in DIGIT and c not in "十百千万" for c in s):
        return None
    total, chunk, digit = 0, 0, None
    for c in s:
        if c in DIGIT:
            if digit is not None:
                return None
            digit = DIGIT[c]
        elif c == "万":
            total += (chunk + (digit or 0) or 1) * 10000
            chunk, digit = 0, None
        else:
            chunk += (digit if digit is not None else 1) * {"十": 10, "百": 100, "千": 1000}[c]
            digit = None
    return total + chunk + (digit or 0)


def _tokens(n: int) -> list[tuple[str, int]]:
    out = []
    if n >= 10000:
        out.append(("man", n // 10000))
        n %= 10000
    for name, size in (("sen", 1000), ("hyaku", 100), ("juu", 10)):
        if n >= size:
            out.append((name, n // size))
            n %= size
    if n:
        out.append(("one", n))
    return out


def _token(name: str, d: int, digit_forms: dict | None = None) -> set[str]:
    if name == "one":
        return set((digit_forms or {}).get(d) or ALT.get(d) or {STD[d]})
    if name == "juu":
        return {"じゅう"} if d == 1 else {STD[d] + "じゅう"}
    if name == "hyaku":
        return {{1: "ひゃく", 3: "さんびゃく", 6: "ろっぴゃく", 8: "はっぴゃく"}.get(d, STD[d] + "ひゃく")}
    if name == "sen":
        return {{1: "せん", 3: "さんぜん", 8: "はっせん"}.get(d, STD[d] + "せん")}
    return {r + "まん" for r in say(d)}                                       # man


def _join(heads: set[str], tails: set[str]) -> set[str]:
    return {h + t for h in heads for t in tails}


def say(n: int) -> set[str]:
    """All readings of a standalone number (四 よん/し, 七 なな/しち, 九 きゅう/く)."""
    out = {""}
    for name, d in _tokens(n):
        out = _join(out, _token(name, d))
    return out


def _gem(r: str) -> set[str]:
    return {r[: -len(a)] + b for a, b in GEM if r.endswith(a)}


def counted(n: int | None, category: str) -> set[str]:
    """Readings of n + counter (n=None means 何)."""
    lex = LEXICAL.get(category, {})
    if n in lex:
        return set(lex[n])
    if category == "tsu":
        return set()
    kana, cls, forms = COUNTERS[category]
    if n is None:
        head = {"なん"}
        if category in B_ON_THREE:
            return {"なん" + VOICED[kana[0]] + kana[1:]}
        if category in P_ON_THREE_FOUR:
            return {"なん" + HALF[kana[0]] + kana[1:]}
        if category == "kai_floor":
            return {"なんがい", "なんかい"}
        return _join(head, {kana})
    toks = _tokens(n)
    head = {""}
    for name, d in toks[:-1]:
        head = _join(head, _token(name, d))
    name, d = toks[-1]
    plain = _token(name, d, forms) if name == "one" else _token(name, d)
    if name == "one" and d not in forms:
        plain = {STD[d]}                                                      # 4/7/9 before a counter: よん/なな/きゅう
    gem_here = (name in ("juu", "hyaku") or (name == "one" and d in ({1, 8} if cls == "s" else {1, 6, 8}))) \
        and cls in ("k", "s", "h")
    out: set[str] = set()
    for p in plain:
        if cls == "h":
            if gem_here:
                out |= {g + HALF[kana[0]] + kana[1:] for g in _gem(p)}
                if name == "one" and d == 8:
                    out.add(p + kana)                                         # はちほん/はちひき (also heard)
            elif name == "one" and d == 3 and category in B_ON_THREE:
                out.add(p + VOICED[kana[0]] + kana[1:])
            elif name == "one" and d in (3, 4) and category in P_ON_THREE_FOUR:
                out.add(p + HALF[kana[0]] + kana[1:])
            else:
                out.add(p + kana)
        elif gem_here:
            out |= {g + kana for g in _gem(p)}
            if name == "one" and d == 8 and cls == "k":
                out.add(p + kana)                                             # はちかい/はちこ (not はちさつ)
        elif category == "kai_floor" and name == "one" and d == 3:
            out |= {p + "がい", p + "かい"}
        else:
            out.add(p + kana)
    return _join(head, out)


def split(jp: str, category: str) -> tuple[str, int | None] | None:
    """('三', 3) style split of an item: returns (numeral text, n) — n None for 何 — or None if unparsable."""
    suf = SUFFIX.get(category, "")
    if suf and not jp.endswith(suf):
        return None
    num = jp[: len(jp) - len(suf)] if suf else jp
    if num == "何":
        return num, None
    n = parse_number(num)
    return (num, n) if n is not None else None


def expected_readings(jp: str, category: str) -> set[str]:
    if jp in WORDS:
        return set(WORDS[jp])
    if category == "youbi":
        return {YOUBI[jp]} if jp in YOUBI else set()
    if category == "fun" and re.fullmatch(r".+時半", jp):
        h = split(jp[:-1], "ji")
        return {r + "はん" for r in counted(h[1], "ji")} if h else set()
    if category == "tsu" and jp == "十":
        return {"とお"}
    sp = split(jp, category)
    if not sp:
        return set()
    return say(sp[1]) if category == "number" else counted(sp[1], category)


def _plain(n: int) -> set[str]:
    """Number read piece by piece with no sound change (はちひゃく, さんせん): the learner's typical mistake."""
    out = {""}
    for name, d in _tokens(n):
        if name == "one":
            tok = ALT.get(d) or {STD[d]}
        elif name == "man":
            tok = {r + "まん" for r in _plain(d)}
        else:
            tok = {("" if d == 1 else STD[d]) + {"juu": "じゅう", "hyaku": "ひゃく", "sen": "せん"}[name]}
        out = _join(out, tok)
    return out


def naive_readings(jp: str, category: str) -> set[str]:
    """Readings obtained by gluing the plain number to the plain counter (八日 はちにち, 三本 さんほん, 四時 よんじ)."""
    if category == "youbi" or jp in WORDS or jp.endswith("時半"):
        return set()
    kana = "つ" if category == "tsu" else COUNTERS[category][0] if category in COUNTERS else ""
    sp = split(jp, category)
    if not sp:
        return set()
    return {"なん" + kana} if sp[1] is None else _join(_plain(sp[1]), {kana})


if __name__ == "__main__":
    assert naive_readings("八日", "nichi") == {"はちにち"} and "よんじ" in naive_readings("四時", "ji")
    assert naive_readings("八百", "number") == {"はちひゃく"} and naive_readings("何本", "hon") == {"なんほん"}
    cases = {("三本", "hon"): {"さんぼん"}, ("六本", "hon"): {"ろっぽん"}, ("一分", "fun"): {"いっぷん"},
             ("四分", "fun"): {"よんぷん"}, ("三階", "kai_floor"): {"さんがい", "さんかい"}, ("八百", "number"): {"はっぴゃく"},
             ("四時", "ji"): {"よじ"}, ("九月", "gatsu"): {"くがつ"}, ("二十日", "nichi"): {"はつか"},
             ("十本", "hon"): {"じゅっぽん", "じっぽん"}, ("何本", "hon"): {"なんぼん"}, ("一人", "nin"): {"ひとり"}}
    for (jp, cat), want in cases.items():
        assert expected_readings(jp, cat) == want, (jp, expected_readings(jp, cat))
    print("ok")
