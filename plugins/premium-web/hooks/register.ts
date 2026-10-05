// premium-web mod: browse the built candidates in a pane, open each one, pick the winner or send feedback.
// Mods are NOT sandboxed: this file runs with the user's permissions. What it does, in full:
//   reads   <cwd>/.premium-web/candidates.json
//   writes  <cwd>/.premium-web/decision.json, and its own $.store entry
//   runs    `python3 -m http.server --bind 127.0.0.1` on a free local port for a candidate that has no preview URL,
//           `uname -s`, and the OS "open a URL" command (open / xdg-open / cmd start)
//   sends   the user's pick/feedback back to Claude with $.prompt.submit
// No other network egress, no environment reads, no secrets.
import {
  type Candidate,
  type Manifest,
  PORT_SCRIPT,
  clampCount,
  feedbackMessage,
  openArgv,
  pickMessage,
  scoresMarkdown,
  tasksMarkdown,
  validateManifest,
} from './lib.ts'

const PANE_ID = 'premium-web-candidates'
const TOOL_PRESENT = 'mcp__premium-web__premium_web_present_candidates'
const TOOL_SETTINGS = 'mcp__premium-web__premium_web_get_settings'

type Feedback = { candidate: string | null; text: string; at: string }
type Saved = { round: number; picked: string | null; feedback: Feedback[]; active: number }
type Server = { gen: { next: () => Promise<{ done?: boolean }>; return: (v?: unknown) => Promise<unknown> }; port: number }

// Module state. Lost on reload by design; the choices are restored from $.store when the pane is next opened.
let candidateCount = 3
let cwdNow = ''
let manifest: Manifest | null = null
let loadError = ''
let active = 0
let revealId: string | null = null
let picked: string | null = null
let feedback: Feedback[] = []
let status = ''
const servers = new Map<string, Server>()

function errText(err: unknown): string {
  return err instanceof Error ? err.message : String(err)
}

async function stopAll(): Promise<void> {
  const all = [...servers.values()]
  servers.clear()
  for (const s of all) {
    try {
      await s.gen.return(undefined)
    } catch {
      // already gone
    }
  }
}

async function drain(gen: Server['gen']): Promise<void> {
  try {
    for (;;) {
      const step = await gen.next()
      if (step.done === true) return
    }
  } catch {
    // the server ended; nothing to report
  }
}

// Reads and validates <cwd>/.premium-web/candidates.json, restores saved choices. Returns an error text or ''.
async function loadManifest($: any): Promise<string> {
  cwdNow = await $.session.cwd()
  let text = ''
  try {
    text = await $.fs.read(cwdNow + '/.premium-web/candidates.json')
  } catch {
    loadError = 'No .premium-web/candidates.json in ' + cwdNow + ' yet. Build candidates with the premium-web skill first.'
    manifest = null
    return loadError
  }
  const checked = validateManifest(text, cwdNow)
  if (!checked.ok) {
    loadError = checked.error
    manifest = null
    return loadError
  }
  await stopAll()
  loadError = ''
  manifest = checked.manifest
  active = 0
  revealId = null
  picked = null
  feedback = []
  status = ''
  const saved = (await $.store.get('state:' + cwdNow)) as Saved | undefined
  if (saved !== undefined && saved !== null && saved.round === manifest.round) {
    const ids = manifest.candidates.map((c) => c.id)
    picked = typeof saved.picked === 'string' && ids.includes(saved.picked) ? saved.picked : null
    feedback = Array.isArray(saved.feedback) ? saved.feedback.slice(-50) : []
    active = Number.isInteger(saved.active) && saved.active >= 0 && saved.active < ids.length ? saved.active : 0
  }
  return ''
}

async function persist($: any): Promise<void> {
  if (manifest === null) return
  const at = new Date(await $.clock.now()).toISOString()
  const decision = { round: manifest.round, picked, feedback, at }
  try {
    await $.fs.write(cwdNow + '/.premium-web/decision.json', JSON.stringify(decision, null, 2) + '\n')
  } catch (err) {
    status = 'Could not write decision.json: ' + errText(err)
  }
  const saved: Saved = { round: manifest.round, picked, feedback, active }
  await $.store.set('state:' + cwdNow, saved)
}

