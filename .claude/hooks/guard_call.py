"""Hook PreToolUse: impoe as regras que texto de skill nao conseguiu impor.

Tres regras, todas derivadas de falha medida (ver NOTAS.md):

1. Python sem consulta de docs. Na rodada 3-bis o agente inventou
   `Rhino.FileIO.FileSaveOptions` e perdeu o arquivo inteiro. O servidor oferece
   `get_rhinoscript_docs`; a skill manda consultar e o agente nao consultou.
   Aqui vira condicao: sem consulta na sessao, a chamada nao sai.

2. Boolean sem dry_run. Os tres booleanos aceitam simulacao e nenhuma das 217
   chamadas registradas usou. A 3-bis falhou justamente num boolean difference.

3. Orcamento de tool calls. A skill diz "pare aos 25 e reporte"; as rodadas
   gastaram 45, 25 e 68. O orcamento vem de `logs/_rodada_atual.json`, escrito
   pelo runner; sem esse arquivo a regra fica desligada (uso interativo).

O estado da sessao e' lido de `logs/rhino_calls.jsonl`, que o `log_call.py`
alimenta no PostToolUse. As duas pecas dependem uma da outra: se o log parar, a
contagem para junto.

Contrato do hook: payload JSON no stdin, decisao JSON no stdout, exit 0.
Negar aqui devolve o motivo ao agente, que pode corrigir e chamar de novo -- nao
mata a sessao.
"""

import json
import pathlib
import sys

DOCS_TOOL = "mcp__rhino__get_rhinoscript_docs"
PYTHON_TOOL = "mcp__rhino__execute_rhinoscript_python_code"
BOOLEAN_TOOLS = (
    "mcp__rhino__boolean_difference",
    "mcp__rhino__boolean_intersection",
    "mcp__rhino__boolean_union",
)


def allow():
    """Silencio = seguir o fluxo normal de permissao do Claude Code."""
    sys.exit(0)


def deny(motivo):
    json.dump({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": motivo,
        }
    }, sys.stdout)
    sys.exit(0)


def chamadas_da_sessao(raiz, session_id):
    """As chamadas ja concluidas nesta sessao, em ordem. Log ausente = lista vazia."""
    log = raiz / "logs" / "rhino_calls.jsonl"
    if not log.exists():
        return []
    registros = []
    with log.open(encoding="utf-8") as f:
        for linha in f:
            linha = linha.strip()
            if not linha:
                continue
            try:
                reg = json.loads(linha)
            except json.JSONDecodeError:
                continue  # linha truncada por escrita concorrente: ignora
            if reg.get("session_id") == session_id:
                registros.append(reg)
    return registros


def orcamento(raiz):
    """max_tool_calls da rodada em curso, ou None em uso interativo."""
    marcador = raiz / "logs" / "_rodada_atual.json"
    if not marcador.exists():
        return None
    try:
        return json.loads(marcador.read_text(encoding="utf-8")).get("max_tool_calls")
    except (json.JSONDecodeError, OSError):
        return None


def main():
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        allow()  # payload ilegivel nao e' motivo para travar o agente

    tool = payload.get("tool_name", "")
    if not tool.startswith("mcp__rhino__"):
        allow()

    entrada = payload.get("tool_input") or {}
    raiz = pathlib.Path(payload.get("cwd") or ".")
    anteriores = chamadas_da_sessao(raiz, payload.get("session_id"))

    limite = orcamento(raiz)
    if limite is not None and len(anteriores) >= limite:
        deny(
            f"Orcamento de {limite} tool calls esgotado ({len(anteriores)} ja "
            "gastas nesta rodada). Pare de construir e reporte o estado atual: o "
            "que existe no documento, o que falta, e o desvio medido. Nao tente "
            "outra rota."
        )

    if tool == PYTHON_TOOL:
        if not any(r.get("tool_name") == DOCS_TOOL for r in anteriores):
            deny(
                "Script Python sem consulta previa de documentacao. Chame "
                "`get_rhinoscript_docs` para as funcoes que voce pretende usar e "
                "so' entao escreva o script. Antes disso, prefira uma tool nativa: "
                "a lista completa esta em references/mcp-superficie.md."
            )

    if tool in BOOLEAN_TOOLS:
        if not entrada.get("dry_run"):
            mesma_tool = [r for r in anteriores if r.get("tool_name") == tool]
            simulou = mesma_tool and (mesma_tool[-1].get("tool_input") or {}).get("dry_run")
            if not simulou:
                deny(
                    f"`{tool.removeprefix('mcp__rhino__')}` sem simulacao. Repita a "
                    "chamada com `dry_run: true`, leia o resultado, e so' entao "
                    "aplique de verdade."
                )

    allow()


if __name__ == "__main__":
    main()
