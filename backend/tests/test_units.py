import sqlite3
from datetime import datetime, timezone

import pytest

from hub import repo
from hub.ingestion import flashcards_csv as fc
from hub.learning import srs
from hub.validation import vocabulary as vr
from hub.validation.kana import check_transcript_gloss, romaji_matches, to_romaji


# ---------- kana / romaji ----------
@pytest.mark.parametrize("kana,romaji", [
    ("がっこう", "gakkou"), ("きって", "kitte"), ("まっちゃ", "matcha"), ("びょういん", "byouin"),
    ("しゅくだい", "shukudai"), ("コーヒー", "koohii"), ("パーティー", "paatii"), ("ちょっと", "chotto"),
])
def test_to_romaji(kana, romaji):
    assert to_romaji(kana) == romaji


def test_transcript_gloss_rules():                          # ADR-032
    t = "店で話しています。\n女：コーヒーを2つください。\n1. はい"
    ok = [{"kana": "みせではなしています。", "romaji": "mise de hanashite imasu.", "vi": "Đang nói chuyện ở cửa hàng."},
          {"kana": "コーヒーをふたつください。", "romaji": "koohii o futatsu kudasai.", "vi": "Cho tôi 2 cà phê."},
          {"kana": "はい", "romaji": "hai", "vi": "Vâng"}]
    assert check_transcript_gloss(t, ok) == []
    assert check_transcript_gloss(t, ok[:2])                                    # line count
    assert check_transcript_gloss(t, [ok[0], {**ok[1], "romaji": "koohii o mittsu kudasai."}, ok[2]])  # romaji ≠ kana
    assert check_transcript_gloss(t, [ok[0], {**ok[1], "kana": "コーヒーを2つください。"}, ok[2]])    # digit in kana
    assert check_transcript_gloss(t, [ok[1], ok[0], ok[2]])                     # shifted lines: original kana missing
    assert check_transcript_gloss(t, [ok[0], ok[1], {**ok[2], "vi": " "}])      # no translation


def test_romaji_match_tolerates_conventions():
    assert romaji_matches("びょういん", "Byōin")
    assert romaji_matches("わたしは", "watashi wa")
    assert romaji_matches("こんばんは", "Konbanwa")
    assert not romaji_matches("ひるやすみ", "hirusumi")
    assert not romaji_matches("おなかがあきました", "Onaka ga sukimashita")


# ---------- CSV parsing: all three real formats ----------
def test_parse_numbered_format():
    f = fc.parse_back("1. Đọc: びょういん - BỆNH VIỆN\n2. Rōmaji: Byōin\n3. Nghĩa: Bệnh viện\n"
                      "4. Ví dụ: 神戸病院の 医者です。\n5. Rōmaji ví dụ: Kōbe Byōin no isha desu.\n"
                      "6. Dịch ví dụ: Bác sĩ của bệnh viện Kobe.")
    assert f["reading"] == "びょういん" and f["han_viet"] == "BỆNH VIỆN"
    assert f["meaning_vi"] == "Bệnh viện" and f["example_jp"] == "神戸病院の 医者です。"
    assert f["example_romaji"].startswith("Kōbe") and f["example_vi"].startswith("Bác sĩ")


def test_parse_unnumbered_format():
    f = fc.parse_back("Đọc: くつ - NGOA\nRōmaji: kutsu\nNghĩa: Giày\nVí dụ: これは 日本の 靴です。")
    assert (f["reading"], f["han_viet"], f["meaning_vi"]) == ("くつ", "NGOA", "Giày")


def test_parse_freeform_returns_none():
    assert fc.parse_back("ひとつ (hitotsu)") is None


@pytest.mark.parametrize("raw,expected", [
    ("おでかけですか (XUẤT)", ("おでかけですか", "XUẤT")),
    ("サイズ (Không có âm Hán-Việt)", ("サイズ", None)),
    ("トイレ / おてあらい (お手洗い - THỦ TẨY)", ("トイレ / おてあらい", "THỦ TẨY")),
    ("ぜんぶ", ("ぜんぶ", None)),
])
def test_split_reading_variants(raw, expected):
    assert fc.split_reading(raw) == expected


def test_deck_info_from_filename():
    from pathlib import Path
    assert fc.deck_info(Path("flashcards_Bai14.csv")) == ("Bai14", 14, [])
    assert fc.deck_info(Path("flashcards_Từ Vựng Kaiwa-Hội thoại giao tiếp.csv"))[2] == ["kaiwa"]


def test_verb_group_never_inferred():
    v = {"word": "見ます", "reading": "みます", "meaning_vi": "xem", "part_of_speech": fc.guess_pos("見ます")}
    codes = [c for c, *_ in vr.validate(v)]
    assert "needs_dictionary_form" in codes and v.get("verb_group") is None


