# -*- coding: utf-8 -*-
"""Bake da geometria do Grasshopper para o documento do Rhino.

NAO RODE ESTE ARQUIVO LOCALMENTE. O conteudo de SCRIPT e' IronPython 2.7 e so'
faz sentido dentro do processo do Rhino: ele e' enviado verbatim para a tool
`execute_rhinoscript_python_code` do MCP `rhino`. O que roda localmente e'
apenas a montagem do texto.

Por que IronPython, e nao C#
----------------------------
A rota `execute_rhinocommon_csharp_code` falhou porque o assembly do
Grasshopper esta' fora da compilacao (por reflexao, NullReferenceException).
O plugin executa scripts com `PythonScript.Create()` (IronPython 2.7, em
processo), e IronPython resolve assembly em TEMPO DE EXECUCAO via
`clr.AddReference` -- exatamente a peca que faltava.

Disciplina que este arquivo existe para sustentar
-------------------------------------------------
O bake e' infraestrutura do harness, como o `check.py`. O script e' literal,
versionado e revisado; o modelo NUNCA o escreve. Isso e' o que mantem de pe'
a secao 5 do PRD: o LLM emite parametros, nao geometria nem codigo.

Uso (do supervisor, com Rhino aberto e o template no canvas):

    python evals/bake_gh.py
    python evals/bake_gh.py --layer "ESTANDE::Mobiliario"
"""

import argparse

# Script enviado ao Rhino. __CAMADA__ e' o unico ponto de substituicao.
SCRIPT = u'''
import clr
clr.AddReference("Grasshopper")
import Grasshopper as gh
import Rhino, System

canvas = gh.Instances.ActiveCanvas
doc_gh = canvas.Document if canvas else None

if doc_gh is None:
    print("ERRO: nenhum documento do Grasshopper aberto no canvas")
else:
    doc_rh = Rhino.RhinoDoc.ActiveDoc
    nome_camada = "__CAMADA__"

    # Camada de destino: reaproveita se existir, cria (com os pais) se nao.
    indice = -1
    if nome_camada:
        indice = doc_rh.Layers.FindByFullPath(nome_camada, -1)
        if indice < 0:
            indice = doc_rh.Layers.AddPath(nome_camada)

    att = doc_rh.CreateDefaultAttributes()
    if indice >= 0:
        att.LayerIndex = indice

    ids = []
    bakeaveis = 0
    for obj in doc_gh.Objects:
        if not isinstance(obj, gh.Kernel.IGH_BakeAwareObject):
            continue
        if not obj.IsBakeCapable:
            continue
        bakeaveis += 1
        guids = System.Collections.Generic.List[System.Guid]()
        obj.BakeGeometry(doc_rh, att, guids)
        ids.extend(list(guids))

    doc_rh.Views.Redraw()
    print("componentes bakeaveis: %d" % bakeaveis)
    print("objetos bakeados: %d" % len(ids))
    print("camada: %s (indice %d)" % (nome_camada or "(padrao)", indice))
'''


def montar(layer=""):
    """Devolve o script pronto para envio, com a camada substituida."""
    return SCRIPT.replace("__CAMADA__", layer or "")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Monta o script de bake para envio ao Rhino.")
    ap.add_argument("--layer", default="", help="camada de destino, ex.: ESTANDE::Mobiliario")
    args = ap.parse_args()
    print(montar(args.layer))
