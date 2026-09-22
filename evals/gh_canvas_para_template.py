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
import re
import sys
from collections import Counter


# Alias aceito pelo contrato do gh_build_graph ($defs/alias).
ALIAS_VALIDO = re.compile(r"^[A-Za-z_][A-Za-z0-9_-]*$")


def aliases(canvas):
    """instance_id -> alias unico e legivel.

    Prefere o `alias` que o proprio canvas carrega: quando o grafo foi montado
    por `gh_build_graph`, ele traz os nomes que o autor escolheu (pA, lnS,
    ends), e derivar do nickname os substituiria por pt, pt_2, pt_3 -- tres
    "Construct Point" viram numeros e o template deixa de ser legivel, que e'
    metade da razao deste formato existir.
    """
    usados = Counter()
    mapa = {}
    for item in canvas.get("standalone_parameters", []) + canvas.get("components", []):
        proprio = (item.get("alias") or "").strip()
        if proprio and ALIAS_VALIDO.match(proprio) and proprio not in usados:
            usados[proprio] += 1
            mapa[item["instance_id"]] = proprio
            continue
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
    """Conexoes no formato de entrada do gh_build_graph.

    `source_output_name` e' obrigatorio na pratica, ainda que o contrato o
    marque opcional: uma origem com mais de uma saida fica ambigua sem ele e o
    build cai na saida 0. Foi esse o defeito que quebrou o balcao.json -- as
    duas linhas do perfil puxavam de `End Points`, uma da saida 'Start' e outra
    da 'End', e sem o nome as duas viraram 'Start'. O perfil nao fechava, o
    Join Curves saia com 2 ramos e o Cap Holes falhava.

    O `param_name` do `gh_get_canvas_state` e' exatamente esse nome de saida.
    """
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
                conexao = {"source": mapa[oid]}
                nome_saida = origem.get("param_name")
                if nome_saida:
                    conexao["source_output_name"] = nome_saida
                conexao["target"] = destino
                conexao["target_input_index"] = entrada["index"]
                saida.append(conexao)
    return saida


def ambiguas(canvas, mapa, cons):
    """Conexoes que vem de origem com varias saidas e nao dizem qual.

    Rede de seguranca para o defeito que quebrou o balcao.json. Sem isto, a
    perda e' silenciosa: o template converte sem erro e so' falha na
    remontagem, num componente muito depois na cadeia (foi o Cap Holes).
    """
    saidas = {}
    for comp in canvas.get("components", []):
        saidas[mapa[comp["instance_id"]]] = len(comp.get("outputs", []) or [])
    suspeitas = []
    for c in cons:
        if "source" not in c or c.get("source_output_name"):
            continue
        if saidas.get(c["source"], 0) > 1:
            suspeitas.append(c)
    return suspeitas


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

    duvidosas = ambiguas(canvas, mapa, template["conexoes"])
    if duvidosas:
        print(f"AVISO: {len(duvidosas)} conexoes de origem com varias saidas e sem "
              "source_output_name -- o build vai cair na saida 0:")
        for c in duvidosas:
            print(f"  {c['source']} -> {c['target']}[{c.get('target_input_index')}]")
    print("escrito:", sys.argv[2])


if __name__ == "__main__":
    main()
