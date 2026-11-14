"""Generate docs/IMPORT_REPORT.md, docs/SOURCE_CATALOG.md, docs/DATA_QUALITY_REPORT.md from the database."""
import json

from . import repo
from .db import ROOT

DOCS = ROOT / "docs"


def _table(headers: list[str], rows: list[list]) -> str:
    esc = lambda v: "" if v is None else str(v).replace("|", "\\|").replace("\n", " ")
    return "\n".join(["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
                     + ["| " + " | ".join(esc(c) for c in r) + " |" for r in rows])


def import_report(conn) -> str:
    srcs = [s for s in repo.list_sources(conn) if s["access_status"] == "local"]
    rows = []
    for s in srcs:
        sid = s["source_id"]
        q = conn.execute("SELECT COUNT(*) FROM questions WHERE source_ids LIKE ?", (f'%"{sid}"%',)).fetchone()[0]
        v = conn.execute("SELECT COUNT(*) FROM vocabulary WHERE source_ids LIKE ?", (f'%"{sid}"%',)).fetchone()[0]
        raw = conn.execute("SELECT COUNT(*) FROM raw_records WHERE source_id=?", (sid,)).fetchone()[0]
        unstructured = conn.execute(
            "SELECT COUNT(*) FROM validation_issues i JOIN raw_records r ON i.entity_type='raw' AND i.entity_id=CAST(r.raw_id AS TEXT) "
            "WHERE r.source_id=?", (sid,)).fetchone()[0]
        audio = 1 if s["source_type"] == "audio" else 0
        dup = s["notes"] if s["notes"] and "Trùng" in s["notes"] else ""
        rows.append([s["name"], s["location"].rsplit(".", 1)[-1], s["size_bytes"], s["location"], s["source_type"],
                     s["page_count"] or "", q or "", audio or "", f"raw {raw} / từ vựng {v}" + (f" / RAW-only {unstructured}" if unstructured else ""),
                     s["processing_status"], dup, s["error"] or ""])
    totals = repo.dashboard(conn)
    return f"""# IMPORT REPORT

Tạo tự động bởi `python -m hub report` lúc {repo.iso()}. Số liệu đọc từ `data/database/hub.sqlite`.

Thư mục đã kiểm tra: `D:\\Japanese\\docs\\N5\\Exam`, `D:\\Japanese\\docs\\N5\\flashcards` (truy cập trực tiếp từ Windows, không qua WSL/Docker).

## Tóm tắt
- Tệp cục bộ đã đăng ký: **{len(srcs)}**
- Từ vựng (lớp NORMALIZED): {json.dumps(totals['vocabulary_by_status'], ensure_ascii=False)} — **0 mục được tự động xác minh**.
- Câu hỏi đề mẫu: {json.dumps(totals['questions_by_status'])}
- Trạng thái xử lý `needs_review` = đã nhập nhưng còn chờ người dùng duyệt (không phải lỗi).

## Chi tiết từng tệp
{_table(["Tệp", "Đuôi", "Bytes", "Vị trí", "Loại", "Số trang", "Câu hỏi", "Audio", "Bản ghi", "Trạng thái xử lý", "Trùng lặp", "Lỗi"], rows)}

## Ghi chú trích xuất
- **PDF đề thi**: text layer hỏng (font CID không có ToUnicode) → trích `get_text()` chỉ lấy được tiêu đề. Câu hỏi được chép lại bằng AI từ ảnh trang (`ai_vision_transcription`), lưu ở `data/normalized/exams/EXAM_N5_OFFICIAL_SAMPLE.json`, trạng thái `needs_review`. Ảnh trang gốc lưu ở `data/raw/<source_id>/pages/`.
- **Đáp án**: lấy từ bảng 正解 (`N5-seikai.pdf`); importer từ chối nạp nếu đáp án chép khác bảng 正解.
- **Audio**: 1 tệp MP3 cho cả 8 câu nghe; chưa có timestamp từng câu (không suy đoán).
- **OCR**: chưa dùng (tesseract chưa cài). Không có PDF scan cần OCR trong bộ dữ liệu hiện tại.
- **Flashcard Số Đếm**: 16 dòng dạng hỏi–đáp tự do → giữ ở RAW, không ép thành từ vựng.
- **Thiếu dữ liệu**: không có `flashcards_Bai15.csv`; `flashcards_Bai18.csv` chỉ có 1 dòng (có thể export bị thiếu).
"""


def source_catalog(conn) -> str:
    rows = [[s["source_id"], s["name"], s["source_type"], s["reliability"], s["access_status"] or "unchecked",
             s["checked_at"] or "", s["url"] or s["location"], s["purpose"] or "", s["notes"] or ""]
            for s in repo.list_sources(conn)]
    return f"""# SOURCE CATALOG

Tạo tự động lúc {repo.iso()}. Định nghĩa độ tin cậy: OFFICIAL / PRIMARY / EDUCATIONAL / SUPPLEMENTARY / AI_GENERATED / USER_CREATED (spec §3.3).

Trạng thái truy cập là kết quả **kiểm tra HTTP** (`python -m hub check-online`), không phải trích xuất nội dung.
`requires_auth` / `manual_export` = cần tài khoản Google hoặc người dùng tải/export tệp về `docs/` để nhập.
Một số lỗi `unreachable` có thể do mạng/chứng chỉ cục bộ (vd. `CERTIFICATE_VERIFY_FAILED`) — mở bằng trình duyệt để xác nhận.

{_table(["ID", "Tên", "Loại", "Độ tin cậy", "Truy cập", "Kiểm tra lúc", "URL / vị trí", "Mục đích", "Ghi chú"], rows)}
"""


def data_quality(conn) -> str:
    by_code = repo.rows(conn.execute(
        "SELECT entity_type, origin, code, severity, COUNT(*) n FROM validation_issues WHERE resolved=0 "
        "GROUP BY 1,2,3,4 ORDER BY CASE severity WHEN 'error' THEN 0 WHEN 'warning' THEN 1 ELSE 2 END, n DESC"))
    flagged = repo.rows(conn.execute(
        "SELECT v.id, v.word, v.reading, v.han_viet, i.origin, i.code, i.message, i.suggestion FROM validation_issues i "
        "JOIN vocabulary v ON v.id=i.entity_id AND i.entity_type='vocabulary' WHERE i.resolved=0 AND i.severity!='info' "
        "ORDER BY v.id, i.origin"))
    return f"""# DATA QUALITY REPORT

Tạo tự động lúc {repo.iso()}.

Hai lớp kiểm tra, **không lớp nào tự sửa dữ liệu**:
1. **Luật tự động** (`origin=rule`): kana hợp lệ, romaji ↔ kana, số âm Hán-Việt ↔ số kanji, mã hoá, trùng lặp, động từ thiếu thể từ điển.
2. **AI rà soát** (`origin=ai_review`, nhãn AI_GENERATED): đọc toàn bộ 963 mục, chỉ báo lỗi rõ ràng (độ tin cậy high/medium) kèm đề xuất. Lưu ở `data/normalized/ai_review/vocabulary_ai_review.json`.

Đề mẫu: AI đối chiếu 29/29 đáp án 正解 với nội dung câu hỏi — **29/29 nhất quán** (`EXAM_N5_OFFICIAL_SAMPLE.ai_review.json`). Giải thích tiếng Việt được gắn nhãn AI_GENERATED.

## Thống kê vấn đề mở
{_table(["Thực thể", "Nguồn kiểm tra", "Mã", "Mức", "Số lượng"], [list(r.values()) for r in by_code])}

## Danh sách mục từ vựng cần duyệt (error/warning)
{_table(["ID", "Từ", "Đọc", "Hán-Việt", "Nguồn", "Mã", "Vấn đề", "Đề xuất"], [list(r.values()) for r in flagged])}
"""


def write_reports(conn) -> list[str]:
    out = []
    for name, fn in (("IMPORT_REPORT.md", import_report), ("SOURCE_CATALOG.md", source_catalog),
                     ("DATA_QUALITY_REPORT.md", data_quality)):
        (DOCS / name).write_text(fn(conn), encoding="utf-8")
        out.append(str(DOCS / name))
    return out
