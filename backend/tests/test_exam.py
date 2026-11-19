"""Mock exam engine (spec Part 9, §15 examination engine tests) and the rule-generated question bank (§11.5)."""
import json
import random
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from hub import api, repo
from hub.ingestion import knowledge
from hub.learning import exam as examlib
from hub.learning import question_gen as qg
from hub.validation import reference as ref

SAMPLE = "EXAM_N5_OFFICIAL_SAMPLE"


# ---------------------------------------------------------------- pure functions
def test_reading_traps_touch_only_kanji_part_and_never_a_valid_reading():
    rng = random.Random(1)
    allowed = {0}                                      # 咲 -> さ; きます is okurigana
    assert all(v.endswith("きます") for v in qg.reading_variants("さきます", allowed))
    d = qg.reading_distractors("がっこう", {"がっこう", "がこう"}, rng)
    assert len(d) == 3 and len({x for x, _ in d}) == 3 and not {x for x, _ in d} & {"がっこう", "がこう"}
    assert qg.reading_distractors("ん", set(), rng) == []          # not enough traps -> no question


def test_orthography_traps_use_the_reading_the_kanji_has_in_the_word():
    rd = {"旅": {"りょ", "たび"}, "行": {"こう", "い", "ぎょう"}, "校": {"こう"}, "口": {"こう", "くち"},
          "高": {"こう", "たか"}, "生": {"せい", "い"}}
    out = qg.orthography_distractors("旅行", "りょこう", rd.get, rd, lambda w: w == "旅行", random.Random(0))
    assert {w for w, _, _ in out} == {"旅校", "旅口", "旅高"}          # 生 shares only い, not こう
    assert qg.orthography_distractors("旅行", "りょこう", rd.get, rd, lambda w: True, random.Random(0)) == []
    assert qg.split_run("今日", "きょう", {"今": {"いま", "こん"}, "日": {"ひ", "にち"}}.get) is None


def test_score_counts_unanswered_and_readiness_is_labelled_estimate():
    qs = [{"question_id": "a", "section": "vocabulary", "mondai_no": 1, "correct_answer": ["1"], "lesson_number": 3},
          {"question_id": "b", "section": "grammar_reading", "mondai_no": 1, "correct_answer": ["2"]},
          {"question_id": "c", "section": "listening", "mondai_no": 2, "correct_answer": ["3"]}]
    s = examlib.score(qs, {"a": ["2"], "b": ["2"]})
    assert (s["total"], s["correct"], s["incorrect"], s["unanswered"]) == (3, 1, 1, 1)
    assert s["by_section"]["listening"]["unanswered"] == 1 and s["listening_accuracy"] == 0.0
    assert s["weak_vocabulary_lessons"][0]["lesson_number"] == 3
    r = examlib.readiness(s["by_section"])
    assert r["language_knowledge_reading"] == 60 and r["listening"] == 0 and r["likely_pass"] is False
    assert "không phải điểm JLPT" in r["label"]
    r = examlib.readiness(examlib.score(qs[:1], {"a": ["1"]})["by_section"])
    assert r["listening"] is None and r["total"] is None and r["likely_pass"] is None


def test_remaining_seconds():
    t0 = datetime(2026, 1, 1)
    assert examlib.remaining_seconds(None, t0, t0 + timedelta(hours=5)) is None
    assert examlib.remaining_seconds(1200, t0, t0 + timedelta(seconds=200)) == 1000
    assert examlib.remaining_seconds(1200, t0, t0 + timedelta(seconds=5000)) == 0


# ---------------------------------------------------------------- generated bank (real data)
def test_generated_bank_is_unambiguous_and_labelled(imported):
    conn, result = imported
    assert result["generated_questions"]["kanji_reading"] > 200 and result["generated_questions"]["orthography"] > 50
    e = conn.execute("SELECT * FROM exams WHERE exam_id='BANK_N5_GENERATED'").fetchone()
    assert e["is_official"] == 0 and e["source_type"] == "AI_GENERATED"
    qs = conn.execute("SELECT * FROM questions WHERE exam_id='BANK_N5_GENERATED' AND verification_status='verified'").fetchall()
    for q in qs:
        opts = [o["text"] for o in json.loads(q["options"])]
        extra = json.loads(q["extra_json"])
        assert len(opts) == 4 == len(set(opts)) and len(json.loads(q["correct_answer"])) == 1
        assert q["explanation_origin"] == "AI_GENERATED" and len(extra["option_explanations"]) == 4
        v = conn.execute("SELECT * FROM vocabulary WHERE id=?", (extra["target_entity"],)).fetchone()
        assert v["verification_status"] == "verified" and v["archived"] == 0
        right = next(o["text"] for o in json.loads(q["options"]) if o["option_id"] == json.loads(q["correct_answer"])[0])
        wrong = [t for t in opts if t != right]
        if q["mondai_type"] == "kanji_reading":
            assert right == v["reading"]
            valid = {ref._hira(r) for r, _, _ in ref.lookup(v["word"])} | {c[1] for c in ref.masu_candidates(v["word"])}
            assert not set(wrong) & valid, q["question_id"]
        else:
            assert right == v["word"] and not any(ref.lookup(w) or ref.masu_candidates(w) for w in wrong), q["question_id"]


