# PROGRESS — Japanese N5 Learning Hub

Cập nhật: 2026-11-15, kết thúc phiên 6. Trạng thái dựa trên kết quả kiểm thử: **84/84 test pass**, frontend build sạch.

## Tóm tắt các phiên
| Phiên | Nội dung | Kết quả |
|---|---|---|
| 1 | Audit (greenfield); schema; DB; Source Library; nhập CSV + đề mẫu; luật kiểm tra; SRS; màn hình Duyệt | 56 test |
| 2 | Tự tải nguồn online; JMdict/KANJIDIC2; rà soát + sửa 963 từ vựng (167 bản sửa); CLAUDE.md | 963/963 từ vựng verified (AI); 57 test |
| 3 | Cài OCR Tesseract; OCR PDF Drive; **hoàn thiện kiến thức N5**: +290 từ vựng, 103 kanji, 135 điểm ngữ pháp; trang Ngữ pháp + Kanji | 1.253 từ vựng + 103 kanji verified; 68 test |
| 4 | Rà soát ngữ pháp vòng 2 (4 agent, nhận 6 / loại 13 đề xuất); **Mock Exam Engine** (thi / luyện tập, theo đề, theo phần, theo mondai, ôn câu sai, tuỳ chỉnh; đồng hồ từng phần, tự lưu, gắn cờ, chấm điểm, lịch sử, ước lượng sẵn sàng); ngân hàng **475 câu từ vựng sinh bằng luật** (348 漢字読み + 127 表記); trang Thi thử; Dashboard có thi thử + ngữ pháp/kanji | 135/135 ngữ pháp verified; 77 test |
| 5 | Tìm đề thật: internet không có nguồn hợp lệ (JLPT không công bố đề cũ). Nhập **6 đề JLPT N5 thật** từ thư mục Drive "ĐỀ THI" (2012-12, 2013-07, 2017-07, 2018, 2021-12, 2024-07; file "2010-2011" thực ra trùng đề 2017-07 nên bỏ). Mỗi đề: AI chép từ ảnh trang, đáp án cộng đồng (参考答案/正答表/Yuuki Bùi), 2 agent giải độc lập (A giải + giải thích, B giải từ ảnh + soát bản chép); verified chỉ khi key = A = B (ADR-019). Importer chung `import_exam()`; bộ lọc nguồn "Đề thi thật các năm" | 490/490 câu đề thật verified (488 key = A = B, 2 người dùng quyết theo căn cứ); 80 test |
| 6 | **Ngân hàng câu ngữ pháp do agent soạn** (ADR-020): 4 agent soạn 405 câu (mỗi điểm 2 câu 文の文法1 + 1 câu 文の文法2 ★); luật tự động (`check_grammar_question`); 2 lượt giải mù độc lập A/B (chia lô khác) → 403/405 key = A = B, 13 câu gắn cờ; người duyệt cuối: sửa 3 (giải mù lại, khớp), loại 6 (5 câu ★ có 2 thứ tự hợp lệ, 1 câu trùng), giữ 4. Kết quả thi có `weak_grammar_points`; luyện tập hiện thứ tự đúng + điểm ngữ pháp | 399/399 câu verified (269 文法1 + 130 文法2); 84 test |

