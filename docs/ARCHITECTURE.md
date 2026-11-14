# ARCHITECTURE — Japanese N5 Learning Hub

Ứng dụng local-first cho 1 người học, chạy offline trên `http://127.0.0.1:8000`.

## 1. Kiến trúc tổng thể

```mermaid
flowchart LR
  subgraph Sources["Nguồn (chỉ đọc)"]
    A1[docs/N5/Exam/*.pdf, *.mp3]
    A2[docs/N5/flashcards/*.csv]
    A3[data/sources_online.json]
  end
  subgraph Backend["backend/hub (FastAPI + SQLite)"]
    I[ingestion/pipeline.py<br/>inventory · CSV · exam · online]
    P[ingestion/flashcards_csv.py<br/>parser 3 định dạng]
    V[validation/<br/>vocabulary.py · kana.py]
    L[learning/srs.py<br/>SM-2 thuần]
    R[repo.py<br/>toàn bộ SQL]
    API[api.py<br/>REST /api/*]
  end
  DB[(data/database/hub.sqlite)]
  RAWF[data/raw/&lt;source_id&gt;/pages/*.png]
  NORM[data/normalized/exams/*.json<br/>data/normalized/ai_review/*.json]
  UI[frontend/ React + TS + Tailwind<br/>build → frontend/dist]

  A1 & A2 & A3 --> I
  I --> P --> V
  I --> RAWF
  NORM --> I
  I & V & L --> R --> DB
  API --> R
  API --> L
  UI -- fetch /api --> API
```

## 2. ERD (rút gọn)

```mermaid
erDiagram
  sources ||--o{ raw_records : "source_id"
  sources ||--o{ assets : "source_id"
  raw_records ||--o{ vocabulary : "raw_ids (JSON)"
  vocabulary ||--o{ srs_cards : "entity_id (jp_vi, vi_jp)"
  srs_cards ||--o{ review_log : "card_id"
  exams ||--o{ questions : "exam_id"
  exams ||--o{ passages : "exam_id"
  passages ||--o{ questions : "passage_id"
  assets ||--o{ questions : "audio_asset_id / image_asset_id"
  vocabulary ||--o{ validation_issues : "entity_id"
  questions ||--o{ validation_issues : "entity_id"
  vocabulary ||--o{ review_actions : "entity_id"
  questions ||--o{ review_actions : "entity_id"
```

Chi tiết cột: xem `docs/DATA_DICTIONARY.md` và `backend/hub/db.py`.

## 3. Luồng dữ liệu & kiểm định

```mermaid
flowchart TD
  F[Tệp / URL] --> D{Loại tệp}
  D -->|csv| C1[Đọc từng dòng → raw_records<br/>bất biến, sha256]
  D -->|pdf| C2[Render ảnh trang → data/raw<br/>text layer → raw_records]
  D -->|mp3| C3[assets: đường dẫn gốc, thời lượng ffprobe]
  D -->|url| C4[sources: chỉ đăng ký + kiểm tra HTTP]
  C1 --> N[Chuẩn hoá: parser → vocabulary]
  C2 --> T[Chép bằng AI từ ảnh → JSON needs_review<br/>đối chiếu bảng 正解]
  N --> VR[Luật tự động → validation_issues origin=rule]
  T --> VQ[Kiểm tra cấu trúc + AI đối chiếu đáp án]
  VR --> AI[AI rà soát nội dung → origin=ai_review<br/>chỉ đề xuất]
  AI --> S{Có error/warning?}
  S -->|có| NR[needs_review]
  S -->|không| NM[normalized — học được, nhãn 'Chưa xác minh']
  NR & NM & VQ --> H[Màn hình Duyệt: approve / edit / reject / ambiguous / re-extract]
  H -->|approve| VF[verified = CURATED]
  H -->|reject| RJ[rejected — loại khỏi SRS]
```

## 4. Phụ thuộc module