def test_generated_ids_are_stable(imported):
    conn, _ = imported
    from hub.ingestion import knowledge
    before = {r[0]: r[1] for r in conn.execute("SELECT question_id, options FROM questions WHERE exam_id='BANK_N5_GENERATED'")}
    knowledge.import_generated_questions(conn)
    after = {r[0]: r[1] for r in conn.execute("SELECT question_id, options FROM questions WHERE exam_id='BANK_N5_GENERATED'")}
    assert before == after


# ---------------------------------------------------------------- API end to end
@pytest.fixture(scope="module")
def client(tmp_path_factory):
    from hub.db import connect
    from hub.ingestion import pipeline
    conn = connect(tmp_path_factory.mktemp("examdb") / "hub.sqlite")
    pipeline.run_all(conn)
    api.set_conn(conn)
    return TestClient(api.app), conn


def _correct(conn, qid):
    return json.loads(repo.get_question(conn, qid)["correct_answer"])


def test_exam_mode_hides_answers_and_keeps_original_structure(client):
    c, conn = client
    overview = c.get("/api/exams").json()
    assert any(e["exam_id"] == SAMPLE and e["question_count"] == 29 for e in overview["exams"])
    a = c.post("/api/attempts", json={"exam_id": SAMPLE, "mode": "exam"}).json()
    assert [len(s["question_ids"]) for s in a["sections"]] == [8, 13, 8]
    assert all(s["duration_sec"] is None for s in a["sections"])          # sample has no recorded timing
    assert [q["question_id"] for q in a["questions"]][:2] == ["Q_N5S_V01", "Q_N5S_V02"]
    for q in a["questions"]:
        assert "correct_answer" not in q and "explanation_vi" not in q and "transcript" not in q
        assert "option_explanations" not in q["extra"] and "expected_sequence" not in q["extra"]
        if q["extra"].get("options_audio_only"):
            assert all(o["text"] == "" for o in q["options"])
    assert a["sections"][0]["status"] == "current" and a["sections"][1]["status"] == "upcoming"
    cur = c.post("/api/attempts", json={"exam_id": SAMPLE, "timing": "current"}).json()
    assert [s["duration_sec"] for s in cur["sections"]] == [1200, 2400, 1800] and cur["remaining_sec"] <= 1200


