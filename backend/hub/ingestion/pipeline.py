"""Import pipeline: inventory local files, register online sources, import flashcards, import the sample exam.
Original files are only read; derived files go to data/raw/<source_id>/."""
import hashlib
import json
import re
import shutil
import subprocess
import urllib.error
import urllib.request
from pathlib import Path

from .. import repo
from ..db import ROOT
from ..validation import vocabulary as vrules
from . import flashcards_csv as fc

EXAM_DIR = ROOT / "docs" / "N5" / "Exam"
FLASHCARD_DIR = ROOT / "docs" / "N5" / "flashcards"
ONLINE_SOURCES = ROOT / "data" / "sources_online.json"
EXAM_JSON = ROOT / "data" / "normalized" / "exams" / "EXAM_N5_OFFICIAL_SAMPLE.json"
EXAM_AI_REVIEW = ROOT / "data" / "normalized" / "exams" / "EXAM_N5_OFFICIAL_SAMPLE.ai_review.json"
RAW_DIR = ROOT / "data" / "raw"

TYPE_BY_EXT = {".pdf": "pdf", ".mp3": "audio", ".wav": "audio", ".m4a": "audio", ".csv": "csv", ".json": "json",
               ".txt": "text", ".docx": "docx", ".doc": "doc", ".xlsx": "xlsx", ".xls": "xls", ".html": "html",
               ".zip": "zip", ".png": "image", ".jpg": "image", ".jpeg": "image"}
EXAM_FILES = {"N5-mondai.pdf": "SRC_LOCAL_N5_MONDAI", "N5-seikai.pdf": "SRC_LOCAL_N5_SEIKAI",
              "N5-script.pdf": "SRC_LOCAL_N5_SCRIPT", "N5-kaitou.pdf": "SRC_LOCAL_N5_KAITOU",
              "N5Sample.mp3": "SRC_LOCAL_N5_AUDIO"}
EXAM_PURPOSE = {"SRC_LOCAL_N5_MONDAI": "問題例 – đề mẫu N5", "SRC_LOCAL_N5_SEIKAI": "正解 – bảng đáp án",
                "SRC_LOCAL_N5_SCRIPT": "聴解スクリプト – script phần nghe",
                "SRC_LOCAL_N5_KAITOU": "解答用紙 – phiếu trả lời", "SRC_LOCAL_N5_AUDIO": "Audio phần nghe (1 track)"}


def rel(p: Path) -> str:
    try:
        return p.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return p.resolve().as_posix()


def source_id_for(path: Path) -> str:
    if path.name in EXAM_FILES:
        return EXAM_FILES[path.name]
    stem = path.stem.removeprefix("flashcards_")
    m = re.fullmatch(r"Bai(\d+)", stem)
    if m:
        return f"SRC_LOCAL_FC_BAI{int(m.group(1)):02d}"
    if "Kaiwa" in stem:
        return "SRC_LOCAL_FC_KAIWA"
    if "Số Đếm" in stem or "So Dem" in stem:
        return "SRC_LOCAL_FC_SODEM"
    return "SRC_LOCAL_" + hashlib.sha1(rel(path).encode()).hexdigest()[:8].upper()


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def audio_duration(path: Path) -> float | None:
    if not shutil.which("ffprobe"):
        return None
    try:
        out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                              str(path)], capture_output=True, text=True, timeout=30)
        return round(float(out.stdout.strip()), 2)
    except (ValueError, subprocess.SubprocessError):
        return None


def pdf_pages(path: Path) -> int | None:
    import pymupdf
    with pymupdf.open(path) as d:
        return len(d)


