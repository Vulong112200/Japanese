# CLAUDE.md — Japanese N5 Learning Hub

Hướng dẫn cho mọi session Claude Code làm việc trên repo này. Đọc file này trước, rồi đọc `docs/PROGRESS.md` để biết đang ở giai đoạn nào.

## 1. Dự án là gì
- Ứng dụng ôn tập và thi thử **JLPT N5** cho người Việt. Local-first, chạy offline trên `http://127.0.0.1:8000`.
- Đặc tả gốc: `docs/PROJECT_MASTER_SPECIFICATION.md`. Đây là nguồn yêu cầu, không sửa.
- Người dùng giao tiếp bằng tiếng Việt. Báo cáo cuối phiên theo mẫu: Files created / modified, Features, Tests, Results, Known issues, Data import status, Remaining tasks, Next step.

## 2. Cách làm việc người dùng muốn
- **Tự làm, đừng đẩy việc cho người dùng.** Tự tải URL (Google Docs export, thư mục Drive công khai, từ điển…), tự đối chiếu, tự sửa. Chỉ hỏi khi thật sự bị chặn (ví dụ trang yêu cầu đăng nhập).
- **Dữ liệu học do AI miễn phí tạo, có lỗi.** Sửa lỗi một cách tự tin, nhưng phải kiểm nhiều lớp: luật tự động, từ điển (JMdict/KANJIDIC2), ít nhất 2 vòng rà soát độc lập, rồi người duyệt cuối.
- Không làm màn hình minh hoạ. Không dùng dữ liệu giả nếu không gắn nhãn DEMO. Không đánh dấu module "hoàn thành" khi chưa có test cho chức năng chính.
- Mỗi phiên làm một nhóm chức năng hoàn chỉnh, xong thì cập nhật `docs/PROGRESS.md` và các ADR.

## 3. Cấu trúc
```
backend/hub/                FastAPI + SQLite (sqlite3 chuẩn, SQL tập trung ở repo.py)
  db.py                     schema DDL + migration cột (ALTER TABLE khi thiếu)
  repo.py                   toàn bộ SQL (repository)
  api.py                    REST /api/* (mỏng) + phục vụ frontend/dist
  ingestion/pipeline.py     inventory, nguồn online, nhập CSV, áp bản sửa, kiểm định, nhập đề mẫu, run_all
  ingestion/knowledge.py    từ vựng bổ sung, ngữ pháp, kanji N5 + kiểm tra tự động cho từng loại
  ingestion/ocr.py          Tesseract OCR (bảng theo cột, xoá đường kẻ); dùng cho PDF scan
  ingestion/flashcards_csv.py  parser 3 định dạng CSV (hàm thuần)
  validation/kana.py        kana→romaji, regex kana/kanji
  validation/vocabulary.py  luật kiểm tra từ vựng (hàm thuần)
  validation/reference.py   tra JMdict/KANJIDIC2 (data/reference/reference.sqlite), nhóm động từ, Hán-Việt
  learning/srs.py           SM-2 (hàm thuần)
  reports.py                sinh docs/IMPORT_REPORT.md, SOURCE_CATALOG.md, DATA_QUALITY_REPORT.md
backend/scripts/ocr_batch.py OCR hàng loạt PDF Drive → data/raw/SRC_LESSON_002/ocr/*.json (bố cục cột từng file)
backend/tests/              pytest: test_units (thuần), test_data (dữ liệu thật), test_api (end-to-end), test_knowledge
frontend/src/               React + TS + Tailwind; pages/: Dashboard, Vocabulary, Grammar, Kanji, Flashcards, Review, Library
schemas/*.schema.json       định dạng trao đổi JSON (được test kiểm)
data/
  sources_online.json       registry nguồn trực tuyến
  normalized/corrections/vocabulary_corrections.json   bản sửa từ vựng CSV đã duyệt + danh sách mục đã audit
  normalized/supplements/vocabulary_supplement.json    290 từ bổ sung (Minna thiếu + JLPT N5), nguồn + review_log
  normalized/grammar/n5_grammar_checklist.json         khung 135 điểm ngữ pháp N5 (đo độ phủ)
  normalized/grammar/grammar.json                      nội dung 135 điểm (origin handbook/handbook+ai/ai)
  normalized/kanji/kanji_n5.json                       103 kanji N5
  normalized/ai_review/     kết quả rà soát AI vòng 1 (bằng chứng)
  normalized/exams/         đề mẫu đã chép (bản chép không commit, xem .gitignore) + AI đối chiếu đáp án
  reference/jlpt_n5_words.csv  danh sách JLPT N5 (718 từ) để đo độ phủ
  raw/ reference/*.gz,*.sqlite,tessdata/ database/   sinh ra trên máy, không commit
docs/                       PROGRESS (tiến độ), ARCHITECTURE (sơ đồ + ADR), DATA_DICTIONARY, báo cáo sinh tự động
docs/N5/                    dữ liệu gốc của người dùng: CHỈ ĐỌC
```

