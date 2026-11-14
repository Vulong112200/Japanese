# PROJECT MASTER SPECIFICATION
# JAPANESE N5 LEARNING HUB
## Unified Learning, Practice, Examination & Resource Management System

**Project Type:** Full-stack Japanese Learning Platform  
**Target Level:** JLPT N5  
**Primary Language:** Vietnamese  
**Learning Language:** Japanese  
**Development Agent:** Claude Code  
**Primary Objective:** Build a reliable, source-driven Japanese N5 learning and examination platform.

---

# PART 1. ROLE AND MISSION

You are acting as a combination of:

1. Senior Software Architect.
2. Senior Full-stack Developer.
3. EdTech Platform Engineer.
4. Japanese Language Education Specialist.
5. JLPT N5 Examination Specialist.
6. Data Engineering and Document Processing Engineer.
7. Software QA and Data Quality Engineer.
8. UX/UI Designer specializing in learning applications.

Your mission is to design, implement, test and complete a comprehensive application named:

**Japanese N5 Learning Hub**

This application is intended for a Vietnamese learner preparing for the JLPT N5 examination.

The application must consolidate multiple learning resources into one centralized system, including:

- PDF examination papers.
- PDF textbooks and study materials.
- MP3 listening examinations.
- Word and Excel documents.
- JSON and CSV flashcard databases.
- Online examination websites.
- Online grammar and vocabulary resources.
- Google Drive learning materials.
- NotebookLM learning notebooks and generated exercises.
- YouTube learning resources.

The system must provide a complete learning lifecycle:

SOURCE COLLECTION → DATA EXTRACTION → DATA NORMALIZATION → VALIDATION → LEARNING → PRACTICE → MOCK EXAM → PERFORMANCE ANALYSIS → PERSONALIZED REVIEW.

## Non-negotiable principles

1. Accuracy before quantity.
2. Preserve original source materials.
3. Never fabricate original examination content.
4. Maintain traceability for every imported question and learning item.
5. Distinguish verified knowledge from AI-generated explanations.
6. Never silently resolve uncertain OCR, audio or answer data.
7. Never overwrite original source data.
8. Support offline learning whenever technically possible.
9. Make the system extensible for JLPT N4 and higher levels in the future.
10. Build a working application, not merely a UI prototype.

---

# PART 2. PROJECT ENVIRONMENT AND RESOURCE INVENTORY

Before implementation, inspect the existing project.

Do not assume that the application is greenfield.

Inspect:

- Existing source code.
- Framework and dependencies.
- Current database.
- Existing UI components.
- Existing flashcard data.
- Existing examination data.
- Existing audio and PDF processing modules.
- Existing application features.
- Existing configuration and environment variables.

Preserve useful existing functionality.

Do not rewrite stable modules unnecessarily.

## 2.1 Local resource directories

The user's local Windows directories are:

**Examination materials:**

`D:\Japanese\docs\N5\Exam`

**Flashcard materials:**

`D:\Japanese\docs\N5\flashcards`

You must inspect these directories when the development environment has access to the user's Windows filesystem.

Important:

If Claude Code is running inside WSL, Docker, a remote environment or another isolated environment, determine the actual mounted paths first.

Do not pretend that these directories have been successfully inspected if they are inaccessible.

Create an import report showing:

- File name.
- File extension.
- File size.
- File location.
- Document type.
- Number of pages where applicable.
- Number of detected questions.
- Number of detected audio files.
- Extraction status.
- Validation status.
- Potential duplicates.
- Processing errors.

Supported formats:

- PDF
- MP3
- WAV
- M4A
- DOCX
- DOC
- XLSX
- XLS
- TXT
- CSV
- JSON
- HTML
- ZIP

Images should also be supported as supplementary learning materials.

## 2.2 Online examination sources

Register the following sources in the Source Library.

### Source EXAM-001: GoJapan

URL:

https://gojapan.vn/thi-thu-jlpt/trinh-do-n5/

Purpose:

- Examine online N5 test structure.
- Collect publicly accessible sample question structures.
- Understand vocabulary, grammar, reading and listening exercises.
- Identify available answer explanations and audio resources.

### Source EXAM-002: Migii JLPT

URL:

https://jlpt.migii.net/vi/mock-test/jlpt-n5

Purpose:

- Analyze mock examination structure.
- Examine different N5 examination sets.
- Study the organization of vocabulary, grammar, reading and listening.
- Identify useful practice formats and feedback mechanisms.

### Source EXAM-003: Nihonez

URL:

https://nihonez.com/jlpt-n5-test/

Purpose:

- Analyze N5 question categories.
- Examine examination variations.
- Collect information about practice formats.
- Study listening and reading question structures.

### Web extraction requirements

For each website:

1. Check whether the page is publicly accessible.
2. Determine whether the content is rendered through HTML, JavaScript or an API.
3. Extract only content that is accessible and permitted for reuse.
4. Preserve original question order and question grouping.
5. Preserve images, audio references and associated answer choices.
6. Record the source URL and extraction timestamp.
7. Record any access restrictions or missing resources.
8. Never bypass authentication, payment restrictions or anti-bot protections.
9. Do not treat marketing claims as evidence of official JLPT accuracy.
10. When full extraction is impossible, retain the source URL as an external learning resource.

