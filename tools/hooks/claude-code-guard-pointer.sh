#!/usr/bin/env bash
# Claude Code PreToolUse hook: an edit to the root pointer (AGENTS.md, or a
# CLAUDE.md not yet renamed) of a project kept to this standard stops and asks the person, with the reason shown to both sides
# (METHODOLOGY.md §5, "a pointer, not a second home"; §2.5).
#
# Install in ~/.claude/settings.json (every project) or .claude/settings.json:
#
#   "hooks": { "PreToolUse": [ {
#       "matcher": "Write|Edit|MultiEdit|Bash|PowerShell",
#       "hooks": [ {
#          "type": "command",
#          "command": "bash /path/to/claude-code-guard-pointer.sh",
#          "timeout": 10 } ] } ] }
#
# Needs jq. Takes effect from the next session: hooks are read when a session
# starts, so an edit in the session that installed it goes through unasked.
#
# Why a hook: the pointer is the one file a session knows is loaded every time,
# so it is where a session reaches when told "write this down so it does not
# happen again". It did, in a project whose pointer already said it was a
# pointer — the words sat in the very file being edited and did not stop it.
# Lint check 19 (H11) catches a rule with no home in project-workbook/ at commit time;
# this catches the moment of writing, which is where the decision is made.
#
# "ask", not "deny": editing the pointer is sometimes right, and the person is
# the one to say so. With no one to ask (claude -p), "ask" acts as a refusal.
#
# Scope: only an AGENTS.md or CLAUDE.md whose directory holds
# project-workbook/start.md, so a global ~/.claude/CLAUDE.md and folders outside the standard are untouched. Shell
# writes are caught by a coarse pattern (redirect, sed -i, tee, Set-Content,
# Out-File, cp/mv onto it); a write that slips past the pattern is not caught.

set -u

input=$(cat)
tool=$(printf '%s' "$input" | jq -r '.tool_name // empty')
cwd=$(printf '%s' "$input" | jq -r '.cwd // empty')
command -v cygpath >/dev/null 2>&1 && [ -n "$cwd" ] && cwd=$(cygpath -u "$cwd")

is_pointer() {   # $1: directory that holds the pointer
   [ -f "$1/project-workbook/start.md" ]
}

hit=""
case "$tool" in
   Edit|Write|MultiEdit)
      path=$(printf '%s' "$input" | jq -r '.tool_input.file_path // empty')
      command -v cygpath >/dev/null 2>&1 && path=$(cygpath -u "$path")
      base=$(basename "$path")
      shopt -s nocasematch
      [[ "$base" == "AGENTS.md" || "$base" == "CLAUDE.md" ]] && is_pointer "$(dirname "$path")" && hit="$path"
      shopt -u nocasematch
      ;;
   Bash|PowerShell)
      cmd=$(printf '%s' "$input" | jq -r '.tool_input.command // empty')
      if printf '%s' "$cmd" | grep -qiE '(AGENTS|CLAUDE)\.md' &&
         printf '%s' "$cmd" | grep -qiE '>[^&]*(AGENTS|CLAUDE)\.md|sed[^|;]*-i|tee |Set-Content|Add-Content|Out-File|(cp|mv|Copy-Item|Move-Item) [^|;]*(AGENTS|CLAUDE)\.md'; then
         root="$cwd"
         top=$(git -C "$cwd" rev-parse --show-toplevel 2>/dev/null) && root="$top"
         is_pointer "$root" && hit="$root/AGENTS.md"
      fi
      ;;
esac
[ -n "$hit" ] || exit 0

reason="The root AGENTS.md (or CLAUDE.md) here is a pointer to project-workbook/: a line on the project, the order to read project-workbook/start.md, and only the critical rules that apply to every task, each also stated in project-workbook/. A new rule or fact goes into project-workbook/ (how: project-workbook/_meta.md), not here. Allow this only if the pointer itself is what needs changing."

jq -n --arg r "$reason" '{
   hookSpecificOutput: {
      hookEventName: "PreToolUse",
      permissionDecision: "ask",
      permissionDecisionReason: $r
   }
}'
