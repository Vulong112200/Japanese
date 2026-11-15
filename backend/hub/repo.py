"""All SQL lives here (repository layer). Functions take a sqlite3 connection."""
import hashlib
import json
import sqlite3
from datetime import datetime, timedelta, timezone

TZ = timezone(timedelta(hours=7))  # learner's timezone (Vietnam)


def now() -> datetime:
    return datetime.now(TZ)


def iso(dt: datetime | None = None) -> str:
    return (dt or now()).isoformat(timespec="seconds")


def sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def rows(cur) -> list[dict]:
    return [dict(r) for r in cur.fetchall()]


# ---------- sources ----------
SOURCE_COLS = ("source_id", "source_type", "name", "location", "url", "reliability", "purpose", "level",
               "size_bytes", "page_count", "duration_seconds", "content_hash", "processing_status",
               "access_status", "checked_at", "imported_at", "record_count", "notes", "error")


def upsert_source(conn: sqlite3.Connection, src: dict) -> None:
    cols = [c for c in SOURCE_COLS if c in src]
    conn.execute(
        f"INSERT INTO sources ({','.join(cols)}) VALUES ({','.join('?' * len(cols))}) "
        f"ON CONFLICT(source_id) DO UPDATE SET {','.join(f'{c}=excluded.{c}' for c in cols if c != 'source_id')}",
        [src[c] for c in cols])


def update_source(conn, source_id: str, **fields) -> None:
    if fields:
        conn.execute(f"UPDATE sources SET {','.join(f'{k}=?' for k in fields)} WHERE source_id=?",
                     [*fields.values(), source_id])


def get_source(conn, source_id: str) -> dict | None:
    r = conn.execute("SELECT * FROM sources WHERE source_id=?", (source_id,)).fetchone()
    return dict(r) if r else None


def list_sources(conn, q: str | None = None, source_type: str | None = None) -> list[dict]:
    sql, args = "SELECT * FROM sources WHERE 1=1", []
    if q:
        sql += " AND (name LIKE ? OR url LIKE ? OR purpose LIKE ? OR source_id LIKE ?)"
        args += [f"%{q}%"] * 4
    if source_type:
        sql += " AND source_type=?"
        args.append(source_type)
    return rows(conn.execute(sql + " ORDER BY source_id", args))


# ---------- raw ----------
def insert_raw(conn, source_id: str, locator: str, content: str, method: str) -> int:
    h = sha256_text(content)
    conn.execute(
        "INSERT OR IGNORE INTO raw_records (source_id, locator, content, content_hash, extraction_method, extracted_at) "
        "VALUES (?,?,?,?,?,?)", (source_id, locator, content, h, method, iso()))
    return conn.execute("SELECT raw_id FROM raw_records WHERE source_id=? AND locator=? AND content_hash=?",
                        (source_id, locator, h)).fetchone()[0]


def raw_by_ids(conn, ids: list[int]) -> list[dict]:
    if not ids:
        return []
    return rows(conn.execute(f"SELECT * FROM raw_records WHERE raw_id IN ({','.join('?' * len(ids))})", ids))


# ---------- issues & review log ----------
def replace_issues(conn, entity_type: str, entity_id: str, issues, origin: str = "rule") -> None:
    conn.execute("DELETE FROM validation_issues WHERE entity_type=? AND entity_id=? AND origin=?",
                 (entity_type, entity_id, origin))
    conn.executemany(
        "INSERT INTO validation_issues (entity_type, entity_id, code, severity, message, suggestion, origin) "
        "VALUES (?,?,?,?,?,?,?)",
        [(entity_type, entity_id, c, s, m, sug, origin) for c, s, m, sug in issues])


def add_issue(conn, entity_type, entity_id, code, severity, message, suggestion=None, origin="rule") -> None:
    conn.execute(
        "INSERT INTO validation_issues (entity_type, entity_id, code, severity, message, suggestion, origin) "
        "VALUES (?,?,?,?,?,?,?)", (entity_type, entity_id, code, severity, message, suggestion, origin))


def issues_for(conn, entity_type: str, entity_id: str) -> list[dict]:
    return rows(conn.execute(
        "SELECT * FROM validation_issues WHERE entity_type=? AND entity_id=? ORDER BY severity, issue_id",
        (entity_type, entity_id)))


