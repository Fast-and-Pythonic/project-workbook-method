# Scenario: an existing project with scattered notes

The project works, has history, and its knowledge lives in loose `.md` files at the root,
in commit messages, and in people's heads.

## Do not start by writing documentation

The instinct is to sit down and document the whole system. Resist it. A retrospective
write-up is guesswork about what mattered, it takes days, and most of it will never be
read.

Start with the two things that pay immediately.

## Step 1 — harvest the traps you already know

Open `gotchas.md` and write down the things that have already bitten you. Not everything:
the ones you remember without effort. That set is small — usually five to ten — and it is
precisely the set that has cost the most time, which is why you remember them.

Use the [gotcha format](../FORMATS.md). The field that matters most and is hardest to
reconstruct later is **Cause** — the mechanism, not "it turned out not to work". If you
cannot reconstruct the mechanism, write the entry anyway with the cause marked unknown;
the next person to hit it will finish it.

Assign ids once. `G01`…`G09` are permanent from that moment and are never reused.

## Step 2 — write `overview.md` and `start.md`

Now the map. `overview.md`: purpose, stack, structure, invariants, current state.
`start.md`: the map, the situational guide, three critical facts.

The situational guide is easier here than on a new project, because you know what people
actually ask. Every question you have answered more than once is a line in the guide.

## Step 3 — fold in the loose files

| What it is | Where it goes |
|------------|---------------|
| Notes on one module or area | `subsystems/<name>.md` |
| A format spec, third-party API behaviour, upstream state | `references/<spec>.md` |
| A decision with rejected alternatives | `architecture.md` as an `A##` |
| A trap | `gotchas.md` as a `G##` |
| Current state, fragile points | `status.md` |
| History of how things went | `journal.md` — one entry summarising the past, not a reconstruction of every week |
| Instructions for users | Leave in `README.md`. Do not copy it into `project-workbook/` |

Anything that does not fit one of these rows is a candidate for deletion. "It might be
useful" is how a document set becomes unreadable.

## Step 4 — the root pointer

Replace whatever grew at the root with the thin pointer. Everything it used to say must
now exist, in full, inside `project-workbook/` — a pointer holds nothing of its own.

## Step 5 — check it with fresh eyes

Run [REVIEW_PROMPT.md](../REVIEW_PROMPT.md) in a session that has not seen this work.
Section A is the one that matters: can it establish the project's state, what to read
next, and what it must not touch? Whatever it could not find is your remaining backlog —
and it is a much better backlog than the one you would have written by guessing.