Do not silently substitute AI-generated questions for unavailable website questions.

## 2.3 Learning resources

### Source LESSON-001: HanoiLink N5 Vocabulary

https://hanoilink.vn/tu-vung-tieng-nhat-n5/

Purpose: N5 vocabulary reference.

### Source LESSON-002: Google Drive Learning Materials

https://drive.google.com/drive/folders/14cvGKUh4Gu7ojd2JE6FzWL5hCTSFwhaz

Purpose: Import available learning documents.

Access must use the user's authorized Google account or files explicitly provided to the development environment.

### Source LESSON-003: NHK Hiragana

https://www3.nhk.or.jp/nhkworld/lesson/vi/letters/hiragana.html

Purpose: Hiragana reference and foundational lessons.

### Source LESSON-004: Minna no Nihongo

https://riki.edu.vn/minna-no-nihongo/

Purpose: Reference for introductory Japanese learning and lesson organization.

### Source LESSON-005: N5 Grammar

https://vtimirai.edu.vn/tong-hop-ngu-phap-n5

Purpose: Grammar reference and supplementary explanations.

### Source LESSON-006: Minna Vocabulary

https://tailieuhoctiengnhat.com/tu-vung-minna.html

Purpose: Vocabulary reference and lesson mapping.

### Source LESSON-007: YouTube Learning Video

https://www.youtube.com/watch?v=d_wfY6lrHxA

Purpose: Supplementary video learning.

Preserve the original video URL and available metadata.

Do not claim that video transcripts or subtitles have been extracted unless they have actually been obtained.

## 2.4 Existing study notebook

Google Notebook:

https://notebook.google.com/notebook/2c99f9e6-272f-4001-a41b-75525f4030f1

This notebook is an important learning reference.

Attempt to access it through an authorized integration or user-provided export.

If access is unavailable, report the limitation and request an export rather than inventing notebook contents.

## 2.5 Grammar document

Google Docs:

https://docs.google.com/document/d/1tjsZBG5RAsIOlqKM_r7dfzlB1b1HKOzVu6YQDm_eUI0/edit?usp=sharing

Purpose:

- Import existing grammar notes.
- Preserve original explanations.
- Extract grammar patterns.
- Build a normalized grammar database.
- Identify missing explanations and examples.

## 2.6 Grammar examination resources

Register all following NotebookLM resources:

1. https://notebooklm.link.google/iIWZ2CoIyutB
2. https://notebooklm.link.google/PvlvBIQvwLE0
3. https://notebooklm.link.google/E1tKkWXMuLm0
4. https://notebooklm.link.google/FZQE68kThNQl
5. https://notebooklm.link.google/940FjRi2u6rW
6. https://notebooklm.link.google/MH5RGRvyIV45
7. https://notebooklm.link.google/fn52vUymA8CR
8. https://notebooklm.link.google/aFpUgNpCr6eN
9. https://notebooklm.link.google/zPmBOgKacTtV
10. https://notebooklm.link.google/SqBkbHRgN5Nt

Purpose:

- Collect grammar practice material.
- Extract questions and answer explanations where accessible.
- Categorize exercises by grammar point.
- Compare overlapping questions.
- Identify recurring grammar mistakes.

If NotebookLM content is inaccessible, create an external resource record and mark it as requiring manual import.

---

# PART 3. SOURCE MANAGEMENT AND DATA GOVERNANCE

This is the most important architectural requirement.

Build a centralized Source Management module.

Every imported resource must have a unique `source_id`.

## 3.1 Three-layer data architecture

Implement three independent data layers.

### Layer 1: RAW

Contains original extracted information.

Examples:

- Original PDF page text.
- Original question wording.
- Original answer choices.
- Original audio files.
- Original website content.
- Original images.
- Original document metadata.

Never modify raw records automatically.

### Layer 2: NORMALIZED

Contains structured and standardized information.

Examples:

- Standardized vocabulary.
- Standardized kanji.
- Grammar patterns.
- Question records.
- Answer choices.
- Audio references.
- Reading passages.

Normalization must not change the original meaning.

### Layer 3: CURATED

Contains verified content approved for learning and examination.

A record may enter the curated layer only after passing the applicable validation requirements.

## 3.2 Data provenance

Every record must support the following metadata:

```json
{
  "source_id": "SRC_EXAM_001",
  "source_type": "pdf",
  "source_name": "N5_Practice_01.pdf",
  "source_location": "D:/Japanese/docs/N5/Exam/N5_Practice_01.pdf",
  "source_url": null,
  "page_number": 3,
  "question_number": 12,
  "extraction_method": "pdf_text",
  "extracted_at": "2026-11-14T10:00:00+07:00",
  "content_hash": "sha256-value",
  "verification_status": "verified",
  "review_notes": null
}
```

The metadata must be adaptable to website, audio and document sources.

## 3.3 Source reliability classification

Use the following categories:

- OFFICIAL: Official JLPT or Japan Foundation materials.
- PRIMARY: Original examination papers or original learning documents.
- EDUCATIONAL: Educational websites and textbooks.
- SUPPLEMENTARY: YouTube and other supporting learning resources.
- AI_GENERATED: Newly generated educational content.
- USER_CREATED: User-provided notes or manually entered content.

