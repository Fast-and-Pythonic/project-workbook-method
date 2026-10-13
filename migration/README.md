# Migration — putting this into a project

Three starting points. Pick the one that matches, then use
[checklist.md](checklist.md) to confirm nothing was missed.

| You have | Read |
|----------|------|
| A new project, or one with no documentation at all | [new_project.md](new_project.md) |
| An existing project with a `CLAUDE.md`, `AGENTS.md` or `.cursorrules` that has grown large | [existing_partial_docs.md](existing_partial_docs.md) |
| An existing project with scattered `.md` files and no system | [existing_no_docs.md](existing_no_docs.md) |

## The one rule for all three

**Do not create empty files.** A file appears on its first real entry. An empty
`architecture.md` teaches an agent that this project has no architecture worth
documenting; an absent one teaches nothing and costs nothing.

The minimum viable set is `start.md` plus `overview.md` plus the root pointer. Everything
else earns its way in.

## The step people skip

Setting up the structure takes an afternoon and does nothing on its own. The method is
the **trigger table** in [RULES.md](../RULES.md): the habit of stopping after a long
debugging session and writing the entry before moving on.

A project with a perfect structure and no trigger discipline ends up with three files
that were accurate in week one, which is worse than having nothing — an agent will
believe them.

Set a reminder if you need one. The most reliable version is a line in your root pointer
file that the agent reads every session: "before finishing, walk the trigger table".
