"""Verifica um .3dm contra o esperado de um caso. Fonte de verdade dos vereditos.

  # caso de medida: bbox alvo, comparada por igualdade dentro de --tol
  uv run --with rhino3dm python evals/check.py <arquivo.3dm> \
    --bbox 2400 829 1100 --tol 0.01 --layer "ESTANDE::Mobiliario" [--volume 1.455e9]

  # caso de envelope: teto e/ou piso por eixo (0 = eixo sem limite)
  uv run --with rhino3dm python evals/check.py <arquivo.3dm> \
    --bbox-max 0 400 0 --bbox-min 2300 0 2150 --layer "ESTANDE::Divisoria"

GEOMETRIA QUE ESTE SCRIPT ENXERGA

Brep, Extrusion, Mesh e SubD. Ate 20/09 so' lia Brep, o que era uma bomba para a
frente organica: Kangaroo relaxa MALHA e o caminho usual de modelagem passa por
SubD, entao geometria correta seria reprovada por ser invisivel ao instrumento.
SubD segue incompleto de proposito -- ver `medir()`.

MEDIDA EXATA vs ENVELOPE

Um caso de primitiva tem alvo ("cilindro de raio 300"). Um caso organico tem
envelope ("400 mm de profundidade MAXIMA"). Comparar envelope por igualdade
reprova geometria correta: medido na sondagem de 20/09, onde uma peca de 322,8 mm
satisfazia um teto de 400 e o veredito saiu FALHOU por 19,3%.

MEDICAO DA BBOX — por que nao usa Brep.GetBoundingBox()

rhino3dm devolve, para um Brep, a caixa das superficies NAO APARADAS (casco dos
pontos de controle), nao a da geometria recortada. Numa tampa plana aparada isso
superestima grosseiramente: um solido correto de 2400 x 829 x 1100 devolvia
2608,4 x 2333,8 x 1100 e era REPROVADO por engano. Este script mede pelas malhas
de render gravadas no arquivo, que seguem o recorte real.

Sem malha de render no arquivo, a caixa solta e' apenas um LIMITE SUPERIOR da
verdadeira. Entao so' da' para reprovar com certeza no lado de baixo (medido
menor que o esperado); acima do esperado o resultado e' INCONCLUSIVO, nunca
reprovacao.
"""

import argparse
import json
import sys

import rhino3dm as r


def _malhas(brep):
    for f in brep.Faces:
        m = f.GetMesh(r.MeshType.Any)
        if m is not None:
            yield m


def _tris(m):
    """Triangulos de uma malha. Quad vira dois triangulos."""
    vs = m.Vertices
    for fi in range(len(m.Faces)):
        face = m.Faces[fi]
        yield vs[face[0]], vs[face[1]], vs[face[2]]
        if len(face) > 3 and face[2] != face[3]:
            yield vs[face[0]], vs[face[2]], vs[face[3]]


def bbox_de(malhas):
    """Caixa justa pelos vertices. None se nao ha malha nenhuma."""
    lo = [float("inf")] * 3
    hi = [float("-inf")] * 3
    achou = False
    for m in malhas:
        for i in range(len(m.Vertices)):
            v = m.Vertices[i]
            achou = True
            for eixo, val in enumerate((v.X, v.Y, v.Z)):
                lo[eixo] = min(lo[eixo], val)
                hi[eixo] = max(hi[eixo], val)
    if not achou:
        return None
    return [hi[i] - lo[i] for i in range(3)]


def volume_de(malhas):
    """Volume por teorema da divergencia. None se nao ha malha."""
    total = 0.0
    achou = False
    for m in malhas:
        for pa, pb, pc in _tris(m):
            achou = True
            total += (
                pa.X * (pb.Y * pc.Z - pb.Z * pc.Y)
                - pa.Y * (pb.X * pc.Z - pb.Z * pc.X)
                + pa.Z * (pb.X * pc.Y - pb.Y * pc.X)
            ) / 6.0
    return abs(total) if achou else None


def _solta(g):
    bb = g.GetBoundingBox()
    return [bb.Max.X - bb.Min.X, bb.Max.Y - bb.Min.Y, bb.Max.Z - bb.Min.Z]


