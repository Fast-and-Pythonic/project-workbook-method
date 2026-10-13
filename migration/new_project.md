# Scenario: a new project

You are starting fresh, or the project exists but has no documentation worth keeping.

## Day one — twenty minutes

Create four files and stop.

**Root pointer** (`AGENTS.md`) from
[templates/root_pointer.md](../templates/root_pointer.md). Five to fifteen lines: what
the project is, the order to read `project-workbook/start.md` first, and only the rules that pass
the admission test in [METHODOLOGY §5](../METHODOLOGY.md#5-tool-independence) — each
naming where in `project-workbook/` it is stated.

**`ONBOARDING.md`** at the root, from [templates/ONBOARDING.md](../templates/ONBOARDING.md):
for the person who clones the project rather than for the agent — what works with nothing
installed, the commit hook to install, the mods to enable. Short; delete what does not apply.

**`project-workbook/overview.md`** from the template. Purpose, stack, structure, and — the field
people skip — **invariants**: the rules of the project that no linter can check and that
a session must stop and ask about rather than work around. On day one you may have one.
Write it anyway.

**`project-workbook/start.md`** from the template. Map, situational guide, three critical facts.
On day one the guide has two lines and the facts are thin. That is correct; it grows by
being wrong in a way you notice.

**`project-workbook/_meta.md`** from the template: the profile, the language, the link to the
standard. Twelve lines.

Do not create `gotchas.md`, `architecture.md` or `status.md` yet. There is nothing to put
in them, and empty files teach an agent the wrong thing.

## Choose a profile

**Engineering** if the work is "build this, make it correct, keep it working". This is
most projects.

**Research** if the work is "test this and find out" — performance, tuning, data
pipelines, anything where a metric decides whether a change was worth making. It is
heavier; turn it on when the first real hypothesis appears, not in anticipation.

You can start engineering and add the research profile later. That is the common path,
and it is how the research profile came to exist in the first place.

## Wire up the linter

Copy `tools/lint_workbook.py` and `tools/lint_workbook.toml`, set the paths, and run it. On a
three-file document set it should pass immediately.

If the project is under version control, install the pre-commit hook now, while it is a
one-line change. If it is not under version control, say so in `_meta.md` and list which
hard rules are consequently demoted to advice — see
[DEVIATIONS.md §5](../DEVIATIONS.md).

## The first month

Files appear on their triggers, not on a schedule:

| When this happens | This appears |
|-------------------|--------------|
| Debugging ran past 30 minutes with a non-obvious cause | `gotchas.md`, entry `G01` |
| A decision settled, with a real alternative rejected | `architecture.md`, entry `A01` |
| Something turned out to be load-bearing and fragile | `status.md`, Fragile points |
| Something is worth remembering a month from now | `journal.md`, first entry |

By the end of the first month a healthy project has four or five files, six to ten
entries, and a `start.md` whose situational guide has been rewritten twice. A project
that still has exactly the three files from day one either had a very quiet month or is
not walking the trigger table.

## The failure mode to watch for

Writing the structure and never filling it. The structure is the cheap part; the
discipline of capture-at-friction is the whole method. If after a month there are no
`G##` entries, the problem is not the template — it is that nobody stopped to write one
while the pain was fresh.
