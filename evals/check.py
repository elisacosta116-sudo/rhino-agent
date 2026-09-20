"""Verifica um .3dm contra o esperado de um caso. Fonte de verdade dos vereditos.

  uv run --with rhino3dm python evals/check.py <arquivo.3dm> \
    --bbox 2400 829 1100 --tol 0.01 --layer "ESTANDE::Mobiliario" [--volume 1.455e9]

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


def bbox_malha(brep):
    """Caixa justa, a partir das malhas de render. None se o arquivo nao as tem."""
    lo = [float("inf")] * 3
    hi = [float("-inf")] * 3
    achou = False
    for m in _malhas(brep):
        for i in range(len(m.Vertices)):
            v = m.Vertices[i]
            achou = True
            for eixo, val in enumerate((v.X, v.Y, v.Z)):
                lo[eixo] = min(lo[eixo], val)
                hi[eixo] = max(hi[eixo], val)
    if not achou:
        return None
    return [hi[i] - lo[i] for i in range(3)]


def volume_malha(brep):
    """Volume por teorema da divergencia sobre as malhas. None se nao ha malha."""
    total = 0.0
    achou = False
    for m in _malhas(brep):
        vs = m.Vertices
        for fi in range(len(m.Faces)):
            face = m.Faces[fi]
            tris = [(face[0], face[1], face[2])]
            if len(face) > 3 and face[2] != face[3]:
                tris.append((face[0], face[2], face[3]))
            for a, b, c in tris:
                achou = True
                pa, pb, pc = vs[a], vs[b], vs[c]
                total += (
                    pa.X * (pb.Y * pc.Z - pb.Z * pc.Y)
                    - pa.Y * (pb.X * pc.Z - pb.Z * pc.X)
                    + pa.Z * (pb.X * pc.Y - pb.Y * pc.X)
                ) / 6.0
    return abs(total) if achou else None


ap = argparse.ArgumentParser()
ap.add_argument("file")
ap.add_argument("--bbox", nargs=3, type=float, required=True)
ap.add_argument("--tol", type=float, default=0.01)
ap.add_argument("--layer", default=None)
ap.add_argument("--volume", type=float, default=None)
a = ap.parse_args()

model = r.File3dm.Read(a.file)
if model is None:
    print(json.dumps({"veredito": "FALHOU", "erro": "nao abriu " + a.file}))
    sys.exit(1)

cands = []
for obj in model.Objects:
    g = obj.Geometry
    if isinstance(g, r.Extrusion):
        g = g.ToBrep(True)
    if not isinstance(g, r.Brep):
        continue
    bb = g.GetBoundingBox()
    solta = [bb.Max.X - bb.Min.X, bb.Max.Y - bb.Min.Y, bb.Max.Z - bb.Min.Z]
    justa = bbox_malha(g)
    li = obj.Attributes.LayerIndex
    cands.append({
        "nome": obj.Attributes.Name,
        "camada": model.Layers[li].FullPath if 0 <= li < len(model.Layers) else None,
        "is_valid": g.IsValid,
        "is_solid": g.IsSolid,
        "bbox": [round(d, 1) for d in (justa or solta)],
        "bbox_fonte": "malha" if justa else "casco-de-controle (LIMITE SUPERIOR)",
        "bbox_solta": [round(d, 1) for d in solta],
        "volume": volume_malha(g) if justa else None,
        "_tem_malha": justa is not None,
        "_v": (justa or solta)[0] * (justa or solta)[1] * (justa or solta)[2],
    })

if not cands:
    print(json.dumps({"veredito": "FALHOU", "erro": "nenhum Brep no arquivo"}))
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
for eixo, med, esp in zip("XYZ", alvo["bbox"], a.bbox):
    desvio = abs(med - esp) / esp
    if desvio <= a.tol:
        continue
    msg = f"bbox {eixo}: medido {med} vs esperado {esp} ({desvio:.1%})"
    if justa or med < esp:
        # caixa justa reprova nos dois lados; caixa solta so' reprova por falta
        falhas.append(msg)
    else:
        inconclusivos.append(msg + " - caixa solta superestima; sem malha para decidir")

if not alvo["is_valid"]:
    falhas.append("IsValid = false")
if not alvo["is_solid"]:
    falhas.append("IsSolid = false")
if a.layer and alvo["camada"] != a.layer:
    falhas.append(f"camada: {alvo['camada']} vs esperado {a.layer}")

if a.volume is not None:
    if alvo["volume"] is None:
        inconclusivos.append("volume: sem malha de render no arquivo")
    else:
        dv = abs(alvo["volume"] - a.volume) / a.volume
        if dv > a.tol:
            falhas.append(f"volume: medido {alvo['volume']:.4g} vs esperado {a.volume:.4g} ({dv:.1%})")

avisos = []
if len(cands) > 1:
    avisos.append(f"{len(cands)} Breps no arquivo: sobrou geometria de construcao")
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
    "outros_breps": outros,
    "breps_no_arquivo": len(cands),
}, ensure_ascii=False, indent=2))
sys.exit(0 if veredito == "PASSOU" else 1)
