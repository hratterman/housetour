#!/usr/bin/env python3
"""Load web/index.html in headless Chromium, jump to each teleport spot, save screenshots, report console errors.

    python3 tools/web_screenshots.py [--out renders/web_shots] [--width 960]
Requires: pip install playwright (uses the Chromium at $PLAYWRIGHT_BROWSERS_PATH or the system one).
"""
import argparse
import http.server
import os
import socketserver
import threading
import glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB = os.path.join(ROOT, "web")


def serve(port):
    handler = http.server.SimpleHTTPRequestHandler
    os.chdir(WEB)
    socketserver.TCPServer.allow_reuse_address = True
    httpd = socketserver.TCPServer(("127.0.0.1", port), handler)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    return httpd


def find_chromium():
    for c in (os.environ.get("CHROMIUM"), "/opt/pw-browsers/chromium"):
        if c and os.path.exists(c):
            return c
    cands = glob.glob(os.path.expanduser("~/.cache/ms-playwright/chromium-*/chrome-linux/chrome"))
    return cands[0] if cands else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(ROOT, "renders", "web_shots"))
    ap.add_argument("--width", type=int, default=640)
    ap.add_argument("--height", type=int, default=360)
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--spots", default=None, help="comma-separated 1-based spot numbers")
    args = ap.parse_args()
    args.out = os.path.abspath(args.out)
    os.makedirs(args.out, exist_ok=True)
    from playwright.sync_api import sync_playwright
    httpd = serve(args.port)
    errors = []
    with sync_playwright() as p:
        kw = {"args": ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"]}
        exe = find_chromium()
        if exe:
            kw["executable_path"] = exe
        b = p.chromium.launch(**kw)
        pg = b.new_page(viewport={"width": args.width, "height": args.height})
        pg.on("console", lambda m: errors.append(m.text) if m.type in ("error",) else None)
        pg.on("pageerror", lambda e: errors.append(str(e)))
        pg.goto("http://127.0.0.1:%d/index.html?lite" % args.port)
        pg.wait_for_function("window.__ready === true", timeout=240000)
        pg.wait_for_timeout(1500)
        pg.evaluate("document.getElementById('help').style.display='none'")
        wanted = set(int(x) for x in args.spots.split(",")) if args.spots else None
        n = pg.evaluate("window.__spots ? window.__spots.length : 0")
        spots = pg.evaluate("window.__spots || []")
        for i, s in enumerate(spots):
            if wanted and (i + 1) not in wanted:
                continue
            pg.evaluate("window.__teleport(%d)" % i)
            pg.wait_for_timeout(900)
            path = os.path.join(args.out, "%02d_%s.png" % (i + 1, s["name"].lower()))
            pg.screenshot(path=path, timeout=240000)
            print("shot", path, flush=True)
        b.close()
    httpd.shutdown()
    if errors:
        print("\nconsole errors:")
        for e in errors[:20]:
            print("  ", e[:300])
    else:
        print("\nno console errors")


if __name__ == "__main__":
    main()
