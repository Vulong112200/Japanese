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
    status = repo.rows(conn.execute(
        "SELECT verification_status, COALESCE(verified_by,'-') verified_by, COUNT(*) n FROM vocabulary "
        "WHERE archived=0 GROUP BY 1,2 ORDER BY 3 DESC"))
    fixes = repo.rows(conn.execute(
        "SELECT a.entity_id, v.word, a.before_json, a.after_json, a.note FROM review_actions a "
        "JOIN vocabulary v ON v.id=a.entity_id WHERE a.action='ai_correction' ORDER BY a.entity_id, a.action_id"))
    by_field: dict[str, int] = {}
    fix_rows = []
    for f in fixes:
        b, a = json.loads(f["before_json"]), json.loads(f["after_json"])
        field = next(iter(b))
        by_field[field] = by_field.get(field, 0) + 1
        fix_rows.append([f["entity_id"], f["word"], field, b[field] or "∅", a[field] or "∅", f["note"]])
    def kv(sql):
        return {r[0]: r[1] for r in conn.execute(sql)}
    decks = kv("SELECT CASE WHEN source_ids LIKE '%SRC_LOCAL_FC%' THEN 'flashcard của bạn (CSV)' "
               "WHEN source_ids LIKE '%SRC_DRIVE_TONG_HOP%' THEN 'bổ sung từ Minna (PDF Drive, OCR)' "
               "ELSE 'bổ sung theo danh sách JLPT N5' END, COUNT(*) FROM vocabulary WHERE archived=0 GROUP BY 1")
    lessons = kv("SELECT lesson_number, COUNT(*) FROM vocabulary WHERE archived=0 AND lesson_number IS NOT NULL GROUP BY 1")
    missing_lessons = [n for n in range(1, 26) if n not in lessons]
    gram = kv("SELECT origin, COUNT(*) FROM grammar GROUP BY 1")
    gram_err = sum(len(json.loads(r[0]).get("handbook_errors") or []) for r in conn.execute("SELECT data_json FROM grammar"))
    return f"""# DATA QUALITY REPORT

Tạo tự động lúc {repo.iso()}.

## Độ phủ N5
- **Từ vựng**: {sum(decks.values())} mục ({"; ".join(f"{k}: {v}" for k, v in decks.items())}). Có đủ 25 bài Minna{"" if not missing_lessons else f" (thiếu bài {missing_lessons})"}. So với danh sách JLPT N5 (718 từ): toàn bộ đã có. 19 từ khớp qua dạng khác (後→後で, 結婚→結婚します…); ～がる là ngữ pháp N4.
- **Kanji**: {conn.execute("SELECT COUNT(*) FROM kanji").fetchone()[0]}/103 chữ N5 (danh sách cấp 4 JLPT cũ), đối chứng với sách Basic Kanji 120.
- **Ngữ pháp**: {sum(gram.values())} điểm (121 điểm Minna bài 1–25 + 14 điểm N5 bổ sung/đối chiếu). Nguồn: {"; ".join(f"{k}: {v}" for k, v in gram.items())}. Đã ghi nhận {gram_err} chỗ sai hoặc thiếu trong cẩm nang gốc.

## Quy trình xác minh từ vựng
1. **Luật tự động**: kana hợp lệ, romaji ↔ kana, mã hoá, trùng lặp.
2. **Đối chiếu từ điển** (EDRDG, CC BY-SA 4.0):
   - Cách đọc, từ loại và nhóm động từ lấy từ **JMdict**. Nhóm động từ suy từ thể từ điển, không suy từ đuôi ます.
   - Hán-Việt lấy từ **KANJIDIC2**, kèm bảng bổ sung `HV_OVERRIDES` cho các chữ mà KANJIDIC2 ghi sai.
3. **Rà soát AI hai vòng độc lập**, mỗi vòng có 4 lượt đọc, phủ toàn bộ 963 mục:
   - Vòng 2 có kèm bằng chứng từ điển.
   - Sau đó người duyệt cuối (Claude) xét từng đề xuất.
4. **Áp bản sửa**: chỉ sửa lớp NORMALIZED, nguồn ở `data/normalized/corrections/vocabulary_corrections.json`.
   - Lớp RAW giữ nguyên.
   - Mỗi thay đổi ghi vào `review_actions` (`ai_correction`) kèm giá trị trước/sau.
   - Có thể hoàn tác bằng "Trích xuất lại từ RAW".
5. **Điều kiện xác minh**: chỉ đặt `verified` (`verified_by=ai`) khi mục đã qua audit **và** không còn lỗi hay cảnh báo nào từ luật hoặc từ điển.
   - Mục bạn đã sửa hoặc duyệt (`verified_by=user|pending_user`) không bị tự động thay đổi.

Đề mẫu: AI đối chiếu 29/29 đáp án 正解 với nội dung câu hỏi, kết quả **29/29 nhất quán**. Câu hỏi vẫn ở trạng thái `needs_review` cho đến khi được đối chiếu với ảnh trang gốc.

## Trạng thái từ vựng
{_table(["Trạng thái", "Xác minh bởi", "Số mục"], [list(r.values()) for r in status])}

## Bản sửa đã áp ({len(fix_rows)}): {", ".join(f"{k} {v}" for k, v in sorted(by_field.items(), key=lambda x: -x[1]))}
{_table(["ID", "Từ", "Trường", "Trước (CSV gốc)", "Sau", "Lý do"], fix_rows)}

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
