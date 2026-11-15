"""Per-question audio timestamps for listening questions (ADR-025).

Each exam has one audio track for the whole listening section. Whisper ASR segments (data/raw/PAST_EXAM_WORK/asr/,
local only) are aligned, in order, with each question's paper-script transcript: a question starts where the ASR text
best matches the opening of its transcript and ends where the next question (or the next 問題) starts. A question that
fails a check gets no timestamp (the learner still has the full track).
Output: data/normalized/exams/listening_timestamps.json (numbers only, no exam content).
Usage: .venv/Scripts/python -X utf8 scripts/listening_timestamps.py"""
import json, re, sys
from difflib import SequenceMatcher
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
from hub.validation.kana import kata_to_hira  # noqa: E402

ASR = ROOT / "data" / "raw" / "PAST_EXAM_WORK" / "asr"
EXAMS = ROOT / "data" / "normalized" / "exams"
OUT = EXAMS / "listening_timestamps.json"
HEAD, MIN_HEAD, MIN_BODY, MIN_LEN, MAX_LEN = 40, 0.5, 0.45, 5.0, 150.0
_MARK = re.compile(r"^(\d+|[一二三四五六七八九十]+)番$")
_MARK_END = re.compile(r"[^\d一二三四五六七八九十](\d|一)番$")
_MONDAI = re.compile(r"問題\s*[1-4１-４一二三四]")


def norm(text: str) -> str:
    """Only kana/kanji, katakana folded to hiragana, speaker labels dropped: what ASR and paper script share."""
    text = re.sub(r"(?m)^[^\n：:]{1,4}[：:]", "", text or "")
    return re.sub(r"[^ぁ-ゖー一-鿿]", "", kata_to_hira(text))


def _ratio(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b, autojunk=False).ratio()


def _best(head: str, texts: list[str], lo: int, hi: int, used: set) -> tuple[float, int | None]:
    best = (0.0, None)
    for i in range(max(0, lo), min(hi, len(texts))):
        if i not in used and len(texts[i]) > 1:     # a bare "N番" is never the opening
            r = _ratio(head, "".join(texts[i:i + 6])[:len(head) + 1])
            if r > best[0] + 1e-9:
                best = (r, i)
    return best


def align(questions: list[dict], segs: list[dict], duration: float) -> dict:
    """questions: [{question_id, mondai_no, transcript}] in paper order; segs: [{start, end, text}] (ASR) ->
    {qid: {start, end, score, coverage}}. Pure function; questions failing a check are left out."""
    texts = [norm(s["text"]) for s in segs]
    hits, used, cursor, m_no, m_start = [], set(), 0, object(), 0
    for q in questions:
        if q.get("mondai_no") != m_no:
            m_no, m_start = q.get("mondai_no"), cursor
        head = norm(q["transcript"])[:HEAD]
        score, i = _best(head, texts, cursor, cursor + 60, used)
        if score < MIN_HEAD:        # the paper can order items differently from the audio: search the whole mondai
            score, i = _best(head, texts, m_start, m_start + 200, used)
        if i is None or score < MIN_HEAD:
            continue
        used.update(range(i - 1, i + 3))
        cursor = max(cursor, i + 1)
        start = max(segs[i - 1]["end"] if i else 0.0, segs[i]["start"] - 1.0)
        for j in range(i - 1, max(m_start, i - 4) - 1, -1):     # the spoken "N番" just before (scene may come between)
            t = segs[j]["text"].strip().replace(" ", "").rstrip("。.")
            if _MARK.match(t):
                start = segs[j]["start"] - 0.3
                break
            if _MARK_END.search(t):                              # glued to the end of the previous segment
                start = segs[j]["end"] - 1.5
                break
        hits.append((max(0.0, start), i, q, score))
    hits.sort(key=lambda h: h[0])
    audio_end = min(duration, segs[-1]["end"] + 3) if segs else duration
    out = {}
    for k, (start, i, q, score) in enumerate(hits):
        nxt = hits[k + 1] if k + 1 < len(hits) else None
        end = nxt[0] if nxt else audio_end
        for j in range(i + 1, nxt[1] if nxt else len(segs)):        # next 問題 intro ends this question earlier
            if _MONDAI.search(segs[j]["text"]) and "用紙" not in segs[j]["text"]:
                end = min(end, segs[j]["start"])
                break
        body = "".join(norm(s["text"]) for s in segs if start - 1 <= s["start"] < end)
        full = norm(q["transcript"])
        coverage = sum(b.size for b in SequenceMatcher(None, full, body, autojunk=False).get_matching_blocks()) / max(
            1, len(full))
        # ponytail: coverage compares surface text, so an ASR that writes kana where the script has kanji scores low;
        # a strong opening match then suffices. Upgrade: compare readings (needs a tokenizer).
        if MIN_LEN <= end - start <= MAX_LEN and (coverage >= MIN_BODY or (score >= 0.65 and coverage >= 0.15)):
            out[q["question_id"]] = {"start": round(start, 1), "end": round(end, 1),
                                     "score": round(score, 2), "coverage": round(coverage, 2)}
    return out


def main() -> None:
    from hub.ingestion.pipeline import _exam_files, audio_duration, source_id_for
    result, report = {}, []
    for f in sorted(EXAMS.glob("EXAM_N5_*.json")):
        if f.name.endswith(".ai_review.json"):
            continue
        data = json.loads(f.read_text(encoding="utf-8"))
        exam_dir, files = _exam_files(data)
        audio = exam_dir / files["audio"]
        sid = source_id_for(audio)
        asr = next((p for p in (ASR / f"{sid}.json", ASR / f"{sid.removesuffix('_AUDIO')}.json") if p.exists()),
                   ASR / f"{sid}.json")
        if not asr.exists() or not audio.exists():
            report.append(f"{data['exam_id']}: bỏ qua (thiếu ASR hoặc audio)")
            continue
        sec = {s["section_id"] for s in data["sections"] if s["section"] == "listening"}
        qs = sorted((q for q in data["questions"] if q["section_id"] in sec and q.get("transcript")),
                    key=lambda q: (q["mondai_no"], q["number"]))
        got = align(qs, json.loads(asr.read_text(encoding="utf-8")), audio_duration(audio) or 1e9)
        result.update(got)
        miss = [q["question_id"] for q in qs if q["question_id"] not in got]
        report.append(f"{data['exam_id']}: {len(got)}/{len(qs)} câu có mốc" + (f"; thiếu: {', '.join(miss)}" if miss else ""))
    OUT.write_text(json.dumps({"method": "Whisper large-v3-turbo segments aligned to paper script (difflib); "
                                         "scripts/listening_timestamps.py, ADR-025",
                               "questions": result}, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\n".join(report))


if __name__ == "__main__":
    main()
