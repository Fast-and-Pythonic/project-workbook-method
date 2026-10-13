// workbook-loader: step 1 of the session protocol (RULES.md §3), done by the
// harness instead of left to the agent. At session start it finds the project
// workbook and hands the model start.md, status.md and the newest journal
// entries, whole, as one block of context.
//
// Why a mod and not only the command hook (tools/hooks/claude-code-session-start.sh):
// Claude Code turns a command hook's output over about 10 KB into a file and a
// 2 KB preview, so that hook can carry start.md alone, capped. Context a hooks
// module returns is not cut that way.
//
// Why `classic.SessionStart`: its result is the folded output of the settings
// SessionStart hooks, one `additionalContext` entry per hook, and a module sits
// above them. So the block rides the same channel the command hook uses, and the
// module can drop that hook's copy of start.md where both are installed, while
// every other SessionStart hook's context passes through untouched.

import type { EngineInterface, Register } from 'claude-code'

const WORKBOOK = 'project-workbook'
const DEFAULT_ENTRIES = 4
const GIT_TIMEOUT_MS = 5_000
/** How much of start.md's opening identifies another hook's copy of it. */
const HEAD_CHARS = 300
const MIN_HEAD_CHARS = 20

/** A journal entry heading, as FORMATS.md writes it: `## YYYY-MM-DD — ...`. */
const ENTRY_HEADING = /^## \d{4}-\d{2}-\d{2}\b/
const ANY_HEADING = /^#{1,2} /
const FENCE = /^\s*(```|~~~)/

export type Workbook = {
  root: string
  start: string
  status?: string
  entries: string[]
}

function slashes(path: string): string {
  return path.replace(/\\/g, '/').replace(/\/+$/, '')
}

function unixLines(text: string): string {
  return text.replace(/\r\n?/g, '\n')
}

/**
 * The newest `count` journal entries, each from its heading to the line before
 * the next heading; the index and the file's preamble are not entries. Headings
 * inside code fences are text, not boundaries.
 */
export function topEntries(journal: string, count: number): string[] {
  const entries: string[] = []
  let current: string[] | undefined
  let inFence = false
  const close = (): void => {
    if (current === undefined) return
    while (current.length > 0 && /^\s*(-{3,})?\s*$/.test(current[current.length - 1] ?? '')) current.pop()
    entries.push(current.join('\n'))
    current = undefined
  }
  for (const line of unixLines(journal).split('\n')) {
    if (FENCE.test(line)) inFence = !inFence
    if (!inFence && ANY_HEADING.test(line)) {
      close()
      if (entries.length >= count) break
      if (ENTRY_HEADING.test(line)) current = []
    }
    current?.push(line)
  }
  if (entries.length < count) close()
  return entries.slice(0, count)
}

function section(path: string, body: string, note?: string): string {
  const attr = note === undefined ? '' : ` note="${note}"`
  return `<file path="${path}"${attr}>\n${unixLines(body).replace(/\n+$/, '')}\n</file>`
}

/** The one block of context the module hands the model. */
export function contextBlock(wb: Workbook, count: number): string {
  const dir = `${wb.root}/${WORKBOOK}`
  const loaded = ['start.md']
  if (wb.status !== undefined) loaded.push('status.md')
  if (wb.entries.length > 0) loaded.push(`the top ${wb.entries.length} journal.md entries`)
  const list = loaded.length > 1 ? `${loaded.slice(0, -1).join(', ')} and ${loaded[loaded.length - 1]}` : 'start.md'
  const parts = [
    `[workbook-loader] Session protocol step 1 is already done by the workbook-loader mod: below are ${list} of the project at ${wb.root}, in full, as they stood at session start, so do not re-read them to start the session (re-read a file only to see a change made after this point); start.md's routing (what to read when) applies to every task, including one that looks like a small edit.`,
    section(`${dir}/start.md`, wb.start),
  ]
  if (wb.status !== undefined) parts.push(section(`${dir}/status.md`, wb.status))
  if (wb.entries.length > 0) {
    const note = `the newest ${wb.entries.length} entries only; the index and older entries are not included`
    parts.push(section(`${dir}/journal.md`, wb.entries.join('\n\n'), note))
  }
  return parts.join('\n\n')
}

/**
 * Whether a context entry from another SessionStart hook already carries this
 * start.md (the command hook's copy, possibly cut short at a line): it holds
 * the file's opening verbatim.
 */
export function carriesStart(entry: string, start: string): boolean {
  const head = unixLines(start).trim().slice(0, HEAD_CHARS)
  return head.length >= MIN_HEAD_CHARS && unixLines(entry).includes(head)
}

async function readIfPresent($: EngineInterface, path: string): Promise<string | undefined> {
  if (!(await $.fs.exists(path))) return undefined
  return await $.fs.read(path)
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

export async function loadWorkbook($: EngineInterface, cwd: string, count: number): Promise<Workbook | undefined> {
  const root = await findRoot($, cwd)
  if (root === undefined) return undefined
  const dir = `${root}/${WORKBOOK}`
  const start = await $.fs.read(`${dir}/start.md`)
  const status = await readIfPresent($, `${dir}/status.md`)
  const journal = count > 0 ? await readIfPresent($, `${dir}/journal.md`) : undefined
  const entries = journal === undefined ? [] : topEntries(journal, count)
  return status === undefined ? { root, start, entries } : { root, start, status, entries }
}

export const register: Register = (on, options) => {
  const raw = Number(options.journalEntries ?? DEFAULT_ENTRIES)
  const count = Number.isFinite(raw) && raw >= 0 ? Math.floor(raw) : DEFAULT_ENTRIES

  on('classic.SessionStart', async ($, e, next) => {
    const result = await next(e)
    const wb = await loadWorkbook($, e.cwd, count)
    if (wb === undefined) return result
    const block = contextBlock(wb, count)
    const others = result.additionalContext ?? []
    const kept = others.filter((entry) => !carriesStart(entry, wb.start))
    const bytes = new TextEncoder().encode(block).length
    $.ui.log(
      `workbook-loader: ${bytes} bytes from ${wb.root} (${wb.entries.length} journal entries); dropped ${others.length - kept.length} other hook copies of start.md`,
      { to: 'debug' },
    )
    return { ...result, additionalContext: [block, ...kept] }
  })
}
