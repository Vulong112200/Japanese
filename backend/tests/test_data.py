"""Data-quality tests on the REAL local data (docs/N5/**), imported into a temp DB."""
import json
from pathlib import Path

import jsonschema
import pytest

from hub.db import ROOT
from hub.ingestion import pipeline

SCHEMAS = ROOT / "schemas"


def schema(name):
    return json.loads((SCHEMAS / f"{name}.schema.json").read_text(encoding="utf-8"))


def test_import_counts(imported):
    _, r = imported
    fc = r["flashcards"]
    assert fc["files"] == 26 and fc["rows"] == 991
    assert fc["vocabulary_new"] + fc["merged"] + fc["unstructured"] == 991
    assert fc["unstructured"] == 16                       # Số Đếm Q&A deck stays RAW
    assert r["exam"]["questions"] == 29


def test_reimport_is_idempotent(imported):
    conn, _ = imported
    before = conn.execute("SELECT COUNT(*) FROM vocabulary").fetchone()[0]
    raw_before = conn.execute("SELECT COUNT(*) FROM raw_records").fetchone()[0]
    again = pipeline.import_flashcards(conn)
    assert again["vocabulary_new"] == 0
    assert conn.execute("SELECT COUNT(*) FROM vocabulary").fetchone()[0] == before
    assert conn.execute("SELECT COUNT(*) FROM raw_records").fetchone()[0] == raw_before


def test_every_raw_row_preserved(imported):
    conn, _ = imported
    n = conn.execute("SELECT COUNT(*) FROM raw_records WHERE extraction_method='csv_row'").fetchone()[0]
    assert n == 991


def test_verification_provenance(imported):
    """Vocabulary may be verified only by the audited pipeline (verified_by='ai'); exam questions stay
    needs_review until a person checks them against the page images."""
    conn, _ = imported
    by = dict(conn.execute("SELECT COALESCE(verified_by,'-'), COUNT(*) FROM vocabulary "
                           "WHERE verification_status='verified' GROUP BY 1").fetchall())
    assert set(by) <= {"ai"}
    assert conn.execute("SELECT COUNT(*) FROM questions WHERE verification_status='verified'").fetchone()[0] == 0


def test_vocabulary_schema_and_traceability(imported):
    conn, _ = imported
    sch = schema("vocabulary")
    for r in conn.execute("SELECT * FROM vocabulary"):
        d = dict(r)
        for k in ("topic", "source_ids", "raw_ids"):
            d[k] = json.loads(d[k])
        jsonschema.validate(d, sch)
        for sid in d["source_ids"]:
            assert conn.execute("SELECT 1 FROM sources WHERE source_id=?", (sid,)).fetchone(), sid
        assert conn.execute(f"SELECT COUNT(*) FROM raw_records WHERE raw_id IN ({','.join('?' * len(d['raw_ids']))})",
                            d["raw_ids"]).fetchone()[0] == len(d["raw_ids"])


def test_sources_schema(imported):
    conn, _ = imported
    sch = schema("source")
    for r in conn.execute("SELECT * FROM sources"):
        jsonschema.validate({k: v for k, v in dict(r).items() if v is not None or k == "access_status"}, sch)


KNOWN_FIXES = {   # word -> (field, wrong value in the user's CSV, corrected value)
    "お腹が空きました": ("reading", "おなかがあきました", "おなかがすきました"),
    "昼休み": ("han_viet", "TRƯA HƯU", "TRÚ HƯU"),
    "クラシック": ("reading", "くらしく", "くらしっく"),
    "一昨日": ("reading", "おとtoi", "おととい"),
    "女の子": ("han_viet", "NỮ NHÂN TỬ", "NỮ TỬ"),
    "放送": ("han_viet", "PHÁP TỐNG", "PHÓNG TỐNG"),
}


def test_known_errors_corrected_raw_preserved(imported):
    conn, r = imported
    assert r["flashcards"]["corrections"]["conflict"] == 0 and r["flashcards"]["corrections"]["skipped"] == 0
    for word, (field, wrong, fixed) in KNOWN_FIXES.items():
        rows = conn.execute("SELECT * FROM vocabulary WHERE word=?", (word,)).fetchall()
        assert rows and all(v[field] == fixed for v in rows), word
        corrected = 0
        for v in rows:
            log = conn.execute("SELECT before_json, after_json FROM review_actions WHERE entity_id=? "
                               "AND action='ai_correction'", (v["id"],)).fetchall()
            if any(json.loads(b).get(field) == wrong and json.loads(a_).get(field) == fixed for b, a_ in log):
                raw = " ".join(x[0] for x in conn.execute(
                    f"SELECT content FROM raw_records WHERE raw_id IN ({','.join(map(str, json.loads(v['raw_ids'])))})"))
                assert wrong in raw, word                             # original CSV text untouched
                corrected += 1
        assert corrected >= 1, word


