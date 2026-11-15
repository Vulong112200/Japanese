# DATA DICTIONARY

Định nghĩa đầy đủ: `backend/hub/db.py` (SQLite) và `schemas/*.schema.json` (định dạng trao đổi JSON, kiểm tra bằng `jsonschema` trong `backend/tests/test_data.py`).

## Trạng thái dùng chung
- `verification_status`: `raw | extracted | normalized | needs_review | verified | rejected`.
  - `normalized`: qua luật tự động nhưng chưa audit. Học được, hiện nhãn "Chưa xác minh".
  - `needs_review`: còn lỗi hoặc cảnh báo (từ luật, từ điển hoặc AI), hoặc là bản chép bằng AI, hoặc người dùng vừa sửa mà chưa duyệt.
  - `verified`: lớp CURATED. Cột `verified_by` cho biết ai xác minh:
    - `ai`: đã audit 2 vòng, khớp từ điển, không còn issue.
    - `user`: người dùng bấm "Duyệt".
- `verified_by`: `ai`, `user`, `pending_user` (người dùng đã sửa, chờ duyệt; automation không động vào) hoặc `NULL`.
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
| part_of_speech | Từ loại chính lấy từ JMdict: noun, verb, i_adjective, na_adjective, adverb, pronoun, expression, interjection, numeral, counter, suffix, prefix, particle, conjunction, prenominal. NULL nếu không tra được |
| verb_group | 1/2/3, chỉ xác định từ lớp chia của **thể từ điển** trong JMdict (見ます→見る→2; 切ります→切る→1). Không bao giờ suy từ ます |
| dictionary_form | Thể từ điển tìm được trong JMdict (vd. 借ります → 借りる) |
| verified_by | Xem mục "Trạng thái dùng chung" |
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
- **Từ điển**: `dict_reading_mismatch` (JMdict), `dict_han_viet_mismatch` (KANJIDIC2 + HV_OVERRIDES).
- **Trùng lặp**: `homograph` (cùng chữ, khác cách đọc; info), `duplicate_same_word` (info).
- **Động từ**: `needs_dictionary_form` (chỉ khi chưa có từ điển).
- **Dữ liệu RAW**: `unstructured_format`.
- **Câu hỏi AI để ngỏ**: `ai_open_question`.
- **Câu hỏi đề thi**: `transcription_unverified`, `options_image_only`, `audio_timestamp_missing`.
- **Do người dùng đánh dấu**: `ambiguous`, `reextract_requested`.

### review_actions
Nhật ký: `ai_correction` (bản sửa đã duyệt, kèm `basis`), approve, reject, edit, ambiguous, reextract, archive. Mỗi dòng lưu `before_json` và `after_json`.

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

### grammar
| Cột | Ý nghĩa |
|---|---|
| id | `GRA_000001`…`GRA_000135` (theo `data/normalized/grammar/n5_grammar_checklist.json`) |
| pattern, lesson_number | Mẫu câu; bài Minna (NULL = điểm N5 ngoài Minna 1–25 hoặc điểm đối chiếu) |
| grammar_name_vi, meaning_vi, formation, explanation_vi | Nội dung tiếng Việt |
| data_json | `usage`, `restrictions`, `formality`, `similar_patterns`, `common_mistakes`, `examples` [{jp, hiragana, romaji, vi}], `handbook_refs` (trích nguyên văn cẩm nang), `handbook_errors` (chỗ cẩm nang sai và cách sửa), `level_note` (ranh giới N5/N4) |
| origin | `handbook` / `handbook+ai` / `ai` |
| verification_status, verified_by | Chỉ `verified` khi `audited: true` trong file **và** kiểm tra tự động không ra lỗi/cảnh báo |

### kanji
| Cột | Ý nghĩa |
|---|---|
| id, kanji | `KAN_000001`…, chữ (UNIQUE) |
| han_viet, meaning_vi | Hán-Việt chuẩn (kiểm với KANJIDIC2 + HV_OVERRIDES), nghĩa tiếng Việt |
| onyomi, kunyomi | JSON. Tập con trong KANJIDIC2, chỉ giữ âm cần cho N5–N4 |
| stroke_count | Kiểm với KANJIDIC2 |
| example_words | JSON [{vocab_id (NULL nếu ngoài kho từ vựng), word, reading, meaning_vi}]; cách đọc kiểm với JMdict |

### kaiwa (hội thoại bổ trợ, ADR-023)
| Cột | Ý nghĩa |
|---|---|
| id, topic | `KAI_001`…; chủ đề: `self_intro, greetings, shopping, directions, transportation, restaurant, daily_routine, work_school, time_dates` |
| title_vi, situation_vi | Tên bài, tình huống |
| data_json | `lines` [{speaker, jp, hiragana, vi}], `vocab` [{ref, id, word, reading, meaning_vi}] (resolve từ từ vựng verified), `grammar` [{id, pattern}], `review_log` |
| origin, verification_status, verified_by | `ai`; chỉ `verified` khi `audited: true` trong file và `check_kaiwa` không ra lỗi/cảnh báo; `excluded: true` → `rejected` |

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
  - Câu sinh tự động (`exam_id='BANK_N5_GENERATED'`): `extraction_method='rule_generated'`, `verified_by='generator'`, `explanation_origin='AI_GENERATED'`; `extra_json` có `target` (chữ được gạch chân), `target_entity` (VOC id), `lesson_number`, `option_explanations` {option_id: lý do}, `generator`.

