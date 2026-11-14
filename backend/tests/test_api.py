"""End-to-end API flows on an imported copy of the real data."""
import pytest
from fastapi.testclient import TestClient

from hub import api


@pytest.fixture(scope="module")
def imported(tmp_path_factory):
    """Own DB: these tests mutate data, so they must not share the read-only import used by test_data."""
    from hub.db import connect
    from hub.ingestion import pipeline
    conn = connect(tmp_path_factory.mktemp("apidb") / "hub.sqlite")
    return conn, pipeline.run_all(conn)


@pytest.fixture(scope="module")
def client(imported):
    conn, _ = imported
    api.set_conn(conn)
    return TestClient(api.app)


def test_dashboard_reflects_real_counts(client):
    d = client.get("/api/stats/dashboard").json()
    assert sum(d["vocabulary_by_status"].values()) >= 1200      # user's 963 cards + verified N5 supplement
    assert d["vocabulary_by_status"].get("verified") == sum(d["vocabulary_by_status"].values())
    assert d["questions_by_status"] == {"needs_review": 29}
    assert d["streak_days"] == 0 and d["reviews_today"] == 0


def test_vocabulary_search_filter(client):
    r = client.get("/api/vocabulary", params={"lesson": 1}).json()
    assert r["total"] > 0 and all(i["lesson_number"] == 1 for i in r["items"])
    r = client.get("/api/vocabulary", params={"q": "びょういん"}).json()
    assert any(i["word"] == "病院" for i in r["items"])


def test_vocab_detail_has_provenance(client):
    vid = client.get("/api/vocabulary", params={"q": "病院"}).json()["items"][0]["id"]
    d = client.get(f"/api/vocabulary/{vid}").json()
    assert d["raw"] and d["sources"][0]["source_id"].startswith("SRC_LOCAL_FC_")


def test_srs_session_and_dashboard(client):
    cards = client.get("/api/srs/due", params={"direction": "jp_vi", "new_limit": 5}).json()
    assert len(cards) == 5
    for c in cards:
        r = client.post(f"/api/srs/cards/{c['card_id']}/answer", json={"rating": "good"}).json()
        assert r["status"] == "reviewing" and r["interval_days"] == 1 and r["due_at"]
    assert client.post(f"/api/srs/cards/{cards[0]['card_id']}/answer", json={"rating": "meh"}).status_code == 422
    d = client.get("/api/stats/dashboard").json()
    assert d["reviews_today"] == 5 and d["streak_days"] == 1
    # new-card daily limit is respected
    assert client.get("/api/srs/due", params={"direction": "jp_vi", "new_limit": 5}).json() == []


def test_review_approve_reject_edit(client):
    v = client.get("/api/vocabulary", params={"q": "病院"}).json()["items"][0]
    assert v["verification_status"] == "verified" and v["verified_by"] == "ai"

    # a hand edit takes the item away from automation until the user approves it
    r = client.post(f"/api/review/vocabulary/{v['id']}",
                    json={"action": "edit", "note": "thử sửa", "edit": {"reading": "びょうinn"}}).json()
    assert r["verification_status"] == "needs_review" and r["verified_by"] == "pending_user"
    assert any(i["code"] == "reading_not_kana" for i in r["issues"])
    assert client.post(f"/api/review/vocabulary/{v['id']}", json={"action": "approve"}).status_code == 409
    q = client.get("/api/review/queue", params={"entity": "vocabulary"}).json()
    assert q["total"] >= 1 and q["items"][0]["id"] == v["id"]
    r = client.post(f"/api/review/vocabulary/{v['id']}",
                    json={"action": "edit", "edit": {"reading": "びょういん"}}).json()
    r = client.post(f"/api/review/vocabulary/{v['id']}", json={"action": "approve", "note": "ok"}).json()
    assert r["verification_status"] == "verified" and r["verified_by"] == "user"
    assert r["history"][0]["action"] == "approve"
    assert "病院" in r["raw"][0]["content"]

    other = client.get("/api/vocabulary", params={"q": "切手"}).json()["items"][0]
    rej = client.post(f"/api/review/vocabulary/{other['id']}", json={"action": "reject"}).json()
    assert rej["verification_status"] == "rejected" and rej["verified_by"] == "user"