Never label a third-party mock examination as an official examination.

---

# PART 4. OFFICIAL JLPT N5 EXAMINATION STANDARD

Use the official JLPT examination structure as the primary reference.

Official references:

https://www.jlpt.jp/e/guideline/testsections.html

https://www.jlpt.jp/e/guideline/results.html

## 4.1 Current N5 examination timing

| Examination section | Duration |
|---|---:|
| Language Knowledge: Vocabulary | 20 minutes |
| Language Knowledge: Grammar + Reading | 40 minutes |
| Listening | 30 minutes |

Total examination time: 90 minutes.

Do not use outdated examination timings as the default.

Historical papers must retain their original timing metadata.

## 4.2 Examination question categories

### A. Vocabulary: 文字・語彙

Support:

1. 漢字読み: Kanji reading.
2. 表記: Orthography.
3. 文脈規定: Contextually-defined expressions.
4. 言い換え類義: Paraphrases and similar expressions.

### B. Grammar: 文法

Support:

1. 文の文法1: Selecting the appropriate grammar form.
2. 文の文法2: Sentence composition and ordering.
3. 文章の文法: Text grammar and sentence relationships.

### C. Reading: 読解

Support:

1. 内容理解（短文）: Short passage comprehension.
2. 内容理解（中文）: Mid-size passage comprehension.
3. 情報検索: Information retrieval.

### D. Listening: 聴解

Support:

1. 課題理解: Task-based comprehension.
2. ポイント理解: Comprehension of key points.
3. 発話表現: Verbal expressions.
4. 即時応答: Quick response.

Keep original question-type labels when importing historical papers.

Do not force every historical question into a newly invented category.

## 4.3 Scoring rules

JLPT N5 official score structure:

- Language Knowledge (Vocabulary/Grammar) + Reading: 0–120.
- Listening: 0–60.
- Total: 0–180.
- Overall passing score: 80.
- Minimum sectional score for Language Knowledge + Reading: 38.
- Minimum sectional score for Listening: 19.

Important:

Official JLPT scores use scaled scoring.

The application may calculate raw correct answers and estimated practice scores, but must never claim that a simple percentage is the actual official JLPT score.

Provide two separate results:

1. Practice performance: Correct answers, incorrect answers and percentages.
2. Estimated JLPT readiness: An explicitly labeled approximation, never an official score.

---

# PART 5. CORE APPLICATION MODULES

## MODULE 01: SOURCE LIBRARY

Build a centralized resource management interface.

Features:

- Add local files.
- Import folders.
- Register website URLs.
- Register Google Drive resources.
- Register NotebookLM resources.
- Import ZIP archives.
- Preview imported documents.
- Search resources.
- Filter by source type.
- Track processing status.
- Track validation status.
- Detect duplicate resources.
- Reprocess failed imports.
- Export source metadata.

Each resource should display:

- Resource name.
- Resource type.
- Origin.
- Import date.
- Processing status.
- Number of extracted records.
- Validation status.
- Associated lessons and questions.

Possible processing statuses:

- pending
- importing
- extracting
- normalizing
- validating
- verified
- needs_review
- failed

## MODULE 02: DOCUMENT AND MEDIA INGESTION ENGINE

Build an extensible ingestion pipeline.

### PDF processing

Support:

- Text-based PDF.
- Scanned PDF.
- Mixed text and image PDF.
- Multi-column layouts.
- Japanese text.
- Furigana.
- Tables.
- Embedded images.
- Question illustrations.
- Answer sheets.

Use OCR when necessary.

OCR must preserve Japanese characters accurately.

Do not discard original page images.

For every extracted question, retain page and position references whenever possible.

### MP3 processing

Support:

- MP3.
- WAV.
- M4A.
- Multiple audio files.
- Audio linked to multiple questions.
- Audio linked to an examination section.

Features:

- Playback.
- Pause.
- Replay.
- Seek.
- Playback speed.
- Audio grouping.
- Transcript when available.
- Timestamp references.
- Original audio download or local storage.

Do not automatically treat an AI-generated transcript as verified.

### Website processing

Support:

- URL registration.
- Accessible HTML extraction.
- JavaScript-rendered content where permitted.
- Question extraction.
- Answer extraction.
- Image extraction.
- Audio reference extraction.
- Source URL preservation.

Provide an import preview before saving extracted records.

### Import pipeline

Use this workflow:

1. Detect file type.
2. Validate file integrity.
3. Extract original content.
4. Preserve raw content.
5. Normalize data.
6. Detect duplicates.
7. Validate content.
8. Generate import report.
9. Require review when confidence is insufficient.
10. Publish verified records to the learning database.

Implement retry and error logging.

---

# PART 6. STANDARDIZED LEARNING DATABASE

Use JSON as the canonical exchange format.

Use a relational database for application persistence where appropriate.

Every entity must have a stable unique ID.

## 6.1 Vocabulary schema

