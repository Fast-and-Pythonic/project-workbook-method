# Project Workbook

A standard for a project's working notebook — `project-workbook/` — written to be read by
an AI coding agent and checked by a linter, so it stays true. A workbook, not
documentation: user guides stay in `README.md` and `docs/`; this folder holds what the
work itself taught — state, decisions, traps — and is written as the work happens.

Not a prompt library and not a set of rules for the agent's behaviour. It is a place to
put the knowledge a session pays for and would otherwise throw away.

---

## The problem in three lines

An agent reads your code and recovers **what** the project does. It cannot recover why
this approach was chosen, what was tried and discarded, which harmless-looking line is
load-bearing, or what will break. That knowledge costs hours to produce and vanishes
when the session ends.

Context inheritance does not fix it. Forking a session or sharing a prompt cache spreads
knowledge *sideways*, between agents working right now; it does nothing *forward*, into
next week's session. It also inherits quality — a root context that guessed the project
from source passes the guess, errors included, to everything downstream.

## What an entry looks like

The unit of the system is a numbered entry, titled by the symptom you were staring at:

```markdown
## G07. Sourcemaps break MAIN-world injection
**Context:** packaging the extension for the store; worked in dev, not in production.
**Symptom:** the `window.fetch` patch never applies. No errors in DevTools;
`window._patching` stays `undefined`.
**Cause:** Vite defaults to `build.sourcemap: true`. Chrome MV3 refuses to run scripts
carrying a sourcemap comment in the MAIN world — extension-specific, not documented.
**Fix:** set `build.sourcemap: false` in `vite.config.ts`. `'inline'` and `'hidden'`
do **not** work either.
**How to spot it:** works in dev, fails in production → grep `dist/` for
`sourceMappingURL`. If it is there, this is it.
**Portable:** yes — MV3 extension packaging
```

That is forty minutes of debugging, written down once. `G07` is a stable anchor: other
documents, commit messages and the situational guide all link to it, and the linter
checks that every such link resolves.

---

## Quick start

**New project.** Copy [templates/](templates/) into `<project>/project-workbook/`, copy the root
pointer to the project root as `AGENTS.md` — read by Claude Code, Codex, Cursor and others — from
[templates/root_pointer.md](templates/root_pointer.md), add
[templates/ONBOARDING.md](templates/ONBOARDING.md) beside it for the people who join, and
fill in `start.md` and `overview.md`. Everything else is created on its first real entry — never empty.

**Existing project.** See [migration/](migration/); there is a scenario for each starting
point.

**Then, on every session:** read `start.md`, work, and walk the trigger table in
[RULES.md](RULES.md) before you stop. That last step is the whole method. The structure
does nothing on its own.

```bash
python tools/lint_workbook.py --docs path/to/project-workbook --profile engineering
```

Or install the two tools and depend on a version of them rather than on a path —
`pipx install git+https://github.com/Fast-and-Pythonic/project-workbook-method` gives you
`workbook-lint` and `workbook-index`. See [tools/README.md](tools/README.md), which also
says why the tools may be copied while the prose may not.

---

## Map

| File | What is inside | When to read |
|------|----------------|--------------|
| [METHODOLOGY.md](METHODOLOGY.md) | Principles, the file inventory, layered loading, anti-patterns | **First.** Read it whole once |
| [RULES.md](RULES.md) | The normative part: triggers, session protocol, hard rules and the mechanism behind each, what lint checks | When you want to know what is mandatory |
| [FORMATS.md](FORMATS.md) | Anatomy of `G##` / `A##` / `E##`, indexes, `[[links]]`, journal entries | When writing an entry |
| [MEASUREMENT.md](MEASUREMENT.md) | The measurement contract, in two regimes | **Before** any measurement |
| [DEVIATIONS.md](DEVIATIONS.md) | How to break these rules on purpose without dissolving the standard | When something here does not fit |
| [REVIEW_PROMPT.md](REVIEW_PROMPT.md) | Cold review of a documentation system by a fresh session | After a restructuring, before a milestone |
| [profiles/](profiles/) | The two axes: [engineering](profiles/engineering.md) · [research](profiles/research.md), and the `S`/`M`/`L` tier | When setting up |
| [templates/](templates/) | Skeletons to copy | Starting a file or an entry |
| [examples/](examples/) | Filled-in entries from real projects | When a template is not enough |
| [migration/](migration/) | Adoption scenarios | Once, at the start |
| [tools/](tools/) | The linter, the index generator and the experiment opener | Every session |

---

## Two ideas worth stealing even if you ignore the rest

**A rule without a mechanism is advice.** If a rule cannot be checked by a linter or
executed by one command, it is demoted to advice — in writing — or dropped. A
five-manual-step ritual stops being performed by the third session, and a rule that is
nominally mandatory but silently unenforced is worse than an honest suggestion: it makes
the whole document set look maintained when it is not.

**Negative results get their own shelf.** "Built it, measured it, threw it away" is the
most expensive knowledge a project produces and the first thing to evaporate. A refuted
hypothesis is never deleted, its number is never reused, and its verdict leaves a line in
the task that tempted it — because an archive nobody opens at the moment of temptation is
not a defence.

---

## Glossary

| Term | Meaning |
|------|---------|
| **Gotcha (`G##`)** | A trap that has already cost time and will again. Titled by symptom |
| **Decision (`A##`)** | A settled decision about how the project is built, with rejected alternatives |
| **Experiment (`E##`)** | A hypothesis tested by measurement — recorded whatever the outcome |
| **Register** | A growing file of numbered entries, opened by an index |
| **Index line** | One line per entry at the head of a register: ID, status, title |
| **Run configuration** | The set of things that must match before two measurements may be compared |
| **Portable entry** | Knowledge not tied to this codebase; a candidate for a shared layer |
| **Capture at friction** | Record it at the moment of pain, not "later" |
| **Layered loading** | File size matches load frequency; big files load on a trigger |
| **Legitimate exception** | A deliberate violation, recorded so nobody "fixes" it |
| **Cold review** | An audit by a reader who did not build the system |

---

## Honest limits

This is a personal standard, derived from a handful of real projects — an Android
application with a native engine, a browser extension, an emulator fork, a CEFR text
analyser — and generalised afterwards. It is not a silver bullet and it is not free.

- **It costs discipline.** The trigger table is the method; a project that skips it ends
  up with an empty structure and the illusion of documentation.
- **Stale is worse than absent.** A document that lies will be believed by an agent that
  cannot check it. Delete a section you cannot keep true.
- **The research profile is heavier than most projects need.** Turn it on when hypotheses
  and measurements actually appear, not in advance.
- **Some of the rules here are one project's evidence generalised to all.** Where a rule
  does not fit your work, [DEVIATIONS.md](DEVIATIONS.md) is the sanctioned way to depart
  from it — write down what you do instead, and why.

---

## Licence

[MIT](LICENSE), for the whole repository — the documents as well as the code. Use it,
adapt it, fork it, ship it in something commercial. Attribution is appreciated and, apart
from keeping the licence text, not required.
