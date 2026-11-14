"""HTTP API (thin layer: validation of input, then repo / pipeline / srs)."""
import json
import os
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

from . import repo
from .db import DEFAULT_DB, ROOT, connect
from .ingestion import flashcards_csv as fc
from .ingestion import pipeline
from .learning import srs

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
        return pipeline.import_sample_exam(conn)
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
    v["history"] = repo.rows(conn.execute(
        "SELECT action, note, acted_at FROM review_actions WHERE entity_type='vocabulary' AND entity_id=? "
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
    repo.update_vocab(conn, vid, **fields)
    # an edited item must be re-checked by a human; drop to needs_review then re-run rules
    repo.update_vocab(conn, vid, verification_status="needs_review")
    pipeline.revalidate_vocab(conn, vid)
    repo.update_vocab(conn, vid, verification_status="needs_review")
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
def review_queue(entity: Literal["vocabulary", "question"] = "vocabulary", status: str | None = None,
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


@router.get("/questions/{qid}")
def question(qid: str, conn=Depends(get_conn)):
    return question_detail(conn, qid)


class ReviewDecision(BaseModel):
    action: Literal["approve", "reject", "edit", "ambiguous", "reextract"]
    note: str | None = Field(None, max_length=2000)
    force: bool = False              # approve despite unresolved error-level issues
    edit: VocabEdit | None = None


@router.post("/review/{entity}/{entity_id}")
def review(entity: Literal["vocabulary", "question"], entity_id: str, body: ReviewDecision, conn=Depends(get_conn)):
    table, key = ("vocabulary", "id") if entity == "vocabulary" else ("questions", "question_id")
    before = conn.execute(f"SELECT * FROM {table} WHERE {key}=?", (entity_id,)).fetchone()
    if not before:
        raise HTTPException(404)
    before = dict(before)

    def set_status(status: str, notes: str | None = None) -> None:
        conn.execute(f"UPDATE {table} SET verification_status=?, review_notes=COALESCE(?, review_notes) WHERE {key}=?",
                     (status, notes, entity_id))

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
                              verification_status="normalized")
            pipeline.revalidate_vocab(conn, entity_id)
        else:
            set_status("needs_review", body.note)
            repo.add_issue(conn, entity, entity_id, "reextract_requested", "warning",
                           body.note or "Người dùng yêu cầu chép lại từ ảnh trang gốc", origin="user")
    after = dict(conn.execute(f"SELECT * FROM {table} WHERE {key}=?", (entity_id,)).fetchone())
    repo.log_action(conn, entity, entity_id, body.action, body.note, before, after)
    conn.commit()
    return vocab_detail(conn, entity_id) if entity == "vocabulary" else question_detail(conn, entity_id)


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
