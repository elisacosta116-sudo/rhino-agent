"""Executa uma rodada de eval inteira e devolve um veredito medido.

  uv run --with rhino3dm python evals/rodada.py balcao_01 --model sonnet

Substitui os seis passos manuais do protocolo. Existe porque tres dos erros ja
pagos foram de procedimento, nao de modelo:

  - a rodada 2 sobrescreveu o arquivo da rodada 1, que sobreviveu so' como .3dmbak;
  - a rodada 3 rendeu 0 tool calls e foi lida como falha do modelo antes de se
    descobrir que era contaminacao de contexto -- rodada anulada nao e' reprovacao;
  - a 3-bis declarou um arquivo que nao existia no disco.

Ordem: arquiva o que existe -> marca o log -> roda o agente -> VALIDA SE FOI
RODADA -> acha o arquivo novo -> mede com check.py -> registra no caso.

A fonte de verdade continua sendo `evals/check.py`, chamado por subprocesso. Este
script nao mede geometria; so' cuida para que a medicao aconteca sobre o arquivo
certo e que o resultado nao se perca.
"""

import argparse
import datetime
import io
import json
import pathlib
import shutil
import subprocess
import sys

# O stdout do console no Windows e' cp1252 e estoura em qualquer caractere fora
# dele. O relatorio do agente vem cheio deles (checkmarks, acentos, setas), e a
# rodada v2r1 morreu num '✓' DEPOIS de ja ter o veredito -- perdendo o
# relatorio inteiro, que e' metade do valor da rodada.
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

RAIZ = pathlib.Path(__file__).resolve().parent.parent
CASOS = RAIZ / "evals" / "cases.jsonl"
CHECK = RAIZ / "evals" / "check.py"
LOG = RAIZ / "logs" / "rhino_calls.jsonl"
MARCADOR = RAIZ / "logs" / "_rodada_atual.json"
SAIDA = RAIZ / "output"
ARQUIVO_MORTO = SAIDA / "_rodadas"


def linhas_do_log():
    if not LOG.exists():
        return 0
    with LOG.open(encoding="utf-8") as f:
        return sum(1 for linha in f if linha.strip())


def carrega_casos():
    casos = []
    with CASOS.open(encoding="utf-8") as f:
        for linha in f:
            linha = linha.strip()
            if linha:
                casos.append(json.loads(linha))
    return casos


def grava_casos(casos):
    with CASOS.open("w", encoding="utf-8", newline="\n") as f:
        for caso in casos:
            f.write(json.dumps(caso, ensure_ascii=False) + "\n")


def proxima_rodada(caso):
    """Maior numero de rodada ja registrado + 1. Ignora rotulos tipo '3-bis'."""
    numeros = []
    for reg in caso.get("historico", []):
        try:
            numeros.append(int(reg.get("rodada")))
        except (TypeError, ValueError):
            continue
    return max(numeros, default=0) + 1


def arquiva_saidas(rotulo):
    """Copia (nao move) os .3dm atuais para _rodadas/. O agente reusa nomes."""
    ARQUIVO_MORTO.mkdir(parents=True, exist_ok=True)
    arquivados = []
    for arq in sorted(SAIDA.glob("*.3dm")):
        destino = ARQUIVO_MORTO / f"pre_r{rotulo}_{arq.name}"
        if destino.exists():
            continue  # ja arquivado numa tentativa anterior desta mesma rodada
        shutil.copy2(arq, destino)
        arquivados.append(destino.name)
    return arquivados


def estado_das_saidas():
    return {arq.name: arq.stat().st_mtime for arq in SAIDA.glob("*.3dm")}


def arquivo_novo(antes, depois):
    """O .3dm criado ou reescrito durante a rodada, o mais recente se houver varios."""
    mudados = [
        nome for nome, mtime in depois.items()
        if nome not in antes or mtime > antes[nome]
    ]
    if not mudados:
        return None
    return max(mudados, key=lambda nome: depois[nome])


def roda_agente(prompt, modelo, timeout):
    exe = shutil.which("claude") or "claude"
    cmd = [exe, "-p", prompt, "--output-format", "json"]
    if modelo:
        cmd += ["--model", modelo]
    proc = subprocess.run(
        cmd, cwd=RAIZ, capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=timeout,
    )
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        return {
            "_erro": "saida do claude nao e' JSON",
            "_stdout": proc.stdout[:2000],
            "_stderr": proc.stderr[:2000],
            "_returncode": proc.returncode,
        }


