# FORMATS — entry formats

Three registers, three prefixes. Numbering is sequential within a register and is
**never reused** — not even when an entry is cancelled or turns out to be wrong. A hole
in the numbering means a deleted entry, and that is a lint error.

| Register | File | What goes there | Profile |
|----------|------|-----------------|---------|
| `G##` | `project-workbook/gotchas.md` | A gotcha: something that has already cost time and will again | core |
| `A##` | `project-workbook/architecture.md` | A settled decision about how the project is built | core |
| `E##` | `project-workbook/experiments.md` | A hypothesis tested by measurement — whatever the outcome | research |

**Choosing a register.** Ask: is this a trap, a decision, or a test? If the entry will
have to be rewritten after the next measurement, it is an `E##`, not an `A##`. An `A##`
is opened when the investigation is **finished** and the outcome has settled.

That distinction is not academic. In the project this standard came from, entry `A07`
was written and then twice substantially rewritten within three weeks, growing past 100
lines. An entry rewritten every other day is not an architecture decision; it is the
current standing of an open investigation, and `A##` is the wrong shelf for it by
volatility.

---

## The index

Every growing register opens with an index — one line per entry, above the bodies:

```markdown
## Index
- **E01** · refuted · Skip the load on fully overwritten targets · [[T-2]]
- **E02** · confirmed · Pin the hot thread to a big core · [[T-4]]
- **E03** · open · Resolve readback lazily, by dirty rectangle · [[T-7]]
```

The index exists so verdicts can be scanned without reading bodies. Lint checks that the
set of index IDs equals the set of headings. It also warns when an index line and its
heading share no words at all — it cannot judge whether a reworded title still means the
same thing, so keeping those honest is on you.

`journal.md` gets an index too, for the same reason: you cannot scan a chronicle you
have to read.

---

## Links

The only cross-reference syntax is `[[ID]]`:

| Form | Resolves to |
|------|-------------|
| `[[G05]]`, `[[A03]]`, `[[E01]]` | A register entry |
| `[[T-2]]` | A task row in `plan/backlog.md` (research profile) |
| `[[subsystems/renderer]]` | A subsystem page (engineering profile) |
| `[[corpus:movies-48]]` | A run configuration in `corpus.md` (research profile) |
| `[[D5]]` | A deviation in the project's own `DELTA.md` (see [DEVIATIONS.md](DEVIATIONS.md)) |

A link to an entry that does not exist **yet** is allowed and means "this is worth
writing" — lint reports it as a warning. A link to something **deleted** is an error: an
unresolved id-shaped link is a typo far more often than a forward reference.

Ordinary markdown links stay for files, code and external URLs. `[[…]]` is only for
project entities.

**Why a checked syntax at all.** Unchecked links rot silently, and the file most likely
to rot is the one nobody re-reads. In one of the projects this standard came from, the
pointer in `_meta.md` — the file that governs all the others — aimed at a drive layout
that had not existed for months, and nobody noticed. Lint check 9 exists for exactly
that failure.

---

## `G##` — gotcha

```markdown
## G08. Short title — the symptom, not the topic
**Context:** during which task, and where, it showed up.
**Symptom:** what is visible from outside — a message, a behaviour, a figure.
**Cause:** why it happens. A mechanism, not "turned out it didn't work".
**Fix:** what to do, and where it lives in the tree if it lives there at all.
**How to spot it:** what tells you that you have hit it again.
**Portable:** yes — <the class of problems>   ← only when not tied to this code
```

**Title by symptom, not by topic.** An entry is found again by what the reader is
staring at, not by the subject it belongs to. "Sourcemaps break MAIN-world injection"
beats "Notes on the Vite config".

**The Cause field is where the value is.** "It turned out not to work" records that you
suffered; a mechanism records what you learned. Compare:

> **Cause:** Vite defaults to `build.sourcemap: true`. Chrome MV3 refuses to execute
> scripts carrying a sourcemap comment in the MAIN world — this is extension-specific
> behaviour and is not documented explicitly.

**How to spot it** should give a signature someone can search for — a string to grep, a
figure to compare, a file to open. That field is what turns a war story into a
diagnostic.

