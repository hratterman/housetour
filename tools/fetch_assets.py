#!/usr/bin/env python3
"""Download CC0 assets listed in assets/wanted.json into assets/ and record every file in
assets/manifest.json with its source URL and license.

Sources: Poly Haven (api.polyhaven.com, CC0) and ambientCG (ambientcg.com, CC0). No accounts.

    python3 tools/fetch_assets.py            # fetch everything missing
    python3 tools/fetch_assets.py --check    # report what is missing, download nothing

Textures land in assets/textures/<name>/<map>.jpg with normalized map names:
    diffuse, rough, normal (OpenGL), disp, ao, metal
Models land in assets/models/<name>/<name>.gltf plus textures/ and .bin.
HDRIs land in assets/hdris/<name>.hdr
"""
import argparse
import io
import json
import os
import sys
import time
import urllib.request
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")
WANTED = os.path.join(ASSETS, "wanted.json")
MANIFEST = os.path.join(ASSETS, "manifest.json")

PH_API = "https://api.polyhaven.com"
PH_MAPS = {"Diffuse": "diffuse", "Rough": "rough", "nor_gl": "normal", "Displacement": "disp",
           "AO": "ao", "Metal": "metal"}
ACG_MAPS = {"Color": "diffuse", "Roughness": "rough", "NormalGL": "normal", "Displacement": "disp",
            "AmbientOcclusion": "ao", "Metalness": "metal"}
UA = {"User-Agent": "housetour-fetch/1.0 (CC0 asset cache)"}


def get(url, retries=4):
    last = None
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=120) as r:
                return r.read()
        except Exception as e:  # noqa
            last = e
            time.sleep(2 ** i)
    raise RuntimeError("failed %s: %s" % (url, last))


def get_json(url):
    return json.loads(get(url).decode("utf-8"))


def load_manifest():
    if os.path.exists(MANIFEST):
        return json.load(open(MANIFEST))
    return {"license_note": "All entries are CC0 1.0 unless stated. Sources: polyhaven.com, ambientcg.com.",
            "files": {}}


def save_manifest(mf):
    json.dump(mf, open(MANIFEST, "w"), indent=1, sort_keys=True)


def record(mf, relpath, url, source, asset_id, license_="CC0-1.0", author=None):
    mf["files"][relpath] = {"url": url, "source": source, "asset": asset_id, "license": license_,
                            "author": author or ""}


# ---------------------------------------------------------------- poly haven


def ph_info(asset_id):
    try:
        return get_json("%s/info/%s" % (PH_API, asset_id))
    except Exception:
        return {}


def fetch_ph_texture(name, asset_id, res, mf, check):
    out = os.path.join(ASSETS, "textures", name)
    have = all(os.path.exists(os.path.join(out, k + ".jpg")) for k in ("diffuse", "rough", "normal"))
    if have:
        return "ok"
    if check:
        return "missing"
    files = get_json("%s/files/%s" % (PH_API, asset_id))
    info = ph_info(asset_id)
    authors = ", ".join(info.get("authors", {}).keys()) if info else ""
    os.makedirs(out, exist_ok=True)
    for ph_key, local in PH_MAPS.items():
        entry = files.get(ph_key, {}).get(res, {}).get("jpg")
        if not entry:
            continue
        dst = os.path.join(out, local + ".jpg")
        if not os.path.exists(dst):
            data = get(entry["url"])
            open(dst, "wb").write(data)
        record(mf, os.path.relpath(dst, ROOT), entry["url"], "polyhaven", asset_id, author=authors)
    save_manifest(mf)
    return "fetched"


