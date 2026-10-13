// workbook-triggers: the Claude Code layer of the update triggers (RULES.md §2).
//
// The trigger table has no checking mechanism: nothing can tell that a debugging
// session ran past thirty minutes or that a decision was settled in a discussion,
// and on the document sets the standard is kept on the table sat unapplied in
// half of them. A session can tell cheap signs underneath: code edited while the
// workbook was not, the same error failing again and again, a long stretch of
// work. This mod counts those signs from the tool calls and turn lengths it sees.
// When one crosses its threshold at the end of a turn, it asks a fork of the
// session (the main thread's own transcript, served from the prompt cache)
// whether a trigger fired. On a yes it blocks the stop with the fork's list, so
// the agent writes the entries while the work is still in its context. The mod
// never writes the workbook itself.
//
// Before compaction it does not ask (the summarizer is already running a long
// request); while signs are pending it tells the summarizer to keep what a
// trigger would record, so the check at the end of the turn still has it.
//
// A failing hook falls through to what lies beneath: this mod reminds, it never
// stands between the session and a tool call, a compaction or a stop.
//
// The counts live in the module: a reload of the mod starts them over.

import type { EngineInterface, Register } from 'claude-code'

const WORKBOOK = 'project-workbook'
const GIT_TIMEOUT_MS = 5_000
const MAX_HINT_LINES = 5
const EDIT_TOOLS = new Set(['Edit', 'Write', 'MultiEdit', 'NotebookEdit'])
const SHELL_TOOLS = new Set(['Bash', 'PowerShell'])

export type Thresholds = { minCodeEdits: number; failureRun: number; workMinutes: number }

export type Signs = {
  /** code file -> edits since the last workbook edit */
  code: Map<string, number>
  /** normalised error line -> failed shell runs since the last workbook edit */
  failures: Map<string, number>
  /** model turn time since the last workbook edit */
  workMs: number
}

export function freshSigns(): Signs {
  return { code: new Map(), failures: new Map(), workMs: 0 }
}

function slashes(path: string): string {
  return path.replace(/\\/g, '/').replace(/\/+$/, '')
}

export function isWorkbookPath(path: string): boolean {
  return slashes(path).split('/').slice(0, -1).includes(WORKBOOK)
}

export function isCodePath(path: string): boolean {
  const p = slashes(path)
  return !p.toLowerCase().endsWith('.md') && !p.split('/').slice(0, -1).includes('_backups')
}

/**
 * The line that names a failure: the first non-empty one that is not the
 * shell's "Exit code N" header, numbers folded, so the same error with another
 * line number, port or duration counts as the same.
 */
export function errorSignature(text: string): string {
  for (const raw of text.replace(/\r\n?/g, '\n').split('\n')) {
    const line = raw.trim()
    if (line === '' || /^exit code -?\d+$/i.test(line)) continue
    return line.replace(/\d+/g, '#').slice(0, 160)
  }
  return '(no output)'
}

/** One line per sign past its threshold; none when no check is due. */
export function dueSigns(s: Signs, t: Thresholds): string[] {
  const out: string[] = []
  const edits = [...s.code.values()].reduce((a, b) => a + b, 0)
  if (t.minCodeEdits > 0 && edits >= t.minCodeEdits) {
    const files = [...s.code.keys()]
    const named = files.slice(0, 6).join(', ') + (files.length > 6 ? ` and ${files.length - 6} more` : '')
    out.push(`${edits} edits of code files with no workbook edit (${named})`)
  }
  if (t.failureRun > 0) {
    for (const [sig, n] of s.failures) {
      if (n >= t.failureRun) out.push(`${n} failed shell runs ending in the same error: ${sig}`)
    }
  }
  const minutes = Math.floor(s.workMs / 60_000)
  if (t.workMinutes > 0 && minutes >= t.workMinutes) out.push(`${minutes} minutes of work with no workbook edit`)
  return out
}

