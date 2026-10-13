# MEASUREMENT — the measurement contract

Part of the [research profile](profiles/research.md). Read it **before** a run, not
after.

The premise: no change is accepted without a mechanical check, and "it got better"
without numbers does not count. This file describes what makes a number comparable and
where it belongs.

---

## 1. The configuration is the key to everything

The unit of measurement is not "the project" but a **registered run configuration**.
Two numbers may be compared only when their configurations differ in exactly one
component.

What a configuration is depends on the work:

| Kind of project | Configuration = |
|-----------------|-----------------|
| Performance on real hardware | scene or workload + device + build |
| A data pipeline | input corpus + reference data + code version |
| A model or heuristic | dataset + parameters + code version |

Register them in `corpus.md`, one entry per configuration, with an index at the top.
The skeleton is [templates/corpus_entry.md](templates/corpus_entry.md).

**Hard rule (H6):** a measurement on an unregistered configuration is not accepted.
Register first, then run. Have the harness validate the id against the register and
refuse an unknown one — the check is worth more at the moment of the run than at the
moment of the commit.

The rule exists because of a specific, expensive failure: in one run the parser and the
reference dictionary both changed, and the report was a single "before/after" table.
Separating the two contributions is now impossible. This rule would have caught it
before the run started.

---

## 2. Data apart from docs

The single source of truth for measurements is a committed report file (JSON), not
prose:

```
<baseline root>/<corpus-id>/<commit8>-<label>.json
```

Two shapes exist and they are not the same file:

- **The raw report** is what the harness writes: per-run entries, unprocessed counters.
- **The curated baseline** is derived from exactly one raw report: per-run values
  aggregated, ambiguous field names disambiguated (a percentage must not be readable as
  a duration), plus a `derived_from` field naming the raw file and whatever editorial
  prose a human wrote.

Both are committed, so numbers can be re-derived instead of trusted. One baseline is the
curation of **exactly one** session — the first canonical baseline in the source project
was found to blend two, reporting one session's spread beside another's counters.

Required fields, enforced by lint check 11:

| Field | Meaning |
|-------|---------|
| `corpus_id` | Identifier from `corpus.md` — ties the run to its configuration |
| `experiment` | The `E##` this run was made for, or `null` for a baseline |
| `compare_to` | Path to the report being compared against |
| `run_order` | The actual order the runs executed in — see bias 2 in regime A |

**In markdown a number appears only as a single headline line with a link to the
report.** There are no tables of numbers in `project-workbook/`. Comparisons and history are
generated from the reports, not maintained by hand.

The strictness has a cause. In a project run without this rule, the same handful of
figures lived in four or five files at once, in varying combinations, and the docs
defended themselves with caveats — "the table in A15 is one device in one thermal state,
do not treat its numbers as the tuning" — instead of structure. A caveat is not a
structure. And there was no machine-readable history at all: "how did this metric move
over the last five changes?" had no answer.

---

## 3. Choose your regime

The apparatus below splits in two, and picking the wrong half is a real cost. Copying
someone else's defences against someone else's disease is cargo cult.

| | **Regime A — noisy measurement** | **Regime B — deterministic pipeline** |
|--|--|--|
| Symptom | The same input gives different numbers | The same input gives the same number |
| Typical of | Live hardware, timing, I/O, anything thermal | Batch processing, parsers, scoring, offline models |
| The threat | Noise is mistaken for signal | The reference you score against is itself wrong |
| Verdict rests on | A threshold derived from observed spread | Agreement of independent indicators |

Both regimes share sections 1, 2 and 6. Everything else is regime-specific. State in
your project's `_meta.md` or `DELTA.md` which one you are in; if a project has both
kinds of work, say so per configuration.

---

## 4. Regime A — noisy measurement

### Three biases that ruin a run

These cost several days on the project they were found in. They are about measurement as
such, not about that project — record them as `G##` entries marked **Portable: yes** and
link them from here rather than restating them.