**Portable: yes** is set when the entry is not about this code but about a class of
problems: measurement methodology, a driver quirk, a tooling trap. Such entries are
candidates for promotion into a shared layer across your projects. Until that layer
exists, the mark is a queue rather than an address — and it is still worth setting,
because it is unrecoverable later.

---

## `A##` — decision

```markdown
## A01. Name of the decision
**Context:** why the question arose. What was wrong with the starting point.
**Alternatives:** what was considered and why it was rejected. If one was built and
measured, link its [[E##]] rather than retelling it.
**Decision:** what was chosen, and where it lives in the tree.
**Consequences:** good and bad. If the project is a fork, state separately how this
diverges from upstream and what that will cost when porting their fixes.
**Based on:** [[E01]], [[E03]]
```

Opened only when the investigation is **finished**. The `Based on` line is what keeps
the two registers honest: a decision with no experiments behind it is either obvious or
unexamined, and it is useful to see which.

---

## `E##` — experiment

```markdown
## E01. Skip the load on targets the frame overwrites entirely
**Status:** refuted | **Task:** [[T-2]] | **Opened:** 2026-08-01 |
**Closed:** 2026-08-03 | **Commit:** never merged

**Hypothesis.** A mechanism, not a wish: why the structure of the thing implies there
should be a gain at all.

**Prediction.** Written BEFORE the run. In numbers, per configuration, with a
threshold:
- `[[corpus:scene-a]]`: frame time p50 down 5% or more, pass count unchanged
- `[[corpus:scene-b]]`: unchanged (nothing to save there)

**Method.** Which configurations, what changed, the sweep order.

**Result.** One headline line per configuration, each linking **this experiment's own
report** — not the baseline it was compared against:
- scene-b: ft_p50 −0.4% (threshold 2.52%) → `baseline/scene-b/9f2ab1-e01.json`

**Verdict.** Refuted. The driver already drops the load for these targets — the gain
was taken before us. No need to retry.

**Traces.** "Do not do this — [[E01]]" recorded in `plan/02_renderer.md`.
```

**Statuses:** `open` (prediction recorded, no measurement yet) · `confirmed` ·
`refuted` · `inconclusive` (the difference does not clear the threshold — see
[MEASUREMENT.md](MEASUREMENT.md)) · `shelved` (abandoned, with a reason).

**The `retro` marker** goes beside the status when an entry was created after the fact
and its prediction was reconstructed from the result. Such an entry proves nothing
about the quality of the prediction; it preserves only the result and the verdict.
Marking it is mandatory — if some predictions are written after the result and that is
not visible, none of them can be trusted.

Three rules carry the whole construction:

1. **The prediction is written before the run.** Otherwise an explanation gets fitted to
   whatever numbers arrive, and measurement becomes theatre. Open the entry with status
   `open` **before** starting the run — [tools/new_experiment.py](tools/new_experiment.py)
   refuses to create one without a prediction, which is the only thing standing between
   this rule and a rule nobody enforces.
2. **A refuted entry is never deleted.** It is the primary asset: an evening of work
   that will not have to be spent again.
3. **A verdict leaves a trace in the task.** The line "do not do this — `[[E##]]`" goes
   into the matching `plan/*.md` file. Knowledge has to sit where the temptation arises,
   not only in the archive.

---

## Journal entries

`project-workbook/journal.md` is append-only, newest on top. An entry is 5–10 lines: what was
done, and links. Details live in register entries and in the data; the journal does not
restate them.

```markdown
## YYYY-MM-DD — <task id>: what was done, one line

Done: the substance of the change, 1-2 lines
Measured: <metric: before → after> on [[corpus:<id>]] → `baseline/<id>/<file>.json`
Experiments: [[E01]] refuted, [[E02]] confirmed
Gotchas: [[G09]] | Decisions: [[A01]]
Status: Working / Fragile — if Fragile, in what way
```

**Supersession marker.** When a later entry overrides an earlier one, a line is added at
the head of the earlier entry. The entry itself is neither edited nor deleted:

```markdown
> **Superseded 2026-08-14** — current state is in the 2026-08-14 entry.
> The reasoning below is kept: it explains why the earlier approach was rejected.
```

Without this marker the journal cannot be read top-down. Some of its statements are
already false, and the reader only finds out on reaching the entry that overturns them —
by which point they have acted on the false one.
