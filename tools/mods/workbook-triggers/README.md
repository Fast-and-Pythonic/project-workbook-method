# workbook-triggers

A Claude Code mod (a plugin of function hooks) that applies the update triggers of
[RULES.md §2](../../../RULES.md#2-update-triggers) at the end of a turn, while the work is
still in the agent's context, instead of leaving them to the agent's memory.

## What it does

During the session it counts three cheap signs, each since the last edit of any
`project-workbook/` file:

- edits of code files (any path that is not Markdown, not in the workbook, not under
  `_backups/`), by `Edit`, `Write`, `MultiEdit` or `NotebookEdit`, the agent's or a
  subagent's;
- failed `Bash` or `PowerShell` runs ending in the same error (the first line after the
  `Exit code N` header, numbers folded);
- minutes of model turns.

When a turn ends and one sign has crossed its threshold, in a project with a workbook, it
asks a **fork** of the session (`$.model.fork`: the main thread's own transcript, served
from the prompt cache, with one question after it and every tool denied) whether the work
met a trigger whose entry is not written yet. The fork answers `NONE` or `WRITE` with up
to three lines `trigger -> file: what`. On `WRITE` the mod blocks the stop with that list,
and the agent writes the entries before it finishes. On `NONE` the stop goes through. In
both cases the counts start over.

The mod never writes the workbook: the agent does, with the index check and the formats
it already follows. A stop the agent was already sent back from (`stop_hook_active`) is
let through, so it re-prompts at most once per turn.

Before a compaction with signs pending it asks nothing (the summarizer is already a long
request) and adds to the summarizer's instructions: keep any non-obvious cause, settled
decision, fragile point or deferral, with the details needed to record it. The check at
the end of the turn then still has them.

## Cost

One fork per crossed threshold, and only then. Measured on a small session (Sonnet, about
54k tokens of context): 2.2 s, 54k tokens read from cache, about 700 fresh input tokens,
5 output tokens for `NONE`, about 120 for `WRITE`. The fork runs on the session's own
model; a prefix whose cache entry lapsed is billed afresh once.

## Enabling it

From a terminal session, installed from the standard's marketplace:

```
/plugin install workbook-triggers --marketplace Fast-and-Pythonic/project-workbook-method
```

Or run it from this folder, as for [workbook-loader](../workbook-loader/README.md):
`claude --plugin-dir <this folder>` for one session, or the folder named in
`CLAUDE_CODE_PLUGIN_DIRS` for every session. A repository cannot enable it for a visitor.

Thresholds are options in user settings; 0 turns a sign off:

```json
{ "pluginConfigs": { "workbook-triggers": { "options": { "minCodeEdits": 3, "failureRun": 3, "workMinutes": 30 } } } }
```

The harness-neutral layer of the same table is
[`tools/check_triggers.py`](../../check_triggers.py) in the pre-commit hook: it works
without Claude Code and reminds at commit time; this mod reminds at the end of the turn.

## Checking it

```bash
claude plugin validate <this folder>
claude plugin test <this folder>
```

With `--debug`, each check writes a line `workbook-triggers: <n> signs; fork says NONE`
(or `WRITE <k>`). The counts live in the module: a reload of the mod starts them over.

The plugin API is early access and may change between Claude Code releases; this mod was
written against 2.1.296.
