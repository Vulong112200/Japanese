"""Import of the curated knowledge base beyond the user's flashcards:
  - vocabulary supplement (missing Minna words recovered by OCR + missing JLPT N5 words)
  - grammar (handbook docx/Google Doc, corrected and completed against the N5 checklist)
  - N5 kanji (103 kanji of the old level-4 list, KANJIDIC2 + Basic Kanji 120 as witnesses)
All files live in data/normalized/. Every record keeps its sources; automatic checks decide whether it can be
verified (verified_by='ai'); anything a person edited or decided is left alone.
"""
import json
import re
from pathlib import Path

from .. import repo
from ..db import ROOT
from ..validation import reference as ref
from ..validation.kana import KANA_RE, kata_to_hira, romaji_matches

NORM = ROOT / "data" / "normalized"
SUPPLEMENT = NORM / "supplements" / "vocabulary_supplement.json"
GRAMMAR = NORM / "grammar" / "grammar.json"
KANJI = NORM / "kanji" / "kanji_n5.json"
JLPT_LIST = ROOT / "data" / "reference" / "jlpt_n5_words.csv"
USER_OWNED = ("user", "pending_user")

REF_SOURCES = [
    {"source_id": "SRC_REF_JLPT_N5", "source_type": "csv", "name": "JLPT N5 word list (tanos.co.uk via elzup/jlpt-word-list)",
     "url": "https://github.com/elzup/jlpt-word-list", "location": "data/reference/jlpt_n5_words.csv",
     "reliability": "EDUCATIONAL", "purpose": "Danh sách đo độ phủ từ vựng N5 (dựa trên danh sách JLPT cũ, CC BY)"},
    {"source_id": "SRC_REF_JMDICT", "source_type": "dictionary", "name": "JMdict (EDRDG)",
     "url": "https://www.edrdg.org/jmdict/j_jmdict.html", "location": "data/reference/JMdict_e.gz",
     "reliability": "EDUCATIONAL", "purpose": "Đối chiếu cách đọc, từ loại, nhóm động từ (CC BY-SA 4.0)"},
    {"source_id": "SRC_REF_KANJIDIC2", "source_type": "dictionary", "name": "KANJIDIC2 (EDRDG)",
     "url": "https://www.edrdg.org/wiki/index.php/KANJIDIC_Project", "location": "data/reference/kanjidic2.xml.gz",
     "reliability": "EDUCATIONAL", "purpose": "Âm on/kun, số nét, Hán-Việt, danh sách kanji N5 (CC BY-SA 4.0)"},
]


def register_reference_sources(conn) -> None:
    for s in REF_SOURCES:
        existing = repo.get_source(conn, s["source_id"])
        repo.upsert_source(conn, {**s, "level": "N5", "access_status": "local",
                                  "processing_status": existing["processing_status"] if existing else "verified"})


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


