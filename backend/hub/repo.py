"""All SQL lives here (repository layer). Functions take a sqlite3 connection."""
import hashlib
import json
import sqlite3
from datetime import datetime, timedelta, timezone

from .learning.analytics import active_seconds

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
# Grammar and kanji cards have one direction (pattern/character -> meaning), stored as 'jp_vi' (ADR-021).
SRS_ENTITIES = {   # entity -> (columns, table alias + join, active filter, new-card order)
    "vocabulary": ("v.word, v.reading, v.romaji, v.han_viet, v.meaning_vi, v.example_jp, v.example_romaji, "
                   "v.example_vi, v.lesson_number, v.deck, v.verification_status, v.verified_by, v.verb_group",
                   "vocabulary v ON v.id=c.entity_id", "v.archived=0 AND v.verification_status!='rejected'",
                   "COALESCE(v.lesson_number,999), v.id"),
    "grammar": ("g.pattern, g.grammar_name_vi, g.meaning_vi, g.formation, g.data_json, g.lesson_number, "
                "g.verification_status", "grammar g ON g.id=c.entity_id", "g.verification_status!='rejected'",
                "COALESCE(g.lesson_number,999), g.id"),
    "kanji": ("k.kanji, k.han_viet, k.meaning_vi, k.onyomi, k.kunyomi, k.example_words, k.verification_status",
              "kanji k ON k.id=c.entity_id", "k.verification_status!='rejected'", "k.id"),
    "number": ("n.jp, n.reading, n.romaji, n.meaning_vi, n.category, n.data_json, n.verification_status, "
               "(SELECT title_vi FROM number_categories WHERE key=n.category) AS category_vi",
               "numbers n ON n.id=c.entity_id", "n.verification_status!='rejected' AND n.irregular=1", "n.position"),
}


def ensure_cards(conn) -> int:
    n = conn.execute(
        "INSERT OR IGNORE INTO srs_cards (entity_type, entity_id, direction) "
        "SELECT 'vocabulary', id, d.direction FROM vocabulary, "
        "(SELECT 'jp_vi' AS direction UNION ALL SELECT 'vi_jp') d "
        "WHERE archived=0 AND verification_status!='rejected'").rowcount
    for entity, table, extra in (("grammar", "grammar", ""), ("kanji", "kanji", ""),
                                 ("number", "numbers", " AND irregular=1")):   # numbers: only forms to memorise
        n += conn.execute(f"INSERT OR IGNORE INTO srs_cards (entity_type, entity_id, direction) "
                          f"SELECT '{entity}', id, 'jp_vi' FROM {table} "
                          f"WHERE verification_status!='rejected'{extra}").rowcount
    return n


def _card_view(r: dict) -> dict:
    if "data_json" in r:                       # only what the card shows
        data = json.loads(r.pop("data_json"))
        if "pattern" in r:                     # grammar
            r["examples"] = data.get("examples", [])[:2]
        else:                                  # number (ADR-029)
            r.update({k: data.get(k) for k in ("alt_readings", "note_vi", "example_jp", "example_vi")})
    for k in ("onyomi", "kunyomi", "example_words"):
        if k in r:
            r[k] = json.loads(r[k])
    return r


def _srs_base(entity: str, lesson_from: int | None, lesson_to: int | None) -> tuple[str, list, str]:
    """SELECT ... WHERE active AND entity AND direction AND lesson range; params after: [entity, direction, *lesson]."""
    cols, join, active, order = SRS_ENTITIES[entity]
    alias = join.split()[1]
    sql = (f"SELECT c.*, {cols} FROM srs_cards c JOIN {join} AND c.entity_type=? "
           f"WHERE {active} AND c.direction=? ")
    la: list = []
    if entity in ("vocabulary", "grammar") and (lesson_from is not None or lesson_to is not None):   # kanji have no lesson
        sql += f"AND {alias}.lesson_number BETWEEN ? AND ? "
        la = [lesson_from if lesson_from is not None else 0, lesson_to if lesson_to is not None else 999]
    return sql, la, order


