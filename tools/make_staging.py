#!/usr/bin/env python3
"""Write staging.json from the room-by-room lists in staging_main.py and staging_rest.py.

    python3 tools/make_staging.py
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import staging_main  # noqa: E402
import staging_rest  # noqa: E402
import staging_clutter  # noqa: E402


def main():
    staging_main.main_floor()
    staging_main.exterior()
    staging_rest.second_floor()
    staging_rest.basement()
    staging_rest.garage()
    staging_clutter.main_floor()
    staging_clutter.exterior()
    staging_clutter.second_floor()
    staging_clutter.basement()
    staging_clutter.garage()
    entries = [e for e in staging_main.E if e is not None]
    out = os.path.join(ROOT, "staging.json")
    json.dump(entries, open(out, "w"), indent=0)
    n_model = sum(1 for e in entries if "asset" in e and not e["asset"].startswith("proc:"))
    n_proc = sum(1 for e in entries if "asset" in e and e["asset"].startswith("proc:"))
    print("wrote", out, "entries", len(entries), "models", n_model, "procedural", n_proc)


if __name__ == "__main__":
    main()