```json
{
  "id": "VOC_000001",
  "kanji": "学校",
  "hiragana": "がっこう",
  "katakana": null,
  "romaji": "gakkou",
  "han_viet": "HỌC HIỆU",
  "meaning_vi": "Trường học",
  "part_of_speech": "noun",
  "verb_group": null,
  "transitivity": null,
  "lesson_number": 1,
  "jlpt_level": "N5",
  "topic": ["education"],
  "example_jp": "わたしは学校へ行きます。",
  "example_reading": "わたしはがっこうへいきます。",
  "example_romaji": "Watashi wa gakkou e ikimasu.",
  "example_vi": "Tôi đi đến trường.",
  "source_ids": ["SRC_LESSON_001"],
  "verification_status": "verified",
  "review_status": "not_started",
  "tags": []
}
```

### Vocabulary requirements

Support:

- Kanji.
- Hiragana.
- Katakana.
- Romaji.
- Hán-Việt.
- Vietnamese meanings.
- Part of speech.
- Verb group.
- Transitivity.
- Example sentences.
- Lesson number.
- JLPT level.
- Topic.
- Synonyms.
- Antonyms.
- Related words.
- Source references.

Romaji and Hán-Việt should be supplementary learning fields, not substitutes for Japanese readings.

If an item has multiple readings or meanings, store them separately rather than forcing one reading into a single field.

Do not invent Hán-Việt readings for words without an appropriate established reading.

### Verb group classification

Group 1: 五段動詞.

Group 2: 一段動詞.

Group 3: Irregular verbs.

Special validation:

Do not classify verbs only by their ending.

Examples requiring attention:

- 見ます → 見る → Group 2.
- 起きます → 起きる → Group 2.
- 降ります → 降りる → Group 2.
- 借ります → 借りる → Group 2.
- 浴びます → 浴びる → Group 2.
- 着ます → 着る → Group 2.
- 切ります → 切る → Group 1.
- 帰ります → 帰る → Group 1.
- 入ります → 入る → Group 1.

Use dictionary forms to determine verb groups.

Never infer the group solely from the -imasu form.

## 6.2 Kanji schema

```json
{
  "id": "KAN_000001",
  "kanji": "日",
  "meaning_vi": "Ngày, mặt trời",
  "han_viet": "NHẬT",
  "onyomi": ["ニチ", "ジツ"],
  "kunyomi": ["ひ", "か"],
  "common_readings": ["にち", "ひ"],
  "example_words": [
    {
      "word": "日本",
      "reading": "にほん",
      "meaning_vi": "Nhật Bản"
    },
    {
      "word": "日曜日",
      "reading": "にちようび",
      "meaning_vi": "Chủ nhật"
    }
  ],
  "stroke_count": 4,
  "jlpt_level": "N5",
  "source_ids": [],
  "verification_status": "verified"
}
```

Do not mix kun'yomi, on'yomi and actual vocabulary readings.

## 6.3 Grammar schema

```json
{
  "id": "GRA_000001",
  "pattern": "N は N です",
  "grammar_name_vi": "Câu khẳng định với です",
  "meaning_vi": "A là B",
  "formation": "Danh từ 1 + は + Danh từ 2 + です",
  "explanation_vi": "Dùng để giới thiệu hoặc xác nhận một thông tin.",
  "usage": [
    "Giới thiệu bản thân",
    "Xác định một sự vật hoặc người"
  ],
  "examples": [
    {
      "jp": "わたしは学生です。",
      "hiragana": "わたしはがくせいです。",
      "romaji": "Watashi wa gakusei desu.",
      "vi": "Tôi là học sinh."
    }
  ],
  "common_mistakes": [],
  "related_grammar_ids": [],
  "lesson_number": 1,
  "jlpt_level": "N5",
  "source_ids": [],
  "verification_status": "verified"
}
```

Grammar explanations must distinguish:

- Meaning.
- Formation.
- Usage.
- Restrictions.
- Formality.
- Similar patterns.
- Common mistakes.
- Exceptions.

Do not create superficial explanations that merely translate the grammar pattern.

## 6.4 Question schema

Use a flexible question model.

Do not limit all questions to a single four-option structure.

```json
{
  "question_id": "Q_N5_000001",
  "exam_id": "EXAM_N5_001",
  "section": "vocabulary",
  "mondai_type": "kanji_reading",
  "question_text": "学校へ行きます。",
  "question_instruction": "学校の読み方を選んでください。",
  "passage_id": null,
  "options": [
    {
      "option_id": "A",
      "text": "がっこう"
    },
    {
      "option_id": "B",
      "text": "がこう"
    },
    {
      "option_id": "C",
      "text": "かっこう"
    },
    {
      "option_id": "D",
      "text": "かこう"
    }
  ],
  "correct_answer": ["A"],
  "answer_type": "single_choice",
  "explanation_vi": "学校 được đọc là がっこう.",
  "option_explanations": {
    "A": "Đúng: cách đọc chính xác.",
    "B": "Sai: thiếu âm ngắt nhỏ っ.",
    "C": "Sai: âm đầu không chính xác.",
    "D": "Sai: cách đọc không đúng."
  },
  "jlpt_trap_warning": "Chú ý âm ngắt nhỏ っ.",
  "audio_asset_id": null,
  "image_asset_id": null,
  "source_ids": [],
  "difficulty": "easy",
  "verification_status": "verified"
}
```

