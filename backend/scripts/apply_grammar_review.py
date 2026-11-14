"""Apply a grammar review round to data/normalized/grammar/grammar.json and mark entries audited.

Review files: JSON arrays of {"id", "field", "new_value", "reason_vi", "confidence"} (one element per corrected
top-level field; see CLAUDE.md §6). Usage:
    python scripts/apply_grammar_review.py review1.json review2.json [--reject GRA_000001:examples ...]
Every change is kept in the entry's review_log (old value + reason). Run `python -m hub import` afterwards.
"""
import json
import sys
from pathlib import Path

GRAMMAR = Path(__file__).resolve().parents[2] / "data" / "normalized" / "grammar" / "grammar.json"
ALLOWED = {"pattern", "grammar_name_vi", "meaning_vi", "formation", "explanation_vi", "usage", "restrictions", "formality",
           "similar_patterns", "common_mistakes", "examples", "handbook_errors", "lesson_number", "level_note"}


def main(argv: list[str]) -> None:
    reject = set(argv[argv.index("--reject") + 1:]) if "--reject" in argv else set()
    files = argv[:argv.index("--reject")] if "--reject" in argv else argv
    doc = json.loads(GRAMMAR.read_text(encoding="utf-8"))
    by = {g["id"]: g for g in doc["entries"]}
    applied, skipped = 0, []
    for f in [x for path in files for x in json.loads(Path(path).read_text(encoding="utf-8"))]:
        g, tag = by.get(f["id"]), f"{f['id']}:{f['field']}"
        if g is None or f["field"] not in ALLOWED or tag in reject:
            skipped.append(tag)
            continue
        g.setdefault("review_log", []).append({"field": f["field"], "old_value": g.get(f["field"]),
                                               "reason_vi": f["reason_vi"], "confidence": f.get("confidence")})
        g[f["field"]] = f["new_value"]
        applied += 1
    for g in doc["entries"]:
        g["audited"] = True
    GRAMMAR.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
    print("applied", applied, "skipped", skipped)


if __name__ == "__main__":
    main(sys.argv[1:])