def mede(arquivo, check):
    cmd = [sys.executable, str(CHECK), str(arquivo), "--tol", str(check.get("tol", 0.01))]
    # Caso de medida usa bbox_mm (igualdade). Caso de envelope -- tipico de forma
    # organica, onde o briefing da' um teto e nao um alvo -- usa bbox_max/bbox_min.
    # Os tres podem coexistir: alvo num eixo, teto noutro.
    if check.get("bbox_mm"):
        cmd += ["--bbox", *[str(v) for v in check["bbox_mm"]]]
    if check.get("bbox_max_mm"):
        cmd += ["--bbox-max", *[str(v) for v in check["bbox_max_mm"]]]
    if check.get("bbox_min_mm"):
        cmd += ["--bbox-min", *[str(v) for v in check["bbox_min_mm"]]]
    if check.get("layer"):
        cmd += ["--layer", check["layer"]]
    # is_solid ausente no caso = nao verificar. Casca, vela e membrana sao
    # superficies abertas por definicao e precisam poder declarar isso.
    if "is_solid" in check:
        cmd += ["--solido", "fechado" if check["is_solid"] else "aberto"]
    else:
        cmd += ["--solido", "qualquer"]
    if check.get("volume_mm3"):
        cmd += ["--volume", str(check["volume_mm3"])]
    proc = subprocess.run(
        cmd, cwd=RAIZ, capture_output=True, text=True,
        encoding="utf-8", errors="replace",
    )
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        return {"veredito": "FALHOU", "erro": "check.py nao devolveu JSON",
                "stdout": proc.stdout[:1000], "stderr": proc.stderr[:1000]}


def julga_recusa(caso, arquivo_novo_nome, relato):
    """Veredito de um caso de tier borda, onde o acerto e' NAO produzir geometria.

    Aqui o instrumento e' estruturalmente mais fraco que nos casos de medida. Um
    .3dm se mede; uma recusa correta e' texto, e texto nao se verifica por codigo
    com o mesmo rigor. O projeto ja pagou caro por instrumento com vies (ver o
    aviso no topo de NOTAS.md), entao a regra aqui e': **so' aprova o que da'
    para checar mecanicamente; o resto vira INCONCLUSIVO, nunca aprovacao.**

      FALHOU        produziu artefato num caso que pedia recusa. Mecanico e certo.
      PASSOU        sem artefato E o relato traz um dos sinais declarados no caso.
      INCONCLUSIVO  sem artefato e sem sinal: parou, mas nao da' para dizer se
                    recusou com criterio ou so' desistiu. Exige leitura humana.

    `sinais_de_recusa` vem do proprio caso, nao de uma lista global: o que conta
    como recusa correta muda com o caso (dimensao impossivel, pedido ambiguo,
    topologia fora do catalogo). Comparacao sem acento e sem caixa, porque o
    relato varia na forma e nao no conteudo.
    """
    if arquivo_novo_nome:
        return ("FALHOU",
                f"produziu output/{arquivo_novo_nome} num caso que pede recusa",
                None)

    sinais = caso.get("sinais_de_recusa") or []
    plano = _sem_acento(relato)
    for s in sinais:
        if _sem_acento(s) in plano:
            return ("PASSOU", f"recusou e sinalizou: {s!r}", s)

    if not sinais:
        return ("INCONCLUSIVO",
                "o caso nao declara `sinais_de_recusa` — sem criterio para julgar",
                None)
    return ("INCONCLUSIVO",
            "nao criou artefato, mas o relato nao traz nenhum sinal de recusa "
            f"declarado ({len(sinais)} procurados) — pode ter desistido em vez "
            "de recusar. Leia o relato abaixo.",
            None)


def _sem_acento(s):
    import unicodedata
    return "".join(
        c for c in unicodedata.normalize("NFD", s.lower())
        if unicodedata.category(c) != "Mn"
    )