# ---------- validation rules ----------
def codes(v):
    return {c for c, *_ in vr.validate(v)}


def test_valid_item_has_no_warnings():
    v = {"word": "病院", "reading": "びょういん", "romaji": "Byōin", "han_viet": "BỆNH VIỆN", "meaning_vi": "Bệnh viện"}
    assert vr.status_for(vr.validate(v)) == "normalized"


def test_vietnamese_tilde_is_not_mojibake():
    assert "encoding" not in codes({"word": "会社", "reading": "かいしゃ", "han_viet": "HỘI XÃ", "meaning_vi": "Công ty"})
    assert "encoding" in codes({"word": "会社", "reading": "かいしゃ", "meaning_vi": "CÃ´ng ty"})


def test_detects_real_errors():
    assert "reading_not_kana" in codes({"word": "一昨日", "reading": "おとtoi", "meaning_vi": "hôm kia"})
    assert "han_viet_count" in codes({"word": "女の子", "reading": "おんなのこ", "han_viet": "NỮ NHÂN TỬ", "meaning_vi": "bé gái"})
    assert "han_viet_count" not in codes({"word": "日曜日", "reading": "にちようび", "han_viet": "NHẬT DIỆU NHẬT", "meaning_vi": "CN"})
    assert "romaji_mismatch" in codes({"word": "昼休み", "reading": "ひるやすみ", "romaji": "hirusumi", "meaning_vi": "nghỉ trưa"})
    assert "kana_word_reading_differs" in codes({"word": "クラシック", "reading": "くらしく", "meaning_vi": "cổ điển"})


def test_multiple_readings_are_accepted():
    assert "reading_not_kana" not in codes({"word": "何", "reading": "なに / なん", "romaji": "nani / nan", "meaning_vi": "cái gì"})


# ---------- SRS ----------
NOW = datetime(2026, 11, 14, 9, 0, tzinfo=timezone.utc)


def test_never_mastered_after_one_answer():
    c, _ = srs.schedule(srs.Card(), "easy", NOW)
    assert c.status != "mastered"


def test_mastery_requires_streak_and_interval():
    c, t = srs.Card(), NOW
    for _ in range(6):
        c, t = srs.schedule(c, "good", t)
    assert c.status == "mastered" and c.interval_days >= 21 and c.reps >= 3


def test_intensive_ladder_and_mastery():
    """SRS cấp tốc (ADR-030): 10 min → 1 → 2 → 4 → 7 days, mastered after 5 correct in a row."""
    c, t, gaps = srs.Card(), NOW, []
    for _ in range(6):
        prev = t
        c, t = srs.schedule(c, "good", t, intensive=True)
        gaps.append(round((t - prev).total_seconds() / 86400, 4))
        assert c.status == ("mastered" if c.reps >= 5 else "reviewing")
    assert gaps == [round(10 / 1440, 4), 1, 2, 4, 7, 7]
    c, due = srs.schedule(c, "again", t, intensive=True)
    assert c.reps == 0 and c.status == "learning" and (due - t).total_seconds() == 600


def test_mastered_after_five_in_a_row_in_any_mode():
    """Mixing modes: 4 correct in cấp tốc, the 5th in normal SRS -> still mastered."""
    c, t = srs.Card(), NOW
    for _ in range(4):
        c, t = srs.schedule(c, "good", t, intensive=True)
    c, t = srs.schedule(c, "easy", t)
    assert c.reps == 5 and c.interval_days < 21 and c.status == "mastered"


def test_intensive_follows_ladder_and_caps_before_exam():
    old = srs.Card(interval_days=15, reps=4, review_count=4, status="reviewing")   # booked far out by normal SM-2
    c, due = srs.schedule(old, "good", NOW, intensive=True)
    assert c.interval_days == 7                                   # the ladder, not the old 15-day gap
    exam = NOW.date().replace(day=19)                             # 5 days away → at most 4 days
    c, due = srs.schedule(old, "good", NOW, intensive=True, exam_date=exam)
    assert c.interval_days == 4 and due.date() < exam
    c, _ = srs.schedule(old, "good", NOW, intensive=True, exam_date=NOW.date())   # exam passed: no cap
    assert c.interval_days == 7
    # read-time gap for a streak = the gap the ladder gives when that streak was reached
    assert [srs.intensive_gap(r) for r in (0, 1, 2, 3, 4, 5, 9)] == [10 / 1440, 10 / 1440, 1, 2, 4, 7, 7]


def test_again_resets_and_counts_lapse():
    c = srs.Card()
    for _ in range(3):
        c, _ = srs.schedule(c, "good", NOW)
    c, due = srs.schedule(c, "again", NOW)
    assert c.reps == 0 and c.interval_days == 0 and c.lapses == 1 and c.status == "learning"
    assert (due - NOW).total_seconds() == 600


