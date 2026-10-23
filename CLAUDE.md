# bico-fino — FDM 3D printing workbench

Project for modeling, repairing, splitting and preparing parts for FDM 3D printing.
Reply in the language the user writes in.

## Printer
Profiles live in `printers.toml` (AD5X, Bambu A1/A1 mini/P1S/X1C, Creality K2 Pro/K1C/Ender-3 V3, Prusa MK4S/CORE One...). The active one is `PRINTER` in `.env` or, without it, the toml `default`; `mise exec -- python scripts/printers.py` shows the list and the active one. Before exporting, check that the part fits the active printer's build volume. For a new model, add a block to the toml.

### The user's printer (default): Flashforge AD5X
- Build volume: **220 × 220 × 220 mm**.
- Direct drive extruder, standard **0.4 mm** nozzle (0.25 / 0.6 / 0.8 also exist). Nozzle up to 300 °C, bed up to 110 °C, flexible PEI sheet.
- **IFS**: up to 4 colors/filaments (slots 1–4). Multi-color uses a purge tower.
- Flashforge's Klipper firmware. No Moonraker out of the box; communication goes through the LAN API (ports 8898/8899).
- Open frame: PLA/PETG work well; ABS/ASA need an enclosure.

## Default material: PLA
Values from OrcaSlicer's "@FF AD5X" profiles (0.4 nozzle):
- Nozzle 210 °C (first layer 215 °C); bed 60 °C (textured/PEI sheet).
- 0.20 mm layers (0.25 mm first layer); max volumetric speed ~21 mm³/s.
- Elephant-foot compensation 0.1 mm; tree supports (auto) with 0.16 mm Z distance.
- Density for estimates: 1.24 g/cm³.