def test_autosave_flag_sections_timer_and_submit(client):
    c, conn = client
    a = c.post("/api/attempts", json={"exam_id": SAMPLE, "mode": "exam", "timing": "current"}).json()
    aid = a["attempt_id"]
    v = a["sections"][0]["question_ids"]
    right = _correct(conn, v[0])
    wrong = [o["option_id"] for o in a["questions"][1]["options"] if o["option_id"] not in _correct(conn, v[1])][:1]
    assert c.put(f"/api/attempts/{aid}/answers/{v[0]}", json={"answer": right}).status_code == 200
    r = c.put(f"/api/attempts/{aid}/answers/{v[1]}", json={"answer": wrong, "flagged": True}).json()
    assert "is_correct" not in r                                            # exam mode: no feedback
    assert c.put(f"/api/attempts/{aid}/answers/{v[2]}", json={"answer": ["9"]}).status_code == 422
    g = a["sections"][1]["question_ids"]
    assert c.put(f"/api/attempts/{aid}/answers/{g[0]}", json={"answer": ["1"]}).status_code == 409   # not started
    got = c.get(f"/api/attempts/{aid}").json()
    assert got["answers"][v[0]]["answer"] == right and got["answers"][v[1]]["flagged"] is True
    assert got["answers"][v[0]]["is_correct"] is None                       # not revealed before submission
    # section transition closes the previous section
    assert c.post(f"/api/attempts/{aid}/advance").json()["current_section"] == 1
    assert c.put(f"/api/attempts/{aid}/answers/{v[3]}", json={"answer": ["1"]}).status_code == 409
    # timer: move the section start back past its limit
    conn.execute("UPDATE exam_attempts SET section_started_at=? WHERE attempt_id=?",
                 (repo.iso(repo.now() - timedelta(seconds=2400 + 60)), aid))
    conn.commit()
    assert c.get(f"/api/attempts/{aid}").json()["remaining_sec"] == 0
    assert c.put(f"/api/attempts/{aid}/answers/{g[0]}", json={"answer": ["1"]}).status_code == 409
    c.post(f"/api/attempts/{aid}/advance")
    assert c.post(f"/api/attempts/{aid}/advance").status_code == 409     # last section: submit instead
    res = c.post(f"/api/attempts/{aid}/submit").json()
    s = res["result"]
    assert (s["total"], s["correct"], s["incorrect"], s["unanswered"]) == (29, 1, 1, 27)
    assert s["by_section"]["vocabulary"]["correct"] == 1 and s["by_section"]["listening"]["unanswered"] == 8
    assert s["by_mondai"][0]["mondai_type"] == "kanji_reading"
    assert s["readiness"]["total"] is not None and "không phải điểm JLPT" in s["readiness"]["label"]
    assert res["questions"][0]["correct_answer"] and res["answers"][v[1]]["is_correct"] == 0
    assert c.post(f"/api/attempts/{aid}/submit").status_code == 409
    assert c.put(f"/api/attempts/{aid}/answers/{v[0]}", json={"answer": right}).status_code == 409
    hist = c.get("/api/attempts").json()
    assert hist[0]["attempt_id"] == aid or any(h["attempt_id"] == aid and h["summary"]["correct"] == 1 for h in hist)
    # mistake review collects the wrong answer
    m = c.post("/api/attempts", json={"mistakes_only": True, "mode": "practice"}).json()
    assert v[1] in [q["question_id"] for q in m["questions"]]
    assert c.get("/api/stats/dashboard").json()["exam"]["mistakes_pending"] >= 1


def test_practice_mode_gives_immediate_feedback_and_filters(client):
    c, conn = client
    a = c.post("/api/attempts", json={"mode": "practice", "mondai_type": "kanji_reading", "source": "generated",
                                      "limit": 5}).json()
    assert len(a["questions"]) == 5 and all(q["mondai_type"] == "kanji_reading" for q in a["questions"])
    assert all(s["duration_sec"] is None for s in a["sections"]) and a["remaining_sec"] is None
    q = a["questions"][0]
    assert "correct_answer" not in q
    r = c.put(f"/api/attempts/{a['attempt_id']}/answers/{q['question_id']}",
              json={"answer": _correct(conn, q["question_id"])}).json()
    assert r["is_correct"] is True and r["question"]["explanation_vi"] and r["question"]["extra"]["option_explanations"]
    assert c.put(f"/api/attempts/{a['attempt_id']}/answers/{q['question_id']}", json={"answer": ["9"]}).status_code == 409
    sec = c.post("/api/attempts", json={"mode": "practice", "section": "listening"}).json()
    assert {q["section"] for q in sec["questions"]} == {"listening"} and sec["questions"][0]["audio_asset_id"]
    custom = c.post("/api/attempts", json={"mode": "exam", "source": "generated", "limit": 10, "timing": "custom",
                                           "time_limit_min": 5}).json()
    assert sum(s["duration_sec"] for s in custom["sections"]) == 300
    assert c.post("/api/attempts", json={"timing": "custom"}).status_code == 422
    assert c.get("/api/assets/AUD_N5S_001", headers={"Range": "bytes=0-99"}).status_code == 206


# ---------------------------------------------------------------- past papers (ADR-019)
def test_consensus_status_needs_key_and_both_solvers():
    assert examlib.consensus_status(2, [2, 2]) == "verified"
    assert examlib.consensus_status(2, [2, 3]) == "needs_review"
    assert examlib.consensus_status(2, [3, 3]) == "needs_review"        # both AIs disagree with the key
    assert examlib.consensus_status(2, [2, None]) == "needs_review"     # a solver missing
    assert examlib.consensus_status(2, []) == "needs_review"            # official sample: no solvers


