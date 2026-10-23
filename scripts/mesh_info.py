"""Quick mesh report: dimensions, watertightness, bodies, volume and estimated PLA weight.

    python scripts/mesh_info.py model.3mf [--scale 1.0] [--printer bambu-a1]

Without --printer, uses the active one (PRINTER in .env or the default in printers.toml).
"""
import argparse

from bicofino import PLA_DENSITY, load, printer


def main():
    p = argparse.ArgumentParser()
    p.add_argument("file")
    p.add_argument("--scale", type=float, default=1.0)
    p.add_argument("--printer", help="key in printers.toml (e.g. ad5x, bambu-a1, k2-pro)")
    a = p.parse_args()
    prn = printer(a.printer)
    vol = prn["build_volume"]
    for name, m in load(a.file, merge=False):
        if a.scale != 1.0:
            m.apply_scale(a.scale)
        e = m.extents
        bodies = m.split(only_watertight=False)
        print(f"== {name}")
        print(f"   size (mm): {e[0]:.1f} x {e[1]:.1f} x {e[2]:.1f}")
        print(f"   faces: {len(m.faces)}  bodies: {len(bodies)}  watertight: {m.is_watertight}  "
              f"consistent normals: {m.is_winding_consistent}")
        if m.is_watertight:
            cm3 = abs(m.volume) / 1000
            print(f"   volume: {cm3:.1f} cm³  solid PLA weight: {cm3 * PLA_DENSITY:.0f} g "
                  f"(with 15% infill and 2 walls, typically 25-40% of that)")
        fits = all(x <= y for x, y in zip(sorted(e), sorted(vol)))
        print(f"   fits {prn['name']} ({vol[0]}x{vol[1]}x{vol[2]}): "
              f"{'yes' if fits else 'NO - split it with split_with_pins.py'}")


if __name__ == "__main__":
    main()
