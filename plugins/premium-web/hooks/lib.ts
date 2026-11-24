// Pure helpers for the premium-web mod. No `$` here: everything that touches Claude Code lives in register.ts.

export const MAX_FILE_BYTES = 256 * 1024
export const MAX_CANDIDATES = 9 // hotkeys 1..9
export const DEFAULT_COUNT = 3
export const MAX_COUNT = 6
export const ID_RE = /^[a-z0-9-]{1,32}$/

export type Candidate = {
  id: string
  label: string
  direction: string
  dir?: string // absolute, inside cwd
  url?: string // http(s) only
  screenshot?: string // absolute, inside cwd, .png
  scores: Record<string, string | number>
  notes: string
}
export type Manifest = { brief: string; round: number; candidates: Candidate[] }
export type Checked = { ok: true; manifest: Manifest } | { ok: false; error: string }

// candidateCount from userConfig: integer 1..6, default 3.
export function clampCount(v: unknown): number {
  const n = typeof v === 'number' ? v : Number(v)
  if (!Number.isFinite(n)) return DEFAULT_COUNT
  return Math.min(MAX_COUNT, Math.max(1, Math.round(n)))
}

// Lexical resolve of `p` against `cwd`; null when it escapes cwd or is malformed.
// ponytail: lexical only (no symlink resolution); the mod never reads these paths itself, it only
// hands them to the browser/static server, so a symlink inside cwd is the owner's own choice.
export function resolveInside(cwd: string, p: unknown): string | null {
  if (typeof p !== 'string' || p === '' || p.length > 1024 || p.includes('\0') || p.includes('\\')) return null
  const base = norm(cwd)
  if (base === null || !base.startsWith('/')) return null
  const abs = norm(p.startsWith('/') ? p : base + '/' + p)
  if (abs === null) return null
  return abs === base || abs.startsWith(base === '/' ? '/' : base + '/') ? abs : null
}

function norm(p: string): string | null {
  const out: string[] = []
  for (const seg of p.split('/')) {
    if (seg === '' || seg === '.') continue
    if (seg === '..') {
      if (out.length === 0) return null
      out.pop()
    } else out.push(seg)
  }
  return '/' + out.join('/')
}

function str(v: unknown, max: number, field: string, required = false): string {
  if (v === undefined || v === null || v === '') {
    if (required) throw new Error(field + ' is required')
    return ''
  }
  if (typeof v !== 'string') throw new Error(field + ' must be a string')
  if (v.length > max) throw new Error(field + ' is over ' + max + ' characters')
  return v
}

export function validateManifest(text: string, cwd: string): Checked {
  try {
    if (text.length > MAX_FILE_BYTES) throw new Error('candidates.json is over ' + MAX_FILE_BYTES + ' bytes')
    const raw = JSON.parse(text) as Record<string, unknown>
    if (typeof raw !== 'object' || raw === null || Array.isArray(raw)) throw new Error('top level must be an object')
    const round = raw.round === undefined ? 1 : raw.round
    if (typeof round !== 'number' || !Number.isInteger(round) || round < 1 || round > 99) throw new Error('round must be an integer 1-99')
    const list = raw.candidates
    if (!Array.isArray(list) || list.length < 1 || list.length > MAX_CANDIDATES) {
      throw new Error('candidates must be a list of 1-' + MAX_CANDIDATES)
    }
    const seen = new Set<string>()
    const candidates = list.map((c: Record<string, unknown>, i: number): Candidate => {
      const at = 'candidates[' + i + '].'
      if (typeof c !== 'object' || c === null) throw new Error(at + ' must be an object')
      const id = c.id
      if (typeof id !== 'string' || !ID_RE.test(id)) throw new Error(at + 'id must match [a-z0-9-]{1,32}')
      if (seen.has(id)) throw new Error(at + 'id "' + id + '" is duplicated')
      seen.add(id)
      const out: Candidate = {
        id,
        label: str(c.label, 80, at + 'label') || id,
        direction: str(c.direction, 300, at + 'direction'),
        scores: {},
        notes: str(c.notes, 2000, at + 'notes'),
      }
      if (c.dir !== undefined && c.dir !== '') {
        const d = resolveInside(cwd, c.dir)
        if (d === null) throw new Error(at + 'dir must stay inside the project folder')
        out.dir = d
      }
      if (c.url !== undefined && c.url !== '') {
        const u = str(c.url, 2048, at + 'url')
        if (!/^https?:\/\/[^\s]+$/i.test(u)) throw new Error(at + 'url must be http(s)')
        out.url = u
      }
      if (out.dir === undefined && out.url === undefined) throw new Error(at + 'needs a dir or a url')
      if (c.screenshot !== undefined && c.screenshot !== '') {
        const s = resolveInside(cwd, c.screenshot)
        if (s === null || !/\.png$/i.test(s)) throw new Error(at + 'screenshot must be a .png inside the project folder')
        out.screenshot = s
      }
      if (c.scores !== undefined) {
        const sc = c.scores as Record<string, unknown>
        if (typeof sc !== 'object' || sc === null || Array.isArray(sc)) throw new Error(at + 'scores must be an object')
        const keys = Object.keys(sc)
        if (keys.length > 12) throw new Error(at + 'scores has more than 12 entries')
        for (const k of keys) {
          const v = sc[k]
          if (k.length > 40) throw new Error(at + 'score name over 40 characters')
          if (typeof v === 'number') out.scores[k] = v
          else if (typeof v === 'string' && v.length <= 200) out.scores[k] = v
          else throw new Error(at + 'score "' + k + '" must be a number or a string up to 200 characters')
        }
      }
      return out
    })
    return { ok: true, manifest: { brief: str(raw.brief, 2000, 'brief'), round, candidates } }
  } catch (err) {
    return { ok: false, error: 'candidates.json: ' + (err instanceof Error ? err.message : String(err)) }
  }
}

export function scoresMarkdown(c: Candidate): string {
  const lines: string[] = []
  const keys = Object.keys(c.scores)
  if (keys.length > 0) lines.push(keys.map((k) => '**' + k + '** ' + c.scores[k]).join(' · '))
  if (c.notes !== '') lines.push(c.notes)
  return lines.join('\n\n')
}

export function pickMessage(m: Manifest, c: Candidate): string {
  return [
    'I picked candidate ' + c.id.toUpperCase() + ' ("' + c.label + '") in round ' + m.round + '.',
    'Finish it: take only this candidate through the full premium-web critic loop to final, and stop building the others.',
    c.dir !== undefined ? 'Its folder: ' + c.dir : 'Its preview: ' + (c.url ?? ''),
  ].join('\n')
}

export function feedbackMessage(m: Manifest, id: string | null, text: string, c?: Candidate): string {
  const head = id === null ? 'Feedback on all candidates (round ' + m.round + '):' : 'Feedback on candidate ' + id.toUpperCase() + ' ("' + (c?.label ?? id) + '", round ' + m.round + '):'
  return head + ' ' + text.trim() + '\nIterate per the premium-web skill (only the candidate named, or all of them if the feedback is general), then present the candidates again.'
}

// argv that opens a URL in the user's browser, by `uname -s` output ('' when uname is missing: Windows).
export function openArgv(uname: string, url: string): string[] {
  const os = uname.trim()
  if (os === 'Darwin') return ['open', url]
  if (os === 'Linux') return ['xdg-open', url]
  return ['cmd', '/c', 'start', '', url]
}

export const PORT_SCRIPT = 'import socket;s=socket.socket();s.bind(("127.0.0.1",0));print(s.getsockname()[1])'
