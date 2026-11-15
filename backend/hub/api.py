"""HTTP API (thin layer: validation of input, then repo / pipeline / srs)."""
import json
import os
import random
from datetime import datetime
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

from . import repo
from .db import DEFAULT_DB, ROOT, connect
from .ingestion import flashcards_csv as fc
from .ingestion import pipeline
from .learning import exam as examlib
from .learning import srs
from .validation import reference as ref

_conn = None


def get_conn():
    global _conn
    if _conn is None:
        _conn = connect(os.environ.get("HUB_DB", DEFAULT_DB))
    return _conn


def set_conn(conn) -> None:
    """Used by tests to inject an isolated database."""
    global _conn
    _conn = conn


router = APIRouter(prefix="/api")
JSON_FIELDS = ("topic", "source_ids", "raw_ids", "options", "correct_answer", "extra_json", "data_json")


def decode(d: dict | None) -> dict | None:
    if d:
        for k in JSON_FIELDS:
            if isinstance(d.get(k), str):
                d[k] = json.loads(d[k])
    return d


# ---------- sources ----------
class UrlSource(BaseModel):
    url: str = Field(pattern=r"^https?://")
    name: str = Field(min_length=1, max_length=200)
    source_type: Literal["website", "google_drive", "google_doc", "notebooklm", "youtube", "other"] = "website"
    reliability: Literal["OFFICIAL", "PRIMARY", "EDUCATIONAL", "SUPPLEMENTARY", "AI_GENERATED", "USER_CREATED"] = "EDUCATIONAL"
    purpose: str | None = None


@router.get("/sources")
def sources(q: str | None = None, source_type: str | None = None, conn=Depends(get_conn)):
    return repo.list_sources(conn, q, source_type)


@router.post("/sources", status_code=201)
def add_source(body: UrlSource, conn=Depends(get_conn)):
    if conn.execute("SELECT 1 FROM sources WHERE url=?", (body.url,)).fetchone():
        raise HTTPException(409, "URL đã được đăng ký")
    n = conn.execute("SELECT COUNT(*) FROM sources WHERE source_id LIKE 'SRC_USER_%'").fetchone()[0]
    sid = f"SRC_USER_{n + 1:03d}"
    repo.upsert_source(conn, {**body.model_dump(), "source_id": sid, "processing_status": "registered",
                              "access_status": "unchecked", "level": "N5"})
    conn.commit()
    return repo.get_source(conn, sid)


@router.post("/sources/scan")
def scan(conn=Depends(get_conn)):
    return {"files": pipeline.inventory(conn)}


@router.post("/sources/check-online")
def check_online(conn=Depends(get_conn)):
    return pipeline.check_online(conn)


@router.post("/sources/{source_id}/reprocess")
def reprocess(source_id: str, conn=Depends(get_conn)):
    s = repo.get_source(conn, source_id)
    if not s:
        raise HTTPException(404)
    if source_id.startswith("SRC_LOCAL_FC_"):
        return pipeline.import_flashcards(conn, ROOT / Path(s["location"]).parent)
    if source_id.startswith("SRC_LOCAL_N5_"):
        return pipeline.import_exam(conn)
    if source_id.startswith("SRC_DRIVE_EXAM_"):
        return pipeline.import_past_exams(conn)
    raise HTTPException(400, "Nguồn này chưa có bộ xử lý tự động (cần nhập thủ công hoặc export)")


@router.get("/sources/export")
def export_sources(conn=Depends(get_conn)):
    return JSONResponse(repo.list_sources(conn),
                        headers={"Content-Disposition": "attachment; filename=sources.json"})


@router.get("/sources/{source_id}")
def source_detail(source_id: str, conn=Depends(get_conn)):
    s = repo.get_source(conn, source_id)
    if not s:
        raise HTTPException(404)
    s["raw_count"] = conn.execute("SELECT COUNT(*) FROM raw_records WHERE source_id=?", (source_id,)).fetchone()[0]
    s["vocabulary_count"] = conn.execute("SELECT COUNT(*) FROM vocabulary WHERE source_ids LIKE ?",
                                         (f'%"{source_id}"%',)).fetchone()[0]
    s["question_count"] = conn.execute("SELECT COUNT(*) FROM questions WHERE source_ids LIKE ?",
                                       (f'%"{source_id}"%',)).fetchone()[0]
    return s


