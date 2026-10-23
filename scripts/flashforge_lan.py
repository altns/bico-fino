"""Talk to Flashforge printers (AD5X, Adventurer 5M/5M Pro) over the local network (flashforge-python-api).

Setup: copy .env.example to .env and fill in the IP, serial number and check code
(the check code is shown on the printer screen under Settings > Network / LAN mode).

    python scripts/flashforge_lan.py discover
    python scripts/flashforge_lan.py status
    python scripts/flashforge_lan.py upload file.gcode.3mf            # upload only
    python scripts/flashforge_lan.py upload file.gcode.3mf --print    # upload and start (slot 1)

The uploaded file must be SLICED (gcode or .gcode.3mf exported by Flash Studio/OrcaSlicer).
"""
import argparse
import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv
from flashforge import (AD5XMaterialMapping, AD5XUploadParams, FlashForgeClient, PrinterDiscovery)

load_dotenv(Path(__file__).resolve().parent.parent / ".env")


def _client() -> FlashForgeClient:
    missing = [k for k in ("FLASHFORGE_IP", "FLASHFORGE_SERIAL", "FLASHFORGE_CHECK_CODE") if not os.getenv(k)]
    if missing:
        raise SystemExit(f"Fill in .env: {', '.join(missing)}")
    return FlashForgeClient(os.environ["FLASHFORGE_IP"], os.environ["FLASHFORGE_SERIAL"],
                            os.environ["FLASHFORGE_CHECK_CODE"])


async def discover():
    found = await PrinterDiscovery().discover()
    if not found:
        print("No printer found (same network? LAN mode on?)")
    for p in found:
        print(f"{p.name}  model={p.model}  ip={p.ip_address}  serial={p.serial_number}")


async def status():
    c = _client()
    try:
        if not await c.initialize():
            raise SystemExit("Could not connect (check IP, serial and check code)")
        info = await c.get_printer_status()
        fields = {k: v for k, v in vars(info).items() if not k.startswith("_")} if info else {}
        for k in sorted(fields):
            print(f"{k}: {fields[k]}")
    finally:
        await c.dispose()


async def upload(file: str, start: bool, slot: int, color: str):
    c = _client()
    try:
        if not await c.initialize():
            raise SystemExit("Could not connect")
        params = AD5XUploadParams(
            file_path=str(Path(file).resolve()),
            start_print=start,
            leveling_before_print=True,
            flow_calibration=False,
            first_layer_inspection=False,
            time_lapse_video=False,
            material_mappings=[AD5XMaterialMapping(tool_id=0, slot_id=slot, material_name="PLA",
                                                   tool_material_color=color, slot_material_color=color)],
        )
        ok = await c.job_control.upload_file_ad5x(params)
        print("uploaded" + (" and print started" if start else "") if ok else "upload failed")
    finally:
        await c.dispose()


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("discover")
    sub.add_parser("status")
    u = sub.add_parser("upload")
    u.add_argument("file")
    u.add_argument("--print", dest="start", action="store_true", help="start printing right after uploading")
    u.add_argument("--slot", type=int, default=1, help="IFS slot (1-4)")
    u.add_argument("--color", default="#FFFFFF")
    a = ap.parse_args()
    if a.cmd == "discover":
        asyncio.run(discover())
    elif a.cmd == "status":
        asyncio.run(status())
    else:
        asyncio.run(upload(a.file, a.start, a.slot, a.color))


if __name__ == "__main__":
    main()
