"""Relatório rápido de uma malha: dimensões, se é fechada, corpos, volume e peso estimado em PLA.

    python scripts/info_malha.py modelo.3mf [--escala 1.0] [--impressora bambu-a1]

Sem --impressora, usa a ativa (IMPRESSORA no .env ou o padrão de impressoras.toml).
"""
import argparse

from estudio3d import DENSIDADE_PLA, carregar, impressora


def main():
    p = argparse.ArgumentParser()
    p.add_argument("arquivo")
    p.add_argument("--escala", type=float, default=1.0)
    p.add_argument("--impressora", help="chave em impressoras.toml (ex.: ad5x, bambu-a1, k2-pro)")
    a = p.parse_args()
    imp = impressora(a.impressora)
    vol = imp["volume"]
    for nome, m in carregar(a.arquivo, juntar=False):
        if a.escala != 1.0:
            m.apply_scale(a.escala)
        e = m.extents
        corpos = m.split(only_watertight=False)
        print(f"== {nome}")
        print(f"   tamanho (mm): {e[0]:.1f} x {e[1]:.1f} x {e[2]:.1f}")
        print(f"   faces: {len(m.faces)}  corpos: {len(corpos)}  fechada: {m.is_watertight}  "
              f"normais consistentes: {m.is_winding_consistent}")
        if m.is_watertight:
            cm3 = abs(m.volume) / 1000
            print(f"   volume: {cm3:.1f} cm³  peso maciço PLA: {cm3 * DENSIDADE_PLA:.0f} g "
                  f"(com 15% infill e 2 paredes, tipicamente 25-40% disso)")
        cabe = all(x <= y for x, y in zip(sorted(e), sorted(vol)))
        print(f"   cabe na {imp['nome']} ({vol[0]}x{vol[1]}x{vol[2]}): "
              f"{'sim' if cabe else 'NÃO - corte com cortar_com_pinos.py'}")


if __name__ == "__main__":
    main()
