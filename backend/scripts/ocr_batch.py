"""One-off batch OCR of the Drive PDFs -> data/raw/SRC_LESSON_002/ocr/<name>.json (RAW layer).
Usage: python scripts/ocr_batch.py <name> [first_page] [last_page]"""
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from hub.ingestion import ocr  # noqa: E402

BASE = Path(__file__).resolve().parents[2] / "data" / "raw" / "SRC_LESSON_002"
LAYOUTS = {
    "Tong-hop-tu-vung-N5": {"kind": "table", "top": 0.03, "bottom": 0.955,
                            "columns": [(0.08, 0.155, "eng"), (0.155, 0.33, "jpn"), (0.33, 0.515, "jpn"),
                                        (0.515, 0.645, "vie"), (0.645, 0.93, "vie")],
                            "fields": ["no", "word", "kana", "han_viet", "meaning_vi"]},
    "Tu-vung-N5": {"kind": "table", "top": 0.10, "bottom": 0.95,
                   "columns": [(0.129, 0.321, "jpn"), (0.325, 0.461, "vie"), (0.465, 0.630, "jpn"), (0.634, 0.94, "vie")],
                   "fields": ["word", "han_viet", "kana", "meaning_vi"]},
    "120-Kanji-co-ban-so-cap": {"kind": "text", "lang": "jpn+eng", "psm": 4},
    "160-kanji-n5-n4": {"kind": "text", "lang": "jpn+vie", "psm": 11},
}


def run_page(name: str, page: int) -> dict:
    lay = LAYOUTS[name]
    pdf = BASE / f"{name}.pdf"
    if lay["kind"] == "table":
        rows = ocr.ocr_table_page(pdf, page, lay["columns"], lay["top"], lay["bottom"])
        return {"page": page + 1, "rows": [{f: (c["text"] if c else None) for f, c in zip(lay["fields"], r)}
                                           | {"min_conf": min((c["conf"] for c in r if c), default=0)} for r in rows]}
    return {"page": page + 1, "lines": ocr.ocr_page_text(pdf, page, lay["lang"], lay["psm"])}


def main():
    name = sys.argv[1]
    import pymupdf
    n = len(pymupdf.open(BASE / f"{name}.pdf"))
    first = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    last = int(sys.argv[3]) if len(sys.argv) > 3 else n
    t = time.time()
    with ThreadPoolExecutor(max_workers=4) as ex:
        pages = list(ex.map(lambda p: run_page(name, p), range(first, last)))
    out = BASE / "ocr"
    out.mkdir(exist_ok=True)
    (out / f"{name}.json").write_text(json.dumps({"source": f"{name}.pdf", "engine": "tesseract 5.4 tessdata_best",
                                                  "layout": LAYOUTS[name], "pages": pages},
                                                 ensure_ascii=False, indent=1), encoding="utf-8")
    print(name, len(pages), "pages", round(time.time() - t), "s")


if __name__ == "__main__":
    main()