def _past(conn):
    rows = conn.execute("SELECT exam_id, is_official, source_type, data_json FROM exams "
                        "WHERE exam_type='past_exam'").fetchall()
    if not rows:
        pytest.skip("Chưa có đề thật trên máy (data/normalized/exams/EXAM_N5_20*.json + data/raw không commit)")
    return rows


def test_past_papers_are_labelled_and_consensus_backed(client):
    _, conn = client
    from hub.ingestion import pipeline
    for r in _past(conn):
        assert r["is_official"] == 0 and r["source_type"] in ("COMMUNITY_KEY", "AI_ANSWERED")
        src = pipeline.EXAM_JSON.parent / f"{r['exam_id']}.json"
        data = json.loads(src.read_text(encoding="utf-8"))
        review = json.loads(src.with_name(f"{r['exam_id']}.ai_review.json").read_text(encoding="utf-8"))
        qs = {q["question_id"]: q for q in repo.questions_where(conn, exam_id=r["exam_id"])}
        assert len(qs) == len(data["questions"])
        decided = {x["question_id"] for x in data["questions"] if x.get("decided_by") == "user"}
        for qid, q in qs.items():
            key = json.loads(q["correct_answer"])[0]
            a = review[qid]
            if qid in decided:                      # user settled a disputed key; JSON keeps the decision
                assert (q["verification_status"], q["verified_by"]) == ("verified", "user"), qid
                assert a["verdict_note"] and "Người dùng quyết định" in a["verdict_note"], qid
            elif q["verification_status"] == "verified" and q["verified_by"] == "ai":
                assert str(a["solver_a"]) == str(a["solver_b"]) == key, qid
            elif q["verified_by"] not in ("user", "pending_user"):
                codes = {i["code"] for i in repo.issues_for(conn, "question", qid) if not i["resolved"]}
                assert "answer_key_disputed" in codes, qid
            if q["section"] == "listening":
                assert q["audio_asset_id"] and q["transcript"], qid


def test_past_papers_filter_and_exam_mode_hide_answers(client):
    c, conn = client
    rows = _past(conn)
    a = c.post("/api/attempts", json={"mode": "practice", "source": "past", "limit": 50}).json()
    past_ids = {r["exam_id"] for r in rows}
    assert a["questions"] and {q["exam_id"] for q in a["questions"]} <= past_ids
    eid = rows[0]["exam_id"]
    e = c.post("/api/attempts", json={"exam_id": eid, "mode": "exam", "timing": "original"}).json()
    meta = json.loads(rows[0]["data_json"])
    assert [s["duration_sec"] for s in e["sections"]] == [s["duration_minutes"] * 60 for s in meta["sections"]]
    for q in e["questions"]:
        assert "correct_answer" not in q and "explanation_vi" not in q and "transcript" not in q
        assert "option_explanations" not in q["extra"] and "expected_sequence" not in q["extra"]
        if q["extra"].get("options_audio_only"):
            assert all(o["text"] == "" for o in q["options"])


# ---------------------------------------------------------------- agent-authored grammar bank (ADR-020)
GQ = {"question_id": "Q_GQ_T", "grammar_id": "GRA_000001", "mondai_type": "sentence_composition",
      "question_text": "つくえの ＿＿ ＿＿ ★ ＿＿ あります。", "options": ["に", "上", "本", "が"], "answer": 3,
      "star_position": 3, "expected_sequence": [2, 1, 3, 4], "explanation_vi": "x",
      "option_explanations": {"1": "a", "2": "b", "3": "c", "4": "d"}}


def _codes(q, past=frozenset()):
    return {c for c, *_ in knowledge.check_grammar_question(q, {"GRA_000001"}, set("上本"), set(past))}


def test_grammar_question_rules():
    assert _codes(GQ) == set()
    assert "star_answer_mismatch" in _codes({**GQ, "answer": 1})
    assert "star_position_mismatch" in _codes({**GQ, "star_position": 2, "expected_sequence": [2, 3, 1, 4]})
    assert "slot_count" in _codes({**GQ, "question_text": "つくえの ＿＿ ★ ＿＿ あります。"})
    assert "bad_sequence" in _codes({**GQ, "expected_sequence": [2, 2, 3, 4]})
    assert "bad_options" in _codes({**GQ, "options": ["に", "に", "本", "が"]})
    assert "grammar_not_verified" in _codes({**GQ, "grammar_id": "GRA_999999"})
    assert "kanji_outside_n5" in _codes({**GQ, "question_text": "机の ＿＿ ＿＿ ★ ＿＿ あります。"})
    assert "copied_from_past_exam" in _codes(GQ, {knowledge.jp_key("つくえの ＿＿ ＿＿ ★ ＿＿ あります。")})
    form = {**GQ, "mondai_type": "grammar_form", "question_text": "つくえの 上（　　） 本が あります。",
            "star_position": None, "expected_sequence": None, "answer": 1}
    assert _codes(form) == set() and "blank_count" in _codes({**form, "question_text": "つくえの 上 本が あります。"})


