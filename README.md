# bico-fino

> *"Bico fino"* is Brazilian Portuguese slang for someone picky and meticulous. Literally, it also means a fine nozzle.

A small, opinionated workbench for **modeling, repairing, splitting and preparing parts for FDM 3D printing**. It works with **any FDM printer**. Flashforge AD5X, Bambu Lab A1, Creality K2 Pro, Prusa MK4S and others come as ready-made profiles, and adding yours takes a few lines of TOML. It bundles:

- **Printer profiles** (`impressoras.toml`) with build volume, temperature limits, enclosure and multi-color capacity. The tools check every part against the active printer.
- **Python mesh tools** (trimesh + manifold3d + pymeshlab) for inspecting, repairing and cutting STL/OBJ/3MF files, including Bambu Studio / OrcaSlicer / Flash Studio project 3MFs.
- **MCP servers** (build123d, OpenSCAD, Blender, FreeCAD), so an AI coding agent such as [Claude Code](https://claude.com/claude-code) can model parts in code and drive CAD apps.
- **A Flashforge printer helper** that talks to the AD5X / Adventurer 5M over the LAN API (discover, status, upload). Other brands send from their own slicer.
- **Git + Git LFS conventions** for versioning 3D files, with a `git diff` driver that shows mesh stats and slicer settings instead of binary noise.
- A [`CLAUDE.md`](CLAUDE.md) with printer notes, PLA profile values and FDM design rules (clearances, wall thickness, overhangs…) for the agent to follow.

The scripts, CLI output and `CLAUDE.md` are in Portuguese (pt-BR). This README is in English.

---

## Table of contents

- [Requirements](#requirements)
- [Installation](#installation)
- [Choosing your printer](#choosing-your-printer)
- [Repository layout](#repository-layout)
- [Mesh tools](#mesh-tools)
- [Flashforge printer helper (LAN API)](#flashforge-printer-helper-lan-api)
- [MCP servers for AI agents](#mcp-servers-for-ai-agents)
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
cp .env.exemplo .env      # then set IMPRESSORA=bambu-a1 (or your printer's key)
```

Run any script through mise so it uses the project's virtualenv:

```bash
mise exec -- python scripts/info_malha.py my_model.3mf
```

## Choosing your printer

Printer profiles live in [`impressoras.toml`](impressoras.toml):

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

1. `--impressora <key>` on the command line, e.g. `info_malha.py part.stl --impressora bambu-a1`
2. `IMPRESSORA=<key>` in your `.env`
3. `padrao = "<key>"` at the top of `impressoras.toml`

List the profiles and see which one is active:

```bash
mise exec -- python scripts/impressoras.py
```

```
* ad5x             Flashforge AD5X            220x220x220 mm  bico até 300 °C, mesa até 110 °C  4 cores
  bambu-a1         Bambu Lab A1               256x256x256 mm  bico até 300 °C, mesa até 100 °C  4 cores
  k2-pro           Creality K2 Pro            300x300x300 mm  bico até 350 °C, mesa até 120 °C  4 cores fechada
  ...
```

**Add your own printer** by appending a block to `impressoras.toml`:

```toml
[impressoras.my-printer]
nome = "My Printer"
volume = [235, 235, 250]   # X, Y, Z in mm
bico_max = 300             # max nozzle temperature (°C)
mesa_max = 110             # max bed temperature (°C)
fechada = false            # enclosed?
multicor = 1               # filaments in the multi-color system (1 = none)
```

In Python, `estudio3d.impressora()` returns the active profile. `impressora("k2-pro")` returns a specific one.

## Repository layout

```
bico-fino/
├── CLAUDE.md               # Instructions for the AI agent (printers, PLA profile, design rules, workflow)
├── impressoras.toml        # Printer profiles (build volume, limits, multi-color)
├── .mcp.json               # MCP servers: build123d, OpenSCAD, Blender, FreeCAD
├── .env.exemplo            # Template for local settings: active printer, Flashforge credentials
├── mise.toml / pyproject.toml / uv.lock
├── scripts/                # Mesh tools and printer helpers
├── projetos/               # One folder per part you work on (git-ignored here)
├── modelos/
│   ├── originais/          # Downloaded models (git-ignored here)
│   └── exportados/         # Temporary outputs (git-ignored)
├── perfis/<printer>/       # Exported slicer profiles
└── referencias/            # Reference images, drawings, measurements
```

Suggested structure for each project in `projetos/<name>/`:

| Folder | Contents |
|---|---|
| `original/` | The source file (download or customer file). Never edited. |
| `fontes/` | What generates the part: scripts, `.scad`, `.FCStd`, `.blend`, working 3MF. |
| `final/` | What goes to the slicer: print-ready 3MF, STLs, preview images. |
| `README.md` | What it is, dimensions, colors/filaments, how to print/assemble, short history. |

> This public repository ignores `projetos/` and `modelos/originais/`, so personal work and third-party downloads stay on your machine. To version them in a private copy, remove those lines from `.gitignore`.

**Keeping your projects in a private repo.** The author's setup keeps personal projects in a separate private repository cloned at `privado/` (also ignored), and makes `projetos/` and `modelos/originais/` Windows directory junctions pointing into it, so every path stays the same:

```powershell
git clone git@github.com:<you>/<your-private-repo>.git privado
New-Item -ItemType Junction -Path projetos -Target privado\projetos
New-Item -ItemType Junction -Path modelos\originais -Target privado\modelos\originais
```

Copy `.gitattributes` into the private repo so its 3D files also go through Git LFS, and commit there with `git -C privado ...`.

## Mesh tools

All tools read **STL, OBJ and 3MF** (including multi-object Bambu/Orca/Flash Studio projects) and write **3MF** with named objects, ready to open in any slicer.

### `info_malha.py`: inspect a mesh

Shows size, whether the mesh is watertight, number of bodies, volume, estimated PLA weight and whether it fits the active printer.

```bash
mise exec -- python scripts/info_malha.py part.3mf
mise exec -- python scripts/info_malha.py part.stl --escala 1.5            # check a scaled version
mise exec -- python scripts/info_malha.py part.stl --impressora bambu-a1   # check against another printer
```

```
== bracket
   tamanho (mm): 144.6 x 161.7 x 24.6
   faces: 2522  corpos: 1  fechada: True  normais consistentes: True
   volume: 165.1 cm³  peso maciço PLA: 205 g (com 15% infill e 2 paredes, tipicamente 25-40% disso)
   cabe na Bambu Lab A1 (256x256x256): sim
```

The fit check allows the part to be rotated, so it compares the sorted dimensions of the part with the sorted dimensions of the build volume.

### `reparar_malha.py`: repair a mesh

Merges duplicate vertices, removes duplicate and degenerate faces, fixes non-manifold edges and vertices, closes holes and re-orients normals (pymeshlab + trimesh).

```bash
mise exec -- python scripts/reparar_malha.py broken.stl fixed.3mf
```

### `cortar_com_pinos.py`: split a part with alignment pins

Cuts a model with an axis-aligned plane, drills matching holes in both halves and generates the dowel pins as separate objects (0.15 mm radial clearance, chamfered ends). The pins go at the points of the cross-section farthest from the edges. Use it for parts larger than your printer's build volume, or to print each half with the cut face on the bed.

```bash
# Cut at the middle of Z, 2 pins of 4 mm, holes 6 mm deep in each half
mise exec -- python scripts/cortar_com_pinos.py vase.stl vase_split.3mf --eixo z

# Cut at X = 80 mm from the model's minimum, 3 pins of 5 mm
mise exec -- python scripts/cortar_com_pinos.py sign.3mf sign_split.3mf --eixo x --pos 80 --pinos 3 --diam 5
```

| Option | Default | Meaning |
|---|---|---|
| `--eixo` | `z` | Cutting axis (`x`, `y` or `z`) |
| `--pos` | middle | Cut position in mm, measured from the model's minimum on that axis |
| `--pinos` | `2` | Number of pins |
| `--diam` | `4.0` | Pin diameter (mm) |
| `--prof` | `6.0` | Hole depth in each half (mm) |

### `resumo_3mf.py`: text summary for `git diff`

Prints the mesh summary of each object and, for slicer projects, every print setting as `key = value`. Git uses it as a `textconv` driver (see [below](#versioning-3d-files-with-git-lfs)), and you can also run it on its own:

```bash
mise exec -- python scripts/resumo_3mf.py project.3mf
```

### `estudio3d.py`: shared library

Import it from your own scripts (run from `scripts/` or add it to `sys.path`):

```python
from estudio3d import carregar, salvar_3mf, para_manifold, de_manifold, impressora

objs = carregar("model.3mf", juntar=False)        # [(name, trimesh.Trimesh), ...]
mesh = carregar("model.stl")                       # single merged mesh

m = para_manifold(mesh)                            # robust booleans with manifold3d
m = m - para_manifold(other_mesh)
result = de_manifold(m)                            # back to trimesh, near-duplicate vertices merged

salvar_3mf("out.3mf", [("Base", result), ("Lid", lid)])
print(impressora()["volume"])                      # e.g. [256, 256, 256]
```

| Function | Purpose |
|---|---|
| `carregar(path, juntar=True)` | Read STL/OBJ/3MF. Returns one merged mesh or a list of `(name, mesh)` |
| `salvar_3mf(path, objects)` | Write several named objects into one 3MF |
| `para_manifold(mesh)` / `de_manifold(x)` | Convert to and from `manifold3d` for reliable booleans |
| `limpar(mesh)` | Round vertices, merge duplicates, drop degenerate faces |
| `impressora(key=None)` | Active printer profile (dict with `nome`, `volume`, `bico_max`…) |
| `no_centro_da_mesa(mesh)` | Center on the active printer's bed and drop to Z = 0 |

**Mesh tips learned the hard way**

- Prefer manifold3d for booleans. trimesh and Blender booleans often leave non-manifold results.
- Don't use `Manifold.simplify()`: it tilts the walls of letters and fine details.
- Avoid cuts that are exactly coplanar with existing faces. They create zero-thickness "films" that slicers show as jagged artifacts. Offset the cut slightly (e.g. +0.002 mm) or rebuild from 2D outlines.
- Before shipping a part, run `info_malha.py`. Each part should be watertight with 1 body.

## Flashforge printer helper (LAN API)

`scripts/impressora_flashforge.py` uses [flashforge-python-api](https://pypi.org/project/flashforge-python-api/) to talk to Flashforge printers (AD5X, Adventurer 5M / 5M Pro) over the local network (ports 8898/8899). These printers run Flashforge's Klipper firmware without Moonraker, so the helper uses the LAN-mode API.

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
   mise exec -- python scripts/impressora_flashforge.py descobrir                # discover printers on the LAN
   mise exec -- python scripts/impressora_flashforge.py status                   # current state, temperatures, job
   mise exec -- python scripts/impressora_flashforge.py enviar part.gcode.3mf    # upload only
   mise exec -- python scripts/impressora_flashforge.py enviar part.gcode.3mf --imprimir --slot 2 --cor "#FF0000"
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
- With Claude Code, open the repo folder and approve the project MCP servers. `.claude/settings.json` already enables all four. `CLAUDE.md` tells the agent which tool to use for what, where the printer profiles are, and the design rules below. Edit its *Impressora do usuário* section to describe your own machine and slicer.

## Versioning 3D files with Git LFS

[`.gitattributes`](.gitattributes) sends 3D and image binaries (`.3mf`, `.stl`, `.obj`, `.step`, `.blend`, `.FCStd`, `.png`, `.jpg`…) through Git LFS. Text sources (`.scad`, `.py`, `.md`) stay in regular git.

**Readable diffs for meshes.** `.3mf` and `.stl` use a `malha3d` diff driver. Enable it once per clone:

```bash
git config diff.malha3d.textconv ".venv/Scripts/python.exe -X utf8 scripts/resumo_3mf.py"
```

(On Linux/macOS use `.venv/bin/python`.) After that, `git diff` and `git log -p` show changes in size, volume, weight and every slicer setting, e.g.:

```diff
-   tamanho (mm): 96.4 x 120.0 x 12.0
+   tamanho (mm): 96.4 x 120.0 x 14.0
-layer_height = 0.2
+layer_height = 0.16
```

**Conventions**

- A new version is a **new commit of the same file**. No `_v2`, `_final_final` or dates in file names.
- Tag a printed and approved version: `git tag <project>-v<n>`.
- To extract an old version of an LFS file: `git cat-file --filters <commit>:<path> > old.3mf` (`git show` returns only the LFS pointer).
- Not versioned: `.env`, `.venv`, G-code, `modelos/exportados/`, Blender/FreeCAD backups.

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

**Other printer-independent settings** live in the scripts: `DENSIDADE_PLA` in `scripts/estudio3d.py` and `FOLGA_FURO` (pin clearance) in `scripts/cortar_com_pinos.py`.

## License

[MIT](LICENSE)
