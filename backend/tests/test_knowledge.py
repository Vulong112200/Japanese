"""Knowledge base beyond the user's flashcards: vocabulary supplement, N5 kanji, grammar, OCR helpers."""
import io
import json

import pytest

from hub.db import ROOT
from hub.ingestion import knowledge, ocr
from hub.validation import numbers as numrules


# ---------- OCR helpers (no Tesseract needed) ----------
def test_remove_rules_whitens_table_lines():
    import numpy as np
    from PIL import Image
    img = np.full((200, 300), 255, dtype=np.uint8)
    img[100, :] = 0            # horizontal rule
    img[:, 150] = 0            # vertical rule
    img[40:60, 40:60] = 0      # "text" blob must survive
    buf = io.BytesIO()
    Image.fromarray(img).save(buf, format="PNG")
    out = np.array(Image.open(io.BytesIO(ocr.remove_rules(buf.getvalue()))))
    assert out[100, 10] == 255 and out[10, 150] == 255
    assert out[50, 50] == 0


def test_lines_join_japanese_without_spaces():
    words = [{"block_num": "1", "par_num": "1", "line_num": "1", "left": str(x), "top": "10", "height": "20",
              "text": t, "conf": "90"} for x, t in ((0, "日本"), (50, "語"), (100, "Tiếng"), (160, "Nhật"))]
    assert ocr.lines(words)[0]["text"] == "日本語 Tiếng Nhật"


def test_grammar_checker_catches_bad_examples_but_allows_quoted_foreign_words():
    def codes(examples):
        g = {"pattern": "p", "meaning_vi": "m", "formation": "f", "explanation_vi": "e", "data": {"examples": examples}}
        return {c for c, *_ in knowledge.check_grammar(g)}
    ok = [{"jp": "「Thank you」は 日本語で 何ですか。", "hiragana": "「Thank you」は にほんごで なんですか。",
           "romaji": "'Thank you' wa Nihongo de nan desu ka.", "vi": "x"},
          {"jp": "ミラーさんは IMCの 社員です。", "hiragana": "ミラーさんは IMCの しゃいんです。",
           "romaji": "Mirā-san wa IMC no shain desu.", "vi": "x"}]
    assert codes(ok) == set()
    bad = [dict(ok[0]), {"jp": "今 テレビを 見ます。", "hiragana": "いま テレビを みます。", "romaji": "Ima terebi o miru.", "vi": "x"}]
    assert "example_romaji_mismatch" in codes(bad)
    assert "few_examples" in codes(ok[:1])


# ---------- data files ----------
def test_supplement_file_provenance():
    doc = json.loads(knowledge.SUPPLEMENT.read_text(encoding="utf-8"))
    assert doc["origin"] == "AI_GENERATED"
    for e in doc["entries"]:
        assert e["source_id"] in ("SRC_DRIVE_TONG_HOP_TU_VUNG_N5", "SRC_REF_JLPT_N5")
        assert e["raw"] and e["raw_locator"]
        assert e["word"] and e["reading"] and e["meaning_vi"]
        assert e["deck"] == (f"Bai{e['lesson_number']}" if e["lesson_number"] else "N5 bổ sung")


def test_kanji_file_is_the_103_n5_kanji():
    doc = json.loads(knowledge.KANJI.read_text(encoding="utf-8"))
    ks = [k["kanji"] for k in doc["entries"]]
    assert len(ks) == len(set(ks)) == 103
    for k in doc["entries"]:
        assert len(k["example_words"]) >= 2 and all(k["kanji"] in w["word"] for w in k["example_words"])


def test_grammar_covers_checklist():
    checklist = json.loads((ROOT / "data/normalized/grammar/n5_grammar_checklist.json").read_text(encoding="utf-8"))
    doc = json.loads(knowledge.GRAMMAR.read_text(encoding="utf-8"))
    assert {p["id"] for p in checklist["points"]} == {g["id"] for g in doc["entries"]}
    for g in doc["entries"]:
        assert g["origin"] in ("handbook", "handbook+ai", "ai")
        assert len(g["examples"]) >= 2


