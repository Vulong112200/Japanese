"""SQLite schema and connection. Plain sqlite3, no ORM (see docs/ARCHITECTURE.md ADR-002)."""
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = ROOT / "data" / "database" / "hub.sqlite"

SCHEMA = """
CREATE TABLE IF NOT EXISTS sources (
  source_id TEXT PRIMARY KEY,
  source_type TEXT NOT NULL,              -- pdf|mp3|csv|website|google_drive|google_doc|notebooklm|youtube|...
  name TEXT NOT NULL,
  location TEXT,                          -- local path (forward slashes)
  url TEXT,
  reliability TEXT NOT NULL CHECK (reliability IN
    ('OFFICIAL','PRIMARY','EDUCATIONAL','SUPPLEMENTARY','AI_GENERATED','USER_CREATED')),
  purpose TEXT,
  level TEXT DEFAULT 'N5',
  size_bytes INTEGER,
  page_count INTEGER,
  duration_seconds REAL,
  content_hash TEXT,
  processing_status TEXT NOT NULL DEFAULT 'pending' CHECK (processing_status IN
    ('pending','importing','extracting','normalizing','validating','verified','needs_review','failed','registered')),
  access_status TEXT CHECK (access_status IN
    ('local','accessible','requires_auth','manual_export','unreachable','unchecked')),
  checked_at TEXT,
  imported_at TEXT,
  record_count INTEGER DEFAULT 0,
  notes TEXT,
  error TEXT
);

-- RAW layer: immutable original content. Triggers below forbid UPDATE/DELETE.
CREATE TABLE IF NOT EXISTS raw_records (
  raw_id INTEGER PRIMARY KEY,
  source_id TEXT NOT NULL REFERENCES sources(source_id),
  locator TEXT NOT NULL,                  -- e.g. "row:12" or "page:3"
  content TEXT NOT NULL,
  content_hash TEXT NOT NULL,
  extraction_method TEXT NOT NULL,
  extracted_at TEXT NOT NULL,
  UNIQUE (source_id, locator, content_hash)
);
CREATE TRIGGER IF NOT EXISTS raw_no_update BEFORE UPDATE ON raw_records
BEGIN SELECT RAISE(ABORT, 'raw_records are immutable'); END;
CREATE TRIGGER IF NOT EXISTS raw_no_delete BEFORE DELETE ON raw_records
BEGIN SELECT RAISE(ABORT, 'raw_records are immutable'); END;

CREATE TABLE IF NOT EXISTS vocabulary (
  id TEXT PRIMARY KEY,                    -- VOC_000001
  word TEXT NOT NULL,                     -- front as written (kanji or kana)
  reading TEXT,                           -- kana reading
  romaji TEXT,
  han_viet TEXT,
  meaning_vi TEXT,
  part_of_speech TEXT,
  verb_group INTEGER CHECK (verb_group IN (1,2,3)),
  lesson_number INTEGER,
  deck TEXT,
  topic TEXT,                             -- JSON array
  example_jp TEXT,
  example_romaji TEXT,
  example_vi TEXT,
  level TEXT NOT NULL DEFAULT 'N5',
  source_ids TEXT NOT NULL DEFAULT '[]',  -- JSON array
  raw_ids TEXT NOT NULL DEFAULT '[]',     -- JSON array
  verification_status TEXT NOT NULL DEFAULT 'normalized' CHECK (verification_status IN
    ('raw','extracted','normalized','needs_review','verified','rejected')),
  review_notes TEXT,
  archived INTEGER NOT NULL DEFAULT 0,
  updated_at TEXT,
  dictionary_form TEXT,                   -- from JMdict; basis for verb_group
  verified_by TEXT                        -- NULL | ai (audit + dictionaries) | user | pending_user (edited, awaiting approval)
);
CREATE INDEX IF NOT EXISTS vocab_lesson ON vocabulary(lesson_number);
CREATE INDEX IF NOT EXISTS vocab_word ON vocabulary(word);

CREATE TABLE IF NOT EXISTS validation_issues (
  issue_id INTEGER PRIMARY KEY,
  entity_type TEXT NOT NULL,
  entity_id TEXT NOT NULL,
  code TEXT NOT NULL,
  severity TEXT NOT NULL CHECK (severity IN ('error','warning','info')),
  message TEXT NOT NULL,
  suggestion TEXT,                        -- AI/rule suggested fix, never auto-applied
  origin TEXT NOT NULL DEFAULT 'rule' CHECK (origin IN ('rule','ai_review','user')),
  resolved INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS issues_entity ON validation_issues(entity_type, entity_id);

CREATE TABLE IF NOT EXISTS review_actions (
  action_id INTEGER PRIMARY KEY,
  entity_type TEXT NOT NULL,
  entity_id TEXT NOT NULL,
  action TEXT NOT NULL,
  note TEXT,
  before_json TEXT,
  after_json TEXT,
  acted_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS srs_cards (
  card_id INTEGER PRIMARY KEY,
  entity_type TEXT NOT NULL,
  entity_id TEXT NOT NULL,
  direction TEXT NOT NULL CHECK (direction IN ('jp_vi','vi_jp')),
  status TEXT NOT NULL DEFAULT 'new',
  ease REAL NOT NULL DEFAULT 2.5,
  interval_days REAL NOT NULL DEFAULT 0,
  reps INTEGER NOT NULL DEFAULT 0,        -- consecutive successful reviews
  lapses INTEGER NOT NULL DEFAULT 0,
  review_count INTEGER NOT NULL DEFAULT 0,
  correct_count INTEGER NOT NULL DEFAULT 0,
  incorrect_count INTEGER NOT NULL DEFAULT 0,
  first_studied TEXT,
  last_studied TEXT,
  due_at TEXT,
  UNIQUE (entity_type, entity_id, direction)
);

CREATE TABLE IF NOT EXISTS review_log (
  log_id INTEGER PRIMARY KEY,
  card_id INTEGER NOT NULL REFERENCES srs_cards(card_id),
  rating TEXT NOT NULL,
  reviewed_at TEXT NOT NULL,
  prev_interval REAL,
  new_interval REAL
);

CREATE TABLE IF NOT EXISTS assets (
  asset_id TEXT PRIMARY KEY,              -- AUD_000001 / IMG_...
  source_id TEXT REFERENCES sources(source_id),
  kind TEXT NOT NULL CHECK (kind IN ('audio','image','document')),
  file_path TEXT NOT NULL,                -- relative to project root
  mime_type TEXT,
  duration_seconds REAL,
  page_number INTEGER,
  transcript_status TEXT,
  notes TEXT
);

CREATE TABLE IF NOT EXISTS exams (
  exam_id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  level TEXT NOT NULL,
  exam_type TEXT NOT NULL,
  source_type TEXT NOT NULL,
  is_official INTEGER NOT NULL,
  duration_minutes INTEGER,
  data_json TEXT NOT NULL,                -- sections, mondai, timing notes, as transcribed
  source_ids TEXT NOT NULL DEFAULT '[]',
  verification_status TEXT NOT NULL DEFAULT 'needs_review'
);

CREATE TABLE IF NOT EXISTS grammar (
  id TEXT PRIMARY KEY,                    -- GRA_000001
  pattern TEXT NOT NULL,
  lesson_number INTEGER,                  -- Minna lesson; NULL = N5 point outside Minna 1–25
  grammar_name_vi TEXT,
  meaning_vi TEXT NOT NULL,
  formation TEXT NOT NULL,
  explanation_vi TEXT,
  data_json TEXT NOT NULL,                -- usage, restrictions, formality, similar_patterns, common_mistakes,
                                          -- examples, handbook_refs, handbook_errors, level_note
  origin TEXT NOT NULL,                   -- handbook | handbook+ai | ai
  level TEXT NOT NULL DEFAULT 'N5',
  source_ids TEXT NOT NULL DEFAULT '[]',
  verification_status TEXT NOT NULL DEFAULT 'needs_review' CHECK (verification_status IN
    ('raw','extracted','normalized','needs_review','verified','rejected')),
  verified_by TEXT,
  review_notes TEXT
);

CREATE TABLE IF NOT EXISTS kanji (
  id TEXT PRIMARY KEY,                    -- KAN_000001
  kanji TEXT NOT NULL UNIQUE,
  han_viet TEXT,
  meaning_vi TEXT NOT NULL,
  onyomi TEXT NOT NULL DEFAULT '[]',
  kunyomi TEXT NOT NULL DEFAULT '[]',
  stroke_count INTEGER,
  example_words TEXT NOT NULL DEFAULT '[]',
  level TEXT NOT NULL DEFAULT 'N5',
  source_ids TEXT NOT NULL DEFAULT '[]',
  verification_status TEXT NOT NULL DEFAULT 'needs_review' CHECK (verification_status IN
    ('raw','extracted','normalized','needs_review','verified','rejected')),
  verified_by TEXT,
  review_notes TEXT
);

CREATE TABLE IF NOT EXISTS number_categories (   -- numbers/counters/dates topic (ADR-029)
  key TEXT PRIMARY KEY,                   -- hon, nichi, gatsu…
  position INTEGER NOT NULL,
  title_vi TEXT NOT NULL,
  rule_vi TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS numbers (
  id TEXT PRIMARY KEY,                    -- NUM_hon_三本 / NUM_hon_nan
  category TEXT NOT NULL,
  position INTEGER NOT NULL,              -- file order (category, then item)
  jp TEXT NOT NULL,
  reading TEXT NOT NULL,
  romaji TEXT,
  meaning_vi TEXT NOT NULL,
  irregular INTEGER NOT NULL DEFAULT 0,   -- 1 = special/sound-changed form to memorise; only these get SRS cards
  data_json TEXT NOT NULL,                -- alt_readings, note_vi, example_jp, example_vi, review_log
  verification_status TEXT NOT NULL DEFAULT 'needs_review' CHECK (verification_status IN
    ('raw','extracted','normalized','needs_review','verified','rejected')),
  verified_by TEXT,
  review_notes TEXT
);

CREATE TABLE IF NOT EXISTS kaiwa (        -- supplementary conversations (spec §7.4, ADR-023); never exam content
  id TEXT PRIMARY KEY,                    -- KAI_001
  topic TEXT NOT NULL,
  title_vi TEXT NOT NULL,
  situation_vi TEXT,
  data_json TEXT NOT NULL,                -- lines [{speaker, jp, hiragana, vi}], vocab refs, grammar refs, review_log
  origin TEXT NOT NULL DEFAULT 'ai',
  level TEXT NOT NULL DEFAULT 'N5',
  source_ids TEXT NOT NULL DEFAULT '[]',
  verification_status TEXT NOT NULL DEFAULT 'needs_review' CHECK (verification_status IN
    ('raw','extracted','normalized','needs_review','verified','rejected')),
  verified_by TEXT,
  review_notes TEXT
);

CREATE TABLE IF NOT EXISTS passages (
  passage_id TEXT PRIMARY KEY,
  exam_id TEXT REFERENCES exams(exam_id),
  text TEXT NOT NULL,
  source_page INTEGER,
  image_asset_id TEXT REFERENCES assets(asset_id)
);

CREATE TABLE IF NOT EXISTS questions (
  question_id TEXT PRIMARY KEY,
  exam_id TEXT REFERENCES exams(exam_id),
  section TEXT NOT NULL,
  section_id TEXT,
  mondai_no INTEGER,
  mondai_type TEXT,
  number INTEGER,
  question_text TEXT,
  instruction TEXT,
  passage_id TEXT REFERENCES passages(passage_id),
  options TEXT NOT NULL,                  -- JSON [{option_id, text, image_asset_id?}]
  correct_answer TEXT NOT NULL,           -- JSON ["4"]
  answer_type TEXT NOT NULL DEFAULT 'single_choice',
  extra_json TEXT,                        -- ordering data, flags (options_audio_only, ...)
  explanation_vi TEXT,
  explanation_origin TEXT,                -- AI_GENERATED | USER_CREATED | OFFICIAL
  audio_asset_id TEXT REFERENCES assets(asset_id),
  image_asset_id TEXT REFERENCES assets(asset_id),
  transcript TEXT,
  level TEXT NOT NULL DEFAULT 'N5',
  source_ids TEXT NOT NULL DEFAULT '[]',
  source_page INTEGER,
  extraction_method TEXT,
  verification_status TEXT NOT NULL DEFAULT 'needs_review' CHECK (verification_status IN
    ('raw','extracted','normalized','needs_review','verified','rejected')),
  review_notes TEXT
);

-- Mock exam engine (spec Part 9). An attempt freezes its question list and section timing at start.
CREATE TABLE IF NOT EXISTS exam_attempts (
  attempt_id TEXT PRIMARY KEY,            -- ATT_20261114_153000_ab12
  exam_id TEXT,                           -- NULL for practice sets built from the question bank
  title TEXT NOT NULL,
  mode TEXT NOT NULL CHECK (mode IN ('exam','practice')),
  config_json TEXT NOT NULL,              -- {filter, sections:[{section_id,name,section,duration_sec|null,question_ids}]}
  current_section INTEGER NOT NULL DEFAULT 0,
  section_started_at TEXT,
  started_at TEXT NOT NULL,
  submitted_at TEXT,
  result_json TEXT
);
CREATE TABLE IF NOT EXISTS attempt_answers (
  attempt_id TEXT NOT NULL REFERENCES exam_attempts(attempt_id),
  question_id TEXT NOT NULL,
  answer TEXT,                            -- JSON list of option_ids; NULL = not answered
  flagged INTEGER NOT NULL DEFAULT 0,
  is_correct INTEGER,
  answered_at TEXT,
  PRIMARY KEY (attempt_id, question_id)
);
CREATE TABLE IF NOT EXISTS settings (     -- learner preferences, e.g. daily_goal (ADR-022)
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);
"""


def connect(path: Path | str = DEFAULT_DB) -> sqlite3.Connection:
    if str(path) != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    migrate(conn)
    return conn


def migrate(conn: sqlite3.Connection) -> None:
    """Create missing tables/columns; safe on any older database (also run after a restore)."""
    conn.executescript(SCHEMA)
    for table, column in (("vocabulary", "dictionary_form TEXT"), ("vocabulary", "verified_by TEXT"),
                          ("questions", "verified_by TEXT"),
                          ("srs_cards", "weak_cleared_at TEXT")):   # cram "Nhớ" after the last miss (ADR-027)       # databases created before these columns
        if column.split()[0] not in {r[1] for r in conn.execute(f"PRAGMA table_info({table})")}:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {column}")