# ------------------------------------------------------------------ vocabulary supplement
def import_supplement(conn, path: Path = SUPPLEMENT) -> dict:
    """Entries: {key, origin, source_id, raw: {...}, raw_locator, word, reading, romaji, han_viet, meaning_vi,
    part_of_speech, lesson_number, deck, example_jp, example_romaji, example_vi, audited}"""
    data = _load(path)
    if not data:
        return {"added": 0}
    register_reference_sources(conn)
    stats = {"added": 0, "existing": 0, "updated": 0, "excluded": 0}
    fields = ("word", "reading", "romaji", "han_viet", "meaning_vi", "part_of_speech", "lesson_number", "deck",
              "example_jp", "example_romaji", "example_vi")
    for e in data["entries"]:
        raw_content = json.dumps(e["raw"], ensure_ascii=False)
        method = "ocr_tesseract_table" if e["origin"] == "minna_ocr" else "csv_row"
        raw_id = repo.insert_raw(conn, e["source_id"], e["raw_locator"], raw_content, method)
        row = conn.execute("SELECT * FROM vocabulary WHERE raw_ids = ?", (f"[{raw_id}]",)).fetchone()
        if row is None and not e.get("excluded") and not e.get("separate_sense"):
            dup = conn.execute("SELECT id FROM vocabulary WHERE word=? AND reading=?", (e["word"], e["reading"])).fetchone()
            if dup:                                    # same word already present (e.g. from the user's CSV)
                stats["existing"] += 1
                continue
        if row is not None:
            if row["verified_by"] in USER_OWNED:
                stats["existing"] += 1
                continue
            if e.get("excluded"):                      # removed after review: archive, never delete
                if not row["archived"]:
                    repo.update_vocab(conn, row["id"], archived=1)
                    repo.log_action(conn, "vocabulary", row["id"], "supplement_exclude", e.get("exclude_reason"), None, None)
                stats["excluded"] += 1
                continue
            # part_of_speech of existing rows is owned by the JMdict enrichment (revalidate), not by this file
            new = {f: (e.get(f) or None) if f != "lesson_number" else e.get(f) for f in fields if f != "part_of_speech"}
            changed = {f: v for f, v in new.items() if (row[f] or None) != v}
            if changed:                                # the supplement file is the source of truth for these rows
                repo.update_vocab(conn, row["id"], **changed)
                reasons = {r["field"]: r["reason_vi"] for r in e.get("review_log", [])}
                for f, v in changed.items():           # one log line per field (same shape as CSV corrections)
                    repo.log_action(conn, "vocabulary", row["id"], "ai_correction",
                                    reasons.get(f, "Cập nhật theo vòng rà soát"), {f: row[f]}, {f: v})
                stats["updated"] += 1
            else:
                stats["existing"] += 1
            continue
        if e.get("excluded"):
            stats["excluded"] += 1
            continue
        vid = repo.next_vocab_id(conn)
        conn.execute(
            "INSERT INTO vocabulary (id, word, reading, romaji, han_viet, meaning_vi, part_of_speech, lesson_number, "
            "deck, topic, example_jp, example_romaji, example_vi, source_ids, raw_ids, updated_at) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (vid, e["word"], e["reading"], e.get("romaji"), e.get("han_viet") or None, e["meaning_vi"],
             e.get("part_of_speech"), e.get("lesson_number"), e["deck"], json.dumps(e.get("topic", []), ensure_ascii=False),
             e.get("example_jp"), e.get("example_romaji"), e.get("example_vi"),
             json.dumps([e["source_id"]]), json.dumps([raw_id]), repo.iso()))
        repo.log_action(conn, "vocabulary", vid, "supplement_add", e.get("reason_vi"), None,
                        {"origin": e["origin"], "basis": e.get("basis")})
        stats["added"] += 1
    return stats


def supplement_audited(conn, path: Path = SUPPLEMENT) -> dict[str, str]:
    """{vocab_id: raw_word} for audited supplement entries (same contract as corrections audit.items)."""
    data = _load(path)
    out = {}
    for e in (data or {}).get("entries", []):
        if not e.get("audited") or e.get("excluded"):
            continue
        raw = conn.execute("SELECT raw_id FROM raw_records WHERE source_id=? AND locator=?",
                           (e["source_id"], e["raw_locator"])).fetchone()
        r = raw and conn.execute("SELECT id FROM vocabulary WHERE raw_ids=?", (f"[{raw[0]}]",)).fetchone()
        if r:                                          # matched through its own RAW row, never by spelling
            out[r[0]] = str(e["raw"].get("word") if isinstance(e["raw"], dict) else e["raw"][0])
    return out