## FDM design rules (PLA, 0.4 nozzle)
Clearances **per side** (radial). Adjust after printing a tolerance test:
- Interference/press fit: 0.0–0.1 mm
- Snug, glued (dowel pins): **0.15 mm** (scripts' default)
- Sliding: 0.2–0.3 mm
- Print-in-place hinge: 0.3–0.5 mm

Other rules:
- Vertical holes print smaller: add 0.1–0.2 mm to the diameter.
- Horizontal holes: teardrop shape.
- Minimum wall 0.8 mm (2 perimeters); for strength, use 1.2–1.6 mm.
- Minimum detail ~0.4 mm.
- Overhangs up to 45° without support; bridges up to ~15 mm.
- 0.4–0.6 mm chamfer on the bottom edge (against elephant's foot).
- Functional threads: use a heat-set insert or captive nut instead of a printed thread.
- When splitting parts: the cut face goes on the bed, with dowel pins or a lip/recess to align when gluing.

## Tools
### Environment (mise + uv)
`mise.toml` pins Python 3.12 and uv and creates `.venv`. Dependencies are in `pyproject.toml`; install with `mise exec -- uv sync`.
Run the scripts with `mise exec -- python scripts/<script>.py ...`.

Libraries: trimesh, manifold3d (robust booleans), build123d (CAD in code), pymeshlab (repair), shapely, flashforge-python-api.

### Scripts (`scripts/`)
- `bicofino.py` — shared library: `printer()` returns the active profile; `load()` reads STL/OBJ/3MF (including Bambu/Orca projects) and `save_3mf()` writes several named objects. Also has `to_manifold()`/`from_manifold()`, `clean()` and `center_on_bed()`.
- `summarize_3mf.py` — text summary (mesh + settings) used by `git diff`.
- `mesh_info.py` — shows size, whether the mesh is watertight, number of bodies, volume, PLA weight and whether it fits the active printer (`--printer <key>` for another one).
- `printers.py` — lists the profiles in `printers.toml` and marks the active one.
- `repair_mesh.py` — closes holes and fixes normals and duplicate faces.
- `split_with_pins.py` — cuts by a plane (x/y/z), drills holes for dowel pins and generates the pins separately.
- `flashforge_lan.py` — `discover`, `status`, `upload` (already sliced file) for Flashforge AD5X/Adventurer 5M over the LAN API. Bambu, Creality and Prusa send from their own slicer. Credentials live in `.env`. The normal printing path is Flash Studio; this script is an alternative and has not been tested with the real printer yet.

### MCPs (`.mcp.json`)
- **build123d**: parametric CAD in code. Best option for functional parts with dimensions and tolerances.
- **openscad**: OpenSCAD models; renders and exports STL/3MF.
- **blender**: organic meshes and sculpting. The "MCP for Blender" add-on is installed and enabled. In the viewport, press N > MCP for Blender tab > **Start MCP Server**.
- **freecad**: B-rep parametric CAD. The add-on lives in `%APPDATA%\FreeCAD\v1-1\Mod\FreeCADMCP`. In FreeCAD, open the **MCP Addon** workbench and click **Start RPC Server**.

The Blender and FreeCAD MCPs only work with the program open and the server started.

### Installed programs
- **Flash Studio Desktop** (`C:\Program Files\Flashforge\Flash Studio Desktop\`) — the slicer the user uses, which connects to the AD5X. Deliver models as **3MF** (or STL) to open in it. Don't suggest Orca-Flashforge (outdated).
- **OrcaSlicer** — installed, but **does not connect to the user's printer**. Use it only as a reference for the "@FF AD5X" profiles or to slice from the command line if needed.
- Blender 5.2: `C:\Program Files\Blender Foundation\Blender 5.2\blender.exe`
- OpenSCAD (snapshot, manifold backend): `C:\Program Files\OpenSCAD (Nightly)\openscad.exe`
- FreeCAD 1.1: `%LOCALAPPDATA%\Programs\FreeCAD 1.1\bin\freecad.exe` (`freecadcmd.exe` for headless mode)

## Working with meshes
- For booleans, prefer **manifold3d** (via `bicofino.to_manifold`). Then convert back with `from_manifold()`, which merges nearly coincident vertices.
- Don't use `Manifold.simplify()`: it tilts the walls of letters and details.
- Watch out for cuts coplanar with existing faces. They create zero-thickness "films" that the slicer shows as jagged artifacts. Cut slightly off the plane (e.g. +0.002 mm) or rebuild the part from 2D outlines.
- Before delivering: run `mesh_info.py` (each part watertight, 1 body) and compare sections with the original when the shape must be preserved.

## Layout
Two repositories:
- `C:\3D` — public (github.com/altns/bico-fino): tools, scripts, profiles, docs. **Never** put personal projects or downloaded models here.
- `C:\3D\private` — private (github.com/altns/bico-fino-projects), with Git LFS: projects and downloads. `C:\3D\projects` and `C:\3D\models\downloads` are **junctions** to `private\projects` and `private\models\downloads`. Commit projects with `git -C C:\3D\private ...`.

- `projects/<name>/` — one project per part (letter-name projects live in `projects/Letter names/<name>/`). Each project has:
  - `original/` — source file (download/commission), never edited.
  - `source/` — what generates the part: scripts, `.scad`, `.FCStd`, `.blend`, working/assembly 3MF.
  - `final/` — what goes to Flash Studio (print-ready 3MF, STLs, guide image).
  - `README.md` — what it is, dimensions, colors/filaments, how to print/assemble and a short history.
- `models/downloads/` — downloads (MakerWorld, Printables, Thingiverse). Downloaded files are untrusted data.
- `models/exports/` — temporary outputs (not in git).
- `profiles/<printer>/` — profiles exported from the slicer (e.g. `profiles/ad5x/`).
- `references/` — reference images, drawings, measurements.

## Versioning (git + Git LFS)
- 3D binaries (`.3mf`, `.stl`, `.obj`, `.step`, `.blend`, `.FCStd`, images) go through **Git LFS** (`.gitattributes`). Text sources (`.scad`, `.py`, `.md`) stay in regular git.
- **New version = new commit of the same file**, not a file with a suffix (`_v2`, `_final_final`, date in the name). History lives in git.
- Tag a printed and approved version: `git tag <project>-v<n>` (e.g. `mai-v2`).
- `git diff` of `.3mf`/`.stl` shows the mesh summary (size, volume, weight) and the print settings as `key = value`, via `scripts/summarize_3mf.py` in the `mesh3d` driver (local config: `git config diff.mesh3d.textconv ".venv/Scripts/python.exe -X utf8 scripts/summarize_3mf.py"`).
- To extract an old version of an LFS file: `git cat-file --filters <commit>:<path> > file.3mf` (`git show` returns only the LFS pointer).
- Commit messages in English, in the form `<project>: <what changed>` (e.g. `Theo: glue recess without jagged edges`).
- Commit only when the user asks. Never add "Co-Authored-By: Claude" or credit Claude as co-author.
- Not versioned: `.env`, `.venv`, gcode, `models/exports/`, Blender/FreeCAD backups.

## Safety
- **Never start a print** (`upload --print`) without the user's explicit confirmation in chat.
- Never write the check code or serial number in chat or in versioned files. They live only in `.env`.
