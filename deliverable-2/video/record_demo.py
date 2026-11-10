"""Record the Sprint 2 demo: a real browser using the real application, captured as video.

    python record_demo.py              # writes ../Sprint2_Demo.mp4

Needs the backend on http://localhost:8000 and the frontend on http://localhost:5173 (see the README), Playwright
(`pip install playwright`), Microsoft Edge, and ffmpeg. It drives Edge in the background, so it does not take over
the screen: files are chosen through the browser's own file chooser, buttons are clicked, and the page is scrolled,
at a human pace, with a visible cursor. The browser's own recording is converted to MP4 (H.264, 1280x720).

A browser recording only contains the page. The operating system's "Open" window and the list a drop-down menu
opens are drawn outside the page, so they would be invisible. While the real file chooser is open, the script
draws a picture of the Open window listing the real folder, and when it picks a menu option it draws the opened
list, so the viewer sees what a person would see. The file and the option are then set for real.
"""

import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
INPUTS = HERE.parent / "demo-inputs"
OUT = HERE.parent / "Sprint2_Demo.mp4"
APP, API = "http://localhost:5173", "http://localhost:8000"
W, H = 1280, 720
TARGET_SECONDS = 120

# Drawn into every page: a visible cursor, a ripple on every click, and the pictures of the Open window and of an
# opened drop-down list (see the module docstring).
PAGE_HELPERS = r"""
(() => {
  const css = `
    #__fd, #__dd { font-family: 'Segoe UI', system-ui, sans-serif; color: #1b1b1b; }
    #__fd .row:hover { background: #e5f3ff; }
    #__fd .row.sel { background: #cce8ff; }
    #__dd .opt:hover { background: #0078d4; color: #fff; }
  `;
  const add = () => {
    if (document.getElementById('__demo_cursor')) return;
    const style = document.createElement('style');
    style.textContent = css;
    document.documentElement.appendChild(style);
    const c = document.createElement('div');
    c.id = '__demo_cursor';
    c.innerHTML = '<svg width="26" height="26" viewBox="0 0 24 24"><path d="M4 2 L4 19 L8.5 14.8 L11.6 21.5 L14.4 20.3 L11.3 13.6 L17.5 13.6 Z" fill="#111" stroke="#fff" stroke-width="1.6" stroke-linejoin="round"/></svg>';
    Object.assign(c.style, {position: 'fixed', left: '-40px', top: '-40px', zIndex: 2147483647, pointerEvents: 'none',
      transform: 'translate(-4px, -2px)', filter: 'drop-shadow(0 1px 2px rgba(0,0,0,.35))'});
    document.documentElement.appendChild(c);
    document.addEventListener('mousemove', e => { c.style.left = e.clientX + 'px'; c.style.top = e.clientY + 'px'; }, true);
    document.addEventListener('mousedown', e => window.__demo.ripple(e.clientX, e.clientY), true);
  };
  const el = (tag, style, html) => {
    const e = document.createElement(tag);
    if (style) e.style.cssText = style;
    if (html !== undefined) e.innerHTML = html;
    return e;
  };
  const centre = e => { const r = e.getBoundingClientRect(); return {x: r.left + r.width / 2, y: r.top + r.height / 2}; };

  window.__demo = {
    ripple(x, y) {
      const r = el('div', `position:fixed;left:${x - 18}px;top:${y - 18}px;width:36px;height:36px;border-radius:50%;
        border:3px solid rgba(21,159,139,.85);z-index:2147483646;pointer-events:none;
        transition:transform .45s ease-out, opacity .45s ease-out`);
      document.documentElement.appendChild(r);
      requestAnimationFrame(() => { r.style.transform = 'scale(1.8)'; r.style.opacity = '0'; });
      setTimeout(() => r.remove(), 600);
    },

    // The list a <select> shows when it is opened. Returns the centre of each option, by value.
    dropdown(index) {
      const select = document.querySelectorAll('select')[index];
      select.focus();
      const r = select.getBoundingClientRect();
      const box = el('div', `position:fixed;left:${r.left}px;top:${r.bottom + 1}px;width:${r.width}px;
        background:#fff;border:1px solid #8a8a8a;border-radius:4px;box-shadow:0 6px 16px rgba(0,0,0,.22);
        z-index:2147483640;padding:3px 0;font-size:14px;overflow:hidden`);
      box.id = '__dd';
      const where = {};
      for (const o of select.options) {
        const row = el('div', `padding:5px 10px;${o.value === select.value ? 'background:#e6e6e6;' : ''}
          ${o.value ? '' : 'color:#6b6b6b;'}`, o.textContent);
        row.className = 'opt';
        box.appendChild(row);
        where[o.value] = row;
      }
      document.documentElement.appendChild(box);
      return Object.fromEntries(Object.entries(where).map(([v, row]) => [v, centre(row)]));
    },
    closeDropdown() { document.getElementById('__dd')?.remove(); },

    // The Windows "Open" window, listing the real folder. Returns where the wanted file and the Open button are.
    fileDialog(spec) {
      const d = el('div', `position:fixed;left:50%;top:50%;transform:translate(-50%,-50%);width:860px;height:540px;
        background:#f3f3f3;border:1px solid #b9b9b9;border-radius:8px;box-shadow:0 18px 50px rgba(0,0,0,.38);
        z-index:2147483640;display:flex;flex-direction:column;overflow:hidden;font-size:12.5px`);
      d.id = '__fd';
      const icon = n => n.endsWith('.csv') ? '📊' : n.endsWith('.txt') || n.endsWith('.md') ? '📄'
        : n.endsWith('.py') ? '🐍' : '🗂️';
      d.innerHTML = `
        <div style="height:34px;display:flex;align-items:center;justify-content:space-between;padding:0 0 0 14px;background:#fff">
          <span>Open</span><span style="width:46px;text-align:center;font-size:14px">✕</span></div>
        <div style="height:44px;display:flex;align-items:center;gap:12px;padding:0 12px;background:#fff;border-bottom:1px solid #e5e5e5">
          <span style="color:#555;letter-spacing:10px">← → ↑ ⟳</span>
          <div style="flex:1;height:28px;border:1px solid #d6d6d6;border-radius:4px;display:flex;align-items:center;padding:0 10px;gap:8px">
            <span>🖥️</span><span>This PC</span><span style="color:#888">›</span><span>Web-Based-ML-Model-Evaluator</span>
            <span style="color:#888">›</span><span>deliverable-2</span><span style="color:#888">›</span><b style="font-weight:600">demo-inputs</b></div>
          <div style="width:200px;height:28px;border:1px solid #d6d6d6;border-radius:4px;display:flex;align-items:center;padding:0 10px;color:#777">Search demo-inputs &nbsp;🔍</div>
        </div>
        <div style="flex:1;display:flex;min-height:0">
          <div style="width:170px;padding:10px 0;background:#f9f9f9;border-right:1px solid #e5e5e5;line-height:30px">
            <div style="padding-left:16px">🏠&nbsp; Home</div><div style="padding-left:16px">🖥️&nbsp; Desktop</div>
            <div style="padding-left:16px">⬇️&nbsp; Downloads</div><div style="padding-left:16px">📁&nbsp; Documents</div>
            <div style="padding-left:16px;background:#e1e1e1">📁&nbsp; demo-inputs</div><div style="padding-left:16px">💻&nbsp; This PC</div></div>
          <div style="flex:1;background:#fff;display:flex;flex-direction:column;min-width:0">
            <div style="display:grid;grid-template-columns:2.2fr 1.3fr 1.3fr .6fr;padding:8px 14px;color:#555;border-bottom:1px solid #eee">
              <span>Name</span><span>Date modified</span><span>Type</span><span style="text-align:right">Size</span></div>
            <div class="list" style="flex:1;overflow:hidden"></div></div>
        </div>
        <div style="height:92px;padding:12px 14px;display:grid;grid-template-columns:auto 1fr 250px;grid-template-rows:30px 30px;gap:10px;align-items:center">
          <span style="text-align:right">File name:</span>
          <div class="name" style="height:28px;border:1px solid #c9c9c9;border-bottom:2px solid #005fb8;border-radius:4px;background:#fff;display:flex;align-items:center;padding:0 8px"></div>
          <div style="height:28px;border:1px solid #c9c9c9;border-radius:4px;background:#fff;display:flex;align-items:center;justify-content:space-between;padding:0 8px">${spec.filter}<span>⌄</span></div>
          <span></span><span></span>
          <div style="display:flex;gap:8px;justify-content:flex-end">
            <div class="open" style="width:110px;height:30px;border-radius:4px;background:#005fb8;color:#fff;display:flex;align-items:center;justify-content:center">Open</div>
            <div style="width:110px;height:30px;border-radius:4px;background:#fff;border:1px solid #c9c9c9;display:flex;align-items:center;justify-content:center">Cancel</div></div>
        </div>`;
      const list = d.querySelector('.list');
      let wanted;
      for (const f of spec.files) {
        const row = el('div', 'display:grid;grid-template-columns:2.2fr 1.3fr 1.3fr .6fr;padding:4px 14px;white-space:nowrap',
          `<span style="overflow:hidden;text-overflow:ellipsis">${icon(f.name)}&nbsp; ${f.name}</span><span style="color:#555">${f.date}</span>
           <span style="color:#555;overflow:hidden;text-overflow:ellipsis">${f.type}</span><span style="color:#555;text-align:right">${f.size}</span>`);
        row.className = 'row';
        row.addEventListener('mousedown', () => {
          d.querySelectorAll('.row.sel').forEach(x => x.classList.remove('sel'));
          row.classList.add('sel');
          d.querySelector('.name').textContent = f.name;
        });
        list.appendChild(row);
        if (f.name === spec.pick) wanted = row;
      }
      document.documentElement.appendChild(d);
      wanted.scrollIntoView({block: 'nearest'});
      return {file: centre(wanted), open: centre(d.querySelector('.open'))};
    },
    closeFileDialog() { document.getElementById('__fd')?.remove(); },
  };

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', add); else add();
})();
"""

