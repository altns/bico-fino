"""PostToolUse hook: check meshes written to projects/**/final/ since the last check.

Each object must be watertight, a single body and fit the active printer. Problems are sent back
to Claude (decision "block" on PostToolUse only feeds the reason back; the tool already ran).
The first run only records a timestamp, so existing files are not re-checked.
"""
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STAMP = ROOT / ".claude" / ".mesh-check-stamp"
EXTS = {".3mf", ".stl"}


def changed_files(since: float) -> list[Path]:
    projects = ROOT / "projects"
    if not projects.exists():
        return []
    base = projects.resolve()  # follow the junction into the private repo
    return sorted(p for p in base.rglob("*") if p.suffix.lower() in EXTS and p.parent.name == "final"
                  and p.stat().st_mtime > since)


def check(path: Path, prn: dict) -> list[str]:
    from bicofino import load

    problems = []
    vol = sorted(prn["build_volume"])
    for name, m in load(path, merge=False):
        bodies = len(m.split(only_watertight=False))
        if not m.is_watertight:
            problems.append(f"{path.name} / {name}: not watertight")
        if bodies != 1:
            problems.append(f"{path.name} / {name}: {bodies} bodies (expected 1)")
        if not all(x <= y for x, y in zip(sorted(m.extents), vol)):
            e = m.extents
            problems.append(f"{path.name} / {name}: {e[0]:.1f}x{e[1]:.1f}x{e[2]:.1f} mm does not fit {prn['name']}")
    return problems


def main():
    sys.stdin.read()  # hook payload (unused)
    now = time.time()
    if not STAMP.exists():
        STAMP.write_text(str(now))
        return
    since = float(STAMP.read_text() or 0)
    files = changed_files(since)
    STAMP.write_text(str(now))
    if not files:
        return
    sys.path.insert(0, str(ROOT / "scripts"))
    from bicofino import printer

    prn = printer()
    problems = []
    for f in files:
        try:
            problems += check(f, prn)
        except Exception as e:  # a broken file is itself a finding
            problems.append(f"{f.name}: could not read ({e})")
    names = ", ".join(f.name for f in files)
    if problems:
        print(json.dumps({"decision": "block",
                          "reason": "Mesh check of new files in final/ found problems:\n- " + "\n- ".join(problems)}))
    else:
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": f"Mesh check OK ({prn['name']}): {names} — watertight, 1 body each, fits."}}))


if __name__ == "__main__":
    main()
