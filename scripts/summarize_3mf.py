"""Text summary of a 3MF/STL for `git diff` (mesh3d driver).

Shows each object's mesh (via mesh_info) and, for Bambu/Orca/Flash Studio projects,
the print settings as "key = value", so the diff points exactly at what changed.

    python scripts/summarize_3mf.py file.3mf
"""
import json
import subprocess
import sys
import zipfile
from pathlib import Path


def settings(path: str) -> list[str]:
    lines = []
    try:
        z = zipfile.ZipFile(path)
    except zipfile.BadZipFile:
        return lines
    for name in sorted(z.namelist()):
        if name.endswith("project_settings.config"):
            try:
                cfg = json.loads(z.read(name))
            except ValueError:
                continue
            lines.append(f"[{name}]")
            for k in sorted(cfg):
                v = cfg[k]
                v = ", ".join(map(str, v)) if isinstance(v, list) else str(v)
                lines.append(f"{k} = {v.replace(chr(10), ' | ')}")
        elif name.endswith((".config", ".json")) and not name.endswith("project_settings.config"):
            lines.append(f"[{name}] {len(z.read(name))} bytes")
    return lines


def main():
    file = sys.argv[1]
    info = Path(__file__).with_name("mesh_info.py")
    r = subprocess.run([sys.executable, "-X", "utf8", str(info), file], capture_output=True, text=True, encoding="utf-8")
    print(r.stdout, end="")
    if file.lower().endswith(".3mf"):
        print("\n".join(settings(file)))


if __name__ == "__main__":
    main()
