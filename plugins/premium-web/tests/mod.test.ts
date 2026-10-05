import { expect, mock, test } from 'claude-code/testing'

const CWD = '/proj'
const MANIFEST = JSON.stringify({
  brief: 'Landing page for Acme',
  round: 1,
  candidates: [
    { id: 'a', label: 'Alpha', direction: 'Editorial dark', dir: 'sites/a', screenshot: 'shots/a.png', scores: { wow: 4 }, notes: 'Strong hero' },
    { id: 'b', label: 'Beta', direction: 'Swiss data', url: 'https://preview.example.com/b' },
    { id: 'c', label: 'Gamma', direction: 'Tactile', dir: 'sites/c' },
  ],
})

const PANE = {
  plugin: 'premium-web',
  component: 'Pane',
  requestId: 'premium-web-candidates',
  viewport: { columns: 120, rows: 40 },
  props: { title: 'Premium candidates', isFocused: true, bodyColumns: 80, placement: 'dock', scroll: { offset: 0, bodyRows: 30 }, view: {} },
} as const

type Env = { submitted: any[]; writes: Map<string, string>; store: Map<string, unknown>; toasts: string[]; opened: any[]; ran: string[][]; spawned: any[] }

// Stubs for everything the mod asks Claude Code. Registered before the first call on $.
function stubs(on: any, manifestText: string | null = MANIFEST): Env {
  const env: Env = { submitted: [], writes: new Map(), store: new Map(), toasts: [], opened: [], ran: [], spawned: [] }
  mock.clock(on)
  on('session.cwd', () => ({ value: CWD }))
  on('fs.read', ($: any, e: any) => {
    if (manifestText === null || !e.path.endsWith('/.premium-web/candidates.json')) return { deny: 'ENOENT' }
    return { value: manifestText }
  })
  on('fs.write', ($: any, e: any) => {
    env.writes.set(e.path, e.text)
    return { value: undefined }
  })
  on('store.get', ($: any, e: any) => ({ value: env.store.get(e.key) }))
  on('store.set', ($: any, e: any) => {
    env.store.set(e.key, e.value)
    return { value: undefined }
  })
  on('ui.toast', ($: any, e: any) => {
    env.toasts.push(e.text)
    return { value: undefined }
  })
  on('ui.open', ($: any, e: any) => {
    env.opened.push(e)
    return { value: { isPlaced: true } }
  })
  on('ui.log', () => ({ value: undefined }))
  on('prompt.submit', ($: any, e: any) => {
    env.submitted.push(e)
    return { text: e.text }
  })
  on('process.run', ($: any, e: any) => {
    env.ran.push(e.argv)
    if (e.argv[0] === 'uname') return { value: { exitCode: 0, stdout: 'Darwin\n', stderr: '' } }
    if (e.argv[1] === '-c') return { value: { exitCode: 0, stdout: '54321\n', stderr: '' } }
    return { value: { exitCode: 0, stdout: '', stderr: '' } }
  })
  on('process.spawn', async function* ($: any, e: any) {
    env.spawned.push(e)
    try {
      // the kit reads a spawn stub to its end, so it must finish; the real child outlives the call
      yield { stream: 'stdout', text: 'Serving\n' }
    } finally {
      // nothing to clean up in the stub
    }
  })
  on('http.fetch', () => ({ value: { status: 200, ok: true, headers: {}, text: '' } }))
  return env
}

const lastText = (env: Env) => env.submitted[env.submitted.length - 1].text as string

test('settings tool returns the default candidate count of 3', async ($, on) => {
  stubs(on)
  on('tool.call', () => ({ result: 'unreachable' }))
  const r: any = await $.tool.call({ tool: 'mcp__premium-web__premium_web_get_settings' })
  expect(JSON.parse(r.result).candidateCount).toBe(3)
})