# ---------- vocabulary ----------
@router.get("/vocabulary")
def vocabulary(q: str | None = None, lesson: int | None = None, status: str | None = None, pos: str | None = None,
               deck: str | None = None, limit: int = Query(100, le=1000), offset: int = 0, conn=Depends(get_conn)):
    items, total = repo.list_vocab(conn, q, lesson, status, pos, deck, limit=limit, offset=offset)
    return {"total": total, "items": [decode(i) for i in items]}


@router.get("/vocabulary/decks")
def decks(conn=Depends(get_conn)):
    return repo.vocab_decks(conn)


def vocab_detail(conn, vid: str) -> dict:
    v = decode(repo.get_vocab(conn, vid))
    if not v:
        raise HTTPException(404)
    v["raw"] = repo.raw_by_ids(conn, v["raw_ids"])
    v["issues"] = repo.issues_for(conn, "vocabulary", vid)
    v["sources"] = [repo.get_source(conn, s) for s in v["source_ids"]]
    v["dictionary"] = {"reading": ref.check_reading(v["word"], v["reading"] or ""),
                       "han_viet": ref.check_han_viet(v["word"], v["han_viet"])} if ref.available() else None
    v["history"] = repo.rows(conn.execute(
        "SELECT action, note, acted_at, before_json, after_json FROM review_actions "
        "WHERE entity_type='vocabulary' AND entity_id=? "
        "ORDER BY action_id DESC", (vid,)))
    return v


@router.get("/vocabulary/{vid}")
def vocabulary_item(vid: str, conn=Depends(get_conn)):
    return vocab_detail(conn, vid)


class VocabEdit(BaseModel):
    word: str | None = None
    reading: str | None = None
    romaji: str | None = None
    han_viet: str | None = None
    meaning_vi: str | None = None
    part_of_speech: str | None = None
    verb_group: Literal[1, 2, 3] | None = None
    lesson_number: int | None = None
    example_jp: str | None = None
    example_romaji: str | None = None
    example_vi: str | None = None
    review_notes: str | None = None


def apply_edit(conn, vid: str, edit: VocabEdit, note: str | None) -> dict:
    before = repo.get_vocab(conn, vid)
    if not before:
        raise HTTPException(404)
    fields = edit.model_dump(exclude_unset=True)
    if not fields:
        raise HTTPException(400, "Không có thay đổi")
    # an item edited by hand waits for the user's own approval (automation will not re-verify it)
    repo.update_vocab(conn, vid, **fields, verification_status="needs_review", verified_by="pending_user")
    pipeline.revalidate_vocab(conn, vid)
    repo.log_action(conn, "vocabulary", vid, "edit", note, before, repo.get_vocab(conn, vid))
    conn.commit()
    return vocab_detail(conn, vid)


@router.patch("/vocabulary/{vid}")
def edit_vocabulary(vid: str, body: VocabEdit, conn=Depends(get_conn)):
    return apply_edit(conn, vid, body, "Chỉnh sửa trực tiếp")


@router.post("/vocabulary/{vid}/archive")
def archive_vocabulary(vid: str, conn=Depends(get_conn)):
    v = repo.get_vocab(conn, vid)
    if not v:
        raise HTTPException(404)
    repo.update_vocab(conn, vid, archived=0 if v["archived"] else 1)
    repo.log_action(conn, "vocabulary", vid, "unarchive" if v["archived"] else "archive", None, v, None)
    conn.commit()
    return {"id": vid, "archived": not v["archived"]}


# ---------- data review ----------
@router.get("/review/queue")
def review_queue(entity: Literal["vocabulary", "question", "grammar", "kanji"] = "vocabulary", status: str | None = None,
                 limit: int = Query(50, le=500), offset: int = 0, conn=Depends(get_conn)):
    items, total = repo.review_queue(conn, entity, status, limit, offset)
    return {"total": total, "items": [decode(i) for i in items]}


