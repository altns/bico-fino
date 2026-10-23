"""Repara malhas com problemas comuns (buracos, normais invertidas, faces duplicadas/degeneradas).

    python scripts/reparar_malha.py entrada.stl saida.3mf
"""
import argparse

import pymeshlab
import trimesh

from estudio3d import carregar, limpar, salvar_3mf


def reparar(m: trimesh.Trimesh) -> trimesh.Trimesh:
    m = limpar(m)
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
    p.add_argument("entrada")
    p.add_argument("saida")
    a = p.parse_args()
    objs = []
    for nome, m in carregar(a.entrada, juntar=False):
        r = reparar(m)
        print(f"{nome}: fechada antes={m.is_watertight} depois={r.is_watertight}")
        objs.append((nome, r))
    if a.saida.lower().endswith(".3mf"):
        salvar_3mf(a.saida, objs)
    else:
        trimesh.util.concatenate([m for _, m in objs]).export(a.saida)


if __name__ == "__main__":
    main()
