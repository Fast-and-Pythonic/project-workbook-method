# Profiles and tiers — the two axes

A project's document set is adjusted along two axes that do not interact. Pick one value
on each and record both in `project-workbook/_meta.md`.

| Axis | Answers | Values | Defined in |
|------|---------|--------|------------|
| **Profile** | What kind of work is this? | [engineering](engineering.md) · [research](research.md) | These files |
| **Tier** | How much of the inventory has it earned? | `S` · `M` · `L` | [RULES.md §6](../RULES.md#6-tiers-and-scaling) |

A research project can be small and an engineering project can be large; the combinations
are all legitimate, which is why these are two axes rather than one list of project types.

## What each may change

**A profile may add files and machinery.** The research profile brings the `E##` register,
the run-configuration register, `plan/` and the measurement contract, and with them hard
rules H6–H9 and lint checks 9–16. The engineering profile brings `conventions.md`,
`subsystems/` and `references/`. Both switch the other's machinery off.

**A tier may change the inventory and the limits, and nothing else.** Triggers, entry
formats, session protocol and hard rules H1–H5 and H10 are identical at every tier. This
is the constraint that keeps one standard from quietly becoming three: if a change you
want to make under a tier would alter *what counts as a defect*, it is not a tier change
— it is either a departure ([DEVIATIONS.md](../DEVIATIONS.md)) or a change to the
standard.

## Choosing

**Profile:** start with engineering. Turn the research profile on for the work that
actually produces hypotheses and measurements, rather than in advance — it is heavier
than most projects need, and an unused `E##` register teaches an agent that this project
does not test its beliefs.

**Tier:** count the areas a session has to hold in its head — in practice, the subsystem
pages the project has earned under the engineering profile's 50–80 line rule. One is `S`,
two to four `M`, five or more `L`. A register past the split threshold also means `L`
whatever the area count says, because the bottleneck it names is the same one.

Both are recorded settings, not judgements to be re-made each session. Re-examine a tier
when a register splits or a subsystem page is added, not otherwise.

## Moving up a tier

Going up is ordinary work, not a migration: the files a tier adds are created on their
first real entry like any other, and the limits that change are checked by the linter.
Nothing already written becomes invalid — a tier is a statement about what is *expected*,
so a project that gains an area gains an expectation, not a defect.

Going back down happens, and is equally unremarkable. A project that consolidates two
subsystems into one has fewer areas; its register does not un-split, but its limits
relax. Record the change in `_meta.md`, where the tier lives.
