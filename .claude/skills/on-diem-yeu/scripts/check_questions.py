"""Usage: backend/.venv/Scripts/python -X utf8 .claude/skills/on-diem-yeu/scripts/check_questions.py <file.json> ...
Runs the app's rule check_grammar_question (ADR-020) on authored entries: a JSON list, or a set file {entries: [...]}.
Prints each question with issues and 'questions with issues: N' (must be 0 before import)."""
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "backend"))
from hub.ingestion.knowledge import _past_keys, check_grammar_question  # noqa: E402

c = sqlite3.connect(f"file:{ROOT / 'data' / 'database' / 'hub.sqlite'}?mode=ro", uri=True)
grammar = {r[0] for r in c.execute("SELECT id FROM grammar WHERE verification_status='verified'")}
kanji = {r[0] for r in c.execute("SELECT kanji FROM kanji WHERE verification_status='verified'")}
past = _past_keys(c, "SELECT q.question_text FROM questions q JOIN exams e USING (exam_id) "
                     "WHERE e.exam_type IN ('past_exam','official_sample') AND q.question_text IS NOT NULL")
bad = 0
for path in sys.argv[1:]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    for q in data["entries"] if isinstance(data, dict) else data:
        issues = check_grammar_question(q, grammar, kanji, past)
        if issues:
            bad += 1
            print(q.get("question_id"), [(code, msg) for code, _, msg, _ in issues])
print("questions with issues:", bad)
