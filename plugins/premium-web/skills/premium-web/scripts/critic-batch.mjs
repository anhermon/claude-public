#!/usr/bin/env node
// critic-batch.mjs: run critic.py ONLY where it is worth its cost.
//   node critic-batch.mjs <piece-dir> [--sections a,b | --all] [--max-rounds N] [--wow ID | --wow-exempt REASON] [--wow-test T] [--dry-run] [--selftest]
// Default selection = report.failing_sections from verify-piece.mjs (sections that failed a mechanical gate). --all = every section
// (use once, on the final round). A section that already used --max-rounds critic runs without passing is SKIPPED with a verdict:
// replace its focal moment or ship it on the known-defects list (references/factory-efficiency.md). Round counts live in
// <piece-dir>/.verify/critic-rounds.json and reset when the section passes. Exit codes are critic.py's (0 pass, 1 fail, 2 usage, 3 unavailable);
// 4 = every requested section is out of rounds.
import { spawnSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url)), DEFAULT_MAX_ROUNDS = 3, EXIT_OUT_OF_ROUNDS = 4;
const VERIFY = ".verify", ROUNDS_FILE = "critic-rounds.json";

// pure: which sections to run, which to skip (budget), given the requested list and the round ledger
export function select(requested, rounds, maxRounds) {
  const skip = requested.filter((s) => (rounds[s] || 0) >= maxRounds);
  return { run: requested.filter((s) => !skip.includes(s)), skip };
}
function selftest() {
  const a = select(["a", "b", "c"], { b: 3, c: 2 }, 3);
  const ok = a.run.join() === "a,c" && a.skip.join() === "b" && select([], {}, 3).run.length === 0;
  console.log(ok ? "selftest ok" : "selftest FAILED"); process.exit(ok ? 0 : 1);
}
const argv = process.argv.slice(2);
if (argv.includes("--help") || !argv.length) { console.log(fs.readFileSync(fileURLToPath(import.meta.url), "utf8").split("\n").slice(1, 9).map((l) => l.replace(/^\/\/ ?/, "")).join("\n")); process.exit(argv.length ? 0 : 2); }
if (argv.includes("--selftest")) selftest();
const val = (n) => (argv.includes(n) ? argv[argv.indexOf(n) + 1] : undefined);
const dir = path.resolve(argv.find((a, i) => !a.startsWith("--") && !["--sections", "--max-rounds", "--wow", "--wow-exempt", "--wow-test"].includes(argv[i - 1])));
const root = path.join(dir, VERIFY), secRoot = path.join(root, "sections"), ledger = path.join(root, ROUNDS_FILE);
const maxRounds = Number(val("--max-rounds") || process.env.CRITIC_MAX_ROUNDS || DEFAULT_MAX_ROUNDS);
const all = fs.existsSync(secRoot) ? fs.readdirSync(secRoot).filter((d) => fs.statSync(path.join(secRoot, d)).isDirectory()).sort() : [];
if (!all.length) { console.error(`no ${VERIFY}/sections: run verify-piece.mjs first`); process.exit(2); }
let requested = argv.includes("--all") ? all.filter((s) => !/footer|foot$/i.test(s)) : val("--sections") ? val("--sections").split(",") : (JSON.parse(fs.readFileSync(path.join(root, "report.json"), "utf8")).failing_sections || []);
const wow = val("--wow");
if (!requested.length && !wow) { console.log("critic-batch: no failing sections and no --wow: nothing to judge (use --all for the final round)"); process.exit(0); }
let rounds = {}; try { rounds = JSON.parse(fs.readFileSync(ledger, "utf8")); } catch {}
const { run, skip } = select(requested.filter((s) => s !== wow), rounds, maxRounds);
skip.forEach((s) => console.log(`SKIP ${s}: ${rounds[s]} critic rounds used (max ${maxRounds}): replace its focal moment or ship it on the known-defects list`));
if (!run.length && !wow) process.exit(EXIT_OUT_OF_ROUNDS);
const args = [path.join(HERE, "critic.py"), secRoot, "--only", run.join(","), ...(wow ? ["--wow", wow] : ["--wow-exempt", val("--wow-exempt") || "not requested for this batch (sub-run of failing sections)"]), ...(val("--wow-test") ? ["--wow-test", val("--wow-test")] : [])];
if (!run.length) args.splice(2, 2); // only the wow dir
console.log(`critic-batch: ${run.length} section(s) [${run.join(",")}]${wow ? ` + wow ${wow}` : ""}, max-rounds ${maxRounds}${skip.length ? `, ${skip.length} skipped` : ""}`);
if (argv.includes("--dry-run")) { console.log("python3 " + args.join(" ")); process.exit(0); }
const r = spawnSync("python3", ["-I", ...args], { stdio: "inherit" });
let res = {}; try { res = JSON.parse(fs.readFileSync(path.join(secRoot, "critic.json"), "utf8")).sections || {}; } catch {}
if (r.status !== 3) { for (const s of run) rounds[s] = res[s]?.pass ? 0 : (rounds[s] || 0) + 1; fs.writeFileSync(ledger, JSON.stringify(rounds, null, 1)); } // exit 3 = critic unavailable: not a round
process.exit(r.status ?? 2);