### Flexible question types

Support:

- Single choice.
- Multiple choice.
- Fill in the blank.
- Sentence ordering.
- Sentence composition.
- Passage-based questions.
- Audio-based questions.
- Image-based questions.
- Listening response selection.

For sentence ordering, store token order and the expected correct sequence.

For passage-based questions, use a shared passage entity rather than duplicating the entire passage in every question.

For listening questions, reference an audio asset and optionally timestamps.

## 6.5 Audio asset schema

```json
{
  "audio_asset_id": "AUD_000001",
  "source_id": "SRC_EXAM_001",
  "file_name": "listening_01.mp3",
  "file_path": "assets/audio/listening_01.mp3",
  "duration_seconds": 45,
  "mime_type": "audio/mpeg",
  "transcript": null,
  "transcript_status": "not_transcribed",
  "associated_question_ids": [
    "Q_N5_000101"
  ],
  "verification_status": "verified"
}
```

## 6.6 Examination schema

```json
{
  "exam_id": "EXAM_N5_001",
  "title": "JLPT N5 Mock Examination 01",
  "level": "N5",
  "exam_type": "mock",
  "source_type": "AI_GENERATED",
  "is_official": false,
  "duration_minutes": 90,
  "sections": [
    {
      "section_id": "SEC_01",
      "name": "Vocabulary",
      "duration_minutes": 20,
      "question_ids": []
    },
    {
      "section_id": "SEC_02",
      "name": "Grammar and Reading",
      "duration_minutes": 40,
      "question_ids": []
    },
    {
      "section_id": "SEC_03",
      "name": "Listening",
      "duration_minutes": 30,
      "question_ids": []
    }
  ],
  "source_ids": [],
  "verification_status": "verified"
}
```

The actual historical examination must retain its original duration and section organization.

Do not overwrite historical metadata to match the current examination format.

---

# PART 7. LEARNING MODULES

## 7.1 Vocabulary Learning

Organize vocabulary by:

- Minna no Nihongo lesson.
- JLPT N5 topic.
- Part of speech.
- Verb group.
- Learning status.
- Difficulty.
- Source.

Provide:

- Flashcard mode.
- List mode.
- Search.
- Filters.
- Random practice.
- Japanese-to-Vietnamese testing.
- Vietnamese-to-Japanese testing.
- Listening and pronunciation support.
- Example sentences.
- Related vocabulary.

Target coverage:

Approximately 700–800 or more relevant N5 vocabulary entries.

Do not claim that one fixed vocabulary count is the official JLPT requirement.

## 7.2 Kanji Learning

Target approximately 100 basic N5 kanji.

Features:

- Character display.
- On'yomi.
- Kun'yomi.
- Vietnamese meaning.
- Hán-Việt.
- Stroke count.
- Vocabulary examples.
- Reading quizzes.
- Recognition quizzes.
- Related words.

## 7.3 Grammar Learning

Create a structured N5 grammar library.

Organize by:

- Minna no Nihongo lesson.
- Grammar category.
- Particle.
- Verb conjugation.
- Sentence structure.
- Similar grammar patterns.

Prioritize:

Particles:

は、が、を、に、で、へ、と、から、まで、も、や、の、か

Verb forms:

- ます形
- 辞書形
- て形
- ない形
- た形
- ません形
- ましょう形
- たい形

Adjectives:

- い形容詞
- な形容詞
- Past forms.
- Negative forms.

Other important grammar:

- です / ます.
- あります / います.
- から / まで.
- もう / まだ.
- ことができます.
- てください.
- てもいいです.
- てはいけません.
- なければなりません.
- ないでください.
- たことがあります.

Only include grammar appropriate to the target learning syllabus.

Do not automatically classify every grammar point as official JLPT N5 vocabulary or grammar.

## 7.4 Kaiwa Practice

Create a separate supplementary conversation module.

Include:

- Self-introduction.
- Greetings.
- Shopping.
- Asking for directions.
- Transportation.
- Ordering food.
- Daily routines.
- Work and school.
- Time and dates.

Each conversation should include:

- Japanese dialogue.
- Hiragana support.
- Vietnamese translation.
- Vocabulary references.
- Grammar references.
- Audio when available.

Kaiwa is supplementary learning and must not be included as an independent official JLPT N5 examination section.

---

# PART 8. SMART FLASHCARD AND REVIEW ENGINE

Implement spaced repetition.

Use an SM-2-compatible algorithm or a configurable scheduling algorithm.

Each vocabulary or grammar item must track:

- First studied date.
- Last studied date.
- Review count.
- Correct count.
- Incorrect count.
- Current interval.
- Ease factor or equivalent.
- Next review date.
- Mastery status.

Support:

1. New.
2. Learning.
3. Reviewing.
4. Mastered.
5. Needs attention.

Flashcard actions:

- Again.
- Hard.
- Good.
- Easy.

Do not mark an item as mastered after a single correct response.

Include a daily review dashboard.

---

# PART 9. MOCK EXAM ENGINE

This is a core application feature.

The exam engine must support both original examination imports and newly generated practice examinations.

## 9.1 Examination modes

### Mode A: Full Mock Examination