def test_corrections_idempotent(imported):
    conn, _ = imported
    again = pipeline.apply_vocab_corrections(conn)
    assert again["applied"] == 0 and again["conflict"] == 0
    conn.rollback()


def test_verb_groups_from_dictionary_form(imported):
    """Spec §6.1 examples: the group comes from the dictionary form, never from the ます ending."""
    conn, _ = imported
    from hub.validation import reference
    if not reference.available():
        pytest.skip("reference.sqlite not built")
    expected = {"見ます": 2, "起きます": 2, "借ります": 2, "浴びます": 2, "着ます": 2,
                "切ります": 1, "帰ります": 1, "入ります": 1, "来ます": 3, "勉強します": 3}
    for word, group in expected.items():
        groups = {r[0] for r in conn.execute("SELECT verb_group FROM vocabulary WHERE word=?", (word,))}
        assert groups == {group}, (word, groups)
    rows = dict(conn.execute("SELECT reading, verb_group FROM vocabulary WHERE word='降ります'").fetchall())
    assert rows == {"おります": 2, "ふります": 1}
    assert conn.execute("SELECT COUNT(*) FROM vocabulary WHERE part_of_speech='verb' "
                        "AND verb_group IS NULL").fetchone()[0] == 0


# ---------- exam ----------
SEIKAI = {"vocabulary": [1, 4, 4, 2, 1, 3, 3, 2],
          "grammar_reading": [4, 3, 2, 1, 4, 3, 2, 1, 3, 4, 2, 1, 1],
          "listening": [3, 4, 3, 4, 3, 2, 2, 1]}       # read from N5-seikai.pdf (正解)


def test_answer_key_matches_seikai(imported):
    conn, _ = imported
    got = {"vocabulary": [], "grammar_reading": [], "listening": []}
    for r in conn.execute("SELECT section, correct_answer FROM questions ORDER BY section_id, mondai_no, number"):
        got[r["section"]].append(int(json.loads(r["correct_answer"])[0]))
    assert got == SEIKAI


def test_question_schema_and_integrity(imported):
    conn, _ = imported
    sch = schema("question")
    for r in conn.execute("SELECT * FROM questions"):
        q = dict(r)
        q["options"], q["correct_answer"] = json.loads(q["options"]), json.loads(q["correct_answer"])
        q["source_ids"] = json.loads(q["source_ids"])
        jsonschema.validate(q, sch)
        assert set(q["correct_answer"]) <= {o["option_id"] for o in q["options"]}
        for col in ("audio_asset_id", "image_asset_id"):
            if q[col]:
                a = conn.execute("SELECT file_path FROM assets WHERE asset_id=?", (q[col],)).fetchone()
                assert a and (ROOT / a[0]).is_file(), (q["question_id"], col)
        if q["passage_id"]:
            assert conn.execute("SELECT 1 FROM passages WHERE passage_id=?", (q["passage_id"],)).fetchone()
        if q["section"] == "listening":
            assert q["audio_asset_id"] and q["transcript"]
        assert q["explanation_origin"] == "AI_GENERATED"


def test_exam_json_schema():
    data = json.loads(pipeline.EXAM_JSON.read_text(encoding="utf-8"))
    jsonschema.validate(data, schema("examination"))
    assert data["duration_minutes"] is None        # sample has no timing; never forced to 20/40/30


def test_transcribed_answer_mismatch_is_rejected(imported, tmp_path):
    conn, _ = imported
    data = json.loads(pipeline.EXAM_JSON.read_text(encoding="utf-8"))
    data["questions"][0]["seikai"] = 2
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(ValueError, match="正解"):
        pipeline.import_sample_exam(conn, bad)
    conn.rollback()


def test_spec_sample_records_validate():
    samples = json.loads((Path(__file__).parent / "fixtures" / "spec_samples.json").read_text(encoding="utf-8"))
    for name, rec in samples.items():
        jsonschema.validate(rec, schema(name))


def test_ai_generated_exam_cannot_be_official():
    rec = {"exam_id": "EXAM_X", "title": "x", "level": "N5", "exam_type": "mock", "source_type": "AI_GENERATED",
           "is_official": True, "sections": [{"section_id": "S", "name": "n"}]}
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(rec, schema("examination"))
