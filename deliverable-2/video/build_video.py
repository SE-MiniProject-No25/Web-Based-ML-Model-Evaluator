"""Build the Sprint 2 demo video (about 2 minutes) from the captured frames and the narration script.

    python build_video.py                    # writes ../Sprint2_Demo.mp4
    python build_video.py --rate 1           # speak a little faster (SAPI rate -10..10)
    python build_video.py --voice David      # use another installed Windows voice

Inputs live next to this script: frames/ (screenshots of the real application, taken at 800x450 so every pixel
is real), downloaded_result.json (the file the Download Results button really saved) and the SEGMENTS below, which
hold the narration. The voice-over is made with the Windows speech engine; to use a human voice, record over the
silent video with --silent and replace the audio. Needs ffmpeg, ffprobe and Pillow.
"""

import argparse
import json
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
FRAMES = HERE / "frames"
OUT = HERE.parent / "Sprint2_Demo.mp4"
W, H, FPS = 1280, 720, 25
SHOT_W, SHOT_H, SHOT_X, SHOT_Y = 960, 540, 160, 58  # where a screenshot sits on the canvas (16:9, scaled 1.2x)
SCALE = SHOT_W / 800
PAD_SECONDS = 0.45  # silence after each segment

NAVY, DARK, TEAL, LIGHT, AMBER, WHITE, MUTED = (
    (18, 48, 59), (11, 31, 39), (21, 159, 139), (236, 245, 243), (255, 190, 60), (255, 255, 255), (160, 190, 196),
)  # fmt: skip
FONT_DIR = Path("C:/Windows/Fonts")


def font(size: int, bold=False, mono=False) -> ImageFont.FreeTypeFont:
    name = ("consolab.ttf" if bold else "consola.ttf") if mono else ("segoeuib.ttf" if bold else "segoeui.ttf")
    return ImageFont.truetype(str(FONT_DIR / name), size)


# --- the story: what is said and what is shown --------------------------------------------------------------------
# kind "shot": one or more screenshots (file, [highlight boxes in the 800x450 screenshot]); other kinds are slides.

SEGMENTS = [
    dict(id="title", kind="title", tag="",
         text="This is the Web-Based ML Model Evaluator. Upload a trained model and a dataset, and get standard "
              "metrics back, safely, in seconds."),
    dict(id="overview", kind="overview", tag="",
         text="Four simple steps: upload, configure, review, and results. A React interface talks to a FastAPI "
              "backend, and every model runs in its own isolated, time limited process."),
    dict(id="upload", kind="shot", tag="Step 1 of 4  ·  Upload",
         frames=[("01_upload.jpg", [(34, 160, 385, 340), (400, 160, 751, 340)])],
         text="Here a customer churn model and its dataset are chosen. Joblib and pickle models are supported, and "
              "files over ten megabytes are refused straight away."),
    dict(id="configure", kind="shot", tag="Step 2 of 4  ·  Configure",
         frames=[("02_configure.jpg", [(34, 295, 751, 325), (34, 245, 751, 282)])],
         text="The app reads the CSV header and lists the columns. We choose classification, and the column to "
              "predict: churned."),
    dict(id="review", kind="shot", tag="Step 3 of 4  ·  Review",
         frames=[("03_review.jpg", [(34, 160, 751, 300)])],
         text="Before anything is submitted, a review screen shows exactly what will be evaluated."),
    dict(id="results", kind="shot", tag="Step 4 of 4  ·  Results",
         frames=[("05_results_table.jpg", [(198, 38, 724, 224)])],
         text="The server answers at once and runs the evaluation in the background. Results arrive as a table, and "
              "every metric comes with a plain language explanation, including which direction is good."),
    dict(id="chart", kind="shot", tag="Step 4 of 4  ·  Results",
         frames=[("06_chart_download.jpg", [(318, 276, 467, 317)])],
         text="A chart shows the scores, and Download Results saves the full result as a file."),
    dict(id="file", kind="file", tag="",
         text="The file holds the evaluation ID, the inputs, every metric, and the timestamps."),
    dict(id="variety", kind="shot", tag="Different models, different metrics",
         frames=[("07_iris_3class.jpg", []), ("08_house_regression.jpg", [(54, 88, 731, 262)]),
                 ("09_cancer_pipeline.jpg", [])],
         text="The same screen handles a three class model, a regression model with M A E, M S E, R M S E and "
              "R squared, and a scikit-learn pipeline on a real dataset."),
    dict(id="reject_csv", kind="shot", tag="Bad input is stopped early",
         frames=[("10_reject_malformed_csv.jpg", [(419, 314, 731, 364)])],
         text="Bad input is stopped before any model runs. A malformed CSV is rejected, and the message appears "
              "next to the field that needs fixing."),
    dict(id="failed", kind="shot", tag="A clear reason when it fails",
         frames=[("11_failed_evaluation.jpg", [(52, 288, 733, 326)])],
         text="If the data does not fit the model, the evaluation fails with a clear reason. Here the wrong target "
              "column was chosen, and the exact columns are named."),
    dict(id="security", kind="shot", tag="Security first",
         frames=[("12_reject_corrupt_model.jpg", [(53, 314, 304, 350)]),
                 ("13_reject_unsupported_file.jpg", [(34, 324, 751, 359)])],
         text="Security comes first. Corrupt model files and unsupported file types are rejected, and a model only "
              "ever runs in a separate process, with a time limit."),
    dict(id="docs", kind="shot", tag="A documented API",
         frames=[("14_api_docs_top.jpg", [(25, 328, 740, 412)]), ("15_api_docs_endpoints.jpg", [(28, 70, 757, 225)])],
         text="The API is fully documented, with optional API key authentication, and one safe error format "
              "everywhere."),
    dict(id="quality", kind="quality", tag="",
         text="Behind it are two hundred and eighty eight automated tests, ninety eight percent line coverage, and "
              "all twenty five test plan cases passing."),
    dict(id="closing", kind="closing", tag="",
         text="That is Sprint 2: a working, tested, documented product. Thank you for watching."),
]