def question_detail(conn, qid: str) -> dict:
    q = decode(repo.get_question(conn, qid))
    if not q:
        raise HTTPException(404)
    q["issues"] = repo.issues_for(conn, "question", qid)
    q["raw"] = repo.raw_by_ids(conn, [q["extra_json"].get("raw_id")] if q["extra_json"].get("raw_id") else [])
    q["passage"] = dict(r) if q["passage_id"] and (r := conn.execute(
        "SELECT * FROM passages WHERE passage_id=?", (q["passage_id"],)).fetchone()) else None
    q["page_asset_id"] = f"IMG_N5_MONDAI_P{q['source_page']:03d}" if q["source_page"] else None
    return q


def grammar_detail(conn, gid: str) -> dict:
    g = conn.execute("SELECT * FROM grammar WHERE id=?", (gid,)).fetchone()
    if not g:
        raise HTTPException(404)
    g = dict(g)
    g.update(json.loads(g.pop("data_json")))
    g["source_ids"] = json.loads(g["source_ids"])
    g["issues"] = repo.issues_for(conn, "grammar", gid)
    return g


def kanji_detail(conn, kid: str) -> dict:
    k = conn.execute("SELECT * FROM kanji WHERE id=? OR kanji=?", (kid, kid)).fetchone()
    if not k:
        raise HTTPException(404)
    k = dict(k)
    for f in ("onyomi", "kunyomi", "example_words", "source_ids"):
        k[f] = json.loads(k[f])
    k["issues"] = repo.issues_for(conn, "kanji", k["id"])
    return k


@router.get("/grammar")
def grammar_list(q: str | None = None, lesson: int | None = None, conn=Depends(get_conn)):
    sql, args = "SELECT id, pattern, lesson_number, grammar_name_vi, meaning_vi, origin, verification_status, verified_by "                 "FROM grammar WHERE 1=1", []
    if q:
        sql += " AND (pattern LIKE ? OR grammar_name_vi LIKE ? OR meaning_vi LIKE ? OR data_json LIKE ?)"
        args += [f"%{q}%"] * 4
    if lesson is not None:
        sql += " AND lesson_number=?"
        args.append(lesson)
    return repo.rows(conn.execute(sql + " ORDER BY COALESCE(lesson_number, 999), id", args))


@router.get("/grammar/{gid}")
def grammar_item(gid: str, conn=Depends(get_conn)):
    return grammar_detail(conn, gid)


@router.get("/kanji")
def kanji_list(conn=Depends(get_conn)):
    out = repo.rows(conn.execute("SELECT * FROM kanji ORDER BY id"))
    for k in out:
        for f in ("onyomi", "kunyomi", "example_words", "source_ids"):
            k[f] = json.loads(k[f])
    return out


@router.get("/kanji/{kid}")
def kanji_item(kid: str, conn=Depends(get_conn)):
    return kanji_detail(conn, kid)


@router.get("/questions/{qid}")
def question(qid: str, conn=Depends(get_conn)):
    return question_detail(conn, qid)


DETAIL = {"vocabulary": lambda c, i: vocab_detail(c, i), "question": lambda c, i: question_detail(c, i),
          "grammar": lambda c, i: grammar_detail(c, i), "kanji": lambda c, i: kanji_detail(c, i)}


class ReviewDecision(BaseModel):
    action: Literal["approve", "reject", "edit", "ambiguous", "reextract"]
    note: str | None = Field(None, max_length=2000)
    force: bool = False              # approve despite unresolved error-level issues
    edit: VocabEdit | None = None