## 4. Lệnh
Môi trường là Windows và Git Bash. Python nằm trong `backend/.venv`. Đặt `PYTHONIOENCODING=utf-8` hoặc dùng `-X utf8` khi in tiếng Nhật/Việt ra console.
```bash
cd backend
.venv/Scripts/python -m hub build-reference   # tải + dựng từ điển (lần đầu, ~1 phút)
# OCR (chỉ khi cần đọc PDF scan): winget install UB-Mannheim.TesseractOCR, rồi tải jpn/jpn_vert/vie/eng
# .traineddata (tessdata_best) vào data/reference/tessdata/. hub/ingestion/ocr.py dùng thư mục đó.
.venv/Scripts/python -m hub import            # nhập/cập nhật toàn bộ, an toàn khi chạy lại
.venv/Scripts/python -m hub serve             # http://127.0.0.1:8000
.venv/Scripts/python -m hub check-online      # kiểm tra truy cập nguồn online
.venv/Scripts/python -m hub report            # sinh lại 3 báo cáo trong docs/
.venv/Scripts/python -m pytest tests -q       # toàn bộ test (cần đã build-reference)
cd ../frontend && npm run build               # tsc + vite build → frontend/dist (server phục vụ)
```

## 5. Quy tắc dữ liệu (bắt buộc)
- **RAW bất biến**: bảng `raw_records` có trigger chặn UPDATE/DELETE. `docs/N5/**` không bao giờ bị sửa.
- **Sửa dữ liệu** chỉ ở lớp NORMALIZED, và chỉ qua 1 trong 2 đường:
  1. Thêm mục vào `data/normalized/corrections/vocabulary_corrections.json`. Mỗi mục có `id`, `raw_word`, `field`, `old_value`, `new_value`, `reason_vi`, `basis`. Chạy `import` để áp. Hàm áp kiểm tra `old_value` và `raw_word`, mọi thay đổi được ghi vào `review_actions`.
  2. Người dùng sửa trên màn hình Duyệt. Mục đó thành `verified_by='pending_user'`, sau khi duyệt thành `'user'`. Automation không động vào nữa.
- **`verification_status='verified'`** chỉ đặt được khi:
  - `verified_by='ai'`: mục nằm trong `audit.items` của file corrections **và** không còn issue error/warning nào từ luật hoặc từ điển; hoặc
  - `verified_by='user'`: người dùng bấm Duyệt.
- **Nhóm động từ** lấy từ thể từ điển trong JMdict, không bao giờ suy từ đuôi ます (spec §6.1).
- **Hán-Việt** đối chiếu KANJIDIC2. KANJIDIC2 sai với một số chữ shinjitai, nên có `HV_OVERRIDES` trong `validation/reference.py`. Chỉ thêm vào đó khi chắc chắn.
- **Đề thi**: đáp án chỉ lấy từ 正解 chính thức. Không bịa câu hỏi. Không tạo audio thay thế. Lựa chọn chỉ có trong audio thì phải ẩn ở chế độ thi.
- **Bản quyền**: không commit đề JLPT (PDF/MP3), ảnh trang, bản chép đề, hay PDF tải từ Drive (`.gitignore` đã chặn). Kiểm `git diff --cached --name-only` trước khi push.

- **Từ vựng bổ sung / ngữ pháp / kanji**: nguồn chuẩn là các file trong `data/normalized/` ở trên.
  - Sửa nội dung bằng cách sửa file: đổi trường cần sửa, ghi `review_log`, giữ `audited: true`. Sau đó chạy `import`.
  - Importer đồng bộ các dòng DB theo file, trừ mục người dùng đã sửa hoặc duyệt.
  - Mục bị loại thì đặt `excluded: true` (DB sẽ lưu trữ mục đó, không xoá).
  - Từ loại của từ vựng do JMdict quyết định, không lấy từ file.
- **Độ phủ N5 đã đạt** (phiên 3): từ vựng phủ danh sách JLPT N5 và đủ 25 bài Minna; 103/103 kanji; 135 điểm ngữ pháp. **Không cần thu thập thêm tài liệu kiến thức.** Việc tiếp theo là tính năng (thi thử, luyện tập), không phải dữ liệu.
  - **Còn dở**: rà soát vòng 2 cho ngữ pháp, nên 135 điểm vẫn ở `needs_review`. Áp kết quả bằng `backend/scripts/apply_grammar_review.py` (xem docs/PROGRESS.md).

## 6. Quy trình rà soát nội dung (đã dùng cho từ vựng, kanji và ngữ pháp)
1. Dump dữ liệu kèm bằng chứng từ điển ra TSV (scratchpad), chia khoảng 4 lô.
2. Chạy agent song song. Mỗi agent đọc toàn bộ lô của mình và trả về JSON gồm `{id, word, field, old_value, new_value, reason_vi, confidence}`.
3. Chạy vòng thứ hai với cách chia lô khác. Người duyệt cuối xem từng đề xuất, loại những đề xuất sai.
4. Ghi các đề xuất đã chấp nhận vào file corrections, chạy `import`, rồi chạy `pytest`. Sinh lại báo cáo bằng `report`.

## 7. Git
- Remote: `https://github.com/Vulong112200/Japanese.git`, nhánh `main`. Commit message viết tiếng Việt, kết bằng dòng attribution được cung cấp trong phiên.
- Trước khi commit: chạy pytest + `npm run build` đều xanh, rồi kiểm tra không có file bản quyền hoặc file DB lọt vào commit.
