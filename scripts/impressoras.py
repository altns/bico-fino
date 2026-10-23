"""Lista os perfis de impressora de impressoras.toml e mostra qual está ativa.

    python scripts/impressoras.py

Para trocar: IMPRESSORA=<chave> no .env (ou --impressora <chave> nos scripts).
"""
from estudio3d import impressora, impressoras


def main():
    _, perfis = impressoras()
    ativa = impressora()["chave"]
    for chave, p in perfis.items():
        x, y, z = p["volume"]
        extras = [f"{p['multicor']} cores" if p.get("multicor", 1) > 1 else "",
                  "fechada" if p.get("fechada") else ""]
        marca = "*" if chave == ativa else " "
        print(f"{marca} {chave:<16} {p['nome']:<26} {x}x{y}x{z} mm  "
              f"bico até {p['bico_max']} °C, mesa até {p['mesa_max']} °C  {' '.join(e for e in extras if e)}")
    print("\n* = ativa (IMPRESSORA no .env ou 'padrao' em impressoras.toml)")


if __name__ == "__main__":
    main()