### exam_attempts, attempt_answers (thi thử)
- **exam_attempts**: `attempt_id` (`ATT_<thời gian>_<ngẫu nhiên>`), `exam_id` (NULL nếu tổ hợp từ ngân hàng), `title`, `mode` (`exam` | `practice`), `config_json` = `{filter, sections:[{section_id, section, name, duration_sec|null, question_ids}]}` đóng băng lúc bắt đầu, `current_section`, `section_started_at`, `started_at`, `submitted_at`, `result_json` (kết quả `score()` + `readiness`).
- **attempt_answers**: khoá (`attempt_id`, `question_id`); `answer` JSON danh sách option_id (NULL = chưa làm), `flagged`, `is_correct` (tính lúc lưu, chỉ trả về sau khi nộp ở chế độ thi), `answered_at`.

### settings
- Khoá/giá trị tuỳ chọn người học. Hiện có `daily_goal` (số lượt học mỗi ngày, 5–500, mặc định 30; ADR-022). API `GET/PUT /api/settings`.
- Ôn câu sai = câu có lần trả lời gần nhất (trong lượt đã nộp) là sai.

## Tệp dữ liệu
| Đường dẫn | Lớp | Nội dung |
|---|---|---|
| `docs/N5/**` | nguồn gốc | Không bao giờ bị sửa |
| `data/raw/<source_id>/pages/*.png` | RAW | Ảnh render trang PDF (130 dpi) |
| `data/normalized/exams/EXAM_N5_OFFICIAL_SAMPLE.json` | NORMALIZED | 29 câu chép bằng AI từ ảnh kèm bảng 正解 |
| `data/normalized/exams/EXAM_N5_OFFICIAL_SAMPLE.ai_review.json` | AI_GENERATED | Đối chiếu đáp án và giải thích |
| `data/normalized/corrections/vocabulary_corrections.json` | NORMALIZED (bản sửa) | `audit.items` (963 mục đã audit, khoá theo `raw_word`), `corrections` (167 bản sửa: id, raw_word, field, old_value, new_value, reason_vi, basis), `open_questions` |
| `data/normalized/supplements/vocabulary_supplement.json` | NORMALIZED | 290 từ bổ sung. Mỗi mục có `source_id` (`SRC_DRIVE_TONG_HOP_TU_VUNG_N5` = OCR PDF Minna, `SRC_REF_JLPT_N5` = danh sách JLPT), `raw` + `raw_locator` (dòng OCR/CSV gốc), các trường từ vựng, `review_log`, `audited`, và tuỳ chọn `excluded` / `separate_sense` |
| `data/normalized/grammar/n5_grammar_checklist.json` | khung | 135 điểm ngữ pháp N5, dùng để đo độ phủ |
| `data/normalized/grammar/grammar.json` | NORMALIZED | Nội dung 135 điểm (xem bảng grammar), `audited`, `review_log` |
| `data/normalized/kanji/kanji_n5.json` | NORMALIZED | 103 kanji N5, `audited`, `review_log` |
| `data/reference/jlpt_n5_words.csv` | tham chiếu | Danh sách JLPT N5, 718 từ (tanos.co.uk qua elzup/jlpt-word-list) |
| `data/raw/SRC_LESSON_002/ocr/*.json` | RAW | Kết quả OCR (Tesseract) của các PDF Drive; không commit |
| `docs/N5/SourceDocs/*.docx` | nguồn gốc | Cẩm nang ngữ pháp của bạn (`SRC_LOCAL_GRAMMAR_DOCX`) |
| `data/normalized/ai_review/vocabulary_ai_review.json` | AI_GENERATED | Rà soát vòng 1 (68 phát hiện), giữ làm bằng chứng |
| `data/normalized/ai_review/grammar_round2.json` | AI_GENERATED | Rà soát ngữ pháp vòng 2 (4 agent, 135 điểm): 19 đề xuất, mỗi đề xuất có `decision` (6 nhận, 13 loại kèm lý do) |
| `data/normalized/kaiwa/kaiwa.json` | NORMALIZED | 27 hội thoại (9 chủ đề × 3), `audited`, `review_log` (xem bảng kaiwa) |
| `data/normalized/ai_review/kaiwa_review.json` | AI_GENERATED | 2 vòng rà soát hội thoại: đề xuất của từng agent kèm `decision` (nhận/loại + lý do) |
| `data/sources_online.json` | registry | 24 nguồn trực tuyến trong spec |
| `data/reference/reference.sqlite` | tham chiếu | JMdict + KANJIDIC2 đã dựng (không commit; `python -m hub build-reference`) |
| `data/raw/SRC_GDOC_001/grammar_handbook.txt` | RAW | Google Doc ngữ pháp (export txt), không commit |
| `data/raw/SRC_LESSON_002/*.pdf` | RAW | PDF từ thư mục Drive công khai (scan), không commit |
| `data/database/hub.sqlite` | DB | Tạo lại bằng `python -m hub import` (tiến độ học nằm ở đây, cần sao lưu) |
