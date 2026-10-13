<!-- Copy to the project root as AGENTS.md. Do not keep a CLAUDE.md beside it: Claude Code
     then reads only CLAUDE.md (METHODOLOGY §5). A tool that does not read AGENTS.md gets
     the same content under its own name (.cursorrules, .github/copilot-instructions.md). -->

# <project name>

<One sentence: what this project is.>

**Read `project-workbook/start.md` before acting on any task, a one-line edit included.** It routes
each kind of task to the file that task needs.

**This file is a pointer. Never add rules or knowledge here** — they go into `project-workbook/`.

## Critical rules

- <rule> (`project-workbook/<file where it is stated>.md`, or a register id such as G04)

<!--
Keep this file short: about 5-15 lines. Lint warns past five rules or twenty lines.

A rule goes here only if both hold (METHODOLOGY §5):
  - it applies to every task in the project, not to a kind of task;
  - breaking it before start.md is read is expensive or irreversible.
Anything else belongs in start.md's three facts or its routing.

Every rule names where in project-workbook/ it is stated — lint check 19 (H11) fails otherwise.
Nothing here may be absent from project-workbook/: this is a pointer, not a second home.
No rules at all is fine; then drop the section.
-->