def log_action(conn, entity_type, entity_id, action, note, before, after) -> None:
    conn.execute(
        "INSERT INTO review_actions (entity_type, entity_id, action, note, before_json, after_json, acted_at) "
        "VALUES (?,?,?,?,?,?,?)",
        (entity_type, entity_id, action, note, json.dumps(before, ensure_ascii=False),
         json.dumps(after, ensure_ascii=False), iso()))


# ---------- vocabulary ----------
VOCAB_EDITABLE = ("word", "reading", "romaji", "han_viet", "meaning_vi", "part_of_speech", "verb_group",
                  "lesson_number", "topic", "example_jp", "example_romaji", "example_vi", "review_notes")


def get_vocab(conn, vid: str) -> dict | None:
    r = conn.execute("SELECT * FROM vocabulary WHERE id=?", (vid,)).fetchone()
    return dict(r) if r else None


def list_vocab(conn, q=None, lesson=None, status=None, pos=None, deck=None, include_archived=False,
               limit=200, offset=0) -> tuple[list[dict], int]:
    where, args = ["1=1"], []
    if not include_archived:
        where.append("archived=0")
    if q:
        where.append("(word LIKE ? OR reading LIKE ? OR romaji LIKE ? OR meaning_vi LIKE ? OR han_viet LIKE ?)")
        args += [f"%{q}%"] * 5
    if lesson is not None:
        where.append("lesson_number=?")
        args.append(lesson)
    if status:
        where.append("verification_status=?")
        args.append(status)
    if pos:
        where.append("part_of_speech=?")
        args.append(pos)
    if deck:
        where.append("deck=?")
        args.append(deck)
    w = " AND ".join(where)
    total = conn.execute(f"SELECT COUNT(*) FROM vocabulary WHERE {w}", args).fetchone()[0]
    items = rows(conn.execute(
        f"SELECT v.*, (SELECT COUNT(*) FROM validation_issues i WHERE i.entity_type='vocabulary' "
        f"AND i.entity_id=v.id AND i.resolved=0 AND i.severity!='info') AS issue_count "
        f"FROM vocabulary v WHERE {w} ORDER BY COALESCE(lesson_number, 999), id LIMIT ? OFFSET ?",
        [*args, limit, offset]))
    return items, total


def update_vocab(conn, vid: str, **fields) -> None:
    fields["updated_at"] = iso()
    conn.execute(f"UPDATE vocabulary SET {','.join(f'{k}=?' for k in fields)} WHERE id=?", [*fields.values(), vid])


def next_vocab_id(conn) -> str:
    r = conn.execute("SELECT MAX(CAST(SUBSTR(id,5) AS INTEGER)) FROM vocabulary").fetchone()[0]
    return f"VOC_{(r or 0) + 1:06d}"


def vocab_decks(conn) -> list[dict]:
    return rows(conn.execute(
        "SELECT deck, lesson_number, COUNT(*) AS n FROM vocabulary WHERE archived=0 "
        "GROUP BY deck ORDER BY COALESCE(lesson_number, 999), deck"))


# ---------- SRS ----------
def ensure_cards(conn, entity_type: str = "vocabulary") -> int:
    cur = conn.execute(
        "INSERT OR IGNORE INTO srs_cards (entity_type, entity_id, direction) "
        "SELECT 'vocabulary', id, d.direction FROM vocabulary, "
        "(SELECT 'jp_vi' AS direction UNION ALL SELECT 'vi_jp') d "
        "WHERE archived=0 AND verification_status!='rejected'")
    return cur.rowcount


