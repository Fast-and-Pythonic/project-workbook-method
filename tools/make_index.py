#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
#
# Index generator for the registers of an project-workbook/ document set.
#
# Rule H1 says every register entry has an index line and every index line has an entry,
# and lint_workbook.py checks it. This is the other half: the thing that produces one. A rule
# with a check and no producer is a rule that reports the same defect every session —
# nobody assembles twenty-five index lines by hand, and a hand-assembled index drifts from
# its entries by the next one.
#
#   python tools/make_index.py                 # every register named in the config
#   python tools/make_index.py --register G    # just the gotchas
#   python tools/make_index.py --check         # exit 1 if an index is out of date
#
# --check writes nothing and is what a pre-commit hook runs.

import argparse
import os
import re
import sys

from lint_workbook import (Ctx, load_config, md_files, read, register_entries,
                       significant_words, strip_code)

# An index line: "- **G07** · Sourcemaps break MAIN-world injection". The separator is
# cosmetic — lint_workbook only requires the "- **ID**" opening — but it stays consistent
# within a document set, so it is taken from the existing index when there is one.
DEFAULT_SEP = "·"
INDEX_LINE_RE = re.compile(r"^- \*\*([A-Za-z]+\d+)\*\*\s*(\S)?")
SECTION_RE = re.compile(r"^## .*\]\(([^)]+\.md)\)")


def entry_num(eid):
    return int(re.sub(r"\D", "", eid) or 0)


def existing_sections(path, text):
    """file -> heading line, for an index already grouped by area.

    Regenerating must not rename the areas: those names were chosen by a person and say
    more than a file stem ever will.
    """
    out = {}
    for line in text.splitlines():
        m = SECTION_RE.match(line)
        if m:
            target = os.path.normpath(os.path.join(os.path.dirname(path), m.group(1)))
            out.setdefault(target, line)
    return out


def existing_sep(text):
    for line in text.splitlines():
        m = INDEX_LINE_RE.match(line)
        if m and m.group(2) and not m.group(2).isalnum():
            return m.group(2)
    return DEFAULT_SEP


def existing_lines(text):
    """id -> the index line as it stands, so a line that is still true can be kept."""
    out = {}
    for line in text.splitlines():
        m = INDEX_LINE_RE.match(line)
        if m:
            out.setdefault(m.group(1), line.rstrip())
    return out


def section_heading(ctx, path, target):
    """A heading for an area that has none yet: the file stem, and a link to it."""
    rel = os.path.relpath(target, os.path.dirname(path)).replace("\\", "/")
    name = os.path.splitext(os.path.basename(target))[0].replace("-", " ").replace(
        "_", " ")
    return f"## {name[:1].upper()}{name[1:]} — [{rel}]({rel})"


def build_block(ctx, prefix, path, text):
    """The index a register's entries imply, as a list of lines."""
    entries = register_entries(ctx, prefix)
    if not entries:
        return []
    sep = existing_sep(text)
    known = existing_sections(path, text)
    order = list(known)  # areas keep the order a person put them in
    standing = existing_lines(text)

    by_file = {}
    for eid, places in entries.items():
        # A duplicated id is lint's error to report, not this tool's to silently pick a
        # winner for. Index it under the first file and leave the check to complain.
        f, title = places[0]
        by_file.setdefault(os.path.normpath(f), []).append((eid, title))
    for f in sorted(by_file, key=lambda f: min(entry_num(e) for e, _ in by_file[f])):
        if f not in order:
            order.append(f)

    def line_for(eid, title):
        """Keep the standing line while it is still true; write a fresh one otherwise.

        An index line carries ID, status and title (the standard's glossary), and a
        project may add fields of its own — a `Portable` mark at the end, a task id in
        the middle. Regenerating from the heading alone silently drops all of that, so
        the test for "still true" is the same one lint's check 3 uses: does the line
        share any significant word with its heading? Nothing is parsed into fields,
        because the shape differs between registers and between projects.

        A line that shares nothing is a rename that went halfway, which is the one case
        worth rewriting. Syncing the index is this tool's job; reformatting it is not.
        """
        old = standing.get(eid)
        if old:
            rest = old.split(f"**{eid}**", 1)[-1]
            if significant_words(rest) & significant_words(title):
                return old
        return f"- **{eid}** {sep} {title}".rstrip()

    def lines_for(f):
        return [line_for(eid, title)
                for eid, title in sorted(by_file[f], key=lambda p: entry_num(p[0]))]

    if len(by_file) == 1:
        return lines_for(next(iter(by_file)))

    block = []
    for f in order:
        if f not in by_file:
            continue  # an area whose entries have all moved away
        if block:
            block.append("")
        block.append(known.get(f) or section_heading(ctx, path, f))
        block.append("")
        block += lines_for(f)
    return block


