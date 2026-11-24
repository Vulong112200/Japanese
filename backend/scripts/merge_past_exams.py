"""Past papers (ADR-019): merge transcription + community key + 2 independent AI solutions + reviewer decisions
-> data/normalized/exams/EXAM_N5_<id>.json and .ai_review.json. Prints every disagreement and transcription issue.

Inputs live in data/raw/PAST_EXAM_WORK/ (local only, never committed): EXAM_N5_<id>.json (transcription),
solve_A_/solve_B_EXAM_N5_<id>.json (AI solvers), keys.json (community keys), review.json (final decisions).
Workflow: docs/PAST_EXAMS.md.  Usage: .venv/Scripts/python -X utf8 scripts/merge_past_exams.py [ids...]"""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
S = ROOT / "data" / "raw" / "PAST_EXAM_WORK"
OUT = ROOT / "data" / "normalized" / "exams"
KEYS = json.loads((S / "keys.json").read_text())
OLD, NEW = (25, 50, 30), (20, 40, 30)     # JLPT N5 timing before / from 2020
EX = {
    "2024_07": dict(title="JLPT N5 2024年7月 (đề thật, bản cộng đồng JLPT Mogi)", audio="audio.mp3", seikai="seikai.pdf",
                    script="script.pdf", timing=NEW, key_note="Đáp án Yuuki Bùi (PDF) + 正解 trong script nghe"),
    "2021_12": dict(title="JLPT N5 2021年12月 (đề thật, bản cộng đồng Mark)", audio="audio.mp3", seikai="seikai.pdf",
                    script="script.pdf", timing=NEW, key_note="Đáp án Yuuki Bùi (PDF) + script nghe"),
    "2018": dict(title="JLPT N5 2018年 (đề thật, bản 荒木日语)", audio="audio.m4a", timing=OLD),
    "2017_07": dict(title="JLPT N5 2017年7月 (đề thật, bản 荒木日语)", audio="audio.m4a", timing=OLD),
    "2013_07": dict(title="JLPT N5 2013年7月 (đề thật, bản 荒木日语)", audio="audio.mp3", timing=OLD),
    "2012_12": dict(title="JLPT N5 2012年12月 (đề thật, bản quét)", audio="audio.m4a", timing=OLD),
}
# Listening-only papers rebuilt from YouTube videos (ADR-034): key = answer shown in the video. Titles: YT_TITLES.
YT = dict(audio="audio.m4a", timing=(30,), exam_type="video_practice", source_type="VIDEO_KEY", key_origin="video_answer",
          key_note="Đáp án công bố trong video YouTube, đối chiếu 2 AI giải độc lập (ADR-034)")
YT_TITLES = {   # the year is what the video says; content is not verifiable against an official paper
    "YT_2025_12": "Đề nghe N5 · video ghi JLPT 2025年12月 (dựng lại từ YouTube)",
    "YT_2025_07": "Đề nghe N5 · video ghi JLPT 2025年7月 (dựng lại từ YouTube)",
    "YT_2017_12": "Đề nghe N5 · video ghi JLPT 2017年12月 (dựng lại từ YouTube)",
    "YT_2016_12": "Đề nghe kiểu 4級 cũ · 12 câu 問題1–2 (video ghi 2016年12月, dựng lại từ YouTube)",
    "YT_2015_12": "Đề luyện nghe N5 · video ghi 2015年12月, nội dung giống đề luyện (dựng lại từ YouTube)",
    "YT_2015_07": "Đề nghe N5 · video ghi JLPT 2015年7月 (dựng lại từ YouTube)",
}
EX.update({k: dict(YT, title=t, sid=f"SRC_YT_N5_{k[3:]}") for k, t in YT_TITLES.items()})
# Final reviewer decisions: {qid: {"seikai": n, "note": "...", "patch": {field: value}}}
REVIEW = json.loads((S / "review.json").read_text(encoding="utf-8")) if (S / "review.json").exists() else {}

SEC = {"SEC_01": "vocabulary", "SEC_02": "grammar_reading", "SEC_03": "listening"}


def tail(qid):
    return re.search(r"(V\d+|G\d+|L\d_\d+)$", qid).group(1)


def key_for(keys, q):
    t = tail(q["question_id"])
    try:
        if t[0] == "V":
            return keys["vocabulary"][int(t[1:]) - 1]
        if t[0] == "G":
            return keys["grammar_reading"][int(t[1:]) - 1]
        m, n = t[1:].split("_")
        return keys["listening"][m][int(n) - 1]
    except (KeyError, IndexError):
        return None


