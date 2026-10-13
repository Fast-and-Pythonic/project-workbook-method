# tools

## Installing them

Running the scripts by path works, and is what every project's `_meta.md` documents:

```bash
python <standard>/tools/lint_workbook.py --config tools/lint_workbook.toml
```

That is fine on one machine and exactly wrong for a project going public: a contributor
who clones it gets no checker at all, and the path points into somebody's directory
layout. So the tools are installable, and then a project depends on a *version* of them
instead:

```bash
pipx install git+https://github.com/Fast-and-Pythonic/project-workbook-method
workbook-lint  --config tools/lint_workbook.toml
workbook-index --config tools/lint_workbook.toml
```

No dependencies — both are standard library only, so installing them cannot disturb a
project's own environment. Reading a `lint_workbook.toml` wants Python 3.11 for `tomllib`;
on anything older the tools say so and fall back to defaults and command-line flags
rather than failing.

**Why the tools may be copied and the prose may not.** The standard is two things, and
"never copy it" belongs to only one of them. `RULES.md`, `FORMATS.md` and
`METHODOLOGY.md` are prose: copy those and the copies drift until neither can be
trusted, which is the disease the method was written against. `lint_workbook.py` is code,
and a second copy of code is not a second source of truth — it is version skew, which
ordinary release machinery already solves. Pin a version, install it, and the question
stops being interesting. What is *not* acceptable is the third option, and one project
had it: a hand-modified copy of the linter, 304 lines running six of eighteen checks,
reporting a clean run on a document set nobody was checking.

## `lint_workbook.py`

Checks what can be checked about a document set. Backs the hard rules in
[RULES.md](../RULES.md); the full list of checks is there, with the reason each exists.

```bash
python tools/lint_workbook.py                                  # uses lint_workbook.toml
python tools/lint_workbook.py --docs project-workbook --profile research
python tools/lint_workbook.py --docs /path/to/other/project-workbook    # audit another project
```

Exit code 0 means clean; warnings are allowed. Exit code 1 means at least one error.

If the configured document set does not exist yet, the linter says so and exits 0 — that
is the normal state of a project on its first day, and of any repository that installed
the pre-commit hook before writing anything. A path passed explicitly with `--docs` is
held to a stricter standard and fails, because there a missing directory is a typo. The
distinction matters: a hook that blocks a commit for having nothing to check teaches
people to pass `--no-verify`, and that disables it for good.

Requires Python 3.11+ for `tomllib`. On an older interpreter it still runs, using the
built-in defaults plus command-line flags, and says so.

**Configuration** is [lint_workbook.toml](lint_workbook.toml), beside the script. It exists to
teach the linter your layout and the metric names your project uses; every value has a
default.

**Documents not in English.** The checks that look for a field — `Prediction`,
`Status`, `Acceptance criterion` — match a literal label. Set them under `[labels]` in
the config if your documents are written in another language. Leaving the defaults does
not produce errors; it produces silence, which looks exactly like passing. The same goes
for `numbers.metric_names`: a metric the linter does not know is a number it will not ask
for a source for.

**A split register.** When a register has outgrown one file (RULES.md, "Scaling"), keep
the index in the register file, move the bodies into a directory and name it in
`register_bodies`. Group the index under headings that link to each area's file —
`## Build — [subsystems/build.md](subsystems/build.md)` — and check 17 holds every index
line to the file its entry is in. A prefix may be longer than one letter (`EG`), and the
`[registers]` table replaces the defaults rather than extending them, so a document set
with its own prefixes lists only those.

**Another document set.** `--config path/to/lint_workbook.toml` points the linter at a
config kept beside the documents rather than beside the script. A relative `root` in a
config is resolved against the config file, so the command works from any directory.

**The tier.** `[project] tier` in the config, or `--tier S|M|L`, sets the size tier
(RULES.md, "Tiers and scaling"). It moves the `status.md` limit and decides which files
are expected; anything set explicitly under `[limits]` wins over it. The tier is printed
on the summary line, so a run says what it held the project to.

**Documented paths.** A path in backticks is tried against `path_roots` first and then
looked for as the tail of any path in the tree, because documentation names a file the
way a person does — `model/Screen.kt`, not the whole path from a source root. Generated
trees are skipped via `ignore_dirs`: a path that resolves only inside `build/` is not
evidence that the file still exists. This is deliberately generous. The check exists to
catch a path pointing at nothing, not to police how paths are written — held to the
stricter reading it produced twelve false errors against four real ones on the first
large project it met, and a linter that cries wolf is one the next session stops reading.

**Adding a check.** The bar is that it backs a hard rule or catches rot that has already
happened. A check nobody's documentation has ever failed is a check that will fire on a
false positive first and be disabled second.