# ------------------------------------------------------------------ grammar
def check_grammar(g: dict) -> list:
    issues = []
    d = g["data"]
    for f in ("pattern", "meaning_vi", "formation", "explanation_vi"):
        if not (g.get(f) or "").strip():
            issues.append(("missing_field", "error", f"Thiếu {f}", None))
    if len(d.get("examples", [])) < 2:
        issues.append(("few_examples", "warning", "Cần ít nhất 2 ví dụ", None))
    for i, ex in enumerate(d.get("examples", []), 1):
        if not all(ex.get(k) for k in ("jp", "vi")):
            issues.append(("example_incomplete", "error", f"Ví dụ {i} thiếu câu Nhật hoặc câu dịch", None))
        # quoted foreign words (「Thank you」) and acronyms (IMC, CD) are legitimate in Japanese sentences
        allowed_latin = r"「[^」]*[A-Za-zÀ-ỹ][^」]*」|『[^』]*』|(?<![A-Za-z])[A-Z]{2,5}(?![A-Za-z])"
        hira = re.sub(allowed_latin + r"|[。、！？!?「」『』（）()・…\s　.]", "", ex.get("hiragana") or "")
        if hira and not KANA_RE.match(hira):
            issues.append(("example_reading_not_kana", "warning", f"Ví dụ {i}: phần đọc có ký tự không phải kana", None))
        elif hira and ex.get("romaji"):
            # compare kana and romaji with the same foreign words (IMC, Thank you, pencil) removed from both sides
            foreign = re.findall(r"[A-Za-zÀ-ỹ]+", ex.get("hiragana") or "")
            kana_side = re.sub(r"[A-Za-zÀ-ỹ]+|[。、！？!?「」『』（）()・…\s　.]", "", ex.get("hiragana") or "")
            ro = ex["romaji"]
            for w in foreign:
                ro = re.sub(rf"(?i)\b{re.escape(w)}\b", " ", ro)
            if not romaji_matches(kana_side, ro):
                issues.append(("example_romaji_mismatch", "warning", f"Ví dụ {i}: romaji không khớp phần đọc", None))
        if re.search(r"[A-Za-zÀ-ỹ]{3,}", re.sub(allowed_latin, "", ex.get("jp") or "")):
            issues.append(("example_mixed_script", "warning", f"Ví dụ {i}: câu tiếng Nhật lẫn chữ Latin", None))
    return issues


def import_grammar(conn, path: Path = GRAMMAR) -> dict:
    data = _load(path)
    if not data:
        return {"grammar": 0}
    stats = {"grammar": 0, "verified": 0}
    keep = ("usage", "restrictions", "formality", "similar_patterns", "common_mistakes", "examples",
            "handbook_refs", "handbook_errors", "level_note", "review_log")
    for g in data["entries"]:
        cur = conn.execute("SELECT verified_by, verification_status FROM grammar WHERE id=?", (g["id"],)).fetchone()
        if cur and cur["verified_by"] in USER_OWNED:
            continue
        rec = {"data": {k: g.get(k) for k in keep}, **g}
        issues = check_grammar(rec)
        repo.replace_issues(conn, "grammar", g["id"], issues)
        blocking = any(sev in ("error", "warning") for _, sev, _, _ in issues)
        status, by = ("verified", "ai") if g.get("audited") and not blocking else ("needs_review", None)
        sources = (["SRC_LOCAL_GRAMMAR_DOCX", "SRC_GDOC_001"] if g["origin"] in ("handbook", "handbook+ai") else [])
        conn.execute(
            "INSERT OR REPLACE INTO grammar (id, pattern, lesson_number, grammar_name_vi, meaning_vi, formation, "
            "explanation_vi, data_json, origin, level, source_ids, verification_status, verified_by) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (g["id"], g["pattern"], g.get("lesson_number"), g.get("grammar_name_vi"), g["meaning_vi"], g["formation"],
             g.get("explanation_vi"), json.dumps(rec["data"], ensure_ascii=False), g["origin"], "N5",
             json.dumps(sources), status, by))
        stats["grammar"] += 1
        stats["verified"] += status == "verified"
    return stats