def test_score_reports_weak_grammar_points():
    qs = [{"question_id": "g1", "section": "grammar_reading", "mondai_no": 1, "correct_answer": ["1"],
           "grammar_id": "GRA_000002", "grammar_pattern": "P2"},
          {"question_id": "g2", "section": "grammar_reading", "mondai_no": 2, "correct_answer": ["1"],
           "grammar_id": "GRA_000002", "grammar_pattern": "P2"},
          {"question_id": "g3", "section": "grammar_reading", "mondai_no": 1, "correct_answer": ["1"],
           "grammar_id": "GRA_000003", "grammar_pattern": "P3"}]
    w = examlib.score(qs, {"g1": ["1"], "g2": ["2"], "g3": ["1"]})["weak_grammar_points"]
    assert [(x["grammar_id"], x["pattern"], x["correct"], x["total"]) for x in w] == [("GRA_000002", "P2", 1, 2)]


def test_grammar_bank_is_consensus_backed(imported):
    conn, result = imported
    st = result["grammar_questions"]
    assert st["verified"] >= 300, st
    e = conn.execute("SELECT * FROM exams WHERE exam_id=?", (knowledge.GQ_EXAM,)).fetchone()
    assert e["is_official"] == 0 and e["source_type"] == "AI_GENERATED" and e["exam_type"] == "question_bank"
    review = json.loads(knowledge.GRAMMAR_Q_REVIEW.read_text(encoding="utf-8"))
    verified_grammar = {r[0] for r in conn.execute("SELECT id FROM grammar WHERE verification_status='verified'")}
    rows = conn.execute("SELECT * FROM questions WHERE exam_id=? AND verification_status='verified'",
                        (knowledge.GQ_EXAM,)).fetchall()
    assert {r["mondai_type"] for r in rows} == {"grammar_form", "sentence_composition"}
    for q in rows:
        extra, ans = json.loads(q["extra_json"]), int(json.loads(q["correct_answer"])[0])
        assert extra["grammar_id"] in verified_grammar and len(extra["option_explanations"]) == 4
        r = review[q["question_id"]]
        assert r["solver_a"] == r["solver_b"] == ans, q["question_id"]
        if q["mondai_type"] == "sentence_composition":
            assert sorted(extra["expected_sequence"]) == [1, 2, 3, 4]
            assert extra["expected_sequence"][extra["star_position"] - 1] == ans
        assert not conn.execute("SELECT 1 FROM validation_issues WHERE entity_type='question' AND entity_id=? "
                                "AND resolved=0 AND severity IN ('error','warning')", (q["question_id"],)).fetchone()


def test_grammar_bank_exam_mode_hides_answers_and_reports_weak_points(client):
    c, conn = client
    a = c.post("/api/attempts", json={"mode": "exam", "source": "generated", "mondai_type": "sentence_composition",
                                      "limit": 10, "timing": "none"}).json()
    assert a["questions"] and all(q["exam_id"] == knowledge.GQ_EXAM for q in a["questions"])
    for q in a["questions"]:
        assert "correct_answer" not in q and "explanation_vi" not in q
        assert not {"option_explanations", "expected_sequence", "grammar_pattern"} & set(q["extra"])
        assert q["extra"]["star_position"] in (1, 2, 3, 4)
    for q in a["questions"]:                      # answer everything wrong
        wrong = next(o["option_id"] for o in q["options"] if [o["option_id"]] != _correct(conn, q["question_id"]))
        c.put(f"/api/attempts/{a['attempt_id']}/answers/{q['question_id']}", json={"answer": [wrong]})
    done = c.post(f"/api/attempts/{a['attempt_id']}/submit").json()
    assert done["result"]["weak_grammar_points"] and done["result"]["weak_grammar_points"][0]["pattern"]
    assert all("expected_sequence" in q["extra"] for q in done["questions"])