def due_cards(conn, direction: str, new_limit: int = 20, lesson_from: int | None = None,
              lesson_to: int | None = None, limit: int = 1000, entity: str = "vocabulary",
              shuffle: bool = False) -> list[dict]:
    base, la, order = _srs_base(entity, lesson_from, lesson_to)
    due = rows(conn.execute(base + "AND c.due_at IS NOT NULL AND c.due_at<=? ORDER BY c.due_at LIMIT ?",
                            [entity, direction, *la, iso(), limit]))
    new_today = conn.execute(
        "SELECT COUNT(*) FROM srs_cards WHERE entity_type=? AND direction=? AND first_studied>=?",
        (entity, direction, iso(now().replace(hour=0, minute=0, second=0, microsecond=0)))).fetchone()[0]
    remaining_new = max(0, new_limit - new_today)
    new = rows(conn.execute(base + f"AND c.due_at IS NULL ORDER BY {'RANDOM()' if shuffle else order} LIMIT ?",
                            [entity, direction, *la, remaining_new])) if remaining_new else []
    return [_card_view(r) for r in due + new]


CRAM_SOURCES = {   # source -> (extra filter, order): off-schedule review before the exam (ADR-027)
    "studied": ("AND c.first_studied IS NOT NULL ", "RANDOM()"),
    # forgotten at least once and not recalled in cram since the last "again"
    "weak": ("AND c.incorrect_count>0 AND (c.weak_cleared_at IS NULL OR c.weak_cleared_at <= (SELECT MAX(reviewed_at) "
             "FROM review_log WHERE card_id=c.card_id AND rating='again')) ",
             "c.lapses + c.incorrect_count DESC, RANDOM()"),
    "all": ("", "RANDOM()"),
}


def cram_cards(conn, entity: str, direction: str, source: str, n: int,
               lesson_from: int | None = None, lesson_to: int | None = None) -> list[dict]:
    base, la, _ = _srs_base(entity, lesson_from, lesson_to)
    where, order = CRAM_SOURCES[source]
    return [_card_view(r) for r in rows(conn.execute(base + where + f"ORDER BY {order} LIMIT ?",
                                                     [entity, direction, *la, n]))]


def clear_weak(conn, card_id: int) -> None:
    """Cram "Nhớ": drop the card from the "weak" list until it is forgotten again; SM-2 schedule untouched."""
    conn.execute("UPDATE srs_cards SET weak_cleared_at=? WHERE card_id=?", (iso(), card_id))


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


# Study activity = SRS reviews + answered exam/practice questions (ADR-022).
ACTIVITY_SQL = ("SELECT reviewed_at AS t, 'review' AS kind, rating!='again' AS ok FROM review_log "
                "UNION ALL SELECT answered_at, 'answer', is_correct FROM attempt_answers "
                "WHERE answer IS NOT NULL AND answered_at IS NOT NULL")


def activity(conn, since: str = "") -> list[dict]:
    """[{t, kind, ok}] since an ISO date/time; is_correct stays NULL until the attempt is submitted."""
    return rows(conn.execute(f"SELECT * FROM ({ACTIVITY_SQL}) WHERE t>=? ORDER BY t", (since,)))


def study_streak(conn) -> int:
    days = {r[0] for r in conn.execute(f"SELECT DISTINCT SUBSTR(t,1,10) FROM ({ACTIVITY_SQL})")}
    d, streak = now().date(), 0
    if d.isoformat() not in days:
        d -= timedelta(days=1)       # streak survives until the end of today
    while d.isoformat() in days:
        streak += 1
        d -= timedelta(days=1)
    return streak


VOC = "entity_type='vocabulary'"


