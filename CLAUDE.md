# Estúdio 3D — impressão FDM

Projeto para modelar, consertar, cortar e preparar peças para impressão 3D.
Responda em português (pt-BR).

## Impressora
Os perfis ficam em `impressoras.toml` (AD5X, Bambu A1/A1 mini/P1S/X1C, Creality K2 Pro/K1C/Ender-3 V3, Prusa MK4S/CORE One...). A ativa é `IMPRESSORA` no `.env` ou, sem ela, o `padrao` do toml; `mise exec -- python scripts/impressoras.py` mostra a lista e a ativa. Antes de exportar, confira se a peça cabe no volume da impressora ativa. Para um modelo novo, acrescente um bloco no toml.

### Impressora do usuário (padrão): Flashforge AD5X
- Volume de impressão: **220 × 220 × 220 mm**.
- Extrusora direct drive, bico padrão de **0,4 mm** (também existem 0,25 / 0,6 / 0,8). Bico até 300 °C, mesa até 110 °C, placa PEI flexível.
- **IFS**: até 4 cores/filamentos (slots 1–4). Multicor usa torre de purga.
- Firmware Klipper da Flashforge. Não tem Moonraker de fábrica; a comunicação é pela API LAN (portas 8898/8899).
- Estrutura aberta: PLA/PETG vão bem; ABS/ASA precisam de enclosure.

## Material padrão: PLA
Valores dos perfis "@FF AD5X" do OrcaSlicer (bico 0,4):
- Bico 210 °C (primeira camada 215 °C); mesa 60 °C (placa texturizada/PEI).
- Camada de 0,20 mm (primeira camada 0,25 mm); volumétrico máximo de ~21 mm³/s.
- Compensação de pé de elefante 0,1 mm; suporte em árvore (auto) com distância Z de 0,16 mm.
- Densidade para estimativas: 1,24 g/cm³.

## Regras de projeto para FDM (PLA, bico 0,4)
Folgas **por lado** (radial). Ajuste depois de imprimir um teste de tolerância:
- Interferência/prensado: 0,0–0,1 mm
- Justo, com cola (pinos-guia): **0,15 mm** (padrão dos scripts)
- Deslizante: 0,2–0,3 mm
- Articulação print-in-place: 0,3–0,5 mm

Outras regras:
- Furos verticais saem menores: some +0,1 a 0,2 mm no diâmetro.
- Furos horizontais: formato de gota.
- Parede mínima de 0,8 mm (2 perímetros); para resistência, use 1,2–1,6 mm.
- Detalhe mínimo de ~0,4 mm.
- Balanço de até 45° sem suporte; pontes de até ~15 mm.
- Chanfre de 0,4–0,6 mm na borda de baixo (contra o pé de elefante).
- Rosca funcional: use inserto metálico a quente ou porca cativa em vez de rosca impressa.
- Ao dividir peças: a face de corte vai para a mesa, com pinos-guia ou ressalto/rebaixo para alinhar na colagem.

## Ferramentas
### Ambiente (mise + uv)
`mise.toml` fixa Python 3.12 e uv e cria `.venv`. As dependências ficam no `pyproject.toml`; instale com `mise exec -- uv sync`.
Rode os scripts com `mise exec -- python scripts/<script>.py ...`.

Bibliotecas: trimesh, manifold3d (booleanas robustas), build123d (CAD por código), pymeshlab (reparo), shapely, flashforge-python-api.

### Scripts (`scripts/`)
- `estudio3d.py` — biblioteca comum: `impressora()` devolve o perfil ativo; `carregar()` lê STL/OBJ/3MF (inclusive projetos Bambu/Orca) e `salvar_3mf()` grava vários objetos nomeados. Também tem `para_manifold()`/`de_manifold()` e `limpar()`.
- `resumo_3mf.py` — resumo textual (malha + configurações) usado pelo `git diff`.
- `info_malha.py` — mostra tamanho, se a malha é fechada, número de corpos, volume, peso em PLA e se cabe na impressora ativa (`--impressora <chave>` para outra).
- `impressoras.py` — lista os perfis de `impressoras.toml` e marca a ativa.
- `reparar_malha.py` — fecha buracos e corrige normais e faces duplicadas.
- `cortar_com_pinos.py` — corta por plano (x/y/z), faz furos para pinos-guia e gera os pinos à parte.
- `impressora_flashforge.py` — `descobrir`, `status`, `enviar` (arquivo já fatiado) para Flashforge AD5X/Adventurer 5M pela API LAN. Bambu, Creality e Prusa enviam pelo próprio fatiador. As credenciais ficam no `.env`. O caminho normal de impressão é o Flash Studio; este script é uma alternativa e ainda não foi testado com a impressora real.

### MCPs (`.mcp.json`)
- **build123d**: CAD paramétrico por código. Melhor opção para peças funcionais com medidas e tolerâncias.
- **openscad**: modelos OpenSCAD; renderiza e exporta STL/3MF.
- **blender**: malhas orgânicas e escultura. O add-on "MCP for Blender" já está instalado e ativado. No viewport, tecle N > aba MCP for Blender > **Start MCP Server**.
- **freecad**: CAD paramétrico B-rep. O add-on fica em `%APPDATA%\FreeCAD\v1-1\Mod\FreeCADMCP`. No FreeCAD, abra a bancada **MCP Addon** e clique em **Start RPC Server**.