## Độ phủ kiến thức N5: ĐÃ ĐỦ, không cần thu thập thêm tài liệu
| Mảng | Độ phủ | Trạng thái xác minh |
|---|---|---|
| Từ vựng | 1.253 mục, đủ 25 bài Minna; phủ toàn bộ danh sách JLPT N5 (718 từ) | 1.253/1.253 verified (AI): rà soát 2 vòng + JMdict/KANJIDIC2 |
| Kanji | 103/103 chữ N5 | 103/103 verified (AI): 2 vòng + KANJIDIC2/JMdict |
| Ngữ pháp | 135 điểm (121 Minna 1–25 + 14 bổ sung) | **135/135 verified (AI)**: vòng 1 lúc soạn + vòng 2 phiên 4 (bằng chứng: `data/normalized/ai_review/grammar_round2.json`) |
| Đề mẫu chính thức | 29 câu, đáp án khớp 正解 29/29 | needs_review (chờ đối chiếu ảnh trang); vẫn thi được, có nhãn |
| Đề thi thật các năm (ADR-019) | 6 đề, 490 câu (2012-12: 85, 2013-07: 91, 2017-07: 89, 2018: 91, 2021-12: 67, 2024-07: 67); có audio + script nghe | Đáp án cộng đồng + 2 AI giải độc lập; nhãn COMMUNITY_KEY, is_official=0 |
| Ngân hàng câu sinh tự động | 475 câu 文字・語彙 (問題1, 問題2) từ từ vựng/kanji đã verified | verified_by='generator' (ADR-017); nhãn AI_GENERATED |
| Ngân hàng câu ngữ pháp do agent soạn | 399 câu (269 文の文法1 + 130 文の文法2 ★), phủ 135/135 điểm (5 điểm chỉ có câu 文法1) | verified_by='ai': luật + key = 2 AI giải mù (ADR-020); bằng chứng `data/normalized/ai_review/grammar_questions_review.json` |

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
| Grammar §7.3 | ✅ | Tra cứu đủ, đã verified. Bài tập: 399 câu 文の文法1/2 trong Thi thử (nguồn "Sinh tự động", lọc theo mondai); kết quả thi báo điểm ngữ pháp yếu. Chưa có SRS cho ngữ pháp. |
| SRS §8 | ✅ | Hiện chỉ áp dụng cho từ vựng |
| Mock Exam §9 | ✅ | Mode A (đề + giờ JLPT 20/40/30), B (đề gốc, giữ cấu trúc/thời gian gốc), C (theo phần), D (theo mondai), E (ôn câu sai), F (tuỳ chỉnh số câu/thời gian/nguồn). Giao diện §9.2 đủ (điều hướng, cờ, trước/sau, tiến độ, đồng hồ, audio, xác nhận nộp). Kết quả §9.3 + ước lượng tách riêng (§4.3). Có 1 đề mẫu chính thức + 6 đề thật các năm (giờ gốc 25/50/30 trước 2020, 20/40/30 từ 2020). Ngân hàng: từ vựng (問題1/2, sinh bằng luật) + ngữ pháp (文の文法1/2, agent soạn). Chưa có câu sinh cho 文章の文法, đọc hiểu, nghe. |
| Listening §10 | 🟡 | Chế độ thi: không lộ script/lựa chọn audio-only; luyện tập: tốc độ phát, script sau khi trả lời. Chưa có timestamp, chưa có đề nghe thứ hai. |
| Dashboard §13 | 🟡 | Có SRS, thi thử, độ xác minh từ vựng/ngữ pháp/kanji. Chưa có mục tiêu ngày, gợi ý học. |
| Kaiwa §7.4 | ⬜ | |
| Analytics §14 | 🟡 | Điểm yếu theo bài (SRS + thi thử) và theo điểm ngữ pháp (thi thử). Chưa có xu hướng theo thời gian. |
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
| Drive "ĐỀ THI" (phiên 5) | **Đã nhập 6 đề** | 2012-12, 2013-07, 2017-07, 2018, 2021-12, 2024-07. Bỏ: "2010-2011" (trùng 2017-07), 2022 và T12-2024 (chỉ có đáp án/script, không có đề) |
| Drive "Đề thi N5_2017" (N5_Vocabulary/Reading/Listening) | Không lấy | Thiếu trang 13–21, không có đáp án; chỉ có phiếu trả lời |
| Internet: đề N5 thật / mock (tìm phiên 5) | **Không có nguồn hợp lệ** | JLPT chỉ công bố 問題例 (đã có); 公式問題集 là sách trả phí; đề mock bên thứ ba có bản quyền/cấm scrape |

## Known issues
- Đề thật các năm là bản cộng đồng dựng lại/quét (chữ gõ lại, hình vẽ lại), có thể khác đề gốc ở chi tiết; các lỗi in đã ghi trong `review_notes`. Bản chép + kết quả AI chỉ lưu trên máy (không commit): máy mới cần chạy lại từ `data/raw` (xem ADR-019).
- 2012-12 mất trang lựa chọn câu 24–29 (đã bỏ 6 câu). Quy trình, nơi lưu và nhật ký quyết định duyệt: [PAST_EXAMS.md](PAST_EXAMS.md). 2021-12: đề in đảo tranh 4番/6番 của 問題2 so với audio (đã ghép đáp án theo nội dung, có ghi chú).
- Romaji trong ví dụ ngữ pháp viết 2 kiểu: macron (Kinō, GRA 1–66) và gõ phím (Kinou, GRA 70+). Cả hai đều đúng (`romaji_matches` chấp nhận). Nếu muốn thống nhất, làm 1 lượt chuẩn hoá máy cho toàn bộ (vòng 2 đã loại 13 đề xuất sửa lẻ).
- Câu 漢字読み sinh tự động có thể có bẫy trông "lạ" (ví dụ うた → ううた) — vẫn chắc chắn sai, nhưng ít tự nhiên hơn đề thật.
- Đề mẫu: 1 file MP3 cho toàn bộ phần nghe, không có mốc thời gian từng câu.
- Câu ngữ pháp do agent soạn: 2 AI giải mù đồng ý không chứng minh tuyệt đối câu chỉ có 1 đáp án (nhất là 文法2 ★ khi các cụm đổi chỗ được). Nếu gặp câu có 2 đáp án, sửa trong `grammar_questions.json` (ghi `review_log`) hoặc `excluded: true`, rồi `import`. 5 điểm (059, 068, 069, 095, 103) hiện chưa có câu ★.
- Vài câu dùng mẫu mà một số danh sách xếp N4 (～ないと, いくら～ても, ～たことがある): đúng theo 135 điểm của dự án (Minna 1–25).

## Việc tiếp theo (theo thứ tự)
1. (Tuỳ chọn) Timestamp từng câu nghe của đề thật từ bản ghi Whisper (`data/raw/PAST_EXAM_WORK/asr/`; mới có 2010/2012/2013/2021).
2. SRS cho ngữ pháp/kanji; mục tiêu ngày + gợi ý học trên Dashboard (dùng `weak_grammar_points` để gợi ý ôn điểm ngữ pháp, link sang trang Ngữ pháp).
3. (Tuỳ chọn) Câu 文章の文法 / đọc hiểu ngắn do agent soạn, cùng quy trình ADR-020.
4. Upload/ZIP qua UI, backup/restore qua UI, Kaiwa, Analytics theo thời gian.
