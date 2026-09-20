"""Regenera references/mcp-superficie.md a partir do log de chamadas MCP.

A superficie do rhinomcp muda entre versoes. Este script le a resposta mais
recente de describe_capabilities registrada em logs/rhino_calls.jsonl e
reescreve o arquivo de referencia, para o corpus nao envelhecer junto com o
servidor.

  uv run --no-project python evals/dump_capabilities.py

Se o servidor for atualizado, basta uma chamada nova a describe_capabilities
numa rodada qualquer: o log passa a conter a resposta nova e o script a usa.
"""

import json
import pathlib
import sys

RAIZ = pathlib.Path(__file__).resolve().parent.parent
LOG = RAIZ / "logs" / "rhino_calls.jsonl"
SAIDA = RAIZ / "references" / "mcp-superficie.md"


def ultima_resposta(nome_tool):
    """Ultima tool_response registrada para uma tool, ja decodificada."""
    achado = None
    with LOG.open(encoding="utf-8") as f:
        for linha in f:
            linha = linha.strip()
            if not linha:
                continue
            reg = json.loads(linha)
            if reg.get("tool_name") == nome_tool:
                achado = reg.get("tool_response")
    if achado is None:
        return None
    if isinstance(achado, str):
        achado = json.loads(achado)
    return achado.get("result", achado)


def tabela(comandos):
    linhas = ["| Comando | Somente leitura | dry_run |", "| --- | --- | --- |"]
    for c in sorted(comandos, key=lambda x: x["name"]):
        ro = "sim" if c.get("read_only") else "-"
        dr = "sim" if c.get("supports_dry_run") else "-"
        linhas.append(f"| `{c['name']}` | {ro} | {dr} |")
    return "\n".join(linhas)


def main():
    cap = ultima_resposta("mcp__rhino__describe_capabilities")
    if cap is None:
        print("describe_capabilities nao encontrado em", LOG, file=sys.stderr)
        print("Rode uma sessao que chame describe_capabilities e tente de novo.", file=sys.stderr)
        return 1

    cmds = cap["commands"]
    gh = [c for c in cmds if c["name"].startswith("gh_")]
    rh = [c for c in cmds if not c["name"].startswith("gh_")]

    perc = cap.get("perception", {})
    flags = perc.get("envelope_flags", [])
    bloco_flags = "\n".join(
        f"- **`{f['flag']}`** — anexa `{f['attaches']}`. {f['description']}" for f in flags
    ) or "- (nenhuma flag reportada por esta versao)"

    texto = f"""# Superficie do MCP `rhino` (rhinomcp {cap.get('version')})

> Gerado por `evals/dump_capabilities.py` a partir de `logs/rhino_calls.jsonl`.
> Nao edite a mao: rode o script de novo.

**{cap.get('command_count')} comandos** — {len(rh)} do Rhino, {len(gh)} do Grasshopper.

Nunca invente nome de tool nem assinatura de metodo. Se nao esta nesta lista,
nao existe. Para scripts em Python, consulte `get_rhinoscript_docs` antes de
escrever. **Nao existe consulta equivalente para C#** — ver `references/rhinocommon.md`.

> **Esta lista diz o que existe, nao como cada tool se comporta.** Comportamentos
> que a descricao das tools nao conta e que ja produziram falha medida estao em
> `references/armadilhas-mcp.md` — entre eles uma tool de camada que falha em
> silencio. Leia antes de confiar no retorno de qualquer chamada.

## Verificacao embutida (envelope de percepcao)

{perc.get('description', '')}

{bloco_flags}

Os tres booleanos aceitam `dry_run`: simule antes de aplicar.

## Rhino ({len(rh)})

{tabela(rh)}

## Grasshopper ({len(gh)})

{tabela(gh)}
"""

    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    SAIDA.write_text(texto, encoding="utf-8")
    print(f"escrito: {SAIDA.relative_to(RAIZ)} ({cap.get('command_count')} comandos)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
