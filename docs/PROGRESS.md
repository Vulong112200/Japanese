# PROGRESS — Japanese N5 Learning Hub

Cập nhật: 2026-11-14, kết thúc phiên 2. Trạng thái dựa trên kết quả kiểm thử: **57/57 test pass**, frontend build sạch.

## Tóm tắt các phiên
| Phiên | Nội dung | Kết quả |
|---|---|---|
| 1 | Audit (greenfield); schema; DB; Source Library; nhập CSV + đề mẫu; luật kiểm tra; SRS; màn hình Duyệt; báo cáo | 56 test pass |
| 2 | Tự tải nguồn online; dựng từ điển JMdict/KANJIDIC2; **rà soát và sửa toàn bộ từ vựng** (2 vòng AI + từ điển + người duyệt cuối); nhóm động từ theo thể từ điển; push GitHub | 963/963 từ vựng `verified` (AI); 167 bản sửa; 57 test pass |

## Ma trận module

Ký hiệu trạng thái:
- ✅ **Hoàn thành**: có test.
- 🟡 **Một phần**: làm được một phần.
- ⬜ **Chưa làm**.
- 🔒 **Bị chặn**: cần đăng nhập hoặc export từ phía người dùng.

| Module (spec) | Trạng thái | Ghi chú |
|---|---|---|
| M01 Source Library | ✅ | Đăng ký URL, quét thư mục, sha256/trùng lặp, trạng thái xử lý và truy cập, xử lý lại, export. Chưa có: upload tệp qua UI, ZIP, preview. |
| M02 Ingestion CSV | ✅ | 3 định dạng, idempotent, RAW bất biến |
| M02 Ingestion PDF | 🟡 | Render ảnh trang, text layer. Đề mẫu chép bằng AI (vision). PDF scan cần OCR (chưa có tesseract). |
| M02 Ingestion Audio | 🟡 | Phát, tua (HTTP 206), thời lượng. Chưa có timestamp từng câu. |
| M02 Website | 🟡 | Kiểm tra truy cập đúng thực tế. Tải được Google Docs (export txt) và Drive công khai. Chưa trích nội dung website bên thứ ba (ADR-008). |
| Từ điển tham chiếu | ✅ | JMdict (đọc, từ loại, nhóm động từ), KANJIDIC2 (Hán-Việt) kèm `HV_OVERRIDES` |
| Data quality §11 | ✅ | Luật, từ điển, rà soát AI 2 vòng, bản sửa có truy vết, màn hình Duyệt, quy tắc người dùng luôn thắng |
| Vocabulary §7.1 | ✅ | 963 mục đã xác minh. Có tìm kiếm/lọc, chi tiết (từ loại, nhóm, thể từ điển, lịch sử sửa, RAW), phát âm giọng máy. Chưa có: lọc theo từ loại/chủ đề trên UI, từ liên quan. |
| SRS §8 | ✅ | SM-2, 2 chiều, giới hạn thẻ mới/ngày, mastered ≥3 lần liên tiếp và ≥21 ngày |
| Dashboard §13 | 🟡 | Có số liệu thật về từ vựng/SRS/chất lượng. Chưa có kanji/ngữ pháp/kết quả thi. |
| Grammar §7.3 | 🟡 | Đã tải nguồn: Google Doc "Cẩm nang ngữ pháp N5 Minna bài 1–25" (389 dòng) ở `data/raw/SRC_GDOC_001/`. **Chưa** parse/nhập/rà soát. |
| Kanji §7.2 | 🟡 | Đã tải PDF Drive: 160 kanji N5–N4, 214 bộ thủ. Đây là PDF scan, cần OCR. Có thể dựng danh sách kanji N5 từ KANJIDIC2 (cờ jlpt_old) kèm từ ví dụ trong từ vựng đã xác minh. |
| Kaiwa §7.4 | ⬜ | Đã có từ vựng Kaiwa (60 dòng) |
| Mock Exam §9 | ⬜ | Đã có dữ liệu 29 câu đề mẫu chính thức (needs_review), audio, đáp án, giải thích. Chưa có giao diện thi. |
| Listening §10 | 🟡 | Audio và script hiện trên màn hình Duyệt. Chưa có chế độ thi/học. |
| Analytics §14 | ⬜ | Đã có review_log |
| Backup/restore | 🟡 | Copy `data/database/hub.sqlite` (README). Chưa có UI. |
| Offline | ✅ | Chạy trên localhost, không dùng CDN |