def fetch_ph_model(name, asset_id, res, mf, check):
    out = os.path.join(ASSETS, "models", name)
    gltf_path = os.path.join(out, asset_id + ".gltf")
    if os.path.exists(gltf_path):
        return "ok"
    if check:
        return "missing"
    files = get_json("%s/files/%s" % (PH_API, asset_id))
    info = ph_info(asset_id)
    authors = ", ".join(info.get("authors", {}).keys()) if info else ""
    g = files["gltf"]
    if res not in g:
        res = sorted(g.keys())[0]
    entry = g[res]["gltf"]
    os.makedirs(out, exist_ok=True)
    open(gltf_path, "wb").write(get(entry["url"]))
    record(mf, os.path.relpath(gltf_path, ROOT), entry["url"], "polyhaven", asset_id, author=authors)
    for rel, inc in entry.get("include", {}).items():
        dst = os.path.join(out, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if not os.path.exists(dst):
            open(dst, "wb").write(get(inc["url"]))
        record(mf, os.path.relpath(dst, ROOT), inc["url"], "polyhaven", asset_id, author=authors)
    save_manifest(mf)
    return "fetched"


def fetch_ph_hdri(name, asset_id, res, mf, check):
    out = os.path.join(ASSETS, "hdris")
    dst = os.path.join(out, name + ".hdr")
    if os.path.exists(dst):
        return "ok"
    if check:
        return "missing"
    files = get_json("%s/files/%s" % (PH_API, asset_id))
    info = ph_info(asset_id)
    authors = ", ".join(info.get("authors", {}).keys()) if info else ""
    entry = files["hdri"][res]["hdr"]
    os.makedirs(out, exist_ok=True)
    open(dst, "wb").write(get(entry["url"]))
    record(mf, os.path.relpath(dst, ROOT), entry["url"], "polyhaven", asset_id, author=authors)
    save_manifest(mf)
    return "fetched"


# ---------------------------------------------------------------- ambientcg


def fetch_acg_texture(name, asset_id, res, mf, check):
    out = os.path.join(ASSETS, "textures", name)
    if all(os.path.exists(os.path.join(out, k + ".jpg")) for k in ("diffuse", "rough", "normal")):
        return "ok"
    if check:
        return "missing"
    fname = "%s_%s-JPG.zip" % (asset_id, res.upper())
    url = "https://ambientcg.com/get?file=%s" % fname
    data = get(url)
    os.makedirs(out, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        for member in z.namelist():
            base = os.path.basename(member)
            for acg_key, local in ACG_MAPS.items():
                if base.endswith("_%s.jpg" % acg_key):
                    dst = os.path.join(out, local + ".jpg")
                    open(dst, "wb").write(z.read(member))
                    record(mf, os.path.relpath(dst, ROOT), url, "ambientcg", asset_id)
    save_manifest(mf)
    return "fetched"


# ---------------------------------------------------------------- main


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--only", default=None, help="comma-separated names")
    args = ap.parse_args()
    wanted = json.load(open(WANTED))
    mf = load_manifest()
    only = set(args.only.split(",")) if args.only else None
    status = {}
    for kind, items in wanted.items():
        for name, spec in items.items():
            if only and name not in only:
                continue
            src = spec.get("source", "polyhaven")
            res = spec.get("res", "2k" if kind != "models" else "1k")
            try:
                if kind == "textures" and src == "polyhaven":
                    r = fetch_ph_texture(name, spec["id"], res, mf, args.check)
                elif kind == "textures" and src == "ambientcg":
                    r = fetch_acg_texture(name, spec["id"], res, mf, args.check)
                elif kind == "models":
                    r = fetch_ph_model(name, spec["id"], res, mf, args.check)
                elif kind == "hdris":
                    r = fetch_ph_hdri(name, spec["id"], res, mf, args.check)
                else:
                    r = "unknown kind"
            except Exception as e:  # noqa
                r = "FAILED: %s" % e
            status[(kind, name)] = r
            print("%-9s %-28s %s" % (kind, name, r), flush=True)
    bad = [k for k, v in status.items() if v.startswith("FAILED") or v == "missing"]
    print("\n%d assets, %d problems" % (len(status), len(bad)))
    if bad:
        print("missing assets fall back to flat materials / procedural stand-ins; re-run to retry downloads")
    # only a total failure (nothing fetched at all) is fatal, so a flaky mirror does not stop the render
    if bad and len(bad) == len(status):
        sys.exit(1)


if __name__ == "__main__":
    main()