# ---------------- inventory ----------------
def inventory(conn, dirs=(EXAM_DIR, FLASHCARD_DIR)) -> list[dict]:
    """Register every supported file. Records size, hash, pages/duration. Flags exact duplicates."""
    report = []
    seen: dict[str, str] = {r["content_hash"]: r["source_id"] for r in repo.list_sources(conn) if r["content_hash"]}
    for d in dirs:
        if not Path(d).exists():
            report.append({"location": rel(Path(d)), "error": "directory not accessible"})
            continue
        for p in sorted(Path(d).rglob("*")):
            if not p.is_file():
                continue
            kind = TYPE_BY_EXT.get(p.suffix.lower())
            sid = source_id_for(p)
            entry = {"source_id": sid, "name": p.name, "location": rel(p), "size_bytes": p.stat().st_size,
                     "source_type": kind or "unsupported"}
            try:
                h = file_sha256(p)
                entry["content_hash"] = h
                if kind == "pdf":
                    entry["page_count"] = pdf_pages(p)
                if kind == "audio":
                    entry["duration_seconds"] = audio_duration(p)
                dup = seen.get(h)
                existing = repo.get_source(conn, sid)
                notes = f"Trùng nội dung với {dup}" if dup and dup != sid else None
                reliability = ("OFFICIAL" if sid in EXAM_PURPOSE else
                               "USER_CREATED" if sid.startswith("SRC_LOCAL_FC_") else "PRIMARY")
                src = {**entry, "reliability": reliability, "access_status": "local", "level": "N5",
                       "purpose": EXAM_PURPOSE.get(sid) or ("Flashcard do người dùng xuất" if kind == "csv" else None),
                       "notes": notes}
                if sid in EXAM_PURPOSE:
                    src["notes"] = ("Bộ 問題例 N5 (khớp định dạng mẫu trên jlpt.jp) – cần người dùng xác nhận nguồn gốc."
                                    + (f" {notes}" if notes else ""))
                if not existing or existing["content_hash"] != h:
                    src["processing_status"] = "pending" if kind else "failed"
                    if not kind:
                        src["error"] = f"Định dạng {p.suffix} chưa hỗ trợ"
                repo.upsert_source(conn, src)
                seen.setdefault(h, sid)
                entry["duplicate_of"] = dup if dup and dup != sid else None
            except Exception as e:  # keep going; record the failure on the source
                entry["error"] = str(e)
                repo.upsert_source(conn, {**entry, "reliability": "PRIMARY", "processing_status": "failed",
                                          "access_status": "local", "error": str(e)})
            report.append(entry)
    conn.commit()
    return report


# ---------------- online sources ----------------
AUTH_TYPES = {"google_drive": "requires_auth", "google_doc": "requires_auth", "notebooklm": "manual_export"}


def register_online(conn) -> int:
    items = json.loads(ONLINE_SOURCES.read_text(encoding="utf-8"))
    for s in items:
        existing = repo.get_source(conn, s["source_id"])
        repo.upsert_source(conn, {**s, "level": "N5",
                                  "processing_status": existing["processing_status"] if existing else "registered",
                                  "access_status": existing["access_status"] if existing else "unchecked"})
    conn.commit()
    return len(items)


def check_url(url: str, timeout: float = 15) -> tuple[str, str]:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; LearningHub/0.1)"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read(200_000).decode("utf-8", "replace")
            js_only = len(re.sub(r"<script.*?</script>|<[^>]+>|\s+", "", body, flags=re.S)) < 300
            return "accessible", f"HTTP {r.status}" + ("; nội dung chủ yếu render bằng JavaScript" if js_only else "")
    except urllib.error.HTTPError as e:
        return ("requires_auth" if e.code in (401, 403) else "unreachable"), f"HTTP {e.code}"
    except Exception as e:
        return "unreachable", type(e).__name__ + ": " + str(e)[:120]


def check_online(conn, checker=check_url) -> list[dict]:
    out = []
    for s in repo.list_sources(conn):
        if not s["url"]:
            continue
        status, detail = checker(s["url"])
        forced = AUTH_TYPES.get(s["source_type"])
        if forced:  # page may load, but the learning content needs the user's account or an export
            detail += f"; nội dung cần {'đăng nhập Google' if forced == 'requires_auth' else 'export thủ công'}"
            status = forced
        repo.update_source(conn, s["source_id"], access_status=status, checked_at=repo.iso(),
                           notes=f"Kiểm tra truy cập: {detail}. Chưa trích xuất nội dung.")
        out.append({"source_id": s["source_id"], "access_status": status, "detail": detail})
    conn.commit()
    return out


