# PROGRESS — Japanese N5 Learning Hub

Cập nhật: 2026-11-14, kết thúc phiên 4. Trạng thái dựa trên kết quả kiểm thử: **77/77 test pass**, frontend build sạch.

## Tóm tắt các phiên
| Phiên | Nội dung | Kết quả |
|---|---|---|
| 1 | Audit (greenfield); schema; DB; Source Library; nhập CSV + đề mẫu; luật kiểm tra; SRS; màn hình Duyệt | 56 test |
| 2 | Tự tải nguồn online; JMdict/KANJIDIC2; rà soát + sửa 963 từ vựng (167 bản sửa); CLAUDE.md | 963/963 từ vựng verified (AI); 57 test |
| 3 | Cài OCR Tesseract; OCR PDF Drive; **hoàn thiện kiến thức N5**: +290 từ vựng, 103 kanji, 135 điểm ngữ pháp; trang Ngữ pháp + Kanji | 1.253 từ vựng + 103 kanji verified; 68 test |
| 4 | Rà soát ngữ pháp vòng 2 (4 agent, nhận 6 / loại 13 đề xuất); **Mock Exam Engine** (thi / luyện tập, theo đề, theo phần, theo mondai, ôn câu sai, tuỳ chỉnh; đồng hồ từng phần, tự lưu, gắn cờ, chấm điểm, lịch sử, ước lượng sẵn sàng); ngân hàng **475 câu từ vựng sinh bằng luật** (348 漢字読み + 127 表記); trang Thi thử; Dashboard có thi thử + ngữ pháp/kanji | 135/135 ngữ pháp verified; 77 test |

## Độ phủ kiến thức N5: ĐÃ ĐỦ, không cần thu thập thêm tài liệu
| Mảng | Độ phủ | Trạng thái xác minh |
|---|---|---|
| Từ vựng | 1.253 mục, đủ 25 bài Minna; phủ toàn bộ danh sách JLPT N5 (718 từ) | 1.253/1.253 verified (AI): rà soát 2 vòng + JMdict/KANJIDIC2 |
| Kanji | 103/103 chữ N5 | 103/103 verified (AI): 2 vòng + KANJIDIC2/JMdict |
| Ngữ pháp | 135 điểm (121 Minna 1–25 + 14 bổ sung) | **135/135 verified (AI)**: vòng 1 lúc soạn + vòng 2 phiên 4 (bằng chứng: `data/normalized/ai_review/grammar_round2.json`) |
| Đề mẫu chính thức | 29 câu, đáp án khớp 正解 29/29 | needs_review (chờ đối chiếu ảnh trang); vẫn thi được, có nhãn |
| Ngân hàng câu sinh tự động | 475 câu 文字・語彙 (問題1, 問題2) từ từ vựng/kanji đã verified | verified_by='generator' (ADR-017); nhãn AI_GENERATED |

## Ma trận module

Ký hiệu trạng thái:
- ✅ **Hoàn thành**: có test.
- 🟡 **Một phần**: làm được một phần.
- ⬜ **Chưa làm**.
- 🔒 **Bị chặn**: cần đăng nhập.

| Module (spec) | Trạng thái | Ghi chú |
|---|---|---|
| M01 Source Library | ✅ | Chưa có: upload tệp qua UI, ZIP, preview. |
| M02 Ingestion CSV / docx | ✅ | |
| M02 OCR | ✅ | Tesseract 5.4 jpn/vie |
| M02 Audio | 🟡 | Phát, tua, chỉnh tốc độ (luyện tập). Chưa có timestamp từng câu (1 track cho cả phần nghe). |
| M02 Website | 🟡 | Kiểm tra truy cập; tải được Google Docs và Drive công khai |
| Data quality §11 | ✅ | |
| Vocabulary §7.1 | ✅ | |
| Kanji §7.2 | ✅ | |
| Grammar §7.3 | 🟡 | Tra cứu đủ, đã verified. **Chưa có bài tập ngữ pháp** (cần câu do agent soạn + rà soát). |
| SRS §8 | ✅ | Hiện chỉ áp dụng cho từ vựng |
| Mock Exam §9 | ✅ | Mode A (đề + giờ JLPT 20/40/30), B (đề gốc, giữ cấu trúc/thời gian gốc), C (theo phần), D (theo mondai), E (ôn câu sai), F (tuỳ chỉnh số câu/thời gian/nguồn). Giao diện §9.2 đủ (điều hướng, cờ, trước/sau, tiến độ, đồng hồ, audio, xác nhận nộp). Kết quả §9.3 + ước lượng tách riêng (§4.3). **Giới hạn: chỉ có 1 đề chính thức (29 câu); ngân hàng sinh tự động chỉ có phần từ vựng.** |
| Listening §10 | 🟡 | Chế độ thi: không lộ script/lựa chọn audio-only; luyện tập: tốc độ phát, script sau khi trả lời. Chưa có timestamp, chưa có đề nghe thứ hai. |
| Dashboard §13 | 🟡 | Có SRS, thi thử, độ xác minh từ vựng/ngữ pháp/kanji. Chưa có mục tiêu ngày, gợi ý học. |
| Kaiwa §7.4 | ⬜ | |
| Analytics §14 | 🟡 | Điểm yếu theo bài (SRS + thi thử). Chưa có xu hướng theo thời gian. |
| Backup/restore | 🟡 | Copy file sqlite |
| Offline | ✅ | |

