#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
#
# REFERENCE IMPLEMENTATION. Taken verbatim from the project it was written for, and
# tied to that project's report schema. It is here to be read, not to be dropped into
# another tree: what transfers is the list of things it refuses to do. See
# examples/tools/README.md and MEASUREMENT.md of the standard.
#
# Turns one raw benchmark report into a curated baseline, and keeps the raw report
# next to it so the result can be checked.
#
# Until this existed, curation was a human retyping numbers into a different schema:
# the harness writes per-run entries with keys like "ee", the curated file carries
# averages under "ee_pct", and nothing recorded which run produced what. The first
# canonical baseline turned out to blend two sessions - its frametime and spread came
# from one run of the scene, its subsystem counters from another whose spread was
# twice as large. The file the docs call the source of truth was reporting a spread
# that did not belong to half its contents.
#
# A baseline is therefore the curation of exactly ONE session. If you want another
# session's numbers, curate it as its own file; both raw reports are committed.
#
#   python tools/curate_baseline.py tools/bench/results/<report>.json --label baseline
#
# Editorial prose in an existing baseline (scene description, observations, caveats)
# is preserved: this tool owns the numbers, a human owns the explanation.

import argparse
import json
import os
import shutil
import statistics
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
BASELINE_DIR = os.path.join(ROOT, "tools", "bench", "baseline")

# The harness names per-run thread figures without a suffix; the curated schema uses
# _pct so a percentage is not mistaken for a duration. This mapping is the whole of
# what "curation" used to mean by hand.
THREAD_KEYS = {"ee": "ee_pct", "gs": "gs_pct", "vu": "vu_pct", "gpu": "gpu_pct"}
COUNTER_KEYS = ["rp", "rb", "bar", "drwc", "tc", "tu", "draw"]
MS_KEYS = ["ee_ms", "gs_ms", "vu_ms", "gpu_ms"]
# Fields a human wrote and this tool must not overwrite.
EDITORIAL = ["_note", "scene", "game_file", "savestate", "device", "renderer",
             "observations", "caveats", "notes"]


def mean(values):
    values = [v for v in values if v is not None]
    return round(statistics.fmean(values), 3) if values else None


def summarise(report):
    runs = report.get("runs") or []
    if not runs:
        sys.exit("error: the report contains no runs.")
    out = {
        "ft_p50_ms": mean([r.get("ft_p50_ms") for r in runs]),
        "ft_p95_ms": mean([r.get("ft_p95_ms") for r in runs]),
        "ft_p99_ms": mean([r.get("ft_p99_ms") for r in runs]),
        "ft_avg_ms": mean([r.get("ft_avg_ms") for r in runs]),
        "fps_avg": mean([r.get("fps_avg") for r in runs]),
        "speed_avg_pct": mean([r.get("speed_avg_pct") for r in runs]),
        "gpu_avg_ms": mean([r.get("gpu_avg_ms") for r in runs]),
    }
    return {k: v for k, v in out.items() if v is not None}


def subsystem(report):
    subs = [r.get("subsystem") for r in report.get("runs", []) if r.get("subsystem")]
    if not subs:
        return None
    out = {}
    for key in COUNTER_KEYS + MS_KEYS:
        value = mean([s.get(key) for s in subs])
        if value is not None:
            out[key] = value
    for raw, curated in THREAD_KEYS.items():
        value = mean([s.get(raw) for s in subs])
        if value is not None:
            out[curated] = value
    return out


