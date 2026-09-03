#!/usr/bin/env python3
"""Generate the procedural image textures that are not downloads (screens with code on them).
Run by tools/fetch_assets.py; safe to run again. Needs Pillow."""
import os
import random

HERE = os.path.dirname(os.path.abspath(__file__))
TEX = os.path.join(os.path.dirname(HERE), "assets", "textures")


def code_screen(path, w=1280, h=800, seed=3):
    from PIL import Image, ImageDraw
    rng = random.Random(seed)
    im = Image.new("RGB", (w, h), (12, 14, 19))
    d = ImageDraw.Draw(im)
    # editor chrome: a dark gutter with line numbers, a lighter tab bar, a status bar
    d.rectangle([0, 0, w, 34], fill=(20, 23, 30))
    d.rectangle([12, 6, 150, 30], fill=(30, 34, 44))
    d.rectangle([0, h - 26, w, h], fill=(38, 62, 110))
    d.rectangle([0, 34, 64, h - 26], fill=(15, 17, 23))
    palette = [(120, 160, 230), (220, 150, 90), (150, 200, 120), (190, 130, 210), (200, 200, 205), (110, 120, 135), (230, 200, 110)]
    y = 46
    indent = 0
    while y < h - 40:
        d.rectangle([22, y + 2, 50, y + 10], fill=(60, 66, 80))          # line number
        if rng.random() < 0.12:
            indent = max(0, min(4, indent + rng.choice((-2, -1, 1, 1, 2))))
        x = 80 + indent * 34
        if rng.random() < 0.1:                                             # blank line
            y += 20
            continue
        if rng.random() < 0.18:                                            # a comment: long gray run
            d.rectangle([x, y + 1, x + rng.randint(200, 520), y + 11], fill=(90, 98, 110))
            y += 20
            continue
        n = rng.randint(2, 7)
        for _ in range(n):
            tw = rng.randint(22, 110)
            if x + tw > w - 60:
                break
            d.rectangle([x, y + 1, x + tw, y + 11], fill=rng.choice(palette))
            x += tw + rng.randint(8, 18)
        y += 20
    # cursor line highlight
    cy = 46 + 20 * rng.randint(8, 24)
    d.rectangle([64, cy - 2, w, cy + 14], fill=None, outline=(40, 46, 60))
    im.save(path, quality=92)


def main():
    os.makedirs(os.path.join(TEX, "screen_code"), exist_ok=True)
    code_screen(os.path.join(TEX, "screen_code", "diffuse.jpg"))
    print("wrote", os.path.join(TEX, "screen_code", "diffuse.jpg"))


if __name__ == "__main__":
    main()