@router.post("/review/{entity}/{entity_id}")
def review(entity: Literal["vocabulary", "question", "grammar", "kanji"], entity_id: str, body: ReviewDecision,
           conn=Depends(get_conn)):
    table, key, _ = repo.ENTITY_TABLES[entity]
    before = conn.execute(f"SELECT * FROM {table} WHERE {key}=?", (entity_id,)).fetchone()
    if not before:
        raise HTTPException(404)
    before = dict(before)

    def set_status(status: str, notes: str | None = None) -> None:
        conn.execute(f"UPDATE {table} SET verification_status=?, verified_by='user', "
                     f"review_notes=COALESCE(?, review_notes) WHERE {key}=?", (status, notes, entity_id))

    if body.action == "approve":
        errors = conn.execute("SELECT COUNT(*) FROM validation_issues WHERE entity_type=? AND entity_id=? "
                              "AND resolved=0 AND severity='error'", (entity, entity_id)).fetchone()[0]
        if errors and not body.force:
            raise HTTPException(409, f"Còn {errors} lỗi mức error chưa xử lý; sửa trước hoặc gửi force=true")
        set_status("verified", body.note)
        conn.execute("UPDATE validation_issues SET resolved=1 WHERE entity_type=? AND entity_id=?", (entity, entity_id))
    elif body.action == "reject":
        set_status("rejected", body.note)
    elif body.action == "ambiguous":
        set_status("needs_review", f"AMBIGUOUS: {body.note or ''}".strip())
        repo.add_issue(conn, entity, entity_id, "ambiguous", "warning", body.note or "Đánh dấu mơ hồ", origin="user")
    elif body.action == "edit":
        if entity != "vocabulary" or not body.edit:
            raise HTTPException(400, "Sửa trực tiếp hiện chỉ hỗ trợ từ vựng (gửi kèm 'edit')")
        return apply_edit(conn, entity_id, body.edit, body.note)
    elif body.action == "reextract":
        if entity == "vocabulary":
            raw = repo.raw_by_ids(conn, json.loads(before["raw_ids"]))
            row = json.loads(raw[0]["content"]) if raw else None
            fields = fc.parse_back(row[1]) if row and len(row) > 1 else None
            if not fields:
                raise HTTPException(422, "Không trích xuất lại được từ bản ghi RAW")
            repo.update_vocab(conn, entity_id, word=row[0].strip(), reading=fields["reading"],
                              romaji=fields.get("romaji"), han_viet=fields.get("han_viet"),
                              meaning_vi=fields["meaning_vi"], example_jp=fields.get("example_jp"),
                              example_romaji=fields.get("example_romaji"), example_vi=fields.get("example_vi"),
                              verification_status="needs_review", verified_by="pending_user")
            pipeline.revalidate_vocab(conn, entity_id)
        else:
            set_status("needs_review", body.note)
            repo.add_issue(conn, entity, entity_id, "reextract_requested", "warning",
                           body.note or "Người dùng yêu cầu chép lại từ ảnh trang gốc", origin="user")
    after = dict(conn.execute(f"SELECT * FROM {table} WHERE {key}=?", (entity_id,)).fetchone())
    repo.log_action(conn, entity, entity_id, body.action, body.note, before, after)
    conn.commit()
    return DETAIL[entity](conn, entity_id)


# ---------- SRS ----------
@router.get("/srs/due")
def srs_due(direction: Literal["jp_vi", "vi_jp"] = "jp_vi", new_limit: int = Query(20, ge=0, le=200),
            lesson: int | None = None, conn=Depends(get_conn)):
    return repo.due_cards(conn, direction, new_limit, lesson)


class Answer(BaseModel):
    rating: Literal["again", "hard", "good", "easy"]


@router.post("/srs/cards/{card_id}/answer")
def srs_answer(card_id: int, body: Answer, conn=Depends(get_conn)):
    row = repo.get_card(conn, card_id)
    if not row:
        raise HTTPException(404)
    card = srs.Card(**{k: row[k] for k in ("ease", "interval_days", "reps", "lapses", "review_count",
                                            "correct_count", "incorrect_count", "status")})
    new, due = srs.schedule(card, body.rating, repo.now())
    repo.save_card(conn, card_id, new, due, body.rating, row["interval_days"], row["first_studied"] is None)
    conn.commit()
    return repo.get_card(conn, card_id)


@router.get("/stats/dashboard")
def stats(conn=Depends(get_conn)):
    return repo.dashboard(conn)


# ---------- mock exam (spec Part 9, 10) ----------
PUBLIC_EXTRA = ("target", "star_position", "options_are_glyph_images", "options_are_pictures", "options_audio_only",
                "has_illustration")
REVEAL_EXTRA = ("option_explanations", "expected_sequence", "expected_sequence_note", "grammar_id", "grammar_pattern")