def main():
    # --dry-run prints JSON that carries the baseline's editorial prose, em dashes and
    # all. A Windows console defaults to a legacy code page and would either mangle it
    # or raise; the file itself is always written as UTF-8.
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

    ap = argparse.ArgumentParser(
        description="Curate one raw benchmark report into a committed baseline.")
    ap.add_argument("report", help="Raw report from tools/bench/results/.")
    ap.add_argument("--label", default="baseline", help="Label for the baseline file.")
    ap.add_argument("--dry-run", action="store_true",
                    help="Print the curated JSON instead of writing it.")
    ap.add_argument("--scene", default=None,
                    help="Scene id, for reports predating --scene. Recorded as supplied "
                         "by hand.")
    ap.add_argument("--commit", default=None,
                    help="Build commit, for reports predating the commit stamp. "
                         "Recorded as supplied by hand.")
    args = ap.parse_args()

    with open(args.report, encoding="utf-8") as f:
        report = json.load(f)

    supplied = []
    scene = report.get("scene_id") or args.scene
    if args.scene and not report.get("scene_id"):
        supplied.append("scene_id")
    if not scene:
        sys.exit("error: the report has no scene_id, so it cannot become a baseline.\n"
                 "       Re-run bench.py with --scene, or pass --scene here if this is\n"
                 "       a report from before that flag existed.")
    # Naming a commit is not enough - the name has to have come from the binary. A
    # commit read off a directory is a guess about which checkout was installed, and
    # with worktrees per subsystem (project-workbook/architecture.md, A01) that guess is wrong
    # exactly when it matters. --commit still overrides, because stating a build by
    # hand is a deliberate act that gets recorded as such; a silent fallback is not.
    source = report.get("armsx2_commit_source")
    if source == "tree" and not args.commit:
        sys.exit("error: this report's commit was inferred from a directory, not read "
                 "from the APK (armsx2_commit_source='tree').\n"
                 "       That is a guess about which build ran, so it cannot become a "
                 "baseline. Rebuild from a tree that\n"
                 "       carries the @@ARMSX2_BUILD@@ tap and re-measure, or pass "
                 "--commit to state the build on the record.")

    # --commit wins over a commit the report only guessed at, otherwise stating one by
    # hand would unlock the check above while quietly recording the guess anyway.
    if args.commit and source != "binary":
        full_commit = args.commit
        if report.get("armsx2_base_commit") != args.commit:
            supplied.append("armsx2_base_commit")
        source = "hand"
    else:
        full_commit = report.get("armsx2_base_commit") or args.commit
        if args.commit and not report.get("armsx2_base_commit"):
            supplied.append("armsx2_base_commit")
            source = "hand"

    commit = (full_commit or "")[:8]
    if not commit:
        sys.exit("error: the report records no armsx2_base_commit. A baseline that "
                 "cannot name its build is not evidence.\n"
                 "       Pass --commit if this predates the stamp.")

    out_dir = os.path.join(BASELINE_DIR, scene)
    out_path = os.path.join(out_dir, f"{commit}-{args.label}.json")

    curated = {}
    if os.path.exists(out_path):
        with open(out_path, encoding="utf-8") as f:
            existing = json.load(f)
        curated = {k: existing[k] for k in EDITORIAL if k in existing}

    curated.update({
        "scene_id": scene,
        "experiment": report.get("experiment"),
        "compare_to": report.get("compare_to"),
        "sweep_order": report.get("sweep_order"),
        "armsx2_base_commit": full_commit,
        "armsx2_commit_source": source,
        "captured": (report.get("timestamp_utc") or "")[:10],
        "config": report.get("config"),
        "derived_from": f"raw/{os.path.basename(args.report)}",
        "fields_supplied_by_hand": supplied or None,
        "summary": summarise(report),
        "p50_spread_pct": report.get("p50_spread_pct"),
        "p50_spread_threshold_pct": report.get("p50_spread_threshold_pct"),
        "stable": report.get("stable"),
    })
    sub = subsystem(report)
    if sub:
        curated["subsystem_per_frame"] = sub

    if args.dry_run:
        print(json.dumps(curated, indent=2, ensure_ascii=False))
        return

    os.makedirs(os.path.join(out_dir, "raw"), exist_ok=True)
    shutil.copy2(args.report, os.path.join(out_dir, "raw",
                                           os.path.basename(args.report)))
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(curated, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"curated {os.path.relpath(out_path, ROOT)}")
    print(f"raw report copied to {scene}/raw/{os.path.basename(args.report)} - commit both")
    if not sub:
        print("note: this report carries no subsystem counters (the APK predates the "
              "GSPERF tap, or the run used the software renderer).")


if __name__ == "__main__":
    main()
