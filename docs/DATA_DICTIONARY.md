# DATA DICTIONARY

Định nghĩa đầy đủ: `backend/hub/db.py` (SQLite) và `schemas/*.schema.json` (định dạng trao đổi JSON, kiểm tra bằng `jsonschema` trong `backend/tests/test_data.py`).

## Trạng thái dùng chung
- `verification_status`: `raw | extracted | normalized | needs_review | verified | rejected`.
  - `normalized`: qua luật tự động, chưa có người duyệt. Học được, hiện nhãn "Chưa xác minh".
  - `needs_review`: có lỗi hoặc cảnh báo (từ luật hoặc từ AI), hoặc là bản chép bằng AI.
  - `verified`: chỉ đạt được khi người dùng bấm "Duyệt". Đây là lớp CURATED.
- `processing_status` (nguồn): `pending | importing | extracting | normalizing | validating | verified | needs_review | failed | registered`.
- `access_status` (nguồn): `local | accessible | requires_auth | manual_export | unreachable | unchecked`.
- `reliability`: `OFFICIAL | PRIMARY | EDUCATIONAL | SUPPLEMENTARY | AI_GENERATED | USER_CREATED`.

## Bảng

### sources
Mỗi tệp hoặc URL có một `source_id` duy nhất.
- `SRC_LOCAL_FC_BAI01…25`, `SRC_LOCAL_FC_KAIWA`, `SRC_LOCAL_FC_SODEM`: các tệp flashcard.
- `SRC_LOCAL_N5_MONDAI | SEIKAI | SCRIPT | KAITOU | AUDIO`: bộ đề mẫu.
- `SRC_EXAM_00x`, `SRC_LESSON_00x`, `SRC_NBLM_0xx`, `SRC_GDOC_001`, `SRC_NOTEBOOK_001`, `SRC_OFFICIAL_00x`: các nguồn trực tuyến.
- `SRC_USER_xxx`: URL do người dùng đăng ký qua UI.

Cột: `size_bytes`, `page_count`, `duration_seconds`, `content_hash` (sha256 của tệp), `checked_at`, `record_count`, `notes` (ghi cả trùng lặp), `error`.

### raw_records (lớp RAW, bất biến)
- `locator`: `row:N` (CSV), `page:N` (text layer PDF) hoặc `page:N/Q_ID` (bản chép AI của câu hỏi).
- `content`: nội dung gốc. Với CSV là JSON `[mặt trước, mặt sau]`.
- `content_hash`: sha256 của content.
- `extraction_method`: `csv_row`, `pdf_text_layer (incomplete…)` hoặc `ai_vision_transcription`.
- Trigger `raw_no_update` / `raw_no_delete` chặn mọi thay đổi.

### vocabulary (lớp NORMALIZED / CURATED)
| Cột | Ý nghĩa |
|---|---|
| id | `VOC_000001`… |
| word | Mặt trước flashcard, giữ nguyên (kanji hoặc kana) |
| reading | Kana. Nhiều cách đọc giữ nguyên dạng `なに / なん` (validator tách theo `/`) |
| romaji, han_viet | Trường phụ trợ; `han_viet` = NULL khi nguồn ghi "Không có Hán-Việt" hoặc "N/A" |
| meaning_vi, example_jp, example_romaji, example_vi | Từ CSV |
| part_of_speech | Chỉ đặt `verb` khi từ kết thúc bằng ます; còn lại NULL (không đoán) |
| verb_group | 1/2/3. **Luôn NULL khi import**: chỉ xác định từ thể từ điển, không suy từ ます |
| lesson_number, deck, topic | Suy từ tên tệp (`BaiN` → N; Kaiwa → topic `kaiwa`) |
| source_ids, raw_ids | JSON, truy vết tới nguồn và bản ghi RAW (các dòng trùng hoàn toàn được gộp) |
| level | `N5` (mở rộng N4–N1) |
| archived | Xoá mềm |