# ---------- imported database (real data) ----------
def test_supplement_imported_and_audited(imported):
    conn, r = imported
    n = conn.execute("SELECT COUNT(*) FROM vocabulary WHERE source_ids LIKE '%SRC_DRIVE_TONG_HOP%' "
                     "OR source_ids LIKE '%SRC_REF_JLPT_N5%'").fetchone()[0]
    assert n >= 250
    bad = conn.execute("SELECT COUNT(*) FROM vocabulary WHERE archived=0 AND verification_status='verified' "
                       "AND verified_by IS NOT 'ai'").fetchone()[0]
    assert bad == 0
    # Minna lessons 15 and 18 were missing from the user's CSV; they are now covered
    for lesson in (15, 18):
        assert conn.execute("SELECT COUNT(*) FROM vocabulary WHERE lesson_number=? AND archived=0",
                            (lesson,)).fetchone()[0] >= 15
    raw = conn.execute("SELECT extraction_method FROM raw_records WHERE source_id='SRC_DRIVE_TONG_HOP_TU_VUNG_N5' "
                       "LIMIT 1").fetchone()[0]
    assert raw == "ocr_tesseract_table"


def test_jlpt_n5_coverage(imported):
    """Every word of the JLPT N5 reference list is covered (or was deliberately judged a duplicate/skip)."""
    conn, _ = imported
    total = conn.execute("SELECT COUNT(*) FROM vocabulary WHERE archived=0").fetchone()[0]
    assert total >= 1200


def test_kanji_imported_verified(imported):
    conn, r = imported
    assert r["kanji"]["kanji"] == 103
    assert conn.execute("SELECT COUNT(*) FROM kanji WHERE verification_status='verified'").fetchone()[0] == 103


def test_grammar_imported_and_gated_by_audit(imported):
    """Grammar is verified only after its audit round (audited=true in grammar.json) and clean automatic checks."""
    conn, r = imported
    assert r["grammar"]["grammar"] == 135
    doc = json.loads(knowledge.GRAMMAR.read_text(encoding="utf-8"))
    audited = {g["id"] for g in doc["entries"] if g.get("audited")}
    verified = {row[0] for row in conn.execute("SELECT id FROM grammar WHERE verification_status='verified'")}
    assert verified <= audited
    assert conn.execute("SELECT COUNT(*) FROM validation_issues WHERE entity_type='grammar' "
                        "AND severity IN ('error','warning')").fetchone()[0] == 0


def test_user_decision_survives_supplement_reimport(imported, tmp_path):
    conn, _ = imported
    vid = conn.execute("SELECT id FROM vocabulary WHERE source_ids LIKE '%SRC_REF_JLPT_N5%' LIMIT 1").fetchone()[0]
    conn.execute("UPDATE vocabulary SET meaning_vi='bạn sửa', verified_by='user' WHERE id=?", (vid,))
    knowledge.import_supplement(conn)
    assert conn.execute("SELECT meaning_vi FROM vocabulary WHERE id=?", (vid,)).fetchone()[0] == "bạn sửa"
    conn.rollback()


# ---------- kaiwa §7.4 (ADR-023) ----------
KAIWA_VOCAB = {"駅": [{"id": "VOC_1", "word": "駅", "reading": "えき", "meaning_vi": "nhà ga"}],
               "えき": [{"id": "VOC_1", "word": "駅", "reading": "えき", "meaning_vi": "nhà ga"}],
               "行きます": [{"id": "VOC_2", "word": "行きます", "reading": "いきます", "meaning_vi": "đi"}]}


