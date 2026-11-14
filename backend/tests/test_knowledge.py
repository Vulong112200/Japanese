"""Knowledge base beyond the user's flashcards: vocabulary supplement, N5 kanji, grammar, OCR helpers."""
import io
import json

import pytest

from hub.db import ROOT
from hub.ingestion import knowledge, ocr


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
