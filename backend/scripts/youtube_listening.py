"""Listening papers rebuilt from YouTube videos (ADR-034), local use only: everything lands in data/raw (never committed).

  download <sid> <url>   video (<=720p) -> data/raw/<sid>/audio.m4a + video/video.mp4, video/source.json
                         (subfolders are not registered as sources by pipeline.inventory)
  frames <sid> [step]    one JPEG every `step` s (default 4), near-duplicates dropped -> data/raw/<sid>/frames/t0123.jpg
  pdf <sid> <t> [<t>...] chosen frames (seconds, as in frame names) -> data/raw/<sid>/mondai.pdf, page i = i-th frame
ASR: data/raw/PAST_EXAM_WORK/.venv/Scripts/python data/raw/PAST_EXAM_WORK/asr/run_asr.py data/raw <asr_out> <sid>
Usage: .venv/Scripts/python -X utf8 scripts/youtube_listening.py download SRC_YT_N5_2015_07 https://youtu.be/..."""
import json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
YTDLP = RAW / "PAST_EXAM_WORK" / ".venv" / "Scripts" / "yt-dlp.exe"


def download(sid: str, url: str) -> None:
    d, v = RAW / sid, RAW / sid / "video"
    v.mkdir(parents=True, exist_ok=True)
    if not (v / "video.mp4").exists():
        subprocess.run([str(YTDLP), "--js-runtimes", "node", "-f", "bv*[height<=720][ext=mp4]+ba[ext=m4a]/b[height<=720]",
                        "--merge-output-format", "mp4", "-o", str(v / "video.%(ext)s"), url], check=True)
    if not (d / "audio.m4a").exists():
        subprocess.run(["ffmpeg", "-v", "error", "-i", str(v / "video.mp4"), "-vn", "-c:a", "copy", str(d / "audio.m4a")],
                       check=True)
    meta = json.loads(subprocess.run([str(YTDLP), "--js-runtimes", "node", "-J", "--skip-download", url],
                                     capture_output=True, check=True).stdout)
    keep = ("id", "webpage_url", "title", "channel", "channel_url", "upload_date", "duration", "description", "chapters")
    (v / "source.json").write_text(json.dumps({k: meta.get(k) for k in keep}, ensure_ascii=False, indent=1), "utf-8")


def frames(sid: str, step: float = 4) -> None:
    from PIL import Image, ImageChops, ImageStat
    d = RAW / sid
    out = d / "frames"
    out.mkdir(exist_ok=True)
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                str(d / "video" / "video.mp4")], capture_output=True, text=True, check=True).stdout)
    prev, kept = None, 0
    t = 0.0
    while t < dur:
        target = out / f"t{int(t):04d}.jpg"
        if not target.exists():
            subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t), "-i", str(d / "video" / "video.mp4"), "-frames:v", "1",
                            "-vf", "scale=960:-1", "-q:v", "4", str(target)], check=True)
        img = Image.open(target).convert("L").resize((96, 54))
        # ponytail: mean-pixel diff dedupe; a slide change below 0.6 grey level (of 255) would be dropped
        if prev is not None and ImageStat.Stat(ImageChops.difference(img, prev)).mean[0] < 0.6:
            target.unlink()
        else:
            prev, kept = img, kept + 1
        t += step
    print(sid, f"{kept} frames kept of {int(dur // step) + 1}")


def pdf(sid: str, times: list[str]) -> None:
    import pymupdf
    d = RAW / sid
    doc = pymupdf.open()
    for t in times:
        img = d / "frames" / f"t{int(float(t)):04d}.jpg"
        with pymupdf.open(img) as im:
            rect = im[0].rect
            page = doc.new_page(width=rect.width, height=rect.height)
            page.insert_image(rect, filename=str(img))
    doc.save(d / "mondai.pdf")
    print(sid, f"mondai.pdf {len(times)} pages")


if __name__ == "__main__":
    cmd, sid, *rest = sys.argv[1:]
    {"download": lambda: download(sid, rest[0]), "frames": lambda: frames(sid, *map(float, rest)),
     "pdf": lambda: pdf(sid, rest)}[cmd]()
