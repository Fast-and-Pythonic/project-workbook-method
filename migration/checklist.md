# Migration checklist

Works for a new project or an existing one.

## Base

- [ ] Create `project-workbook/` at the project root
- [ ] Copy `templates/root_pointer.md` to the root as `AGENTS.md` (an existing `CLAUDE.md` is renamed, not kept beside it) / `.cursorrules` /
      `.github/copilot-instructions.md`; fill in the name and only the critical rules that pass
      the admission test in METHODOLOGY §5, each naming where in `project-workbook/` it is stated
- [ ] Copy `templates/start.md` → `project-workbook/start.md` and fill it in
- [ ] Copy `templates/overview.md` → `project-workbook/overview.md`; fill in purpose, invariants,
      stack, structure
- [ ] Copy `templates/_meta.md` → `project-workbook/_meta.md`; set the profile, the language, and
      the link to the standard
- [ ] Choose a profile: [engineering](../profiles/engineering.md) or
      [research](../profiles/research.md)
- [ ] Copy `tools/lint_workbook.py` and `tools/lint_workbook.toml`; set the paths and limits
- [ ] Run the linter once. It should pass on an almost-empty document set

## As the project grows

- [ ] First trap that cost time → create `gotchas.md`, write `G01`
- [ ] First settled decision → create `architecture.md`, write `A01`
- [ ] First fragile point or deferred feature → create `status.md`
- [ ] First entry worth remembering a month later → create `journal.md`
- [ ] A subsystem passes ~50-80 lines of documentation → `subsystems/<name>.md` **[E]**
- [ ] An external spec matters → `references/<spec>.md` **[E]**
- [ ] First hypothesis to be tested by measurement → turn on the research profile:
      `experiments.md`, `corpus.md`, `plan/` **[R]**

## For an existing project

- [ ] Split the existing large pointer file by destination:
      stack and structure → `overview.md`; code style → `conventions.md`; decisions →
      `architecture.md` as `A##`; traps → `gotchas.md` as `G##`
- [ ] Replace the root file with the thin pointer
- [ ] Leave `README.md` alone. It is for users; do not duplicate it into `project-workbook/`
- [ ] Move loose `.md` files at the root into `subsystems/` or `references/` by topic
- [ ] Renumber nothing later: assign `G##` / `A##` ids once, at import, and never reuse them

## Verify

- [ ] A fresh session, given only `start.md`, can say what state the project is in and
      what to read next
- [ ] `start.md` ≤ 150 lines, `status.md` ≤ 150
- [ ] Every register has an index, and the ids match the bodies
- [ ] Nothing is duplicated between `overview.md`, `architecture.md` and `subsystems/*`
- [ ] The linter passes
- [ ] Deliberate violations are recorded as legitimate exceptions, not left to be
      discovered and "fixed"
- [ ] Run [REVIEW_PROMPT.md](../REVIEW_PROMPT.md) in a fresh session and act on what it
      finds
