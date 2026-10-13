#!/usr/bin/env bash
# Claude Code SessionStart hook: load project-workbook/start.md into context before the
# first turn, so step 1 of the session protocol does not depend on the agent
# deciding the task is big enough to count as "starting work" (RULES.md §3,
# METHODOLOGY.md §2.5).
#
# Install in ~/.claude/settings.json (every project) or .claude/settings.json:
#
#   "hooks": { "SessionStart": [ { "hooks": [ {
#       "type": "command",
#       "command": "bash /path/to/claude-code-session-start.sh",
#       "timeout": 10 } ] } ] }
#
# Needs jq. Looks in the session's cwd, then at the root of the git repository
# the cwd is in; silent when there is no project-workbook/start.md, so it is safe to
# install globally.
#
# Only start.md, and never more than MAX_BYTES of it. Claude Code does not put a
# large hook output into context: past roughly 10 KB it saves the output to a
# file and shows the agent a 2 KB preview, which looks loaded while missing its
# tail. The cut is made at a whole line and says so.

set -u

MAX_BYTES=${MAX_BYTES:-8000}

input=$(cat)
cwd=$(printf '%s' "$input" | jq -r '.cwd // empty' 2>/dev/null)
[ -n "$cwd" ] || cwd="${CLAUDE_PROJECT_DIR:-$PWD}"
command -v cygpath >/dev/null 2>&1 && cwd=$(cygpath -u "$cwd")

root=""
if [ -f "$cwd/project-workbook/start.md" ]; then
   root="$cwd"
else
   top=$(git -C "$cwd" rev-parse --show-toplevel 2>/dev/null)
   [ -n "$top" ] && [ -f "$top/project-workbook/start.md" ] && root="$top"
fi
[ -n "$root" ] || exit 0

body=$(LC_ALL=C awk -v max="$MAX_BYTES" '
   { n += length($0) + 1; if (n > max) { cut = 1; exit } print }
   END { if (cut) printf "\n[cut by the session-start hook to fit the context limit - read the rest of project-workbook/start.md yourself]\n" }
' "$root/project-workbook/start.md")

context="Below is project-workbook/start.md of $root, loaded by a hook before the first turn. Its routing (what to read when) applies to every task, including one that looks like a small edit. The session protocol is not finished: read project-workbook/status.md and the top entries of project-workbook/journal.md yourself."$'\n\n'"$body"

jq -n --arg ctx "$context" '{
   hookSpecificOutput: {
      hookEventName: "SessionStart",
      additionalContext: $ctx
   }
}'