def test_reextract_restores_from_raw(client):
    v = client.get("/api/vocabulary", params={"q": "病院"}).json()["items"][0]
    client.patch(f"/api/vocabulary/{v['id']}", json={"meaning_vi": "SAI"})
    r = client.post(f"/api/review/vocabulary/{v['id']}", json={"action": "reextract"}).json()
    assert r["meaning_vi"] == v["meaning_vi"]


def test_archive_toggle(client):
    v = client.get("/api/vocabulary", params={"lesson": 2}).json()["items"][0]
    assert client.post(f"/api/vocabulary/{v['id']}/archive").json()["archived"] is True
    assert all(i["id"] != v["id"] for i in client.get("/api/vocabulary", params={"lesson": 2, "limit": 1000}).json()["items"])
    assert client.post(f"/api/vocabulary/{v['id']}/archive").json()["archived"] is False


def test_question_review_detail(client):
    q = client.get("/api/questions/Q_N5S_L4_1").json()
    assert q["audio_asset_id"] == "AUD_N5S_001" and q["extra_json"]["options_audio_only"] is True
    assert q["page_asset_id"] and q["raw"][0]["extraction_method"] == "ai_vision_transcription"


def test_assets_and_audio_range(client):
    assert client.get("/api/assets/IMG_N5_MONDAI_P002").headers["content-type"] == "image/png"
    r = client.get("/api/assets/AUD_N5S_001", headers={"Range": "bytes=0-1023"})
    assert r.status_code == 206 and len(r.content) == 1024
    assert client.get("/api/assets/NOPE").status_code == 404


def test_sources(client):
    s = client.get("/api/sources").json()
    assert any(x["source_id"] == "SRC_NBLM_010" for x in s)
    assert client.post("/api/sources", json={"url": "ftp://x", "name": "x"}).status_code == 422
    r = client.post("/api/sources", json={"url": "https://example.org/n5", "name": "Ví dụ"})
    assert r.status_code == 201 and r.json()["processing_status"] == "registered"
    assert client.post("/api/sources", json={"url": "https://example.org/n5", "name": "dup"}).status_code == 409
    d = client.get("/api/sources/SRC_LOCAL_FC_BAI01").json()
    assert d["raw_count"] == 45 and d["vocabulary_count"] > 0


def test_reimport_keeps_user_decisions(client, imported):
    conn, _ = imported
    from hub.ingestion import pipeline
    vid = client.get("/api/vocabulary", params={"q": "放送"}).json()["items"][0]["id"]   # has AI issue
    client.post(f"/api/review/vocabulary/{vid}", json={"action": "approve", "force": True})
    client.post("/api/review/question/Q_N5S_V01", json={"action": "approve"})
    pipeline.run_all(conn)
    v = client.get(f"/api/vocabulary/{vid}").json()
    q = client.get("/api/questions/Q_N5S_V01").json()
    assert v["verification_status"] == "verified" and not [i for i in v["issues"] if not i["resolved"]]
    assert q["verification_status"] == "verified" and not [i for i in q["issues"] if not i["resolved"]]
    # SRS progress survives re-import
    assert client.get("/api/stats/dashboard").json()["reviews_today"] >= 5


def test_online_check_with_stub(imported):
    conn, _ = imported
    from hub.ingestion import pipeline
    seen = []

    def stub(url):
        seen.append(url)
        return ("requires_auth", "login") if "notebook.google.com/notebook" in url else ("accessible", "HTTP 200")
    res = pipeline.check_online(conn, checker=stub)
    by = {r["source_id"]: r["access_status"] for r in res}
    assert by["SRC_NBLM_001"] == "manual_export"            # loads, but content needs an export
    assert by["SRC_NOTEBOOK_001"] == "requires_auth"
    assert by["SRC_EXAM_001"] == "accessible" and by["SRC_LESSON_002"] == "accessible"
    assert any(u.endswith("/export?format=txt") for u in seen)   # Google Doc checked via its text export
