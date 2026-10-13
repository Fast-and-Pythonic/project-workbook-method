# REVIEW_PROMPT — cold review of a documentation system

A documentation system can only be judged by someone who did not build it. Everyone
else knows what the files were meant to say, and reads that instead of what they say.

This file holds the prompt for that review. Paste it into a **fresh session** — one with
none of the design conversation in its context. Fill in the four bracketed slots and
delete any section that does not apply.

**Run it on events, not on a calendar.** After a restructuring, and before a milestone.
Three reviews in one day during an initial build each found real defects; once a system
settles, months may pass without one being warranted. The signal that another is due is
a change in shape, not elapsed time.

The prompt deliberately avoids stating what its author believes, so the reviewer is not
primed to agree.

---

```
You are reviewing a documentation system. Do not fix anything — report findings.

The project is [PATH] ([one-line description of what it is and what it is for]).
[If it is a research project, say so: most tasks are hypothesis -> measurement ->
verdict, and most hypotheses are expected to fail.]

Two things are under review:
  1. project-workbook/          — the project documentation.
  2. workbook-method/   — the local rules for keeping that documentation. It claims to
                         be a delta over a standard at [STANDARD URL OR PATH].
     [Omit if the project has no local method folder.]

Read them as a session that has never seen this project before. Report on each of the
following, with concrete file:line evidence rather than impressions.

A. COLD START.
   Starting from project-workbook/start.md, and within a few minutes, can you establish:
   what state the project is in; which task is next and what its acceptance criterion
   is; what has already been tried and rejected; how to take a measurement so that it
   counts as evidence; and what you are forbidden to touch? Name everything you could
   not find, or found only by accident.

B. ARE THE RULES EXECUTABLE?
   RULES.md claims that every hard rule has a real checking mechanism. Test the claim.
   Run `python tools/lint_workbook.py`. Then, for each check it advertises, break it
   deliberately (edit a file, run the linter, revert the edit) and report any check
   that fails to fire, fires for the wrong reason, or is trivial to satisfy without
   meeting the rule's intent. Revert every edit you make.

C. IS IT TRUE?
   Find anything in the docs that contradicts the code or the data. Worth testing
   specifically: do the documented commands and flags match what the tools actually
   accept; does every number quoted in project-workbook/ have a traceable source; does the run
   configuration register agree with the report files on disk; do the paths mentioned
   in the docs exist.

D. DUPLICATION AND CONTRADICTION.
   The design forbids one fact living in two places, on the grounds that two sources
   of truth drift apart. Find any statement that exists in two files and could drift,
   and any two files that already disagree.

E. DESIGN CRITIQUE.
   Where is this over-engineered — a rule nobody will follow, a file nobody will read,
   ceremony that costs more than it saves? Where is it under-engineered — something
   that will break as the docs grow, or knowledge that has nowhere to go? If you think
   the whole approach is wrong, say so and say why. The author wants disagreement, not
   confirmation; a review that finds nothing is a review that was not done.

F. FALSIFIABLE CLAIMS ABOUT OTHER PROJECTS (optional).
   [If your DELTA.md justifies decisions with empirical claims about a sibling project
   — file sizes, an entry rewritten three times, subsystems built and discarded — name
   that project's path here and ask the reviewer to check whether the claims hold.]

Constraints: read-only apart from the deliberate lint-breaking in B, which you must
revert. Do not implement fixes. Do not reorganise anything. Rank your findings by how
much damage they would do if left alone, and say plainly which ones you would ignore.

For every finding where something is required but held up only by words — a rule, an
instruction to the agent, a step everyone is expected to remember — add one line:
"Mechanism: exists (which) / can be built (what: a lint check, a hook, a pre-commit, a
script that refuses) / cannot (why)."
```

---

## Why each section is there

**A — cold start** is the only test of the thing the system exists for. Everything else
is hygiene; if a fresh session cannot orient itself in a few minutes, the hygiene does
not matter.

**B — executable rules** is the test of principle 2.5. A linter that advertises a check
it does not really perform is worse than no linter, because the rule it backs is then
believed to be enforced. Breaking each check deliberately is the only way to find out;
reading the source is not, since the bug is usually a regex that matches nothing.

**C — truth** catches the failure mode that does actual damage. A missing document costs
a session some time; a lying document costs it a working feature.

**D — duplication** finds tomorrow's contradictions today. Two copies of a fact are not
yet a defect; they are a defect with a delay.

**E — design critique** is where the review earns its cost. The instruction that the
author wants disagreement is load-bearing: without it, a reviewer will find the system
impressive and say so, which is worth nothing.

**The "Mechanism:" line** applies principle 2.5 to the review itself. Without it, a reviewer
reports "this is held up only by a sentence" and the author picks the cheapest remedy —
another default, a firmer sentence — because the question "could a hook or a check enforce
it?" belongs to the moment a rule is added, and a review finds old rules. In one session
the reviewer flagged exactly such a rule, the fix chosen was a default value, and the hook
that settled it came from the user, later in the same session. The line makes the reviewer ask.

**F — falsifiable claims** keeps the justifications honest. A departure justified by
"our sibling project's `status.md` hit 349 lines" invites the question of whether it did.
If nobody ever checks, the justifications decay into folklore.