# ---------------- flashcards ----------------
def _norm(s: str | None) -> str:
    return re.sub(r"\s+", "", s or "")


def import_flashcards(conn, directory: Path = FLASHCARD_DIR) -> dict:
    stats = {"files": 0, "rows": 0, "vocabulary_new": 0, "merged": 0, "unstructured": 0, "skipped_existing": 0}
    known_raw = set()
    by_key: dict[tuple, str] = {}
    for v in repo.rows(conn.execute("SELECT id, word, reading, meaning_vi, raw_ids FROM vocabulary")):
        known_raw.update(json.loads(v["raw_ids"]))
        by_key[(_norm(v["word"]), _norm(v["reading"]), _norm(v["meaning_vi"]))] = v["id"]

    for path in sorted(Path(directory).glob("*.csv")):
        sid = source_id_for(path)
        if not repo.get_source(conn, sid):
            inventory(conn, [path.parent])
        repo.update_source(conn, sid, processing_status="extracting")
        deck, lesson, topics = fc.deck_info(path)
        stats["files"] += 1
        count = 0
        try:
            for i, row in enumerate(fc.read_rows(path), start=1):
                stats["rows"] += 1
                content = json.dumps(row, ensure_ascii=False)
                raw_id = repo.insert_raw(conn, sid, f"row:{i}", content, "csv_row")
                if raw_id in known_raw:
                    stats["skipped_existing"] += 1
                    count += 1
                    continue
                fields = fc.parse_back(row[1]) if len(row) >= 2 else None
                if not fields:
                    stats["unstructured"] += 1
                    repo.replace_issues(conn, "raw", str(raw_id), [(
                        "unstructured_format", "info",
                        "Dòng dạng hỏi–đáp tự do, không phải mục từ vựng; giữ ở lớp RAW, chưa chuẩn hoá.", None)])
                    continue
                v = {"word": row[0].strip(), **fields, "part_of_speech": fc.guess_pos(row[0].strip()),
                     "lesson_number": lesson, "deck": deck}
                key = (_norm(v["word"]), _norm(v["reading"]), _norm(v["meaning_vi"]))
                if key in by_key:  # exact same item in another deck/row: merge provenance
                    ex = repo.get_vocab(conn, by_key[key])
                    repo.update_vocab(conn, ex["id"],
                                      source_ids=json.dumps(sorted(set(json.loads(ex["source_ids"])) | {sid})),
                                      raw_ids=json.dumps(sorted(set(json.loads(ex["raw_ids"])) | {raw_id})))
                    stats["merged"] += 1
                else:
                    vid = repo.next_vocab_id(conn)
                    conn.execute(
                        "INSERT INTO vocabulary (id, word, reading, romaji, han_viet, meaning_vi, part_of_speech, "
                        "lesson_number, deck, topic, example_jp, example_romaji, example_vi, source_ids, raw_ids, "
                        "updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        (vid, v["word"], v["reading"], v.get("romaji"), v.get("han_viet"), v["meaning_vi"],
                         v["part_of_speech"], lesson, deck, json.dumps(topics, ensure_ascii=False),
                         v.get("example_jp"), v.get("example_romaji"), v.get("example_vi"),
                         json.dumps([sid]), json.dumps([raw_id]), repo.iso()))
                    by_key[key] = vid
                    stats["vocabulary_new"] += 1
                known_raw.add(raw_id)
                count += 1
            repo.update_source(conn, sid, processing_status="needs_review", record_count=count,
                               imported_at=repo.iso(), error=None)
        except Exception as e:
            repo.update_source(conn, sid, processing_status="failed", error=str(e))
    revalidate_all(conn)
    repo.ensure_cards(conn)
    conn.commit()
    return stats