FILE_TYPES = {".joblib": "JOBLIB File", ".pkl": "PKL File", ".csv": "Microsoft Excel CSV File", ".txt": "Text Document",
              ".py": "Python File", ".md": "Markdown File"}  # fmt: skip


def folder_listing(accept: tuple[str, ...] | None) -> list[dict]:
    """The demo-inputs folder as the Open window lists it, limited to the accepted file types."""
    rows = []
    for path in sorted(INPUTS.iterdir(), key=lambda p: p.name.lower()):
        if not path.is_file() or (accept and path.suffix.lower() not in accept):
            continue
        stat = path.stat()
        when = datetime.fromtimestamp(stat.st_mtime)
        rows.append({
            "name": path.name,
            "date": f"{when.month}/{when.day}/{when.year} {when.strftime('%I:%M %p').lstrip('0')}",
            "type": FILE_TYPES.get(path.suffix.lower(), f"{path.suffix[1:].upper()} File"),
            "size": f"{max(1, round(stat.st_size / 1024))} KB",
        })  # fmt: skip
    return rows


class Demo:
    def __init__(self, page):
        self.page = page
        self.x, self.y = W / 2, H / 2

    def wait(self, seconds: float) -> None:
        time.sleep(seconds)

    def glide(self, x: float, y: float, duration: float = 0.6) -> None:
        """Move the mouse smoothly, like a person would."""
        steps = max(8, int(duration * 45))
        x0, y0 = self.x, self.y
        for i in range(1, steps + 1):
            t = i / steps
            ease = t * t * (3 - 2 * t)
            self.page.mouse.move(x0 + (x - x0) * ease, y0 + (y - y0) * ease)
            time.sleep(duration / steps)
        self.x, self.y = x, y

    def to(self, locator, duration: float = 0.6):
        locator.scroll_into_view_if_needed()
        box = locator.bounding_box()
        self.glide(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2, duration)
        return box

    def click_here(self, pause: float = 0.0) -> None:
        self.page.mouse.click(self.x, self.y)
        self.wait(pause)

    def click(self, locator, pause: float = 0.6) -> None:
        self.to(locator)
        self.wait(0.15)
        self.click_here(pause)

    def choose_file(self, index: int, name: str, unhurried: bool = False) -> None:
        """Click the real 'Choose File' button and pick the file in the browser's file chooser."""
        if index == 0:
            accept, label = (".pkl", ".joblib"), "Model files (*.pkl;*.joblib)"
        else:
            accept, label = (".csv",), "CSV files (*.csv)"
        # Picking a file of another type means switching the filter first.
        if Path(name).suffix not in accept:
            accept, label = None, "All files (*.*)"
        self.to(self.page.locator("input[type=file]").nth(index))
        self.wait(0.2)
        with self.page.expect_file_chooser() as chooser:
            self.click_here()
        spots = self.page.evaluate("s => window.__demo.fileDialog(s)",
                                   {"files": folder_listing(accept), "filter": label, "pick": name})  # fmt: skip
        self.wait(0.7 if unhurried else 0.35)
        self.glide(spots["file"]["x"], spots["file"]["y"], 0.8 if unhurried else 0.55)
        self.wait(0.15)
        self.click_here(0.45 if unhurried else 0.25)
        self.glide(spots["open"]["x"], spots["open"]["y"], 0.55 if unhurried else 0.4)
        self.wait(0.1)
        self.click_here(0.1)
        self.page.evaluate("window.__demo.closeFileDialog()")
        chooser.value.set_files(str(INPUTS / name))
        self.wait(0.8 if unhurried else 0.55)

    def pick(self, index: int, value: str) -> None:
        """Open a drop-down menu and choose an option from its list."""
        select = self.page.locator("select").nth(index)
        self.to(select)
        self.wait(0.15)
        self.page.evaluate("([x, y]) => window.__demo.ripple(x, y)", [self.x, self.y])
        spots = self.page.evaluate("i => window.__demo.dropdown(i)", index)
        self.wait(0.4)
        self.glide(spots[value]["x"], spots[value]["y"], 0.55)
        self.wait(0.2)
        self.click_here(0.1)
        self.page.evaluate("window.__demo.closeDropdown()")
        select.select_option(value)
        self.wait(0.5)

    def button(self, text: str):
        return self.page.get_by_role("button", name=text).first

    def scroll(self, pixels: int, duration: float = 1.2) -> None:
        steps = max(10, int(duration * 40))
        for _ in range(steps):
            self.page.mouse.wheel(0, pixels / steps)
            time.sleep(duration / steps)

    def top(self) -> None:
        self.page.evaluate("window.scrollTo({top: 0, behavior: 'smooth'})")
        self.wait(0.7)

    def run(self, review_pause: float = 0.6) -> None:
        """From the Configure step: review, then submit."""
        self.click(self.button("Next: Review"), review_pause)
        self.click(self.button("Evaluate model"), 0.3)

    def wait_for_text(self, text: str, timeout: float = 30) -> None:
        self.page.get_by_text(text).first.wait_for(timeout=timeout * 1000)

    def point_at(self, text: str, linger: float) -> None:
        self.wait_for_text(text)
        self.wait(0.4)
        self.to(self.page.get_by_text(text).first, 0.7)
        self.wait(linger)


