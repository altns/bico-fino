"""bico-fino shared library: reading/writing meshes (3MF/STL/OBJ), conversions and printer profiles.

Typical use in the other scripts:
    from bicofino import load, save_3mf, to_manifold, from_manifold, printer
"""
from __future__ import annotations

import os
import re
import tomllib
import zipfile
from pathlib import Path

import numpy as np
import trimesh

# PLA density (g/cm³) used for weight estimates
PLA_DENSITY = 1.24

ROOT = Path(__file__).resolve().parent.parent
PRINTERS_FILE = ROOT / "printers.toml"

_NS_CORE = "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"


def _matrix_3mf(text: str | None) -> np.ndarray:
    m = np.eye(4)
    if text:
        v = [float(x) for x in text.split()]
        m[:3, :3] = np.array(v[:9]).reshape(3, 3).T
        m[:3, 3] = v[9:12]
    return m


def _read_3mf(path: Path) -> list[tuple[str, trimesh.Trimesh]]:
    """Read a 3MF (including Bambu/Orca projects whose components live in separate files).

    Returns one (name, mesh) per build item, with its transform already applied.
    """
    from lxml import etree

    z = zipfile.ZipFile(path)
    docs = {"/" + n: etree.fromstring(z.read(n)) for n in z.namelist() if n.lower().endswith(".model")}
    root = next(k for k in docs if k.lower() == "/3d/3dmodel.model")

    def tag(t):
        return f"{{{_NS_CORE}}}{t}"

    objects = {}
    for file, doc in docs.items():
        for ob in doc.iter(tag("object")):
            objects[(file, ob.get("id"))] = ob

    def object_meshes(file, oid, tf):
        ob = objects[(file, oid)]
        parts = []
        mesh = ob.find(tag("mesh"))
        if mesh is not None:
            v = np.array([[float(e.get(k)) for k in "xyz"] for e in mesh.iter(tag("vertex"))])
            f = np.array([[int(e.get(k)) for k in ("v1", "v2", "v3")] for e in mesh.iter(tag("triangle"))])
            m = trimesh.Trimesh(v, f, process=True)
            m.apply_transform(tf)
            parts.append(m)
        comps = ob.find(tag("components"))
        if comps is not None:
            for c in comps.findall(tag("component")):
                comp_path = None
                for k, val in c.attrib.items():
                    if k.endswith("}path"):
                        comp_path = val
                parts += object_meshes(comp_path or file, c.get("objectid"), tf @ _matrix_3mf(c.get("transform")))
        return parts

    out = []
    for i, item in enumerate(docs[root].iter(tag("item"))):
        oid = item.get("objectid")
        parts = object_meshes(root, oid, _matrix_3mf(item.get("transform")))
        name = objects[(root, oid)].get("name") or f"object_{i + 1}"
        out.append((name, trimesh.util.concatenate(parts)))
    return out


def load(path: str | Path, merge: bool = True):
    """Load STL/OBJ/3MF. With merge=True returns a single mesh; otherwise a list of (name, mesh)."""
    path = Path(path)
    if path.suffix.lower() == ".3mf":
        items = _read_3mf(path)
    else:
        m = trimesh.load(path, force="mesh")
        items = [(path.stem, m)]
    if merge:
        return trimesh.util.concatenate([m for _, m in items])
    return items


def save_3mf(dest: str | Path, objects: list[tuple[str, trimesh.Trimesh]], title: str = "") -> None:
    """Write a simple 3MF with several named objects (opens in Bambu Studio, OrcaSlicer, Flash Studio...)."""
    objs, items = [], []
    for i, (name, m) in enumerate(objects, 1):
        v = "".join(f'<vertex x="{a:.5f}" y="{b:.5f}" z="{c:.5f}"/>' for a, b, c in m.vertices)
        t = "".join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in m.faces)
        name_xml = name.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;")
        objs.append(f'<object id="{i}" name="{name_xml}" type="model"><mesh><vertices>{v}</vertices>'
                    f"<triangles>{t}</triangles></mesh></object>")
        items.append(f'<item objectid="{i}"/>')
    model = ('<?xml version="1.0" encoding="UTF-8"?>\n'
             f'<model unit="millimeter" xml:lang="en-US" xmlns="{_NS_CORE}">'
             f'<metadata name="Title">{title}</metadata>'
             f'<resources>{"".join(objs)}</resources><build>{"".join(items)}</build></model>')
    types = ('<?xml version="1.0" encoding="UTF-8"?>\n'
             '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
             '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
             '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
    rels = ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Target="/3D/3dmodel.model" Id="rel0" '
            'Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", types)
        zf.writestr("_rels/.rels", rels)
        zf.writestr("3D/3dmodel.model", model)


def to_manifold(m: trimesh.Trimesh):
    import manifold3d as mf

    m = m.copy()
    m.merge_vertices()
    return mf.Manifold(mf.Mesh(vert_properties=m.vertices.astype(np.float32),
                               tri_verts=m.faces.astype(np.uint32)))


def from_manifold(x) -> trimesh.Trimesh:
    """Convert back and merge nearly coincident vertices (avoids zero-thickness 'films' and open edges)."""
    g = x.to_mesh()
    v = np.array(g.vert_properties)[:, :3]
    f = np.array(g.tri_verts)
    return clean(trimesh.Trimesh(v, f, process=False))


def clean(m: trimesh.Trimesh, decimals: int = 4) -> trimesh.Trimesh:
    """Merge vertices at 10^-decimals mm, drop degenerate faces and pairs of duplicate faces."""
    v, inv = np.unique(m.vertices.round(decimals), axis=0, return_inverse=True)
    f = inv.reshape(-1)[m.faces]
    f = f[(f[:, 0] != f[:, 1]) & (f[:, 1] != f[:, 2]) & (f[:, 0] != f[:, 2])]
    key = np.sort(f, axis=1)
    _, idx, count = np.unique(key, axis=0, return_inverse=True, return_counts=True)
    f = f[count[idx.reshape(-1)] == 1]
    r = trimesh.Trimesh(v, f, process=False)
    r.remove_unreferenced_vertices()
    return r


def printers() -> tuple[str, dict[str, dict]]:
    """Read printers.toml: returns (default key, {key: profile})."""
    with open(PRINTERS_FILE, "rb") as f:
        cfg = tomllib.load(f)
    return cfg.get("default", ""), cfg["printers"]


def printer(key: str | None = None) -> dict:
    """Printer profile: the requested key, else PRINTER from the environment/.env, else the toml default."""
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
    default, profiles = printers()
    key = key or os.getenv("PRINTER") or default
    if key not in profiles:
        raise SystemExit(f"Printer '{key}' is not in {PRINTERS_FILE.name}. "
                         f"Options: {', '.join(profiles)}")
    return {"key": key, **profiles[key]}


def center_on_bed(m: trimesh.Trimesh, bed: tuple[float, float] | None = None) -> trimesh.Trimesh:
    """Center in XY on the bed (by default the active printer's) and rest it on Z=0."""
    if bed is None:
        bed = printer()["build_volume"][:2]
    m = m.copy()
    c = (m.bounds[0] + m.bounds[1]) / 2
    m.apply_translation([bed[0] / 2 - c[0], bed[1] / 2 - c[1], -m.bounds[0, 2]])
    return m


def safe_name(s: str) -> str:
    return re.sub(r"[^\w\-. ]", "_", s).strip() or "object"
