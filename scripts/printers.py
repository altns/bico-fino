"""List the printer profiles in printers.toml and show which one is active.

    python scripts/printers.py

To switch: PRINTER=<key> in .env (or --printer <key> in the scripts).
"""
from bicofino import printer, printers


def main():
    _, profiles = printers()
    active = printer()["key"]
    for key, p in profiles.items():
        x, y, z = p["build_volume"]
        extras = [f"{p['filament_slots']} filaments" if p.get("filament_slots", 1) > 1 else "",
                  "enclosed" if p.get("enclosed") else ""]
        mark = "*" if key == active else " "
        print(f"{mark} {key:<16} {p['name']:<26} {x}x{y}x{z} mm  "
              f"nozzle up to {p['max_nozzle_temp']} °C, bed up to {p['max_bed_temp']} °C  "
              f"{' '.join(e for e in extras if e)}")
    print("\n* = active (PRINTER in .env or 'default' in printers.toml)")


if __name__ == "__main__":
    main()
