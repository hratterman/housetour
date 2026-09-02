#!/usr/bin/env python3
"""Tile the PNGs in a directory into one labeled contact sheet.

    python3 tools/contact_sheet.py renders/stills renders/contact_sheet.png [--cols 3]
"""
import argparse
import glob
import os

from PIL import Image, ImageDraw, ImageFont


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--cols", type=int, default=3)
    ap.add_argument("--width", type=int, default=640, help="tile width in px")
    args = ap.parse_args()
    files = sorted(f for f in glob.glob(os.path.join(args.src, "*.png")))
    if not files:
        raise SystemExit("no PNGs in %s" % args.src)
    ims = [Image.open(f).convert("RGB") for f in files]
    tw = args.width
    th = int(round(tw * ims[0].height / ims[0].width))
    label_h = 28
    cols = min(args.cols, len(ims))
    rows = (len(ims) + cols - 1) // cols
    pad = 8
    sheet = Image.new("RGB", (cols * (tw + pad) + pad, rows * (th + label_h + pad) + pad), (24, 22, 20))
    draw = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
    except Exception:
        font = ImageFont.load_default()
    for i, (f, im) in enumerate(zip(files, ims)):
        r, c = divmod(i, cols)
        x = pad + c * (tw + pad)
        y = pad + r * (th + label_h + pad)
        sheet.paste(im.resize((tw, th), Image.LANCZOS), (x, y))
        draw.text((x + 4, y + th + 5), os.path.splitext(os.path.basename(f))[0], fill=(235, 225, 210), font=font)
    sheet.save(args.dst)
    print("wrote", args.dst, sheet.size, "from", len(files), "stills")


if __name__ == "__main__":
    main()