**Releasing a check.** A new error-level check is a tightening change, and by
[DEVIATIONS.md §6](../DEVIATIONS.md#6-changing-the-standard-itself) it ships as a warning
and is promoted once every consumer is clean. Check 18 is the current example. Sweep the
consumers before and after: a correctly released check moves the warning count and leaves
the error count alone.

## `make_index.py`

Generates a register's index from its entries — the producer behind rule H1, which
lint_workbook.py only checks.

```bash
python tools/make_index.py                 # every register in the config
python tools/make_index.py --register G    # just the gotchas
python tools/make_index.py --check         # write nothing; exit 1 if an index is stale
```

Idempotent: a second run changes nothing, so it is safe from a hook. It sorts entries by
number, and on a register already split by area it keeps the existing section headings and
their order — those names were chosen by a person and say more than a file stem does.

A check with no producer reports the same defect every session and never fixes it. Nobody
assembles twenty-five index lines by hand, and an index that was assembled by hand drifts
from its entries by the next session. `--check` in the pre-commit hook is what keeps the
two in step.

## `new_experiment.py`

Opens an `E##` entry: allocates the number, writes the index line, and **refuses to
proceed without a prediction**. Research profile.

```bash
python tools/new_experiment.py --task T-2 \
  --title "Skip the load on fully overwritten targets" \
  --hypothesis "The tiler can drop the load for targets the frame rewrites entirely." \
  --predict "[[corpus:scene-a]]: frame time p50 down 5% or more"
```

This tool is the mechanism behind hard rule H7. Nothing can verify after the fact that a
prediction was written before its run, so the enforcement has to happen at the moment of
creation — which means the entry must be cheaper to create with the tool than by hand.
That is the whole design goal. An entry written by hand afterwards must carry the `retro`
marker.

## `check_triggers.py`

The harness-neutral layer of the update triggers ([RULES.md §2](../RULES.md#2-update-triggers)).
Nothing can tell that a debugging session ran past thirty minutes or that a decision was
settled; a commit can tell the cheap signal under most of them: code changed and the
workbook did not. When the staged snapshot shows that, the script prints the trigger table
— read from `RULES.md` of the standard it sits in, so it cannot drift from it — at the one
moment the entry can still go into the same commit.

```bash
python tools/check_triggers.py              # what a pre-commit hook runs
python tools/check_triggers.py --strict     # exit 1 instead of warning
```

It warns and exits 0: most code commits are routine, and a gate that fires on routine
commits teaches `--no-verify`. Each tracked `project-workbook/` covers the tree it sits
in, so a repository holding several projects is judged per project. Code is any staged
path outside the workbook that is not Markdown and not under `_backups/`; `--ignore GLOB`
adds more. Installed through `pipx` it is `workbook-triggers`; there it has no `RULES.md`
beside it and names the section instead of printing the table. The Claude Code layer
over the same table is [mods/workbook-triggers/](mods/workbook-triggers/README.md).

## `hooks/pre-commit`

Runs the linter before every commit, then `check_triggers.py` as a reminder that never
fails the commit. This one is the standard's own, with `tools/` beside it; a project that
uses the standard from outside copies [templates/pre-commit](../templates/pre-commit)
instead, which finds the standard beside or above the checkout, or the installed
commands, and lets the commit through when there is neither. Install once:

```bash
git config core.hooksPath tools/hooks
```

Finding a problem before you write the commit message is cheaper than after. If the
project is not under version control, say so in `_meta.md` and record which hard rules
are consequently demoted to advice — see [DEVIATIONS.md](../DEVIATIONS.md).

## `mods/workbook-loader/`

A Claude Code mod that does step 1 of the session protocol in full: at session start it
puts `start.md`, `status.md` and the top four `journal.md` entries in front of the first
turn, with no size cap — a mod's context is not cut to a preview the way a command hook's
output is. Where the command hook below also runs, the mod drops that hook's copy of
`start.md`, so the agent sees one. If the mod fails, the hook's copy stays: that is the
fallback, not a bug. Enabling it is the person's choice: a repository cannot turn a mod on
for a visitor. See [mods/workbook-loader/README.md](mods/workbook-loader/README.md).

## `mods/workbook-triggers/`

A Claude Code mod for the update triggers. It counts cheap signs during the session — code
edited with no workbook edit, the same error failing again and again, half an hour of
work — and when one crosses its threshold at the end of a turn it asks a fork of the
session, served from the prompt cache, whether a trigger of RULES.md §2 fired. On a yes it
sends the agent back to write the entry before it stops; the mod itself writes nothing.
See [mods/workbook-triggers/README.md](mods/workbook-triggers/README.md).

## `hooks/claude-code-session-start.sh`

The fallback where mods are unavailable (cloud sessions, older Claude Code). Loads `project-workbook/start.md` into a Claude Code session before its first turn. This is the
mechanism behind step 1 of the session protocol ([RULES.md §3](../RULES.md#3-session-protocol)):
without it, reading `start.md` rests on an instruction in the root pointer, and an agent
that judges a task too small to count as "starting work" skips it — in the case that
prompted this, on exactly the edit whose right file `start.md` would have named.

Install it as a `SessionStart` hook; the header of the script has the snippet. It needs
`jq`, finds `project-workbook/` in the session's directory or at the root of its git repository,
and says nothing where there is none, so a global install is harmless.

It loads `start.md` alone and caps it at `MAX_BYTES` (8000 by default), cutting at a whole
line and saying so. Claude Code replaces a hook output of roughly 10 KB or more with a
2 KB preview, and a preview is the worst outcome — the head of the file is there, so it
reads as loaded. When checking a hook like this, ask the agent to quote the **last** line
of what it was given; the first line is in the preview either way.

Other tools: the same idea applies wherever the tool can run a command at session start
and hand its output to the agent. Where it cannot, step 1 remains advice, and should be
called that.

## `hooks/claude-code-guard-pointer.sh`

Stops a Claude Code edit to the root pointer (`AGENTS.md`, or a `CLAUDE.md` not yet renamed) of a project kept to this standard and
asks the person, showing why: the pointer holds no knowledge of its own
([METHODOLOGY §5](../METHODOLOGY.md#5-tool-independence)). The pointer is the one file a
session knows is always loaded, so "write this down so it does not happen again" tends to
land there; lint check 19 catches the result at commit time, this catches the moment of
writing.

Install it as a `PreToolUse` hook; the header of the script has the snippet. It needs
`jq` and acts only where `project-workbook/start.md` sits next to the pointer, so a global
install is harmless. It asks rather than refuses, because editing the pointer is
sometimes the task; with no one to ask, as under `claude -p`, the ask becomes a refusal.
Shell writes are matched by a coarse pattern, and one that slips past it is not caught.
Hooks are read at session start: the session that installs it is not yet guarded.
