# Đề JLPT N5 thật các năm — quy trình và trạng thái (ADR-019)

Cập nhật: 2026-11-15, phiên 5.

## Trạng thái
| Đề | Câu | Verified | Nguồn đáp án cộng đồng | Ghi chú |
|---|---|---|---|---|
| EXAM_N5_2012_12 | 85 | 85 (84 ai + 1 user) | 参考答案 trong PDF (p013) | Mất trang lựa chọn câu 24–29 → bỏ 6 câu |
| EXAM_N5_2013_07 | 91 | 91 | 参考答案 (p014) | |
| EXAM_N5_2017_07 | 89 | 89 | 正答表 (p040–041) | 4 câu 表記 có lựa chọn là chữ dạng ảnh (xem ảnh trang) |
| EXAM_N5_2018 | 91 | 91 (90 ai + 1 user) | 参考答案 (p015) | |
| EXAM_N5_2021_12 | 67 | 67 | PDF đáp án Yuuki Bùi + script | Đề in đảo tranh 問題2 4番/6番 so với audio |
| EXAM_N5_2024_07 | 67 | 67 | PDF đáp án Yuuki Bùi + 正解 trong script | G22 không có key cộng đồng → theo 2 AI |
| **Tổng** | **490** | **490** | | |

Không nhập:
- File Drive "N5-2010-2011年.pdf": thực ra là đề 2017-07 dàn trang lại (72/80 câu trùng, bảng đáp án khớp).
- 2022, T12-2024: chỉ có đáp án/script, không có đề.
- Thư mục "Đề thi N5_2017": thiếu trang, không có đáp án.
- Internet: không có nguồn hợp lệ (JLPT chỉ công bố 問題例; đề mock bên thứ ba có bản quyền).

## Nơi lưu (không commit, vì đề JLPT có bản quyền)
| Thư mục | Nội dung |
|---|---|
| `data/raw/SRC_DRIVE_EXAM_N5_<id>/` | File gốc tải từ Drive (`mondai.pdf`, `seikai.pdf`, `script.pdf`, `audio.*`) + `pages/` ảnh render |
| `data/raw/PAST_EXAM_WORK/` | Dữ liệu làm việc: bản chép thô `EXAM_N5_<id>.json`, `solve_A_/solve_B_*.json`, `keys.json`, `review.json`, `BRIEF.md`, `SOLVE_BRIEF.md`, `asr/` (Whisper) |
| `data/normalized/exams/EXAM_N5_<id>.json` + `.ai_review.json` | Kết quả gộp, nguồn cho `hub import` |

Drive: thư mục "ĐỀ THI" `1XQr4kpH9YtLdU_yasMmpvrAdiWlErGpF` (xem `data/sources_online.json`, SRC_EXAM_004). Tải bằng `https://drive.usercontent.google.com/download?id=<file id>&export=download&confirm=t`.

## Quy trình (làm lại cho đề mới)
1. **RAW**: tải file vào `data/raw/SRC_DRIVE_EXAM_N5_<id>/` với tên `mondai.pdf`, `seikai.pdf`, `script.pdf`, `audio.mp3|m4a`. Render ảnh trang 150–170 dpi để agent đọc.
2. **Chép đề** (1 agent/đề, theo `BRIEF.md`): agent đọc ảnh trang, ghi JSON theo định dạng đề mẫu. Agent **không được xem đáp án**; script nghe được bỏ đáp án trước (`*_script_noans.txt`). Nếu không có script: dùng Whisper (`asr/run_asr.py`, venv riêng Python 3.13 + faster-whisper, model large-v3-turbo).
3. **Key cộng đồng**: đọc bảng 参考答案/正答表/PDF đáp án → `keys.json` (`{vocabulary:[…], grammar_reading:[…], listening:{m:[…]}}` theo số câu in).
4. **2 AI giải độc lập** (theo `SOLVE_BRIEF.md`), không thấy key và không thấy nhau: A giải + `explanation_vi` + `option_explanations` + `expected_sequence` (câu ★); B giải từ ảnh gốc + `transcription_issue`.
5. **Gộp**: `cd backend && .venv/Scripts/python -X utf8 scripts/merge_past_exams.py [id…]` in mọi câu lệch / lỗi chép.
6. **Người duyệt cuối** ghi quyết định vào `review.json`: `{qid: {seikai?, note, patch?, drop?}}`. `patch: {"decided_by": "user"}` = người dùng đã quyết (import thành `verified_by='user'`). `drop: true` = bỏ câu (mất trang).
7. `hub import` → `pytest` → `hub report`.
8. **Mốc thời gian câu nghe** (ADR-025): chạy Whisper cho audio của đề (`uv run --python 3.13 --with faster-whisper --with numpy python data/raw/PAST_EXAM_WORK/asr/run_asr.py data/raw data/raw/PAST_EXAM_WORK/asr SRC_DRIVE_EXAM_N5_<id>`), rồi `cd backend && .venv/Scripts/python -X utf8 scripts/listening_timestamps.py` (in số câu có mốc từng đề) → `hub import`.

Quy tắc trạng thái: `verified` (`verified_by='ai'`) chỉ khi key = A = B (`examlib.consensus_status`); lệch → `needs_review` + issue `answer_key_disputed`, trừ khi người dùng đã quyết.