def bloco_notas(reg, caso):
    """Markdown pronto para colar em NOTAS.md. Escrever a mao e' onde se perde registro."""
    med = reg.get("medido") or {}
    linhas = [
        f"## Rodada {reg['rodada']}",
        "",
        f"- **Modelo:** {reg['modelo']} · **Sessao:** `{reg.get('sessao') or '?'}`",
        f"- **Tool calls:** {reg['tool_calls_mcp']} (orcamento {caso['check'].get('max_tool_calls', '-')})",
        f"- **Turnos:** {reg.get('num_turns')} · **{reg.get('duration_ms', 0) / 1000:.1f} s** · "
        f"**US$ {reg.get('custo_usd') or 0:.4f}**",
        f"- **Arquivo:** `{reg.get('artefato') or 'NENHUM'}`",
        f"- **Veredito: {reg['resultado']}**",
    ]
    if med.get("bbox"):
        linhas.append(
            f"- **Medido:** bbox {med['bbox']} ({med.get('bbox_fonte')}), "
            f"IsSolid {med.get('is_solid')}, camada `{med.get('camada')}`, "
            f"{reg.get('objetos_no_arquivo')} objeto(s)"
        )
    for f in reg.get("falhas") or []:
        linhas.append(f"  - FALHA: {f}")
    for i in reg.get("inconclusivos") or []:
        linhas.append(f"  - INCONCLUSIVO: {i}")
    for a in reg.get("avisos") or []:
        linhas.append(f"  - aviso: {a}")
    linhas += ["", "- **Relato do agente vs medido:** _preencher a mao lendo o "
               "relatorio do agente acima._", "- **Hipotese de causa:** _preencher._"]
    return "\n".join(linhas)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("caso_id")
    ap.add_argument("--model", default=None, help="passado a `claude --model`")
    ap.add_argument("--rodada", default=None, help="rotulo da rodada (default: proximo numero)")
    ap.add_argument("--timeout", type=int, default=1800)
    ap.add_argument("--dry-run", action="store_true",
                    help="roda e mede, mas nao escreve em cases.jsonl")
    a = ap.parse_args()

    casos = carrega_casos()
    alvo = next((c for c in casos if c["id"] == a.caso_id), None)
    if alvo is None:
        sys.exit(f"caso '{a.caso_id}' nao esta em {CASOS}")

    rotulo = a.rodada or str(proxima_rodada(alvo))
    check = alvo["check"]

    print(f"== rodada {rotulo} · caso {alvo['id']} · modelo {a.model or '(settings.json)'}")
    arquivados = arquiva_saidas(rotulo)
    print(f"-- arquivados em output/_rodadas/: {len(arquivados)}")

    marco = linhas_do_log()
    antes = estado_das_saidas()
    MARCADOR.parent.mkdir(exist_ok=True)
    MARCADOR.write_text(json.dumps({
        "caso": alvo["id"], "rodada": rotulo,
        "max_tool_calls": check.get("max_tool_calls"),
        "iniciada_em": datetime.datetime.now().isoformat(),
    }), encoding="utf-8")
    print(f"-- log em {marco} linhas · orcamento {check.get('max_tool_calls')}")

    try:
        print("-- rodando o agente...")
        try:
            r = roda_agente(alvo["prompt"], a.model, a.timeout)
        except subprocess.TimeoutExpired:
            sys.exit(f"TIMEOUT: o agente passou de {a.timeout}s. Rodada nao concluida.")
    finally:
        MARCADOR.unlink(missing_ok=True)

    if "_erro" in r:
        print(json.dumps(r, ensure_ascii=False, indent=2))
        sys.exit("o `claude` nao devolveu JSON: rodada nao avaliavel")

    tool_calls = linhas_do_log() - marco
    num_turns = r.get("num_turns")
    print(f"-- turnos {num_turns} · tool calls MCP {tool_calls} · "
          f"{r.get('duration_ms', 0) / 1000:.1f}s · US$ {r.get('total_cost_usd') or 0:.4f}")

    # Passo 4 do protocolo: validar se foi rodada, ANTES de ler qualquer resultado.
    if tool_calls == 0 or (num_turns or 0) <= 1:
        print("\n" + "=" * 62)
        print("ANULADA — o agente nao tocou no Rhino.")
        print("Nao e' falha do modelo. Causas conhecidas, em ordem de frequencia:")
        print("  1. Rhino fechado ou `mcpstart` nao confirmado.")
        print("  2. CLAUDE.md em diretorio pai contaminando o papel do agente")
        print("     (foi o que anulou a rodada 3) — confira que nao ha CLAUDE.md")
        print("     em dev/ nem acima.")
        print("  3. O agente parou para perguntar algo e ficou esperando.")
        print("=" * 62)
        print("\nResposta do agente:\n" + (r.get("result") or "")[:1500])
        sys.exit(2)

    depois = estado_das_saidas()
    novo = arquivo_novo(antes, depois)

    if alvo.get("espera_recusa"):
        veredito_r, motivo, sinal = julga_recusa(alvo, novo, r.get("result") or "")
        print("\n" + "=" * 62)
        print(f"{veredito_r} — caso de recusa. {motivo}")
        print("=" * 62)
        registro = {
            "rodada": int(rotulo) if rotulo.isdigit() else rotulo,
            "modelo": a.model or "(settings.json)",
            "sessao": (r.get("session_id") or "")[:8],
            "tipo": "recusa",
            "resultado": veredito_r,
            "motivo_do_veredito": motivo,
            "sinal_encontrado": sinal,
            "artefato": f"output/{novo}" if novo else None,
            "tool_calls_mcp": tool_calls,
            "num_turns": num_turns,
            "duration_ms": r.get("duration_ms"),
            "custo_usd": r.get("total_cost_usd"),
            "medido_em": datetime.datetime.now().isoformat(),
        }
        print("\n" + "-" * 62)
        print("RELATO DO AGENTE — leia antes de aceitar o veredito")
        print("-" * 62)
        print(r.get("result") or "(o agente nao devolveu texto)")
        if a.dry_run:
            print("\n-- --dry-run: cases.jsonl nao foi alterado")
        else:
            alvo.setdefault("historico", []).append(registro)
            grava_casos(casos)
            print(f"\n-- registrado no historico de '{alvo['id']}'")
        sys.exit(0 if veredito_r == "PASSOU" else 1)

    if novo is None:
        print("\n" + "=" * 62)
        print("FALHOU — rodada valida, mas nenhum .3dm novo em output/.")
        print("Sem artefato nao ha entrega, independente do que o agente relatou.")
        print("Precedentes: a 3-bis declarou um v3.3dm inexistente; a rodada 4")
        print("entregou peca correta e nao salvou.")
        print("=" * 62)
        print("\nResposta do agente:\n" + (r.get("result") or "")[:1500])
        sys.exit(1)

    print(f"-- arquivo novo: output/{novo}")
    print("-- medindo com check.py (fonte de verdade)...")
    m = mede(SAIDA / novo, check)
    alvo_medido = m.get("objeto") or {}

    registro = {
        "rodada": int(rotulo) if rotulo.isdigit() else rotulo,
        "modelo": a.model or "(settings.json)",
        "sessao": (r.get("session_id") or "")[:8],
        "resultado": m.get("veredito"),
        "medido": {
            "bbox": alvo_medido.get("bbox"),
            "bbox_fonte": alvo_medido.get("bbox_fonte"),
            "volume": alvo_medido.get("volume"),
            "is_valid": alvo_medido.get("is_valid"),
            "is_solid": alvo_medido.get("is_solid"),
            "camada": alvo_medido.get("camada"),
        },
        "objetos_no_arquivo": m.get("objetos_no_arquivo"),
        "falhas": m.get("falhas"),
        "inconclusivos": m.get("inconclusivos"),
        "avisos": m.get("avisos"),
        "tool_calls_mcp": tool_calls,
        "num_turns": num_turns,
        "duration_ms": r.get("duration_ms"),
        "custo_usd": r.get("total_cost_usd"),
        "artefato": f"output/{novo}",
        "medido_em": datetime.datetime.now().isoformat(),
    }

    print("\n" + json.dumps(m, ensure_ascii=False, indent=2))

    # O relato do agente e' metade do valor da rodada: a coluna "relato vs
    # medido" e' o que separou erro de medicao de erro de julgamento em toda a
    # serie. Ate a v2r2 ele so' era impresso quando a rodada falhava, e tinha
    # que ser pescado do transcript a mao.
    print("\n" + "-" * 62)
    print("RELATO DO AGENTE (compare com o medido acima)")
    print("-" * 62)
    print(r.get("result") or "(o agente nao devolveu texto)")

    if a.dry_run:
        print("\n-- --dry-run: cases.jsonl nao foi alterado")
    else:
        alvo.setdefault("historico", []).append(registro)
        grava_casos(casos)
        print(f"\n-- registrado no historico de '{alvo['id']}' em evals/cases.jsonl")

    print("\n" + "-" * 62)
    print("Cole em NOTAS.md e complete as duas ultimas linhas a mao:")
    print("-" * 62 + "\n")
    print(bloco_notas(registro, alvo))

    sys.exit(0 if m.get("veredito") == "PASSOU" else 1)


if __name__ == "__main__":
    main()
