#!/usr/bin/env python3
"""
setup_custom_dashboard.py — Deploy and start the custom telemetry stack.

Copies the bundled dashboard and backend from the skill to a destination
directory, installs dependencies, and starts both services.

Usage:
    python3 setup_custom_dashboard.py [--dest PATH]

Options:
    --dest PATH   Root directory for instances (default: ~/.paperclip/instances)
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


SKILL_DIR = Path(__file__).parent.parent
DASHBOARD_SRC = SKILL_DIR / "dashboard"
BACKEND_SRC = SKILL_DIR / "backend"

BACKEND_PORT = 5001
DASHBOARD_PORT = 3001
BACKEND_URL = f"http://localhost:{BACKEND_PORT}/events"

HOOKS_DIR = Path.home() / ".claude" / "hooks"
HOOK_PATTERN = re.compile(r'"http://localhost:\d+/events"')
HOOK_REPLACEMENT = f'"http://localhost:{BACKEND_PORT}/events"'


def run(cmd: list[str], cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess:
    print(f"  $ {' '.join(str(c) for c in cmd)}")
    return subprocess.run(cmd, cwd=cwd, check=check, text=True, capture_output=False)


def copy_tree(src: Path, dest: Path, skip_if_exists: bool = False) -> bool:
    """Copy src to dest. Returns True if copy was performed, False if skipped."""
    if dest.exists():
        if skip_if_exists:
            print(f"  Skipping copy — {dest} already exists (reusing existing installation)")
            return False
        shutil.rmtree(dest)
    shutil.copytree(src, dest, ignore=shutil.ignore_patterns(
        "node_modules", ".next", "__pycache__", "*.db", "*.pyc",
    ))
    print(f"  Copied {src} -> {dest}")
    return True


def install_backend(backend_dest: Path) -> None:
    req = backend_dest / "requirements.txt"
    if not req.exists():
        print("  WARNING: requirements.txt not found, skipping pip install")
        return
    run(["pip", "install", "-r", str(req)], cwd=backend_dest)


def install_dashboard(dashboard_dest: Path) -> None:
    pkg = dashboard_dest / "package.json"
    if not pkg.exists():
        print("  WARNING: package.json not found, skipping npm install")
        return
    run(["npm", "install"], cwd=dashboard_dest)


def start_backend(backend_dest: Path) -> None:
    pid_file = backend_dest / ".backend.pid"
    log_file = backend_dest / "backend.log"

    if pid_file.exists():
        try:
            pid = int(pid_file.read_text().strip())
            os.kill(pid, 0)  # check process exists
            print(f"  Backend already running (pid {pid}), skipping start")
            return
        except (ProcessLookupError, OSError):
            pid_file.unlink(missing_ok=True)

    env = os.environ.copy()
    env["PORT"] = str(BACKEND_PORT)
    env["HOST"] = "0.0.0.0"

    with open(log_file, "w") as log:
        proc = subprocess.Popen(
            [sys.executable, "app.py"],
            cwd=backend_dest,
            env=env,
            stdout=log,
            stderr=log,
            start_new_session=True,
        )
    pid_file.write_text(str(proc.pid))
    print(f"  Backend started (pid {proc.pid}) on :{BACKEND_PORT} — logs: {log_file}")


def start_dashboard(dashboard_dest: Path) -> None:
    pid_file = dashboard_dest / ".dashboard.pid"
    log_file = dashboard_dest / "dashboard.log"

    if pid_file.exists():
        try:
            pid = int(pid_file.read_text().strip())
            os.kill(pid, 0)
            print(f"  Dashboard already running (pid {pid}), skipping start")
            return
        except (ProcessLookupError, OSError):
            pid_file.unlink(missing_ok=True)

    env = os.environ.copy()
    env["PORT"] = str(DASHBOARD_PORT)

    with open(log_file, "w") as log:
        proc = subprocess.Popen(
            ["npm", "run", "dev", "--", "-p", str(DASHBOARD_PORT)],
            cwd=dashboard_dest,
            env=env,
            stdout=log,
            stderr=log,
            start_new_session=True,
        )
    pid_file.write_text(str(proc.pid))
    print(f"  Dashboard started (pid {proc.pid}) on :{DASHBOARD_PORT} — logs: {log_file}")


def update_hooks(target_url: str) -> None:
    if not HOOKS_DIR.exists():
        print(f"  Hooks dir not found ({HOOKS_DIR}), skipping hook update")
        return

    updated = []
    for hook_file in sorted(HOOKS_DIR.glob("*.py")):
        text = hook_file.read_text()
        new_text, n = re.subn(
            r'http://localhost:\d+/events',
            target_url,
            text,
        )
        if n > 0:
            hook_file.write_text(new_text)
            updated.append(hook_file.name)

    if updated:
        print(f"  Updated hooks to POST to {target_url}: {', '.join(updated)}")
    else:
        print(f"  No hooks needed updating (already pointing to {target_url} or none found)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Deploy custom telemetry dashboard and backend")
    parser.add_argument(
        "--dest",
        default=str(Path.home() / ".paperclip" / "instances"),
        help="Root directory for instances (default: ~/.paperclip/instances)",
    )
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        default=False,
        help="Run without prompts; reuse existing installations instead of overwriting them",
    )
    args = parser.parse_args()

    skip_existing = args.non_interactive

    dest_root = Path(args.dest).expanduser().resolve()
    backend_dest = dest_root / "telemetry-backend"
    dashboard_dest = dest_root / "telemetry-dashboard"

    print(f"\n=== Telemetry Stack Setup ===")
    print(f"Destination: {dest_root}\n")

    # Step 1: Copy source files
    print("[1/4] Copying backend files...")
    backend_copied = copy_tree(BACKEND_SRC, backend_dest, skip_if_exists=skip_existing)

    print("\n[2/4] Copying dashboard files...")
    dashboard_copied = copy_tree(DASHBOARD_SRC, dashboard_dest, skip_if_exists=skip_existing)

    # Verify copies
    assert (backend_dest / "app.py").exists(), "app.py missing after copy"
    assert (dashboard_dest / "package.json").exists(), "package.json missing after copy"
    print("  Verification: OK")

    # Step 2: Install dependencies (skip if we reused an existing install)
    print("\n[3/4] Installing dependencies...")
    if backend_copied:
        print("  Installing backend (pip)...")
        install_backend(backend_dest)
    else:
        print("  Skipping backend pip install (reusing existing)")
    if dashboard_copied:
        print("  Installing dashboard (npm)...")
        install_dashboard(dashboard_dest)
    else:
        print("  Skipping dashboard npm install (reusing existing)")

    # Step 3: Start services
    print("\n[4/4] Starting services...")
    start_backend(backend_dest)
    start_dashboard(dashboard_dest)

    # Step 4: Update hooks
    print("\n[+] Updating Claude hooks...")
    update_hooks(BACKEND_URL)

    print(f"""
=== Setup complete ===
  Backend:   http://localhost:{BACKEND_PORT}   (health: http://localhost:{BACKEND_PORT}/health)
  Dashboard: http://localhost:{DASHBOARD_PORT}

Logs:
  {backend_dest}/backend.log
  {dashboard_dest}/dashboard.log

To stop services, kill by PID:
  kill $(cat {backend_dest}/.backend.pid)
  kill $(cat {dashboard_dest}/.dashboard.pid)
""")


if __name__ == "__main__":
    main()