- Follow current JLPT N5 timing.
- Display section-specific timers.
- Preserve question order.
- Support audio.
- Support answer navigation.
- Auto-save answers.
- Submit and calculate results.

### Mode B: Historical Examination

- Preserve original source structure.
- Preserve original number of questions.
- Preserve original audio.
- Preserve original duration.
- Identify the examination year when known.

### Mode C: Section Practice

Practice vocabulary, grammar, reading or listening separately.

### Mode D: Question-Type Practice

Practice one specific Mondai type.

### Mode E: Mistake Review

Automatically collect incorrect questions.

### Mode F: Custom Examination

Allow users to select:

- Question categories.
- Difficulty.
- Number of questions.
- Time limit.
- Learning topics.
- Previously incorrect questions.

## 9.2 Examination interface

Include:

- Question number.
- Question navigation.
- Answer selection.
- Section timer.
- Audio player.
- Flag for review.
- Previous and next buttons.
- Progress indicator.
- Confirmation before submission.

During examination mode, do not display explanations or correct answers.

Only show explanations after submission or when the user explicitly selects practice mode.

## 9.3 Examination scoring

Display:

- Total questions.
- Correct answers.
- Incorrect answers.
- Unanswered questions.
- Accuracy percentage.
- Performance by section.
- Performance by Mondai.
- Weak grammar topics.
- Weak vocabulary topics.
- Listening accuracy.

Keep raw results separate from estimated scaled JLPT scores.

Do not fabricate official scaled scores.

---

# PART 10. LISTENING ENGINE

Listening requires special attention because PDF text alone cannot reconstruct an original listening examination.

Support:

- Original MP3.
- WAV and M4A.
- Multiple audio tracks.
- Audio-question associations.
- Audio replay.
- Playback speed.
- Audio progress.
- Optional transcript.
- Optional transcript timestamps.

Provide two separate modes:

**Exam mode:**

- No transcript before answering.
- Follow the original audio rules.
- Prevent accidental exposure to answers.

**Study mode:**

- Allow repeated playback.
- Allow transcript when verified or available.
- Display vocabulary and grammar explanations.
- Allow sentence-by-sentence review.

If an original audio file is missing, mark the question as incomplete.

Never generate replacement audio and label it as original examination audio.

---

# PART 11. DATA QUALITY AND ACCURACY CONTROL

This module must be implemented before bulk content generation.

## 11.1 Verification status

Every learning item and examination question must support:

- raw
- extracted
- normalized
- needs_review
- verified
- rejected

## 11.2 Automated validation

Check:

1. Japanese character integrity.
2. Hiragana and Katakana consistency.
3. Kanji readings.
4. Romaji consistency.
5. Vietnamese meanings.
6. Verb group classification.
7. Grammar formation.
8. Question structure.
9. Answer-option completeness.
10. Correct-answer references.
11. Audio references.
12. Image references.
13. Duplicate questions.
14. Duplicate vocabulary.
15. Source references.
16. Examination section mapping.

## 11.3 Ambiguity handling

If the correct answer cannot be verified:

- Do not guess.
- Do not publish as verified.
- Mark `needs_review`.
- Preserve the original content.
- Record the reason.
- Provide a review interface.

If two answers are linguistically acceptable, explain the ambiguity and do not force an incorrect single-answer key.

## 11.4 Human review interface

Build a dedicated review screen.

Display:

- Original source content.
- Extracted content.
- Normalized content.
- AI interpretation.
- Suggested answer.
- Confidence level.
- Source reference.
- Review decision.

Available actions:

- Approve.
- Reject.
- Edit.
- Request re-extraction.
- Mark ambiguous.

## 11.5 AI-generated content rules

AI-generated questions must:

- Be labeled AI_GENERATED.
- Have a clear target grammar or vocabulary point.
- Have exactly one intended correct answer when using single-choice format.
- Have plausible but unambiguously incorrect distractors.
- Include explanations for all answer options.
- Be checked against the N5 syllabus.
- Be validated before entering the curated bank.

AI must never claim that generated questions are official JLPT questions.

---

# PART 12. DATABASE AND TECHNICAL ARCHITECTURE

Inspect the existing stack before choosing a technology.

Prefer preserving the current working framework.

If no usable stack exists, propose a practical architecture with:

- Frontend: React + TypeScript.
- UI: Tailwind CSS and a consistent component library.
- Backend: Python FastAPI or an equivalent maintainable backend.
- Database: SQLite for a local-first single-user application.
- Optional PostgreSQL for future multi-user expansion.
- Local asset storage for PDFs, MP3 and images.
- JSON import/export.
- PWA or equivalent offline-capable delivery where suitable.

Use a repository pattern or equivalent separation between application logic and database access.

Separate:

- UI.
- Business logic.
- Data access.
- Import processing.
- Validation.
- Learning algorithms.
- Examination logic.

Do not put all business logic inside UI components.

## Suggested project organization