### validation_issues
- `origin`: `rule` (luật tự động), `ai_review` (AI rà soát, có `suggestion`) hoặc `user`.
- `severity`: `error`, `warning` hoặc `info`.
- Khi người dùng duyệt, `resolved = 1`.

Các mã chính:
- **Lỗi định dạng**: `missing_field`, `encoding`, `reading_not_kana`.
- **Lệch nhau giữa các trường**: `romaji_mismatch`, `kana_word_reading_differs`.
- **Hán-Việt**: `han_viet_count`, `han_viet_without_kanji`, `han_viet_missing`.
- **Trùng lặp**: `duplicate_reading_conflict`, `duplicate_same_word`.
- **Động từ**: `needs_dictionary_form`.
- **Dữ liệu RAW**: `unstructured_format`.
- **Do AI phát hiện**: `ai_<field>`.
- **Câu hỏi đề thi**: `transcription_unverified`, `options_image_only`, `audio_timestamp_missing`.
- **Do người dùng đánh dấu**: `ambiguous`, `reextract_requested`.

### review_actions
Nhật ký duyệt: approve, reject, edit, ambiguous, reextract, archive. Mỗi dòng lưu `before_json` và `after_json`.

### srs_cards, review_log
- Mỗi từ vựng có 2 thẻ: `jp_vi` và `vi_jp`.
- Mỗi thẻ có các trường: `ease` (≥ 1.3), `interval_days`, `reps` (số lần nhớ liên tiếp), `lapses`, `review_count`, `correct_count`, `incorrect_count`, `first_studied`, `last_studied`, `due_at`.
- `status` là một trong: new, learning, reviewing, mastered, needs_attention.
  - mastered: `interval ≥ 21` ngày và `reps ≥ 3`.
  - needs_attention: `lapses ≥ 3`.

### assets
- `IMG_N5_<FILE>_Pxxx`: ảnh render trang gốc, nằm ở `data/raw/<source_id>/pages/`.
- `AUD_N5S_001`: tệp MP3 gốc. Tham chiếu tới đường dẫn gốc, không sao chép.
- Có `transcript_status`.

### exams, passages, questions
- **exams**: `data_json` giữ nguyên cấu trúc section và mondai như đã chép.
- **passages**: đoạn văn dùng chung cho nhiều câu.
- **questions**:
  - `options`: JSON `[{option_id, text, image_asset_id?}]`. Khi lựa chọn là tranh hoặc glyph thì `text` = null.
  - `correct_answer`: JSON `["4"]`.
  - `answer_type`: `single_choice` hoặc `sentence_ordering`.
  - `extra_json` chứa các cờ: `options_audio_only`, `options_are_pictures`, `options_are_glyph_images`, `star_position`, `expected_sequence` (do AI suy luận, có ghi chú), `raw_id`.
  - `explanation_vi` kèm `explanation_origin = AI_GENERATED`.
  - `transcript`: script nghe.

## Tệp dữ liệu
| Đường dẫn | Lớp | Nội dung |
|---|---|---|
| `docs/N5/**` | nguồn gốc | Không bao giờ bị sửa |
| `data/raw/<source_id>/pages/*.png` | RAW | Ảnh render trang PDF (130 dpi) |
| `data/normalized/exams/EXAM_N5_OFFICIAL_SAMPLE.json` | NORMALIZED | 29 câu chép bằng AI từ ảnh kèm bảng 正解 |
| `data/normalized/exams/EXAM_N5_OFFICIAL_SAMPLE.ai_review.json` | AI_GENERATED | Đối chiếu đáp án và giải thích |
| `data/normalized/ai_review/vocabulary_ai_review.json` | AI_GENERATED | 68 phát hiện về nội dung flashcard |
| `data/sources_online.json` | registry | 24 nguồn trực tuyến trong spec |
| `data/database/hub.sqlite` | DB | Tạo lại bằng `python -m hub import` (tiến độ học nằm ở đây, cần sao lưu) |