def medir(g):
    """Mede um Brep, Mesh ou SubD. None para o que nao sabemos medir.

    Forma organica raramente sai como Brep: Kangaroo relaxa MALHA, e o caminho
    usual de modelagem passa por SubD. Ate 20/09 este script pulava os dois, o
    que reprovaria geometria correta por nao conseguir ve-la.

    SubD e' o caso incompleto e fica declarado como tal: o rhino3dm 8.35 nao
    expoe extracao da superficie limite, so' `Mesh.CreateFromSubDControlNet`,
    que devolve a REDE DE CONTROLE -- o mesmo tipo de aproximacao que causou o
    bug de bbox de 19/09. Entao para SubD medimos a caixa de controle, tratada
    como limite superior, e nao medimos volume.
    """
    if isinstance(g, r.Extrusion):
        g = g.ToBrep(True)

    if isinstance(g, r.Brep):
        malhas = list(_malhas(g))
        justa = bbox_de(malhas)
        return {
            "tipo": "Brep",
            "bbox": justa or _solta(g),
            "bbox_fonte": "malha" if justa else "casco-de-controle (LIMITE SUPERIOR)",
            "bbox_solta": _solta(g),
            "volume": volume_de(malhas) if justa else None,
            "is_valid": g.IsValid,
            "is_solid": g.IsSolid,
            "justa": justa is not None,
        }

    if isinstance(g, r.Mesh):
        justa = bbox_de([g])
        return {
            "tipo": "Mesh",
            "bbox": justa or _solta(g),
            "bbox_fonte": "malha" if justa else "sem vertices",
            "bbox_solta": _solta(g),
            "volume": volume_de([g]) if (justa and g.IsClosed) else None,
            "is_valid": g.IsValid,
            "is_solid": g.IsClosed,
            "justa": justa is not None,
            "nota": None if g.IsClosed else "malha aberta: volume nao definido",
        }

    if isinstance(g, r.SubD):
        return {
            "tipo": "SubD",
            "bbox": _solta(g),
            "bbox_fonte": "caixa de controle do SubD (LIMITE SUPERIOR)",
            "bbox_solta": _solta(g),
            "volume": None,
            "is_valid": g.IsValid,
            "is_solid": g.IsSolid,
            "justa": False,
            "nota": "rhino3dm nao expoe a superficie limite do SubD; volume nao medido",
        }

    return None


ap = argparse.ArgumentParser()
ap.add_argument("file")
ap.add_argument("--bbox", nargs=3, type=float, default=None,
                help="bbox alvo por eixo, comparada com --tol")
# Forma organica se especifica por ENVELOPE, nao por medida exata: "400 mm de
# profundidade maxima" e' um teto, nao um alvo. Comparar isso por igualdade
# reprova geometria correta -- medido na sondagem de 20/09, onde uma peca de
# 322,8 mm satisfazia um teto de 400 e o check devolvia FALHOU por 19,3%.
ap.add_argument("--bbox-max", nargs=3, type=float, default=None,
                help="teto por eixo; use 0 num eixo para nao limitar")
ap.add_argument("--bbox-min", nargs=3, type=float, default=None,
                help="piso por eixo; use 0 num eixo para nao limitar")
ap.add_argument("--tol", type=float, default=0.01)
ap.add_argument("--layer", default=None)
ap.add_argument("--volume", type=float, default=None)
a = ap.parse_args()

if a.bbox is None and a.bbox_max is None and a.bbox_min is None:
    ap.error("informe --bbox, --bbox-max ou --bbox-min")

model = r.File3dm.Read(a.file)
if model is None:
    print(json.dumps({"veredito": "FALHOU", "erro": "nao abriu " + a.file}))
    sys.exit(1)

cands = []
for obj in model.Objects:
    m = medir(obj.Geometry)
    if m is None:
        continue
    li = obj.Attributes.LayerIndex
    d = {
        "nome": obj.Attributes.Name,
        "tipo": m["tipo"],
        "camada": model.Layers[li].FullPath if 0 <= li < len(model.Layers) else None,
        "is_valid": m["is_valid"],
        "is_solid": m["is_solid"],
        "bbox": [round(x, 1) for x in m["bbox"]],
        "bbox_fonte": m["bbox_fonte"],
        "bbox_solta": [round(x, 1) for x in m["bbox_solta"]],
        "volume": m["volume"],
        "_tem_malha": m["justa"],
        "_v": m["bbox"][0] * m["bbox"][1] * m["bbox"][2],
    }
    if m.get("nota"):
        d["nota"] = m["nota"]
    cands.append(d)

if not cands:
    print(json.dumps({
        "veredito": "FALHOU",
        "erro": "nenhuma geometria mensuravel no arquivo (procurados Brep, Extrusion, Mesh, SubD)",
    }))
    sys.exit(1)