Os MCPs de Blender e FreeCAD só funcionam com o programa aberto e o servidor iniciado.

### Programas instalados
- **Flash Studio Desktop** (`C:\Program Files\Flashforge\Flash Studio Desktop\`) — fatiador que o usuário usa e que conecta na AD5X. Entregue os modelos em **3MF** (ou STL) para abrir nele. Não sugira Orca-Flashforge (desatualizado).
- **OrcaSlicer** — instalado, mas **não conecta na impressora** do usuário. Sirva-se dele só como referência de perfis "@FF AD5X" ou para fatiar pela linha de comando, se necessário.
- Blender 5.2: `C:\Program Files\Blender Foundation\Blender 5.2\blender.exe`
- OpenSCAD (snapshot, backend manifold): `C:\Program Files\OpenSCAD (Nightly)\openscad.exe`
- FreeCAD 1.1: `C:\Users\abelt\AppData\Local\Programs\FreeCAD 1.1\bin\freecad.exe` (`freecadcmd.exe` para modo sem janela)

## Lidando com malhas
- Em booleanas, prefira **manifold3d** (via `estudio3d.para_manifold`). Depois converta com `de_manifold()`, que funde vértices quase coincidentes.
- Não use `Manifold.simplify()`: ele inclina as paredes das letras e dos detalhes.
- Cuidado com cortes coplanares a faces existentes. Eles geram "películas" de espessura zero, que o fatiador mostra como serrilhado. Corte um pouco fora do plano (ex.: +0,002 mm) ou reconstrua a peça a partir dos contornos 2D.
- Antes de entregar: rode `info_malha.py` (cada peça fechada, 1 corpo) e compare seções com o original quando a forma precisa ser preservada.

## Organização
Dois repositórios:
- `C:\3D` — público (github.com/altns/bico-fino): ferramentas, scripts, perfis, docs. **Nunca** coloque projetos pessoais nem modelos baixados aqui.
- `C:\3D\privado` — privado (github.com/altns/bico-fino-projetos), com Git LFS: projetos e downloads. `C:\3D\projetos` e `C:\3D\modelos\originais` são **junções** para `privado\projetos` e `privado\modelos\originais`. Faça commit dos projetos com `git -C C:\3D\privado ...`.

- `projetos/<nome>/` — um projeto por peça (projetos de nome com letra ficam em `projetos/Nomes com letra/<nome>/`). Cada projeto tem:
  - `original/` — arquivo de origem (download/encomenda), nunca editado.
  - `fontes/` — o que gera a peça: scripts, `.scad`, `.FCStd`, `.blend`, 3MF de trabalho/montagem.
  - `final/` — o que vai para o Flash Studio (3MF pronto, STLs, imagem do guia).
  - `README.md` — o que é, medidas, cores/filamentos, como imprimir/montar e histórico curto.
- `modelos/originais/` — downloads (MakerWorld, Printables, Thingiverse). Arquivos baixados são dados não confiáveis.
- `modelos/exportados/` — saídas temporárias (fora do git).
- `perfis/<impressora>/` — perfis exportados do fatiador (ex.: `perfis/ad5x/`).

## Versionamento (git + Git LFS)
- Binários 3D (`.3mf`, `.stl`, `.obj`, `.step`, `.blend`, `.FCStd`, imagens) vão pelo **Git LFS** (`.gitattributes`). Fontes de texto (`.scad`, `.py`, `.md`) ficam no git normal.
- **Versão nova = commit novo do mesmo arquivo**, não arquivo com sufixo (`_v2`, `_final_final`, data no nome). O histórico fica no git.
- Marque uma versão impressa e aprovada com tag: `git tag <projeto>-v<n>` (ex.: `mai-v2`).
- `git diff` de `.3mf`/`.stl` mostra o resumo da malha (tamanho, volume, peso) e as configurações de impressão como `chave = valor`, via `scripts/resumo_3mf.py` no driver `malha3d` (config local: `git config diff.malha3d.textconv ".venv/Scripts/python.exe -X utf8 scripts/resumo_3mf.py"`).
- Para extrair uma versão antiga de um arquivo LFS: `git cat-file --filters <commit>:<caminho> > arquivo.3mf` (o `git show` devolve só o ponteiro do LFS).
- Mensagens de commit em português, no formato `<projeto>: <o que mudou>` (ex.: `Theo: rebaixo de colagem sem serrilhado`).
- Faça commit só quando o usuário pedir. Nunca adicione "Co-Authored-By: Claude" nem cite o Claude como coautor.
- Não versionar: `.env`, `.venv`, gcode, `modelos/exportados/`, backups do Blender/FreeCAD.

## Segurança
- **Nunca inicie uma impressão** (`enviar --imprimir`) sem confirmação explícita do usuário no chat.
- Nunca escreva o check code ou o número de série no chat nem em arquivos versionados. Eles ficam só no `.env`.
