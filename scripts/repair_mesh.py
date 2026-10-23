"""Repair meshes with common problems (holes, flipped normals, duplicate/degenerate faces).

    python scripts/repair_mesh.py input.stl output.3mf
"""
import argparse

import pymeshlab
import trimesh

from bicofino import clean, load, save_3mf


def repair(m: trimesh.Trimesh) -> trimesh.Trimesh:
    m = clean(m)
    if m.is_watertight:
        trimesh.repair.fix_normals(m)
        return m
    ms = pymeshlab.MeshSet()
    ms.add_mesh(pymeshlab.Mesh(m.vertices, m.faces))
    ms.meshing_remove_duplicate_vertices()
    ms.meshing_remove_duplicate_faces()
    ms.meshing_remove_null_faces()
    ms.meshing_repair_non_manifold_edges()
    ms.meshing_repair_non_manifold_vertices()
    ms.meshing_close_holes(maxholesize=1000)
    ms.meshing_re_orient_faces_coherently()
    r = ms.current_mesh()
    out = trimesh.Trimesh(r.vertex_matrix(), r.face_matrix(), process=True)
    trimesh.repair.fix_normals(out)
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument("input")
    p.add_argument("output")
    a = p.parse_args()
    objs = []
    for name, m in load(a.input, merge=False):
        r = repair(m)
        print(f"{name}: watertight before={m.is_watertight} after={r.is_watertight}")
        objs.append((name, r))
    if a.output.lower().endswith(".3mf"):
        save_3mf(a.output, objs)
    else:
        trimesh.util.concatenate([m for _, m in objs]).export(a.output)


if __name__ == "__main__":
    main()
