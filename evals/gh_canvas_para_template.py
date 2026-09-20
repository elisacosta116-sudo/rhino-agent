"""Converte o estado de um canvas Grasshopper no formato de entrada do gh_build_graph.

  uv run --no-project python evals/gh_canvas_para_template.py <canvas.json> <template.json>

Por que existe: nao ha tool `gh_save` no rhinomcp, entao o grafo montado vive
so' na sessao aberta do Grasshopper. Sem conversao, fechar o Rhino perde o
template -- e refaze-lo custou US$ 0,75 na primeira vez.

O formato versionado do template passa a ser este JSON, e nao o binario `.gh`:
e' diffavel no git, e' o que `gh_build_graph` consome direto, e casa com a
arquitetura do PRD, onde o LLM preenche parametros de algo ja declarado.

`gh_get_canvas_state` e' formato de SAIDA (instance_ids, valores resolvidos,
posicoes); `gh_build_graph` quer formato de ENTRADA (aliases estaveis). A
traducao principal e' instance_id -> alias legivel e unico.
"""

import json
import pathlib
import sys
from collections import Counter


def aliases(canvas):
    """instance_id -> alias unico e legivel, derivado do nickname."""
    usados = Counter()
    mapa = {}
    for item in canvas.get("standalone_parameters", []) + canvas.get("components", []):
        base = (item.get("nickname") or item.get("name") or "c").strip()
        base = "".join(ch if ch.isalnum() else "_" for ch in base).strip("_").lower() or "c"
        usados[base] += 1
        mapa[item["instance_id"]] = base if usados[base] == 1 else f"{base}_{usados[base]}"
    return mapa


def componentes(canvas, mapa):
    saida = []
    for p in canvas.get("standalone_parameters", []):
        c = {"alias": mapa[p["instance_id"]], "component_name": p["name"]}
        # Slider carrega o proprio dominio: sem min/max o gh_build_graph recria
        # com o default e o template deixa de reproduzir o que foi medido.
        for chave in ("value", "min", "max", "decimals"):
            if p.get(chave) is not None:
                c[chave] = p[chave]
        if p.get("special_type") == "panel" and p.get("content") is not None:
            c["value"] = p["content"]
        saida.append(c)
    for comp in canvas.get("components", []):
        saida.append({"alias": mapa[comp["instance_id"]], "component_name": comp["name"]})
    return saida


def conexoes(canvas, mapa):
    saida = []
    for comp in canvas.get("components", []):
        destino = mapa[comp["instance_id"]]
        for entrada in comp.get("inputs", []):
            for origem in entrada.get("sources", []) or []:
                oid = origem.get("component_id")
                if oid not in mapa:
                    # Fonte fora do canvas lido: registrar em vez de inventar.
                    saida.append({"_origem_desconhecida": oid, "target": destino,
                                  "target_input_index": entrada["index"]})
                    continue
                saida.append({"source": mapa[oid], "target": destino,
                              "target_input_index": entrada["index"]})
    return saida


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    canvas = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
    mapa = aliases(canvas)
    comps = componentes(canvas, mapa)
    cons = conexoes(canvas, mapa)

    orfas = [c for c in cons if "_origem_desconhecida" in c]
    template = {
        "componentes": comps,
        "conexoes": [c for c in cons if "_origem_desconhecida" not in c],
        "layout": {"enabled": True, "max_columns": 6},
    }
    if orfas:
        template["_conexoes_sem_origem"] = orfas

    pathlib.Path(sys.argv[2]).write_text(
        json.dumps(template, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"componentes: {len(comps)}  conexoes: {len(template['conexoes'])}")
    if orfas:
        print(f"AVISO: {len(orfas)} conexoes com origem fora do canvas lido")
    print("escrito:", sys.argv[2])


if __name__ == "__main__":
    main()
