# Example: a deviation with its justification

A real `D##` from a project that departs from this standard on purpose. See
[DEVIATIONS.md](../DEVIATIONS.md) for the mechanism.

---

## D2. `status.md` splits into state and chronicle

**Standard:** `status.md` holds Working / Fragile points / Deferred / **Decision log**,
limit 150 lines, one line per log entry: `- YYYY-MM-DD — <decision> — <reason>`.

**Locally:** `status.md` holds state only, rewritten in place, ≤80 lines. The chronicle
moves to `project-workbook/journal.md` — append-only, newest on top.

**Why:** the neighbouring project's `status.md` is 349 lines, more than double the
standard's own limit, and 236 of them (68%) are the decision log, with individual entries
running to 34 lines instead of the prescribed one. This is not sloppiness: one line
genuinely cannot hold a real decision together with its measurements and its rejected
alternatives. Two volatility classes are mixed — a rewritable snapshot and a growing
journal — and the growing one crowds out the snapshot.

**Side effect:** with a chronicle available, `A##` entries stop absorbing narrative they
were never meant to hold, and the register goes back to holding settled decisions only.

---

## What makes this deviation legitimate

**The evidence is specific and falsifiable.** A file, a line count, a percentage, a limit
it exceeds. Anyone can open that project and check whether the claim holds — and the
[cold review prompt](../REVIEW_PROMPT.md) has a section that asks a reviewer to do
exactly that. A justification nobody can check decays into folklore.

**It names the mechanism, not the discomfort.** "Two volatility classes are mixed and the
growing one crowds out the snapshot" explains why this recurs and why the fix is a split
rather than a bigger limit. "The file got long" would explain neither.

**The replacement is concrete.** A file, a limit, an ordering rule. A deviation that says
"we are more flexible about this" is not a deviation; it is an exemption.

**It was written from evidence already in hand, not from anticipated difficulty.** A
departure invented in advance is a guess, and guesses accumulate faster than anyone
removes them.

**It was promoted.** This deviation is now part of the standard — the `status`/`journal`
split in [RULES.md](../RULES.md) is this entry, generalised after it had proven itself on
a second project. That is the intended life cycle: a `D##` is a hypothesis about the
standard, and two independent confirmations retire it into the standard itself.