## Đánh giá các nguồn không tải được / không nên tải
| Nguồn | Có cần không? | Lý do |
|---|---|---|
| 10 link NotebookLM + Google Notebook | **Không cần** | Bài trắc nghiệm do AI sinh từ chính cẩm nang ngữ pháp; phải đăng nhập |
| tailieuhoctiengnhat (Minna vocab) | **Không cần** | Bị chặn chống bot; nội dung đã có đủ |
| HanoiLink (từ vựng N5) | **Không cần** | Độ phủ JLPT N5 đã đủ |
| nihonez.com (10 đề N5, kiểm tra phiên 4) | **Không lấy** | Phải đăng nhập, một số đề trả phí; điều khoản mục 4 cấm "copy, scrape, bulk-download… our questions". Giữ làm link ngoài |
| gojapan.vn (Đề 1–10, kiểm tra phiên 4) | **Không lấy** | Xem công khai (HTML + mp3), nhưng "ALL RIGHTS RESERVED", không có điều khoản cho phép dùng lại, và **không công bố đáp án** (chấm qua form tên + SĐT) → không có 正解 để nhập đúng quy tắc. Giữ làm link ngoài |
| Migii | Không lấy | Đề thương mại |
| Thư mục con trên Drive (Đề thi N5 2017, video kaiwa) | **Có ích** | Thư mục công khai của bạn; có thể có đề + audio + 正解. Việc tiếp theo số 1 |

## Known issues
- Romaji trong ví dụ ngữ pháp viết 2 kiểu: macron (Kinō, GRA 1–66) và gõ phím (Kinou, GRA 70+). Cả hai đều đúng (`romaji_matches` chấp nhận). Nếu muốn thống nhất, làm 1 lượt chuẩn hoá máy cho toàn bộ (vòng 2 đã loại 13 đề xuất sửa lẻ).
- Câu 漢字読み sinh tự động có thể có bẫy trông "lạ" (ví dụ うた → ううた) — vẫn chắc chắn sai, nhưng ít tự nhiên hơn đề thật.
- Đề mẫu: 1 file MP3 cho toàn bộ phần nghe, không có mốc thời gian từng câu.

## Việc tiếp theo (theo thứ tự)
1. **Đề N5 2017 trên Drive** (`SRC_LESSON_002`, thư mục con "Đề thi N5_2017"): tải, xem có đề + audio + 正解 không. Nếu có: chép như đề mẫu (`data/normalized/exams/EXAM_N5_2017_xx.json`, không commit bản chép), import qua `import_sample_exam` tổng quát hoá. Đây là đề đầy đủ thứ hai, có phần nghe thật.
2. **Câu ngữ pháp do agent soạn** (文の文法1 chọn mẫu, 文の文法2 sắp xếp ★) từ 135 điểm đã verified: mỗi câu có `target_grammar_id`, đúng 1 đáp án, giải thích từng lựa chọn; rà soát 2 vòng (CLAUDE.md §6); nhập vào ngân hàng với `weak_grammar_points` trong kết quả thi.
3. SRS cho ngữ pháp/kanji; mục tiêu ngày + gợi ý học trên Dashboard.
4. Upload/ZIP qua UI, backup/restore qua UI, Kaiwa, Analytics theo thời gian.