def revalidate_vocab(conn, vid: str, dupes: dict[str, list[str]] | None = None) -> list:
    v = repo.get_vocab(conn, vid)
    issues = vrules.validate(v)
    others = [o for o in (dupes or {}).get(_norm(v["word"]), []) if o != vid]
    if others:
        diff_reading = [o for o in others if _norm(repo.get_vocab(conn, o)["reading"]) != _norm(v["reading"])]
        if diff_reading:
            issues.append(("duplicate_reading_conflict", "warning",
                           f"Cùng từ '{v['word']}' nhưng cách đọc khác ở: {', '.join(diff_reading)}", None))
        else:
            issues.append(("duplicate_same_word", "info",
                           f"Từ '{v['word']}' còn xuất hiện ở {', '.join(others)} với nghĩa diễn đạt khác "
                           "(có thể là đa nghĩa hoặc trùng lặp)", None))
    repo.replace_issues(conn, "vocabulary", vid, issues)
    if v["verification_status"] == "verified":   # human decision stands; re-runs must not reopen issues
        conn.execute("UPDATE validation_issues SET resolved=1 WHERE entity_type='vocabulary' AND entity_id=?", (vid,))
    if v["verification_status"] not in ("verified", "rejected"):
        other_open = conn.execute(
            "SELECT COUNT(*) FROM validation_issues WHERE entity_type='vocabulary' AND entity_id=? "
            "AND origin!='rule' AND resolved=0 AND severity!='info'", (vid,)).fetchone()[0]
        repo.update_vocab(conn, vid, verification_status="needs_review" if other_open else vrules.status_for(issues))
    return issues


def revalidate_all(conn) -> None:
    dupes: dict[str, list[str]] = {}
    for r in conn.execute("SELECT id, word FROM vocabulary WHERE archived=0"):
        dupes.setdefault(_norm(r["word"]), []).append(r["id"])
    for vid in [r[0] for r in conn.execute("SELECT id FROM vocabulary")]:
        revalidate_vocab(conn, vid, dupes)


# ---------------- sample exam ----------------
def render_pages(pdf: Path, source_id: str, dpi: int = 130) -> list[str]:
    import pymupdf
    out_dir = RAW_DIR / source_id / "pages"
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    with pymupdf.open(pdf) as d:
        for i, page in enumerate(d, start=1):
            target = out_dir / f"p{i:03d}.png"
            if not target.exists():          # derived file; never overwrite once rendered
                page.get_pixmap(dpi=dpi).save(target)
            paths.append(rel(target))
    return paths


