"""Corta um modelo por um plano e adiciona furos para pinos-guia de colagem (pinos impressos à parte).

    python scripts/cortar_com_pinos.py modelo.stl saida.3mf --eixo z --pos 80 [--pinos 2] [--diam 4] [--prof 6]

- --pos é a coordenada do corte em mm, medida a partir do mínimo do modelo naquele eixo
  (sem --pos, corta no meio).
- Os furos ficam nas duas metades; os pinos saem como objetos separados, já com folga para PLA.
- Os pinos são posicionados nos pontos mais "internos" da seção (longe das bordas).
"""
import argparse

import manifold3d as mf
import numpy as np
import trimesh

from estudio3d import carregar, de_manifold, para_manifold, salvar_3mf

FOLGA_FURO = 0.15  # mm no raio: pino de PLA entra justo, com cola
CHANFRO_PINO = 0.4  # mm


def pontos_internos(secao: mf.CrossSection, n: int, diam: float) -> list[np.ndarray]:
    """Escolhe n pontos bem dentro da seção, espalhados (amostragem + distância à borda)."""
    from shapely.geometry import Point, Polygon
    from shapely.ops import unary_union

    polys = []
    for contorno in secao.to_polygons():
        pg = Polygon(np.array(contorno))
        if pg.is_valid and pg.area > 0:
            polys.append(pg)
    regiao = unary_union([p for p in polys if p.exterior.is_ccw]) if polys else None
    if regiao is None or regiao.is_empty:
        return []
    for buraco in [p for p in polys if not p.exterior.is_ccw]:
        regiao = regiao.difference(buraco)
    xmin, ymin, xmax, ymax = regiao.bounds
    g = np.mgrid[xmin:xmax:120j, ymin:ymax:120j].reshape(2, -1).T
    cand = [(Point(p).distance(regiao.exterior if regiao.geom_type == "Polygon" else regiao.boundary), p)
            for p in g if regiao.contains(Point(p))]
    cand = [(d, p) for d, p in cand if d >= diam * 1.2]
    escolhidos: list[np.ndarray] = []
    while cand and len(escolhidos) < n:
        if not escolhidos:
            d, p = max(cand, key=lambda t: t[0])
        else:
            d, p = max(cand, key=lambda t: min(np.linalg.norm(t[1] - q) for q in escolhidos) * min(t[0], diam * 3))
        escolhidos.append(p)
        cand = [(dd, pp) for dd, pp in cand if np.linalg.norm(pp - p) > diam * 2.5]
    return escolhidos


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("entrada")
    ap.add_argument("saida")
    ap.add_argument("--eixo", choices="xyz", default="z")
    ap.add_argument("--pos", type=float)
    ap.add_argument("--pinos", type=int, default=2)
    ap.add_argument("--diam", type=float, default=4.0)
    ap.add_argument("--prof", type=float, default=6.0, help="profundidade do furo em cada metade")
    a = ap.parse_args()

    m = carregar(a.entrada)
    # gira para que o eixo do corte vire Z, corta, e desfaz a rotação no fim
    rot = {"z": np.eye(4),
           "x": trimesh.transformations.rotation_matrix(np.pi / 2, [0, 1, 0]),
           "y": trimesh.transformations.rotation_matrix(-np.pi / 2, [1, 0, 0])}[a.eixo]
    m.apply_transform(rot)
    zmin, zmax = m.bounds[0, 2], m.bounds[1, 2]
    zc = zmin + (a.pos if a.pos is not None else (zmax - zmin) / 2)
    man = para_manifold(m)

    baixo, cima = man.split_by_plane((0, 0, 1), zc)
    sec = man.slice(zc)
    pts = pontos_internos(sec, a.pinos, a.diam)
    print(f"corte em {a.eixo}={zc:.2f} mm, área da seção {sec.area():.0f} mm², pinos: {len(pts)}")

    r_furo = a.diam / 2 + FOLGA_FURO
    pinos = []
    for p in pts:
        furo = mf.Manifold.cylinder(2 * a.prof + 0.4, r_furo, r_furo, 48, True).translate((p[0], p[1], zc))
        baixo -= furo
        cima -= furo
        L = 2 * a.prof - 0.6  # um pouco mais curto que os dois furos somados (sobra para cola)
        c = CHANFRO_PINO
        r = a.diam / 2
        pino = (mf.Manifold.cylinder(c, r - c, r, 48)
                + mf.Manifold.cylinder(L - 2 * c, r, r, 48).translate((0, 0, c))
                + mf.Manifold.cylinder(c, r, r - c, 48).translate((0, 0, L - c)))
        pinos.append(pino)

    # as duas metades saem com a face de corte (plana) apoiada na mesa: sem suporte na face de colagem
    pecas = []
    for nome, x, virar in (("Parte A", baixo, True), ("Parte B", cima, False)):
        t = de_manifold(x)
        if virar:
            t.apply_transform(trimesh.transformations.rotation_matrix(np.pi, [1, 0, 0]))
        pecas.append((nome, t))
    for i, p in enumerate(pinos, 1):
        pecas.append((f"Pino {i}", de_manifold(p)))

    # arruma na mesa lado a lado
    x = 0.0
    saida = []
    for nome, t in pecas:
        t.apply_translation([x - t.bounds[0, 0], -t.bounds[0, 1], -t.bounds[0, 2]])
        x = t.bounds[1, 0] + 8
        print(f"  {nome}: {np.round(t.extents, 1)} mm, fechada={t.is_watertight}")
        saida.append((nome, t))
    salvar_3mf(a.saida, saida, titulo="corte com pinos")
    print(f"salvo em {a.saida}")


if __name__ == "__main__":
    main()