QUALITY_TILES = [("288", "automated tests", "0 failed"), ("98.0%", "line coverage", "backend"),
                 ("95.5%", "branch coverage", "backend"), ("25 / 25", "test plan cases", "all pass")]  # fmt: skip


# --- drawing -------------------------------------------------------------------------------------------------------


def gradient() -> Image.Image:
    img = Image.new("RGB", (W, H), NAVY)
    px = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        px.line([(0, y), (W, y)], fill=tuple(int(NAVY[i] * (1 - t) + DARK[i] * t) for i in range(3)))
    return img


def centered(draw, text, y, f, fill=WHITE):
    draw.text(((W - draw.textlength(text, font=f)) / 2, y), text, font=f, fill=fill)


def slide_title() -> Image.Image:
    img, d = gradient(), None
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 10], fill=TEAL)
    centered(d, "Web-Based ML Model Evaluator", 220, font(76, bold=True))
    d.rectangle([(W - 160) / 2, 330, (W + 160) / 2, 336], fill=TEAL)
    centered(d, "Sprint 2 demo", 365, font(44), TEAL)
    centered(d, "Upload a model and a dataset. Get trusted metrics back.", 440, font(30), MUTED)
    centered(d, "Adyanth   ·   Akash   ·   Akshath   ·   Akshya", 620, font(28), MUTED)
    return img


def slide_overview() -> Image.Image:
    img = gradient()
    d = ImageDraw.Draw(img)
    centered(d, "How it works", 70, font(48, bold=True))
    steps = [("1", "Upload", "a model and a CSV"), ("2", "Configure", "task and target column"),
             ("3", "Review", "check before running"), ("4", "Results", "metrics and download")]  # fmt: skip
    box_w, gap = 250, 40
    x0 = (W - (4 * box_w + 3 * gap)) / 2
    for i, (n, title, sub) in enumerate(steps):
        x = x0 + i * (box_w + gap)
        d.rounded_rectangle([x, 190, x + box_w, 390], radius=22, fill=(24, 66, 80), outline=TEAL, width=3)
        d.ellipse([x + 20, 208, x + 76, 264], fill=TEAL)
        d.text((x + 48 - d.textlength(n, font=font(30, True)) / 2, 215), n, font=font(30, True), fill=WHITE)
        d.text((x + 24, 285), title, font=font(36, True), fill=WHITE)
        d.text((x + 24, 335), sub, font=font(22), fill=MUTED)
        if i < 3:
            d.text((x + box_w + 6, 262), "→", font=font(34, True), fill=AMBER)
    pills = ["React + Vite interface", "FastAPI backend", "scikit-learn models in an isolated process"]
    x = 130
    for p in pills:
        w = d.textlength(p, font=font(26)) + 44
        d.rounded_rectangle([x, 450, x + w, 500], radius=25, outline=TEAL, width=3)
        d.text((x + 22, 458), p, font=font(26), fill=WHITE)
        x += w + 20
    centered(d, "Optional API-key authentication   ·   one safe error format   ·   OpenAPI documentation", 545,
             font(26), MUTED)  # fmt: skip
    return img