def test_dashboard_suggests_grammar_points_until_answered_right(client):
    """ADR-021: dashboard uses the latest answer of each question, so fixing a mistake removes the suggestion."""
    c, conn = client

    def redo_mistakes_correctly():
        r = c.post("/api/attempts", json={"mode": "practice", "mistakes_only": True, "limit": 200})
        if r.status_code == 404:                  # no mistakes pending
            return
        redo = r.json()
        for q in redo["questions"]:
            c.put(f"/api/attempts/{redo['attempt_id']}/answers/{q['question_id']}",
                  json={"answer": _correct(conn, q["question_id"])})
        c.post(f"/api/attempts/{redo['attempt_id']}/submit")

    redo_mistakes_correctly()                     # clear mistakes left by earlier tests in this module
    assert c.get("/api/stats/dashboard").json()["weak_grammar_points"] == []
    a = c.post("/api/attempts", json={"mode": "practice", "source": "generated", "mondai_type": "grammar_form",
                                      "limit": 3}).json()
    for q in a["questions"]:
        wrong = next(o["option_id"] for o in q["options"] if [o["option_id"]] != _correct(conn, q["question_id"]))
        c.put(f"/api/attempts/{a['attempt_id']}/answers/{q['question_id']}", json={"answer": [wrong]})
    c.post(f"/api/attempts/{a['attempt_id']}/submit")
    missed = {json.loads(repo.get_question(conn, q["question_id"])["extra_json"])["grammar_id"] for q in a["questions"]}
    weak = c.get("/api/stats/dashboard").json()["weak_grammar_points"]
    assert {w["grammar_id"] for w in weak} == missed and all(w["pattern"] and w["correct"] < w["total"] for w in weak)

    redo_mistakes_correctly()
    assert c.get("/api/stats/dashboard").json()["weak_grammar_points"] == []


# ---------- Dashboard goal / analytics / practice by grammar point (ADR-022) ----------
def test_settings_daily_goal(client):
    c, _ = client
    assert c.get("/api/settings").json() == {"daily_goal": 30, "exam_date": None}
    assert c.put("/api/settings", json={"daily_goal": 50}).json() == {"daily_goal": 50, "exam_date": None}
    assert c.get("/api/stats/dashboard").json()["daily_goal"] == 50
    assert c.put("/api/settings", json={"daily_goal": 3}).status_code == 422


def test_practice_by_grammar_point_and_activity_analytics(client):
    c, conn = client
    gid = conn.execute("SELECT json_extract(extra_json,'$.grammar_id') FROM questions WHERE exam_id='BANK_N5_GRAMMAR_AI' "
                       "AND verification_status='verified' GROUP BY 1 HAVING COUNT(*)=2 LIMIT 1").fetchone()[0]
    assert c.post("/api/attempts", json={"mode": "practice", "grammar_id": "x"}).status_code == 422
    before = c.get("/api/stats/dashboard").json()["done_today"]
    for _ in range(2):                                    # same point answered wrong twice → repeated mistakes
        a = c.post("/api/attempts", json={"mode": "practice", "grammar_id": gid, "limit": 2}).json()
        qids = [q["question_id"] for q in a["questions"]]
        assert len(qids) == 2 and {json.loads(repo.get_question(conn, q)["extra_json"])["grammar_id"] for q in qids} == {gid}
        for q in a["questions"]:
            wrong = next(o["option_id"] for o in q["options"] if [o["option_id"]] != _correct(conn, q["question_id"]))
            c.put(f"/api/attempts/{a['attempt_id']}/answers/{q['question_id']}", json={"answer": [wrong]})
        c.post(f"/api/attempts/{a['attempt_id']}/submit")

    d = c.get("/api/stats/dashboard").json()
    assert d["done_today"] == before + 4 and d["streak_days"] >= 1     # exam-only day counts for the streak
    kinds = {r["kind"]: r for r in d["recommendations"]}
    assert "mistakes" in kinds and "exam" not in kinds                # just submitted → no "take an exam" nudge
    assert any(w["grammar_id"] == gid for w in d["weak_grammar_points"])

    an = c.get("/api/stats/analytics").json()
    assert len(an["daily"]) == 30 and an["daily"][-1]["reviews"] + an["daily"][-1]["answers"] == d["done_today"]
    assert an["attempts"][-1]["attempt_id"] == a["attempt_id"] and "grammar_reading" in an["attempts"][-1]["by_section"]
    assert set(qids) <= {m["question_id"] for m in an["repeated_mistakes"] if m["wrong"] >= 2}
    assert c.get("/api/stats/analytics", params={"days": 3}).status_code == 422


