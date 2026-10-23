"""Resumo textual de um 3MF/STL para o `git diff` (driver malha3d).

Mostra a malha de cada objeto (via info_malha) e, em projetos Bambu/Orca/Flash Studio,
as configurações de impressão como "chave = valor", para o diff apontar exatamente o que mudou.

    python scripts/resumo_3mf.py arquivo.3mf
"""
import json
import subprocess
import sys
import zipfile
from pathlib import Path


def configuracoes(caminho: str) -> list[str]:
    linhas = []
    try:
        z = zipfile.ZipFile(caminho)
    except zipfile.BadZipFile:
        return linhas
    for nome in sorted(z.namelist()):
        if nome.endswith("project_settings.config"):
            try:
                cfg = json.loads(z.read(nome))
            except ValueError:
                continue
            linhas.append(f"[{nome}]")
            for k in sorted(cfg):
                v = cfg[k]
                v = ", ".join(map(str, v)) if isinstance(v, list) else str(v)
                linhas.append(f"{k} = {v.replace(chr(10), ' | ')}")
        elif nome.endswith((".config", ".json")) and not nome.endswith("project_settings.config"):
            linhas.append(f"[{nome}] {len(z.read(nome))} bytes")
    return linhas


def main():
    arq = sys.argv[1]
    info = Path(__file__).with_name("info_malha.py")
    r = subprocess.run([sys.executable, "-X", "utf8", str(info), arq], capture_output=True, text=True, encoding="utf-8")
    print(r.stdout, end="")
    if arq.lower().endswith(".3mf"):
        print("\n".join(configuracoes(arq)))


if __name__ == "__main__":
    main()