| Bias | What it costs you |
|------|-------------------|
| The ceiling drifts across a session (the device heats up and throttles) | A configuration measured late looks worse than it is |
| A back-to-back A/B is biased by order | Whichever ran first wins, and a spread criterion does not catch it |
| A run that does not force real work measures a buffer | The limiter is on, the screen is off, or unlike quantities are being compared |

### Two rules follow

**Sweep in both directions.** Any comparison of two configurations runs A→B, then B→A,
scored within pairs, with the real order recorded in `run_order`. Reversing the order
must not change the verdict — the cheapest available proof that the method is not
broken.

**Same device state.** Warm-up and cool-down between runs are mandatory. The reasoning
and the way to detect drift belong in the drift `G##`.

### The significance threshold

A difference counts only if it exceeds the **worst spread observed among the runs being
compared, by at least a factor of three**. Below that the verdict is `inconclusive`, not
"a small win".

The threshold is a rule, not a number, and the comparison tool computes it from the
reports themselves. This is deliberate: one configuration in the source project measured
its own noise at 0.42% in one session and 0.84% in another — same build, same day. A
threshold derived once from the luckier of the two would certify differences that are
noise. Nothing about the threshold is settled before the runs exist, and nothing about it
can be chosen after seeing the delta; it falls out of the spreads either way.

The tool must also **refuse outright when a report carries no observed spread**. A single
run has nothing to vary against, and three times zero would certify anything.

---

## 5. Regime B — deterministic pipeline, unreliable reference

There is no spread here and nothing to measure it in, so the entire apparatus of regime
A is **not applied**. The disease is different: not that the measurement is noisy, but
that the reference it is scored against is itself unreliable.

### Three biases that ruin a verdict

| Bias | What it costs you |
|------|-------------------|
| Fitting to a noisy reference | The score rises while the thing being scored gets worse; you have learned the reference's errors |
| Mixing effects | Two components changed in one run; the contributions cannot be separated afterwards, ever |
| Ranking mechanics | The metric responds to the shape of the output rather than to its quality — reordering ties moves the number |

### The verdict rule

A verdict of "this is better" requires **agreement of at least two indicators, of which
at least one does not depend on the reference data**.

A worked example from the source project: after one change the headline correlation
**fell** (0.584 → 0.555) while three reference-independent indicators improved, and the
conclusion rested on those three. A rule that trusted the headline correlation alone
would have given the opposite answer, and it would have been wrong.

Choose the reference-independent indicators once, per project, and write them into
`overview.md` as an invariant. Picking them after seeing the result is the same failure
as writing a prediction after the run.

### Completeness is not quality

Where the work is extraction or collection rather than scoring, the question is usually
"did all of it arrive?", and the answer comes from an external ground truth and from
nothing else. A collector does not know about its own incompleteness: in one build it
flagged 340 suspicious items, and a check against an external list found a shortfall of
574 — 234 of which it had not suspected at all. Internal completeness signals do not
work; this has been tested twice.

---

## 6. Order of operations

1. The configuration is registered in `corpus.md` — or is being registered right now.
2. An `E##` exists with status `open` and a **written prediction**. Open it with
   `python tools/new_experiment.py`, not by editing `experiments.md`: the tool allocates
   the number, writes the index line, and refuses to proceed without a prediction. That
   refusal is the only thing standing between H7 and a rule nobody enforces.
3. The run. In regime A: both directions, warm-up and cool-down, device in a known
   state. In regime B: exactly one component of the configuration changed.
4. The reports land with all required fields written by the harness. A report worth
   keeping becomes a baseline through the curation step, which writes the curated file
   **and copies the raw report next to it**.
5. The comparison. It refuses a verdict unless the run is valid for the regime, derives
   the threshold (A) or checks indicator agreement (B), and prints a line ready for the
   **Result** block.
6. Result as headline lines in the `E##`, plus the verdict. If refuted, the "do not do
   this — `[[E##]]`" line goes into the task.
7. A line in `journal.md`.

Steps 2 and 6 are where knowledge is actually saved. The rest is what makes it true.