def slide_file() -> Image.Image:
    data = json.loads((HERE / "downloaded_result.json").read_text())
    img = gradient()
    d = ImageDraw.Draw(img)
    centered(d, "Download Results saves this file", 34, font(36, bold=True))
    x, y, w, h = 170, 100, 940, 560
    d.rounded_rectangle([x, y, x + w, y + h], radius=16, fill=(15, 36, 45), outline=(60, 100, 112), width=2)
    d.rounded_rectangle([x, y, x + w, y + 46], radius=16, fill=(30, 66, 80))
    d.rectangle([x, y + 30, x + w, y + 46], fill=(30, 66, 80))
    for i, c in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        d.ellipse([x + 20 + i * 26, y + 15, x + 34 + i * 26, y + 29], fill=c)
    name = f"evaluation-{data['evaluation_id'][:8]}….json"
    d.text((x + 120, y + 9), name, font=font(22), fill=LIGHT)
    mono, lh = font(25, mono=True), 29
    lines = json.dumps(data, indent=2).split("\n")
    for i, line in enumerate(lines):
        stripped = line.lstrip()
        ind = len(line) - len(stripped)
        cx, cy = x + 28 + ind * 14.4, y + 62 + i * lh
        if stripped.startswith('"') and '": ' in stripped:
            key, _, val = stripped.partition(": ")
            d.text((cx, cy), key, font=mono, fill=(120, 210, 255))
            kx = cx + d.textlength(key + ": ", font=mono)
            colour = AMBER if val.startswith('"') else (170, 230, 150)
            d.text((kx, cy), val, font=mono, fill=colour)
        else:
            d.text((cx, cy), stripped, font=mono, fill=LIGHT)
    return img


def slide_quality() -> Image.Image:
    img = gradient()
    d = ImageDraw.Draw(img)
    centered(d, "Built and tested", 80, font(52, bold=True))
    tile_w, gap = 270, 30
    x0 = (W - (4 * tile_w + 3 * gap)) / 2
    for i, (big, label, small) in enumerate(QUALITY_TILES):
        x = x0 + i * (tile_w + gap)
        d.rounded_rectangle([x, 220, x + tile_w, 460], radius=22, fill=(24, 66, 80), outline=TEAL, width=3)
        f = font(64, bold=True)
        d.text((x + (tile_w - d.textlength(big, font=f)) / 2, 262), big, font=f, fill=TEAL)
        d.text((x + (tile_w - d.textlength(label, font=font(28))) / 2, 358), label, font=font(28), fill=WHITE)
        d.text((x + (tile_w - d.textlength(small, font=font(22))) / 2, 402), small, font=font(22), fill=MUTED)
    centered(d, "Checked on every pull request   ·   reports in the docs folder", 540, font(28), MUTED)
    return img


def slide_closing() -> Image.Image:
    img = gradient()
    d = ImageDraw.Draw(img)
    d.rectangle([0, H - 10, W, H], fill=TEAL)
    centered(d, "Sprint 2 complete", 250, font(72, bold=True))
    centered(d, "A working, tested, documented product", 350, font(36), TEAL)
    centered(d, "github.com/SE-MiniProject-No25/Web-Based-ML-Model-Evaluator", 520, font(26), MUTED)
    return img


def screenshot_frame(name: str, boxes, tag: str) -> Image.Image:
    img = Image.new("RGB", (W, H), NAVY)
    d = ImageDraw.Draw(img)
    shot = Image.open(FRAMES / name).convert("RGB").resize((SHOT_W, SHOT_H), Image.LANCZOS)
    shot = shot.filter(ImageFilter.UnsharpMask(radius=1.2, percent=70, threshold=2))
    mask = Image.new("L", shot.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, SHOT_W, SHOT_H], radius=14, fill=255)
    shadow = Image.new("RGB", (SHOT_W + 24, SHOT_H + 24), DARK)
    img.paste(shadow, (SHOT_X - 12, SHOT_Y - 4), Image.new("L", shadow.size, 120).filter(ImageFilter.GaussianBlur(10)))
    img.paste(shot, (SHOT_X, SHOT_Y), mask)
    for x0, y0, x1, y1 in boxes:  # callouts, given in the 800x450 coordinates of the screenshot
        d.rounded_rectangle([SHOT_X + x0 * SCALE - 6, SHOT_Y + y0 * SCALE - 6, SHOT_X + x1 * SCALE + 6,
                             SHOT_Y + y1 * SCALE + 6], radius=10, outline=AMBER, width=4)  # fmt: skip
    if tag:
        d.rounded_rectangle([SHOT_X, 14, SHOT_X + d.textlength(tag, font=font(26, True)) + 36, 52], radius=19, fill=TEAL)
        d.text((SHOT_X + 18, 15), tag, font=font(26, True), fill=WHITE)
    return img


