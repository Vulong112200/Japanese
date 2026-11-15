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
  validation/numbers.py     luật biến âm số đếm/trợ số từ/ngày tháng (expected_readings, naive_readings) (ADR-029)
  learning/srs.py           SM-2 (hàm thuần)
  learning/exam.py          chấm điểm thi, ước lượng sẵn sàng, đồng hồ (hàm thuần)
  learning/analytics.py     thời gian học ước tính + gợi ý hoạt động tiếp theo (hàm thuần)
  learning/question_gen.py  sinh câu 漢字読み/表記 bằng luật từ dữ liệu đã verified (hàm thuần)
  reports.py                sinh docs/IMPORT_REPORT.md, SOURCE_CATALOG.md, DATA_QUALITY_REPORT.md
backend/scripts/ocr_batch.py OCR hàng loạt PDF Drive → data/raw/SRC_LESSON_002/ocr/*.json (bố cục cột từng file)
backend/scripts/merge_past_exams.py  gộp bản chép + key cộng đồng + 2 AI + quyết định duyệt → đề thật (docs/PAST_EXAMS.md)
backend/scripts/listening_timestamps.py  căn ASR Whisper với script → mốc thời gian từng câu nghe (ADR-025)
backend/tests/              pytest: test_units (thuần), test_data (dữ liệu thật), test_api (end-to-end), test_knowledge, test_exam
frontend/src/               React + TS + Tailwind; pages/: Dashboard (có sao lưu/khôi phục), Vocabulary, Grammar, Kanji, Numbers (số đếm), Kaiwa (hội thoại), Flashcards, Exam (thi thử), Analytics (thống kê), Review, Library
schemas/*.schema.json       định dạng trao đổi JSON (được test kiểm)
data/
  sources_online.json       registry nguồn trực tuyến
  normalized/corrections/vocabulary_corrections.json   bản sửa từ vựng CSV đã duyệt + danh sách mục đã audit
  normalized/supplements/vocabulary_supplement.json    290 từ bổ sung (Minna thiếu + JLPT N5), nguồn + review_log
  normalized/grammar/n5_grammar_checklist.json         khung 135 điểm ngữ pháp N5 (đo độ phủ)
  normalized/grammar/grammar.json                      nội dung 135 điểm (origin handbook/handbook+ai/ai)
  normalized/kanji/kanji_n5.json                       103 kanji N5
  normalized/grammar_questions/grammar_questions.json  399 câu 文の文法1/2 do agent soạn (ADR-020)
  normalized/kaiwa/kaiwa.json                           27 hội thoại Kaiwa §7.4, 9 chủ đề (ADR-023)
  normalized/reading_questions/reading_questions.json   68 bài / 142 câu 文章の文法 + 読解 do agent soạn (ADR-026)
  normalized/numbers/numbers.json                       273 mục số đếm & ngày tháng, 23 nhóm (ADR-029)
  normalized/exams/listening_timestamps.json            mốc giây từng câu nghe (chỉ số, được commit; ADR-025)
  normalized/ai_review/     kết quả rà soát AI (bằng chứng; grammar_questions_review.json / reading_questions_review.json = 2 AI giải mù; kaiwa_review.json = 2 vòng rà soát hội thoại)
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
- **Đề thi**: đề chính thức chỉ lấy đáp án từ 正解. Đề thật các năm (ADR-019) dùng đáp án cộng đồng, đối chiếu 2 AI giải độc lập; chỉ `verified` khi key = A = B, có nhãn `COMMUNITY_KEY`/`AI_ANSWERED`, `is_official=0`. Không bịa câu hỏi. Không tạo audio thay thế. Lựa chọn chỉ có trong audio thì phải ẩn ở chế độ thi.
  - Không trích đề từ website bên thứ ba (nihonez cấm scrape; gojapan không công bố đáp án, giữ bản quyền). Xem bảng nguồn trong docs/PROGRESS.md.
  - Câu luyện tập tự sinh nằm trong đề `BANK_N5_GENERATED` (`is_official=0`, nhãn AI_GENERATED), `verified_by='generator'`. Chỉ sinh từ dữ liệu verified; phương án nhiễu phải được chứng minh sai bằng JMdict (ADR-017). Câu không sinh lại được thì `rejected`, không xoá (lịch sử thi tham chiếu).
  - Chế độ thi không được trả về đáp án/giải thích/script trước khi nộp (ADR-018, có test).
  - Câu ngữ pháp do agent soạn (ADR-020) nằm trong đề `BANK_N5_GRAMMAR_AI`, `verified_by='ai'` chỉ khi qua luật `check_grammar_question` và key = 2 AI giải mù. Sửa câu: sửa file + `review_log`, rồi **giải mù lại** câu đó (cập nhật `grammar_questions_review.json`) trước khi `import`; loại: `excluded: true`.
  - Bài đọc do agent soạn (ADR-026) nằm trong đề `BANK_N5_READING_AI`, cùng quy tắc trên (luật `check_reading_group` + key = 2 AI giải mù, bằng chứng `reading_questions_review.json`). Mỗi mục là 1 bài; sửa bài thì giải mù lại mọi câu của bài đó. Lấy mẫu luyện tập không được cắt rời bài đọc (có test).
  - Mốc thời gian câu nghe (ADR-025): chỉ sinh bằng `scripts/listening_timestamps.py` từ ASR + script; câu không qua kiểm tra thì không có mốc (vẫn nghe cả track). Không sửa tay số giây.
- **Bản quyền**: không commit đề JLPT (PDF/MP3), ảnh trang, bản chép đề, hay PDF tải từ Drive (`.gitignore` đã chặn). Kiểm `git diff --cached --name-only` trước khi push.

- **Từ vựng bổ sung / ngữ pháp / kanji**: nguồn chuẩn là các file trong `data/normalized/` ở trên.
  - Sửa nội dung bằng cách sửa file: đổi trường cần sửa, ghi `review_log`, giữ `audited: true`. Sau đó chạy `import`.
  - Importer đồng bộ các dòng DB theo file, trừ mục người dùng đã sửa hoặc duyệt.
  - Mục bị loại thì đặt `excluded: true` (DB sẽ lưu trữ mục đó, không xoá).
  - Từ loại của từ vựng do JMdict quyết định, không lấy từ file.
- **Độ phủ N5 đã đạt** (phiên 3): từ vựng phủ danh sách JLPT N5 và đủ 25 bài Minna; 103/103 kanji; 135 điểm ngữ pháp. **Không cần thu thập thêm tài liệu kiến thức.** Việc tiếp theo là tính năng (thi thử, luyện tập), không phải dữ liệu.
  - Ngữ pháp đã xong rà soát vòng 2 (phiên 4): 135/135 verified. Bằng chứng: `data/normalized/ai_review/grammar_round2.json`. Sửa ngữ pháp về sau: dùng `backend/scripts/apply_grammar_review.py`.
- **Mock exam** (phiên 4) đã có. **6 đề thật các năm** (phiên 5, ADR-019) đã nhập: bản chép ở `data/normalized/exams/EXAM_N5_20*.json` (không commit), file gốc ở `data/raw/SRC_DRIVE_EXAM_N5_*`. Quy trình + nơi lưu + nhật ký duyệt: `docs/PAST_EXAMS.md` (script `backend/scripts/merge_past_exams.py`). Khi key cộng đồng lệch AI: chọn theo căn cứ chính xác nhất, giải thích được (người dùng uỷ quyền). **Câu ngữ pháp 文の文法1/2** (phiên 6, ADR-020): 399 câu verified. **SRS ngữ pháp/kanji + Dashboard "Ngữ pháp cần ôn"** (phiên 7, ADR-021) đã có. **Mục tiêu ngày, "Học gì tiếp", trang Thống kê, luyện theo 1 điểm ngữ pháp** (phiên 8, ADR-022; `learning/analytics.py`, bảng `settings`). **Kaiwa §7.4** (phiên 9, ADR-023): 27 hội thoại verified, không bao giờ vào đề thi; sửa qua file + `review_log` rồi `import`. **Sao lưu/khôi phục qua UI** (ADR-024: `GET /api/backup`, `POST /api/restore` thân thô, tự lưu bản trước khi ghi đè). **Mốc thời gian câu nghe** (phiên 10, ADR-025): 144/144 câu đề thật. **Bài đọc 文章の文法/読解** (phiên 10, ADR-026): 142 câu verified. **Flashcard ôn tổng hợp** (phiên 11, ADR-027): 500 thẻ mới/ngày, lọc khoảng bài, xáo trộn, `/api/srs/cram` (chỉ ghi "Quên" vào SRS). **Ôn ngữ pháp gom nhiều bài** (phiên 12, ADR-028): `lesson_from`/`lesson_to` trên `/api/attempts` (26 = N5 bổ sung), panel ở trang Ngữ pháp. **Số đếm & ngày tháng** (phiên 13, ADR-029): trang Số đếm, SRS `number`, đề `BANK_N5_NUMBERS`; sửa nội dung qua file + `review_log` rồi `import` (luật `check_number_item` phải sạch; cách đọc phải khớp `validation/numbers.py`). Việc tiếp theo: upload/ZIP qua UI (người dùng hoãn; xem docs/PROGRESS.md).

## 6. Quy trình rà soát nội dung (đã dùng cho từ vựng, kanji và ngữ pháp)
1. Dump dữ liệu kèm bằng chứng từ điển ra TSV (scratchpad), chia khoảng 4 lô.
2. Chạy agent song song. Mỗi agent đọc toàn bộ lô của mình và trả về JSON gồm `{id, word, field, old_value, new_value, reason_vi, confidence}`.
3. Chạy vòng thứ hai với cách chia lô khác. Người duyệt cuối xem từng đề xuất, loại những đề xuất sai.
4. Ghi các đề xuất đã chấp nhận vào file corrections, chạy `import`, rồi chạy `pytest`. Sinh lại báo cáo bằng `report`.

## 7. Git
- Remote: `https://github.com/Vulong112200/Japanese.git`, nhánh `main`. Commit message viết tiếng Việt, kết bằng dòng attribution được cung cấp trong phiên.
- Trước khi commit: chạy pytest + `npm run build` đều xanh, rồi kiểm tra không có file bản quyền hoặc file DB lọt vào commit.
