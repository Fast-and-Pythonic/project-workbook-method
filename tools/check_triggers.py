#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
#
# Update-trigger reminder for a commit, the harness-neutral layer of RULES.md §2.
#
# The trigger table has no checking mechanism of its own: nothing can tell that a debugging
# session ran past thirty minutes or that a decision was settled in a discussion. What a
# commit can tell is the cheap signal underneath most of them: code changed and the
# workbook did not. That is not a defect — most such commits are routine — so this script
# warns and lets the commit through; it puts the table in front of the person at the one
# moment the entry can still go into the same commit.
#
#   python tools/check_triggers.py              # the staged snapshot, from a pre-commit hook
#   python tools/check_triggers.py --strict     # exit 1 instead of warning
#
# Scope. Every `project-workbook/` folder tracked in the repository covers the tree it sits
# in, so a repository holding several projects, each with its own workbook, is checked per
# project: code staged under a project whose workbook is untouched is reported for that
# project alone. Code outside every workbook's tree is not judged.
#
# "Code" is any staged path (added, changed, renamed or deleted) outside the workbook that
# is not Markdown and not under `_backups/`; --ignore adds glob patterns to that.

import argparse
import fnmatch
import os
import re
import subprocess
import sys

DOCS = "project-workbook"
RULES = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, "RULES.md")
LISTED = 8  # staged paths named per project before "and N more"


def git(*args, cwd=None):
    out = subprocess.run(["git", *args], cwd=cwd, capture_output=True, check=True)
    return out.stdout.decode("utf-8", errors="replace")


def nul_list(text):
    return [p for p in text.split("\0") if p]


def workbook_scopes(paths, docs):
    """The trees the workbooks cover: '' for one at the root, 'sub/dir' for one below."""
    scopes = set()
    for path in paths:
        parts = path.split("/")
        if docs in parts[:-1]:
            scopes.add("/".join(parts[:parts.index(docs)]))
    return scopes


def scope_of(path, scopes):
    """The deepest workbook tree the path is in, or None."""
    best = None
    for scope in scopes:
        if scope == "" or path == scope or path.startswith(scope + "/"):
            if best is None or len(scope) > len(best):
                best = scope
    return best


def in_workbook(path, scope, docs):
    prefix = f"{scope}/{docs}/" if scope else f"{docs}/"
    return path.startswith(prefix)


def is_code(path, ignore):
    if path.lower().endswith(".md"):
        return False
    if "_backups" in path.split("/")[:-1]:
        return False
    return not any(fnmatch.fnmatch(path, pat) for pat in ignore)


def untouched(staged, scopes, docs, ignore):
    """scope -> the code paths staged under it, for each scope whose workbook is untouched."""
    code, touched = {}, set()
    for path in staged:
        scope = scope_of(path, scopes)
        if scope is None:
            continue
        if in_workbook(path, scope, docs):
            touched.add(scope)
        elif is_code(path, ignore):
            code.setdefault(scope, []).append(path)
    return {s: ps for s, ps in sorted(code.items()) if s not in touched}


def trigger_rows(rules_path):
    """The untagged rows of RULES.md §2 as "what happened -> action", or [] if unreadable.

    Read from the standard rather than copied here, so the reminder cannot drift from the
    table. Rows tagged [E] or [R] belong to the extended and research profiles and are left
    out: the reminder is read at every such commit and has to stay short.
    """
    try:
        with open(rules_path, encoding="utf-8") as f:
            text = f.read()
    except OSError:
        return []
    m = re.search(r"^## 2\. .*?$(.*?)^## ", text, re.S | re.M)
    if not m:
        return []
    rows = []
    for line in m.group(1).splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 2 or set(cells[0]) <= set("-: ") or cells[0] == "What happened":
            continue
        if len(cells) > 2 and cells[2]:
            continue
        clean = [re.sub(r"\*\*|`", "", c) for c in cells[:2]]
        rows.append(f"{clean[0]} -> {clean[1]}")
    return rows