def due_cards(conn, direction: str, new_limit: int = 20, lesson: int | None = None, limit: int = 100) -> list[dict]:
    t = iso()
    lesson_sql, la = ("AND v.lesson_number=?", [lesson]) if lesson is not None else ("", [])
    base = ("SELECT c.*, v.word, v.reading, v.romaji, v.han_viet, v.meaning_vi, v.example_jp, v.example_romaji, "
            "v.example_vi, v.lesson_number, v.deck, v.verification_status, v.verified_by, v.verb_group FROM srs_cards c "
            "JOIN vocabulary v ON v.id=c.entity_id AND c.entity_type='vocabulary' "
            "WHERE v.archived=0 AND v.verification_status!='rejected' AND c.direction=? ")
    due = rows(conn.execute(base + f"AND c.due_at IS NOT NULL AND c.due_at<=? {lesson_sql} ORDER BY c.due_at LIMIT ?",
                            [direction, t, *la, limit]))
    new_today = conn.execute(
        "SELECT COUNT(*) FROM srs_cards WHERE direction=? AND first_studied>=?",
        (direction, iso(now().replace(hour=0, minute=0, second=0, microsecond=0)))).fetchone()[0]
    remaining_new = max(0, new_limit - new_today)
    new = rows(conn.execute(base + f"AND c.due_at IS NULL {lesson_sql} "
                            "ORDER BY COALESCE(v.lesson_number,999), v.id LIMIT ?",
                            [direction, *la, remaining_new])) if remaining_new else []
    return due + new


def get_card(conn, card_id: int) -> dict | None:
    r = conn.execute("SELECT * FROM srs_cards WHERE card_id=?", (card_id,)).fetchone()
    return dict(r) if r else None


def save_card(conn, card_id: int, card, due_at: datetime, rating: str, prev_interval: float, first: bool) -> None:
    t = iso()
    conn.execute(
        "UPDATE srs_cards SET status=?, ease=?, interval_days=?, reps=?, lapses=?, review_count=?, correct_count=?, "
        "incorrect_count=?, last_studied=?, due_at=?, first_studied=COALESCE(first_studied, ?) WHERE card_id=?",
        (card.status, card.ease, card.interval_days, card.reps, card.lapses, card.review_count, card.correct_count,
         card.incorrect_count, t, iso(due_at), t, card_id))
    conn.execute("INSERT INTO review_log (card_id, rating, reviewed_at, prev_interval, new_interval) VALUES (?,?,?,?,?)",
                 (card_id, rating, t, prev_interval, card.interval_days))


def study_streak(conn) -> int:
    days = {r[0] for r in conn.execute("SELECT DISTINCT SUBSTR(reviewed_at,1,10) FROM review_log")}
    d, streak = now().date(), 0
    if d.isoformat() not in days:
        d -= timedelta(days=1)       # streak survives until the end of today
    while d.isoformat() in days:
        streak += 1
        d -= timedelta(days=1)
    return streak


def dashboard(conn) -> dict:
    def kv(sql, *a):
        return {r[0]: r[1] for r in conn.execute(sql, a)}
    today = now().date().isoformat()
    return {
        "level": "N5",
        "vocabulary_by_status": kv("SELECT verification_status, COUNT(*) FROM vocabulary WHERE archived=0 GROUP BY 1"),
        "vocabulary_verified_by": kv("SELECT COALESCE(verified_by,'none'), COUNT(*) FROM vocabulary "
                                     "WHERE archived=0 AND verification_status='verified' GROUP BY 1"),
        "cards_by_status": kv("SELECT status, COUNT(*) FROM srs_cards WHERE direction='jp_vi' GROUP BY 1"),
        "cards_by_status_vi_jp": kv("SELECT status, COUNT(*) FROM srs_cards WHERE direction='vi_jp' GROUP BY 1"),
        "due_now": kv("SELECT direction, COUNT(*) FROM srs_cards WHERE due_at IS NOT NULL AND due_at<=? GROUP BY 1", iso()),
        "reviews_today": conn.execute("SELECT COUNT(*) FROM review_log WHERE reviewed_at>=?", (today,)).fetchone()[0],
        "correct_today": conn.execute("SELECT COUNT(*) FROM review_log WHERE reviewed_at>=? AND rating!='again'",
                                      (today,)).fetchone()[0],
        "streak_days": study_streak(conn),
        "questions_by_status": kv("SELECT verification_status, COUNT(*) FROM questions GROUP BY 1"),
        "exam": exam_stats(conn),
        "grammar_by_status": kv("SELECT verification_status, COUNT(*) FROM grammar GROUP BY 1"),
        "kanji_by_status": kv("SELECT verification_status, COUNT(*) FROM kanji GROUP BY 1"),
        "sources_by_access": kv("SELECT COALESCE(access_status,'unchecked'), COUNT(*) FROM sources GROUP BY 1"),
        "open_issues": kv("SELECT severity, COUNT(*) FROM validation_issues WHERE resolved=0 GROUP BY 1"),
        "weak_lessons": rows(conn.execute(
            "SELECT v.lesson_number, v.deck, SUM(c.incorrect_count) AS wrong, SUM(c.correct_count) AS right "
            "FROM srs_cards c JOIN vocabulary v ON v.id=c.entity_id "
            "WHERE c.review_count>0 GROUP BY v.deck HAVING wrong>0 "
            "ORDER BY CAST(wrong AS REAL)/(wrong+right) DESC LIMIT 5")),
    }