def add_subtitle(img: Image.Image, lines: list[str], progress: float) -> Image.Image:
    img = img.copy()
    d = ImageDraw.Draw(img)
    f = font(29)
    top = H - 14 - 12 - len(lines) * 36
    d.rectangle([0, top - 8, W, H], fill=(8, 22, 28))
    for i, line in enumerate(lines):
        d.text(((W - d.textlength(line, font=f)) / 2, top + i * 36), line, font=f, fill=WHITE)
    d.rectangle([0, H - 6, int(W * progress), H], fill=TEAL)
    return img


# --- narration ---------------------------------------------------------------------------------------------------------


def wrap(text: str, max_width: int = 1180) -> list[str]:
    probe, f = ImageDraw.Draw(Image.new("RGB", (10, 10))), font(29)
    lines, line = [], ""
    for word in text.split():
        trial = f"{line} {word}".strip()
        if probe.textlength(trial, font=f) <= max_width:
            line = trial
        else:
            lines.append(line)
            line = word
    return lines + [line] if line else lines


def chunks(text: str) -> list[list[str]]:
    lines = wrap(text)
    return [lines[i : i + 2] for i in range(0, len(lines), 2)]


def spoken(text: str) -> str:
    return text.replace("M A E", "M.A.E.").replace("M S E", "M.S.E.").replace("R M S E", "R.M.S.E.")


def synthesize(texts: list[str], folder: Path, voice: str, rate: int) -> list[Path]:
    script = folder / "speak.ps1"
    jobs = [{"text": spoken(t), "out": str(folder / f"raw_{i:02d}.wav")} for i, t in enumerate(texts)]
    (folder / "jobs.json").write_text(json.dumps(jobs), encoding="utf-8")
    script.write_text(
        "Add-Type -AssemblyName System.Speech\n"
        f"$jobs = Get-Content -Raw -Encoding UTF8 '{folder / 'jobs.json'}' | ConvertFrom-Json\n"
        "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer\n"
        f"$s.SelectVoice('Microsoft {voice} Desktop')\n$s.Rate = {rate}\n"
        "foreach ($j in $jobs) { $s.SetOutputToWaveFile($j.out); $s.Speak($j.text); $s.SetOutputToNull() }\n",
        encoding="utf-8",
    )
    subprocess.run(["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script)], check=True)
    padded = []
    for i in range(len(texts)):
        raw, out = folder / f"raw_{i:02d}.wav", folder / f"seg_{i:02d}.wav"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(raw), "-ar", "44100", "-ac", "1", "-af",
                        f"apad=pad_dur={PAD_SECONDS}", str(out)], check=True)  # fmt: skip
        padded.append(out)
    return padded


def duration(path: Path) -> float:
    with wave.open(str(path)) as w:
        return w.getnframes() / w.getframerate()


def write_script_doc(lengths: list[float], path: Path) -> None:
    """The shot list and narration, with the time each scene starts, generated from the same data as the video."""
    nl = chr(10)
    rows, start = [], 0.0
    for number, (seg, length) in enumerate(zip(SEGMENTS, lengths, strict=True), start=1):
        shown = ", ".join(f"`{name}`" for name, _ in seg["frames"]) if seg["kind"] == "shot" else f"slide: {seg['kind']}"
        minutes, seconds = divmod(int(start), 60)
        rows.append(f"| {number} | {minutes}:{seconds:02d} | {length - PAD_SECONDS:.0f} s | {shown} | {seg['text']} |")
        start += length
    total_min, total_sec = divmod(int(start), 60)
    lines = [
        "# Sprint 2 demo video: shot list and narration",
        "",
        f"Total length {total_min}:{total_sec:02d}. This file is generated by `video/build_video.py` from the same data "
        "as the video, so the two cannot disagree. To use your own voice, build a silent version "
        "(`python build_video.py --silent`) and read the narration below over it.",
        "",
        "| # | Starts | Length | On screen | Narration |",
        "|---|---|---|---|---|",
        *rows,
        "",
        "Screenshots are in `video/frames/`; they were captured from the running application with the demo inputs "
        "in `demo-inputs/`. The file shown in scene 8 is the real file the Download Results button saved "
        "(`video/downloaded_result.json`).",
    ]
    path.write_text(nl.join(lines) + nl, encoding="utf-8")