def fallback_rows(ts_path):
    """The FALLBACK_ROWS copy in the workbook-triggers mod, as strings."""
    with open(ts_path, encoding="utf-8") as f:
        text = f.read()
    head = "export const FALLBACK_ROWS: readonly string[] = ["
    if head not in text:
        return []
    block = text.split(head, 1)[1].split("\n]", 1)[0]
    return [m[1:-1] for m in re.findall(r"^  (['\"].*['\"]),$", block, re.M)]


def verify_fallback(ts_path, rules_path):
    """The standard's own pre-commit: the mod's copy of the table still matches RULES.md."""
    rows, copy = trigger_rows(rules_path), fallback_rows(ts_path)
    if rows == copy:
        return 0
    print(f"check_triggers: FALLBACK_ROWS in {ts_path} no longer matches RULES.md section 2;"
          " copy the untagged rows of the table into it.", file=sys.stderr)
    return 1


def report(found, docs, rows):
    lines = []
    for scope, paths in found.items():
        where = f"{scope}/" if scope else "the repository"
        book = f"{scope}/{docs}/" if scope else f"{docs}/"
        named = ", ".join(paths[:LISTED])
        more = f" and {len(paths) - LISTED} more" if len(paths) > LISTED else ""
        lines.append(f"check_triggers: code staged in {where}, {book} untouched ({named}{more}).")
    lines.append("If any of these happened in the work behind this commit, its entry belongs in the")
    lines.append("same commit (RULES.md section 2, update triggers):")
    if rows:
        lines += [f"  - {r}" for r in rows]
    else:
        lines.append("  (the table could not be read; see RULES.md §2 of the standard)")
    lines.append("None did? Commit as it is: this is a reminder, not a gate.")
    return ascii_only("\n".join(lines))


def ascii_only(text):
    """The text as any console prints it: a hook's stderr reaches a Windows console in its
    code page, where an em dash or an arrow comes out as mojibake."""
    for a, b in (("—", "-"), ("–", "-"), ("→", "->"), ("§", "section "),
                 ("“", '"'), ("”", '"'), ("‘", "'"), ("’", "'")):
        text = text.replace(a, b)
    return text.encode("ascii", "replace").decode("ascii")


def main():
    ap = argparse.ArgumentParser(
        description="Warn when staged code changes leave the project workbook untouched.")
    ap.add_argument("--root", help="repository root (default: the current repository's)")
    ap.add_argument("--docs", default=DOCS, help=f"workbook folder name (default: {DOCS})")
    ap.add_argument("--ignore", action="append", default=[], metavar="GLOB",
                    help="staged paths matching this are not code; repeatable")
    ap.add_argument("--rules", default=RULES, help="RULES.md to read the trigger table from")
    ap.add_argument("--strict", action="store_true", help="exit 1 instead of warning")
    ap.add_argument("--verify-fallback", metavar="REGISTER_TS",
                    help="only check that the mod's FALLBACK_ROWS match RULES.md, then exit")
    args = ap.parse_args()
    if args.verify_fallback:
        return verify_fallback(args.verify_fallback, args.rules)

    try:
        root = args.root or git("rev-parse", "--show-toplevel").strip()
        staged = nul_list(git("diff", "--cached", "--name-only", "-z",
                              "--diff-filter=ACDMRT", cwd=root))
        tracked = nul_list(git("ls-files", "-z", cwd=root))
    except (OSError, subprocess.CalledProcessError) as exc:
        print(f"check_triggers: git unavailable here, skipped ({exc})", file=sys.stderr)
        return 0

    scopes = workbook_scopes(tracked + staged, args.docs)
    found = untouched(staged, scopes, args.docs, args.ignore)
    if not found:
        return 0
    print(report(found, args.docs, trigger_rows(args.rules)), file=sys.stderr)
    return 1 if args.strict else 0


if __name__ == "__main__":
    sys.exit(main())