def splice(lines, block, prefix):
    """Put the block where the index belongs, replacing one that is already there."""
    entry_re = re.compile(rf"^## {prefix}\d+\s*[.:]")
    head_end = next((i for i, ln in enumerate(lines) if entry_re.match(ln)), len(lines))

    marks = [i for i in range(head_end)
             if INDEX_LINE_RE.match(lines[i]) or SECTION_RE.match(lines[i])]
    if marks:
        start, end = marks[0], marks[-1] + 1
    else:
        # No index yet. Before the first heading of the head — after the title and
        # whatever prose explains the register, which is where a reader looks for it.
        start = next((i for i in range(head_end) if lines[i].startswith("## ")), head_end)
        end = start
        block = block + [""]
    return lines[:start] + block + lines[end:]


def process(ctx, prefix, check):
    path = ctx.registers[prefix]
    if not os.path.exists(path):
        return None
    text = read(path)
    block = build_block(ctx, prefix, path, strip_code(text))
    if not block:
        return None
    lines = text.splitlines()
    new = splice(lines, block, prefix)
    # Trailing blank lines accumulate otherwise: the block is spliced between a title and
    # a heading that each bring their own.
    out = re.sub(r"\n{3,}", "\n\n", "\n".join(new).rstrip() + "\n")
    if out == text:
        return False
    if not check:
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(out)
    return True


def main():
    ap = argparse.ArgumentParser(
        description="Generate the index of an project-workbook/ register from its entries.")
    ap.add_argument("--config", default=os.path.join(os.path.dirname(__file__),
                                                     "lint_workbook.toml"))
    ap.add_argument("--root", help="project root (default: from config)")
    ap.add_argument("--docs", help="path to project-workbook/, relative to root")
    ap.add_argument("--profile", choices=["engineering", "research"])
    ap.add_argument("--register", action="append", metavar="PREFIX",
                    help="only this register; repeatable (default: all)")
    ap.add_argument("--check", action="store_true",
                    help="write nothing; exit 1 if an index is out of date")
    args = ap.parse_args()

    root, docs = args.root, args.docs
    if docs and os.path.isabs(docs):
        root, docs = root or os.path.dirname(os.path.abspath(docs)), \
            os.path.basename(os.path.normpath(docs))

    cfg = load_config(args.config, [
        ("paths", "root", root),
        ("paths", "docs", docs),
        ("profile", "name", args.profile),
    ])
    if root is None and not os.path.isabs(cfg["paths"]["root"]) \
            and os.path.exists(args.config):
        cfg["paths"]["root"] = os.path.normpath(os.path.join(
            os.path.dirname(os.path.abspath(args.config)), cfg["paths"]["root"]))
    ctx = Ctx(cfg)

    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, OSError):
            pass

    if not os.path.isdir(ctx.docs):
        print(f"nothing to index: {ctx.rel(ctx.docs)} does not exist")
        return 0

    wanted = args.register or list(ctx.registers)
    stale = 0
    for prefix in wanted:
        if prefix not in ctx.registers:
            print(f"warning  no register {prefix!r} in this configuration")
            continue
        changed = process(ctx, prefix, args.check)
        name = ctx.rel(ctx.registers[prefix])
        if changed is None:
            continue
        if changed:
            stale += 1
            print(f"{'stale' if args.check else 'wrote'}    {name}")
        else:
            print(f"ok       {name}")
    if args.check and stale:
        print(f"\n{stale} index(es) out of date — run make_index.py")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