def scenes(demo: Demo, page, downloads: Path) -> None:
    # 1. Upload a churn model and its data, and make the classic mistake: a feature picked as the target column.
    page.goto(APP)
    demo.wait(1.0)
    demo.glide(640, 300, 0.7)
    demo.choose_file(0, "01_churn_model.joblib", unhurried=True)
    demo.choose_file(1, "01_churn_data.csv", unhurried=True)
    demo.click(demo.button("Next: Configure"), 0.7)
    demo.pick(0, "classification")
    demo.pick(1, "tenure_months")
    demo.run(review_pause=1.2)
    demo.wait_for_text("FAILED")
    demo.point_at("Missing from the dataset", 2.2)

    # 2. Back to the configuration, choose the right column, and run it again: the results.
    demo.click(demo.button("Back to configuration"), 0.7)
    demo.pick(1, "churned")
    demo.run()
    demo.wait_for_text("COMPLETED")
    demo.wait(1.0)
    demo.scroll(330, 1.3)
    demo.wait(0.8)
    demo.glide(560, 300, 0.7)  # read along the "What it means" column
    demo.glide(900, 300, 1.3)
    demo.wait(1.0)
    demo.scroll(330, 1.1)
    demo.wait(1.0)

    # 3. Download the result, then open the file that was saved.
    with page.expect_download() as download:
        demo.click(demo.button("Download Results"), 0.2)
    saved = downloads / download.value.suggested_filename
    download.value.save_as(saved)
    demo.wait(0.9)
    page.goto(saved.as_uri())
    demo.wait(0.5)
    demo.glide(420, 260, 0.7)
    demo.wait(2.0)

    # 4. A different kind of model: regression, with its own metrics.
    page.goto(APP)
    demo.wait(0.8)
    demo.choose_file(0, "03_house_price_model.joblib")
    demo.choose_file(1, "03_house_price_data.csv")
    demo.click(demo.button("Next: Configure"), 0.6)
    demo.pick(0, "regression")
    demo.pick(1, "price")
    demo.run()
    demo.wait_for_text("COMPLETED")
    demo.wait(0.6)
    demo.scroll(360, 1.1)
    demo.wait(2.0)

    # 5. A corrupt model file: rejected, and the model is never opened inside the server.
    demo.click(demo.button("New evaluation"), 0.6)
    demo.top()
    demo.choose_file(0, "bad_corrupt_model.joblib")
    demo.click(demo.button("Next: Configure"), 0.5)
    demo.run(review_pause=0.4)
    demo.point_at("could not be loaded", 1.8)

    # 6. A malformed CSV is rejected before anything runs; the message sits next to the field.
    demo.choose_file(0, "01_churn_model.joblib")
    demo.choose_file(1, "bad_ragged_rows.csv")
    demo.click(demo.button("Next: Configure"), 0.5)
    demo.pick(0, "classification")
    demo.pick(1, "churned")
    demo.run(review_pause=0.4)
    demo.point_at("ragged rows", 1.8)

    # 7. A file that is not a model at all is refused as soon as it is chosen.
    demo.choose_file(0, "bad_unsupported_model.txt")
    demo.to(page.get_by_text("Please select a .pkl or .joblib").first, 0.7)
    demo.wait(1.8)

    # 8. The documented API.
    page.goto(f"{API}/docs")
    page.get_by_text("Submit an evaluation").first.wait_for()
    demo.wait(1.0)
    demo.glide(500, 420, 0.7)
    demo.wait(1.0)
    demo.scroll(300, 1.2)
    demo.wait(0.5)
    # Open "POST /api/evaluations" to show its fields.
    demo.click(page.locator(".opblock-post .opblock-summary").first, 1.0)
    demo.scroll(420, 1.4)
    demo.wait(2.2)