## Nhật ký quyết định duyệt (phiên 5)
| Câu | Key cộng đồng | AI A / B | Đáp án chốt | Căn cứ |
|---|---|---|---|---|
| 2024_07 G04 | 2 | 4 / 4 | 4 | Key tự mâu thuẫn: dãy số ghi 2 nhưng dòng giải thích của chính key ghi が (= lựa chọn 4) |
| 2021_12 L2_4, L2_6 | 1, 4 (theo số bài audio) | 4 / 4, 1 / 1 | 4, 1 | Đề in đảo tranh so với audio (Whisper: 4番 = thể thao, 6番 = bưu thiếp); ghép key theo nội dung tranh |
| 2018 V22–V25 | (gõ nhầm khi chép key) | khớp | theo ảnh 参考答案 | 2 AI phát hiện lỗi chép key; đã sửa `keys.json` theo ảnh |
| 2018 G27 | 3 | 3 / 4 | 3 | Bài đọc nói sáng nay không ăn gì, chuối chỉ mang theo; B nhầm. **Người dùng quyết định 2026-11-15: chọn theo căn cứ** |
| 2012_12 G06 | 2 (には) | 1 / 1 (では) | 1 (では) | ぬぐ là hành động → nơi diễn ra dùng で, không dùng に; は đối chiếu "ở trong lớp thì". **Người dùng quyết định 2026-11-15: chọn theo căn cứ** |
| 2012_12 G24–G26 | | | bỏ | Trang lựa chọn bị mất; G25 chỉ khôi phục được từ trang giải thích |

Nguyên tắc người dùng đặt (2026-11-15): khi key cộng đồng và AI lệch nhau, **chọn theo căn cứ chính xác nhất, miễn giải thích được đáp án**; ghi căn cứ vào `review.json` và bảng trên.

## Đề nghe dựng lại từ video YouTube (phiên 17, ADR-034)
Chỉ có phần 聴解. Người dùng chọn tải để dùng riêng; video, audio, khung hình và bản chép chỉ nằm trên máy (`data/raw/SRC_YT_N5_*`, `EXAM_N5_YT_*` trong `.gitignore`). Năm trong tiêu đề là năm **video ghi**: không có đề gốc để đối chiếu.

| Đề | Video (id) | Câu | Ghi chú nguồn |
|---|---|---|---|
| YT_2025_12 | PhsQJE1B9O0 | 23 | Video thiếu 問題2 6番 |
| YT_2025_07 | st6AmJs_ycg | 24 | ASR có VAD đủ câu; đối chiếu thêm Whisper không VAD |
| YT_2017_12 | OYXy3OFv01M | 24 | ASR có VAD bỏ sót 問題4 → ghép ASR không VAD cho đoạn ≥ 895 s; khung 2-6 có watermark kênh → làm trắng nền xám |
| YT_2016_12 | _PKWEfSkdmU | 12 | Thực ra là đề kiểu 4級 cũ (2 mondai, mỗi câu phát 2 lần) |
| YT_2015_12 | 4mM4qlD7JEY | 24 | Nội dung giống đề luyện (北京, 饅頭 đọc マントウ); audio cắt còn lượt làm bài (0–1136 s); video cắt mất câu dẫn của 問題2 1番 (script bổ sung từ lượt phát lại, câu này không có mốc thời gian) |
| YT_2015_07 | PIyzrj59l14 (tranh) + njSg3mk_V5A (audio) | 24 | Totoro đăng cùng audio cho "T7" và "T12/2015" (ASR trùng 100%; khớp 92% với video 2015/7 kênh khác) → chỉ dùng 1; audio Totoro cắt mất câu chốt 1-5 nên dùng audio kênh kia (0–1148 s) |

Quy trình: `backend/scripts/youtube_listening.py download|frames|pdf` → `asr/run_asr.py` (`ASR_VAD=0` để tắt VAD) → chép theo `YT_BRIEF.md` (agent chọn `pages`, không khung lộ đáp án; key từ bảng 正解 cuối video vào `keys.json`) → 2 AI giải mù (`SOLVE_BRIEF.md`) → `merge_past_exams.py YT_<id>` → romaji/dịch theo `GLOSS_BRIEF.md` (file riêng `gloss_EXAM_N5_YT_<id>.json`, gộp vào `listening_gloss.json` khi `check_transcript_gloss` sạch) → `listening_timestamps.py` (căn cả theo kana của gloss) → `hub import`.

### Nhật ký quyết định (phiên 17)
| Câu | Đáp án video | AI A / B | Chốt | Căn cứ |
|---|---|---|---|---|
| YT_2016_12 L2_2 | 2 | 4 / 4 | 4 | Tranh: người 2 đeo kính; 長いスカート + めがね？→ ううん ⇒ người 4 |
| YT_2017_12 L1_1 | 2 | 3 / 3 | 3 | Audio: 「いいえ、父のです」 |
| YT_2017_12 L2_3 | 1 | 2 / 2 (medium) | 1, **chờ duyệt** | Tranh 1/2 lật gương; 720p không phân biệt quay mặt/quay lưng → không đủ căn cứ để bác key |
| YT_2025_07 L3_1 | 2 | 1 → 2 / 2 | 2 | A giải lần đầu không mở tranh 問題3 (người mũi tên ngồi ở bàn → お帰りなさい); được yêu cầu mở tranh và giải lại (vẫn mù đáp án) |
| YT_2015_12 L2_5 | 2 | 4 / 4 | 4 | 「車を洗っているのはお父さん」「お母さんは…洗濯」⇒ mẹ ở máy giặt; script video gán ngược vai (B đo cao độ giọng) |
