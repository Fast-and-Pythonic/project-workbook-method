# Profile: research

For projects where the work is hypothesis → measurement → verdict, and where **more
hypotheses fail than succeed**: performance optimisation, tuning, data pipelines,
anything with a metric that decides whether a change was worth making.

Read [METHODOLOGY.md](../METHODOLOGY.md) and [RULES.md](../RULES.md) first. This file
says only what the profile adds.

---

## Why it exists

Two classes of knowledge have nowhere to live in the core set, and both are expensive:

- **Negative results.** "Built it, measured it, threw it away." Each one costs an
  evening, and an unrecorded one costs that evening again.
- **Numeric measurements**, comparable only when their run configurations match.

The diagnosis is not theoretical. In the project that prompted this profile, six
subsystems were built, measured and discarded over a few months, plus two retracted
justifications for a tuning constant. All of it settled as prose inside a decision log,
and the question "what have we already tried and rejected?" had no answer short of
reading 800 lines. Meanwhile a "before/after" table was typed in from a console by hand,
and "how did this metric move over the last five changes?" had no answer at all.

An `A##` cannot absorb this. An architecture decision that gets rewritten after every
measurement is not a decision; it is an open investigation on the wrong shelf.

---

## What it adds

| File | Size | Role |
|------|------|------|
| `experiments.md` | grows | `E##` entries plus an index |
| `corpus.md` | grows | Register of run configurations — the key to every measurement |
| `plan/*.md` | — | Tasks with acceptance criteria, plus `backlog.md` |

Plus the measurement contract in [MEASUREMENT.md](../MEASUREMENT.md), hard rules H6–H9
in [RULES.md](../RULES.md), and lint checks 9–16.

### `experiments.md` — the `E##` register

The format is in [FORMATS.md](../FORMATS.md). Three rules carry it, and none of them
survives without a mechanism:

1. **The prediction is written before the run.** Create the entry with
   [tools/new_experiment.py](../tools/new_experiment.py), which allocates the number,
   writes the index line, and refuses to proceed without a prediction. Editing the file
   by hand defeats this; nothing can verify ordering after the fact, which is why a
   reconstructed entry must carry the `retro` marker.
2. **A refuted entry is never deleted, and its number is never reused.** Lint checks for
   gaps.
3. **A verdict leaves a trace in the task.** "Do not do this — `[[E##]]`" goes into the
   `plan/*.md` file where the temptation lives. An archive nobody reads at the moment of
   temptation is not a defence.

A refuted `E##` is the most valuable thing this profile produces. Treat it that way in
writing: the register's index shows verdicts, so a reader can scan what has already been
ruled out without opening anything.

### `corpus.md` — run configurations

One entry per configuration, with an index at the top. Skeleton:
[templates/corpus_entry.md](../templates/corpus_entry.md). What a configuration *is*
depends on the work — see [MEASUREMENT.md §1](../MEASUREMENT.md).

Planned-but-unregistered configurations are written as prose, not as headings. A heading
would make the harness accept a configuration that has no data and no baseline; the
index distinguishes registered from planned, and lint check 12 enforces the distinction.

The register may live beside the measurement data rather than in `project-workbook/`. Put it
where the person about to take a measurement will actually look, and set the path in
`tools/lint_workbook.toml`.

### `plan/*.md` — tasks with acceptance criteria

This is a **legitimate exception** to the standard's "no task lists in `project-workbook/`" rule,
and every project using this profile should record it as such in its `DELTA.md` — see
[DEVIATIONS.md §3](../DEVIATIONS.md).

The exception is earned by the format: Context → What to do → How to verify →
Acceptance criterion → Owner. A task without a checkable acceptance criterion does not
enter the plan. "Figure it out and improve it" is forbidden, and lint check 16 warns on
criteria that hedge — "noticeably faster" cannot settle an argument later, which is the
only thing an acceptance criterion is for.

For a project of any size, split by phase: `plan/01_infra.md`, `plan/02_renderer.md`,
with `backlog.md` holding the index and the statuses. Declare the status legend in
`backlog.md` itself; lint check 9 holds you to it.

---

## Which measurement regime

The measurement apparatus splits in two, and taking the wrong half is a real cost —
copying someone else's defences against someone else's disease is cargo cult.

- **Regime A, noisy measurement** — live hardware, timing, I/O. The threat is mistaking
  noise for signal. Defences: sweep in both directions, warm-up and cool-down, a
  threshold derived from the observed spread of the runs being compared.
- **Regime B, deterministic pipeline** — the same input gives the same number. There is
  no spread and nothing to measure it in, so none of regime A applies. The threat is
  that the reference you score against is itself wrong. Defence: a verdict requires
  agreement of at least two indicators, of which at least one does not depend on the
  reference data.

Both are specified in [MEASUREMENT.md](../MEASUREMENT.md). State which one you are in,
in `_meta.md` or `DELTA.md`. A project can be in both, per configuration — say so
explicitly rather than leaving it to be inferred.

---

## Session shape

One task from `plan/` per session. The protocol in [RULES.md §3](../RULES.md) applies,
with two additions:

- Read [MEASUREMENT.md](../MEASUREMENT.md) and `corpus.md` **before** the run, not after.
  Afterwards is when you find out the configuration was never registered.
- A doubt that touches an invariant in `overview.md` stops the session and goes to the
  user. In a research project the invariants are what the measurements are *for*;
  quietly working around one invalidates everything measured after it.