# --- assembling ------------------------------------------------------------------------------------------------------------


def build(args) -> None:
    work = Path(tempfile.mkdtemp(prefix="demo-video-"))
    audio = synthesize([s["text"] for s in SEGMENTS], work, args.voice, args.rate)
    lengths = [duration(p) for p in audio]
    total = sum(lengths)
    print(f"narration: {total:.1f} s over {len(SEGMENTS)} segments")
    write_script_doc(lengths, HERE.parent / "Sprint2_Demo_Script.md")

    slides = {"title": slide_title, "overview": slide_overview, "file": slide_file, "quality": slide_quality,
              "closing": slide_closing}  # fmt: skip
    entries, elapsed, index = [], 0.0, 0
    for seg, length in zip(SEGMENTS, lengths, strict=True):
        speak_len = length - PAD_SECONDS
        subs = chunks(seg["text"])
        weights = [sum(len(x) for x in c) for c in subs]
        bounds_sub = [0.0]
        for wgt in weights:
            bounds_sub.append(bounds_sub[-1] + wgt / sum(weights))
        if seg["kind"] == "shot":
            n = len(seg["frames"])
            bounds_frame = [i / n for i in range(n + 1)]
            bases = [screenshot_frame(name, boxes, seg["tag"]) for name, boxes in seg["frames"]]
        else:
            bounds_frame, bases = [0.0, 1.0], [slides[seg["kind"]]()]
        cuts = sorted(set(bounds_sub + bounds_frame))
        for a, b in zip(cuts, cuts[1:], strict=False):
            mid = (a + b) / 2
            frame = bases[max(i for i in range(len(bases)) if bounds_frame[i] <= mid)]
            sub = subs[max(i for i in range(len(subs)) if bounds_sub[i] <= mid)]
            span = (b - a) * speak_len
            if b == cuts[-1]:
                span += PAD_SECONDS
            image = add_subtitle(frame, sub, (elapsed + (a + (b - a) / 2) * speak_len) / total)
            path = work / f"img_{index:03d}.png"
            image.save(path)
            entries.append((path, span))
            index += 1
        elapsed += length

    listing = work / "frames.txt"
    listing.write_text(
        "".join(f"file '{p.as_posix()}'\nduration {d:.4f}\n" for p, d in entries) + f"file '{entries[-1][0].as_posix()}'\n"
    )
    wavs = work / "audio.txt"
    wavs.write_text("".join(f"file '{p.as_posix()}'\n" for p in audio))
    joined = work / "audio.wav"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(wavs), "-c", "copy",
                    str(joined)], check=True)  # fmt: skip
    command = ["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(listing)]
    if not args.silent:
        command += ["-i", str(joined)]
    command += ["-vf", f"fps={FPS},fade=t=in:st=0:d=0.5,fade=t=out:st={total - 0.7:.2f}:d=0.7,format=yuv420p",
                "-c:v", "libx264", "-crf", "21", "-preset", "slow", "-movflags", "+faststart"]  # fmt: skip
    if not args.silent:
        command += ["-c:a", "aac", "-b:a", "128k", "-shortest"]
    command += [str(args.out)]
    subprocess.run(command, check=True)
    size = args.out.stat().st_size / 1e6
    print(f"wrote {args.out} ({size:.1f} MB, {total:.1f} s)")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--voice", default="Zira", help="installed Windows voice, e.g. Zira or David")
    parser.add_argument("--rate", type=int, default=0, help="speech rate, -10 (slow) to 10 (fast)")
    parser.add_argument("--silent", action="store_true", help="no voice-over, for recording your own")
    parser.add_argument("--out", type=Path, default=OUT)
    build(parser.parse_args())
    return 0


if __name__ == "__main__":
    sys.exit(main())
