# PROGRESS — Japanese N5 Learning Hub

Cập nhật: 2026-11-14, kết thúc phiên 3. Trạng thái dựa trên kết quả kiểm thử: **68/68 test pass**, frontend build sạch.

## Tóm tắt các phiên
| Phiên | Nội dung | Kết quả |
|---|---|---|
| 1 | Audit (greenfield); schema; DB; Source Library; nhập CSV + đề mẫu; luật kiểm tra; SRS; màn hình Duyệt | 56 test |
| 2 | Tự tải nguồn online; JMdict/KANJIDIC2; rà soát + sửa 963 từ vựng (167 bản sửa); CLAUDE.md | 963/963 từ vựng verified (AI); 57 test |
| 3 | Cài OCR Tesseract; OCR PDF Drive; **hoàn thiện kiến thức N5**: +290 từ vựng (bài 15, 18, từ Minna bị thiếu, danh sách JLPT N5), 103 kanji, 135 điểm ngữ pháp; trang Ngữ pháp + Kanji (có luyện đọc) | 1.253 từ vựng + 103 kanji verified; 135 ngữ pháp chờ rà soát vòng 2; 68 test |

## Độ phủ kiến thức N5: ĐÃ ĐỦ, không cần thu thập thêm tài liệu
| Mảng | Độ phủ | Trạng thái xác minh |
|---|---|---|
| Từ vựng | 1.253 mục, đủ 25 bài Minna; phủ toàn bộ danh sách JLPT N5 (718 từ: 699 khớp trực tiếp, 19 khớp qua dạng khác như 後→後で; riêng ～がる là N4) | 1.253/1.253 verified (AI): rà soát 2 vòng + JMdict/KANJIDIC2 |
| Kanji | 103/103 chữ N5 (danh sách cấp 4 JLPT cũ), đối chứng với sách Basic Kanji 120 | 103/103 verified (AI): 2 vòng + KANJIDIC2/JMdict |
| Ngữ pháp | 135 điểm: 121 điểm Minna 1–25 + 14 điểm N5 bổ sung/đối chiếu (は/が, に/で, もう/まだ, しか, ながら, でしょう…); 75 điểm từ cẩm nang của bạn (đã sửa 20 chỗ sai), 60 điểm AI soạn mới | **needs_review**: vòng 2 bị dừng do hết hạn mức API, chạy lại ở phiên sau (xem "Việc tiếp theo") |
| Đề mẫu | 29 câu chính thức, đáp án khớp 正解 29/29 | needs_review (chờ đối chiếu ảnh trang) |

## Ma trận module

Ký hiệu trạng thái:
- ✅ **Hoàn thành**: có test.
- 🟡 **Một phần**: làm được một phần.
- ⬜ **Chưa làm**.
- 🔒 **Bị chặn**: cần đăng nhập.

| Module (spec) | Trạng thái | Ghi chú |
|---|---|---|
| M01 Source Library | ✅ | Gồm cả PDF Drive, docx SourceDocs và nguồn tham chiếu (JLPT list, JMdict, KANJIDIC2). Chưa có: upload tệp qua UI, ZIP, preview. |
| M02 Ingestion CSV / docx | ✅ | |
| M02 OCR | ✅ | Tesseract 5.4 jpn/vie. OCR bảng theo cột, xoá đường kẻ. Đã OCR: Tong-hop-tu-vung-N5 (39 trang), Tu-vung-N5 (63), Basic Kanji 120 (23). Kết quả lưu ở `data/raw/SRC_LESSON_002/ocr/`. |
| M02 Audio | 🟡 | Phát và tua được. Chưa có timestamp từng câu. |
| M02 Website | 🟡 | Kiểm tra truy cập; tải được Google Docs và Drive công khai |
| Data quality §11 | ✅ | Luật tự động, từ điển, rà soát AI 2 vòng, truy vết bản sửa, màn hình Duyệt (từ vựng / câu hỏi / ngữ pháp / kanji qua API) |
| Vocabulary §7.1 | ✅ | |
| Kanji §7.2 | ✅ | Lưới 103 chữ, thẻ chi tiết (Hán-Việt, on/kun, số nét, ví dụ), luyện đọc trắc nghiệm |
| Grammar §7.3 | 🟡 | Có trang tra cứu theo bài (cấu trúc, giải thích, ví dụ, lỗi thường gặp, mẫu tương tự, chỗ sửa so với cẩm nang). Chưa xong rà soát vòng 2. Chưa có bài tập ngữ pháp. |
| SRS §8 | ✅ | Hiện chỉ áp dụng cho từ vựng (2.506 thẻ) |
| Dashboard §13 | 🟡 | Chưa hiện số liệu ngữ pháp/kanji, kết quả thi |
| Kaiwa §7.4 | ⬜ | |
| Mock Exam §9 / Listening §10 | ⬜ | Dữ liệu 29 câu đề mẫu đã sẵn sàng |
| Analytics §14 | ⬜ | |
| Backup/restore | 🟡 | Copy file sqlite |
| Offline | ✅ | |