test('session.start registers both tools and /candidates', async ($, on) => {
  stubs(on)
  const seen: string[] = []
  on('tool.register', ($: any, e: any) => {
    seen.push('tool:' + e.name)
    return { value: { tool: 'mcp__premium-web__' + e.name } }
  })
  on('command.register', ($: any, e: any) => {
    seen.push('cmd:' + e.name)
    return { value: undefined }
  })
  on('session.start', () => ({ cwd: CWD }))
  await $.session.start({ surface: 'terminal', isInteractive: true, cwd: CWD })
  expect(seen).toEqual(['tool:premium_web_get_settings', 'tool:premium_web_present_candidates', 'cmd:candidates'])
})

test('present tool opens the pane and tells Claude to stop', async ($, on) => {
  const env = stubs(on)
  on('tool.call', () => ({ result: 'unreachable' }))
  const r: any = await $.tool.call({ tool: 'mcp__premium-web__premium_web_present_candidates' })
  expect(r.result).toContain('3 candidate(s) presented')
  expect(r.result).toContain('STOP')
  expect(env.opened[0].id).toBe('premium-web-candidates')
})

test('present tool reports a bad manifest instead of throwing', async ($, on) => {
  stubs(on, JSON.stringify({ candidates: [{ id: 'a', dir: '../../etc' }] }))
  on('tool.call', () => ({ result: 'unreachable' }))
  const r: any = await $.tool.call({ tool: 'mcp__premium-web__premium_web_present_candidates' })
  expect(r.result).toContain('ERROR')
  expect(r.result).toContain('inside the project folder')
})

test('/candidates without a manifest says so', async ($, on) => {
  stubs(on, null)
  const r: any = await $.command.run({ command: 'candidates', args: '' })
  expect(r.text).toContain('candidates.json')
})

for (const surface of ['terminal', 'desktop'] as const) {
  test('pane draws tabs, body and controls on ' + surface, async ($, on) => {
    stubs(on)
    await $.command.run({ command: 'candidates', args: '' })
    const ui = await $.ui.mount({ ...PANE, surface })
    for (const key of ['tab-a', 'tab-b', 'tab-c', 'open-a', 'pick-a', 'changes-a', 'feedback-all']) {
      expect(await ui.find({ key })).toBeDefined()
    }
    expect(await ui.find({ type: 'Text', text: 'Editorial dark' })).toBeDefined()
    // the screenshot is an Image in the terminal and a path line on the desktop
    expect(!!(await ui.find({ type: 'Image' }))).toBe(surface === 'terminal')
    expect(!!(await ui.find({ type: 'Text', text: /^Screenshot: \/proj\/shots\/a\.png$/ }))).toBe(surface === 'desktop')
    await ui.press({ key: 'tab-b' })
    expect(await ui.find({ type: 'Text', text: 'Swiss data' })).toBeDefined()
    expect(await ui.find({ type: 'Link' })).toBeDefined()
    await ui.unmount()
  })
}

test('Pick sends a structured message, persists decision.json and the store, and toasts', async ($, on) => {
  const env = stubs(on)
  await $.command.run({ command: 'candidates', args: '' })
  const ui = await $.ui.mount({ ...PANE, surface: 'terminal' })
  await ui.press({ key: 'tab-c' })
  await ui.press({ key: 'pick-c' })
  const sent = env.submitted[0]
  // the test kit's prompt.submit event carries only the text; asUser:true is checked in the live run
  expect(sent.text).toContain('I picked candidate C ("Gamma")')
  expect(sent.text).toContain('/proj/sites/c')
  const decision = JSON.parse(env.writes.get('/proj/.premium-web/decision.json') as string)
  expect(decision.round).toBe(1)
  expect(decision.picked).toBe('c')
  expect((env.store.get('state:/proj') as any).picked).toBe('c')
  expect(env.toasts.some((t) => t.includes('Picked candidate C'))).toBe(true)
  await ui.unmount()
})

test('Request changes reveals an input; submitting sends per-candidate feedback', async ($, on) => {
  const env = stubs(on)
  await $.command.run({ command: 'candidates', args: '' })
  const ui = await $.ui.mount({ ...PANE, surface: 'terminal' })
  expect(await ui.find({ key: 'fb-a' })).toBeUndefined()
  await ui.press({ key: 'changes-a' })
  await ui.input({ key: 'fb-a', text: 'Hero too busy' })
  expect(lastText(env)).toContain('Feedback on candidate A ("Alpha", round 1): Hero too busy')
  const decision = JSON.parse(env.writes.get('/proj/.premium-web/decision.json') as string)
  expect(decision.feedback[0]).toMatchObject({ candidate: 'a', text: 'Hero too busy' })
  expect(decision.picked).toBe(null)
  await ui.unmount()
})