# Escolha do alvo. Ordenar so' por tamanho misturava caixa justa com caixa solta
# entre candidatos: num arquivo com dois objetos, o que NAO tem malha ganhava por
# ter a caixa inflada, e a medicao firme do outro era descartada (rodada 2).
# Ordem: mensuravel primeiro, depois solido fechado, depois maior.
def _rank(c):
    return (c["_tem_malha"], bool(c["is_solid"]), c["_v"])


ordenados = sorted(cands, key=_rank, reverse=True)
alvo = ordenados[0]
criterio = "malha > solido fechado > maior caixa"

solidos_com_malha = [c for c in cands if c["_tem_malha"] and c["is_solid"]]
ambiguo = len(solidos_com_malha) > 1

outros = [
    {"nome": c["nome"], "bbox": c["bbox"], "bbox_fonte": c["bbox_fonte"],
     "is_solid": c["is_solid"], "camada": c["camada"]}
    for c in ordenados[1:]
]
for c in cands:
    c.pop("_v", None)
    c.pop("_tem_malha", None)

justa = alvo["bbox_fonte"] == "malha"

falhas = []
inconclusivos = []

if a.bbox:
    # Eixo esperado ZERO e' legitimo -- geometria plana (regiao planar, malha
    # aberta, chapa sem espessura). Desvio relativo nao existe ai, entao a
    # comparacao vira absoluta, contra uma fracao do maior eixo do caso.
    escala = max(a.bbox) or 1.0
    for eixo, med, esp in zip("XYZ", alvo["bbox"], a.bbox):
        if esp == 0:
            if abs(med) <= a.tol * escala:
                continue
            falhas.append(f"bbox {eixo}: medido {med} vs esperado 0 (deveria ser plano)")
            continue
        desvio = abs(med - esp) / esp
        if desvio <= a.tol:
            continue
        msg = f"bbox {eixo}: medido {med} vs esperado {esp} ({desvio:.1%})"
        if justa or med < esp:
            # caixa justa reprova nos dois lados; caixa solta so' reprova por falta
            falhas.append(msg)
        else:
            inconclusivos.append(msg + " - caixa solta superestima; sem malha para decidir")

if a.bbox_max:
    for eixo, med, teto in zip("XYZ", alvo["bbox"], a.bbox_max):
        if teto <= 0 or med <= teto * (1 + a.tol):
            continue
        # Medida acima do teto reprova mesmo com caixa solta: a caixa solta e'
        # limite superior, entao se ELA estoura o teto, a real pode nao estourar.
        msg = f"bbox {eixo}: medido {med} excede o teto de {teto}"
        (falhas if justa else inconclusivos).append(
            msg if justa else msg + " - caixa solta superestima; sem malha para decidir")

if a.bbox_min:
    for eixo, med, piso in zip("XYZ", alvo["bbox"], a.bbox_min):
        if piso <= 0 or med >= piso * (1 - a.tol):
            continue
        # Abaixo do piso reprova sempre: a caixa solta so' erra para cima, entao
        # se ate' ela ficou abaixo do piso, a real ficou tambem.
        falhas.append(f"bbox {eixo}: medido {med} abaixo do piso de {piso}")

if not alvo["is_valid"]:
    falhas.append("IsValid = false")
if not alvo["is_solid"]:
    falhas.append("IsSolid = false")
if a.layer and alvo["camada"] != a.layer:
    falhas.append(f"camada: {alvo['camada']} vs esperado {a.layer}")

if a.volume is not None:
    if alvo["volume"] is None:
        inconclusivos.append("volume: " + (alvo.get("nota") or "sem malha de render no arquivo"))
    else:
        dv = abs(alvo["volume"] - a.volume) / a.volume
        if dv > a.tol:
            falhas.append(f"volume: medido {alvo['volume']:.4g} vs esperado {a.volume:.4g} ({dv:.1%})")

avisos = []
if len(cands) > 1:
    avisos.append(f"{len(cands)} objetos mensuraveis no arquivo: sobrou geometria de construcao")
if ambiguo:
    avisos.append(f"{len(solidos_com_malha)} solidos fechados mensuraveis: alvo escolhido por tamanho")

if falhas:
    veredito = "FALHOU"
elif inconclusivos:
    veredito = "INCONCLUSIVO"
else:
    veredito = "PASSOU"

print(json.dumps({
    "veredito": veredito,
    "falhas": falhas,
    "inconclusivos": inconclusivos,
    "avisos": avisos,
    "objeto": alvo,
    "alvo_escolhido_por": criterio,
    "outros_objetos": outros,
    "objetos_no_arquivo": len(cands),
}, ensure_ascii=False, indent=2))
sys.exit(0 if veredito == "PASSOU" else 1)
