import { expect, test, type TestBody } from 'claude-code/testing'

import { errorSignature, isCodePath, isWorkbookPath, parseReply, triggerRows } from './register'

const ROOT = 'C:/work/proj'
const USAGE = { input_tokens: 10, output_tokens: 5, cache_read_input_tokens: 90_000, cache_creation_input_tokens: 0 }
const RULES = [
  '## 2. Update triggers',
  '',
  '| What happened | Action | |',
  '|---------------|--------|--|',
  '| Debugging > 30 min with a non-obvious cause | `gotchas.md`: a `G##` — **now** | |',
  '| A decision settled | `architecture.md`: an `A##` | |',
  '| Code style changed | `conventions.md` | **[E]** |',
  '',
  '## 3. Session protocol',
].join('\r\n')

test('paths: the workbook, code and what is neither', () => {
  expect(isWorkbookPath('C:\\work\\proj\\project-workbook\\gotchas.md')).toBe(true)
  expect(isWorkbookPath(`${ROOT}/src/project-workbook.ts`)).toBe(false)
  expect(isCodePath(`${ROOT}/src/main.rs`)).toBe(true)
  expect(isCodePath(`${ROOT}/README.md`)).toBe(false)
  expect(isCodePath(`${ROOT}/_backups/old.py`)).toBe(false)
})

test('the same error with other numbers is one signature; the exit-code header is skipped', () => {
  const a = errorSignature('Exit code 1\nerror[E0308]: mismatched types at src/main.rs:12:5')
  const b = errorSignature('Exit code 101\r\n\r\nerror[E0308]: mismatched types at src/main.rs:40:9')
  expect(a).toBe(b)
  expect(a.startsWith('error[E#]')).toBe(true)
})

test('the trigger rows are the untagged ones of section 2, without markup', () => {
  expect(triggerRows(RULES)).toEqual([
    'Debugging > 30 min with a non-obvious cause -> gotchas.md: a G## — now',
    'A decision settled -> architecture.md: an A##',
  ])
})

test('the reply: NONE, WRITE with items, and anything out of form', () => {
  expect(parseReply('NONE')).toBe(undefined)
  expect(parseReply('**WRITE**\n- A decision settled -> architecture.md: why X\nextra')).toEqual(['- A decision settled -> architecture.md: why X'])
  expect(parseReply('WRITE')).toBe(undefined)
  expect(parseReply('I think so')).toBe(undefined)
})

/** A session in a project with a workbook, whose fork answers `reply`; counts the forks. */
function project(on: Parameters<TestBody>[1], reply: string, workbook = true): { forks: string[] } {
  const seen = { forks: [] as string[] }
  on('fs.exists', ($, e) => ({ value: workbook && e.path.replace(/\\/g, '/') === `${ROOT}/project-workbook/start.md` }))
  on('process.run', () => ({ value: { exitCode: 128, stdout: '', stderr: 'not a git repository', isStdoutTruncated: false, isStderrTruncated: false } }))
  on('fs.read', () => ({ value: '' }))
  on('model.fork', ($, e) => {
    seen.forks.push(e.prompt)
    return { value: { isAnswered: true as const, text: reply, usage: USAGE } }
  })
  on('classic.Stop', () => ({}))
  return seen
}

test('three code edits make the stop ask the fork, and its WRITE blocks the stop', async ($, on) => {
  const seen = project(on, 'WRITE\n- A decision settled -> architecture.md: chose the ring buffer')
  on('tool.call', () => ({ result: { ok: true } as never }))
  for (const f of ['a.rs', 'b.rs', 'a.rs']) {
    await $.tool.call({ tool: 'Edit', file_path: `${ROOT}/src/${f}`, old_string: 'x', new_string: 'y' })
  }
  const result = await $.classic.Stop({ stop_hook_active: false, cwd: ROOT })
  expect(seen.forks.length).toBe(1)
  expect(seen.forks[0]).toContain('3 edits of code files')
  expect(result.block).toContain('- A decision settled -> architecture.md: chose the ring buffer')
  expect(result.block).toContain(`${ROOT}/project-workbook/`)
  // The signs were spent on that check: the next stop asks nothing.
  const again = await $.classic.Stop({ stop_hook_active: false, cwd: ROOT })
  expect(seen.forks.length).toBe(1)
  expect(again.block).toBe(undefined)
})

test('a workbook edit clears the signs; NONE lets the stop through', async ($, on) => {
  const seen = project(on, 'NONE')
  on('tool.call', () => ({ result: { ok: true } as never }))
  for (const f of ['a.rs', 'b.rs', 'c.rs']) {
    await $.tool.call({ tool: 'Write', file_path: `${ROOT}/src/${f}`, content: 'x' })
  }
  await $.tool.call({ tool: 'Edit', file_path: `${ROOT}/project-workbook/status.md`, old_string: 'x', new_string: 'y' })
  expect((await $.classic.Stop({ stop_hook_active: false, cwd: ROOT })).block).toBe(undefined)
  expect(seen.forks.length).toBe(0)
  for (const f of ['a.rs', 'b.rs', 'c.rs']) {
    await $.tool.call({ tool: 'Write', file_path: `${ROOT}/src/${f}`, content: 'x' })
  }
  expect((await $.classic.Stop({ stop_hook_active: false, cwd: ROOT })).block).toBe(undefined)
  expect(seen.forks.length).toBe(1)
})

test('a run of failures on one error is a sign; a re-prompted stop is let through', async ($, on) => {
  const seen = project(on, 'WRITE\n- Debugging > 30 min -> gotchas.md: the linker wants /FORCE')
  on('tool.call', ($, e) => ({ isError: true as const, result: undefined, text: `Exit code 1\nLINK : fatal error LNK${e.tool === 'Bash' ? 1104 : 1105}: cannot open file` }))
  for (let i = 0; i < 3; i++) await $.tool.call({ tool: 'Bash', command: 'cargo build' })
  expect((await $.classic.Stop({ stop_hook_active: true, cwd: ROOT })).block).toBe(undefined)
  expect(seen.forks.length).toBe(0)
  const result = await $.classic.Stop({ stop_hook_active: false, cwd: ROOT })
  expect(seen.forks[0]).toContain('3 failed shell runs ending in the same error')
  expect(result.block).toContain('gotchas.md')
})

test('outside a workbook nothing is asked', async ($, on) => {
  const seen = project(on, 'WRITE\n- x -> y: z', false)
  on('tool.call', () => ({ result: { ok: true } as never }))
  for (const f of ['a.rs', 'b.rs', 'c.rs']) {
    await $.tool.call({ tool: 'Write', file_path: `C:/elsewhere/${f}`, content: 'x' })
  }
  expect((await $.classic.Stop({ stop_hook_active: false, cwd: 'C:/elsewhere' })).block).toBe(undefined)
  expect(seen.forks.length).toBe(0)
})