SOURCE_EXAM_TYPE = {"official": "official_sample", "past": "past_exam", "generated": "question_bank"}


class AttemptStart(BaseModel):
    mode: Literal["exam", "practice"] = "exam"
    exam_id: str | None = None                       # Mode A/B: a stored exam, original order
    section: Literal["vocabulary", "grammar_reading", "listening"] | None = None   # Mode C
    mondai_type: str | None = Field(None, max_length=50)                              # Mode D
    source: Literal["all", "official", "past", "generated"] = "all"
    mistakes_only: bool = False                      # Mode E
    limit: int = Field(20, ge=1, le=200)             # Mode F
    timing: Literal["none", "original", "current", "custom"] = "original"
    time_limit_min: int | None = Field(None, ge=1, le=300)


class AnswerSave(BaseModel):
    answer: list[str] | None = Field(None, max_length=4)
    flagged: bool = False


def _sections_for(questions: list[dict], body: AttemptStart, exam: dict | None) -> list[dict]:
    """Group questions by section (exam order) and freeze each section's time limit."""
    meta = {s["section_id"]: s for s in (exam or {}).get("sections", [])}
    groups: dict[str, list[dict]] = {}
    for q in questions:
        groups.setdefault(q["section"], []).append(q)
    order = sorted(groups, key=lambda s: examlib.SECTION_ORDER.index(s) if s in examlib.SECTION_ORDER else 9)
    total = len(questions)
    out = []
    for s in order:
        qs = groups[s]
        m = meta.get(qs[0]["section_id"], {})
        if body.mode == "practice" or body.timing == "none":
            dur = None
        elif body.timing == "original":
            dur = m["duration_minutes"] * 60 if m.get("duration_minutes") else None   # historical paper: as recorded
        elif body.timing == "current":
            dur = examlib.CURRENT_TIMING_MIN.get(s, 30) * 60
        else:
            dur = round(body.time_limit_min * 60 * len(qs) / total)
        out.append({"section_id": qs[0]["section_id"] or s, "section": s,
                    "name": m.get("name") or examlib.SECTION_NAMES.get(s, s), "duration_sec": dur,
                    "question_ids": [q["question_id"] for q in qs]})
    return out


@router.get("/exams")
def exams(conn=Depends(get_conn)):
    return repo.exam_overview(conn)