# ------------------------------------------------------------------ kanji
def check_kanji(k: dict) -> list:
    issues = []
    if not ref.available():
        return issues
    row = ref._db().execute("SELECT onyomi, kunyomi, strokes FROM kd WHERE kanji=?", (k["kanji"],)).fetchone()
    if not row:
        return [("kanji_not_in_kanjidic", "error", "Không có trong KANJIDIC2", None)]
    on, kun = set(json.loads(row[0])), set(json.loads(row[1]))
    bad_on = [o for o in k["onyomi"] if o not in on]
    bad_kun = [x for x in k["kunyomi"] if x not in kun]
    if bad_on or bad_kun:
        issues.append(("kanji_reading_not_in_kanjidic", "warning", f"Âm không có trong KANJIDIC2: {bad_on + bad_kun}", None))
    if row[2] and k.get("stroke_count") != row[2]:
        issues.append(("stroke_count_mismatch", "warning", f"Số nét {k.get('stroke_count')} ≠ KANJIDIC2 {row[2]}", None))
    allowed = {ref.hv_key(x) for x in ref.kanji_han_viet(k["kanji"])}
    for hv in re.split(r"[,/、]\s*", k.get("han_viet") or ""):
        if hv and ref.hv_key(hv) not in allowed:
            issues.append(("han_viet_not_in_reference", "warning", f"Hán-Việt '{hv}' không có trong KANJIDIC2/HV_OVERRIDES", None))
    if len(k.get("example_words", [])) < 2:
        issues.append(("few_examples", "warning", "Cần ít nhất 2 từ ví dụ", None))
    for ex in k.get("example_words", []):
        if k["kanji"] not in ex["word"]:
            issues.append(("example_without_kanji", "error", f"Từ ví dụ {ex['word']} không chứa {k['kanji']}", None))
        res = ref.check_reading(ex["word"], ex["reading"])
        if res["status"] == "mismatch":
            issues.append(("example_reading_mismatch", "warning",
                           f"{ex['word']} đọc là {'/'.join(res['expected'][:3])}, ghi {ex['reading']}", None))
    return issues


def import_kanji(conn, path: Path = KANJI) -> dict:
    data = _load(path)
    if not data:
        return {"kanji": 0}
    register_reference_sources(conn)
    stats = {"kanji": 0, "verified": 0}
    for i, k in enumerate(data["entries"], 1):
        kid = f"KAN_{i:06d}"
        cur = conn.execute("SELECT verified_by FROM kanji WHERE id=?", (kid,)).fetchone()
        if cur and cur["verified_by"] in USER_OWNED:
            continue
        issues = check_kanji(k)
        repo.replace_issues(conn, "kanji", kid, issues)
        blocking = any(sev in ("error", "warning") for _, sev, _, _ in issues)
        status, by = ("verified", "ai") if k.get("audited") and not blocking else ("needs_review", None)
        conn.execute(
            "INSERT OR REPLACE INTO kanji (id, kanji, han_viet, meaning_vi, onyomi, kunyomi, stroke_count, example_words, "
            "level, source_ids, verification_status, verified_by) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (kid, k["kanji"], k["han_viet"], k["meaning_vi"], json.dumps(k["onyomi"], ensure_ascii=False),
             json.dumps(k["kunyomi"], ensure_ascii=False), k.get("stroke_count"),
             json.dumps(k["example_words"], ensure_ascii=False), "N5",
             json.dumps(["SRC_REF_KANJIDIC2", "SRC_DRIVE_120_KANJI_CO_BAN_SO_CAP"]), status, by))
        stats["kanji"] += 1
        stats["verified"] += status == "verified"
    return stats


def kata_norm(s: str) -> str:
    return kata_to_hira(re.sub(r"\s", "", s or ""))


# ------------------------------------------------------------------ generated questions (spec §11.5)
GEN_EXAM = "BANK_N5_GENERATED"
GEN_INSTRUCTION = {1: "＿＿＿の ことばは どう よみますか。1・2・3・4から いちばん いい ものを ひとつ えらんで ください。",
                   2: "＿＿＿の ことばは どう かきますか。1・2・3・4から いちばん いい ものを ひとつ えらんで ください。"}


def valid_readings(word: str) -> set[str]:
    return {kata_to_hira(r) for r, _, _ in ref.lookup(word)} | {c[1] for c in ref.masu_candidates(word)}


def is_word(text: str) -> bool:
    return bool(ref.lookup(text) or ref.masu_candidates(text))