## Đánh giá các nguồn không tải được
| Nguồn | Có cần không? | Lý do |
|---|---|---|
| 10 link NotebookLM + Google Notebook | **Không cần** | Đây là bài trắc nghiệm ngữ pháp do NotebookLM (AI) sinh từ chính cẩm nang ngữ pháp mà ta đã có. Phải đăng nhập mới xem được, và nội dung không phải đề chính thức. Bài luyện ngữ pháp sẽ được sinh có kiểm soát từ 135 điểm đã chuẩn hoá. |
| tailieuhoctiengnhat (Minna vocab) | **Không cần** | Bị chặn bởi trang xác minh chống bot. Nội dung (từ vựng Minna 1–25) đã có đủ từ 2 PDF Drive (OCR) cộng flashcard của bạn. |
| HanoiLink (từ vựng N5) | **Không cần** | Đã đo độ phủ bằng danh sách JLPT N5 (718 từ), toàn bộ đã có. |
| GoJapan / Migii / Nihonez (đề thi thử) | Tuỳ chọn, chưa cần | Đề của bên thứ ba có bản quyền; spec cấm trích tự động khi chưa xét điều khoản. Đề luyện sẽ dùng đề mẫu chính thức + câu hỏi tự sinh có nhãn AI_GENERATED. |
| Thư mục con trên Drive (Đề thi N5 2017, video kaiwa) | Có ích cho phần thi thử | Có thể tải được (thư mục công khai). Làm khi xây Mock Exam. |

## Việc tiếp theo (theo thứ tự)
1. **Rà soát ngữ pháp vòng 2** (đang dở dang vì hết hạn mức API):
   - Chia `data/normalized/grammar/grammar.json` thành 2 lô, khác cách chia lúc soạn.
   - Chạy 2 agent theo CLAUDE.md §6. Mỗi agent trả về `{id, field, new_value, reason_vi, confidence}`.
   - Người duyệt cuối xét các đề xuất.
   - Chạy `python scripts/apply_grammar_review.py r1.json r2.json`, rồi `python -m hub import` và `pytest`.
2. **Mock Exam Engine (Phase 5)**:
   - Thi theo section/mondai với timer, auto-save, chấm điểm, kết quả. Tách kết quả luyện tập với ước lượng sẵn sàng.
   - Bộ đề gồm 29 câu đề mẫu (cần đối chiếu ảnh trang trước) và câu hỏi tự sinh từ từ vựng/kanji/ngữ pháp đã xác minh, gắn nhãn AI_GENERATED.
   - Tải thư mục "Đề thi N5_2017" trên Drive để xem có đề kèm audio và đáp án không.
3. Bài tập ngữ pháp + SRS cho ngữ pháp/kanji; dashboard thêm ngữ pháp/kanji.
4. Upload/ZIP qua UI, backup/restore qua UI, Kaiwa, Analytics.