def _kaiwa(**over):
    lines = [{"speaker": "A", "jp": "すみません。駅はどこですか。", "hiragana": "すみません。 えきは どこですか。", "vi": "Xin lỗi, nhà ga ở đâu?"},
             {"speaker": "B", "jp": "あそこです。", "hiragana": "あそこです。", "vi": "Ở đằng kia."},
             {"speaker": "A", "jp": "駅へ行きます。", "hiragana": "えきへ いきます。", "vi": "Tôi đi đến ga."},
             {"speaker": "B", "jp": "はい。", "hiragana": "はい。", "vi": "Vâng."}]
    return {"id": "KAI_999", "topic": "directions", "title_vi": "Hỏi ga", "situation_vi": "Ở phố.", "lines": lines,
            "vocab": ["駅", "行きます"], "grammar_ids": ["GRA_000001"], "origin": "ai", **over}


def test_kaiwa_checker():
    check = lambda k: {c for c, *_ in knowledge.check_kaiwa(k, KAIWA_VOCAB, {"GRA_000001"}, set("駅行"))}
    assert check(_kaiwa()) == set()
    bad = _kaiwa()
    bad["lines"][1] = {**bad["lines"][1], "hiragana": "あそこでした。"}          # kana of the sentence not in reading
    assert "reading_mismatch" in check(bad)
    bad["lines"][1] = {**bad["lines"][1], "hiragana": "あそこ です 1"}            # digit in the reading line
    assert "reading_not_kana" in check(bad)
    assert "vocab_not_verified" in check(_kaiwa(vocab=["銀行"]))
    assert "vocab_not_in_dialogue" in check(_kaiwa(vocab=["駅", "えき", "行きます"], lines=_kaiwa()["lines"][1:2] * 4))
    assert "grammar_not_verified" in check(_kaiwa(grammar_ids=["GRA_000999"]))
    assert "bad_topic" in check(_kaiwa(topic="sports"))
    out = knowledge.check_kaiwa(_kaiwa(lines=[{**l, "jp": l["jp"].replace("駅", "私")} for l in _kaiwa()["lines"]],
                                       vocab=[]), KAIWA_VOCAB, {"GRA_000001"}, set("駅行"))
    assert ("kanji_outside_n5", "info") in {(c, s) for c, s, *_ in out}


def test_kaiwa_file_covers_9_topics():
    doc = json.loads(knowledge.KAIWA.read_text(encoding="utf-8"))
    live = [k for k in doc["entries"] if not k.get("excluded")]
    assert {k["topic"] for k in live} == set(knowledge.KAIWA_TOPICS)
    assert all(sum(k["topic"] == t for k in live) >= 2 for t in knowledge.KAIWA_TOPICS)
    assert len({k["id"] for k in doc["entries"]}) == len(doc["entries"])


def test_kaiwa_imported_verified_and_not_exam_content(imported):
    conn, r = imported
    doc = json.loads(knowledge.KAIWA.read_text(encoding="utf-8"))
    live = [k for k in doc["entries"] if not k.get("excluded")]
    assert r["kaiwa"]["kaiwa"] == len(live) and r["kaiwa"]["verified"] == len(live)
    assert conn.execute("SELECT COUNT(*) FROM validation_issues WHERE entity_type='kaiwa' "
                        "AND severity IN ('error','warning')").fetchone()[0] == 0
    row = json.loads(conn.execute("SELECT data_json FROM kaiwa WHERE id=?", (live[0]["id"],)).fetchone()[0])
    assert row["vocab"] and all(v["id"].startswith("VOC_") for v in row["vocab"]) and row["grammar"]
    assert conn.execute("SELECT COUNT(*) FROM questions WHERE question_id LIKE 'KAI%' OR exam_id LIKE '%KAIWA%'").fetchone()[0] == 0


# ---------- numbers / counters / dates (ADR-029)