def test_ease_floor_and_needs_attention():
    c = srs.Card()
    c, _ = srs.schedule(c, "good", NOW)
    for _ in range(10):
        c, _ = srs.schedule(c, "again", NOW)
    assert c.ease == pytest.approx(srs.MIN_EASE) and c.status == "needs_attention"


def test_intervals_grow():
    c, t = srs.Card(), NOW
    intervals = []
    for _ in range(4):
        c, t = srs.schedule(c, "good", t)
        intervals.append(c.interval_days)
    assert intervals == sorted(intervals) and intervals[:2] == [1, 6]


def test_invalid_rating():
    with pytest.raises(ValueError):
        srs.schedule(srs.Card(), "perfect", NOW)


# ---------- RAW immutability (DB-level) ----------
def test_raw_records_are_immutable(conn):
    repo.upsert_source(conn, {"source_id": "S1", "source_type": "csv", "name": "x", "reliability": "USER_CREATED"})
    rid = repo.insert_raw(conn, "S1", "row:1", "original", "csv_row")
    with pytest.raises(sqlite3.DatabaseError, match="immutable"):
        conn.execute("UPDATE raw_records SET content='changed' WHERE raw_id=?", (rid,))
    with pytest.raises(sqlite3.DatabaseError, match="immutable"):
        conn.execute("DELETE FROM raw_records WHERE raw_id=?", (rid,))
    assert repo.insert_raw(conn, "S1", "row:1", "original", "csv_row") == rid   # idempotent


def test_reliability_constraint(conn):
    with pytest.raises(sqlite3.IntegrityError):
        repo.upsert_source(conn, {"source_id": "S2", "source_type": "pdf", "name": "x", "reliability": "MAYBE"})


# ---------- analytics (ADR-022) ----------
def test_active_seconds_counts_only_short_gaps():
    from hub.learning.analytics import active_seconds
    t = ["2026-01-01T10:00:00+07:00", "2026-01-01T10:01:00+07:00", "2026-01-01T10:30:00+07:00",
         "2026-01-01T10:30:20+07:00"]
    assert active_seconds(t) == 80 and active_seconds(list(reversed(t))) == 80
    assert active_seconds([]) == 0 and active_seconds(t[:1]) == 0


def test_recommend_priority_and_no_data():
    from hub.learning.analytics import recommend
    base = {"due": {"vocabulary": 0, "grammar": 0, "kanji": 0}, "mistakes_pending": 0, "weak_grammar_points": [],
            "days_since_last_exam": 1, "new_cards_left": 0}
    assert recommend(base) == []
    r = recommend({**base, "due": {"vocabulary": 2, "grammar": 5, "kanji": 0}, "mistakes_pending": 3,
                   "weak_grammar_points": [{"grammar_id": "GRA_000001", "pattern": "は", "correct": 0, "total": 2}],
                   "days_since_last_exam": None, "new_cards_left": 10})
    assert [x["kind"] for x in r] == ["srs_due", "mistakes", "grammar_point", "exam"]
    assert r[0]["href"] == "#/flashcards?entity=grammar" and r[2]["start"]["grammar_id"] == "GRA_000001"
    assert [x["kind"] for x in recommend({**base, "new_cards_left": 5, "days_since_last_exam": 8})] == ["exam", "srs_new"]


# ---------- listening timestamps (ADR-025) ----------
def test_listening_alignment_finds_each_question_after_its_number():
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
    from listening_timestamps import align
    segs = [{"start": 0, "end": 5, "text": "問題1"}, {"start": 10, "end": 12, "text": "1番"},
            {"start": 13, "end": 20, "text": "男の人と女の人が話しています 男の人はどこへ行きますか"},
            {"start": 21, "end": 30, "text": "すみません 駅はどこですか"},
            {"start": 40, "end": 42, "text": "2番"},
            {"start": 43, "end": 50, "text": "先生が話しています 学生は明日何を持ってきますか"},
            {"start": 51, "end": 60, "text": "辞書を持ってきてください"}, {"start": 70, "end": 72, "text": "問題2"}]
    qs = [{"question_id": "a", "mondai_no": 1, "transcript": "男の人と女の人が話しています。男の人はどこへ行きますか。\n男：すみません、駅はどこですか。"},
          {"question_id": "b", "mondai_no": 1, "transcript": "先生が話しています。学生は明日何を持ってきますか。\n先生：辞書を持ってきてください。"}]
    out = align(qs, segs, 100)
    assert (out["a"]["start"], out["a"]["end"]) == (9.7, 39.7)       # from "1番" to "2番"
    assert (out["b"]["start"], out["b"]["end"]) == (39.7, 70)        # ends where 問題2 starts