# ---------- exams / questions ----------
def get_question(conn, qid: str) -> dict | None:
    r = conn.execute("SELECT * FROM questions WHERE question_id=?", (qid,)).fetchone()
    return dict(r) if r else None


ENTITY_TABLES = {   # entity -> (table, key column, queue order)
    "vocabulary": ("vocabulary", "id", "COALESCE(lesson_number,999), id"),
    "question": ("questions", "question_id", "section_id, mondai_no, number"),
    "grammar": ("grammar", "id", "COALESCE(lesson_number,999), id"),
    "kanji": ("kanji", "id", "id"),
}


def review_queue(conn, entity: str, status: str | None = None, limit: int = 50, offset: int = 0) -> tuple[list[dict], int]:
    statuses = [status] if status else ["needs_review", "normalized", "extracted"]
    ph = ",".join("?" * len(statuses))
    table, key, order = ENTITY_TABLES[entity]
    where = f"verification_status IN ({ph})" + (" AND archived=0" if table == "vocabulary" else "")
    total = conn.execute(f"SELECT COUNT(*) FROM {table} WHERE {where}", statuses).fetchone()[0]
    items = rows(conn.execute(
        f"SELECT t.*, (SELECT COUNT(*) FROM validation_issues i WHERE i.entity_type=? AND i.entity_id=t.{key} "
        f"AND i.resolved=0 AND i.severity!='info') AS issue_count FROM {table} t WHERE {where} "
        f"ORDER BY issue_count DESC, {order} LIMIT ? OFFSET ?",
        [entity, *statuses, limit, offset]))
    return items, total


# ---------- mock exam (spec Part 9) ----------
LIVE_Q = "verification_status != 'rejected'"


def exam_overview(conn) -> dict:
    exams = rows(conn.execute(
        f"SELECT e.exam_id, e.title, e.exam_type, e.source_type, e.is_official, e.duration_minutes, e.verification_status, "
        f"(SELECT COUNT(*) FROM questions q WHERE q.exam_id=e.exam_id AND q.{LIVE_Q}) AS question_count "
        f"FROM exams e WHERE e.exam_type != 'question_bank' ORDER BY e.exam_id"))
    bank = rows(conn.execute(
        f"SELECT q.section, q.mondai_no, q.mondai_type, e.exam_type, COUNT(*) AS n FROM questions q "
        f"JOIN exams e ON e.exam_id=q.exam_id WHERE q.{LIVE_Q} GROUP BY 1,2,3,4 ORDER BY 1,2"))
    return {"exams": exams, "bank": bank, "mistakes": len(mistake_question_ids(conn))}


def questions_where(conn, exam_id=None, section=None, mondai_type=None, exam_type=None, ids=None) -> list[dict]:
    sql, args = f"SELECT q.* FROM questions q JOIN exams e ON e.exam_id=q.exam_id WHERE q.{LIVE_Q}", []
    for col, val in (("q.exam_id", exam_id), ("q.section", section), ("q.mondai_type", mondai_type),
                     ("e.exam_type", exam_type)):
        if val is not None:
            sql += f" AND {col}=?"
            args.append(val)
    if ids is not None:
        sql += f" AND q.question_id IN ({','.join('?' * len(ids)) or 'NULL'})"
        args += list(ids)
    return rows(conn.execute(sql + " ORDER BY q.section_id, q.mondai_no, q.number, q.question_id", args))