```text
japanese-n5-learning-hub/
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── modules/
│   │   │   ├── dashboard/
│   │   │   ├── vocabulary/
│   │   │   ├── kanji/
│   │   │   ├── grammar/
│   │   │   ├── practice/
│   │   │   ├── examination/
│   │   │   ├── listening/
│   │   │   ├── review/
│   │   │   ├── analytics/
│   │   │   └── library/
│   │   └── services/
│   │
├── backend/
│   ├── api/
│   ├── services/
│   ├── repositories/
│   ├── models/
│   ├── schemas/
│   ├── ingestion/
│   ├── extraction/
│   ├── validation/
│   ├── exam_engine/
│   └── learning_engine/
│
├── data/
│   ├── raw/
│   ├── normalized/
│   ├── curated/
│   ├── exports/
│   └── database/
│
├── assets/
│   ├── audio/
│   ├── images/
│   └── documents/
│
├── schemas/
│   ├── vocabulary.schema.json
│   ├── kanji.schema.json
│   ├── grammar.schema.json
│   ├── question.schema.json
│   └── examination.schema.json
│
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── data_quality/
│   └── examination/
│
├── docs/
│   ├── ARCHITECTURE.md
│   ├── DATA_DICTIONARY.md
│   ├── SOURCE_CATALOG.md
│   ├── IMPORT_REPORT.md
│   ├── DATA_QUALITY_REPORT.md
│   └── USER_GUIDE.md
│
└── README.md
```

This is a proposed structure, not a requirement to duplicate an existing project unnecessarily.

---

# PART 13. UI/UX REQUIREMENTS

Build a clean, modern, practical Japanese learning interface.

The application should prioritize studying rather than decorative elements.

## Main navigation

1. Dashboard.
2. Lessons.
3. Vocabulary.
4. Kanji.
5. Grammar.
6. Practice.
7. Mock Examination.
8. Listening.
9. Smart Review.
10. Resource Library.
11. Analytics.
12. Settings.

## Dashboard

Display:

- Current JLPT level.
- Today's learning goal.
- Daily study streak.
- Vocabulary mastery.
- Kanji mastery.
- Grammar mastery.
- Upcoming reviews.
- Recent examination results.
- Weakest learning categories.
- Recommended next activities.

## Visual requirements

- Responsive desktop and mobile layouts.
- Good Japanese typography.
- Proper rendering of Japanese characters.
- Readable furigana.
- Clear question navigation.
- Consistent spacing.
- Accessible contrast.
- Dark and light themes.
- Minimal unnecessary animation.

Prioritize usability and fast navigation.

---

# PART 14. ANALYTICS AND PERSONALIZED LEARNING

Build a learning analytics engine.

Track:

- Total study time.
- Daily study time.
- Vocabulary retention.
- Kanji accuracy.
- Grammar accuracy.
- Reading performance.
- Listening performance.
- Examination history.
- Incorrect question history.
- Repeated mistakes.
- SRS review performance.

Create a weakness analysis engine.

Example:

If the learner repeatedly confuses:

- は and が.
- に and で.
- あります and います.
- 見る and 見える.
- 着る and 切る.

The system should identify the underlying learning topic and recommend related lessons and exercises.

Recommendations must be based on actual user performance data.

Do not generate meaningless recommendations from arbitrary random rules.

---

# PART 15. TESTING AND ACCEPTANCE CRITERIA

The application is not complete merely because the UI loads.

Implement automated tests and functional verification.

## Data tests

- JSON schema validation.
- Required field validation.
- Japanese Unicode integrity.
- Duplicate detection.
- Referential integrity.
- Source traceability.
- Audio asset existence.
- Image asset existence.
- Correct answer validation.

## Application tests

- Import PDF.
- Import MP3.
- Import JSON.
- Import CSV.
- Register website URLs.
- Create vocabulary.
- Create grammar.
- Edit flashcards.
- Delete or archive records safely.
- Search and filter.
- Complete a practice session.
- Complete a full mock examination.
- Save examination results.
- Review incorrect questions.
- Restore user progress.
- Export and import backups.
- Offline operation.

## Examination engine tests

Verify:

- Correct timer behavior.
- Section transitions.
- Answer persistence.
- Question navigation.
- Unanswered questions.
- Submission behavior.
- Audio playback.
- Score calculation.
- Result history.

## Acceptance criteria

The application is considered ready only when:

1. Existing project functionality remains intact.
2. All core modules work.
3. Source records are traceable.
4. Imported content retains its original source references.
5. Invalid or uncertain records cannot silently enter the verified bank.
6. Examination timing follows the appropriate examination version.
7. Listening questions work with their associated audio.
8. Examination results persist correctly.
9. Review scheduling works.
10. The application can be backed up and restored.
11. The application can operate offline for locally available learning materials.
12. Critical automated tests pass.

---

# PART 16. DEVELOPMENT WORKFLOW

Do not attempt to implement every module in one uncontrolled operation.

Follow these phases.

## Phase 0: Existing Project Audit

Deliver:

- Project structure report.
- Existing technology stack.
- Existing database report.
- Existing feature report.
- Technical debt report.
- Proposed implementation plan.

Do not modify existing code until the audit is complete.

## Phase 1: Source Inventory and Data Architecture

Implement:

- Source Library.
- File inventory.
- Source metadata.
- JSON schemas.
- Database models.
- Raw, normalized and curated data layers.

Deliver:

- SOURCE_CATALOG.md.
- DATA_DICTIONARY.md.
- Import report.
- Database schema.

