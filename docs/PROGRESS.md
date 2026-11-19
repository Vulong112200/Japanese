# PROGRESS — Japanese N5 Learning Hub

Cập nhật: 2026-11-15, kết thúc phiên 11. Trạng thái dựa trên kết quả kiểm thử: **103/103 test pass**, frontend build sạch.

## Tóm tắt các phiên
| Phiên | Nội dung | Kết quả |
|---|---|---|
| 1 | Audit (greenfield); schema; DB; Source Library; nhập CSV + đề mẫu; luật kiểm tra; SRS; màn hình Duyệt | 56 test |
| 2 | Tự tải nguồn online; JMdict/KANJIDIC2; rà soát + sửa 963 từ vựng (167 bản sửa); CLAUDE.md | 963/963 từ vựng verified (AI); 57 test |
| 3 | Cài OCR Tesseract; OCR PDF Drive; **hoàn thiện kiến thức N5**: +290 từ vựng, 103 kanji, 135 điểm ngữ pháp; trang Ngữ pháp + Kanji | 1.253 từ vựng + 103 kanji verified; 68 test |
| 4 | Rà soát ngữ pháp vòng 2 (4 agent, nhận 6 / loại 13 đề xuất); **Mock Exam Engine** (thi / luyện tập, theo đề, theo phần, theo mondai, ôn câu sai, tuỳ chỉnh; đồng hồ từng phần, tự lưu, gắn cờ, chấm điểm, lịch sử, ước lượng sẵn sàng); ngân hàng **475 câu từ vựng sinh bằng luật** (348 漢字読み + 127 表記); trang Thi thử; Dashboard có thi thử + ngữ pháp/kanji | 135/135 ngữ pháp verified; 77 test |
| 5 | Tìm đề thật: internet không có nguồn hợp lệ (JLPT không công bố đề cũ). Nhập **6 đề JLPT N5 thật** từ thư mục Drive "ĐỀ THI" (2012-12, 2013-07, 2017-07, 2018, 2021-12, 2024-07; file "2010-2011" thực ra trùng đề 2017-07 nên bỏ). Mỗi đề: AI chép từ ảnh trang, đáp án cộng đồng (参考答案/正答表/Yuuki Bùi), 2 agent giải độc lập (A giải + giải thích, B giải từ ảnh + soát bản chép); verified chỉ khi key = A = B (ADR-019). Importer chung `import_exam()`; bộ lọc nguồn "Đề thi thật các năm" | 490/490 câu đề thật verified (488 key = A = B, 2 người dùng quyết theo căn cứ); 80 test |
| 6 | **Ngân hàng câu ngữ pháp do agent soạn** (ADR-020): 4 agent soạn 405 câu (mỗi điểm 2 câu 文の文法1 + 1 câu 文の文法2 ★); luật tự động (`check_grammar_question`); 2 lượt giải mù độc lập A/B (chia lô khác) → 403/405 key = A = B, 13 câu gắn cờ; người duyệt cuối: sửa 3 (giải mù lại, khớp), loại 6 (5 câu ★ có 2 thứ tự hợp lệ, 1 câu trùng), giữ 4. Kết quả thi có `weak_grammar_points`; luyện tập hiện thứ tự đúng + điểm ngữ pháp | 399/399 câu verified (269 文法1 + 130 文法2); 84 test |
| 7 | **SRS cho ngữ pháp + kanji** (ADR-021): chung `srs_cards`/SM-2, 1 chiều, hạn mức thẻ mới riêng từng loại; trang Ôn tập SRS có chọn loại thẻ (mặt sau ngữ pháp: nghĩa, cách dùng, 2 ví dụ, link chi tiết; kanji: Hán-Việt, 音/訓, từ ví dụ). **Dashboard**: thẻ đến hạn + mức độ thuộc cho 3 loại; khung **"Ngữ pháp cần ôn"** từ câu trả lời mới nhất của mỗi câu (link sang trang Ngữ pháp `#/grammar?id=`). Sửa lỗi có sẵn: hai lượt nộp cùng giây làm sai thứ tự "câu trả lời mới nhất" (Mode E) | 135 thẻ ngữ pháp + 103 thẻ kanji; 86 test |
| 8 | **Dashboard §13 + Thống kê §14** (ADR-022): mục tiêu ngày (`settings.daily_goal`, sửa tại chỗ; tính lượt ôn thẻ + câu trả lời), thời gian học ước tính từ dấu thời gian; streak tính cả ngày chỉ làm bài; khung **"Học gì tiếp"** (gợi ý theo dữ liệu thật: thẻ đến hạn → câu sai → điểm ngữ pháp yếu → thi thử → thẻ mới); **luyện câu theo 1 điểm ngữ pháp** (nút "Luyện" ở Dashboard, Thống kê, chi tiết Ngữ pháp). Trang **Thống kê**: cột lượt học 30 ngày, tổng thời gian, tỉ lệ nhớ SRS theo loại, lịch sử thi theo phần, mondai yếu, điểm ngữ pháp yếu, câu sai ≥ 2 lần. Sửa lỗi có sẵn: "lượt gần nhất" sai thứ tự khi nộp cùng giây (thêm `rowid`) | 90 test |
| 9 | **Kaiwa §7.4** (ADR-023): 27 hội thoại (9 chủ đề × 3, 251 lượt lời) do 3 agent soạn chỉ từ từ vựng/ngữ pháp verified; luật `check_kaiwa` (kana của câu khớp thứ tự dòng hiragana, từ tham chiếu verified + có trong câu + cách đọc có trong dòng đọc, ngữ pháp verified, kanji ngoài N5 = info); 2 vòng rà soát độc lập (chia nửa / chia chẵn-lẻ) → 41 đề xuất: 30 nhận, 7 trùng giữa 2 vòng, 2 gộp, 2 thay thế; + 4 sửa của người duyệt cuối. Trang **Hội thoại**: bật/tắt hiragana và bản dịch, giọng máy từng câu, link ngữ pháp. **Sao lưu/khôi phục qua UI** (ADR-024): tải file sqlite, khôi phục có kiểm tra toàn vẹn + tự lưu bản trước khi ghi đè | 27/27 hội thoại verified; 97 test |
| 10 | **Mốc thời gian từng câu nghe** (ADR-025): chạy thêm Whisper cho 2017-07, 2024-07, đề mẫu; script `listening_timestamps.py` căn ASR với script giấy (theo thứ tự đề, tìm lại trong cả mondai khi đề in đảo thứ tự) → 148 câu có mốc; nút "▶ Nghe câu này" tự dừng cuối câu. **Ngân hàng bài đọc do agent soạn** (ADR-026): 4 agent soạn 68 bài / 142 câu (24 文章の文法, 24 短文, 12 中文, 8 情報検索); luật `check_reading_group` 0 lỗi; 2 lượt giải mù A/B → 142/142 key = A = B; người duyệt cuối: sửa 2 bài (409 thay từ vượt N5; 203 sửa câu gượng + nêu rõ chủ ngữ để loại もらいます, giải mù lại 3 lần), giữ 6 bài có ghi chú mức N4 (mẫu nằm trong 135 điểm). Lấy mẫu luyện tập không cắt rời bài đọc. Sửa lỗi có sẵn: câu ngân hàng ngữ pháp bị gắn nhãn "Đề chính thức" | 142/142 câu đọc verified; 6/6 đề thật có mốc nghe (144/144 câu); 102 test |
| 11 | **Flashcard ôn tổng hợp** (ADR-027): thẻ mới/ngày tối đa 500 (trước 200), 1000 thẻ đến hạn mỗi lần tải; lọc khoảng bài; thứ tự Theo bài / Ngẫu nhiên; chế độ **Ôn tổng hợp** (từ đã học / từ hay quên / tất cả, lật ngẫu nhiên ngoài lịch; Quên → đưa lại vào SRS, Nhớ → không ghi). Phím số trong ô nhập không còn bị hiểu là chấm điểm | 103 test |
| 12 | **Ôn ngữ pháp gom nhiều bài** (ADR-028): panel "Ôn nhanh nhiều bài" ở trang Ngữ pháp, chọn Bài X–Y (có "25 + N5 bổ sung") và 10/20/30/50 câu, trộn ngẫu nhiên câu 文の文法1/2; sau khi trả lời hiện ý nghĩa + cấu trúc điểm ngữ pháp kèm link | 104 test |
| 13 | **Chuyên đề Số đếm & ngày tháng** (ADR-029): 273 mục / 23 nhóm (số, trợ số từ, giờ phút, thứ, ngày, tháng, năm, tiền), luật biến âm độc lập + JMdict + 2 vòng rà soát → 273 verified; trang **Số đếm** (bảng + quy tắc, tô cách đọc đặc biệt); 118 thẻ SRS loại "Số đếm"; 147 câu trắc nghiệm 漢字読み (`BANK_N5_NUMBERS`), luyện từ trang Số đếm | 109 test |
| 13b | Sửa lỗi "Từ hay quên" (ADR-027): bấm **Nhớ** ở Ôn tổng hợp ghi `srs_cards.weak_cleared_at` (`POST /api/srs/cards/{id}/recalled`), thẻ rời danh sách đến khi bị Quên lại; lịch SM-2 không đổi. **Nhớ** với thẻ chưa học = lượt ôn `good` thật (trước đây không ghi gì → học ở Ôn tổng hợp "Tất cả" không hiện ở Tổng quan); ghi chú cách ghi nhận ngay dưới bộ lọc | 109 test |
| 14 | **SRS cấp tốc** (ADR-030): chế độ thứ 3 ở trang Flashcard cho những tuần trước ngày thi. Lịch nén 10 phút → 1 → 2 → 4 → 7 ngày, không hẹn quá ngày trước hôm thi (setting `exam_date`), "thuộc" = nhớ đúng 5 lần liên tiếp; thẻ không gặp 7 ngày tự đến hạn lại (tính khi đọc, không sửa lịch SM-2). Thẻ đến hạn trong 20 phút quay lại ngay trong phiên | 112 test |

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
| Ngân hàng bài đọc do agent soạn | 68 bài / 142 câu: 文章の文法 24 bài (86 câu), 短文 24, 中文 12 (24 câu), 情報検索 8 | verified_by='ai': luật + key = 2 AI giải mù (ADR-026); bằng chứng `data/normalized/ai_review/reading_questions_review.json` |

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
| M02 Audio | ✅ | Phát, tua, chỉnh tốc độ (luyện tập). Mốc thời gian từng câu (ADR-025): 144/144 câu đề thật + 4/8 câu đề mẫu (MP3 mẫu chỉ có 4 câu). |
| M02 Website | 🟡 | Kiểm tra truy cập; tải được Google Docs và Drive công khai |
| Data quality §11 | ✅ | |
| Vocabulary §7.1 | ✅ | |
| Kanji §7.2 | ✅ | |
| Grammar §7.3 | ✅ | Tra cứu đủ, đã verified. Bài tập: 399 câu 文の文法1/2 trong Thi thử (nguồn "Sinh tự động", lọc theo mondai); kết quả thi + Dashboard báo điểm ngữ pháp cần ôn. SRS 1 chiều (mẫu → nghĩa). Ôn nhanh gom nhiều bài (ADR-028). |
| SRS §8 | ✅ | Từ vựng (2 chiều), ngữ pháp + kanji (1 chiều), ADR-021. Lọc khoảng bài, xáo trộn, chế độ Ôn tổng hợp (ADR-027), SRS cấp tốc (ADR-030). Số đếm: 118 thẻ dạng đặc biệt (ADR-029). |
| Mock Exam §9 | ✅ | Mode A (đề + giờ JLPT 20/40/30), B (đề gốc, giữ cấu trúc/thời gian gốc), C (theo phần), D (theo mondai), E (ôn câu sai), F (tuỳ chỉnh số câu/thời gian/nguồn). Giao diện §9.2 đủ (điều hướng, cờ, trước/sau, tiến độ, đồng hồ, audio, xác nhận nộp). Kết quả §9.3 + ước lượng tách riêng (§4.3). Có 1 đề mẫu chính thức + 6 đề thật các năm (giờ gốc 25/50/30 trước 2020, 20/40/30 từ 2020). Ngân hàng: từ vựng (問題1/2, sinh bằng luật) + ngữ pháp (文の文法1/2, agent soạn) + bài đọc (文章の文法, 短文, 中文, 情報検索; agent soạn, ADR-026). Chưa có câu sinh cho nghe (không tạo audio thay thế). |
| Listening §10 | ✅ | Chế độ thi: không lộ script/lựa chọn audio-only; luyện tập: tốc độ phát, script sau khi trả lời; nút nghe đúng đoạn của câu (ADR-025). Nguồn nghe = 7 đề có audio gốc (không tạo audio thay thế). |
| Dashboard §13 | ✅ | Cấp độ, mục tiêu ngày, streak, mức độ thuộc 3 loại, thẻ đến hạn, lượt thi gần nhất, ngữ pháp/bài yếu, "Học gì tiếp" (ADR-022). |
| Kaiwa §7.4 | ✅ | 27 bài, 9 chủ đề, verified (ADR-023). Giọng máy trình duyệt (không có audio gốc). Chưa có màn Duyệt riêng (sửa qua file + `review_log`). |
| Analytics §14 | ✅ | Trang Thống kê: thời gian học (ước tính), hoạt động 30 ngày, tỉ lệ nhớ SRS theo loại, lịch sử thi theo phần, mondai yếu, điểm ngữ pháp yếu, câu sai lặp lại. Đọc/nghe tính theo phần thi (chưa tách kỹ năng con). |
| Backup/restore | ✅ | Dashboard: tải bản sao lưu / khôi phục từ file (ADR-024); bản trước khi khôi phục lưu ở `data/database/backups/`. |
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
- Mốc thời gian câu nghe căn tự động từ Whisper (ADR-025): có thể lệch 1–2 s (ví dụ 2017-07 問題3 3番 bắt đầu muộn ~2 s). MP3 đề mẫu chỉ có 4/8 câu nghe. Bản ghi ASR nằm ở `data/raw` (không commit); máy mới: chạy lại `asr/run_asr.py` rồi `scripts/listening_timestamps.py` (file mốc đã commit nên không bắt buộc).
- Bài đọc do agent soạn (ADR-026): 情報検索 là bảng dạng chữ (đề thật có hình); một số bài dùng mẫu mà vài danh sách xếp N4 (～と, ～ても, ～た ほうが いい, ～かた) — đều nằm trong 135 điểm của dự án. Lấy mẫu giữ trọn bài nên số câu có thể vượt số yêu cầu vài câu.
- Câu ngữ pháp do agent soạn: 2 AI giải mù đồng ý không chứng minh tuyệt đối câu chỉ có 1 đáp án (nhất là 文法2 ★ khi các cụm đổi chỗ được). Nếu gặp câu có 2 đáp án, sửa trong `grammar_questions.json` (ghi `review_log`) hoặc `excluded: true`, rồi `import`. 5 điểm (059, 068, 069, 095, 103) hiện chưa có câu ★.
- Thời gian học là ước tính (ADR-022): không tính thời gian đọc trước câu đầu mỗi phiên, nên thường thấp hơn thực tế.
- Hội thoại do AI soạn: đã qua luật + 2 vòng rà soát, nhưng có thể còn câu hơi "sách vở". Sửa trong `data/normalized/kaiwa/kaiwa.json` (ghi `review_log`) rồi `import`; loại: `excluded: true`. Một số từ đời thường ngoài kho từ vựng (サラダ, ラーメン, しゅっちょう…) có trong câu nhưng không gắn tham chiếu.
- Khôi phục thay **toàn bộ** DB (cả nội dung học); bản sao lưu cũ cần chạy `hub import` để lấy nội dung mới. Không hợp nhất 2 bản.
- Vài câu dùng mẫu mà một số danh sách xếp N4 (～ないと, いくら～ても, ～たことがある): đúng theo 135 điểm của dự án (Minna 1–25).

## Việc tiếp theo (theo thứ tự)
1. Upload tệp / ZIP qua UI cho Thư viện nguồn (M01) — người dùng hoãn lại (phiên 10).
2. (Tuỳ chọn) Chiều Việt→Nhật cho thẻ ngữ pháp/kanji.
3. (Tuỳ chọn) Nút "Nghe câu này" ở màn Duyệt dữ liệu (hiện chỉ ở Thi thử).