## Dữ liệu (đã import vào DB)
- **Từ vựng**: 991 dòng CSV → 963 mục.
  - 12 dòng trùng hoàn toàn được gộp; 16 dòng hỏi–đáp của bộ Số Đếm chỉ giữ ở RAW.
  - **963 mục `verified` bởi AI**.
  - 167 bản sửa: han_viet 59, example_romaji 40, example_jp 14, romaji 14, word 13, reading 11, example_vi 9, meaning_vi 7.
  - Chi tiết từng bản sửa: `docs/DATA_QUALITY_REPORT.md`.
- **Nhóm động từ**: 143 động từ đều có nhóm (nhóm 1: 77, nhóm 2: 41, nhóm 3: 25), lấy từ thể từ điển.
- **Đề mẫu**: 29 câu, 4 đoạn văn, 29 ảnh trang, 1 audio. Đáp án khớp 正解 29/29. Bản chép câu hỏi vẫn ở trạng thái `needs_review`.
- **Thiếu**: không có `flashcards_Bai15.csv`; `flashcards_Bai18.csv` chỉ có 1 dòng.

## Nguồn trực tuyến (kiểm tra 2026-11-14)
- **Đã tải về** (lưu ở `data/raw/`, không commit):
  - Google Docs ngữ pháp, dạng txt.
  - Thư mục Drive "Kho tài liệu N5": Tong-hop-tu-vung-N5.pdf, Tu-vung-N5.pdf, 160-kanji-n5-n4.pdf, 214 bộ thủ, phó từ/tự-tha động từ.
  - Riêng file "120 Kanji" tải lỗi; 4 thư mục con (đề 2017, kanji, kaiwa video, tài liệu thêm) chưa tải.
- **Truy cập được**: Migii, Nihonez, NHK, Riki (render bằng JS), YouTube (đã lấy metadata oEmbed), jlpt.jp ×2, VTI Mirai, GoJapan (có 10 đề, cần đánh giá điều khoản trước khi trích).
- **Không đọc được**: tailieuhoctiengnhat (bị chặn bởi trang xác minh chống bot, không vượt), HanoiLink (lúc timeout, lúc tải được, chưa phân tích).
- **Cần đăng nhập Google**: NotebookLM (10 link) và Google Notebook. Các link chia sẻ đều chuyển về trang yêu cầu đăng nhập, nội dung render phía client nên không đọc được.

## Việc tiếp theo (theo thứ tự)
1. **Ngữ pháp (Phase 3)**:
   - Parse `data/raw/SRC_GDOC_001/grammar_handbook.txt` thành bảng `grammar` theo `schemas/grammar.schema.json`.
   - Rà soát theo quy trình ở CLAUDE.md §6.
   - Làm UI tra cứu và học ngữ pháp.
2. **Mock Exam Engine (Phase 5)**:
   - Thi theo section/mondai bằng 29 câu đề mẫu.
   - Timer theo section; đề mẫu không có thời gian gốc nên cho người dùng tự chọn.
   - Ẩn đáp án và lựa chọn chỉ có trong audio ở chế độ thi.
   - Lưu bài làm; tách kết quả luyện tập với ước lượng sẵn sàng.
   - Trước đó cần xác minh bản chép 29 câu với ảnh trang (vòng vision thứ 2).
3. **Kanji**: danh sách N5 từ KANJIDIC2 (jlpt_old=4, khoảng 80 chữ) kèm từ ví dụ từ vựng đã xác minh. Cân nhắc OCR các PDF Drive.
4. Tải nốt các thư mục con trên Drive (đề N5 2017 nếu có audio và đáp án); upload tệp/ZIP qua UI; backup/restore qua UI.