def test_practice_grammar_by_lesson_range(client):     # ADR-028
    c, conn = client
    lesson = {r[0]: r[1] for r in conn.execute("SELECT id, COALESCE(lesson_number, 26) FROM grammar")}
    expect = sum(1 for q in repo.questions_where(conn) if not q["passage_id"]
                 and lesson.get(json.loads(q["extra_json"] or "{}").get("grammar_id"), 0) in (1, 2, 3))
    a = c.post("/api/attempts", json={"mode": "practice", "lesson_from": 1, "lesson_to": 3, "limit": 200}).json()
    assert len(a["questions"]) == expect > 0 and "bài 1–3" in a["title"]
    for q in a["questions"]:
        extra = json.loads(repo.get_question(conn, q["question_id"])["extra_json"])
        assert lesson[extra["grammar_id"]] in (1, 2, 3) and q["passage_id"] is None
    sup = c.post("/api/attempts", json={"mode": "practice", "lesson_from": 26, "lesson_to": 26}).json()
    assert all(lesson[json.loads(repo.get_question(conn, q["question_id"])["extra_json"])["grammar_id"]] == 26
               for q in sup["questions"]) and sup["questions"]
    for bad in ({"lesson_from": 3, "lesson_to": 1}, {"lesson_from": 1}, {"lesson_to": 27, "lesson_from": 1}):
        assert c.post("/api/attempts", json={"mode": "practice", **bad}).status_code == 422


# ---------------------------------------------------------------- agent-authored reading bank (ADR-026)
def _q(k, **kw):
    return {"question_id": f"Q_RQ_T_{k}", "question_text": f"［{k}］", "options": ["は", "を", "に", "で"],
            "answer": 1, "explanation_vi": "x", "option_explanations": {"1": "a", "2": "b", "3": "c", "4": "d"}, **kw}


RG = {"passage_id": "PSG_RQ_T", "mondai_type": "text_grammar",
      "text": "わたしは 毎朝 パン［1］ 食べます。［2］、学校へ 行きます。", "questions": [_q(1), _q(2)]}


def _rcodes(p, past=frozenset()):
    return {c for issues in knowledge.check_reading_group(p, {"GRA_000001"}, set("毎朝食学校行"), set(past)).values()
            for c, *_ in issues}


def test_reading_group_rules():
    assert _rcodes(RG) == set()
    assert "blank_count" in _rcodes({**RG, "questions": [_q(1)]})
    assert "blank_question_mismatch" in _rcodes({**RG, "questions": [_q(2), _q(1)]})
    assert "bad_answer" in _rcodes({**RG, "questions": [_q(1), _q(2, answer=5)]})
    assert "grammar_not_verified" in _rcodes({**RG, "questions": [_q(1, grammar_id="GRA_999999"), _q(2)]})
    assert "kanji_outside_n5" in _rcodes({**RG, "text": RG["text"].replace("パン", "麺")})
    assert "copied_from_past_exam" in _rcodes(RG, {knowledge.jp_key(RG["text"])})
    short = {**RG, "mondai_type": "reading_short", "text": "あした 学校へ 行きます。",
             "questions": [_q(1, question_text="あした どこへ 行きますか。")]}
    assert _rcodes(short) == set()
    assert "unexpected_blank" in _rcodes({**short, "text": RG["text"]})
    assert "missing_question" in _rcodes({**short, "questions": [_q(1, question_text="")]})
    assert "bad_mondai_type" in _rcodes({**short, "mondai_type": "essay"})


def test_reading_bank_is_consensus_backed(imported):
    conn, result = imported
    st = result["reading_questions"]
    assert st["verified"] >= 100, st
    e = conn.execute("SELECT * FROM exams WHERE exam_id=?", (knowledge.RQ_EXAM,)).fetchone()
    assert e["is_official"] == 0 and e["source_type"] == "AI_GENERATED" and e["exam_type"] == "question_bank"
    review = json.loads(knowledge.READING_Q_REVIEW.read_text(encoding="utf-8"))
    rows = conn.execute("SELECT q.*, p.text FROM questions q JOIN passages p USING (passage_id) WHERE q.exam_id=? "
                        "AND q.verification_status='verified'", (knowledge.RQ_EXAM,)).fetchall()
    assert len(rows) == st["verified"]                                   # every question has its passage
    assert {r["mondai_type"] for r in rows} == set(knowledge.RQ_MONDAI)
    for q in rows:
        ans = int(json.loads(q["correct_answer"])[0])
        assert review[q["question_id"]]["solver_a"] == review[q["question_id"]]["solver_b"] == ans, q["question_id"]
        assert q["mondai_no"] == knowledge.RQ_MONDAI[q["mondai_type"]][0] and q["number"] >= 1
        if q["mondai_type"] == "text_grammar":
            assert q["question_text"] == f"［{q['number']}］" and q["question_text"] in q["text"]
        assert not conn.execute("SELECT 1 FROM validation_issues WHERE entity_type='question' AND entity_id=? "
                                "AND resolved=0 AND severity IN ('error','warning')", (q["question_id"],)).fetchone()