def dashboard(conn) -> dict:
    def kv(sql, *a):
        return {r[0]: r[1] for r in conn.execute(sql, a)}
    today = now().date().isoformat()
    return {
        "level": "N5",
        "vocabulary_by_status": kv("SELECT verification_status, COUNT(*) FROM vocabulary WHERE archived=0 GROUP BY 1"),
        "vocabulary_verified_by": kv("SELECT COALESCE(verified_by,'none'), COUNT(*) FROM vocabulary "
                                     "WHERE archived=0 AND verification_status='verified' GROUP BY 1"),
        "cards_by_status": kv(f"SELECT status, COUNT(*) FROM srs_cards WHERE {VOC} AND direction='jp_vi' GROUP BY 1"),
        "cards_by_status_vi_jp": kv(f"SELECT status, COUNT(*) FROM srs_cards WHERE {VOC} AND direction='vi_jp' GROUP BY 1"),
        "due_now": kv(f"SELECT direction, COUNT(*) FROM srs_cards WHERE {VOC} AND due_at IS NOT NULL AND due_at<=? "
                      "GROUP BY 1", iso()),
        "cards_by_entity": {e: kv("SELECT status, COUNT(*) FROM srs_cards WHERE entity_type=? AND direction='jp_vi' "
                                  "GROUP BY 1", e) for e in SRS_ENTITIES},
        "due_by_entity": kv("SELECT entity_type, COUNT(*) FROM srs_cards WHERE due_at IS NOT NULL AND due_at<=? "
                            "GROUP BY 1", iso()),
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
            "FROM srs_cards c JOIN vocabulary v ON v.id=c.entity_id AND c.entity_type='vocabulary' "
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


def questions_where(conn, exam_id=None, section=None, mondai_type=None, exam_type=None, ids=None,
                    grammar_id=None, grammar_lessons=None) -> list[dict]:
    sql, args = f"SELECT q.* FROM questions q JOIN exams e ON e.exam_id=q.exam_id WHERE q.{LIVE_Q}", []
    if grammar_lessons:     # (lo, hi); points with no lesson count as 26. Passages excluded: never split a passage
        sql += (" AND q.passage_id IS NULL AND json_extract(q.extra_json,'$.grammar_id') IN "
                "(SELECT id FROM grammar WHERE COALESCE(lesson_number, 26) BETWEEN ? AND ?)")
        args += list(grammar_lessons)
    for col, val in (("q.exam_id", exam_id), ("q.section", section), ("q.mondai_type", mondai_type),
                     ("e.exam_type", exam_type), ("json_extract(q.extra_json,'$.grammar_id')", grammar_id)):
        if val is not None:
            sql += f" AND {col}=?"
            args.append(val)
    if ids is not None:
        sql += f" AND q.question_id IN ({','.join('?' * len(ids)) or 'NULL'})"
        args += list(ids)
    return rows(conn.execute(sql + " ORDER BY q.section_id, q.mondai_no, q.number, q.question_id", args))


def latest_answers(conn) -> dict[str, dict]:
    """Most recent answer of each question across submitted attempts: qid -> {answer, is_correct}."""
    return {r["question_id"]: {"answer": json.loads(r["answer"]), "is_correct": r["is_correct"]}
            for r in conn.execute(
                "SELECT a.question_id, a.answer, a.is_correct FROM attempt_answers a JOIN exam_attempts t "
                "USING (attempt_id) WHERE t.submitted_at IS NOT NULL AND a.answer IS NOT NULL "
                "ORDER BY t.submitted_at, a.answered_at, a.rowid")}   # rowid: same-second ties


def mistake_question_ids(conn) -> list[str]:
    """Questions whose most recent answer in a submitted attempt was wrong (spec §9.1 Mode E)."""
    return [q for q, a in latest_answers(conn).items() if a["is_correct"] == 0]


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
    for r in rows(conn.execute("SELECT * FROM exam_attempts ORDER BY started_at DESC, rowid DESC LIMIT ?", (limit,))):
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
                        "WHERE submitted_at IS NOT NULL ORDER BY submitted_at DESC, rowid DESC LIMIT 1").fetchone()
    res = json.loads(last["result_json"]) if last else None
    return {
        "attempts_submitted": conn.execute("SELECT COUNT(*) FROM exam_attempts WHERE submitted_at IS NOT NULL").fetchone()[0],
        "last": {"attempt_id": last["attempt_id"], "title": last["title"], "mode": last["mode"],
                 "submitted_at": last["submitted_at"], "accuracy": res["accuracy"], "correct": res["correct"],
                 "total": res["total"]} if last else None,
        "mistakes_pending": len(mistake_question_ids(conn)),
        "bank_questions": conn.execute(f"SELECT COUNT(*) FROM questions WHERE {LIVE_Q}").fetchone()[0],
    }