/** The untagged rows of RULES.md §2 as "what happened -> action". */
export function triggerRows(rules: string): string[] {
  const m = /^## 2\. [^\n]*\n([\s\S]*?)^## /m.exec(rules.replace(/\r\n?/g, '\n'))
  if (m === null) return []
  const rows: string[] = []
  for (const line of (m[1] ?? '').split('\n')) {
    if (!line.trim().startsWith('|')) continue
    const cells = line.trim().replace(/^\||\|$/g, '').split('|').map((c) => c.trim())
    const [what, action, tag] = cells
    if (what === undefined || action === undefined || /^[-: ]*$/.test(what) || what === 'What happened') continue
    if (tag !== undefined && tag !== '') continue
    rows.push(`${what} -> ${action}`.replace(/\*\*|`/g, ''))
  }
  return rows
}

export function question(signs: string[], root: string, rows: string[]): string {
  const table = rows.length > 0 ? rows.map((r) => `- ${r}`).join('\n') : '- (see RULES.md §2 of the Project Workbook standard)'
  return [
    '[workbook-triggers] This message is an automatic check by the workbook-triggers mod, not a request from the user. Answer the check only; do not continue the task or address the user.',
    '',
    `Since the last edit of the project workbook (${root}/${WORKBOOK}/) the session shows:`,
    ...signs.map((s) => `- ${s}`),
    '',
    "The workbook's update triggers (RULES.md §2; the project's _meta.md may add its own):",
    table,
    '',
    'Going only by what this transcript shows: did the work since the last workbook edit meet one of these triggers, with the entry not yet written? Routine edits with nothing non-obvious learned, decided or left fragile do not count.',
    '',
    'Reply in exactly one of two forms. Either the single word',
    'NONE',
    'or the word WRITE followed by at most three lines, each',
    '- <trigger> -> <file>: <what to record, one line>',
  ].join('\n')
}

/** The fork's list of entries to write, or undefined for NONE or a reply out of form. */
export function parseReply(text: string): string[] | undefined {
  const lines = text.replace(/\r\n?/g, '\n').split('\n').map((l) => l.trim()).filter((l) => l !== '')
  const head = (lines[0] ?? '').replace(/[*`]/g, '')
  if (!/^WRITE\b/.test(head)) return undefined
  const items = lines.slice(1).filter((l) => l.startsWith('-')).slice(0, MAX_HINT_LINES)
  return items.length > 0 ? items : undefined
}

export function hint(items: string[], root: string): string {
  return [
    '[workbook-triggers] Before you stop: a check over this session found update triggers (RULES.md §2) whose entries are not in the workbook yet:',
    ...items,
    '',
    `Write them now in ${root}/${WORKBOOK}/, checking the register's index for an existing entry to extend first, then tell the user in one line what was recorded. An item that does not hold on a second look: skip it and say why in one line.`,
  ].join('\n')
}

/** The session's cwd if it holds the workbook, else its git toplevel if that does. */
export async function findRoot($: EngineInterface, cwd: string): Promise<string | undefined> {
  const here = slashes(cwd)
  if (await $.fs.exists(`${here}/${WORKBOOK}/start.md`)) return here
  let top: string
  try {
    const git = await $.process.run(['git', 'rev-parse', '--show-toplevel'], { cwd, timeoutMs: GIT_TIMEOUT_MS })
    if (git.exitCode !== 0) return undefined
    top = slashes(git.stdout.trim())
  } catch {
    return undefined
  }
  if (top === '' || top === here) return undefined
  return (await $.fs.exists(`${top}/${WORKBOOK}/start.md`)) ? top : undefined
}

async function readRules($: EngineInterface): Promise<string[]> {
  const path = `${slashes($.plugin.root)}/../../../RULES.md`
  try {
    return (await $.fs.exists(path)) ? triggerRows(await $.fs.read(path)) : []
  } catch {
    return []
  }
}

function threshold(value: unknown, fallback: number): number {
  const n = Number(value ?? fallback)
  return Number.isFinite(n) && n >= 0 ? n : fallback
}

export const register: Register = (on, options) => {
  const t: Thresholds = {
    minCodeEdits: threshold(options.minCodeEdits, 3),
    failureRun: threshold(options.failureRun, 3),
    workMinutes: threshold(options.workMinutes, 30),
  }
  let signs = freshSigns()

  on('tool.call', async ($, e, next) => {
    const ran = await next(e)
    if (ran.deny !== undefined) return ran
    const input = e as unknown as { file_path?: unknown; notebook_path?: unknown }
    if (EDIT_TOOLS.has(e.tool) && ran.isError !== true) {
      const path = typeof input.file_path === 'string' ? input.file_path : input.notebook_path
      if (typeof path === 'string') {
        if (isWorkbookPath(path)) signs = freshSigns()
        else if (isCodePath(path)) signs.code.set(slashes(path), (signs.code.get(slashes(path)) ?? 0) + 1)
      }
    } else if (SHELL_TOOLS.has(e.tool) && ran.isError === true) {
      const sig = errorSignature(ran.text ?? '')
      signs.failures.set(sig, (signs.failures.get(sig) ?? 0) + 1)
    }
    return ran
  }).catch(($, e, next) => next(e))

  on('turn.complete', async ($, e, next) => {
    if (e.agentId === undefined) signs.workMs += e.durationMs
    return next(e)
  })

  on('session.compact', async ($, e, next) => {
    const due = dueSigns(signs, t)
    if (e.agentId !== undefined || due.length === 0) return next(e)
    const keep = `Pending for the project workbook (workbook-triggers): ${due.join('; ')}. Keep in the summary, with the details needed to write them, any non-obvious cause found, decision settled, fragile point identified or feature deferred in the work being summarized: they may still have to be recorded under RULES.md §2.`
    return next({ ...e, instructions: e.instructions === undefined ? keep : `${e.instructions}\n\n${keep}` })
  }).catch(($, e, next) => next(e))

  on('classic.Stop', async ($, e, next) => {
    const result = await next(e)
    if (result.block !== undefined || result.preventContinuation === true) return result
    // A stop already re-prompted once (by this mod or another hook) is let through.
    if (e.stop_hook_active || e.agent_id !== undefined) return result
    const due = dueSigns(signs, t)
    if (due.length === 0) return result
    const root = await findRoot($, e.cwd)
    if (root === undefined) {
      signs = freshSigns()
      return result
    }
    const reply = await $.model.fork({ prompt: question(due, root, await readRules($)) })
    if (!reply.isAnswered) {
      $.ui.log(`workbook-triggers: no check (${reply.reason}); signs kept for the next turn`, { to: 'debug' })
      return result
    }
    signs = freshSigns()
    const items = parseReply(reply.text)
    $.ui.log(`workbook-triggers: ${due.length} signs; fork says ${items === undefined ? 'NONE' : `WRITE ${items.length}`}`, { to: 'debug' })
    return items === undefined ? result : { ...result, block: hint(items, root) }
  }).catch(($, e, next) => next(e))
}
