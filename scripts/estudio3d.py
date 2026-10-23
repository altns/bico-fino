"""Biblioteca comum do estúdio 3D: leitura/gravação de malhas (3MF/STL/OBJ) e conversões.

Uso típico nos outros scripts:
    from estudio3d import carregar, salvar_3mf, para_manifold, de_manifold
"""
from __future__ import annotations

import os
import re
import tomllib
import zipfile
from pathlib import Path

import numpy as np
import trimesh

# Densidade do PLA (g/cm³) usada para estimar peso
DENSIDADE_PLA = 1.24

RAIZ = Path(__file__).resolve().parent.parent
PERFIS_IMPRESSORA = RAIZ / "impressoras.toml"

_NS_CORE = "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"


def _matriz_3mf(texto: str | None) -> np.ndarray:
    m = np.eye(4)
    if texto:
        v = [float(x) for x in texto.split()]
        m[:3, :3] = np.array(v[:9]).reshape(3, 3).T
        m[:3, 3] = v[9:12]
    return m


def _ler_3mf(caminho: Path) -> list[tuple[str, trimesh.Trimesh]]:
    """Lê um 3MF (inclusive projetos Bambu/Orca com componentes em arquivos separados).

    Retorna uma lista (nome, malha) por item da mesa, já com a transformação aplicada.
    """
    from lxml import etree

    z = zipfile.ZipFile(caminho)
    docs = {"/" + n: etree.fromstring(z.read(n)) for n in z.namelist() if n.lower().endswith(".model")}
    raiz = next(k for k in docs if k.lower() == "/3d/3dmodel.model")

    def tag(t):
        return f"{{{_NS_CORE}}}{t}"

    objetos = {}
    for arq, doc in docs.items():
        for ob in doc.iter(tag("object")):
            objetos[(arq, ob.get("id"))] = ob

    def malha_do_objeto(arq, oid, tf):
        ob = objetos[(arq, oid)]
        partes = []
        mesh = ob.find(tag("mesh"))
        if mesh is not None:
            v = np.array([[float(e.get(k)) for k in "xyz"] for e in mesh.iter(tag("vertex"))])
            f = np.array([[int(e.get(k)) for k in ("v1", "v2", "v3")] for e in mesh.iter(tag("triangle"))])
            m = trimesh.Trimesh(v, f, process=True)
            m.apply_transform(tf)
            partes.append(m)
        comps = ob.find(tag("components"))
        if comps is not None:
            for c in comps.findall(tag("component")):
                caminho_c = None
                for k, val in c.attrib.items():
                    if k.endswith("}path"):
                        caminho_c = val
                partes += malha_do_objeto(caminho_c or arq, c.get("objectid"), tf @ _matriz_3mf(c.get("transform")))
        return partes

    saida = []
    for i, item in enumerate(docs[raiz].iter(tag("item"))):
        oid = item.get("objectid")
        partes = malha_do_objeto(raiz, oid, _matriz_3mf(item.get("transform")))
        nome = objetos[(raiz, oid)].get("name") or f"objeto_{i + 1}"
        saida.append((nome, trimesh.util.concatenate(partes)))
    return saida


def carregar(caminho: str | Path, juntar: bool = True):
    """Carrega STL/OBJ/3MF. Com juntar=True devolve uma única malha; senão lista (nome, malha)."""
    caminho = Path(caminho)
    if caminho.suffix.lower() == ".3mf":
        itens = _ler_3mf(caminho)
    else:
        m = trimesh.load(caminho, force="mesh")
        itens = [(caminho.stem, m)]
    if juntar:
        return trimesh.util.concatenate([m for _, m in itens])
    return itens


