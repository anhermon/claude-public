#!/usr/bin/env node
// Extend the shared comparison without modifying the premium-web skill's files.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { fingerprint as sharedFingerprint, matrix } from '../../premium-web/scripts/variation-check.mjs';
import { GRAMMAR_TERMINAL, GRAMMAR_COLLAGE } from './lib/const.mjs';

const SPEC_PATHS = ['spec/piece.json', 'spec.json', 'piece/spec/piece.json'];
const EXIT = { ok:0, siblings:1, usage:2 };
const HELP = 'usage: node skills/premium-web-factory/scripts/variation-check.mjs <spec-or-piece-dir...>';
export function fingerprint(spec) {
  if (spec.grammar === GRAMMAR_TERMINAL) {
    const chapters = [...spec.terminal.session.map((entry) => ({ archetype:`command:${entry.pane.kind}` })), ...(spec.chapters || [])];
    return { ...sharedFingerprint({ ...spec, chapters }), heroLayout:'window', scrollMode:'session' };
  }
  const result = sharedFingerprint(spec);
  return spec.grammar === GRAMMAR_COLLAGE ? { ...result, heroLayout:'type', scrollMode:'collage' } : result;
}
export function readSpecs(inputs) {
  return inputs.map((input) => {
    const resolved = path.resolve(input);
    const file = fs.statSync(resolved).isDirectory() ? SPEC_PATHS.map((rel) => path.join(resolved,rel)).find((candidate) => fs.existsSync(candidate)) : resolved;
    if (!file) throw new Error(`${input}: no spec found`);
    return fingerprint(JSON.parse(fs.readFileSync(file,'utf8')));
  });
}
function main(args) {
  if (!args.length) { console.error(HELP); return EXIT.usage; }
  try { const result = matrix(readSpecs(args)); console.log(result.output); return result.failures.length ? EXIT.siblings : EXIT.ok; }
  catch(error) { console.error(error.message); return EXIT.usage; }
}
if (process.argv[1] && fs.realpathSync(process.argv[1]) === fileURLToPath(import.meta.url)) process.exitCode = main(process.argv.slice(2));
