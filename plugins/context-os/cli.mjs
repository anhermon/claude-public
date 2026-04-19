#!/usr/bin/env node
/**
 * npx / bunx shim: runs the Python package via `python3 -m context_os`.
 * Requires Python 3.10+. With a dev checkout, sets PYTHONPATH to the repo root.
 */
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import path from "node:path";
import fs from "node:fs";

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here);
const py = process.env.PYTHON ?? "python3";
const argv = process.argv.slice(2);

const env = { ...process.env };
if (!env.PYTHONPATH) {
  env.PYTHONPATH = root;
} else if (!env.PYTHONPATH.split(path.delimiter).includes(root)) {
  env.PYTHONPATH = `${root}${path.delimiter}${env.PYTHONPATH}`;
}

let r = spawnSync(py, ["-m", "context_os", ...argv], {
  stdio: "inherit",
  env,
  encoding: "utf-8",
});

if (r.status === 0) {
  process.exit(0);
}

if (r.error?.code === "ENOENT") {
  console.error("context-os: Python not found. Install Python 3.10+ or set PYTHON.");
  process.exit(127);
}

const cliPy = path.join(root, "context_os", "context_os_cli.py");
if (fs.existsSync(cliPy)) {
  r = spawnSync(py, [cliPy, ...argv], { stdio: "inherit", env, cwd: root });
  process.exit(r.status ?? 1);
}

process.exit(r.status ?? 1);