def test_reading_bank_keeps_passages_whole_and_hides_answers(client):
    c, conn = client
    a = c.post("/api/attempts", json={"mode": "exam", "source": "generated", "mondai_type": "text_grammar",
                                      "limit": 3, "timing": "none"}).json()
    qs = a["questions"]
    assert qs and all(q["exam_id"] == knowledge.RQ_EXAM and q["passage_id"] in a["passages"] for q in qs)
    for pid in {q["passage_id"] for q in qs}:                  # a passage is never split by the sampler
        live = {r[0] for r in conn.execute("SELECT question_id FROM questions WHERE passage_id=? "
                                           "AND verification_status!='rejected'", (pid,))}
        got = [q for q in qs if q["passage_id"] == pid]
        assert {q["question_id"] for q in got} == live
        assert [q["number"] for q in got] == sorted(q["number"] for q in got)
    for q in qs:
        assert "correct_answer" not in q and "passage_translation_vi" not in q["extra"]


# ---------------------------------------------------------------- listening timestamps (ADR-025)
def test_listening_timestamps_fit_the_track_and_hide_nothing(client):
    c, conn = client
    rows = conn.execute("SELECT q.question_id, q.exam_id, q.extra_json, a.duration_seconds FROM questions q "
                        "JOIN assets a ON a.asset_id=q.audio_asset_id WHERE json_extract(q.extra_json,'$.audio_start') "
                        "IS NOT NULL").fetchall()
    assert len(rows) >= 90
    by_exam: dict[str, list] = {}
    for r in rows:
        x = json.loads(r["extra_json"])
        assert 0 <= x["audio_start"] < x["audio_end"] <= (r["duration_seconds"] or 1e9) + 1, r["question_id"]
        by_exam.setdefault(r["exam_id"], []).append((x["audio_start"], x["audio_end"]))
    for spans in by_exam.values():                          # clips of one track never overlap
        spans.sort()
        assert all(e <= s2 for (_, e), (s2, _) in zip(spans, spans[1:]))
    stamped = [r["question_id"] for r in rows]                # a timestamped question is not reported as missing one
    assert not conn.execute(f"SELECT 1 FROM validation_issues WHERE code='audio_timestamp_missing' AND resolved=0 "
                            f"AND entity_id IN ({','.join('?' * len(stamped))})", stamped).fetchone()
    exam_id = rows[0]["exam_id"]
    a = c.post("/api/attempts", json={"mode": "exam", "exam_id": exam_id, "section": "listening"}).json()
    q = next(q for q in a["questions"] if "audio_start" in q["extra"])
    assert "transcript" not in q and "correct_answer" not in q


def test_numbers_topic_api_srs_and_practice(client):      # ADR-029
    c, conn = client
    cats = c.get("/api/numbers").json()
    keys = [x["key"] for x in cats]
    assert {"number", "tsu", "nin", "hon", "fun", "ji", "nichi", "gatsu", "kai_floor", "en"} <= set(keys)
    hon = next(x for x in cats if x["key"] == "hon")
    assert hon["rule_vi"] and any(i["jp"] == "三本" and i["reading"] == "さんぼん" and i["irregular"] for i in hon["items"])
    cards = c.get("/api/srs/due", params={"entity": "number", "new_limit": 5}).json()
    assert len(cards) == 5 and all(x["jp"] and x["reading"] and x["category_vi"] for x in cards)
    a = c.post("/api/attempts", json={"mode": "practice", "topic": "numbers", "limit": 10}).json()
    assert len(a["questions"]) == 10 and "Số đếm" in a["title"]
    assert {q["exam_id"] for q in a["questions"]} == {"BANK_N5_NUMBERS"}
    assert all("correct_answer" not in q for q in a["questions"])          # nothing revealed before answering
    assert c.post("/api/attempts", json={"mode": "practice", "topic": "x"}).status_code == 422