def import_generated_questions(conn) -> dict:
    """Rebuild the rule-based question bank from verified vocabulary and verified N5 kanji. Stable ids; questions that
    can no longer be generated become 'rejected' (attempt history may reference them), never deleted."""
    from ..learning import question_gen
    if not ref.available():
        return {"generated": 0, "note": "reference dictionary missing (run build-reference)"}
    vocab = repo.rows(conn.execute("SELECT id, word, reading, meaning_vi, lesson_number, example_jp FROM vocabulary "
                                   "WHERE verification_status='verified' AND archived=0"))
    kanji = repo.rows(conn.execute("SELECT kanji, han_viet, onyomi, kunyomi FROM kanji WHERE verification_status='verified'"))
    pool = {k["kanji"]: question_gen.kanji_reading_set(json.loads(k["onyomi"]), json.loads(k["kunyomi"])) for k in kanji}
    db, cache = ref._db(), {}

    def readings_of(ch: str) -> set[str]:          # KANJIDIC2 readings of any kanji (N5 or not)
        if ch not in cache:
            row = db.execute("SELECT onyomi, kunyomi FROM kd WHERE kanji=?", (ch,)).fetchone()
            cache[ch] = question_gen.kanji_reading_set(json.loads(row[0]), json.loads(row[1])) if row else set()
        return cache[ch]
    qs = question_gen.make_questions(vocab, valid_readings, readings_of, pool, is_word,
                                     {k["kanji"]: k["han_viet"] for k in kanji})
    conn.execute("INSERT OR REPLACE INTO exams (exam_id, title, level, exam_type, source_type, is_official, "
                 "duration_minutes, data_json, source_ids, verification_status) VALUES (?,?,?,?,?,?,?,?,?,?)",
                 (GEN_EXAM, "Ngân hàng câu luyện tập sinh tự động (AI_GENERATED)", "N5", "question_bank",
                  "AI_GENERATED", 0, None, json.dumps({"generator": "hub.learning.question_gen", "note":
                  "Sinh bằng luật từ từ vựng/kanji đã verified; không phải câu hỏi JLPT chính thức."}, ensure_ascii=False),
                  json.dumps(["SRC_REF_JMDICT", "SRC_REF_KANJIDIC2"]), "verified"))
    for q in qs:
        extra = {k: q[k] for k in ("target", "target_entity", "option_explanations", "lesson_number")}
        extra["generator"] = "rule:" + q["mondai_type"]
        conn.execute(
            "INSERT OR REPLACE INTO questions (question_id, exam_id, section, section_id, mondai_no, mondai_type, number, "
            "question_text, instruction, options, correct_answer, answer_type, extra_json, explanation_vi, "
            "explanation_origin, level, source_ids, extraction_method, verification_status, verified_by) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (q["question_id"], GEN_EXAM, q["section"], q["section_id"], q["mondai_no"], q["mondai_type"], None,
             q["question_text"], GEN_INSTRUCTION[q["mondai_no"]], json.dumps(q["options"], ensure_ascii=False),
             json.dumps(q["correct_answer"]), "single_choice", json.dumps(extra, ensure_ascii=False),
             q["explanation_vi"], "AI_GENERATED", "N5", json.dumps(["SRC_REF_JMDICT", "SRC_REF_KANJIDIC2"]),
             "rule_generated", "verified", "generator"))
    ids = [q["question_id"] for q in qs]
    conn.execute(f"UPDATE questions SET verification_status='rejected' WHERE exam_id=? "
                 f"AND question_id NOT IN ({','.join('?' * len(ids))})", [GEN_EXAM, *ids])
    return {"generated": len(qs), "kanji_reading": sum(q["mondai_no"] == 1 for q in qs),
            "orthography": sum(q["mondai_no"] == 2 for q in qs)}


# ------------------------------------------------------------------ agent-authored grammar questions (ADR-020)
GRAMMAR_Q = NORM / "grammar_questions" / "grammar_questions.json"
GRAMMAR_Q_REVIEW = NORM / "ai_review" / "grammar_questions_review.json"
GQ_EXAM = "BANK_N5_GRAMMAR_AI"
GQ_MONDAI = {   # instructions as on the real N5 paper
    "grammar_form": (1, "（　　）に 何を 入れますか。1・2・3・4から いちばん いい ものを 一つ えらんで ください。"),
    "sentence_composition": (2, "＿★＿に 入る ものは どれですか。1・2・3・4から いちばん いい ものを 一つ えらんで ください。"),
}
_NOT_JP = re.compile(r"[\s　＿★（）()。、「」A-Za-z:：]")


