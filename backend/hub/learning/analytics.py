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
        names = {"vocabulary": "từ vựng", "grammar": "ngữ pháp", "kanji": "kanji", "number": "số đếm"}
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



WEAK_HALF_LIFE_DAYS = 7     # a mistake counts half as much after a week
WEAK_MAX_PER_POINT = 5      # questions per grammar point in the weak-point drill
WEAK_RESOLVED_STREAK = 2    # correct answers in a row after the last mistake -> point dropped


def weak_points(history: list[dict], now: datetime) -> list[dict]:
    """Recency-aware grammar weak points (ADR-033). history: [{grammar_id, pattern, correct, t}] (any order).
    A point stays in the drill while its recent answers are wrong: base = 2 + recency-weighted mistakes (max 5);
    after the last mistake 1 correct answer halves it ("improving"), 2 in a row drop it ("resolved")."""
    by: dict[str, list[dict]] = {}
    for e in sorted(history, key=lambda e: e["t"]):
        by.setdefault(e["grammar_id"], []).append(e)
    out = []
    for gid, ev in by.items():
        wrong_at = [i for i, e in enumerate(ev) if not e["correct"]]
        if not wrong_at:
            continue
        streak = len(ev) - 1 - wrong_at[-1]
        weight = sum(0.5 ** ((now - datetime.fromisoformat(ev[i]["t"])).total_seconds() / 86400 / WEAK_HALF_LIFE_DAYS)
                     for i in wrong_at)
        base = min(WEAK_MAX_PER_POINT, 2 + round(weight))
        need = base if streak == 0 else max(1, base // 2) if streak < WEAK_RESOLVED_STREAK else 0
        out.append({"grammar_id": gid, "pattern": ev[-1].get("pattern"), "wrong": len(wrong_at), "total": len(ev),
                    "streak": streak, "weight": round(weight, 2), "need": need, "last_wrong_at": ev[wrong_at[-1]]["t"],
                    "status": "weak" if streak == 0 else "improving" if need else "resolved"})
    return sorted(out, key=lambda x: (-x["need"], -x["weight"], x["grammar_id"]))