def test_number_reading_rules():
    e = numrules.expected_readings
    cases = {("三本", "hon"): {"さんぼん"}, ("六本", "hon"): {"ろっぽん"}, ("一分", "fun"): {"いっぷん"},
             ("四分", "fun"): {"よんぷん"}, ("三階", "kai_floor"): {"さんがい", "さんかい"}, ("八百", "number"): {"はっぴゃく"},
             ("三千", "number"): {"さんぜん"}, ("四時", "ji"): {"よじ"}, ("九時", "ji"): {"くじ"}, ("四月", "gatsu"): {"しがつ"},
             ("八日", "nichi"): {"ようか"}, ("二十日", "nichi"): {"はつか"}, ("一人", "nin"): {"ひとり"}, ("四人", "nin"): {"よにん"},
             ("二十歳", "sai"): {"はたち", "にじゅっさい", "にじっさい"}, ("十", "tsu"): {"とお"}, ("六冊", "satsu"): {"ろくさつ"},
             ("八冊", "satsu"): {"はっさつ"}, ("何階", "kai_floor"): {"なんがい", "なんかい"}, ("四円", "en"): {"よえん"},
             ("三百円", "en"): {"さんびゃくえん"}, ("土曜日", "youbi"): {"どようび"}, ("四時半", "fun"): {"よじはん"}}
    for (jp, cat), want in cases.items():
        assert e(jp, cat) == want, jp
    for jp, cat, wrong in (("三本", "hon", "さんほん"), ("一分", "fun", "いちふん"), ("四時", "ji", "よんじ"),
                           ("九月", "gatsu", "きゅうがつ"), ("八日", "nichi", "はちにち"), ("八冊", "satsu", "はちさつ")):
        assert wrong not in e(jp, cat) and wrong in numrules.naive_readings(jp, cat)
    assert e("三本", "satsu") == set() and numrules.parse_number("二十四") == 24


def test_number_item_checker():
    ok = {"id": "NUM_hon_三本", "jp": "三本", "reading": "さんぼん", "vi": "3 cây", "irregular": True,
          "note_vi": "ほん → ぼん", "example_jp": "えんぴつが 三本 あります。", "example_vi": "Có 3 cây bút chì."}
    codes = lambda it: {c for c, *_ in knowledge.check_number_item(it, "hon", set("三本"))}
    assert codes(ok) == set()
    assert "reading_rule_mismatch" in codes({**ok, "reading": "さんほん"})
    assert "reading_rule_mismatch" in codes({**ok, "alt_readings": ["さんぽん"]})
    assert "missing_note" in codes({**ok, "note_vi": None})
    assert "example_missing_word" in codes({**ok, "example_jp": "えんぴつが あります。"})
    assert "reading_not_kana" in codes({**ok, "reading": "sanbon"})


def test_number_questions_distractors(imported):
    conn, result = imported
    assert result["numbers"]["verified"] == result["numbers"]["numbers"] > 250
    rows = conn.execute("SELECT q.*, n.category, n.jp FROM questions q JOIN numbers n "
                        "ON n.id=json_extract(q.extra_json,'$.target_entity') "
                        "WHERE q.exam_id='BANK_N5_NUMBERS' AND q.verification_status='verified'").fetchall()
    assert len(rows) >= 100
    for q in rows:
        item = conn.execute("SELECT * FROM numbers WHERE jp=? AND category=?", (q["jp"], q["category"])).fetchone()
        valid = knowledge.number_valid_readings(q["jp"], q["category"], {"reading": item["reading"],
                                                **json.loads(item["data_json"])})
        opts = {o["option_id"]: o["text"] for o in json.loads(q["options"])}
        ans = json.loads(q["correct_answer"])[0]
        assert len(opts) == 4 and len(set(opts.values())) == 4
        assert opts[ans] == item["reading"] and opts[ans] in numrules.expected_readings(q["jp"], q["category"])
        assert not ({t for k, t in opts.items() if k != ans} & valid), q["question_id"]
        assert q["jp"] in q["question_text"]


def test_number_srs_cards_only_for_memorised_forms(imported):
    conn, _ = imported
    n = conn.execute("SELECT COUNT(*) FROM srs_cards WHERE entity_type='number'").fetchone()[0]
    assert n == conn.execute("SELECT COUNT(*) FROM numbers WHERE irregular=1 AND verification_status!='rejected'").fetchone()[0] > 100
