"""Comunicação com impressoras Flashforge (AD5X, Adventurer 5M/5M Pro) pela rede local (biblioteca flashforge-python-api).

Configuração: copie .env.exemplo para .env e preencha IP, número de série e check code
(o check code aparece na tela da impressora em Configurações > Rede / modo LAN).

    python scripts/impressora_flashforge.py descobrir
    python scripts/impressora_flashforge.py status
    python scripts/impressora_flashforge.py enviar arquivo.gcode.3mf            # só envia
    python scripts/impressora_flashforge.py enviar arquivo.gcode.3mf --imprimir # envia e inicia (slot 1)

O arquivo enviado precisa estar FATIADO (gcode ou .gcode.3mf exportado pelo Flash Studio/OrcaSlicer).
"""
import argparse
import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv
from flashforge import (AD5XMaterialMapping, AD5XUploadParams, FlashForgeClient, PrinterDiscovery)

load_dotenv(Path(__file__).resolve().parent.parent / ".env")


def _cliente() -> FlashForgeClient:
    faltando = [k for k in ("FLASHFORGE_IP", "FLASHFORGE_SERIAL", "FLASHFORGE_CHECK_CODE") if not os.getenv(k)]
    if faltando:
        raise SystemExit(f"Preencha no .env: {', '.join(faltando)}")
    return FlashForgeClient(os.environ["FLASHFORGE_IP"], os.environ["FLASHFORGE_SERIAL"],
                            os.environ["FLASHFORGE_CHECK_CODE"])


async def descobrir():
    achadas = await PrinterDiscovery().discover()
    if not achadas:
        print("Nenhuma impressora encontrada (mesma rede? modo LAN ligado?)")
    for p in achadas:
        print(f"{p.name}  modelo={p.model}  ip={p.ip_address}  serie={p.serial_number}")


async def status():
    c = _cliente()
    try:
        if not await c.initialize():
            raise SystemExit("Falha ao conectar (confira IP, série e check code)")
        info = await c.get_printer_status()
        campos = {k: v for k, v in vars(info).items() if not k.startswith("_")} if info else {}
        for k in sorted(campos):
            print(f"{k}: {campos[k]}")
    finally:
        await c.dispose()


async def enviar(arquivo: str, imprimir: bool, slot: int, cor: str):
    c = _cliente()
    try:
        if not await c.initialize():
            raise SystemExit("Falha ao conectar")
        params = AD5XUploadParams(
            file_path=str(Path(arquivo).resolve()),
            start_print=imprimir,
            leveling_before_print=True,
            flow_calibration=False,
            first_layer_inspection=False,
            time_lapse_video=False,
            material_mappings=[AD5XMaterialMapping(tool_id=0, slot_id=slot, material_name="PLA",
                                                   tool_material_color=cor, slot_material_color=cor)],
        )
        ok = await c.job_control.upload_file_ad5x(params)
        print("enviado" + (" e impressão iniciada" if imprimir else "") if ok else "falha no envio")
    finally:
        await c.dispose()


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("descobrir")
    sub.add_parser("status")
    e = sub.add_parser("enviar")
    e.add_argument("arquivo")
    e.add_argument("--imprimir", action="store_true", help="inicia a impressão logo após enviar")
    e.add_argument("--slot", type=int, default=1, help="slot do IFS (1-4)")
    e.add_argument("--cor", default="#FFFFFF")
    a = ap.parse_args()
    if a.cmd == "descobrir":
        asyncio.run(descobrir())
    elif a.cmd == "status":
        asyncio.run(status())
    else:
        asyncio.run(enviar(a.arquivo, a.imprimir, a.slot, a.cor))


if __name__ == "__main__":
    main()
