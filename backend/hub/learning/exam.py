"""Mock exam scoring and timing (spec §4.3, §9.3). Pure functions, no DB.

Practice performance (raw counts) and the readiness estimate are kept apart: JLPT uses scaled scores, so the
estimate is a labelled linear approximation, never an official score.
"""
from datetime import datetime

CURRENT_TIMING_MIN = {"vocabulary": 20, "grammar_reading": 40, "listening": 30}   # JLPT N5 timing (spec §4.1)
SECTION_NAMES = {"vocabulary": "言語知識（文字・語彙）", "grammar_reading": "言語知識（文法）・読解", "listening": "聴解"}
SECTION_ORDER = ("vocabulary", "grammar_reading", "listening")
LANGUAGE_KNOWLEDGE = ("vocabulary", "grammar_reading")
PASS = {"total": 80, "language_knowledge_reading": 38, "listening": 19}
GRACE_SEC = 5                     # an answer clicked as the clock hits zero is still saved


def remaining_seconds(duration_sec: int | None, started_at: datetime | None, now: datetime) -> int | None:
    """None = untimed."""
    if duration_sec is None:
        return None
    if started_at is None:
        return duration_sec
    return max(0, duration_sec - int((now - started_at).total_seconds()))


def consensus_status(key: int, solvers: list[int | None]) -> str:
    """ADR-019: a past-paper answer is 'verified' only when the answer key and two independent AI solvers agree.
    No solver results (e.g. the official sample) -> needs_review."""
    return "verified" if len(solvers) >= 2 and all(s == key for s in solvers) else "needs_review"


def is_correct(answer: list[str] | None, correct: list[str]) -> bool | None:
    if not answer:
        return None
    return sorted(answer) == sorted(correct)


def _bucket() -> dict:
    return {"total": 0, "correct": 0, "incorrect": 0, "unanswered": 0}


def _add(b: dict, status: str) -> None:
    b["total"] += 1
    b[status] += 1


def _finish(b: dict) -> dict:
    b["accuracy"] = round(100 * b["correct"] / b["total"], 1) if b["total"] else None
    return b


def score(questions: list[dict], answers: dict[str, list[str] | None]) -> dict:
    """questions: {question_id, section, mondai_no, mondai_type, correct_answer, lesson_number?};
    answers: question_id -> list of option ids (missing/None = unanswered). Unanswered counts as not correct."""
    total, by_section, by_mondai, lessons, per_q = _bucket(), {}, {}, {}, {}
    for q in questions:
        ok = is_correct(answers.get(q["question_id"]), q["correct_answer"])
        status = "unanswered" if ok is None else "correct" if ok else "incorrect"
        per_q[q["question_id"]] = status
        _add(total, status)
        _add(by_section.setdefault(q["section"], _bucket()), status)
        key = f"{q['section']}:{q.get('mondai_no')}"
        m = by_mondai.setdefault(key, {**_bucket(), "section": q["section"], "mondai_no": q.get("mondai_no"),
                                       "mondai_type": q.get("mondai_type")})
        _add(m, status)
        if q.get("lesson_number") is not None:
            _add(lessons.setdefault(q["lesson_number"], _bucket()), status)
    weak = sorted(({"lesson_number": k, **_finish(v)} for k, v in lessons.items() if v["correct"] < v["total"]),
                  key=lambda x: (x["accuracy"], -x["total"]))
    return {
        **_finish(total),
        "by_section": {k: _finish(v) for k, v in sorted(by_section.items(),
                                                       key=lambda kv: SECTION_ORDER.index(kv[0]) if kv[0] in SECTION_ORDER else 9)},
        "by_mondai": [_finish(v) for _, v in sorted(by_mondai.items(), key=lambda kv: (
            SECTION_ORDER.index(kv[1]["section"]) if kv[1]["section"] in SECTION_ORDER else 9, kv[1]["mondai_no"] or 0))],
        "listening_accuracy": by_section["listening"]["accuracy"] if "listening" in by_section else None,
        "weak_vocabulary_lessons": weak[:5],
        "weak_grammar_points": [],          # no question targets a grammar point yet (grammar bank: next phase)
        "per_question": per_q,
    }


def readiness(by_section: dict) -> dict:
    """Linear estimate on the JLPT N5 scale. Sections absent from the attempt stay None."""
    def part(sections, scale):
        t = sum(by_section[s]["total"] for s in sections if s in by_section)
        c = sum(by_section[s]["correct"] for s in sections if s in by_section)
        return (round(scale * c / t), t) if t else (None, 0)
    lk, lk_n = part(LANGUAGE_KNOWLEDGE, 120)
    li, li_n = part(("listening",), 60)
    notes = []
    if lk is None:
        notes.append("Lượt này không có phần Kiến thức ngôn ngữ + Đọc.")
    if li is None:
        notes.append("Lượt này không có phần Nghe.")
    if 0 < lk_n + li_n < 30:
        notes.append(f"Chỉ có {lk_n + li_n} câu, ước lượng rất thô.")
    both = lk is not None and li is not None
    return {
        "label": "Ước lượng mức sẵn sàng (không phải điểm JLPT chính thức)",
        "language_knowledge_reading": lk, "listening": li, "total": lk + li if both else None,
        "likely_pass": (lk + li >= PASS["total"] and lk >= PASS["language_knowledge_reading"]
                        and li >= PASS["listening"]) if both else None,
        "thresholds": PASS,
        "notes": notes,
        "disclaimer": "JLPT dùng điểm quy đổi (scaled score). Con số này chỉ quy tỉ lệ câu đúng ra thang 120/60 "
                      "để tham khảo, không phải điểm thi thật.",
    }


if __name__ == "__main__":
    from datetime import timedelta
    t0 = datetime(2026, 1, 1)
    assert remaining_seconds(None, t0, t0) is None and remaining_seconds(60, t0, t0 + timedelta(seconds=70)) == 0
    qs = [{"question_id": "a", "section": "vocabulary", "mondai_no": 1, "correct_answer": ["1"], "lesson_number": 3},
          {"question_id": "b", "section": "vocabulary", "mondai_no": 1, "correct_answer": ["2"], "lesson_number": 3},
          {"question_id": "c", "section": "listening", "mondai_no": 1, "correct_answer": ["3"]}]
    s = score(qs, {"a": ["1"], "b": ["1"]})
    assert (s["correct"], s["incorrect"], s["unanswered"]) == (1, 1, 1) and s["listening_accuracy"] == 0.0
    r = readiness(s["by_section"])
    assert r["language_knowledge_reading"] == 60 and r["listening"] == 0 and r["likely_pass"] is False
    print("ok")
