#!/usr/bin/env python3
"""Render the named review stills listed under "stills" in plan.json.

Runs Blender once per still (the scene builds in about a second). System Python, no bpy needed.

    python3 tools/stills.py --res 1280x720 --samples 256 --out renders/stills
Env: BLENDER (binary), DEVICE (CPU/METAL/...).
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def find_blender():
    b = os.environ.get("BLENDER")
    if b:
        return b
    for cand in ("blender42", "/opt/blender-4.2.11-linux-x64/blender",
                 "/Applications/Blender.app/Contents/MacOS/Blender",
                 os.path.expanduser("~/Applications/Blender.app/Contents/MacOS/Blender"), "blender"):
        if shutil.which(cand) or os.path.isfile(cand):
            return shutil.which(cand) or cand
    sys.exit("Blender not found; set BLENDER=/path/to/blender")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", default=os.path.join(ROOT, "plan.json"))
    ap.add_argument("--res", default="1280x720")
    ap.add_argument("--samples", type=int, default=256)
    ap.add_argument("--stage", default="auto")
    ap.add_argument("--out", default=os.path.join(ROOT, "renders", "stills"))
    ap.add_argument("--only", default=None, help="comma-separated still names")
    ap.add_argument("--exposure", type=float, default=None)
    ap.add_argument("--views", action="store_true", help="render plan['views'] (free poses off the camera path) instead")
    args = ap.parse_args()
    plan = json.load(open(args.plan))
    stills = plan.get("views", []) if args.views else plan.get("stills", [])
    if args.only:
        keep = set(args.only.split(","))
        stills = [s for s in stills if s["name"] in keep]
    blender = find_blender()
    device = os.environ.get("DEVICE", "CPU")
    os.makedirs(args.out, exist_ok=True)
    # build_scene writes to <out>/stills/<name>.png, so hand it the parent
    tmp_out = os.path.join(args.out, "_work")
    timings = {}
    for s in stills:
        t0 = time.time()
        if "pos" in s:
            sel = ["--view", "%s:%s" % (s["name"], ",".join(str(x) for x in list(s["pos"]) + list(s["look"])))]
        else:
            sel = ["--still", "%s:%s:%s" % (s["shot"], s["t"], s["name"])]
        cmd = [blender, "-b", "-P", os.path.join(ROOT, "build_scene.py"), "--",
               "--plan", args.plan] + sel + [
               "--res", args.res, "--samples", str(args.samples), "--device", device,
               "--stage", args.stage, "--out", tmp_out, "--no-blend", "--motion-blur", "off"]
        if args.exposure is not None:
            cmd += ["--exposure", str(args.exposure)]
        r = subprocess.run(cmd, capture_output=True, text=True)
        src = os.path.join(tmp_out, "stills", s["name"] + ".png")
        if r.returncode != 0 or not os.path.exists(src):
            print(r.stdout[-3000:], r.stderr[-3000:])
            sys.exit("still %s failed" % s["name"])
        shutil.move(src, os.path.join(args.out, s["name"] + ".png"))
        dt = time.time() - t0
        timings[s["name"]] = round(dt, 1)
        print("still %-16s %6.1fs" % (s["name"], dt), flush=True)
    shutil.rmtree(tmp_out, ignore_errors=True)
    json.dump({"res": args.res, "samples": args.samples, "device": device, "seconds": timings},
              open(os.path.join(args.out, "timings.json"), "w"), indent=2)


if __name__ == "__main__":
    main()
