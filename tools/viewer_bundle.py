#!/usr/bin/env python3
"""Package the web viewer for someone who just wants to walk around the house.

Two outputs in dist/:
  housetour_viewer.zip    the web/ folder plus start_viewer.command (macOS), start_viewer.bat (Windows) and a
                          README. Unzip, double-click the starter, the browser opens on http://localhost:8765.
  housetour_viewer.html   one self-contained file: three.js from jsDelivr, the house (house.glb), lights.json and
                          plan_web.json inlined as base64 / JSON. Opens from anywhere that allows module scripts
                          (a hosted page, an artifact); browsers block module imports from file://, so the zip is
                          the double-click route.

Usage: python3 tools/viewer_bundle.py [--out dist]
"""
import argparse
import base64
import json
import os
import re
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB = os.path.join(ROOT, "web")

STARTER_SH = """#!/bin/bash
# Serves this folder and opens the viewer. Needs python3 (macOS ships it; Windows users use start_viewer.bat).
cd "$(dirname "$0")"
PORT=8765
( sleep 1.5; open "http://localhost:$PORT" 2>/dev/null || xdg-open "http://localhost:$PORT" 2>/dev/null ) &
echo "Serving the house at http://localhost:$PORT  (Ctrl-C to stop)"
python3 -m http.server $PORT
"""

STARTER_BAT = """@echo off
cd /d "%~dp0"
start "" http://localhost:8765
echo Serving the house at http://localhost:8765  (close this window to stop)
python -m http.server 8765
"""

README = """House walkthrough (web viewer)

1. macOS: double-click start_viewer.command (first time: right-click, Open, because it is unsigned).
   Windows: double-click start_viewer.bat (needs Python from python.org, ticked "Add to PATH").
   Anything else: open a terminal in this folder and run  python3 -m http.server 8765
2. The browser opens http://localhost:8765 . Click the page to grab the mouse.
3. WASD or arrows to walk, mouse to look, Space to jump, Shift to run, Esc to release the mouse.
   Number keys or the buttons top-left teleport to a room. L toggles the lamps, M the map, F flies (Q/E up, down).
   Add ?lite to the address on a weak GPU (no shadows, 1x pixels).

The viewer is web/index.html from the housetour repository; house.glb is exported from the same plan.json and
staging.json the renders use, with the materials baked to tiles at their physical size.
"""


def single_file(revision):
    html = open(os.path.join(WEB, "index.html"), encoding="utf-8").read()
    cdn = "https://cdn.jsdelivr.net/npm/three@0.%s.0" % revision
    importmap = ('<script type="importmap">\n{ "imports": {\n  "three": "%s/build/three.module.js",\n'
                 '  "three/addons/": "%s/examples/jsm/"\n} }\n</script>' % (cdn, cdn))
    html, n = re.subn(r'<script type="importmap">.*?</script>', importmap, html, count=1, flags=re.S)
    assert n == 1, "importmap not found in web/index.html"
    with open(os.path.join(WEB, "house.glb"), "rb") as f:
        glb = base64.b64encode(f.read()).decode("ascii")
    inline = {
        "house.glb": glb,
        "lights.json": json.load(open(os.path.join(WEB, "lights.json"))),
        "plan_web.json": json.load(open(os.path.join(WEB, "plan_web.json"))),
    }
    tag = "<script>window.__INLINE__ = %s;</script>\n" % json.dumps(inline, separators=(",", ":"))
    html = html.replace('<script type="module">', tag + '<script type="module">', 1)
    return html


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(ROOT, "dist"))
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    three = open(os.path.join(WEB, "vendor", "three", "three.module.js"), encoding="utf-8", errors="ignore").read(4000)
    m = re.search(r"REVISION\s*=\s*'(\d+)", three)
    revision = m.group(1) if m else "160"

    zpath = os.path.join(a.out, "housetour_viewer.zip")
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for dp, dns, fns in os.walk(WEB):
            dns[:] = [d for d in dns if not d.startswith("_")]
            for fn in fns:
                if fn.startswith("_") or fn.endswith(".log"):
                    continue
                full = os.path.join(dp, fn)
                z.write(full, os.path.join("housetour_viewer", os.path.relpath(full, WEB)))
        info = zipfile.ZipInfo("housetour_viewer/start_viewer.command")
        info.external_attr = 0o755 << 16
        z.writestr(info, STARTER_SH)
        z.writestr("housetour_viewer/start_viewer.bat", STARTER_BAT)
        z.writestr("housetour_viewer/README.txt", README)
    print("wrote %s (%.1f MB)" % (zpath, os.path.getsize(zpath) / 1e6))

    hpath = os.path.join(a.out, "housetour_viewer.html")
    html = single_file(revision)
    open(hpath, "w", encoding="utf-8").write(html)
    print("wrote %s (%.1f MB, three r%s from jsDelivr)" % (hpath, os.path.getsize(hpath) / 1e6, revision))


if __name__ == "__main__":
    main()
