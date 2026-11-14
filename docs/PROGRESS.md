# PROGRESS — Japanese N5 Learning Hub

Cập nhật: 2026-11-14 (phiên 1). Trạng thái được xác định theo kết quả kiểm thử, không theo giao diện.

## Phase 0: Audit (hoàn thành)
- Hiện trạng: dự án greenfield. `D:\Japanese` lúc đầu chỉ có `docs/` gồm spec và dữ liệu, chưa có code. `D:\Mori_AI_Local` là dự án khác, không liên quan.
- Môi trường máy: Windows 11, Python 3.14, Node 24, ffprobe. Chưa có tesseract và poppler-data.
- Dữ liệu đề thi: bộ 問題例 N5 gồm mondai (22 trang), seikai, script (3 trang), kaitou (3 trang) và MP3 316 giây.
  - Text layer PDF hỏng: font CID không có ToUnicode.
- Dữ liệu flashcard: 26 tệp CSV, 991 dòng, 3 định dạng.
  - Không có Bai15; Bai18 chỉ có 1 dòng.
  - Dữ liệu do AI tạo và có lỗi: 68 lỗi nội dung do AI rà soát phát hiện, cộng thêm lỗi định dạng do luật tự động bắt được.

## Ma trận module

Ký hiệu trạng thái:
- ✅ **Hoàn thành**: đã kiểm thử.
- 🟡 **Một phần**: làm được một phần.
- 🔵 **Cần người dùng**: cần dữ liệu hoặc thao tác của người dùng.
- 🔒 **Bị chặn**: cần truy cập bên ngoài.
- ⬜ **Chưa làm**: chưa triển khai.

| Module (spec) | Trạng thái | Ghi chú / kiểm thử |
|---|---|---|
| M01 Source Library | ✅ | Đăng ký URL, quét thư mục, tìm/lọc, trạng thái xử lý và truy cập, phát hiện trùng theo sha256, xử lý lại, export JSON (`test_api::test_sources`). Chưa có: upload tệp qua UI, nhập ZIP, preview tài liệu. |
| M02 Ingestion: CSV | ✅ | 3 định dạng, idempotent, RAW bất biến (`test_units`, `test_data`) |
| M02 Ingestion: PDF | 🟡 | Render ảnh trang và lấy text layer. Câu hỏi chép bằng AI (vision) cho bộ đề mẫu. Chưa có trích xuất tổng quát hay OCR. |
| M02 Ingestion: Audio | 🟡 | Đăng ký asset, đo thời lượng, phát và tua (HTTP Range 206). Chưa có timestamp từng câu. |
| M02 Ingestion: Website | 🟡 | Đăng ký và kiểm tra truy cập HTTP. Chưa trích nội dung (ADR-008). |
| JSON schemas | ✅ | 6 schema, kiểm tra trên toàn bộ dữ liệu thật và mẫu của spec |
| Data quality §11 | ✅ | Luật tự động, AI rà soát (chỉ đề xuất), màn hình Duyệt (approve / edit / reject / ambiguous / re-extract), nhật ký duyệt |
| Vocabulary learning §7.1 | 🟡 | Danh sách, tìm kiếm, lọc theo bài và trạng thái, chi tiết kèm nguồn gốc, phát âm giọng máy. Chưa có lọc theo từ loại/chủ đề trên UI và từ liên quan. |
| SRS §8 | ✅ | SM-2 với Again/Hard/Good/Easy, 2 chiều, giới hạn thẻ mới/ngày, mastered ≥3 lần liên tiếp và ≥21 ngày (`test_units`, `test_api`) |
| Dashboard §13 | 🟡 | Chuỗi ngày, lượt ôn, thẻ đến hạn, mức thuộc, chất lượng dữ liệu, bài hay quên. Chưa có kanji, ngữ pháp, kết quả thi. |
| Kanji §7.2 | 🔵 | Chưa có nguồn cục bộ đáng tin. Đã có schema. |
| Grammar §7.3 | 🔒 | Cần export Google Docs (SRC_GDOC_001) hoặc NotebookLM. Đã có schema. |
| Kaiwa §7.4 | ⬜ | Đã nhập từ vựng Kaiwa (60 dòng). Chưa có module hội thoại. |
| Mock Exam Engine §9 | ⬜ | Đã có dữ liệu: 29 câu, passage, audio, đáp án. Chưa có giao diện thi, timer, chấm điểm. |
| Listening §10 | 🟡 | Đã có audio và script trên màn hình Duyệt. Chưa có chế độ thi/học riêng. |
| Analytics §14 | ⬜ | Chỉ có review_log. Chưa có phân tích điểm yếu theo chủ điểm. |
| Backup/restore | 🟡 | Sao lưu thủ công bằng cách copy `data/database/hub.sqlite` (README). Chưa có UI. |
| Offline | ✅ | Toàn bộ chạy trên localhost, font hệ thống, không dùng CDN |

## Nguồn trực tuyến (kiểm tra ngày 2026-11-14)
- **Truy cập được (7)**: Migii, Nihonez, NHK Hiragana, Riki, YouTube, jlpt.jp ×2.
- **Không truy cập được từ máy (4)**:
  - GoJapan: lỗi chứng chỉ SSL cục bộ.
  - HanoiLink: timeout.
  - VTI Mirai: HTTP 500.
  - tailieuhoctiengnhat: timeout.
- **Cần đăng nhập Google (2)**: Google Drive, Google Docs.
- **Cần export thủ công (11)**: 10 liên kết NotebookLM và Google Notebook.

## Quyết định đã chốt với người dùng
1. Flashcard chưa xác minh vẫn học được, có nhãn. Đề thi chỉ dùng câu đã xác minh.
2. Phiên 1 làm nền tảng, từ vựng và SRS. Đề mẫu lưu ở trạng thái `needs_review`.
3. Người dùng yêu cầu AI tự rà soát tính đúng sai của bài học và đáp án:
   - Đề mẫu: đã đối chiếu 29/29 câu, đều nhất quán.
   - Flashcard: 68 phát hiện được gắn vào màn hình Duyệt.

## Việc tiếp theo (đề xuất theo thứ tự)
1. **Mock Exam Engine** (Phase 5):
   - Thi theo mondai/section bằng 29 câu đề mẫu.
   - Timer theo section; đề mẫu không có thời gian gốc nên cho người dùng tự chọn.
   - Ẩn đáp án và lựa chọn chỉ có trong audio ở chế độ thi.
   - Lưu bài làm và kết quả; tách điểm luyện tập với ước lượng sẵn sàng.
2. **Người dùng duyệt**:
   - 84 mục từ vựng cần duyệt.
   - 29 câu đề mẫu: đối chiếu với ảnh trang; riêng câu V03 có lựa chọn dạng glyph.
3. **Nhập ngữ pháp**: cần người dùng export Google Docs ra `.docx`/`.txt`, đặt vào `docs/N5/grammar/`.
4. Backup/restore qua UI; upload tệp và nhập ZIP.
