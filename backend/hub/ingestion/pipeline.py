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
from ..learning import exam as examlib
from ..validation import reference as ref
from ..validation.kana import check_transcript_gloss
from ..validation import vocabulary as vrules
from . import flashcards_csv as fc

EXAM_DIR = ROOT / "docs" / "N5" / "Exam"
FLASHCARD_DIR = ROOT / "docs" / "N5" / "flashcards"
SOURCEDOCS_DIR = ROOT / "docs" / "N5" / "SourceDocs"
DRIVE_DIR = ROOT / "data" / "raw" / "SRC_LESSON_002"
ONLINE_SOURCES = ROOT / "data" / "sources_online.json"
EXAM_JSON = ROOT / "data" / "normalized" / "exams" / "EXAM_N5_OFFICIAL_SAMPLE.json"
TIMESTAMPS = ROOT / "data" / "normalized" / "exams" / "listening_timestamps.json"   # ADR-025
GLOSS = ROOT / "data" / "normalized" / "exams" / "listening_gloss.json"             # ADR-032 (local only)
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
    if path.parent.parent == RAW_DIR and path.parent.name.startswith("SRC_DRIVE_EXAM_"):   # past paper folder
        return path.parent.name + {"mondai": "", "seikai": "_KEY", "script": "_SCRIPT", "audio": "_AUDIO"}.get(
            path.stem, "_" + path.stem.upper())
    if path.parent == DRIVE_DIR:                      # PDFs downloaded from the public Drive folder
        return "SRC_DRIVE_" + re.sub(r"[^A-Z0-9]+", "_", path.stem.upper()).strip("_")[:30]
    if path.suffix.lower() == ".docx" and "Ngữ Pháp" in path.stem:
        return "SRC_LOCAL_GRAMMAR_DOCX"
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
def inventory(conn, dirs=(EXAM_DIR, FLASHCARD_DIR, SOURCEDOCS_DIR, DRIVE_DIR)) -> list[dict]:
    """Register every supported file. Records size, hash, pages/duration. Flags exact duplicates."""
    report = []
    seen: dict[str, str] = {r["content_hash"]: r["source_id"] for r in repo.list_sources(conn) if r["content_hash"]}
    for d in dirs:
        if not Path(d).exists():
            report.append({"location": rel(Path(d)), "error": "directory not accessible"})
            continue
        # data/raw holds derived files (OCR json, page images) next to downloaded PDFs: register PDFs only
        files = (Path(d).glob("*.pdf") if Path(d) == DRIVE_DIR else
                 Path(d).glob("*") if Path(d).parent == RAW_DIR else Path(d).rglob("*"))
        for p in sorted(files):
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
                               "SUPPLEMENTARY" if sid.startswith("SRC_DRIVE_EXAM_") else
                               "USER_CREATED" if sid.startswith(("SRC_LOCAL_FC_", "SRC_LOCAL_GRAMMAR")) else
                               "EDUCATIONAL" if sid.startswith("SRC_DRIVE_") else "PRIMARY")
                src = {**entry, "reliability": reliability, "access_status": "local", "level": "N5",
                       "purpose": EXAM_PURPOSE.get(sid) or ("Flashcard do người dùng xuất" if kind == "csv" else
                                                            "Đề JLPT N5 thật (bản cộng đồng, thư mục Drive ĐỀ THI)"
                                                            if sid.startswith("SRC_DRIVE_EXAM_") else None),
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
# NotebookLM share links open a page whose content is rendered client-side behind Google sign-in:
# the HTTP check passes but nothing can be read without an export.
AUTH_TYPES = {"notebooklm": "manual_export"}


def probe_url(url: str, source_type: str) -> str:
    """URL actually fetched for the check: a public Google Doc is checked through its text export."""
    m = re.match(r"https://docs\.google\.com/document/d/([^/]+)", url)
    if source_type == "google_doc" and m:
        return f"https://docs.google.com/document/d/{m.group(1)}/export?format=txt"
    return url


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
            if "accounts.google.com" in r.geturl():
                return "requires_auth", "chuyển hướng tới trang đăng nhập Google"
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
        status, detail = checker(probe_url(s["url"], s["source_type"]))
        forced = AUTH_TYPES.get(s["source_type"])
        if forced and status == "accessible":
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
    stats["corrections"] = apply_vocab_corrections(conn)
    revalidate_all(conn)
    repo.ensure_cards(conn)
    conn.commit()
    return stats


VOCAB_CORRECTIONS = ROOT / "data" / "normalized" / "corrections" / "vocabulary_corrections.json"
USER_OWNED = ("user", "pending_user")     # a person decided or is editing: automation keeps its hands off


def _raw_word(conn, v: dict) -> str:
    raw = repo.raw_by_ids(conn, json.loads(v["raw_ids"])[:1])
    if not raw:
        return ""
    content = json.loads(raw[0]["content"])        # CSV row: [front, back]; OCR/reference row: {"word": ...}
    return _norm(content.get("word") if isinstance(content, dict) else content[0])


def load_corrections(path: Path = VOCAB_CORRECTIONS) -> dict:
    if not path.exists():
        return {"audit": {"items": {}}, "corrections": [], "open_questions": []}
    return json.loads(path.read_text(encoding="utf-8"))


def apply_vocab_corrections(conn, path: Path = VOCAB_CORRECTIONS) -> dict:
    """Apply reviewed corrections to the NORMALIZED layer. RAW rows are never touched; every change is
    logged in review_actions (action=ai_correction) with before/after, so it can be traced and undone
    ("Trích xuất lại từ RAW" on the review screen)."""
    data = load_corrections(path)
    stats = {"applied": 0, "already_applied": 0, "conflict": 0, "skipped": 0}
    conn.execute("DELETE FROM validation_issues WHERE entity_type='vocabulary' AND origin='ai_review'")
    for c in data["corrections"]:
        v = repo.get_vocab(conn, c["id"])
        if not v or _raw_word(conn, v) != _norm(c["raw_word"]) or v["verified_by"] in USER_OWNED:
            stats["skipped"] += 1
            continue
        cur, new = v[c["field"]] or "", c["new_value"] or ""
        if cur == new:
            stats["already_applied"] += 1
        elif cur == (c["old_value"] or ""):
            repo.update_vocab(conn, c["id"], **{c["field"]: new or None})
            repo.log_action(conn, "vocabulary", c["id"], "ai_correction", c["reason_vi"],
                            {c["field"]: cur}, {c["field"]: new, "basis": c.get("basis")})
            stats["applied"] += 1
        else:
            stats["conflict"] += 1            # value differs from both old and new: leave it alone
    for q in data.get("open_questions", []):
        v = repo.get_vocab(conn, q["id"])
        if v and _raw_word(conn, v) == _norm(q["raw_word"]) and v["verified_by"] not in USER_OWNED:
            repo.add_issue(conn, "vocabulary", q["id"], "ai_open_question", "warning", q["question_vi"],
                           q.get("suggestion"), origin="ai_review")
    return stats


def dictionary_check(v: dict) -> tuple[list, dict]:
    """Issues from JMdict / KANJIDIC2 plus fields the dictionary can fill in (POS, verb group)."""
    if not ref.available():
        return [], {}
    issues, enrich = [], {}
    a = ref.check_reading(v["word"], v["reading"] or "")
    if a["status"] == "mismatch":
        issues.append(("dict_reading_mismatch", "warning",
                       f"JMdict: '{v['word']}' đọc là {' / '.join(a['expected'][:4])}; dữ liệu ghi '{v['reading']}'",
                       a["expected"][0]))
    elif a["status"] == "confirmed":
        # verb_group / dictionary_form are always overwritten (also with NULL) so stale guesses disappear
        enrich = {"verb_group": a.get("verb_group"), "dictionary_form": a.get("dictionary_form")}
        if a.get("pos"):
            enrich["part_of_speech"] = a["pos"]
    elif v.get("part_of_speech") == "verb":
        enrich = {"part_of_speech": "expression", "verb_group": None}   # ます phrase, not a dictionary verb
    b = ref.check_han_viet(v["word"], v["han_viet"])
    if b["status"] == "mismatch":
        allowed = "; ".join(f"{p['kanji']} = {', '.join(p['allowed'][:4]) or '?'}" for p in b["per_kanji"])
        issues.append(("dict_han_viet_mismatch", "warning",
                       f"Hán-Việt '{v['han_viet']}' không khớp từ điển ({allowed})", None))
    return issues, enrich


def revalidate_vocab(conn, vid: str, dupes: dict[str, list[str]] | None = None,
                     audited: dict[str, str] | None = None) -> list:
    """Re-run every automatic check and set the status.
    verified (verified_by=ai) needs ALL of: covered by the AI audit, no error/warning from the rules,
    reading and Hán-Việt not contradicted by the dictionaries. Items a person approved or edited keep
    their status."""
    v = repo.get_vocab(conn, vid)
    owned = v["verified_by"] in USER_OWNED
    dict_issues, enrich = dictionary_check(v)
    if enrich and not owned:
        repo.update_vocab(conn, vid, **enrich)
        v = repo.get_vocab(conn, vid)
    issues = vrules.validate(v)
    if ref.available():        # the dictionary check supersedes the cruder syllable count
        issues = [i for i in issues if i[0] != "han_viet_count"]
    issues += dict_issues
    others = [o for o in (dupes or {}).get(_norm(v["word"]), []) if o != vid]
    if others:
        diff_reading = [o for o in others if _norm(repo.get_vocab(conn, o)["reading"]) != _norm(v["reading"])]
        if diff_reading:   # each reading is checked against JMdict on its own (～人 じん/にん, 降ります ふ/お)
            issues.append(("homograph", "info",
                           f"Cùng cách viết '{v['word']}' nhưng cách đọc khác ở {', '.join(diff_reading)}", None))
        else:
            issues.append(("duplicate_same_word", "info",
                           f"Từ '{v['word']}' còn xuất hiện ở {', '.join(others)} "
                           "(đa nghĩa hoặc trùng lặp giữa các bài)", None))
    repo.replace_issues(conn, "vocabulary", vid, issues)
    if v["verification_status"] == "rejected" or owned:
        if v["verification_status"] == "verified":     # a person's approval stands; do not reopen issues
            conn.execute("UPDATE validation_issues SET resolved=1 WHERE entity_type='vocabulary' AND entity_id=?",
                         (vid,))
        return issues
    blocking = any(sev in ("error", "warning") for _, sev, _, _ in issues) or conn.execute(
        "SELECT COUNT(*) FROM validation_issues WHERE entity_type='vocabulary' AND entity_id=? "
        "AND origin!='rule' AND resolved=0 AND severity!='info'", (vid,)).fetchone()[0]
    if blocking:
        repo.update_vocab(conn, vid, verification_status="needs_review", verified_by=None)
    elif audited and _norm(audited.get(vid, "\0")) == _raw_word(conn, v):
        repo.update_vocab(conn, vid, verification_status="verified", verified_by="ai")
    else:
        repo.update_vocab(conn, vid, verification_status="normalized", verified_by=None)
    return issues


def revalidate_all(conn) -> None:
    dupes: dict[str, list[str]] = {}
    for r in conn.execute("SELECT id, word FROM vocabulary WHERE archived=0"):
        dupes.setdefault(_norm(r["word"]), []).append(r["id"])
    from . import knowledge
    audited = {**load_corrections()["audit"]["items"], **knowledge.supplement_audited(conn)}
    for vid in [r[0] for r in conn.execute("SELECT id FROM vocabulary")]:
        revalidate_vocab(conn, vid, dupes, audited)


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


def _exam_files(data: dict) -> tuple[Path, dict]:
    """Where an exam's original files live. A JSON without a `files` block is the official sample in docs/N5/Exam."""
    f = data.get("files") or {"mondai": "N5-mondai.pdf", "seikai": "N5-seikai.pdf", "script": "N5-script.pdf",
                              "audio": "N5Sample.mp3", "audio_asset_id": "AUD_N5S_001"}
    if f.get("dir"):
        return ROOT / f["dir"], f
    found = next(EXAM_DIR.rglob(f["mondai"]), None)
    return (found.parent if found else EXAM_DIR), f


def import_exam(conn, exam_json: Path = EXAM_JSON) -> dict:
    """Import one transcribed exam (official sample or past paper). The JSON names its files, question-id prefix and
    answer key; `<exam>.ai_review.json` next to it holds the independent AI solutions and explanations (ADR-019)."""
    data = json.loads(exam_json.read_text(encoding="utf-8"))
    exam_dir, files = _exam_files(data)
    if not (exam_dir / files["mondai"]).is_file():
        return {"skipped": f"thiếu file gốc {rel(exam_dir / files['mondai'])}"}
    prefix = data.get("question_id_prefix", "Q_N5S")
    key_origin = data.get("key_origin", "official_seikai")
    inventory(conn, [exam_dir])
    pages: dict[str, list[str]] = {}
    for f in sorted(exam_dir.glob("*.pdf")):
        sid = source_id_for(f)
        repo.update_source(conn, sid, processing_status="extracting")
        pages[sid] = render_pages(f, sid)
        with __import__("pymupdf").open(f) as d:
            for i, pg in enumerate(d, start=1):
                repo.insert_raw(conn, sid, f"page:{i}", pg.get_text() or "",
                                "pdf_text_layer (incomplete: CID fonts without ToUnicode)")
        for i, pth in enumerate(pages[sid], start=1):
            conn.execute("INSERT OR REPLACE INTO assets (asset_id, source_id, kind, file_path, mime_type, page_number, notes) "
                         "VALUES (?,?,?,?,?,?,?)", (f"IMG_{sid[10:]}_P{i:03d}", sid, "image", pth, "image/png", i,
                                                     "Ảnh render trang gốc (lớp RAW)"))
    sid_of = lambda role: source_id_for(exam_dir / files[role]) if files.get(role) else None
    mondai_sid, key_sid, script_sid = sid_of("mondai"), sid_of("seikai"), sid_of("script")
    audio = exam_dir / files["audio"]
    audio_sid, audio_id = source_id_for(audio), files["audio_asset_id"]
    stamps = json.loads(TIMESTAMPS.read_text(encoding="utf-8"))["questions"] if TIMESTAMPS.exists() else {}
    gloss = json.loads(GLOSS.read_text(encoding="utf-8"))["questions"] if GLOSS.exists() else {}
    n_stamped = sum(q["question_id"] in stamps for q in data["questions"])
    conn.execute("INSERT OR REPLACE INTO assets (asset_id, source_id, kind, file_path, mime_type, duration_seconds, "
                 "transcript_status, notes) VALUES (?,?,?,?,?,?,?,?)",
                 (audio_id, audio_sid, "audio", rel(audio), "audio/mp4" if audio.suffix == ".m4a" else "audio/mpeg",
                  audio_duration(audio), data.get("transcript_status", "official_script_transcribed_needs_review"),
                  "Một track cho toàn bộ phần nghe; " + (f"{n_stamped} câu có mốc thời gian (ADR-025)." if n_stamped
                                                         else "chưa có timestamp từng câu.")))

    key = data["answer_key"]
    official = {**{f"{prefix}_V{i:02d}": a for i, a in enumerate(key["vocabulary"], 1)},
                **{f"{prefix}_G{i:02d}": a for i, a in enumerate(key["grammar_reading"], 1)},
                **{f"{prefix}_L{m}_{i}": a for m, arr in key["listening"].items() for i, a in enumerate(arr, 1)}}
    review_file = exam_json.with_name(exam_json.stem + ".ai_review.json")
    ai = json.loads(review_file.read_text(encoding="utf-8")) if review_file.exists() else {}

    meta = {k: v for k, v in data.items() if k not in ("questions", "passages")}
    conn.execute("INSERT OR REPLACE INTO exams (exam_id, title, level, exam_type, source_type, is_official, "
                 "duration_minutes, data_json, source_ids, verification_status) VALUES (?,?,?,?,?,?,?,?,?,?)",
                 (data["exam_id"], data["title"], data["level"], data["exam_type"], data["source_type"],
                  int(data["is_official"]), data["duration_minutes"], json.dumps(meta, ensure_ascii=False),
                  json.dumps(data["source_ids"]), "needs_review"))
    img = lambda page: f"IMG_{mondai_sid[10:]}_P{page:03d}"
    for p in data["passages"]:
        conn.execute("INSERT OR REPLACE INTO passages (passage_id, exam_id, text, source_page, image_asset_id) "
                     "VALUES (?,?,?,?,?)", (p["passage_id"], data["exam_id"], p["text"], p["source_page"],
                                            img(p["image_page"]) if p.get("image_page") else None))
    sections = {s["section_id"]: s for s in data["sections"]}
    stats = {"verified": 0, "needs_review": 0}
    for q in data["questions"]:
        sec = sections[q["section_id"]]
        mondai = next(m for m in sec["mondai"] if m["mondai_no"] == q["mondai_no"])
        if official.get(q["question_id"]) != q["seikai"]:
            raise ValueError(f"{q['question_id']}: transcribed answer {q['seikai']} != 正解 table")
        if not 1 <= q["seikai"] <= len(q["options"]):
            raise ValueError(f"{q['question_id']}: answer outside options")
        page_img = img(q["source_page"])
        glyph = q.get("options_are_glyph_images") or q.get("options_are_pictures")
        options = [{"option_id": str(i), "text": t, **({"image_asset_id": page_img} if glyph else {})}
                   for i, t in enumerate(q["options"], 1)]
        a = ai.get(q["question_id"], {})
        extra = {k: q[k] for k in ("target", "options_are_glyph_images", "options_are_pictures", "options_audio_only",
                                    "star_position", "expected_sequence", "expected_sequence_note",
                                    "has_illustration") if k in q}
        if a.get("option_explanations"):
            extra["option_explanations"] = a["option_explanations"]
        extra["key_origin"] = key_origin
        extra["raw_id"] = repo.insert_raw(conn, mondai_sid, f"page:{q['source_page']}/{q['question_id']}",
                                          json.dumps(q, ensure_ascii=False), "ai_vision_transcription")
        listening = sec["section"] == "listening"
        stamp = stamps.get(q["question_id"]) if listening else None
        if stamp:
            extra.update(audio_start=stamp["start"], audio_end=stamp["end"])
        g = gloss.get(q["question_id"]) if listening and q.get("transcript") else None
        gloss_problems = check_transcript_gloss(q["transcript"], g["lines"]) if g else []
        if g and not gloss_problems:
            extra["transcript_gloss"] = g["lines"]
        status = examlib.consensus_status(q["seikai"], [a.get("solver_a"), a.get("solver_b")])
        by = "ai" if status == "verified" else None
        if q.get("decided_by") == "user":           # the user settled a disputed key; recorded in the exam JSON
            status, by = "verified", "user"
        cur = conn.execute("SELECT verification_status, verified_by FROM questions WHERE question_id=?",
                           (q["question_id"],)).fetchone()
        if cur and cur["verified_by"] in ("user", "pending_user"):
            status, by = cur["verification_status"], cur["verified_by"]          # a person decided: keep it
        conn.execute(
            "INSERT OR REPLACE INTO questions (question_id, exam_id, section, section_id, mondai_no, mondai_type, number, "
            "question_text, instruction, passage_id, options, correct_answer, answer_type, extra_json, explanation_vi, "
            "explanation_origin, audio_asset_id, image_asset_id, transcript, level, source_ids, source_page, "
            "extraction_method, verification_status, verified_by, review_notes) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (q["question_id"], data["exam_id"], sec["section"], q["section_id"], q["mondai_no"], mondai["mondai_type"],
             q["number"], q["question_text"], mondai["instruction"], q.get("passage_id"),
             json.dumps(options, ensure_ascii=False), json.dumps([str(q["seikai"])]),
             q.get("answer_type", "single_choice"), json.dumps(extra, ensure_ascii=False),
             a.get("explanation_vi"), "AI_GENERATED" if a else None,
             audio_id if listening else None,
             page_img if (glyph or q.get("has_illustration") or listening) else None,
             q.get("transcript"), data["level"],
             json.dumps([s for s in [mondai_sid, key_sid] + ([script_sid, audio_sid] if listening else []) if s]),
             q["source_page"], "ai_vision_transcription", status, by, q.get("review_notes")))
        stats["verified" if status == "verified" else "needs_review"] += 1
        issues = [("transcription_unverified", "warning",
                   "Câu hỏi được chép bằng AI từ ảnh trang; cần đối chiếu với ảnh gốc.", None)]
        if q.get("options_are_glyph_images"):
            issues.append(("options_image_only", "warning", "Lựa chọn là ký tự dạng ảnh, không có văn bản.", None))
        if listening and not stamp:
            issues.append(("audio_timestamp_missing", "info", "Chưa có timestamp của câu trong file audio.", None))
            if data.get("transcript_status") == "asr_whisper":
                issues.append(("transcript_asr", "info", "Script nghe chép tự động bằng Whisper (không có script gốc).",
                               None))
        if gloss_problems:
            issues.append(("transcript_gloss_invalid", "info",
                           "Romaji/dịch script nghe không qua luật, không hiển thị: " + "; ".join(gloss_problems[:3]), None))
        repo.replace_issues(conn, "question", q["question_id"], issues)
        doubt = []
        if a and a.get("verdict") not in (None, "consistent"):
            doubt.append(("ai_answer_doubt", "warning", a.get("verdict_note") or "AI nghi ngờ đáp án", None))
        if a.get("solver_a") is not None and status != "verified":
            doubt.append(("answer_key_disputed", "warning",
                          f"Đáp án ({key_origin}) = {q['seikai']}; AI giải độc lập: {a.get('solver_a')} / "
                          f"{a.get('solver_b')}. {a.get('verdict_note') or ''}".strip(), None))
        repo.replace_issues(conn, "question", q["question_id"], doubt, origin="ai_review")
        if status == "verified":
            conn.execute("UPDATE validation_issues SET resolved=1 WHERE entity_type='question' AND entity_id=?",
                         (q["question_id"],))
    for sid in pages:
        repo.update_source(conn, sid, processing_status="needs_review", imported_at=repo.iso(),
                           record_count=len(pages[sid]))
    repo.update_source(conn, mondai_sid, record_count=len(data["questions"]))
    repo.update_source(conn, audio_sid, processing_status="needs_review", imported_at=repo.iso(),
                       record_count=sum(sections[q["section_id"]]["section"] == "listening" for q in data["questions"]))
    conn.commit()
    return {"questions": len(data["questions"]), "passages": len(data["passages"]),
            "page_images": sum(len(v) for v in pages.values()), **stats}