def import_sample_exam(conn, exam_json: Path = EXAM_JSON, exam_dir: Path | None = None) -> dict:
    exam_dir = exam_dir or next(EXAM_DIR.rglob("N5-mondai.pdf")).parent
    data = json.loads(exam_json.read_text(encoding="utf-8"))
    inventory(conn, [exam_dir])
    pages: dict[str, list[str]] = {}
    for fname, sid in EXAM_FILES.items():
        f = exam_dir / fname
        if f.suffix == ".pdf":
            repo.update_source(conn, sid, processing_status="extracting")
            pages[sid] = render_pages(f, sid)
            with __import__("pymupdf").open(f) as d:
                for i, pg in enumerate(d, start=1):
                    repo.insert_raw(conn, sid, f"page:{i}", pg.get_text() or "",
                                    "pdf_text_layer (incomplete: CID fonts without ToUnicode)")
            for i, p in enumerate(pages[sid], start=1):
                conn.execute("INSERT OR REPLACE INTO assets (asset_id, source_id, kind, file_path, mime_type, page_number, notes) "
                             "VALUES (?,?,?,?,?,?,?)", (f"IMG_{sid[10:]}_P{i:03d}", sid, "image", p, "image/png", i,
                                                         "Ảnh render trang gốc (lớp RAW)"))
    audio = exam_dir / "N5Sample.mp3"
    conn.execute("INSERT OR REPLACE INTO assets (asset_id, source_id, kind, file_path, mime_type, duration_seconds, "
                 "transcript_status, notes) VALUES (?,?,?,?,?,?,?,?)",
                 ("AUD_N5S_001", "SRC_LOCAL_N5_AUDIO", "audio", rel(audio), "audio/mpeg", audio_duration(audio),
                  "official_script_transcribed_needs_review",
                  "Một track cho toàn bộ phần nghe; chưa có timestamp từng câu."))

    key = data["answer_key"]
    official = {**{f"Q_N5S_V{i:02d}": a for i, a in enumerate(key["vocabulary"], 1)},
                **{f"Q_N5S_G{i:02d}": a for i, a in enumerate(key["grammar_reading"], 1)},
                **{f"Q_N5S_L{m}_{i}": a for m, arr in key["listening"].items() for i, a in enumerate(arr, 1)}}
    ai = json.loads(EXAM_AI_REVIEW.read_text(encoding="utf-8")) if EXAM_AI_REVIEW.exists() else {}

    meta = {k: v for k, v in data.items() if k not in ("questions", "passages")}
    conn.execute("INSERT OR REPLACE INTO exams (exam_id, title, level, exam_type, source_type, is_official, "
                 "duration_minutes, data_json, source_ids, verification_status) VALUES (?,?,?,?,?,?,?,?,?,?)",
                 (data["exam_id"], data["title"], data["level"], data["exam_type"], data["source_type"],
                  int(data["is_official"]), data["duration_minutes"], json.dumps(meta, ensure_ascii=False),
                  json.dumps(data["source_ids"]), "needs_review"))
    mondai_pages = pages["SRC_LOCAL_N5_MONDAI"]
    for p in data["passages"]:
        img = f"IMG_N5_MONDAI_P{p['image_page']:03d}" if p.get("image_page") else None
        conn.execute("INSERT OR REPLACE INTO passages (passage_id, exam_id, text, source_page, image_asset_id) "
                     "VALUES (?,?,?,?,?)", (p["passage_id"], data["exam_id"], p["text"], p["source_page"], img))
    sections = {s["section_id"]: s for s in data["sections"]}
    for q in data["questions"]:
        sec = sections[q["section_id"]]
        mondai = next(m for m in sec["mondai"] if m["mondai_no"] == q["mondai_no"])
        if official[q["question_id"]] != q["seikai"]:
            raise ValueError(f"{q['question_id']}: transcribed answer {q['seikai']} != 正解 table")
        if not 1 <= q["seikai"] <= len(q["options"]):
            raise ValueError(f"{q['question_id']}: answer outside options")
        page_img = f"IMG_N5_MONDAI_P{q['source_page']:03d}"
        glyph = q.get("options_are_glyph_images") or q.get("options_are_pictures")
        options = [{"option_id": str(i), "text": t, **({"image_asset_id": page_img} if glyph else {})}
                   for i, t in enumerate(q["options"], 1)]
        extra = {k: q[k] for k in ("target", "options_are_glyph_images", "options_are_pictures", "options_audio_only",
                                    "star_position", "expected_sequence", "expected_sequence_note",
                                    "has_illustration") if k in q}
        raw_id = repo.insert_raw(conn, "SRC_LOCAL_N5_MONDAI", f"page:{q['source_page']}/{q['question_id']}",
                                 json.dumps(q, ensure_ascii=False), "ai_vision_transcription")
        extra["raw_id"] = raw_id
        a = ai.get(q["question_id"], {})
        conn.execute(
            "INSERT OR REPLACE INTO questions (question_id, exam_id, section, section_id, mondai_no, mondai_type, number, "
            "question_text, instruction, passage_id, options, correct_answer, answer_type, extra_json, explanation_vi, "
            "explanation_origin, audio_asset_id, image_asset_id, transcript, level, source_ids, source_page, "
            "extraction_method, verification_status, review_notes) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,"
            "COALESCE((SELECT verification_status FROM questions WHERE question_id=?), 'needs_review'),?)",
            (q["question_id"], data["exam_id"], sec["section"], q["section_id"], q["mondai_no"], mondai["mondai_type"],
             q["number"], q["question_text"], mondai["instruction"], q.get("passage_id"),
             json.dumps(options, ensure_ascii=False), json.dumps([str(q["seikai"])]),
             q.get("answer_type", "single_choice"), json.dumps(extra, ensure_ascii=False),
             a.get("explanation_vi"), "AI_GENERATED" if a else None,
             "AUD_N5S_001" if sec["section"] == "listening" else None,
             page_img if (glyph or q.get("has_illustration") or sec["section"] == "listening") else None,
             q.get("transcript"), data["level"],
             json.dumps(["SRC_LOCAL_N5_MONDAI", "SRC_LOCAL_N5_SEIKAI"] +
                        (["SRC_LOCAL_N5_SCRIPT", "SRC_LOCAL_N5_AUDIO"] if sec["section"] == "listening" else [])),
             q["source_page"], "ai_vision_transcription", q["question_id"], q.get("review_notes")))
        issues = [("transcription_unverified", "warning",
                   "Câu hỏi được chép bằng AI từ ảnh trang; cần đối chiếu với ảnh gốc.", None)]
        if q.get("options_are_glyph_images"):
            issues.append(("options_image_only", "warning", "Lựa chọn là ký tự dạng ảnh, không có văn bản.", None))
        if sec["section"] == "listening":
            issues.append(("audio_timestamp_missing", "info", "Chưa có timestamp của câu trong file audio.", None))
        repo.replace_issues(conn, "question", q["question_id"], issues)
        if a and a.get("verdict") != "consistent":
            repo.replace_issues(conn, "question", q["question_id"], [(
                "ai_answer_doubt", "warning", a.get("verdict_note") or "AI nghi ngờ đáp án", None)], origin="ai_review")
        if repo.get_question(conn, q["question_id"])["verification_status"] == "verified":
            conn.execute("UPDATE validation_issues SET resolved=1 WHERE entity_type='question' AND entity_id=?",
                         (q["question_id"],))
    for sid in pages:
        repo.update_source(conn, sid, processing_status="needs_review", imported_at=repo.iso(),
                           record_count=len(pages[sid]))
    repo.update_source(conn, "SRC_LOCAL_N5_MONDAI", record_count=len(data["questions"]))
    repo.update_source(conn, "SRC_LOCAL_N5_AUDIO", processing_status="needs_review", imported_at=repo.iso(),
                       record_count=8)
    conn.commit()
    return {"questions": len(data["questions"]), "passages": len(data["passages"]),
            "page_images": sum(len(v) for v in pages.values())}


