# METHODOLOGY — the core of the Project Workbook standard

Project documentation written to be read by an AI agent, and by the humans who work
alongside one.

This file holds what is true for every project. The normative part — the inventory,
the triggers, the hard rules and their checking mechanisms — is in
[RULES.md](RULES.md). Entry anatomy is in [FORMATS.md](FORMATS.md). Two profiles
adapt the set to a kind of work: [engineering](profiles/engineering.md) and
[research](profiles/research.md).

---

## 1. The problem

An agent starts every session with no memory of the last one. It compensates by
reading the code, and reading the code is genuinely good at recovering **what** the
project does. It is structurally unable to recover:

- why a thing was built this way, and what was rejected on the way there;
- what was tried, measured and thrown away;
- which innocuous-looking line is load-bearing;
- what breaks if you change this, and how you would find out.

That second class of knowledge is produced by hours of debugging and measurement, and
it evaporates when the session ends. Recreating it costs the same hours again. Every
mechanism in this standard exists to move a piece of it out of a session and into a
file at the moment it is cheapest to record — right after it has been paid for.

Two things follow, and both are worth stating plainly because both are easy to get
backwards.

**Context inheritance is not a substitute.** Forking a session, sharing a context
window, warming a prompt cache — these distribute knowledge *horizontally*, across
agents working now. They do nothing *vertically*, across sessions in time. They also
inherit quality: a root context that reconstructed the project by reading code passes
that reconstruction, errors included, to everything downstream. Feeding a good root is
the highest-leverage move available, and that is what `project-workbook/` is for.

**Documentation that lies is worse than none.** The agent will believe it and break
something that works. This is not a slogan; it is the constraint that shapes the rest
of the standard, and the reason so much of what follows is about *removing* and
*checking* rather than about writing more.

---

## 2. Principles

### 2.1. Only what cannot be derived from the code

File layout, function names, imports, signatures, obvious type hierarchies — an agent
reads these from the source faster and more accurately than from a document that lags
behind. Documenting them is duplication with a short shelf life.

Document the second layer: **why** it is like this, **what happens if you change it**,
**what alternatives were considered**, **where the traps are**.

The one exception is a high-level directory tree in `overview.md`. That is a map, not
a duplicate.

### 2.2. Separate by volatility

Stable knowledge (architecture, conventions) lives apart from volatile knowledge
(current state, priorities). Mixing them means re-reading the architecture on every
status update — and stale architecture rots slowly and invisibly.

Mixing also lets the growing class crowd out the rewritable one. In the project this
standard was first derived from, `status.md` reached 349 lines against its own 150-line
limit, and 68% of it was an append-only decision log that had nowhere else to go. The
cure is the split in [RULES.md](RULES.md): `status.md` is state, rewritten in place;
`journal.md` is chronicle, append-only.

### 2.3. Layered loading

An agent reads with priorities. `start.md` is short and always read. Everything else
loads on a trigger from the situational guide inside it.

A large file that is "sometimes needed" is a file the agent will read at the worst
possible moment, or not at all. Size must match load frequency; when a file outgrows
its band, split it or move part of it onto a subsystem page.

**The limits are not defending a context budget, and it is worth being exact about
that.** Measured across the six document sets this standard is kept on, everything a
session always reads — `start.md`, `status.md`, the top journal entries and the register
indexes — comes to between 8 and 20 KB, and the heaviest set including `overview.md` is
about 6k tokens. That is roughly 3 % of a 200K window. No plausible relaxation of these
numbers would cost anything a reader could notice.

