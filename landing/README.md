Landing page for W&M Sports Analytics

What this is
- A standalone landing page (static HTML/CSS/JS) in `landing/` that shows a full-screen slideshow of five photos and two large choice boxes linking to your dashboards.
- Purpose: keep your dashboards untouched while providing a visual header/hub that links to them.

Files created
- `landing/index.html` — the landing page.
- `landing/styles.css` — styles for the page.
- `landing/script.js` — slideshow behavior (auto advance every 5s, manual prev/next).
- `landing/README.md` — this file.

How to use
1. Place your 5 Zable stadium images in `landing/images/` and name them exactly `ff1.jpg`, `ff2.jpg`, `ff3.jpg`, `ff4.jpg`, `ff5.jpg` (or update the `img` paths in `index.html`).
2. Open the page in a browser. For best behavior (no file:// restrictions) serve the project folder with a simple HTTP server. From the workspace root run (PowerShell):

   python -m http.server 8000

   Then open: http://localhost:8000/landing/index.html

3. The two choice boxes currently link to `http://localhost:8051/richmond` and `http://localhost:8051/wm` — `Main.py` in this project runs the Dash app on port 8051 by default. If your dashboards run on a different address or port, edit the `href` values in `index.html` or pass a different command to `run_landing.py` using `--dash-cmd`.

Assumptions and notes
- I did NOT modify any existing dashboard files. This is a new, isolated folder.
- Assumes images are provided by you in `landing/images/` (not created here).

If you want
- I can: copy your existing images into `landing/images/` if you tell me where they are now.
- I can change the links to match exact routes your Dash app uses (if you tell me the urls or ports).
- Convert this into a Dash page that integrates into your app instead of a static HTML page (will require editing app files).