def import_past_exams(conn) -> dict:
    """Every other transcribed exam in data/normalized/exams (past papers, ADR-019). Missing originals are skipped."""
    return {p.stem: import_exam(conn, p) for p in sorted(EXAM_JSON.parent.glob("EXAM_*.json"))
            if p != EXAM_JSON and not p.stem.endswith(".ai_review")}


def run_all(conn, check_network: bool = False) -> dict:
    out = {"inventory": len(inventory(conn)), "online_registered": register_online(conn)}
    from . import knowledge
    out["flashcards"] = import_flashcards(conn)          # CSV first: keeps VOC ids of the user's cards stable
    out["vocab_supplement"] = knowledge.import_supplement(conn)
    revalidate_all(conn)
    out["grammar"] = knowledge.import_grammar(conn)
    out["kanji"] = knowledge.import_kanji(conn)
    out["kaiwa"] = knowledge.import_kaiwa(conn)          # after vocabulary/grammar/kanji: it references them
    out["numbers"] = knowledge.import_numbers(conn)      # numbers/counters/dates topic (ADR-029)
    repo.ensure_cards(conn)                              # after grammar/kanji: they get SRS cards too (ADR-021)
    out["exam"] = import_exam(conn)
    out["past_exams"] = import_past_exams(conn)
    out["generated_questions"] = knowledge.import_generated_questions(conn)
    out["grammar_questions"] = knowledge.import_grammar_questions(conn)
    out["reading_questions"] = knowledge.import_reading_questions(conn)
    out["number_questions"] = knowledge.import_number_questions(conn)
    conn.commit()
    if check_network:
        out["online_check"] = check_online(conn)
    return out