So a limit here has to earn its place some other way, and exactly one of them does.
**`status.md`'s limit is a forcing function**: its job is to refuse an append-only
chronicle, so that the chronicle goes to `journal.md` instead of quietly crowding out the
state. That is principle [2.2](#22-separate-by-volatility) with a mechanism attached, and
it works — in the two projects where it was applied, the decision log moved out because
the limit would not accommodate it, not because anyone decided to tidy up. Both then
settled at 79 and 80 lines of actual state, against three unconstrained document sets
that came in at 37, 48 and 55. The number is about the natural size of state, not below
it.

Every other limit is **advice**: "this is getting long, consider splitting it." The
linter says so — `limits.enforce` names the forcing ones and everything else warns —
because an error raised for advice teaches the next session to stop reading the output,
which costs far more than a long `overview.md` ever will.

The growth that does need watching is structural rather than numeric: a file every
session reads must not be the file that accumulates one section per subsystem. The fix at
every size is the same move — what belongs to one area goes on that area's page, and the
always-loaded file keeps only what crosses areas. See
[RULES.md §6](RULES.md#6-tiers-and-scaling).

### 2.4. Capture at friction

The most valuable knowledge appears at the moment of pain — right after a long
debugging session, right after a measurement contradicts an expectation. If it is not
recorded then, it is lost.

This is a requirement on *process*, not on structure. Without the trigger "debugging
ran past 30 minutes with a non-obvious cause → write the entry now", the structure sits
empty and the standard does nothing. The triggers are in [RULES.md](RULES.md).

Be honest about what kind of thing a trigger is. By principle [2.5](#25-a-rule-without-a-mechanism-is-advice)
below, a rule with no checking mechanism is advice — and no linter can tell that a
debugging session ran long, or that a decision was settled in conversation. The triggers
are advice. What the linter catches is the *consequence* of ignoring them: a `status.md`
over its limit, a file that should exist and does not. On the six document sets this
standard is kept on, the triggers were present and unapplied in three, which is the
measured failure rate of capture that depends on a session noticing. That is the case for
automated capture — a pass that proposes candidate entries the session did not think to
write — with the quality gate moved to promotion into a register rather than placed at
capture. It is discussed, and deliberately not settled, in [RULES.md §6](RULES.md#6-tiers-and-scaling).

### 2.5. A rule without a mechanism is advice

A rule that cannot be checked by a linter or executed by a single command **cannot be
a hard rule**. It is demoted to advice, in writing, or dropped.

This is the least obvious principle here and the one that does the most work. A
five-manual-step ritual stops being performed by the third session, and a rule that is
nominally mandatory but silently unenforced is worse than an honest suggestion: it
makes the whole document set look maintained when it is not. Every hard rule in
[RULES.md](RULES.md) names its mechanism in the same table row.

**The same holds for instructions to the agent itself** — the root pointer, `start.md`,
a skill, a system prompt. An instruction is advice the agent can and occasionally will
set aside, and the way it does so is specific: it rarely forgets the rule, it decides
the rule does not apply *this time*. "Read `start.md` before starting work" gets read as
not covering a request that looks like a one-line edit — and the one-line edit is where
the routing in `start.md` would have said which of two files actually loads. Nobody wrote
the exception; the agent supplied it. Wording the instruction more strongly does not
help, because the next session makes the same judgement about the stronger wording.

So anything that must happen *every* time needs a mechanism outside the prompt: a hook in
the agent's tool, a linter, a pre-commit, a script that refuses. The instruction stays,
as the explanation of what the mechanism does and why. The question to ask of any new
instruction is what happens when it is skipped: if the answer is expensive and nothing
prevents the skip, look for the mechanism before polishing the words. The session
protocol's own first step is the standing example — see [RULES.md §3](RULES.md#3-session-protocol).
"The root pointer is a pointer, not a second home" is another: it has lint check 19, and
a Claude Code hook that stops an edit to the pointer and asks the person
(`tools/hooks/claude-code-guard-pointer.sh`).

### 2.6. Negative results are assets

"Built it, measured it, threw it away" is an evening of work. Unrecorded, it will be
spent again — often by the same person, sometimes twice.

A refuted hypothesis is therefore never deleted, and numbering is never reused. The
register that holds them (`E##`) belongs to the [research profile](profiles/research.md),
because projects that ship a feature list produce few negative results and projects
that test hypotheses produce more failures than successes.

### 2.7. One home per fact

The same statement in two files is a guarantee that one of them will drift. If
something is needed in two places, one of them holds a link.

There is a narrow, deliberate exception: **operational** warnings, repeated exactly
where someone is about to trip over them — a caveat in a tool's README as well as in
the register entry. Repeat only when consolidating would move the warning away from the
moment it is needed, and record that you did it on purpose.

---

## 3. What lives in `project-workbook/`

The core set, present in every project:

| File | Size | Role |
|------|------|------|
| `start.md` | ≤100 | Entry point: map, situational guide, critical facts |
| `overview.md` | ≤200 | Purpose, invariants, stack, structure, current state |
| `status.md` | ≤80 | State only: Working / Fragile points / Blocked / Deferred. Rewritten in place |
| `journal.md` | grows | Chronicle, append-only, newest on top, with an index |
| `gotchas.md` | grows | `G##` entries plus an index |
| `architecture.md` | grows | `A##` entries plus an index |
| `_meta.md` | ≤100 | Pointer to the rules and the version they are true against; per-project settings such as language |

Two axes adjust it, and they are independent. **Profiles** add by kind of work:
`conventions.md`, `subsystems/`, `references/` from the
[engineering profile](profiles/engineering.md); `experiments.md`, `corpus.md`, `plan/`
from the [research profile](profiles/research.md). **Tiers** adjust by size — which of
these files a project of this size has earned, and what its limits are. The authoritative
version of both is the inventory in [RULES.md §1](RULES.md#1-target-inventory-of-project-workbook);
the tiers themselves are in [§6](RULES.md#6-tiers-and-scaling).

**A file is created on its first real entry, not in advance.** An empty
`architecture.md` teaches an agent that architecture is undocumented here; an absent
one teaches nothing and costs nothing.

**And once that entry exists, creating the file is part of writing it** — not a decision
to put to the user, not work for the end of the session, not a reason to park the entry
somewhere else. Of the two failures this rule guards against, that one is the worse: an
empty file is visible and deleted in a second, while an entry nobody wrote is invisible
and costs its hours again.

**The Fragile points section of `status.md` is mandatory.** It is the most valuable
part of the file: places that look removable but are load-bearing. Phrase them as
"looks like X, is actually Y, breaks this way" — never as "be careful here", which
carries no information an agent can act on.

---

## 4. Loading priority

| File | Target size | When it loads |
|------|-------------|---------------|
| Root pointer (`AGENTS.md`) | 5–15 lines | Automatically, by the tool |
| `start.md` | ≤150 | Every session |
| `status.md` | ≤150 | Every session |
| `journal.md` (top entries) | 3–5 entries | Every session |
| `overview.md` | ≤200 | Most sessions |
| Register **indexes** | one line per entry | Every session that touches the code |
| Register **bodies** | by link | Only the entries the task links to |
| `conventions.md` | ≤300 | Once per session, before writing code |
| `subsystems/*`, `references/*` | ≤300 per page, then split | By task context |
| `_meta.md` | ≤100 | Rarely |

The index-and-body split is what keeps registers usable. A 506-line `gotchas.md` with
no index turns the protocol "non-trivial task → read the gotchas" into "read 506 lines
or skip it", and skipping is the likelier outcome. With an index, the same register
costs one screen to survey and one entry to read.

---

## 5. Tool independence

`project-workbook/` contains **no files specific to any AI tool** — no `AGENTS.md`, no
`CLAUDE.md`, no `.cursorrules` inside the folder.

The folder is addressed to every reader: any agent, and people. This matters most for
open source, where contributors arrive with different tools, and it matters for
longevity, because tools change faster than projects do.

`project-workbook/start.md` is the single entry point. The pointer lives at the **project
root** as `AGENTS.md` and holds nothing but a one-line description, an order to read
`project-workbook/start.md` first, and the few critical rules that pass the admission test
below. `AGENTS.md` is the shared convention: Claude Code, Codex, Cursor and others read it, so
one file serves every contributor's tool.

**Rename, do not add.** Claude Code reads `AGENTS.md` only where the directory has no
`CLAUDE.md` of its own (checked on 2.1.296): with both files present the pointer you
maintain is silently skipped. Move an existing `CLAUDE.md` to `AGENTS.md`. A tool that does
not read `AGENTS.md` gets a pointer under its own name (`.cursorrules`,
`.github/copilot-instructions.md`) with the same content. Nothing may appear in a pointer that is not also stated, in
full, inside `project-workbook/` — each critical rule names that place, and lint checks it (H11).

**Why the map does not move into the pointer.** Once every tool in use reads `AGENTS.md`,
`start.md` can look like a leftover from the time a project needed two pointers and a
shared file behind them. That was one reason for it and the only one that went away
(re-examined 2026-10-14). The others stand. The two files change at different rates: the
map is edited whenever a file or subsystem appears (the triggers in RULES §2), while an
edit to the pointer stops and asks the person (the guard hook in [tools/hooks/](tools/hooks/)),
because the pointer is where "write this down" lands. Merged, either every map update
asks or the guard goes and the pointer fills up again. A map of a hundred lines among
the critical rules dilutes them, and a tool reads everything in `AGENTS.md` as
instruction. The folder keeps its own entry point, so it works handed over alone — to a
person, an Obsidian vault, an agent given only the folder. A document set that is not a
project needs the same: `my-setup-notes`, the author's private store of knowledge about
the machine, its tools, network and devices — what would break in any project on that
machine, so belongs to none — is kept to this standard, and a hook injects the routing
from its `start.md` into every session of every project, where its own `AGENTS.md` would
never be read. Where the tool loads `start.md` itself, the extra hop costs nothing. The case for
merging is a tool with no such loader, where reading `start.md` stays advice; reopen
the question when a session there is seen skipping it, not before.

**The admission test for a critical rule.** A rule belongs in the pointer only if both
hold: it applies to *every* task in the project, not to a kind of task — kinds of task
are what the routing in `start.md` is for; and breaking it *before* `start.md` has been
read is expensive or irreversible — a commit to the wrong repository, a push, lost data,
the invariant the project exists for. Everything else goes to `start.md`'s three facts or
its routing, where it is read anyway.

There is deliberately no number. An earlier version said "at most three", which nothing
justified and nothing checked. The reason to keep the list short is an argument, not a
measurement: the pointer is loaded into every session, and every rule added to it dilutes
the weight of the others. The pressure to add one is real and specific — the pointer is
the one file a session knows is always read, so "write this down so it does not happen
again" lands there. Past five rules or twenty lines, lint warns, as a prompt to apply the
test again. Where the tool can load `start.md` itself at session start (the Claude Code
hook in `tools/hooks/`), the pointer matters less still; it matters most for tools that
cannot.

**Naming rule:** if a file is named after a tool, it belongs at the root. If a file
lives in `project-workbook/`, its name describes its content — `start`, `overview`, `gotchas`.

**Human contributors** are served by the conventional place, `CONTRIBUTING.md`, which
should mention that the project follows this standard and that `project-workbook/start.md` is
the entry point.

**Personal per-project settings** — the language you want the agent to speak, local
paths to test data, private reminders — go in the tool's local override file
(`CLAUDE.local.md` and its equivalents), which is git-ignored. Each contributor keeps
their own; only the shared pointer is committed.

### A note on `[[wikilinks]]`

The cross-reference syntax in [FORMATS.md](FORMATS.md) is Obsidian's native one, so an
`project-workbook/` folder opens as an Obsidian vault with no changes: graph view, backlinks and
an unresolved-link list, for free. That is a convenience for human readers only.

Nothing in this standard depends on Obsidian, and nothing may come to depend on it.
The files stay plain markdown that any editor, any agent and `grep` can read — and
`grep` is exact where a search UI is approximate.

---

## 6. Anti-patterns — what does not go in `project-workbook/`

**Anything derivable from the code.** Signatures, variable names, imports, obvious
hierarchies. Exception: the high-level tree in `overview.md`.

**Change history.** That is `git log`. `status.md` describes the current state;
`journal.md` records why work went the way it did, not what changed line by line.

**Task lists.** Tasks are tasks; use an issue tracker or a todo list. `project-workbook/` holds
what outlives the current task. Two narrow exceptions: `Deferred` in `status.md` —
deliberately postponed, with the reason — and, in the research profile, `plan/*.md`,
which carries acceptance criteria rather than intentions.

**Instructions of the form "do X".** `project-workbook/` is context, not a request. "Implement
feature Y" belongs in the conversation.

**Tutorials and general theory.** This is a reference for an agent that already knows
how to program. Explain the project, not HTTP.

**Numbers in prose.** In the research profile this is a hard rule with a linter behind
it; everywhere else it is still good practice. A figure that appears in four files will
disagree with itself within a month.

**Precise counters that go stale fast.** Line counts, file sizes, entry totals. Give a
ballpark and a link to the source.

**Caveats instead of structure.** If you find yourself writing "do not take these
numbers seriously", the numbers are in the wrong place. Move them; do not apologise for
them.

**Duplication between files.** See principle 2.7.

---

## 7. Keeping it true

A stale document is a defect, not untidiness. When one is found: update it now, or
delete the section now. Not "I will tidy this up later" — later does not arrive, and in
the meantime the document is actively misleading an agent that has no way to know.

Two mechanisms support this, and both are ordinary engineering rather than virtue:

- **The linter** ([tools/lint_workbook.py](tools/lint_workbook.py)) checks what can be checked:
  broken links, gaps in numbering, an index that disagrees with its bodies, a number
  with no source, a file over its limit, a path that no longer exists. Run it at the
  end of a session, and from a pre-commit hook.
- **The cold review** ([REVIEW_PROMPT.md](REVIEW_PROMPT.md)) checks what cannot. A
  documentation system can only be judged by a reader who did not build it; the prompt
  is written to be pasted into a fresh session with none of the design conversation in
  its context.

---

## 8. Where to go next

| You want to | Read |
|-------------|------|
| Set this up in a project | [migration/](migration/) |
| Know what is mandatory | [RULES.md](RULES.md) |
| Write an entry | [FORMATS.md](FORMATS.md) |
| Pick a profile | [engineering](profiles/engineering.md) · [research](profiles/research.md) |
| Record a measurement | [MEASUREMENT.md](MEASUREMENT.md) |
| Break a rule on purpose | [DEVIATIONS.md](DEVIATIONS.md) |
| Audit an existing setup | [REVIEW_PROMPT.md](REVIEW_PROMPT.md) |
