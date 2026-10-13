#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
#
# Opens a new E## entry in project-workbook/experiments.md. Research profile.
#
# This exists because hard rule H7 (RULES.md) requires the prediction to be written
# BEFORE the run, and nothing can verify that after the fact. The only real enforcement
# is a tool that refuses to open an entry without one — so use this instead of editing
# experiments.md by hand, and mark any entry written afterwards as `retro`.
#
#   python tools/new_experiment.py --task T-2 \
#       --title "Skip the load on fully overwritten targets" \
#       --hypothesis "A pass that reloads tiles it is about to overwrite pays a full
#                     tile load for nothing." \
#       --predict "[[corpus:scene-a]]: frame time p50 down 5% or more" \
#       --predict "[[corpus:scene-b]]: unchanged, nothing to save there"
#
# Then run the measurement, fill in Result and Verdict, and — if refuted — put the
# "do not do this" line in the plan file. The linter checks both.

import argparse
import os
import re
import sys

INDEX_EMPTY = "*(empty)*"


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def live(text):
    """Text with fenced blocks and HTML comments removed.

    A template ships its entry skeleton inside a comment. Counting it as a real entry
    makes the first experiment in a project come out as E02.
    """
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    return re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)


def next_id(text):
    used = [int(n) for n in re.findall(r"^## E(\d+)\.", live(text), re.MULTILINE)]
    return max(used) + 1 if used else 1


def known_tasks(backlog, pattern):
    if not os.path.exists(backlog):
        return set()
    return set(re.findall(rf"^\| ({pattern}) \|", live(read(backlog)), re.MULTILINE))


def build_entry(eid, args, today):
    predictions = "\n".join(f"- {p}" for p in args.predict)
    return f"""## {eid}. {args.title}
**Status:** open | **Task:** [[{args.task}]] | **Opened:** {today} |
**Closed:** — | **Commit:** —

**Hypothesis.** {args.hypothesis}

**Prediction.** Written before the run:
{predictions}
- Threshold: computed by the comparison tool from the spreads of the runs actually
  compared, not fixed here in advance

**Method.** {args.method}

**Result.** *(pending — one headline line per configuration, each linking its report)*

**Verdict.** *(pending)*

**Traces.** *(pending)*
"""


def main():
    ap = argparse.ArgumentParser(
        description="Open an E## entry with its prediction recorded up front.")
    ap.add_argument("--task", required=True, help="Backlog task id this serves, e.g. T-2.")
    ap.add_argument("--title", required=True,
                    help="What is being tested — a claim, not a topic.")
    ap.add_argument("--hypothesis", required=True,
                    help="The mechanism: why a gain should follow from how the system works.")
    ap.add_argument("--predict", action="append", default=[], metavar="TEXT",
                    help="One prediction per configuration. Repeatable. Required.")
    ap.add_argument("--method",
                    default="*(configurations, what changed, run order — fill in)*",
                    help="How it will be measured.")
    ap.add_argument("--docs", default="project-workbook", help="Path to project-workbook/.")
    ap.add_argument("--task-pattern", default=r"[A-Z]-[0-9a-z]+",
                    help="Shape of a task id in the backlog table.")
    ap.add_argument("--date", default=None, help="Override the opening date (YYYY-MM-DD).")
    args = ap.parse_args()

    experiments = os.path.join(args.docs, "experiments.md")
    backlog = os.path.join(args.docs, "plan", "backlog.md")

    if not os.path.exists(experiments):
        sys.exit(f"error: {experiments} does not exist.\n"
                 f"       Create it from templates/experiments.md first — a register is\n"
                 f"       created on its first real entry, and this is it.")

    if not any(p.strip() for p in args.predict):
        sys.exit("error: at least one non-empty --predict is required.\n"
                 "       A verdict without a prediction recorded beforehand does not\n"
                 "       count (rule H7): any numbers would get an explanation fitted to\n"
                 "       them after the fact. Decide what you expect, then measure.")

    tasks = known_tasks(backlog, args.task_pattern)
    if tasks and args.task not in tasks:
        sys.exit(f"error: task '{args.task}' is not in {backlog}.\n"
                 f"       known: {', '.join(sorted(tasks))}")

    if args.date:
        today = args.date
    else:
        from datetime import date
        today = date.today().isoformat()

    text = read(experiments)
    eid = f"E{next_id(text):02d}"
    index_line = f"- **{eid}** · open · {args.title} · [[{args.task}]]"

    if INDEX_EMPTY in text:
        text = text.replace(INDEX_EMPTY, index_line, 1)
        # A "no experiments yet" note explains an empty register. With an entry above
        # it, it is simply false — and nothing else would ever remove it.
        text = re.sub(r"\*\*No experiments yet\.\*\*.*?(?=\n## |\Z)", "", text,
                      flags=re.DOTALL)
    else:
        lines = text.splitlines()
        existing = [i for i, l in enumerate(lines) if re.match(r"^- \*\*E\d+\*\*", l)]
        if existing:
            lines.insert(max(existing) + 1, index_line)
        else:
            # No index lines yet: put it under the Index heading.
            head = next((i for i, l in enumerate(lines)
                         if re.match(r"^##+\s*Index\b", l)), None)
            if head is None:
                sys.exit("error: experiments.md has no '## Index' section to write into.")
            lines.insert(head + 2, index_line)
        text = "\n".join(lines) + "\n"

    text = text.rstrip() + "\n\n---\n\n" + build_entry(eid, args, today)
    # Removing the "no experiments yet" note can leave its separator behind.
    text = re.sub(r"\n---\s*\n+---\s*\n", "\n\n---\n\n", text)
    with open(experiments, "w", encoding="utf-8") as f:
        f.write(text)

    print(f"opened {eid} in {experiments} (status: open)")
    print("Next: take the measurement, then fill in Result and Verdict.")
    print("If it comes back refuted, add the 'do not do this' line to the plan file:")
    print("the linter will not let the entry close without it.")


if __name__ == "__main__":
    main()