```mermaid
flowchart BT
  kana[validation/kana] --> vocab[validation/vocabulary]
  fc[ingestion/flashcards_csv] --> pipe[ingestion/pipeline]
  vocab --> pipe
  repo --> pipe
  db --> repo
  srs[learning/srs] --> api
  pipe --> api
  repo --> api
  reports --> repo
  api --> main[__main__]
  pipe --> main
  reports --> main
```

`learning/srs.py`, `validation/*` và `ingestion/flashcards_csv.py` là hàm thuần (không DB), kiểm thử độc lập.

## 5. Quyết định kiến trúc (ADR)

| # | Quyết định | Lý do | Hệ quả / nâng cấp |
|---|---|---|---|
| ADR-001 | FastAPI + SQLite + React/TS/Tailwind (đúng gợi ý spec Part 12) | Dự án greenfield; 1 người dùng; offline | Có thể chuyển PostgreSQL khi nhiều người dùng |
| ADR-002 | `sqlite3` chuẩn, SQL tập trung trong `repo.py`, không ORM | Ít phụ thuộc, dễ đọc; repository pattern vẫn tách UI/logic/DB | Migration hiện bằng `CREATE … IF NOT EXISTS`; thêm `PRAGMA user_version` khi đổi schema có dữ liệu |
| ADR-003 | Lớp RAW = bảng `raw_records` với trigger chặn UPDATE/DELETE | Ràng buộc ở DB, không phụ thuộc code | Sửa dữ liệu chỉ ở lớp NORMALIZED |
| ADR-004 | NORMALIZED vs CURATED phân biệt bằng `verification_status`; chỉ API Review (người dùng) đặt `verified` | Tránh nhân bản bảng; một nguồn sự thật | "Curated bank" = `WHERE verification_status='verified'` |
| ADR-005 | Flashcard chưa xác minh vẫn học được, có nhãn | Quyết định của người dùng (phiên 1) | Đề thi chỉ dùng câu đã xác minh |
| ADR-006 | Đề PDF có font CID hỏng → chép bằng AI từ ảnh trang, `needs_review`, đáp án lấy từ 正解 và bị kiểm tra chéo khi import | Không có text layer dùng được; không bịa | Người dùng đối chiếu ảnh gốc trên màn hình Duyệt |
| ADR-007 | AI rà soát chỉ tạo `validation_issues` (origin=ai_review) + `suggestion`, không sửa dữ liệu | Spec §11.5: phân biệt nội dung AI và dữ liệu đã xác minh | Người dùng bấm "Điền gợi ý" rồi Duyệt |
| ADR-008 | Website bên thứ ba: chỉ đăng ký + kiểm tra truy cập HTTP | Spec §2.2: không vượt rào, không thay câu hỏi bằng AI | Trích xuất từng site cần đánh giá điều khoản sử dụng trước |
| ADR-009 | Phát âm dùng Web Speech API, ghi rõ "giọng máy" | Không có audio gốc cho từ vựng | Không bao giờ gán nhãn audio gốc |
| ADR-010 | Điều hướng bằng hash, không thêm router | 5 trang; ít phụ thuộc | Thêm react-router khi cần route lồng nhau |
| ADR-011 | ID từ vựng `VOC_xxxxxx` cấp theo thứ tự import (tệp sắp xếp theo tên, dòng theo thứ tự); file AI review chỉ áp khi `id` **và** `word` khớp | Ổn định khi import lại; an toàn nếu ID lệch | Thêm khoá nội dung nếu bổ sung nhiều nguồn mới |

## 6. Thời gian & điểm thi
- Thời gian đề hiện hành (20/40/30 phút) sẽ dùng cho đề mock; đề mẫu chính thức giữ `duration_minutes = null` vì tài liệu gốc không ghi.
- Điểm: sẽ tách "kết quả luyện tập" (đúng/sai/%) và "ước lượng sẵn sàng" có nhãn rõ — chưa triển khai (phiên sau).