async function send($: any, text: string): Promise<void> {
  await persist($)
  // Not awaited: submit resolves when the turn starts, which can be after the current one ends.
  $.prompt.submit({ text, asUser: true }).catch(() => {})
}

async function ensureServer($: any, c: Candidate): Promise<string> {
  if (c.url !== undefined) return c.url
  if (c.dir === undefined) throw new Error('candidate has no dir or url')
  const have = servers.get(c.id)
  if (have !== undefined) return 'http://127.0.0.1:' + have.port + '/'
  const found = await $.process.run(['python3', '-c', PORT_SCRIPT])
  const port = Number(String(found.stdout).trim())
  if (!Number.isInteger(port) || port < 1024 || port > 65535) throw new Error('could not find a free local port')
  const gen = (await $.process.spawn({
    argv: ['python3', '-m', 'http.server', String(port), '--bind', '127.0.0.1', '--directory', c.dir],
  })) as Server['gen']
  servers.set(c.id, { gen, port })
  drain(gen)
  const url = 'http://127.0.0.1:' + port + '/'
  for (let i = 0; i < 15; i++) {
    try {
      const res = await $.http.fetch(url)
      if (res.ok) return url
    } catch {
      // not listening yet
    }
    await $.clock.sleep(300)
  }
  servers.delete(c.id)
  try {
    await gen.return(undefined)
  } catch {
    // ignore
  }
  throw new Error('the local preview server did not start (is python3 installed?)')
}

async function openCandidate($: any, c: Candidate): Promise<void> {
  try {
    const url = await ensureServer($, c)
    let uname = ''
    try {
      uname = String((await $.process.run(['uname', '-s'])).stdout)
    } catch {
      // no uname: Windows
    }
    await $.process.run(openArgv(uname, url))
    status = 'Opened ' + url
  } catch (err) {
    status = 'Could not open the preview: ' + errText(err)
  }
  $.ui.invalidate('ui.render')
}

async function pick($: any, c: Candidate): Promise<void> {
  if (manifest === null) return
  picked = c.id
  status = 'Picked ' + c.id.toUpperCase() + '. Sent to Claude.'
  await $.ui.toast('Picked candidate ' + c.id.toUpperCase() + ' (' + c.label + ')')
  $.ui.invalidate('ui.render')
  await send($, pickMessage(manifest, c))
}

async function sendFeedback($: any, id: string | null, text: string): Promise<void> {
  if (manifest === null || text.trim() === '') return
  const c = manifest.candidates.find((x) => x.id === id)
  const at = new Date(await $.clock.now()).toISOString()
  feedback = [...feedback, { candidate: id, text: text.trim().slice(0, 2000), at }].slice(-50)
  revealId = null
  status = 'Feedback sent' + (id === null ? ' (all candidates).' : ' (candidate ' + id.toUpperCase() + ').')
  await $.ui.toast(status)
  $.ui.invalidate('ui.render')
  await send($, feedbackMessage(manifest, id, text.trim().slice(0, 2000), c))
}

async function openPane($: any): Promise<{ isPlaced: boolean }> {
  const r = await $.ui.open({ id: PANE_ID, title: 'Premium candidates', focus: true, closeOnEscape: true })
  return { isPlaced: r?.isPlaced !== false }
}

