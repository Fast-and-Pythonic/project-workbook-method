import { expect, test } from 'claude-code/testing'

import { carriesStart, topEntries } from './register'

const JOURNAL = [
  '# Journal',
  '',
  '## Index',
  '',
  '- **2026-03-03** — third',
  '- **2026-03-02** — second',
  '- **2026-03-01** — first',
  '',
  '## 2026-03-03 — third',
  '',
  'Done: three',
  '```',
  '## 2026-01-01 — inside a fence, not an entry',
  '```',
  'Status: Working',
  '',
  '---',
  '',
  '## 2026-03-02 — second',
  '',
  'Done: two',
  '',
  '## 2026-03-01 — first',
  '',
  'Done: one',
].join('\r\n')

const START = '# Start here\n\nRouting: for a build task read conventions.md first.\n'
const STATUS = '# Status\n\nAll green.\n'
const ROOT = 'C:/work/proj'
const files: Record<string, string> = {
  [`${ROOT}/project-workbook/start.md`]: START,
  [`${ROOT}/project-workbook/status.md`]: STATUS,
  [`${ROOT}/project-workbook/journal.md`]: JOURNAL,
}
/** The engine hands a `$.fs` hook the path as the platform spells it. */
const file = (path: string): string | undefined => files[path.replace(/\\/g, '/')]

test('journal entries are the dated headings, newest first, without the index', () => {
  const entries = topEntries(JOURNAL, 2)
  expect(entries.length).toBe(2)
  expect(entries[0]).toBe('## 2026-03-03 — third\n\nDone: three\n```\n## 2026-01-01 — inside a fence, not an entry\n```\nStatus: Working')
  expect(entries[1]).toBe('## 2026-03-02 — second\n\nDone: two')
  expect(topEntries(JOURNAL, 10).length).toBe(3)
  expect(topEntries(JOURNAL, 0)).toEqual([])
})

test('another hook copy of start.md is recognised by its opening, cut or not', () => {
  expect(carriesStart(`Below is project-workbook/start.md of ${ROOT}.\r\n\r\n${START.replace(/\n/g, '\r\n')}`, START)).toBe(true)
  expect(carriesStart('Plan files from earlier sessions: none.', START)).toBe(false)
  expect(carriesStart('anything', '')).toBe(false)
})

test('at session start the workbook replaces the command hook copy and keeps other context', async ($, on) => {
  on('fs.exists', ($, e) => ({ value: file(e.path) !== undefined }))
  on('fs.read', ($, e) => ({ value: file(e.path) ?? '' }))
  on('process.run', () => ({ value: { exitCode: 128, stdout: '', stderr: 'not a git repository', isStdoutTruncated: false, isStderrTruncated: false } }))
  on('classic.SessionStart', () => ({
    additionalContext: [`Below is project-workbook/start.md of ${ROOT}.\n\n${START}`, 'Plan files from earlier sessions: none.'],
  }))
  const result = await $.classic.SessionStart({ source: 'startup', cwd: ROOT })
  const context = result.additionalContext ?? []
  expect(context.length).toBe(2)
  const block = context[0] ?? ''
  expect(block.startsWith('[workbook-loader] ')).toBe(true)
  expect(block).toContain(`<file path="${ROOT}/project-workbook/start.md">\n${START.trimEnd()}\n</file>`)
  expect(block).toContain(`<file path="${ROOT}/project-workbook/status.md">\n${STATUS.trimEnd()}\n</file>`)
  expect(block).toContain('## 2026-03-01 — first\n\nDone: one\n</file>')
  expect(block).not.toContain('## Index')
  expect(context[1]).toBe('Plan files from earlier sessions: none.')
})

test('a cwd below the root finds the workbook through git', async ($, on) => {
  on('fs.exists', ($, e) => ({ value: file(e.path) !== undefined }))
  on('fs.read', ($, e) => ({ value: file(e.path) ?? '' }))
  on('process.run', () => ({ value: { exitCode: 0, stdout: `${ROOT}\n`, stderr: '', isStdoutTruncated: false, isStderrTruncated: false } }))
  on('classic.SessionStart', () => ({}))
  const result = await $.classic.SessionStart({ source: 'startup', cwd: 'C:\\work\\proj\\src' })
  expect((result.additionalContext ?? [])[0]).toContain(`<file path="${ROOT}/project-workbook/start.md">`)
})

test('without a workbook nothing is added and the other hooks pass through', async ($, on) => {
  on('fs.exists', () => ({ value: false }))
  on('process.run', () => ({ value: { exitCode: 128, stdout: '', stderr: 'not a git repository', isStdoutTruncated: false, isStderrTruncated: false } }))
  on('classic.SessionStart', () => ({ additionalContext: ['other hook'] }))
  const result = await $.classic.SessionStart({ source: 'startup', cwd: 'C:/elsewhere' })
  expect(result.additionalContext).toEqual(['other hook'])
})
