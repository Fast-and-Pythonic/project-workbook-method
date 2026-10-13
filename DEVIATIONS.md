# DEVIATIONS — how to break these rules on purpose

A standard that cannot be departed from is either wrong for most projects or quietly
ignored. This file describes the only sanctioned way to depart from it: **write the
departure down, with its justification, in a file the next session will read.**

Departing "because it suits us better" is not allowed. Once that is permitted, the
standard stops meaning anything and the documents drift back into whatever each session
felt like doing.

---

## 1. The local method folder

A project that departs from the standard keeps its own method folder at the project root:

```
<project>/
├── project-workbook/
│   └── _meta.md          ← thin pointer to the folder below
└── workbook-method/
    ├── README.md         ← what is local and why a local method was needed at all
    └── DELTA.md          ← the list of departures, each justified
```

Anything not stated locally comes from this standard. Where something **is** stated
locally, **the local method wins** — and `project-workbook/_meta.md` says so in one line, so a
session never has to guess which document is in charge.

Do not copy rules from the standard into the local folder. Two sources of truth drift
apart, which is the disease the whole method was written to cure. The local folder holds
deltas and nothing else.

If a project has no departures, it needs no method folder: `project-workbook/_meta.md` points
straight at the standard.

---

## 2. The format of a departure

```markdown
## D1. One-line title of the departure

**Standard:** what it says, with the section reference.

**Locally:** what we do instead. Concrete — a file, a format, a limit.

**Why:** the evidence. What went wrong, on which project, at what size. A
justification that could not be falsified is not a justification.

**Side effect:** what else this fixes or costs. Optional, but it is often the most
useful field — it is where you notice that a departure is really two.
```

Number them `D1`, `D2`, … The numbers are link targets: `[[D5]]` resolves here, and lint
checks it.

**The Why field carries the whole thing.** "Our project is different" is not evidence.
"Our `status.md` reached 349 lines against a 150-line limit, 68% of it a decision log
that had nowhere else to go" is evidence — it names the file, the size and the mechanism,
and anyone can check whether it is true.

Write departures against the *evidence you already have*, not against difficulties you
anticipate. A departure invented in advance is a guess, and guesses accumulate faster
than they are removed.

---

## 3. Legitimate exceptions

Separate from departures, and just as important: places where the project's `project-workbook/`
**breaks the standard deliberately** and must be left alone.

```markdown
## Legitimate exceptions

Places where this project's `project-workbook/` breaks the standard on purpose — recorded so a
future session does not "tidy them up".

- **"No task lists in `project-workbook/`".** Ours are `plan/*.md` — a plan with acceptance
  criteria, not a todo list, and the primary carrier of intent. It stays.
- **Decision log inside `status.md`.** Replaced by `journal.md` — see D2.
```

Without this section, a diligent session will eventually find the violation, fix it,
and delete something load-bearing. This has happened. The section costs four lines and
prevents it.

---

## 4. Promotion back into the standard

A departure is a hypothesis about the standard. When the same mechanism has proven
itself on a **second** project, it stops being a local delta and becomes a candidate for
the standard itself.

That is how most of what is now in [RULES.md](RULES.md) arrived: the experiment
register, the `status`/`journal` split, register indexes, checked links, "measurements
are data", portable entries, and the rule that a rule without a mechanism is only advice
— all were `D##` entries in one project's `DELTA.md` before they were rules here.

Two consequences worth planning for:

- **Attribution, not dependency.** When a local method borrows from a sibling project,
  say so in its README — and keep the normative files self-contained, so nothing breaks
  if that project moves or disappears.
- **Two implementations of one idea is a temporary state.** When a mechanism is promoted,
  the local deltas that carried it collapse to genuine differences of substance. If they
  do not collapse, the promotion was premature.

---

## 5. Demotion: when a rule cannot be enforced here

A hard rule whose mechanism does not exist **in this project** must be demoted to advice
explicitly, in writing, rather than silently left in place.

The commonest cause is a project not under version control, where every rule that leans
on commit history or a pre-commit hook loses its mechanism. The honest response is a
short list:

```markdown
### Demoted to advice (this project is not under version control)

- **Lint before commit.** Run manually as the last step of a session.
- **Deleting the last entry of a register.** Caught by git history elsewhere; caught by
  nothing here. A gap in the middle is still a lint error.

If the project is put under version control, all of these return to hard rules unchanged.
```

Pretending a rule is enforced when it is not is worse than admitting it is a suggestion:
it makes the document set look maintained, which is precisely the state this standard
exists to avoid.

---

## 6. Changing the standard itself

Everything above is about a project departing from the standard. This section is the
reverse: the standard moves, and several projects are held to it.

The hazard is specific. With one shared source and no version identity, every edit
silently re-rules every consumer at once, so no change can be made without first auditing
all of them. A maintainer who notices that stops making changes — and a standard that has
become too expensive to improve is already dead, it just has not been told yet. Two
mechanisms keep the cost down, and neither is new machinery; both are ordinary release
practice.

### 6.1. A version, and what each project is true against

The standard is **tagged**. Every project's `project-workbook/_meta.md` records the version its
documents were last audited against, and the date:

```markdown
Standard: <URL> — audited against v2.1 on 2026-09-12
```

This is the whole decoupling. A project that has not caught up with the standard is
**behind, not broken** — a scheduled piece of work rather than an emergency, and one that
can be done per project, in its own time, by a session that has that project's context
loaded. Without the stamp there is no way to tell "has not caught up" from "was never
compliant", and the two need very different responses.

### 6.2. Three classes of change

| Class | Examples | What existing projects owe |
|-------|----------|----------------------------|
| **Permissive** | A new optional file, a relaxed limit, a new profile or tier, new advice | **Nothing.** They remain valid as they are |
| **Clarifying** | Rewording that does not change what is required | **Nothing** |
| **Tightening** | A new error-level check, a stricter limit, a newly mandatory file | Work — and therefore the rule below |

**A tightening change ships as a warning.** It is promoted to an error only once every
consumer is clean. The mechanism is not invented for this: the linter already separates
errors from warnings, and all that is new is using that separation as a *release policy*
rather than deciding case by case.

The consequence is the point: a tightening change is **inert** until somebody chooses to
act on it. The standard can move ahead of its consumers without dragging them, which is
what makes a single shared source affordable in the first place. H10 is the worked
example — a hard rule that says so in its own row.

### 6.3. Measure the blast radius, do not imagine it

The audit that feels expensive is one command per project. Run the linter across every
consumer and read the error counts; a tightening change that was released correctly moves
the warning count and leaves the error count alone. That is also the regression test for
this policy, and it takes seconds.

Keep a list of the consumers so the sweep is repeatable. **If any consumer is private,
that list does not belong in this repository** — a public standard must not carry an
inventory of private paths. Keep it wherever the private side already lives, and let it
point inward at the standard rather than the other way round.
