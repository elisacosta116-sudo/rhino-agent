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
import json
import pathlib
import shutil
import subprocess
import sys

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
    cmd = [
        sys.executable, str(CHECK), str(arquivo),
        "--bbox", *[str(v) for v in check["bbox_mm"]],
        "--tol", str(check.get("tol", 0.01)),
    ]
    if check.get("layer"):
        cmd += ["--layer", check["layer"]]
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
            f"{reg.get('breps_no_arquivo')} Brep(s)"
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
        "breps_no_arquivo": m.get("breps_no_arquivo"),
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