def mistake_question_ids(conn) -> list[str]:
    """Questions whose most recent answer in a submitted attempt was wrong (spec §9.1 Mode E)."""
    last: dict[str, int] = {}
    for qid, ok in conn.execute(
            "SELECT a.question_id, a.is_correct FROM attempt_answers a JOIN exam_attempts t USING (attempt_id) "
            "WHERE t.submitted_at IS NOT NULL AND a.answer IS NOT NULL ORDER BY t.submitted_at, a.answered_at"):
        last[qid] = ok
    return [q for q, ok in last.items() if ok == 0]


def create_attempt(conn, attempt_id: str, exam_id, title: str, mode: str, config: dict) -> None:
    ts = iso()
    conn.execute("INSERT INTO exam_attempts (attempt_id, exam_id, title, mode, config_json, current_section, "
                 "section_started_at, started_at) VALUES (?,?,?,?,?,0,?,?)",
                 (attempt_id, exam_id, title, mode, json.dumps(config, ensure_ascii=False), ts, ts))


def get_attempt(conn, attempt_id: str) -> dict | None:
    r = conn.execute("SELECT * FROM exam_attempts WHERE attempt_id=?", (attempt_id,)).fetchone()
    if not r:
        return None
    a = dict(r)
    a["config"] = json.loads(a.pop("config_json"))
    a["result"] = json.loads(a.pop("result_json")) if a["result_json"] else None
    return a


def list_attempts(conn, limit: int = 50) -> list[dict]:
    out = []
    for r in rows(conn.execute("SELECT * FROM exam_attempts ORDER BY started_at DESC LIMIT ?", (limit,))):
        res = json.loads(r.pop("result_json")) if r["result_json"] else None
        cfg = json.loads(r.pop("config_json"))
        r["question_count"] = sum(len(s["question_ids"]) for s in cfg["sections"])
        r["summary"] = {k: res[k] for k in ("total", "correct", "incorrect", "unanswered", "accuracy")} if res else None
        r["readiness"] = res.get("readiness") if res else None
        out.append(r)
    return out


def attempt_answers(conn, attempt_id: str) -> dict[str, dict]:
    return {r["question_id"]: {"answer": json.loads(r["answer"]) if r["answer"] else None, "flagged": bool(r["flagged"]),
                               "is_correct": r["is_correct"]}
            for r in conn.execute("SELECT * FROM attempt_answers WHERE attempt_id=?", (attempt_id,))}


def save_answer(conn, attempt_id: str, qid: str, answer, flagged: bool, is_correct) -> None:
    conn.execute("INSERT INTO attempt_answers (attempt_id, question_id, answer, flagged, is_correct, answered_at) "
                 "VALUES (?,?,?,?,?,?) ON CONFLICT (attempt_id, question_id) DO UPDATE SET answer=excluded.answer, "
                 "flagged=excluded.flagged, is_correct=excluded.is_correct, answered_at=excluded.answered_at",
                 (attempt_id, qid, json.dumps(answer) if answer else None, int(flagged),
                  None if is_correct is None else int(is_correct), iso()))


def advance_section(conn, attempt_id: str, to_index: int) -> None:
    conn.execute("UPDATE exam_attempts SET current_section=?, section_started_at=? WHERE attempt_id=?",
                 (to_index, iso(), attempt_id))


def finish_attempt(conn, attempt_id: str, result: dict) -> None:
    conn.execute("UPDATE exam_attempts SET submitted_at=?, result_json=? WHERE attempt_id=?",
                 (iso(), json.dumps(result, ensure_ascii=False), attempt_id))


def exam_stats(conn) -> dict:
    last = conn.execute("SELECT attempt_id, title, mode, submitted_at, result_json FROM exam_attempts "
                        "WHERE submitted_at IS NOT NULL ORDER BY submitted_at DESC LIMIT 1").fetchone()
    res = json.loads(last["result_json"]) if last else None
    return {
        "attempts_submitted": conn.execute("SELECT COUNT(*) FROM exam_attempts WHERE submitted_at IS NOT NULL").fetchone()[0],
        "last": {"attempt_id": last["attempt_id"], "title": last["title"], "mode": last["mode"],
                 "submitted_at": last["submitted_at"], "accuracy": res["accuracy"], "correct": res["correct"],
                 "total": res["total"]} if last else None,
        "mistakes_pending": len(mistake_question_ids(conn)),
        "bank_questions": conn.execute(f"SELECT COUNT(*) FROM questions WHERE {LIVE_Q}").fetchone()[0],
    }
