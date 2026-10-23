"""Split a model with a plane and add holes for alignment dowel pins (pins printed separately).

    python scripts/split_with_pins.py model.stl output.3mf --axis z --pos 80 [--pins 2] [--diam 4] [--depth 6]

- --pos is the cut coordinate in mm, measured from the model's minimum on that axis
  (without --pos, cuts in the middle).
- Both halves get holes; the pins come out as separate objects, already with PLA clearance.
- Pins are placed at the most "inner" points of the section (far from the edges).
"""
import argparse

import manifold3d as mf
import numpy as np
import trimesh

from bicofino import from_manifold, load, save_3mf, to_manifold

HOLE_CLEARANCE = 0.15  # mm on the radius: PLA pin fits snug, with glue
PIN_CHAMFER = 0.4  # mm


def inner_points(section: mf.CrossSection, n: int, diam: float) -> list[np.ndarray]:
    """Pick n points well inside the section, spread apart (sampling + distance to the edge)."""
    from shapely.geometry import Point, Polygon
    from shapely.ops import unary_union

    polys = []
    for contour in section.to_polygons():
        pg = Polygon(np.array(contour))
        if pg.is_valid and pg.area > 0:
            polys.append(pg)
    region = unary_union([p for p in polys if p.exterior.is_ccw]) if polys else None
    if region is None or region.is_empty:
        return []
    for hole in [p for p in polys if not p.exterior.is_ccw]:
        region = region.difference(hole)
    xmin, ymin, xmax, ymax = region.bounds
    g = np.mgrid[xmin:xmax:120j, ymin:ymax:120j].reshape(2, -1).T
    cand = [(Point(p).distance(region.exterior if region.geom_type == "Polygon" else region.boundary), p)
            for p in g if region.contains(Point(p))]
    cand = [(d, p) for d, p in cand if d >= diam * 1.2]
    chosen: list[np.ndarray] = []
    while cand and len(chosen) < n:
        if not chosen:
            d, p = max(cand, key=lambda t: t[0])
        else:
            d, p = max(cand, key=lambda t: min(np.linalg.norm(t[1] - q) for q in chosen) * min(t[0], diam * 3))
        chosen.append(p)
        cand = [(dd, pp) for dd, pp in cand if np.linalg.norm(pp - p) > diam * 2.5]
    return chosen


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("output")
    ap.add_argument("--axis", choices="xyz", default="z")
    ap.add_argument("--pos", type=float)
    ap.add_argument("--pins", type=int, default=2)
    ap.add_argument("--diam", type=float, default=4.0)
    ap.add_argument("--depth", type=float, default=6.0, help="hole depth in each half")
    a = ap.parse_args()

    m = load(a.input)
    # rotate so the cut axis becomes Z, cut, and undo the rotation at the end
    rot = {"z": np.eye(4),
           "x": trimesh.transformations.rotation_matrix(np.pi / 2, [0, 1, 0]),
           "y": trimesh.transformations.rotation_matrix(-np.pi / 2, [1, 0, 0])}[a.axis]
    m.apply_transform(rot)
    zmin, zmax = m.bounds[0, 2], m.bounds[1, 2]
    zc = zmin + (a.pos if a.pos is not None else (zmax - zmin) / 2)
    man = to_manifold(m)

    bottom, top = man.split_by_plane((0, 0, 1), zc)
    sec = man.slice(zc)
    pts = inner_points(sec, a.pins, a.diam)
    print(f"cut at {a.axis}={zc:.2f} mm, section area {sec.area():.0f} mm², pins: {len(pts)}")

    r_hole = a.diam / 2 + HOLE_CLEARANCE
    pins = []
    for p in pts:
        hole = mf.Manifold.cylinder(2 * a.depth + 0.4, r_hole, r_hole, 48, True).translate((p[0], p[1], zc))
        bottom -= hole
        top -= hole
        L = 2 * a.depth - 0.6  # a bit shorter than both holes together (room for glue)
        c = PIN_CHAMFER
        r = a.diam / 2
        pin = (mf.Manifold.cylinder(c, r - c, r, 48)
               + mf.Manifold.cylinder(L - 2 * c, r, r, 48).translate((0, 0, c))
               + mf.Manifold.cylinder(c, r, r - c, 48).translate((0, 0, L - c)))
        pins.append(pin)

    # both halves rest on their flat cut face: no supports on the gluing face
    parts = []
    for name, x, flip in (("Part A", bottom, True), ("Part B", top, False)):
        t = from_manifold(x)
        if flip:
            t.apply_transform(trimesh.transformations.rotation_matrix(np.pi, [1, 0, 0]))
        parts.append((name, t))
    for i, p in enumerate(pins, 1):
        parts.append((f"Pin {i}", from_manifold(p)))

    # lay them out side by side on the bed
    x = 0.0
    out = []
    for name, t in parts:
        t.apply_translation([x - t.bounds[0, 0], -t.bounds[0, 1], -t.bounds[0, 2]])
        x = t.bounds[1, 0] + 8
        print(f"  {name}: {np.round(t.extents, 1)} mm, watertight={t.is_watertight}")
        out.append((name, t))
    save_3mf(a.output, out, title="split with pins")
    print(f"saved to {a.output}")


if __name__ == "__main__":
    main()