VOCAB_AI_REVIEW = ROOT / "data" / "normalized" / "ai_review" / "vocabulary_ai_review.json"


def apply_vocab_ai_review(conn, path: Path = VOCAB_AI_REVIEW) -> dict:
    """Attach AI audit findings as issues (origin=ai_review). Data itself is never changed."""
    if not path.exists():
        return {"applied": 0, "skipped": 0}
    findings = json.loads(path.read_text(encoding="utf-8"))
    by_id: dict[str, list] = {}
    skipped = 0
    for f in findings:
        v = repo.get_vocab(conn, f["id"])
        if not v or _norm(v["word"]) != _norm(f["word"]):   # ids are only trusted with a matching word
            skipped += 1
            continue
        by_id.setdefault(f["id"], []).append(f)
    for vid, fs in by_id.items():
        if repo.get_vocab(conn, vid)["verification_status"] in ("verified", "rejected"):
            continue                                   # already decided by the user
        repo.replace_issues(conn, "vocabulary", vid, [(
            f"ai_{f['field']}", "warning",
            f"[AI rà soát, độ tin cậy {f['confidence']}] {f['problem_vi']}", f.get("suggestion")) for f in fs],
            origin="ai_review")
        if repo.get_vocab(conn, vid)["verification_status"] == "normalized":
            repo.update_vocab(conn, vid, verification_status="needs_review")
    conn.commit()
    return {"applied": sum(len(v) for v in by_id.values()), "items": len(by_id), "skipped": skipped}


def run_all(conn, check_network: bool = False) -> dict:
    out = {"inventory": len(inventory(conn)), "online_registered": register_online(conn)}
    out["flashcards"] = import_flashcards(conn)
    out["vocab_ai_review"] = apply_vocab_ai_review(conn)
    out["exam"] = import_sample_exam(conn)
    if check_network:
        out["online_check"] = check_online(conn)
    return out
