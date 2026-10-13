# workbook-loader

A Claude Code mod (a plugin of function hooks) that does step 1 of the session protocol
before the first turn: it puts the project's `project-workbook/start.md`,
`project-workbook/status.md` and the newest entries of `project-workbook/journal.md` into
the model's context, whole, as one block.

## What it does

At session start (and again on resume, `/clear` and compaction, when Claude Code raises
`SessionStart` again) it looks for `project-workbook/start.md` in the session's working
directory, then at the root of the git repository that directory is in. Where there is
none it does nothing and says nothing.

Where there is one, it adds one block of context:

- a first line telling the model that step 1 is done and the files need not be re-read;
- `start.md` in full;
- `status.md` in full, if present;
- the newest journal entries (`## YYYY-MM-DD — ...` headings, FORMATS.md), 4 by default,
  without the journal's index.

Each part is wrapped in `<file path="...">` with the file's path.

The command hook [`../../hooks/claude-code-session-start.sh`](../../hooks/claude-code-session-start.sh)
can carry `start.md` alone, capped at 8 KB: Claude Code turns a command hook's output over
about 10 KB into a file and a 2 KB preview. Context returned by a hooks module is not cut
that way; a run on a workbook of 24 KB (start, status and four entries) had the model
quote the last line of each part.

## Installing both

The mod hooks `classic.SessionStart`, which sits above the settings `SessionStart` hooks
and receives their `additionalContext`, one entry per hook. It drops any entry that
contains the opening of this project's `start.md` verbatim (the command hook's copy, cut
or not) and passes every other hook's context through. So the mod and the command hook
can both be installed: with the mod loaded the model gets `start.md` once, from the mod;
where the mod is unavailable, or its hook fails (a failed hook is skipped), the command
hook's copy stays.

## Enabling it

From a terminal session, installed from the standard's marketplace:

```
/plugin install workbook-loader --marketplace Fast-and-Pythonic/project-workbook-method
```

Or run it from this folder:

- **One session:** `claude --plugin-dir <path to this folder>`.
- **Every session for this user:** name the folder in `CLAUDE_CODE_PLUGIN_DIRS`, either in
  the process environment or in the `env` block of the user's `~/.claude/settings.json`.
  Several folders are separated by the platform's path-list separator (`;` on Windows,
  `:` elsewhere). This is also the way for sessions started by the desktop app or an SDK
  host, where no command-line flag can be given.

The number of journal entries is the option `journalEntries` (0 loads none), set in user
settings:

```json
{ "pluginConfigs": { "workbook-loader": { "options": { "journalEntries": 6 } } } }
```

**A repository cannot turn the mod on for a visitor.** Project settings
(`.claude/settings.json`) cannot set `CLAUDE_CODE_PLUGIN_DIRS`, and a marketplace a
repository declares, or a plugin under its `.claude/skills/`, loads only with the
person's consent. Each person enables it for themselves.

**Where mods are unavailable** (cloud sessions, older Claude Code, a policy that turns
plugins off), the command hook `tools/hooks/claude-code-session-start.sh` remains the
fallback: `start.md` only, and the agent reads `status.md` and the journal itself.

## Checking it

```bash
claude plugin validate <this folder>
claude plugin test <this folder>
```

With `--debug`, each session start writes a line `workbook-loader: <bytes> bytes from
<root> (<n> journal entries); dropped <k> other hook copies of start.md`.

The plugin API is early access and may change between Claude Code releases; this mod was
written against 2.1.296.
