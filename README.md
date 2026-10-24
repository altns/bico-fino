# bico-fino

> *"Bico fino"* is Brazilian Portuguese slang for someone picky and meticulous. Literally, it also means a fine nozzle.

A small, opinionated workbench for **modeling, repairing, splitting and preparing parts for FDM 3D printing**. It works with **any FDM printer**. Flashforge AD5X, Bambu Lab A1, Creality K2 Pro, Prusa MK4S and others come as ready-made profiles, and adding yours takes a few lines of TOML. It bundles:

- **Printer profiles** (`printers.toml`) with build volume, temperature limits, enclosure and multi-color capacity. The tools check every part against the active printer.
- **Python mesh tools** (trimesh + manifold3d + pymeshlab) for inspecting, repairing and cutting STL/OBJ/3MF files, including Bambu Studio / OrcaSlicer / Flash Studio project 3MFs.
- **MCP servers** (build123d, OpenSCAD, Blender, FreeCAD), so an AI coding agent such as [Claude Code](https://claude.com/claude-code) can model parts in code and drive CAD apps.
- **A Flashforge printer helper** that talks to the AD5X / Adventurer 5M over the LAN API (discover, status, upload). Other brands send from their own slicer.
- **Git + Git LFS conventions** for versioning 3D files, with a `git diff` driver that shows mesh stats and slicer settings instead of binary noise.
- A [`CLAUDE.md`](CLAUDE.md) with printer notes, PLA profile values and FDM design rules (clearances, wall thickness, overhangs…) for the agent to follow.

---

## Table of contents

- [Requirements](#requirements)
- [Installation](#installation)
- [Choosing your printer](#choosing-your-printer)
- [Repository layout](#repository-layout)
- [Mesh tools](#mesh-tools)
- [Flashforge printer helper (LAN API)](#flashforge-printer-helper-lan-api)
- [MCP servers for AI agents](#mcp-servers-for-ai-agents)
- [Claude Code hooks, skills and agents](#claude-code-hooks-skills-and-agents)
- [Versioning 3D files with Git LFS](#versioning-3d-files-with-git-lfs)
- [FDM design rules](#fdm-design-rules)
- [License](#license)

---

## Requirements

- **Windows 10/11.** The paths in `.mcp.json` and `scripts/mcp.cmd` assume Windows. The Python scripts themselves are cross-platform.
- [**mise**](https://mise.jdx.dev/) pins Python 3.12 and [uv](https://docs.astral.sh/uv/) and creates the `.venv`.
- [**Git LFS**](https://git-lfs.com/) for `.3mf`, `.stl`, `.blend`, `.FCStd`, images, etc.
- Optional, depending on what you use:
  - [OpenSCAD](https://openscad.org/) (a nightly build with the Manifold backend is recommended)
  - [Blender](https://www.blender.org/) with the *MCP for Blender* add-on
  - [FreeCAD](https://www.freecad.org/) 1.x with the *FreeCADMCP* add-on
  - A slicer: Bambu Studio, OrcaSlicer, PrusaSlicer, Creality Print, Flash Studio…

## Installation

```bash
git clone https://github.com/altns/bico-fino.git
cd bico-fino
git lfs install
mise trust
mise install
mise exec -- uv sync
```

`uv sync` installs everything listed in [`pyproject.toml`](pyproject.toml): trimesh, manifold3d, build123d, pymeshlab, shapely, numpy/scipy, flashforge-python-api and python-dotenv.

Then pick your printer (see the next section):

```bash
cp .env.example .env      # then set PRINTER=bambu-a1 (or your printer's key)
```

Run any script through mise so it uses the project's virtualenv:

```bash
mise exec -- python scripts/mesh_info.py my_model.3mf
```

## Choosing your printer

Printer profiles live in [`printers.toml`](printers.toml):

| Key | Printer | Build volume (mm) | Multi-color | Enclosed |
|---|---|---|---|---|
| `ad5x` | Flashforge AD5X | 220 × 220 × 220 | 4 (IFS) | no |
| `adventurer-5m` | Flashforge Adventurer 5M | 220 × 220 × 220 | — | no |
| `bambu-a1` | Bambu Lab A1 | 256 × 256 × 256 | 4 (AMS lite) | no |
| `bambu-a1-mini` | Bambu Lab A1 mini | 180 × 180 × 180 | 4 (AMS lite) | no |
| `bambu-p1s` | Bambu Lab P1S | 256 × 256 × 256 | 4 (AMS) | yes |
| `bambu-x1c` | Bambu Lab X1 Carbon | 256 × 256 × 256 | 4 (AMS) | yes |
| `k2-pro` | Creality K2 Pro | 300 × 300 × 300 | 4 (CFS) | yes |
| `k1c` | Creality K1C | 220 × 220 × 250 | — | yes |
| `ender3-v3` | Creality Ender-3 V3 | 220 × 220 × 250 | — | no |
| `prusa-mk4s` | Prusa MK4S | 250 × 210 × 220 | — | no |
| `prusa-core-one` | Prusa CORE One | 250 × 220 × 270 | — | yes |

The values come from the manufacturers' published specs. Check them against your manual.

**Select the active printer.** The first match wins:

1. `--printer <key>` on the command line, e.g. `mesh_info.py part.stl --printer bambu-a1`
2. `PRINTER=<key>` in your `.env`
3. `default = "<key>"` at the top of `printers.toml`

List the profiles and see which one is active:

```bash
mise exec -- python scripts/printers.py
```

```
* ad5x             Flashforge AD5X            220x220x220 mm  nozzle up to 300 °C, bed up to 110 °C  4 filaments
  bambu-a1         Bambu Lab A1               256x256x256 mm  nozzle up to 300 °C, bed up to 100 °C  4 filaments
  k2-pro           Creality K2 Pro            300x300x300 mm  nozzle up to 350 °C, bed up to 120 °C  4 filaments enclosed
  ...
```

**Add your own printer** by appending a block to `printers.toml`:

```toml
[printers.my-printer]
name = "My Printer"
build_volume = [235, 235, 250]   # X, Y, Z in mm
max_nozzle_temp = 300            # °C
max_bed_temp = 110               # °C
enclosed = false
filament_slots = 1               # filaments in the multi-color system (1 = none)
```

In Python, `bicofino.printer()` returns the active profile. `printer("k2-pro")` returns a specific one.

## Repository layout

```
bico-fino/
├── CLAUDE.md               # Instructions for the AI agent (printers, PLA profile, design rules, workflow)
├── printers.toml          # Printer profiles (build volume, limits, multi-color)
├── .mcp.json               # MCP servers: build123d, OpenSCAD, Blender, FreeCAD
├── .env.example           # Template for local settings: active printer, Flashforge credentials
├── mise.toml / pyproject.toml / uv.lock
├── scripts/                # Mesh tools and printer helpers
├── projects/               # One folder per part you work on (git-ignored here)
├── models/
│   ├── downloads/          # Downloaded models (git-ignored here)
│   └── exports/            # Temporary outputs (git-ignored)
├── profiles/<printer>/     # Exported slicer profiles
└── references/             # Reference images, drawings, measurements
```

Suggested structure for each project in `projects/<name>/`:

| Folder | Contents |
|---|---|
| `original/` | The source file (download or customer file). Never edited. |
| `source/` | What generates the part: scripts, `.scad`, `.FCStd`, `.blend`, working 3MF. |
| `final/` | What goes to the slicer: print-ready 3MF, STLs, preview images. |
| `README.md` | What it is, dimensions, colors/filaments, how to print/assemble, short history. |

> This public repository ignores `projects/` and `models/downloads/`, so personal work and third-party downloads stay on your machine. To version them in a private copy, remove those lines from `.gitignore`.

**Keeping your projects in a private repo.** The author's setup keeps personal projects in a separate private repository cloned at `private/` (also ignored), and makes `projects/` and `models/downloads/` Windows directory junctions pointing into it, so every path stays the same:

```powershell
git clone git@github.com:<you>/<your-private-repo>.git private
New-Item -ItemType Junction -Path projects -Target private\projects
New-Item -ItemType Junction -Path models\downloads -Target private\models\downloads
```

Copy `.gitattributes` into the private repo so its 3D files also go through Git LFS, and commit there with `git -C private ...`.

## Mesh tools

All tools read **STL, OBJ and 3MF** (including multi-object Bambu/Orca/Flash Studio projects) and write **3MF** with named objects, ready to open in any slicer.

### `mesh_info.py`: inspect a mesh

Shows size, whether the mesh is watertight, number of bodies, volume, estimated PLA weight and whether it fits the active printer.

```bash
mise exec -- python scripts/mesh_info.py part.3mf
mise exec -- python scripts/mesh_info.py part.stl --scale 1.5            # check a scaled version
mise exec -- python scripts/mesh_info.py part.stl --printer bambu-a1     # check against another printer
```

```
== bracket
   size (mm): 144.6 x 161.7 x 24.6
   faces: 2522  bodies: 1  watertight: True  consistent normals: True
   volume: 165.1 cm³  solid PLA weight: 205 g (with 15% infill and 2 walls, typically 25-40% of that)
   fits Bambu Lab A1 (256x256x256): yes
```

The fit check allows the part to be rotated, so it compares the sorted dimensions of the part with the sorted dimensions of the build volume.

### `repair_mesh.py`: repair a mesh

Merges duplicate vertices, removes duplicate and degenerate faces, fixes non-manifold edges and vertices, closes holes and re-orients normals (pymeshlab + trimesh).

```bash
mise exec -- python scripts/repair_mesh.py broken.stl fixed.3mf
```

### `split_with_pins.py`: split a part with alignment pins

Cuts a model with an axis-aligned plane, drills matching holes in both halves and generates the dowel pins as separate objects (0.15 mm radial clearance, chamfered ends). The pins go at the points of the cross-section farthest from the edges. Use it for parts larger than your printer's build volume, or to print each half with the cut face on the bed.

```bash
# Cut at the middle of Z, 2 pins of 4 mm, holes 6 mm deep in each half
mise exec -- python scripts/split_with_pins.py vase.stl vase_split.3mf --axis z

# Cut at X = 80 mm from the model's minimum, 3 pins of 5 mm
mise exec -- python scripts/split_with_pins.py sign.3mf sign_split.3mf --axis x --pos 80 --pins 3 --diam 5
```

| Option | Default | Meaning |
|---|---|---|
| `--axis` | `z` | Cutting axis (`x`, `y` or `z`) |
| `--pos` | middle | Cut position in mm, measured from the model's minimum on that axis |
| `--pins` | `2` | Number of pins |
| `--diam` | `4.0` | Pin diameter (mm) |
| `--depth` | `6.0` | Hole depth in each half (mm) |

### `summarize_3mf.py`: text summary for `git diff`

Prints the mesh summary of each object and, for slicer projects, every print setting as `key = value`. Git uses it as a `textconv` driver (see [below](#versioning-3d-files-with-git-lfs)), and you can also run it on its own:

```bash
mise exec -- python scripts/summarize_3mf.py project.3mf
```

### `bicofino.py`: shared library

Import it from your own scripts (run from `scripts/` or add it to `sys.path`):

```python
from bicofino import load, save_3mf, to_manifold, from_manifold, printer

objs = load("model.3mf", merge=False)             # [(name, trimesh.Trimesh), ...]
mesh = load("model.stl")                           # single merged mesh

m = to_manifold(mesh)                              # robust booleans with manifold3d
m = m - to_manifold(other_mesh)
result = from_manifold(m)                          # back to trimesh, near-duplicate vertices merged

save_3mf("out.3mf", [("Base", result), ("Lid", lid)])
print(printer()["build_volume"])                   # e.g. [256, 256, 256]
```

| Function | Purpose |
|---|---|
| `load(path, merge=True)` | Read STL/OBJ/3MF. Returns one merged mesh or a list of `(name, mesh)` |
| `save_3mf(path, objects)` | Write several named objects into one 3MF |
| `to_manifold(mesh)` / `from_manifold(x)` | Convert to and from `manifold3d` for reliable booleans |
| `clean(mesh)` | Round vertices, merge duplicates, drop degenerate faces |
| `printer(key=None)` | Active printer profile (dict with `name`, `build_volume`, `max_nozzle_temp`…) |
| `center_on_bed(mesh)` | Center on the active printer's bed and drop to Z = 0 |

**Mesh tips learned the hard way**

- Prefer manifold3d for booleans. trimesh and Blender booleans often leave non-manifold results.
- Don't use `Manifold.simplify()`: it tilts the walls of letters and fine details.
- Avoid cuts that are exactly coplanar with existing faces. They create zero-thickness "films" that slicers show as jagged artifacts. Offset the cut slightly (e.g. +0.002 mm) or rebuild from 2D outlines.
- Before shipping a part, run `mesh_info.py`. Each part should be watertight with 1 body.

## Flashforge printer helper (LAN API)

`scripts/flashforge_lan.py` uses [flashforge-python-api](https://pypi.org/project/flashforge-python-api/) to talk to Flashforge printers (AD5X, Adventurer 5M / 5M Pro) over the local network (ports 8898/8899). These printers run Flashforge's Klipper firmware without Moonraker, so the helper uses the LAN-mode API.

For **Bambu Lab, Creality, Prusa** and other brands, send from their own slicer (Bambu Studio, Creality Print, PrusaSlicer, OrcaSlicer). All of them open the 3MF files these tools produce.

> ⚠️ This helper has not been tested end-to-end against a real printer yet. The normal workflow is to open the 3MF in your slicer and send from there.

1. On the printer, enable LAN mode and note the IP, serial number and **check code** (Settings › Network).
2. Fill them in your `.env`. **Never commit `.env`** (it is git-ignored).

   ```ini
   FLASHFORGE_IP=192.168.x.x
   FLASHFORGE_SERIAL=...
   FLASHFORGE_CHECK_CODE=...
   ```

3. Use it:

   ```bash
   mise exec -- python scripts/flashforge_lan.py discover                 # discover printers on the LAN
   mise exec -- python scripts/flashforge_lan.py status                   # current state, temperatures, job
   mise exec -- python scripts/flashforge_lan.py upload part.gcode.3mf    # upload only
   mise exec -- python scripts/flashforge_lan.py upload part.gcode.3mf --print --slot 2 --color "#FF0000"
   ```

The uploaded file must already be **sliced** (`.gcode` or `.gcode.3mf`). On the AD5X, `--slot` selects the IFS filament slot (1–4).

## MCP servers for AI agents

[`.mcp.json`](.mcp.json) registers four [Model Context Protocol](https://modelcontextprotocol.io/) servers. Each one starts through `scripts/mcp.cmd`, which changes into the repo folder and runs the command via mise, so `uv`/`uvx` and Python 3.12 are always available.

| Server | Package | Best for | Needs |
|---|---|---|---|
| **build123d** | `build123d-mcp` | Parametric CAD in code: functional parts with exact dimensions and tolerances | nothing else |
| **openscad** | `openscad-mcp` | OpenSCAD models; render and export STL/3MF | OpenSCAD installed (`OPENSCAD_PATH`) |
| **blender** | `mcp-for-blender` | Organic meshes, sculpting, rendering | Blender open, add-on enabled: viewport › `N` › *MCP for Blender* › **Start MCP Server** |
| **freecad** | `freecad-mcp` | B-rep parametric CAD, assemblies | FreeCAD open, *MCP Addon* workbench › **Start RPC Server** |

**Setup notes**

- The paths in `.mcp.json` point to `C:\3D` and to the default OpenSCAD Nightly location. Edit them to match your clone and installs.
- `scripts/mcp.cmd` calls mise from `%LOCALAPPDATA%\Microsoft\WinGet\Links\mise.exe` (the WinGet install location). Change it if you installed mise elsewhere.
- With Claude Code, open the repo folder and approve the project MCP servers. `.claude/settings.json` already enables all four. `CLAUDE.md` tells the agent which tool to use for what, where the printer profiles are, and the design rules below. Edit its *The user's printer* section to describe your own machine and slicer.

## Claude Code hooks, skills and agents

Everything here lives in `.claude/` and loads automatically when you open the repo in Claude Code.

**Hooks** ([`.claude/settings.json`](.claude/settings.json), scripts in `scripts/hooks/`)

| Hook | When | What it does |
|---|---|---|
| `check_new_meshes.py` | After every Bash/PowerShell/Write/MCP tool call | Finds `.3mf`/`.stl` files in any `projects/**/final/` folder that changed since the last check and verifies each object is watertight, a single body and fits the active printer. Problems go straight back to Claude; a clean check adds a one-line note. The first run only records a timestamp. |
| `guard_print.py` | Before every Bash/PowerShell call | If the command would start a print (`flashforge_lan.py upload ... --print`), Claude Code asks you for permission, whatever the permission mode. |

The hook commands call `.venv/Scripts/python.exe` (Windows). On Linux/macOS change it to `.venv/bin/python`.

**Skills** (`.claude/skills/`)

| Skill | Use it for |
|---|---|
| `prepare-print` | Inspect → repair → fit/split → design-rule check → save to `final/` → update the README. |
| `new-project` | Create `projects/<name>/` with `original/`, `source/`, `final/` and a README template. |
| `b123d-modeling`, `b123d-edit`, `b123d-repair` | The build123d MCP server's own workflows (installed with its `install_skill` tool): model from a description or drawing, edit existing parts, repair invalid solids. |

**Agent** (`.claude/agents/mesh-reviewer.md`): a read-only reviewer that checks files in `final/` (watertight, bodies, fit, sections vs. the original, design rules, README consistency) and reports PASS/FAIL per file. Ask for it explicitly, e.g. *"use the mesh-reviewer agent on projects/Theo"*.

### Third-party extras worth considering

Researched on 2026-10-23 (stars and dates checked on GitHub, features from the READMEs, nothing tested). None of these is installed. Pin exact versions (`npx -y pkg@x.y.z`, `uvx pkg==x.y.z`) and keep print-start confirmations on.

| Need | Project | Notes |
|---|---|---|
| Bambu Lab printers (LAN) | [DMontgomery40/bambu-printer-mcp](https://github.com/DMontgomery40/bambu-printer-mcp) | GPL-2.0, actively maintained, MQTT/FTPS with the access code, Bambu Studio CLI slicing, preflight confirmation for print starts. Avoid look-alike forks. |
| Klipper/Moonraker, OctoPrint, PrusaLink, Creality | [DMontgomery40/mcp-3D-printer-server](https://github.com/DMontgomery40/mcp-3D-printer-server) | GPL-2.0, one server for many backends, human confirmation on by default (never set `PRINT_REQUIRE_CONFIRMATION=0`). Moonraker/Prusa support is community-reported. |
| Printability checks + OrcaSlicer CLI slicing | [earthtojake/text-to-cad](https://github.com/earthtojake/text-to-cad) | Claude Code plugin (MIT) with a DfAM check skill and a G-code skill. Telemetry is **on by default** (`uvx cadgen telemetry off`); its unsigned DLL is blocked by Windows Smart App Control. |
| OpenSCAD design / reconstruct from STL | [andreahaku/openscad_claude_skill](https://github.com/andreahaku/openscad_claude_skill) | Complements openscad-mcp; no license and Bash-only scripts. |
| Flashforge | — | No dedicated MCP exists; `scripts/flashforge_lan.py` is the integration. |

## Versioning 3D files with Git LFS

[`.gitattributes`](.gitattributes) sends 3D and image binaries (`.3mf`, `.stl`, `.obj`, `.step`, `.blend`, `.FCStd`, `.png`, `.jpg`…) through Git LFS. Text sources (`.scad`, `.py`, `.md`) stay in regular git.

**Readable diffs for meshes.** `.3mf` and `.stl` use a `mesh3d` diff driver. Enable it once per clone:

```bash
git config diff.mesh3d.textconv ".venv/Scripts/python.exe -X utf8 scripts/summarize_3mf.py"
```

(On Linux/macOS use `.venv/bin/python`.) After that, `git diff` and `git log -p` show changes in size, volume, weight and every slicer setting, e.g.:

```diff
-   size (mm): 96.4 x 120.0 x 12.0
+   size (mm): 96.4 x 120.0 x 14.0
-layer_height = 0.2
+layer_height = 0.16
```

**Conventions**

- A new version is a **new commit of the same file**. No `_v2`, `_final_final` or dates in file names.
- Tag a printed and approved version: `git tag <project>-v<n>`.
- To extract an old version of an LFS file: `git cat-file --filters <commit>:<path> > old.3mf` (`git show` returns only the LFS pointer).
- Not versioned: `.env`, `.venv`, G-code, `models/exports/`, Blender/FreeCAD backups.

## FDM design rules

These are the defaults the scripts and the agent use, for **PLA with a 0.4 mm nozzle**. They hold on most printers, but print a tolerance test on your own machine and adjust.

**Clearances (per side / radial)**

| Fit | Clearance |
|---|---|
| Press fit | 0.0 – 0.1 mm |
| Snug, glued (dowel pins) | **0.15 mm** (script default) |
| Sliding | 0.2 – 0.3 mm |
| Print-in-place hinge | 0.3 – 0.5 mm |

**Other rules**

- Vertical holes print smaller: add 0.1–0.2 mm to the diameter.
- Horizontal holes: teardrop shape.
- Minimum wall 0.8 mm (2 perimeters). Use 1.2–1.6 mm for strength.
- Minimum detail ≈ 0.4 mm.
- Overhangs up to 45° without support. Bridges up to ≈ 15 mm.
- 0.4–0.6 mm chamfer on the bottom edge to counter elephant's foot.
- Functional threads: use heat-set inserts or captive nuts instead of printed threads.
- When splitting parts: cut face on the bed, with dowel pins or a lip/recess for alignment.

**Reference PLA profile** (OrcaSlicer "@FF AD5X", 0.4 mm nozzle; similar on most printers, but prefer your slicer's profile for your machine): nozzle 210 °C (first layer 215 °C), bed 60 °C on textured PEI, 0.20 mm layers (0.25 mm first layer), max volumetric speed ≈ 21 mm³/s, elephant-foot compensation 0.1 mm, auto tree supports with 0.16 mm Z distance. Density for weight estimates: 1.24 g/cm³.

**Other printer-independent settings** live in the scripts: `PLA_DENSITY` in `scripts/bicofino.py` and `HOLE_CLEARANCE` (pin clearance) in `scripts/split_with_pins.py`.

## License

[MIT](LICENSE)