test('general feedback is sent for all candidates', async ($, on) => {
  const env = stubs(on)
  await $.command.run({ command: 'candidates', args: '' })
  const ui = await $.ui.mount({ ...PANE, surface: 'desktop' })
  expect(await ui.find({ key: 'fb-all' })).toBeUndefined()
  await ui.press({ key: 'feedback-all' })
  await ui.input({ key: 'fb-all', text: 'All too dark' })
  expect(lastText(env)).toContain('Feedback on all candidates (round 1): All too dark')
  await ui.unmount()
})

test('choices are restored from the store when the pane is reopened', async ($, on) => {
  const env = stubs(on)
  env.store.set('state:/proj', { round: 1, picked: 'b', feedback: [], active: 1 })
  await $.command.run({ command: 'candidates', args: '' })
  const ui = await $.ui.mount({ ...PANE, surface: 'terminal' })
  expect(await ui.find({ type: 'Text', text: 'Swiss data' })).toBeDefined() // active tab restored
  expect(await ui.find({ type: 'Text', text: /picked/ })).toBeDefined()
  await ui.unmount()
})

test('a candidate with a url opens it directly without a server', async ($, on) => {
  const env = stubs(on)
  await $.command.run({ command: 'candidates', args: 'b' })
  const ui = await $.ui.mount({ ...PANE, surface: 'terminal' })
  await ui.press({ key: 'open-b' })
  expect(env.spawned.length).toBe(0)
  expect(env.ran).toContainEqual(['open', 'https://preview.example.com/b'])
  await ui.unmount()
})

test('a local candidate is served on 127.0.0.1 only and one server is reused', async ($, on) => {
  const env = stubs(on)
  await $.command.run({ command: 'candidates', args: '' })
  const ui = await $.ui.mount({ ...PANE, surface: 'terminal' })
  await ui.press({ key: 'open-a' })
  await ui.press({ key: 'open-a' })
  expect(env.spawned.length).toBe(1) // one server per candidate
  expect(env.spawned[0].argv).toEqual(['python3', '-m', 'http.server', '54321', '--bind', '127.0.0.1', '--directory', '/proj/sites/a'])
  expect(env.ran).toContainEqual(['open', 'http://127.0.0.1:54321/'])
  expect(env.spawned[0].argv.join(' ')).not.toContain('0.0.0.0')
  await ui.unmount()
})

test('app-mode candidate shows tasks with step counts and task end-state shots; marketing candidates unchanged', async ($, on) => {
  const app = JSON.stringify({
    brief: 'Run console',
    mode: 'app',
    candidates: [
      { id: 'a', label: 'Alpha', direction: 'Table-first', dir: 'sites/a', tasks: [{ task: 'Triage a failed run', steps: 4, result: 'cause visible', screenshot: 'shots/a-t1.png' }] },
      { id: 'b', label: 'Beta', direction: 'Marketing-style', dir: 'sites/b' },
    ],
  })
  for (const surface of ['terminal', 'desktop'] as const) {
    stubs(on, app)
    await $.command.run({ command: 'candidates', args: '' })
    const ui = await $.ui.mount({ ...PANE, surface })
    expect(await ui.find({ type: 'Markdown', text: /Triage a failed run.*4 steps/ })).toBeDefined()
    if (surface === 'terminal') expect(await ui.find({ key: 'task-shot-a-0' })).toBeDefined()
    else expect(await ui.find({ type: 'Text', text: /^Task shot: \/proj\/shots\/a-t1\.png$/ })).toBeDefined()
    await ui.press({ key: 'tab-b' })
    expect(await ui.find({ type: 'Text', text: 'Marketing-style' })).toBeDefined()
    expect(await ui.find({ type: 'Markdown', text: /Tasks/ })).toBeUndefined()
    await ui.unmount()
  }
})
