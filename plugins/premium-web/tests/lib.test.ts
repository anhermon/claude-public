import { expect, test } from 'claude-code/testing'
import { clampCount, openArgv, resolveInside, validateManifest } from '../hooks/lib.ts'

const CWD = '/proj'
const good = (over: Record<string, unknown> = {}) =>
  JSON.stringify({
    brief: 'b',
    round: 2,
    candidates: [
      { id: 'a', label: 'Alpha', direction: 'd', dir: 'sites/a', screenshot: 'shots/a.png', scores: { wow: 4, sections: 'ok' }, notes: 'n' },
      { id: 'b-2', url: 'https://example.com/x' },
    ],
    ...over,
  })

test('valid manifest is normalised and paths are made absolute', () => {
  const r = validateManifest(good(), CWD)
  expect(r.ok).toBe(true)
  if (r.ok) {
    expect(r.manifest.round).toBe(2)
    expect(r.manifest.candidates[0].dir).toBe('/proj/sites/a')
    expect(r.manifest.candidates[0].screenshot).toBe('/proj/shots/a.png')
    expect(r.manifest.candidates[1].label).toBe('b-2')
  }
})

test('path escapes are rejected', () => {
  for (const dir of ['../outside', '/etc', 'a/../../x', '/projx/evil', 'a\\b', '/proj/../etc']) {
    const r = validateManifest(JSON.stringify({ candidates: [{ id: 'a', dir }] }), CWD)
    expect(r.ok).toBe(false)
  }
  expect(resolveInside(CWD, 'a/../b')).toBe('/proj/b')
  expect(resolveInside(CWD, '/proj')).toBe('/proj')
  expect(resolveInside(CWD, '..')).toBe(null)
})

test('ids, urls, screenshots and sizes are validated', () => {
  const bad = (c: Record<string, unknown>) => validateManifest(JSON.stringify({ candidates: [c] }), CWD).ok
  expect(bad({ id: 'A', dir: 'a' })).toBe(false)
  expect(bad({ id: 'a b', dir: 'a' })).toBe(false)
  expect(bad({ id: 'x'.repeat(33), dir: 'a' })).toBe(false)
  expect(bad({ id: 'a' })).toBe(false) // needs dir or url
  expect(bad({ id: 'a', url: 'javascript:alert(1)' })).toBe(false)
  expect(bad({ id: 'a', url: 'file:///etc/passwd' })).toBe(false)
  expect(bad({ id: 'a', dir: 'a', screenshot: 'shot.jpg' })).toBe(false)
  expect(bad({ id: 'a', dir: 'a', notes: 'x'.repeat(2001) })).toBe(false)
  expect(bad({ id: 'a', dir: 'a', scores: { k: { nested: 1 } } })).toBe(false)
  expect(bad({ id: 'a', dir: 'a' })).toBe(true)
  expect(validateManifest(JSON.stringify({ candidates: [{ id: 'a', dir: 'a' }, { id: 'a', dir: 'b' }] }), CWD).ok).toBe(false)
  expect(validateManifest(JSON.stringify({ candidates: [] }), CWD).ok).toBe(false)
  expect(validateManifest('not json', CWD).ok).toBe(false)
  expect(validateManifest(' '.repeat(300 * 1024), CWD).ok).toBe(false)
  expect(validateManifest(good({ round: 0 }), CWD).ok).toBe(false)
})

test('candidate count is clamped to 1-6 with default 3', () => {
  expect(clampCount(undefined)).toBe(3)
  expect(clampCount('x')).toBe(3)
  expect(clampCount(5)).toBe(5)
  expect(clampCount(0)).toBe(1)
  expect(clampCount(99)).toBe(6)
  expect(clampCount(2.6)).toBe(3)
})

test('browser command per OS', () => {
  expect(openArgv('Darwin\n', 'http://x/')).toEqual(['open', 'http://x/'])
  expect(openArgv('Linux', 'http://x/')).toEqual(['xdg-open', 'http://x/'])
  expect(openArgv('', 'http://x/')[0]).toBe('cmd')
})
