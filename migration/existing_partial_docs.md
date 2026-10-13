# Scenario: a pointer file that grew too large

The commonest starting point. There is a `CLAUDE.md`, an `AGENTS.md`, a `.cursorrules` or a
`copilot-instructions.md` at the root, it started at twenty lines, and it is now several
hundred. Every session loads all of it, and nobody is sure which parts are still true.

## Why this hurts

Three separate problems, and splitting the file fixes all three at once.

**Everything loads every time.** A trap that matters only when touching the build is
being read at the top of every session, including the ones that never go near it. That is
the layered-loading principle violated in its purest form.

**Volatility classes are mixed.** The stack description changes once a year; the list of
what currently works changes weekly. In one file, the weekly edits bury the annual ones,
and nobody re-reads the parts that did not change — which is exactly where staleness
hides.

**There are no anchors.** You cannot link to "the third paragraph about the build" from a
commit message, from a task, or from another document. Numbered entries exist so that you
can.

## The split

Go through the file top to bottom and send each paragraph to its destination. Do not
rewrite while splitting — move first, edit afterwards, or you will do both badly.

| What it says | Where it goes |
|--------------|---------------|
| What the project is, stack, directory tree | `overview.md` |
| Rules of the project no linter can check | `overview.md`, as **invariants** |
| Naming, formatting, build and test commands, what not to auto-format | `conventions.md` |
| "Careful, X breaks if Y" | `gotchas.md` as a `G##` — reconstruct the mechanism if you can |
| "We do it this way because Z" | `architecture.md` as an `A##` |
| "Currently broken / not implemented / postponed" | `status.md` |
| "Do not do X, we tried it" | `gotchas.md`, or an `E##` if it was measured **[R]** |
| Instructions addressed to the agent's behaviour | Stay at the root, in the pointer — only those that pass the admission test in METHODOLOGY §5, each also stated in `project-workbook/` |

Two categories deserve a decision rather than a destination:

- **Anything derivable from the source** — function lists, signatures, import graphs.
  Delete it. It is already stale, and the agent reads it faster from the code.
- **Anything you cannot confirm is still true.** Do not carry it across. Either verify it
  now or delete it; a claim you were unsure about will be believed by a session that has
  no way to check.

## Assign ids once

As traps and decisions come out of the old file, number them. `G01`, `G02`, `A01`. From
that moment the numbers are permanent and are never reused, even if an entry is later
found to be wrong — a hole in the numbering means a deleted entry, and lint treats it as
an error.

Sort by nothing. Do not group by theme, do not renumber for tidiness. Order of arrival is
fine; the index at the top of the register is what makes them findable.

## Then shrink the root file

What remains at the root is five to fifteen lines: one sentence about the project, the
order to read `project-workbook/start.md` first, and the critical rules that pass the admission
test in [METHODOLOGY §5](../METHODOLOGY.md#5-tool-independence). Nothing in it may be
absent from `project-workbook/` — a pointer file holds no knowledge of its own.

If a rule feels too important to leave out of the pointer, that is a signal it belongs in
`start.md`'s "three facts to know up front", where it will be read anyway.

## Verify the split worked

The test is not that the files look tidy. It is:

1. A fresh session, given `start.md` alone, reaches the right file for a given task.
2. Nothing appears in two places. Run through
   [REVIEW_PROMPT.md](../REVIEW_PROMPT.md) section D specifically — duplication created
   during a split is the single commonest defect, because moving a paragraph and copying
   it look identical while you are doing it.
3. The linter passes: every `[[link]]` you introduced while splitting resolves.