# ---------- settings ----------
def get_setting(conn, key: str, default: str) -> str:
    r = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    return r[0] if r else default


def set_setting(conn, key: str, value: str) -> None:
    conn.execute("INSERT INTO settings (key, value) VALUES (?,?) ON CONFLICT (key) DO UPDATE SET value=excluded.value",
                 (key, value))


# ---------- analytics (spec §14) ----------
def daily_activity(conn, days: int = 30) -> list[dict]:
    """One row per local day (oldest first): reviews/answers with correct counts and estimated active seconds."""
    start = now().date() - timedelta(days=days - 1)
    out = {(start + timedelta(days=i)).isoformat(): {"reviews": 0, "reviews_correct": 0, "answers": 0,
                                                    "answers_correct": 0, "ts": []} for i in range(days)}
    for e in activity(conn, start.isoformat()):
        d = out.get(e["t"][:10])
        if d is None:
            continue
        d["ts"].append(e["t"])
        k = "reviews" if e["kind"] == "review" else "answers"
        d[k] += 1
        d[k + "_correct"] += bool(e["ok"])
    return [{"date": k, **{f: v for f, v in d.items() if f != "ts"}, "seconds": active_seconds(d["ts"])}
            for k, d in out.items()]


def srs_retention(conn, since: str) -> dict:
    """entity_type -> {reviews, remembered, retention%} over review_log since a date (rating != again)."""
    out = {}
    for r in conn.execute("SELECT c.entity_type, COUNT(*), SUM(l.rating!='again') FROM review_log l "
                          "JOIN srs_cards c USING (card_id) WHERE l.reviewed_at>=? GROUP BY 1", (since,)):
        out[r[0]] = {"reviews": r[1], "remembered": r[2], "retention": round(100 * r[2] / r[1], 1)}
    return out


def attempt_trend(conn, limit: int = 30) -> list[dict]:
    """Submitted attempts oldest first with accuracy per section (exam history over time)."""
    out = []
    for r in conn.execute("SELECT attempt_id, title, mode, submitted_at, result_json FROM exam_attempts "
                          "WHERE submitted_at IS NOT NULL ORDER BY submitted_at DESC, rowid DESC LIMIT ?", (limit,)):
        res = json.loads(r["result_json"])
        out.append({"attempt_id": r["attempt_id"], "title": r["title"], "mode": r["mode"],
                    "submitted_at": r["submitted_at"], "accuracy": res["accuracy"], "total": res["total"],
                    "by_section": {k: v["accuracy"] for k, v in res["by_section"].items()}})
    return out[::-1]


def repeated_mistakes(conn, min_wrong: int = 2, limit: int = 20) -> list[dict]:
    """Questions answered wrong at least min_wrong times across submitted attempts."""
    return rows(conn.execute(
        "SELECT a.question_id, COUNT(*) AS wrong, q.section, q.mondai_type, q.question_text, "
        "json_extract(q.extra_json,'$.grammar_id') AS grammar_id, "
        "json_extract(q.extra_json,'$.grammar_pattern') AS grammar_pattern FROM attempt_answers a "
        "JOIN exam_attempts t USING (attempt_id) JOIN questions q USING (question_id) "
        "WHERE t.submitted_at IS NOT NULL AND a.is_correct=0 GROUP BY a.question_id HAVING wrong>=? "
        "ORDER BY wrong DESC, a.question_id LIMIT ?", (min_wrong, limit)))