## Phase 2: Ingestion and Validation

Implement:

- PDF extraction.
- OCR.
- Audio asset import.
- JSON and CSV import.
- Website registration and extraction.
- Data normalization.
- Duplicate detection.
- Validation.
- Human review.

Deliver:

- Working import pipeline.
- Validation report.
- Sample imported records.
- Error handling.

## Phase 3: Learning Database

Implement:

- Vocabulary.
- Kanji.
- Grammar.
- Lesson mapping.
- Flashcards.
- Search and filtering.

Populate from verified available resources.

## Phase 4: Practice and Review Engine

Implement:

- Vocabulary practice.
- Kanji practice.
- Grammar exercises.
- Reading exercises.
- Listening practice.
- SRS review.
- Incorrect answer tracking.

## Phase 5: Mock Examination Engine

Implement:

- Full examinations.
- Historical examinations.
- Section practice.
- Listening examinations.
- Timers.
- Answer persistence.
- Results.
- Detailed explanations.

## Phase 6: Dashboard and Analytics

Implement:

- Learning progress.
- Weakness analysis.
- Daily learning goals.
- Study recommendations.
- Examination readiness estimation.

## Phase 7: Final QA and Documentation

Perform:

- Full regression tests.
- Data integrity tests.
- UI testing.
- Offline testing.
- Backup and restore tests.
- Performance optimization.

Deliver:

- Final QA report.
- User guide.
- Installation guide.
- Data import guide.
- Known limitations.
- Future improvement roadmap.

---

# PART 17. REQUIRED DELIVERABLES

At the end of development, provide:

1. Fully functional application.
2. Complete source code.
3. Database schema.
4. JSON data schemas.
5. Imported vocabulary database.
6. Imported Kanji database.
7. Imported grammar database.
8. Imported examination database.
9. Audio asset mapping.
10. Source catalog.
11. Data quality report.
12. Examination validation report.
13. Installation instructions.
14. User guide.
15. Backup and restoration instructions.
16. Automated tests.
17. Future development roadmap.

Do not mark an unavailable deliverable as completed.

Clearly distinguish:

- Completed.
- Partially completed.
- Requires user input.
- Blocked by external access.
- Not implemented.

---

# PART 18. IMPORTANT DEVELOPMENT RULES

1. Inspect the existing project before editing.
2. Do not invent files, directories or source content.
3. Do not fabricate imported examination questions.
4. Do not replace missing audio with invented original audio.
5. Do not invent answer keys.
6. Do not silently modify original question wording.
7. Do not discard source metadata.
8. Do not overwrite raw data.
9. Do not use mock data in production screens without labeling it.
10. Do not claim that all resources have been imported when only a subset has been processed.
11. Do not claim that OCR is 100% accurate.
12. Do not hardcode all questions directly into frontend components.
13. Do not generate thousands of unverified flashcards merely to satisfy a target count.
14. Keep the database extensible for N4, N3, N2 and N1.
15. Keep the application maintainable and easy to extend.
16. Document technical decisions.
17. Test each module before moving to the next phase.

When requirements are ambiguous, inspect the project and available data first. Ask only for information that cannot be obtained safely from the existing environment.

---

# PART 19. INITIAL EXECUTION INSTRUCTIONS

Start by performing the following tasks:

### Task 1: Audit

Inspect the current application and produce a technical report.

### Task 2: Inventory

Inspect:

- D:\Japanese\docs\N5\Exam
- D:\Japanese\docs\N5\flashcards

If inaccessible, explain exactly why and provide the required file transfer or mount instructions.

### Task 3: Source Assessment

Register all online sources in this specification.

Determine which sources are accessible, which require authentication and which need manual export.

### Task 4: Architecture

Produce:

- Architecture diagram.
- Database ERD.
- Data flow diagram.
- Module dependency diagram.
- Data validation workflow.

### Task 5: Data Schema

Create the initial JSON schemas and sample records.

Validate them programmatically.

### Task 6: Implementation Plan

Provide an ordered implementation plan based on the existing application.

Identify dependencies, risks and milestones.

### Task 7: Begin Development

After completing the audit and architecture, begin implementing the highest-priority modules.

Do not stop after presenting recommendations.

Proceed with implementation, testing and documentation.

If a critical external dependency is inaccessible, implement the supported parts and clearly document the remaining blocker.

---

# FINAL SUCCESS DEFINITION

The final result must be a personal Japanese N5 Learning Hub that allows the learner to:

- Collect learning resources from different sources.
- Import examination papers and learning documents.
- Preserve and retrieve original content.
- Learn vocabulary and Kanji systematically.
- Understand N5 grammar thoroughly.
- Practice all JLPT N5 question categories.
- Listen to original MP3 examination audio.
- Complete timed mock examinations.
- Review incorrect answers.
- Understand why an answer is correct or incorrect.
- Identify weak areas.
- Track progress over time.
- Study offline using locally available content.

**The most important requirement is not to build the largest possible question bank. It is to build a trustworthy learning system in which every question, answer, vocabulary item and grammar explanation can be traced, checked and corrected.**

Build this system as a maintainable software product, not as a collection of disconnected study pages.