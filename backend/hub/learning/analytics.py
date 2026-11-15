"""Study-time estimate and next-activity recommendations (pure functions, spec §13, §14, ADR-022)."""
from datetime import datetime

GAP_CAP = 300   # seconds; a longer pause between two answers starts a new study session


def active_seconds(timestamps: list[str], gap_cap: int = GAP_CAP) -> int:
    """Sum of gaps between consecutive answers that are <= gap_cap.
    ponytail: time before the first answer of a session (reading the first card/question) is not counted;
    add explicit session start/stop events if the estimate proves too low."""
    ts = sorted(datetime.fromisoformat(t) for t in timestamps)
    return int(sum(g for g in ((b - a).total_seconds() for a, b in zip(ts, ts[1:])) if g <= gap_cap))


def recommend(d: dict) -> list[dict]:
    """d: {due: {vocabulary, grammar, kanji}, mistakes_pending, weak_grammar_points: [{grammar_id, pattern, correct,
    total}], days_since_last_exam: int | None, new_cards_left: int}. Ordered by priority; nothing without data."""
    out = []
    due = {k: v for k, v in d["due"].items() if v}
    if due:
        names = {"vocabulary": "từ vựng", "grammar": "ngữ pháp", "kanji": "kanji"}
        top = max(due, key=due.get)
        out.append({"kind": "srs_due", "title": f"Ôn {sum(due.values())} thẻ đến hạn",
                    "reason": " · ".join(f"{names[k]} {v}" for k, v in due.items()) + " — để quá hạn sẽ dễ quên",
                    "href": f"#/flashcards?entity={top}"})
    if d["mistakes_pending"]:
        out.append({"kind": "mistakes", "title": f"Làm lại {d['mistakes_pending']} câu sai",
                    "reason": "Lần trả lời gần nhất của các câu này còn sai", "start": {"mode": "practice",
                                                                                      "mistakes_only": True,
                                                                                      "limit": 200}})
    if d["weak_grammar_points"]:
        w = d["weak_grammar_points"][0]
        out.append({"kind": "grammar_point", "title": f"Luyện ngữ pháp {w['pattern'] or w['grammar_id']}",
                    "reason": f"Điểm ngữ pháp yếu nhất: đúng {w['correct']}/{w['total']} câu gần nhất",
                    "start": {"mode": "practice", "grammar_id": w["grammar_id"], "limit": 10}})
    if d["days_since_last_exam"] is None or d["days_since_last_exam"] >= 7:
        out.append({"kind": "exam", "title": "Làm một đề thi thử",
                    "reason": "Chưa nộp lượt thi nào" if d["days_since_last_exam"] is None
                    else f"Lượt thi gần nhất cách đây {d['days_since_last_exam']} ngày", "href": "#/exam"})
    if not due and d["new_cards_left"]:
        out.append({"kind": "srs_new", "title": "Học thẻ mới",
                    "reason": f"Còn {d['new_cards_left']} thẻ chưa học, hôm nay không có thẻ đến hạn",
                    "href": "#/flashcards"})
    return out