def main() -> int:
    if shutil.which("ffmpeg") is None:
        print("ffmpeg is needed", file=sys.stderr)
        return 1
    work = Path(tempfile.mkdtemp(prefix="demo-recording-"))
    downloads = work / "downloads"
    downloads.mkdir()
    started = time.time()
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        context = browser.new_context(
            viewport={"width": W, "height": H},
            record_video_dir=str(work),
            record_video_size={"width": W, "height": H},
            accept_downloads=True,
        )
        context.add_init_script(PAGE_HELPERS)
        page = context.new_page()
        page.set_default_timeout(30000)
        try:
            scenes(Demo(page), page, downloads)
        finally:
            raw = Path(page.video.path())
            context.close()
            browser.close()
    print(f"recorded {time.time() - started:.0f} s of browsing; raw video {raw.name}")

    # The first moment is a blank page while the browser starts; skip it, and convert to MP4. Waiting for the
    # evaluations takes real time, so if the take runs past two minutes it is sped up evenly to fit.
    def encode(speed: float) -> float:
        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-ss", "0.6", "-i", str(raw), "-vf", f"setpts=PTS/{speed:.4f}",
             "-c:v", "libx264", "-crf", "20", "-preset", "slow", "-pix_fmt", "yuv420p", "-r", "25",
             "-movflags", "+faststart", "-an", str(OUT)],
            check=True,
        )  # fmt: skip
        return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                     str(OUT)], check=True, capture_output=True, text=True).stdout)  # fmt: skip

    length = encode(1.0)
    if length > TARGET_SECONDS:
        length = encode(length / TARGET_SECONDS)
    print(f"wrote {OUT} ({OUT.stat().st_size / 1e6:.1f} MB, {length:.1f} s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