def merge(eid):
    cfg = EX[eid]
    sid = cfg.get("sid") or f"SRC_DRIVE_EXAM_N5_{eid}"
    d = json.loads((S / f"EXAM_N5_{eid}.json").read_text(encoding="utf-8"))
    A = json.loads((S / f"solve_A_EXAM_N5_{eid}.json").read_text(encoding="utf-8"))
    B = json.loads((S / f"solve_B_EXAM_N5_{eid}.json").read_text(encoding="utf-8"))
    keys = KEYS.get(sid, {})
    lost = lambda q: q.get("options_missing") or REVIEW.get(q["question_id"], {}).get("drop")
    dropped = [q["question_id"] for q in d["questions"] if lost(q)]
    d["questions"] = [q for q in d["questions"] if not lost(q)]    # page lost: not usable
    review, by_no = {}, {"vocabulary": {}, "grammar_reading": {}, "listening": {}}
    n_key = n_ok = 0
    for q in d["questions"]:
        qid = q["question_id"]
        r = REVIEW.get(qid, {})
        q.update(r.get("patch", {}))
        a, b = A.get(qid, {}), B.get(qid, {})
        k = key_for(keys, q)
        n_key += k is not None
        sa, sb = a.get("answer"), b.get("answer")
        seikai = r.get("seikai") or k or (sa if sa == sb else None) or sa
        q["seikai"] = seikai
        if a.get("expected_sequence") and q.get("answer_type") == "sentence_ordering":
            q["expected_sequence"] = a["expected_sequence"]
            q["expected_sequence_note"] = "Thứ tự đầy đủ do AI suy luận; đáp án chỉ cho vị trí ★."
        notes = []
        if k is None:
            notes.append("Không có đáp án cộng đồng cho câu này: đáp án theo 2 AI giải độc lập.")
        if r.get("note"):
            notes.append(r["note"])
            q["review_notes"] = " ".join(x for x in (q.get("review_notes"), "Người duyệt: " + r["note"]) if x)
        if b.get("transcription_issue") and not r.get("patch"):
            notes.append("Soát bản chép (AI B): " + b["transcription_issue"])
        review[qid] = {"solver_a": sa, "solver_b": sb, "key": k, "explanation_vi": a.get("explanation_vi"),
                       "option_explanations": a.get("option_explanations"),
                       "verdict_note": " ".join(notes) or None}
        ok = sa == sb == seikai
        n_ok += ok
        if not ok or b.get("transcription_issue"):
            print(f"  {qid}: key={k} A={sa}({a.get('confidence')}) B={sb}({b.get('confidence')}) -> {seikai}"
                  f"{' | TI: ' + b['transcription_issue'] if b.get('transcription_issue') else ''}"
                  f"{' | reviewed' if r else ''}")
        sec, t = SEC[q["section_id"]], tail(qid)
        if sec == "listening":
            m, n = t[1:].split("_")
            by_no["listening"].setdefault(m, {})[int(n)] = seikai
        else:
            by_no[sec][int(t[1:])] = seikai
    # answer_key is positional by printed number (importer rebuilds ids from it): gaps (lost pages) stay null
    pos = lambda m: [m.get(i) for i in range(1, max(m, default=0) + 1)]
    lists = {"vocabulary": pos(by_no["vocabulary"]), "grammar_reading": pos(by_no["grammar_reading"]),
             "listening": {m: pos(v) for m, v in by_no["listening"].items()}}
    if dropped:
        print(f"  bỏ {dropped} (mất trang lựa chọn)")
    for s, dur in zip(d["sections"], cfg["timing"]):
        s["duration_minutes"] = dur
    has_key = n_key > 0
    files = {"dir": f"data/raw/{sid}", "mondai": "mondai.pdf", "audio": cfg["audio"], "audio_asset_id": f"AUD_{eid}_001"}
    files.update({k: cfg[k] for k in ("seikai", "script") if cfg.get(k)})
    d.update(exam_id=f"EXAM_N5_{eid}", title=cfg["title"], level="N5", exam_type=cfg.get("exam_type", "past_exam"),
             source_type=cfg.get("source_type") or ("COMMUNITY_KEY" if has_key else "AI_ANSWERED"), is_official=False,
             key_origin=cfg.get("key_origin") or ("community" if has_key else "ai_consensus"), duration_minutes=sum(cfg["timing"]),
             question_id_prefix=f"Q_{eid}", files=files, answer_key={**lists, "source": keys.get("page") or cfg.get("key_note") or "2 AI giải độc lập"},
             source_ids=[sid] + [f"{sid}_KEY"] * bool(cfg.get("seikai")) + [f"{sid}_SCRIPT"] * bool(cfg.get("script")) + [f"{sid}_AUDIO"],
             transcription={"method": "ai_vision_transcription", "note": d.pop("transcription_notes", None),
                            "key_note": cfg.get("key_note") if cfg.get("exam_type") else
                            "Đáp án cộng đồng (không phải 正解 chính thức), đối chiếu với 2 AI giải độc lập (ADR-019)."})
    (OUT / f"EXAM_N5_{eid}.json").write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    (OUT / f"EXAM_N5_{eid}.ai_review.json").write_text(json.dumps(review, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{eid}: {len(d['questions'])} câu, có key {n_key}, key=A=B {n_ok}")


for eid in sys.argv[1:] or [e for e in EX if (S / f"EXAM_N5_{e}.json").exists()]:
    merge(eid)