def salvar_3mf(destino: str | Path, objetos: list[tuple[str, trimesh.Trimesh]], titulo: str = "") -> None:
    """Grava um 3MF simples com vários objetos nomeados (abre no Orca-Flashforge/OrcaSlicer/Bambu)."""
    objs, itens = [], []
    for i, (nome, m) in enumerate(objetos, 1):
        v = "".join(f'<vertex x="{a:.5f}" y="{b:.5f}" z="{c:.5f}"/>' for a, b, c in m.vertices)
        t = "".join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in m.faces)
        nome_xml = nome.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;")
        objs.append(f'<object id="{i}" name="{nome_xml}" type="model"><mesh><vertices>{v}</vertices>'
                    f"<triangles>{t}</triangles></mesh></object>")
        itens.append(f'<item objectid="{i}"/>')
    modelo = ('<?xml version="1.0" encoding="UTF-8"?>\n'
              f'<model unit="millimeter" xml:lang="pt-BR" xmlns="{_NS_CORE}">'
              f'<metadata name="Title">{titulo}</metadata>'
              f'<resources>{"".join(objs)}</resources><build>{"".join(itens)}</build></model>')
    tipos = ('<?xml version="1.0" encoding="UTF-8"?>\n'
             '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
             '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
             '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
    rels = ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Target="/3D/3dmodel.model" Id="rel0" '
            'Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
    with zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", tipos)
        zf.writestr("_rels/.rels", rels)
        zf.writestr("3D/3dmodel.model", modelo)


def para_manifold(m: trimesh.Trimesh):
    import manifold3d as mf

    m = m.copy()
    m.merge_vertices()
    return mf.Manifold(mf.Mesh(vert_properties=m.vertices.astype(np.float32),
                               tri_verts=m.faces.astype(np.uint32)))


def de_manifold(x) -> trimesh.Trimesh:
    """Converte de volta e funde vértices quase coincidentes (evita 'películas' e arestas abertas)."""
    g = x.to_mesh()
    v = np.array(g.vert_properties)[:, :3]
    f = np.array(g.tri_verts)
    return limpar(trimesh.Trimesh(v, f, process=False))


def limpar(m: trimesh.Trimesh, casas: int = 4) -> trimesh.Trimesh:
    """Funde vértices a 10^-casas mm, remove faces degeneradas e pares de faces duplicadas."""
    v, inv = np.unique(m.vertices.round(casas), axis=0, return_inverse=True)
    f = inv.reshape(-1)[m.faces]
    f = f[(f[:, 0] != f[:, 1]) & (f[:, 1] != f[:, 2]) & (f[:, 0] != f[:, 2])]
    chave = np.sort(f, axis=1)
    _, idx, cont = np.unique(chave, axis=0, return_inverse=True, return_counts=True)
    f = f[cont[idx.reshape(-1)] == 1]
    r = trimesh.Trimesh(v, f, process=False)
    r.remove_unreferenced_vertices()
    return r


def impressoras() -> tuple[str, dict[str, dict]]:
    """Lê impressoras.toml: devolve (chave padrão, {chave: perfil})."""
    with open(PERFIS_IMPRESSORA, "rb") as f:
        cfg = tomllib.load(f)
    return cfg.get("padrao", ""), cfg["impressoras"]


def impressora(chave: str | None = None) -> dict:
    """Perfil da impressora: a chave pedida, senão IMPRESSORA do ambiente/.env, senão o padrão do toml."""
    from dotenv import load_dotenv

    load_dotenv(RAIZ / ".env")
    padrao, perfis = impressoras()
    chave = chave or os.getenv("IMPRESSORA") or padrao
    if chave not in perfis:
        raise SystemExit(f"Impressora '{chave}' não está em {PERFIS_IMPRESSORA.name}. "
                         f"Opções: {', '.join(perfis)}")
    return {"chave": chave, **perfis[chave]}


def no_centro_da_mesa(m: trimesh.Trimesh, mesa: tuple[float, float] | None = None) -> trimesh.Trimesh:
    """Centraliza em XY na mesa (por padrão a da impressora ativa) e apoia em Z=0."""
    if mesa is None:
        mesa = impressora()["volume"][:2]
    m = m.copy()
    c = (m.bounds[0] + m.bounds[1]) / 2
    m.apply_translation([mesa[0] / 2 - c[0], mesa[1] / 2 - c[1], -m.bounds[0, 2]])
    return m


def nome_seguro(s: str) -> str:
    return re.sub(r"[^\w\-. ]", "_", s).strip() or "objeto"
