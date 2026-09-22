# -*- coding: utf-8 -*-
"""Hook de log: grava cada chamada ao MCP do Rhino em logs/rhino_calls.jsonl.

Registrado em DOIS eventos, e os dois importam:

  PreToolUse    a TENTATIVA. Dispara sempre -- inclusive quando a chamada vai
                falhar, ou ser negada por permissao.
  PostToolUse   o RESULTADO. So dispara quando a tool retorna com sucesso.

Ate 22/09 so o PostToolUse estava registrado, e o log era CEGO a chamada que
falha: na sondagem daquele dia, o `gh_build_graph` que errou nao apareceu no
log; o que teve sucesso, apareceu. Como a contagem de chamadas e' criterio de
todo caso de eval, o numero comparado com o orcamento era LIMITE INFERIOR, nao
valor. E o que ficava escondido era justamente o modo de falha mais
interessante: tentar, errar, tentar de novo.

Tentativa sem resultado de mesmo `tool_use_id` E' a chamada que falhou -- nao
so o numero certo, mas QUAL falhou e com que tool. Quem faz a conta e' o
`evals/rodada.py`, funcao `conta_chamadas()`.

FALHA ABERTA, e isto nao e' negociavel
--------------------------------------
Em PreToolUse, sair com codigo != 0 BLOQUEIA a chamada. Um logger que derruba a
chamada que deveria medir inverte o instrumento: a rodada passaria a medir o
hook, e nao o agente -- e falharia do jeito mais caro, parecendo resultado do
modelo. Por isso tudo aqui esta em try/except e o processo sai com 0 sempre.

Perder uma linha de log e' barato. Negar uma tool call e' fabricar resultado.

E' exatamente a diferenca entre este hook e o `guard_call.py`, que falha FECHADO
-- e e' por isso que aquele segue inerte, sem registro, por decisao.

Nada e' escrito em stdout nem em stderr: em PreToolUse, o que o hook imprime
pode entrar no contexto do agente, e o contexto do agente e' variavel do eval.
"""
import sys


def registra():
    import json
    import datetime
    import pathlib

    payload = json.load(sys.stdin)
    payload["logged_at"] = datetime.datetime.now().isoformat()
    log = pathlib.Path("logs") / "rhino_calls.jsonl"
    log.parent.mkdir(exist_ok=True)
    with log.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")


try:
    registra()
except Exception:
    pass

sys.exit(0)