def jp_key(text: str) -> str:
    """Text without spaces, blanks and punctuation: for duplicate detection against past papers."""
    return _NOT_JP.sub("", text or "")


def check_grammar_question(q: dict, verified_grammar: set[str], n5_kanji: set[str], past_keys: set[str]) -> list:
    """Rule checks for one authored grammar question -> [(code, severity, message, suggestion)]."""
    issues = []
    err = lambda code, msg: issues.append((code, "error", msg, None))
    opts, text, ans = q.get("options") or [], q.get("question_text") or "", q.get("answer")
    if q.get("mondai_type") not in GQ_MONDAI:
        err("bad_mondai_type", f"mondai_type không hợp lệ: {q.get('mondai_type')}")
    if len(opts) != 4 or len(set(opts)) != 4 or not all(o.strip() for o in opts):
        err("bad_options", "Cần đúng 4 lựa chọn khác nhau, không rỗng")
    if ans not in (1, 2, 3, 4):
        err("bad_answer", f"Đáp án phải là 1–4, đang là {ans}")
    if q.get("grammar_id") not in verified_grammar:
        err("grammar_not_verified", f"Điểm ngữ pháp {q.get('grammar_id')} không tồn tại hoặc chưa verified")
    if set(q.get("option_explanations") or {}) != {"1", "2", "3", "4"}:
        err("missing_option_explanations", "Cần giải thích cho cả 4 lựa chọn")
    if not (q.get("explanation_vi") or "").strip():
        err("missing_explanation", "Thiếu giải thích")
    if q.get("mondai_type") == "grammar_form" and text.count("（　　）") != 1:
        err("blank_count", "文の文法1 cần đúng 1 chỗ trống （　　）")
    if q.get("mondai_type") == "sentence_composition":
        star, seq = q.get("star_position"), q.get("expected_sequence")
        if text.count("★") != 1 or text.count("＿＿") != 3:
            err("slot_count", "文の文法2 cần đúng 4 ô: 3 ô ＿＿ và 1 ô ★")
        elif star != text.split("★")[0].count("＿＿") + 1:
            err("star_position_mismatch", f"star_position {star} không khớp vị trí ★ trong câu")
        if sorted(seq or []) != [1, 2, 3, 4]:
            err("bad_sequence", "expected_sequence phải là hoán vị của 1–4")
        elif star in (1, 2, 3, 4) and seq[star - 1] != ans:
            err("star_answer_mismatch", f"Đáp án {ans} ≠ lựa chọn ở ô ★ ({seq[star - 1]})")
    outside = sorted({c for c in text + "".join(opts) if re.match(r"[一-鿿]", c)} - n5_kanji)
    if outside:
        issues.append(("kanji_outside_n5", "warning", f"Kanji ngoài N5: {''.join(outside)} (nên viết kana)", None))
    if jp_key(text) in past_keys:
        err("copied_from_past_exam", "Trùng câu trong đề thi thật")
    return issues