export function register(on: any, options: any): void {
  candidateCount = clampCount(options?.candidateCount)

  on('session.start', async ($: any, e: any, next: any) => {
    try {
      await $.tool.register({
        name: 'premium_web_get_settings',
        description: 'Returns the user\'s premium-web settings: { candidateCount }, the default number of candidate sites to build.',
        inputSchema: { type: 'object', properties: {} },
      })
      await $.tool.register({
        name: 'premium_web_present_candidates',
        description:
          'Show the built premium-web candidates to the user in the "Premium candidates" pane (reads .premium-web/candidates.json in the project folder). Call it once all candidates are built, then STOP and wait: the user\'s pick or feedback arrives as their next message.',
        inputSchema: { type: 'object', properties: {} },
      })
      await $.command.register({
        name: 'candidates',
        description: 'Browse the premium-web candidates, open one, pick the best or send feedback',
        argumentHint: '[number|id]',
      })
    } catch (err) {
      try {
        $.ui.log('premium-web: setup failed: ' + errText(err))
      } catch {
        // never break the session
      }
    }
    return next(e)
  })

  on('tool.call', { tool: TOOL_SETTINGS }, async () => {
    return { result: JSON.stringify({ candidateCount }) }
  })

  on('tool.call', { tool: TOOL_PRESENT }, async ($: any) => {
    try {
      const err = await loadManifest($)
      if (err !== '' || manifest === null) {
        return { result: 'ERROR: ' + err + ' Fix the file, or fall back to presenting links and screenshots in chat.' }
      }
      const n = manifest.candidates.length
      let placed = false
      try {
        placed = (await openPane($)).isPlaced
      } catch {
        placed = false
      }
      if (!placed) await $.ui.toast('Premium candidates are ready: run /candidates')
      return {
        result:
          n + ' candidate(s) presented' +
          (placed ? ' in the Premium candidates pane.' : '; the pane did not open (narrow terminal), so tell the user to run /candidates.') +
          ' STOP now. Do not build or edit anything until the user\'s pick or feedback arrives as their next message.',
      }
    } catch (err) {
      return { result: 'ERROR: ' + errText(err) + ' Fall back to presenting links and screenshots in chat.' }
    }
  })

  on('command.run', { command: 'candidates' }, async ($: any, e: any) => {
    try {
      const err = await loadManifest($)
      if (err !== '' || manifest === null) return { text: err }
      const arg = String(e.args ?? '').trim()
      if (arg !== '') {
        const byId = manifest.candidates.findIndex((c) => c.id === arg)
        const byNum = Number(arg) - 1
        if (byId >= 0) active = byId
        else if (Number.isInteger(byNum) && byNum >= 0 && byNum < manifest.candidates.length) active = byNum
      }
      await openPane($)
      return {}
    } catch (err) {
      return { text: 'premium-web: ' + errText(err) }
    }
  })

  on('ui.render', { component: 'Pane' }, async ($: any, e: any, next: any) => {
    if (e.requestId !== PANE_ID) return next(e)
    try {
      const { Box, Text, Button, Input, Link, Markdown, Image } = $.ui.resolve(e)
      const redraw = () => $.ui.invalidate('ui.render')
      if (manifest === null) {
        return Text({ children: [loadError !== '' ? loadError : 'Run /candidates to load .premium-web/candidates.json'] })
      }
      const m = manifest
      const c = m.candidates[active] ?? m.candidates[0]
      const terminal = e.surface === 'terminal'

      const tabs = Box({
        flexDirection: 'row',
        columnGap: 2,
        children: m.candidates.map((x, i) =>
          Button({
            key: 'tab-' + x.id,
            label: (i === active ? '● ' : '') + x.label + (picked === x.id ? ' ✓' : ''),
            hotkey: String(i + 1),
            plain: true,
            dimColor: i !== active,
            onPress: async () => {
              active = i
              revealId = null
              redraw()
              await persist($)
            },
          }),
        ),
      })

      const body: any[] = [
        Text({ bold: true, children: [c.label + (picked === c.id ? '  ✓ picked' : '')] }),
        Text({ children: [c.direction] }),
      ]
      if (c.screenshot !== undefined) {
        body.push(
          terminal
            ? Image({
                key: 'shot-' + c.id,
                source: { file: c.screenshot, format: 'png' },
                columns: Math.max(20, Math.min(72, (e.props?.bodyColumns ?? 80) - 2)),
                rows: 16,
                alt: 'Screenshot of candidate ' + c.id,
              })
            : Text({ dimColor: true, children: ['Screenshot: ' + c.screenshot] }),
        )
      }
      const tmd = tasksMarkdown(c)
      if (tmd !== '') body.push(Markdown({ text: '**Tasks (steps measured on the prototype)**\n' + tmd }))
      for (const [j, t] of (c.tasks ?? []).entries()) {
        if (t.screenshot === undefined) continue
        body.push(
          terminal
            ? Image({
                key: 'task-shot-' + c.id + '-' + j,
                source: { file: t.screenshot, format: 'png' },
                columns: Math.max(20, Math.min(72, (e.props?.bodyColumns ?? 80) - 2)),
                rows: 12,
                alt: 'End state of task: ' + t.task,
              })
            : Text({ dimColor: true, children: ['Task shot: ' + t.screenshot] }),
        )
      }
      const md = scoresMarkdown(c)
      if (md !== '') body.push(Markdown({ text: md }))
      body.push(
        c.url !== undefined
          ? Link({ href: c.url, label: 'Preview' })
          : Text({ dimColor: true, children: ['Folder: ' + c.dir + ' (served on 127.0.0.1 when opened)'] }),
      )
      // Two rows so the buttons fit an 80-column pane.
      body.push(
        Box({
          flexDirection: 'column',
          children: [
            Box({
              flexDirection: 'row',
              columnGap: 2,
              children: [
                Button({ key: 'open-' + c.id, label: 'Open in browser', hotkey: 'o', onPress: () => openCandidate($, c) }),
                Button({ key: 'pick-' + c.id, label: 'Pick this one', hotkey: 'p', onPress: () => pick($, c) }),
              ],
            }),
            Box({
              flexDirection: 'row',
              columnGap: 2,
              children: [
                Button({
                  key: 'changes-' + c.id,
                  label: 'Request changes',
                  hotkey: 'c',
                  onPress: () => {
                    revealId = revealId === c.id ? null : c.id
                    redraw()
                  },
                }),
                Button({
                  key: 'feedback-all',
                  label: 'Feedback on all',
                  hotkey: 'f',
                  onPress: () => {
                    revealId = revealId === '*' ? null : '*'
                    redraw()
                  },
                }),
              ],
            }),
          ],
        }),
      )
      if (revealId === c.id) {
        body.push(
          Input({
            key: 'fb-' + c.id,
            label: 'Changes to ' + c.id.toUpperCase(),
            placeholder: 'What should change? Enter sends it to Claude',
            value: '',
            submitLabel: 'send',
            autoFocus: true,
            onSubmit: (value: string) => sendFeedback($, c.id, value),
          }),
        )
      }
      // Fields are only drawn when asked for: while a field has focus, the o / p / c / f hotkeys go to the field.
      if (revealId === '*') {
        body.push(
          Input({
            key: 'fb-all',
            label: 'Feedback on all',
            placeholder: 'Applies to every candidate. Enter sends it',
            value: '',
            submitLabel: 'send',
            autoFocus: true,
            onSubmit: (value: string) => sendFeedback($, null, value),
          }),
        )
      }
      if (status !== '') body.push(Text({ dimColor: true, children: [status] }))
      return Box({
        flexDirection: 'column',
        rowGap: 1,
        children: [
          Text({ dimColor: true, children: ['Round ' + m.round + (m.mode === 'app' ? ' · app' : '') + (m.brief !== '' ? ' · ' + m.brief.slice(0, 120) : '')] }),
          tabs,
          ...body,
        ],
      })
    } catch (err) {
      try {
        $.ui.log('premium-web: draw failed: ' + errText(err))
      } catch {
        // never break the session
      }
      return next(e)
    }
  })

  on('ui.close', async ($: any, e: any, next: any) => {
    if (e.id === PANE_ID) await stopAll()
    return next(e)
  })

  on('session.end', async ($: any, e: any, next: any) => {
    await stopAll()
    return next(e)
  })
}
