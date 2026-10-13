<!-- Copy to the project root as ONBOARDING.md. It is for a person who has just cloned the
     project — not for the agent, which reads AGENTS.md and project-workbook/. Keep it to
     what that person installs and enables; how the code works belongs in the workbook.
     Lint check 21 warns when this file is absent and when a link in it is broken. -->

# Joining <project name>

<One sentence: what this project is, and where a newcomer starts reading — usually
`project-workbook/start.md`.>

## What works with nothing installed

- **[`project-workbook/`](project-workbook/start.md)** — the project's working notes: the
  map, the current state, the gotchas (`G##`) and decisions (`A##`) that cost time to
  find. Plain Markdown; start at `start.md`.
- **[`AGENTS.md`](AGENTS.md)** — the pointer any coding agent reads first. It sends the
  agent to the workbook; whatever agent you use, it works without setup.

## Command-line tools

**Required:**

- **Python 3.8+** (3.11+ to read `tools/lint_workbook.toml`) — runs the workbook linter.
- **The commit hook**, once per clone:

  ```bash
  git config core.hooksPath tools/hooks
  ```

  Before each commit it lints the workbook, and when code is staged with no workbook
  change it prints the update triggers — a reminder, it never blocks the commit.
- **The Project Workbook tools** — either the standard checked out beside this
  repository (`../project-workbook-method`), or installed:

  ```bash
  pipx install git+https://github.com/Fast-and-Pythonic/project-workbook-method
  ```

- <the project's own build tools: toolchain, SDK, versions>

**Recommended:**

- [`rg`](https://github.com/BurntSushi/ripgrep) — fast search; agents use it when present.
- [`ast-grep`](https://ast-grep.github.io/) — structural search and rewrite over code.
- <anything else that makes work here faster, with why>

## Claude Code

What this repository ships for Claude Code, and how to turn it on. Each item is optional:
the project works without any of them.

- **Loaded with the repository** once you trust the folder: <hooks in
  `.claude/settings.json`, skills in `.claude/skills/`, MCP servers in `.mcp.json` — or
  "nothing">.
- **Mods you enable yourself.** A repository cannot turn a mod on for a visitor; each
  person installs it for themselves. From a terminal session:

  ```
  /plugin install workbook-loader --marketplace Fast-and-Pythonic/project-workbook-method
  /plugin install workbook-triggers --marketplace Fast-and-Pythonic/project-workbook-method
  ```

  - `workbook-loader` puts `start.md`, `status.md` and the newest journal entries into
    the session before its first turn, in full.
  - `workbook-triggers` asks, at the end of a turn with signs of recordable work, whether
    an update trigger fired, and has the agent write the entry before it stops.

## What the authors use and you do not need

<Personal setup visible in the history or the docs that a newcomer can ignore: private
notes the docs refer to, the authors' own agents and hooks, machine-specific paths.
"Nothing" is a fine answer.>