def import_grammar_questions(conn, path: Path = GRAMMAR_Q, review_path: Path = GRAMMAR_Q_REVIEW) -> dict:
    """Agent-authored 文の文法1/2 practice questions (ADR-020). Verified only when the rules pass and two independent
    blind AI solvers both pick the authored answer; anything else stays needs_review. Questions that are excluded or
    gone become 'rejected' (attempt history may reference them), never deleted. A person's decision is kept."""
    from ..learning import exam as examlib
    data = _load(path)
    if not data:
        return {"grammar_questions": 0}
    review = _load(review_path) or {}
    grammar = {r[0]: r[1] for r in conn.execute("SELECT id, pattern FROM grammar WHERE verification_status='verified'")}
    n5_kanji = {r[0] for r in conn.execute("SELECT kanji FROM kanji WHERE verification_status='verified'")}
    past_keys = {jp_key(r[0]) for r in conn.execute(
        "SELECT q.question_text FROM questions q JOIN exams e USING (exam_id) WHERE e.exam_type!='question_bank' "
        "AND q.question_text IS NOT NULL")}
    conn.execute("INSERT OR REPLACE INTO exams (exam_id, title, level, exam_type, source_type, is_official, "
                 "duration_minutes, data_json, source_ids, verification_status) VALUES (?,?,?,?,?,?,?,?,?,?)",
                 (GQ_EXAM, "Ngân hàng câu ngữ pháp do AI soạn (AI_GENERATED)", "N5", "question_bank", "AI_GENERATED", 0,
                  None, json.dumps({"note": "Câu 文の文法1/2 do agent soạn từ các điểm ngữ pháp đã verified; 2 AI giải "
                                    "mù độc lập (ADR-020). Không phải câu hỏi JLPT chính thức."}, ensure_ascii=False),
                  json.dumps(["SRC_LOCAL_GRAMMAR_DOCX"]), "verified"))
    stats, live = {"grammar_questions": 0, "verified": 0, "needs_review": 0}, []
    for q in data["entries"]:
        if q.get("excluded"):
            continue
        qid = q["question_id"]
        live.append(qid)
        mondai_no, instruction = GQ_MONDAI.get(q["mondai_type"], (None, None))
        issues = check_grammar_question(q, set(grammar), n5_kanji, past_keys)
        repo.replace_issues(conn, "question", qid, issues)
        r = review.get(qid, {})
        agreed = examlib.consensus_status(q["answer"], [r.get("solver_a"), r.get("solver_b")]) == "verified"
        doubt = [] if agreed or not r else [("ai_solver_disagrees", "warning", f"Đáp án {q['answer']}; AI giải mù: "
                                             f"{r.get('solver_a')} / {r.get('solver_b')}. {r.get('note') or ''}".strip(), None)]
        repo.replace_issues(conn, "question", qid, doubt, origin="ai_review")
        blocking = any(sev in ("error", "warning") for _, sev, _, _ in issues)
        status, by = ("verified", "ai") if q.get("audited") and agreed and not blocking else ("needs_review", None)
        cur = conn.execute("SELECT verification_status, verified_by FROM questions WHERE question_id=?", (qid,)).fetchone()
        if cur and cur["verified_by"] in USER_OWNED:
            status, by = cur["verification_status"], cur["verified_by"]
        extra = {"grammar_id": q["grammar_id"], "grammar_pattern": grammar.get(q["grammar_id"]),
                 "option_explanations": q.get("option_explanations"), "generator": "agent:" + q["mondai_type"]}
        if q["mondai_type"] == "sentence_composition":
            extra.update(star_position=q.get("star_position"), expected_sequence=q.get("expected_sequence"))
        conn.execute(
            "INSERT OR REPLACE INTO questions (question_id, exam_id, section, section_id, mondai_no, mondai_type, number, "
            "question_text, instruction, options, correct_answer, answer_type, extra_json, explanation_vi, "
            "explanation_origin, level, source_ids, extraction_method, verification_status, verified_by, review_notes) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (qid, GQ_EXAM, "grammar_reading", "SEC_02", mondai_no, q["mondai_type"], None, q["question_text"],
             instruction, json.dumps([{"option_id": str(i), "text": t} for i, t in enumerate(q["options"], 1)],
                                     ensure_ascii=False),
             json.dumps([str(q["answer"])]),
             "sentence_ordering" if q["mondai_type"] == "sentence_composition" else "single_choice",
             json.dumps(extra, ensure_ascii=False), q.get("explanation_vi"), "AI_GENERATED", "N5",
             json.dumps(["SRC_LOCAL_GRAMMAR_DOCX"]), "agent_authored", status, by,
             json.dumps(q["review_log"], ensure_ascii=False) if q.get("review_log") else None))
        if status == "verified":
            conn.execute("UPDATE validation_issues SET resolved=1 WHERE entity_type='question' AND entity_id=?", (qid,))
        stats["grammar_questions"] += 1
        stats["verified" if status == "verified" else "needs_review"] += 1
    conn.execute(f"UPDATE questions SET verification_status='rejected' WHERE exam_id=? AND verified_by IS NOT 'user' "
                 f"AND question_id NOT IN ({','.join('?' * len(live)) or 'NULL'})", [GQ_EXAM, *live])
    return stats
