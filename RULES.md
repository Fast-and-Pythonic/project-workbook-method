# RULES — the normative part

What is mandatory, when to write it, and what checks it. Principles are in
[METHODOLOGY.md](METHODOLOGY.md); entry anatomy is in [FORMATS.md](FORMATS.md).

Rows marked **[R]** belong to the [research profile](profiles/research.md) and are
inactive in a project that has not enabled it; rows marked **[E]** belong to the
[engineering profile](profiles/engineering.md). Everything else is core.

A second axis runs beside the profiles: the **tier**, `S` / `M` / `L`, which says how much
of the inventory a project of this size warrants and what its limits are. A profile
answers *what kind of work*; a tier answers *how much*. See [§6](#6-tiers-and-scaling).
The tier changes the inventory and the limits and **nothing else** — triggers, entry
formats and the hard rules are identical at every tier.

---

## 1. Target inventory of `project-workbook/`

| File | Tier | Size | Role | |
|------|------|------|------|--|
| `start.md` | S | ≤150 | Entry point: map, situational guide, critical facts | |
| `overview.md` | S | ≤200 | Purpose, **invariants**, stack, structure, phases | |
| `status.md` | S | **≤150** | State only: Working / Fragile points / Blocked / Deferred. Rewritten in place | |
| `gotchas.md` | S | grows | `G##` plus index | |
| `_meta.md` | S | ≤100 | Pointer to the rules and the version they are true against; per-project settings | |
| `architecture.md` | S | grows | `A##` plus index | |
| `journal.md` | M | grows | Chronicle, append-only, newest on top, with an index | |
| `conventions.md` | M | ≤300 | Code style, build, test, what must not be auto-formatted | **[E]** |
| `subsystems/*.md` | M | ≤300 per page | Compiled knowledge about one part of the tree | **[E]** |
| `references/*.md` | M | ≤300 per page | External specs, upstream state, third-party formats | **[E]** |
| `experiments.md` | S | grows | `E##` plus index | **[R]** |
| `corpus.md` | S | grows | Register of run configurations — the key to every measurement | **[R]** |
| `plan/*.md` | S | — | Tasks with acceptance criteria, plus `backlog.md` | **[R]** |

The tier column says from which size a file is **expected**. Below that tier it is not
missing, it is unwarranted: a one-area project with no `subsystems/` is complete, not
half-documented. Above it, an absent file is a gap worth explaining.

**Only `status.md`'s size is enforced.** It is a forcing limit — it exists to refuse an
append-only chronicle, so the chronicle goes to `journal.md` rather than crowding out the
state. Every other size in the table is advice, and the linter warns rather than errors:
measured across six document sets, everything a session always reads comes to about 6k
tokens, so none of these numbers is defending a context budget and an error raised for
advice only teaches the reader to ignore the linter. See
[METHODOLOGY §2.3](METHODOLOGY.md#23-layered-loading). A page limit (`subsystems/`,
`references/`) means "split this page", not "stop writing".

**The numbers are the linter's defaults, and a project changes one only with a reason.**
Set in 2026-10 from nine document sets: five sat at or past the old `status.md` limit of
80 (80, 80, 82, 86, 122), two had raised it to 160 in their own config, and page limits
had been invented per project at 180, 200 and 250. A default that half the projects
override is not a default. An override in `lint_workbook.toml` carries a comment saying
why; one without a comment, or equal to the default, is a warning (check 20).

### Creating a file

**A file is created on its first real entry, not in advance.** An empty
`architecture.md` teaches an agent that architecture is undocumented here; an absent one
teaches nothing and costs nothing.

**And when that first entry exists, creating the file is part of writing the entry** —
not a separate decision to be raised with the user, not something to defer to the end of
the session, and not a reason to park the entry in a neighbouring file "for now". If the
trigger fired, write it where it belongs, now.

Both halves are defects, and the second is the more expensive of the two. An empty file
is visible and deleted in a second. An entry that was never written because its file did
not exist yet is visible to nobody, and costs the same hours over again — which is the
whole reason this standard exists.

`corpus.md` may live beside the measurement data instead of in `project-workbook/` — set the
path in `tools/lint_workbook.toml`. Put it wherever the person taking a measurement will
actually look.

**Task format in `plan/*.md`:** Context → What to do → How to verify → Acceptance
criterion → Owner. A task without a checkable acceptance criterion does not enter the
plan; tasks of the form "figure it out and improve it" are forbidden.

**The Fragile points section of `status.md` is mandatory.** Phrase entries as "looks
like X, is actually Y, breaks this way", not "be careful here".

---

## 2. Update triggers

The table is the process. Without it the structure sits empty.

| What happened | Action | |
|---------------|--------|--|
| Debugging > 30 min with a non-obvious cause | `gotchas.md`: a `G##` — **now**, not "later" | |
| A quirk of an external dependency | `gotchas.md`: a `G##` with the dependency named in the title | |
| A decision settled | `architecture.md`: an `A##` | |
| A fragile point was identified | `status.md`: Fragile points | |
| A feature was deliberately deferred | `status.md`: Deferred, **with the reason** | |
| A feature was finished | `status.md`: Working; `journal.md`: an entry | |
| Knowledge not tied to this project | Mark the entry **Portable: yes** | |
| **A research answer to the user that outlives the session** | Into the matching file; the chat gets the short version with a link | |
| A new file or subsystem appeared | `start.md`: the map | |
| The method itself changed | The project's `DELTA.md`, and `_meta.md` if needed | |
| Code style, build or workflow changed | `conventions.md` | **[E]** |
| A deep dive into one part of the tree | `subsystems/<name>.md` — create or extend | **[E]** |
| Checked against upstream | `references/upstream-watch.md`: date, range reviewed, verdict | **[E]** |
| A hypothesis was formed | `experiments.md`: an `E##`, status `open`, **prediction written BEFORE the run** | **[R]** |
| A measurement was taken | JSON into the baseline tree; headline line in the `E##`; line in `journal.md` | **[R]** |
| A hypothesis was refuted | Verdict in the `E##` (**never deleted**) plus a `[[E##]]` back-link in the task, carrying the lesson. Usually that reads "do not do this"; a hypothesis refuted to the letter of its prediction and adopted in substance needs the pointer just as much, and there the phrase would be false | **[R]** |
| A backlog task finished | `backlog.md`: status; `journal.md`: entry; `status.md`: Working or Fragile | **[R]** |
| The run configuration changed | `corpus.md`: a new configuration; old baselines are not rewritten | **[R]** |

The trigger on *conversation* is easy to overlook and is one of the most productive.
The commonest way to lose knowledge is to work it out in a discussion and never write
it down; a chat log is not a document, and the next session cannot read it.

**These triggers have no checking mechanism, and by H-rule logic that makes them
advice.** Nothing can verify that a debugging session ran past thirty minutes or that a
decision was settled in a discussion; the linter catches only the consequences — a
`status.md` past its limit, a file that ought to exist. Measured on the six document
sets this standard is kept on, the table was present and unapplied in three. That is
the honest failure rate of capture that depends on a session noticing, and the reason
automated capture is a live question rather than a rejected one — see §6.

---

## 3. Session protocol

1. **Always:** `start.md` → `status.md` → the top 3–5 entries of `journal.md`.
2. Your task in full, including every `[[E##]]` and `[[G##]]` it links to.
3. The **indexes** of the growing registers — indexes only; bodies by link.
4. Working on a subsystem → `subsystems/<name>.md`. If the page does not exist, create
   it from what you learn. **[E]**
5. About to measure → [MEASUREMENT.md](MEASUREMENT.md) and `corpus.md` **before** the
   run, not after. **[R]**
6. **Stop and ask the user** when: a doubt touches the invariants in `overview.md`; a
   contract or the architecture would have to change; the method contradicts reality.
7. At the end, work through the triggers above and run `python tools/lint_workbook.py`.

Step 1 is the rule every other step depends on, and by [METHODOLOGY §2.5](METHODOLOGY.md#25-a-rule-without-a-mechanism-is-advice)
it is advice as long as the only thing behind it is an instruction in the root pointer.
Where the agent's tool can run a command at session start and put its output into
context, that is its mechanism: load `start.md` there, and the reading no longer depends
on the session judging the task big enough to count. [`tools/hooks/`](tools/hooks/)
has one for Claude Code. Keep what the hook loads small — a tool may cut a large hook
output down to a preview, and a preview looks loaded while missing its tail.

Step 6 is not politeness. An invariant is a rule of the project rather than of its
documentation, and no linter can check one; stop-and-ask is its only mechanism, which
is exactly why it is written down as a step rather than assumed.

---

## 4. Hard rules

A violation is an error, not a stylistic blemish. **Every hard rule names its checking
mechanism in the same row.** A rule without one is demoted to advice or removed —
otherwise it is a dead letter within three sessions.

| # | Rule | Mechanism | |
|---|------|-----------|--|
| H1 | Every register entry has an index line, and every index line has an entry | lint: the set of headings equals the set of index IDs | |
| H2 | Every `[[link]]` resolves | lint: an unresolved id-shaped link (`G05`, `E01`, `D5`) is an **error** — it is a typo, not a forward reference. Links to planned pages and configurations are warnings | |
| H3 | `status.md` ≤ 150 lines | lint: line count. **The only forcing limit, and the only one that is an error.** It exists to refuse an append-only chronicle, not to save bytes — every other limit in the inventory is advice and warns. See [METHODOLOGY §2.3](METHODOLOGY.md#23-layered-loading) for the measurement that settles it | |
| H4 | Numbering has no gaps; a refuted or cancelled entry is never deleted | lint: gap-free numbering. A gap only appears when an entry is removed from the middle; deleting the **last** entry is invisible to lint and is caught by git history instead | |
| H5 | An absolute path written in prose points at something that exists | lint: existence check. Depends on the convention below | |
| H6 | Measure only on a configuration registered in `corpus.md` | lint: every report's `corpus_id` exists in the register and matches its directory | **[R]** |
| H7 | An `E##` whose status is not `open` has a Prediction naming a quantity or a configuration | `new_experiment.py` refuses to open an entry without one; lint checks it. Ordering ("before the run") is enforced by using the tool rather than editing by hand — nothing can verify it after the fact, which is why a reconstructed entry must be marked `retro`. **A `retro` entry is held only to having a prediction at all**: its quality is already declared unverifiable, so demanding a figure of it buys a better-looking reconstruction rather than better evidence | **[R]** |
| H8 | A measurement number appears only as a headline line linking to its report | lint: a number with a unit in a line with no path ending in `.json` | **[R]** |
| H9 | A refuted `E##` has a back-link from the task that tempted it | lint: presence of the back-link | **[R]** |
| H10 | `_meta.md` exists and names the standard the documents are kept to, with the version they were last audited against | lint: the file is present and carries a resolvable standard and a version. Shipped as a warning and **promoted to an error on 2026-09-13**, once every consumer was clean — the release policy in [DEVIATIONS.md §6](DEVIATIONS.md#6-changing-the-standard-itself) working as written, and its first completed cycle | |
| H11 | Every critical rule in a root pointer (`AGENTS.md`, or a tool's own file such as `.cursorrules`) says where in `project-workbook/` it is stated | lint: each rule under the pointer's *Critical rules* carries a path into the documents that exists, or a register id that resolves. An **error** from the release that introduced it, 2026-10-02: measured across every consumer first, the rules it flagged were each already stated in their documents and lacked only the path. Which rules belong in a pointer at all is a judgement — the admission test in [METHODOLOGY §5](METHODOLOGY.md#5-tool-independence) — and only warns past five rules or twenty lines | |

**The convention H5 depends on:** an absolute path written in prose goes in backticks,
and only then may it contain spaces — where an unquoted path with spaces ends is not
decidable. Fenced blocks are skipped; they hold examples.

**Standing apart** are the project's own invariants, stated once in `overview.md` and
repeated nowhere. Those are rules of the project rather than of its documentation, and
their only mechanism is step 6 of the protocol.

---

## 5. What lint checks

**Scope:** `project-workbook/`, the run-configuration register, and the measurement reports.
`[[wikilinks]]` inside your method folder are **not** checked — it holds placeholders
such as `[[E##]]`, which are samples. Its **file** links and absolute paths are checked
all the same: a rotting path is no less broken for living in the method folder. Fenced
blocks and HTML comments are skipped everywhere: both hold examples, and a template
ships its entry skeleton inside one.

**Documents written in another language.** The checks that look for a field —
`Prediction`, `Status`, `Acceptance criterion` — match a literal label, and so does the
list of metric names. Set them under `[labels]` and `[numbers]` in the config if your
documents are not in English. Leaving the defaults does not produce errors; it produces
silence, which is indistinguishable from passing.

Each check backs a hard rule above, or catches rot that has actually happened in the
projects this standard came from.

| # | Check | |
|---|-------|--|
| 1 | Broken `[[links]]` and broken markdown links to files | |
| 2 | Index against headings in every register; gaps in numbering. A register with entries and no index at all is reported once, not once per entry; a register whose entries are numbered under some other scheme (`## 7.` rather than `## G07.`) is a warning, because otherwise every check below passes by finding nothing. Once a register is split by area (§6), the bodies are read from every file under `register_bodies`, and an id with an entry in two files is an error | |
| 3 | Index line and heading that share no words — a warning; a rename probably went halfway | |
| 4 | Line limits. An **error** only for the names in `limits.enforce` — `status.md` by default, the one limit that forces something. Every other limit warns, including the page globs (`subsystems/*.md`, `references/*.md`, 300 by default), because "this is getting long" is advice and an error raised for advice trains the reader to ignore the output | |
| 5 | Absolute paths in prose, checked for existence | |
| 6 | Repo-relative paths in backticks, checked against a small set of roots | |
| 7 | `journal.md` index against its entries, counted **per date** | |
| 8 | A register grown past 60 entries — a warning that its index has stopped being scannable. Once the register is split by area, the threshold applies to each area's file instead | |
| 9 | Backlog statuses belong to the legend that file declares | **[R]** |
| 10 | Backlog tasks marked `done` with no `journal.md` entry **headed** with that id | **[R]** |
| 11 | Every measurement report: required fields present, `corpus_id` registered and matching its directory | **[R]** |
| 12 | The `corpus.md` index against the configurations that actually parse as registered | **[R]** |
| 13 | Numbers with no link to a source | **[R]** |
| 14 | An `E##` with status `refuted` and no back-link from a task | **[R]** |
| 15 | An `E##` whose status is not `open` with no prediction naming a quantity or a configuration; a `retro` entry only has to have one at all | **[R]** |
| 16 | An acceptance criterion that hedges (`noticeably`, `measurable`, `faster than`) without a figure — a warning | **[R]** |
| 17 | In a split register whose index is grouped under headings that link to each area's file, every id sits under the section of the file its entry is in. Silent for a flat index. This is what breaks when an entry moves between files and the index is not updated to match | |
| 18 | `_meta.md` is present, names the standard, and carries the version it was audited against (H10). An **error** since 2026-09-13. Without it a document set cannot say which rules it is being held to, and a session has to guess; without the version, "behind" and "never compliant" look the same | |
| 19 | Every critical rule in a root pointer names its place in `project-workbook/` — a path that exists or a register id that resolves (H11). An **error**. More than five rules or twenty lines in a pointer — a warning | |
| 20 | A limit overridden in the project's config with no comment saying why, or overridden to the default value — a warning (§1) | |

Three of these are subtler than they look, and the subtlety is load-bearing. Do not
simplify them away:

- **Check 13 works per line, not per paragraph, and verifies relevance.** A
  paragraph-wide test lets one allow-phrase or one unrelated link excuse every number in
  a bullet list. And presence alone is not enough: the defect this exists for was a
  figure about one configuration backed by a link to a different configuration's
  baseline. If a line names a registered configuration, the report it cites must belong
  to that configuration. The Prediction block of an `E##` is exempt — by H7 it is
  written before any report exists.
- **Check 7 counts per date rather than comparing sets.** Comparing sets makes a missing
  index line invisible whenever two entries share a date.
- **Check 12 treats planned configurations as prose, not headings.** A heading would make
  the measurement harness accept a configuration that has no data and no baseline, so
  the register deliberately writes planned ones as prose and the index distinguishes
  them.

**Rules enforced outside the linter**, in the tools that produce the evidence, because
no amount of markdown checking can catch them: a comparison tool that refuses a verdict
when the sweep ran in one direction only, refuses when a report carries no observed
spread, and derives its threshold from the runs being compared rather than from a number
written down once. See [MEASUREMENT.md](MEASUREMENT.md).

---

## 6. Tiers and scaling

### What a tier is keyed on

**The number of distinct areas a session must hold in its head** — not lines of code.
Two projects measured at 12k and 14k lines came out at the same size by any line count
and at different tiers by this one: the first is twenty files in one language, the second
is ninety-five across two with a foreign-function boundary between them. Lines of code
predicted neither.

The discriminator is already in use: the [engineering profile](profiles/engineering.md)
says to split a subsystem out when its documentation passes 50–80 lines. Counting how
many such pages a project has earned *is* the tier.

| Tier | The project | Inventory | Limits |
|------|-------------|-----------|--------|
| **S** | One area. No subsystem pages earned | The `S` rows of [§1](#1-target-inventory-of-project-workbook) | As written |
| **M** | Two to four areas | Adds `journal.md`, `conventions.md`, `subsystems/`, `references/` | As written |
| **L** | Five or more areas, or a register past the split threshold | Registers split by area under one index | As written; see below |

**Tier S is there to legitimise what already works.** A small project running on four
files, passing lint, with a situational guide that fits on a screen, is not an incomplete
`M` — it is a correct `S`. Calling it incomplete is how a standard earns a reputation for
bureaucracy and stops being run at all.

**Tier L changes where things live, not how much is written.** Three moves, and each has
the same shape — push what belongs to one area onto that area's page, keep only the
cross-cutting part in the file everyone loads:

- **Registers** split by area (below). The index stays in the register file.
- **Fragile points.** A subsystem's fragile points move to its `subsystems/` page;
  `status.md` keeps the ones that cross areas. That, not a bigger number, is what keeps
  it inside its limit.
- **The situational guide** in `start.md` keeps cross-cutting situations and hands the
  rest to the subsystem pages. A guide that grows one line per area outgrows `start.md`
  at exactly the size where it matters most.

Raising a limit before making those moves treats the symptom. In both projects that blew
the `status.md` limit fourfold, the file was carrying an append-only chronicle because
neither had a `journal.md`; with the chronicle evicted, one of them came in at 112 lines —
far enough from 340 that the chronicle was plainly the disease. Tier L once had its own
`status.md` limit of 120; the common limit of 150 replaced it.

### Splitting a register

When check 8 fires, the register becomes a directory with one file per area under a
single top-level index. **Numbering stays sequential across the whole register**, so no
existing `[[G17]]` breaks.

The linter follows the split: name the directory in `register_bodies` in
`lint_workbook.toml`, keep the index in the register file, and group it under headings that
link to each area's file — `## Build — [subsystems/build.md](subsystems/build.md)`.
Checks 2 and 17 then hold the index to the files, which is the part a hand-made split
gets wrong first.

After the split, check 8 counts per area file rather than the whole register: the
total keeps growing and splitting has already answered it. The next warning names the
area that has outgrown its page.

That addresses one bottleneck — the size of the chunk you must read to know what
exists — and it is worth being exact about which one, because the question "should this
be a database instead of a folder" is really two questions with different answers.

**Retrieval** — how a session finds what it needs. The map (`start.md`, the indexes,
`[[links]]`) is a hand-built retrieval system: deterministic and auditable, and you can
see why a document was loaded. Its cost was measured on the six document sets this
standard is kept on — about 6k tokens for everything a session always reads, and the
largest register at 25 entries — so at this size an embedding index, tags or a knowledge
graph would not be solving a problem that exists. That is a statement about *these*
sizes, not a verdict. The signals that would change it: a split register passing ~80
entries; a session failing to find an entry that exists and writing a duplicate — record
*that* as a `G##`, it is the first real evidence; cross-cutting queries becoming routine;
an external corpus appearing.

**Capture** — how knowledge gets *into* the documents. This standard's answer is the
trigger table in §2, and it is manual: a session has to notice that a trigger fired and
act. On the same six document sets that mechanism was present and unapplied in three —
a decision log grown to 349 lines because the journal was never created, a project with
no `_meta.md`, a register in a format the linter could not see. Automated capture — a
pass over the session that proposes candidate entries — addresses exactly that failure,
and the objection that it would record wrong conclusions applies to the manual route
too: the same audit found a `_meta.md` describing a file layout months out of date and a
root pointer citing an entry that did not exist. The gate belongs at *promotion* — what
gets a number and enters a register — not at capture. Nothing here has been tried yet;
see §2 for why the triggers as written are advice rather than rules.

A reader arriving at this section from a session that has just polished the map should
notice the pull to defend it. The two paragraphs above were rewritten on 2026-09-14 for
that reason: the earlier text carried a settled verdict against heavier machinery, and
every session that read it reproduced the verdict as its own.

---

## 7. What we do not write

Beyond the anti-patterns in [METHODOLOGY.md §6](METHODOLOGY.md#6-anti-patterns--what-does-not-go-in-project-workbook):

- **Retelling the code of a dependency or an upstream tree.** What goes into
  `subsystems/` is what cannot be derived from the source in reasonable time: who owns
  what, where the boundaries are, which invariants hold, where it is fragile.
- **Speculation about performance or quality.** Either an `E##` with a prediction and a
  check, or nothing.
- **Caveats instead of structure.** If you are writing "do not take these numbers
  seriously", the numbers are in the wrong place.
