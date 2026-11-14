"""OCR for scanned PDFs with Tesseract (jpn / jpn_vert / vie traineddata in data/reference/tessdata).

Tables (vocabulary lists) are OCR'd column by column: each column is cropped and read with the language
that fits it (Japanese for word/kana, Vietnamese for Hán-Việt/meaning); rows are re-assembled from the
line positions Tesseract reports. OCR output is RAW-layer material: it is never treated as verified.
"""
import csv
import io
import shutil
import subprocess
from pathlib import Path

from ..db import ROOT

TESSDATA = ROOT / "data" / "reference" / "tessdata"
TESSERACT = shutil.which("tesseract") or r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def available() -> bool:
    return Path(TESSERACT).exists() and (TESSDATA / "jpn.traineddata").exists()


def tesseract_tsv(png: bytes, lang: str, psm: int = 6) -> list[dict]:
    """Words with positions and confidence."""
    out = subprocess.run([TESSERACT, "stdin", "stdout", "--tessdata-dir", str(TESSDATA), "-l", lang,
                          "--psm", str(psm), "-c", "preserve_interword_spaces=1", "-c", "tessedit_create_tsv=1"],
                         input=png, capture_output=True, timeout=300)
    rows = list(csv.DictReader(io.StringIO(out.stdout.decode("utf-8", "replace")), delimiter="\t",
                               quoting=csv.QUOTE_NONE))
    return [r for r in rows if r.get("text", "").strip() and r.get("conf") not in (None, "-1")]


def lines(words: list[dict]) -> list[dict]:
    """Group words into lines: [{'top','bottom','text','conf'}] (Japanese words are joined without spaces)."""
    groups: dict[tuple, list[dict]] = {}
    for w in words:
        groups.setdefault((w["block_num"], w["par_num"], w["line_num"]), []).append(w)
    out = []
    for ws in groups.values():
        ws.sort(key=lambda w: int(w["left"]))
        text = ""
        for w in ws:
            t = w["text"]
            if text and not (_is_cjk(text[-1]) and _is_cjk(t[0])):
                text += " "
            text += t
        out.append({"top": min(int(w["top"]) for w in ws), "bottom": max(int(w["top"]) + int(w["height"]) for w in ws),
                    "text": text, "conf": round(sum(float(w["conf"]) for w in ws) / len(ws), 1)})
    return sorted(out, key=lambda l: l["top"])


def _is_cjk(ch: str) -> bool:
    return "\u3000" <= ch <= "\u9fff" or "\uff00" <= ch <= "\uffef"


def render(pdf: Path, page: int, dpi: int = 300, clip=None) -> bytes:
    import pymupdf
    with pymupdf.open(pdf) as d:
        p = d[page]
        rect = None
        if clip:
            r = p.rect
            rect = pymupdf.Rect(r.x0 + clip[0] * r.width, r.y0 + clip[1] * r.height,
                                r.x0 + clip[2] * r.width, r.y0 + clip[3] * r.height)
        png = p.get_pixmap(dpi=dpi, clip=rect, colorspace=pymupdf.csGRAY).tobytes("png")
    return remove_rules(png)


def remove_rules(png: bytes) -> bytes:
    """Whiten table rules (long dark horizontal/vertical runs) that make Tesseract hallucinate."""
    import numpy as np
    from PIL import Image
    img = np.array(Image.open(io.BytesIO(png)).convert("L"))
    dark = img < 210
    h, w = dark.shape
    rows = dark.sum(axis=1) > 0.5 * w
    cols = dark.sum(axis=0) > 0.5 * h
    for arr, axis in ((rows, 0), (cols, 1)):
        idx = np.where(arr)[0]
        for i in idx:
            lo, hi = max(i - 2, 0), i + 3
            if axis == 0:
                img[lo:hi, :] = 255
            else:
                img[:, lo:hi] = 255
    buf = io.BytesIO()
    Image.fromarray(img).save(buf, format="PNG")
    return buf.getvalue()


def ocr_table_page(pdf: Path, page: int, columns: list[tuple[float, float, str]], top=0.0, bottom=1.0,
                   dpi: int = 300) -> list[list[dict]]:
    """columns: [(x0_frac, x1_frac, lang)]. Returns rows; each row = one cell dict per column (or None)."""
    col_lines = []
    for x0, x1, lang in columns:
        col_lines.append(lines(tesseract_tsv(render(pdf, page, dpi, (x0, top, x1, bottom)), lang)))
    # row anchors come from the column with the most lines (normally the Japanese word column)
    anchor = max(range(len(columns)), key=lambda i: len(col_lines[i]))
    rows = []
    for a in col_lines[anchor]:
        mid = (a["top"] + a["bottom"]) / 2
        row = []
        for i, ls in enumerate(col_lines):
            cell = [l for l in ls if l["top"] - 25 <= mid <= l["bottom"] + 25]
            row.append({"text": " ".join(c["text"] for c in cell), "conf": min((c["conf"] for c in cell), default=0)}
                       if cell else None)
        rows.append(row)
    return rows


def ocr_page_text(pdf: Path, page: int, lang: str = "jpn+vie", psm: int = 6, dpi: int = 300) -> list[dict]:
    return lines(tesseract_tsv(render(pdf, page, dpi), lang, psm))