@router.post("/attempts", status_code=201)
def start_attempt(body: AttemptStart, conn=Depends(get_conn)):
    if body.timing == "custom" and not body.time_limit_min:
        raise HTTPException(422, "timing=custom cần time_limit_min")
    exam = None
    if body.exam_id:
        row = conn.execute("SELECT * FROM exams WHERE exam_id=?", (body.exam_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Không có đề này")
        exam = json.loads(row["data_json"])
        qs = repo.questions_where(conn, exam_id=body.exam_id, section=body.section)
        title = row["title"] + (f" · {examlib.SECTION_NAMES.get(body.section, body.section)}" if body.section else "")
    else:
        ids = repo.mistake_question_ids(conn) if body.mistakes_only else None
        qs = repo.questions_where(conn, section=body.section, mondai_type=body.mondai_type, ids=ids,
                                  exam_type=SOURCE_EXAM_TYPE.get(body.source))
        qs = sorted(random.sample(qs, min(body.limit, len(qs))), key=lambda q: (
            examlib.SECTION_ORDER.index(q["section"]) if q["section"] in examlib.SECTION_ORDER else 9,
            q["mondai_no"] or 0, q["exam_id"], q["number"] or 0))
        parts = ["Ôn câu sai" if body.mistakes_only else "Luyện tập",
                 examlib.SECTION_NAMES.get(body.section or "", ""), body.mondai_type or ""]
        title = " · ".join(p for p in parts if p) + f" ({len(qs)} câu)"
    if not qs:
        raise HTTPException(404, "Không có câu hỏi phù hợp")
    attempt_id = f"ATT_{repo.now():%Y%m%d_%H%M%S}_{os.urandom(2).hex()}"
    config = {"filter": body.model_dump(), "sections": _sections_for(qs, body, exam)}
    repo.create_attempt(conn, attempt_id, body.exam_id, title, body.mode, config)
    conn.commit()
    return attempt_view(conn, attempt_id)


@router.get("/attempts")
def attempts(conn=Depends(get_conn)):
    return repo.list_attempts(conn)


def _section_of(a: dict, qid: str) -> int:
    return next((i for i, s in enumerate(a["config"]["sections"]) if qid in s["question_ids"]), -1)


def _remaining(a: dict) -> int | None:
    if a["mode"] != "exam" or a["submitted_at"]:
        return None
    sec = a["config"]["sections"][a["current_section"]]
    return examlib.remaining_seconds(sec["duration_sec"], datetime.fromisoformat(a["section_started_at"]), repo.now())


def public_question(q: dict, reveal: bool) -> dict:
    q = decode(q)
    extra = q.get("extra_json") or {}
    out = {k: q[k] for k in ("question_id", "exam_id", "section", "section_id", "mondai_no", "mondai_type", "number",
                             "question_text", "instruction", "passage_id", "options", "answer_type", "audio_asset_id",
                             "image_asset_id", "explanation_origin", "verification_status")}
    out["extra"] = {k: extra[k] for k in PUBLIC_EXTRA if k in extra}
    out["lesson_number"] = extra.get("lesson_number")
    if reveal:
        out.update(correct_answer=q["correct_answer"], explanation_vi=q["explanation_vi"], transcript=q["transcript"])
        out["extra"].update({k: extra[k] for k in REVEAL_EXTRA if k in extra})
    elif extra.get("options_audio_only"):       # choices exist only in the audio: never show their text in advance
        out["options"] = [{"option_id": o["option_id"], "text": ""} for o in out["options"]]
    return out


def attempt_view(conn, attempt_id: str) -> dict:
    a = repo.get_attempt(conn, attempt_id)
    if not a:
        raise HTTPException(404)
    answers = repo.attempt_answers(conn, attempt_id)
    ids = [qid for s in a["config"]["sections"] for qid in s["question_ids"]]
    by_id = {q["question_id"]: q for q in repo.questions_where(conn, ids=ids)}
    by_id.update({r["question_id"]: dict(r) for r in conn.execute(      # rejected after the attempt: keep history
        f"SELECT * FROM questions WHERE question_id IN ({','.join('?' * len(ids))})", ids) if r["question_id"] not in by_id})
    done = bool(a["submitted_at"])

    def reveal(qid):
        return done or (a["mode"] == "practice" and bool((answers.get(qid) or {}).get("answer")))
    questions = [public_question(dict(by_id[q]), reveal(q)) for q in ids if q in by_id]
    if not done and a["mode"] == "exam":
        answers = {k: {**v, "is_correct": None} for k, v in answers.items()}
    pids = {q["passage_id"] for q in questions if q["passage_id"]}
    passages = {r["passage_id"]: dict(r) for r in conn.execute(
        f"SELECT passage_id, text, image_asset_id FROM passages WHERE passage_id IN ({','.join('?' * len(pids)) or 'NULL'})",
        list(pids))}
    cur = a["current_section"]
    sections = [{**s, "status": "done" if done or (a["mode"] == "exam" and i < cur) else
                 "current" if a["mode"] == "practice" or i == cur else "upcoming"}
                for i, s in enumerate(a["config"]["sections"])]
    return {**{k: a[k] for k in ("attempt_id", "exam_id", "title", "mode", "started_at", "submitted_at",
                                 "current_section", "result")},
            "filter": a["config"]["filter"], "sections": sections, "remaining_sec": _remaining(a),
            "questions": questions, "passages": passages, "answers": answers}


@router.get("/attempts/{attempt_id}")
def attempt(attempt_id: str, conn=Depends(get_conn)):
    return attempt_view(conn, attempt_id)


def _open_attempt(conn, attempt_id: str) -> dict:
    a = repo.get_attempt(conn, attempt_id)
    if not a:
        raise HTTPException(404)
    if a["submitted_at"]:
        raise HTTPException(409, "Bài đã nộp")
    return a


@router.put("/attempts/{attempt_id}/answers/{qid}")
def save_answer(attempt_id: str, qid: str, body: AnswerSave, conn=Depends(get_conn)):
    a = _open_attempt(conn, attempt_id)
    idx = _section_of(a, qid)
    if idx < 0:
        raise HTTPException(404, "Câu hỏi không thuộc lượt thi này")
    prev = repo.attempt_answers(conn, attempt_id).get(qid, {})
    if a["mode"] == "exam":
        if idx != a["current_section"]:
            raise HTTPException(409, "Phần này đã đóng" if idx < a["current_section"] else "Phần này chưa bắt đầu")
        sec = a["config"]["sections"][idx]
        started = datetime.fromisoformat(a["section_started_at"])
        if sec["duration_sec"] is not None and (repo.now() - started).total_seconds() > sec["duration_sec"] + examlib.GRACE_SEC:
            raise HTTPException(409, "Hết giờ cho phần này")
    elif prev.get("answer") and body.answer != prev["answer"]:
        raise HTTPException(409, "Chế độ luyện tập: đã trả lời câu này")
    q = repo.get_question(conn, qid)
    options = {o["option_id"] for o in json.loads(q["options"])}
    if body.answer and not set(body.answer) <= options:
        raise HTTPException(422, "Lựa chọn không hợp lệ")
    ok = examlib.is_correct(body.answer, json.loads(q["correct_answer"]))
    repo.save_answer(conn, attempt_id, qid, body.answer, body.flagged, ok)
    conn.commit()
    out = {"question_id": qid, "answer": body.answer, "flagged": body.flagged}
    if a["mode"] == "practice" and body.answer:
        out.update(is_correct=ok, question=public_question(dict(q), True))
    return out


@router.post("/attempts/{attempt_id}/advance")
def advance(attempt_id: str, conn=Depends(get_conn)):
    a = _open_attempt(conn, attempt_id)
    if a["mode"] != "exam":
        raise HTTPException(409, "Chỉ chế độ thi mới chia phần")
    if a["current_section"] + 1 >= len(a["config"]["sections"]):
        raise HTTPException(409, "Đây là phần cuối; hãy nộp bài")
    repo.advance_section(conn, attempt_id, a["current_section"] + 1)
    conn.commit()
    return attempt_view(conn, attempt_id)


@router.post("/attempts/{attempt_id}/submit")
def submit(attempt_id: str, conn=Depends(get_conn)):
    a = _open_attempt(conn, attempt_id)
    ids = [qid for s in a["config"]["sections"] for qid in s["question_ids"]]
    qs = []
    for r in conn.execute(f"SELECT * FROM questions WHERE question_id IN ({','.join('?' * len(ids))})", ids):
        q = decode(dict(r))
        extra = q["extra_json"] or {}
        qs.append({**q, **{k: extra.get(k) for k in ("lesson_number", "grammar_id", "grammar_pattern")}})
    answers = {k: v["answer"] for k, v in repo.attempt_answers(conn, attempt_id).items()}
    result = examlib.score(qs, answers)
    result["readiness"] = examlib.readiness(result["by_section"])
    repo.finish_attempt(conn, attempt_id, result)
    conn.commit()
    return attempt_view(conn, attempt_id)


# ---------- assets ----------
@router.get("/assets/{asset_id}")
def asset(asset_id: str, conn=Depends(get_conn)):
    a = conn.execute("SELECT * FROM assets WHERE asset_id=?", (asset_id,)).fetchone()
    if not a:
        raise HTTPException(404)
    path = (ROOT / a["file_path"]).resolve()
    if ROOT not in path.parents or not path.is_file():   # never serve outside the project
        raise HTTPException(404, "Tệp không tồn tại")
    return FileResponse(path, media_type=a["mime_type"])   # Starlette handles Range requests (audio seek)


def create_app() -> FastAPI:
    app = FastAPI(title="Japanese N5 Learning Hub")
    app.include_router(router)
    dist = ROOT / "frontend" / "dist"
    if dist.exists():
        @app.get("/{path:path}", include_in_schema=False)
        def spa(path: str):
            f = (dist / path).resolve()
            if path and dist in f.parents and f.is_file():
                return FileResponse(f)
            return FileResponse(dist / "index.html")
    return app


app = create_app()
