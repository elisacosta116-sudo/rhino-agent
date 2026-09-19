# Harness do agente Rhino — guia de configuração

O harness é tudo o que envolve o modelo: instruções persistentes, ferramentas, permissões, hooks, logs e evals. O modelo (Haiku 4.5) é a peça trocável; o harness é o que torna o comportamento previsível.

## Estrutura do projeto

```
rhino-agent/
├── CLAUDE.md                 # contexto persistente do projeto
├── .mcp.json                 # servidores MCP do projeto (gerado pelo `claude mcp add --scope project`)
├── .claude/
│   ├── settings.json         # modelo, permissões, hooks
│   ├── hooks/log_call.py     # logger das chamadas MCP
│   └── skills/
│       ├── rhino-nurbs/SKILL.md
│       └── prd-ia/SKILL.md
├── gh-templates/             # definições .gh parametrizadas (a rota preferida da skill)
├── evals/
│   ├── cases.jsonl           # casos de teste
│   └── run_evals.py
└── logs/
```

## CLAUDE.md (camada 1: contexto)

Seja curto: o Haiku segue instruções curtas e específicas melhor do que documentos longos. Um bom ponto de partida:

```markdown
# Projeto: agente NURBS
- Rhino 8 via MCP `rhino`. Unidade padrão: mm. Z vertical.
- Para qualquer geometria, siga a skill `rhino-nurbs` (inspecionar → construir → verificar → reportar).
- Rota preferida: templates em gh-templates/ > tools MCP > comandos Rhino > script curto.
- Nunca declare sucesso sem IsValid/IsSolid verificados.
- Arquivos de saída vão para ./output com sufixo _vN.
```

## settings.json (camadas 2 e 3: modelo e permissões)

```json
{
  "model": "claude-haiku-4-5-20251001",
  "permissions": {
    "allow": ["mcp__rhino", "Read", "Edit(./gh-templates/**)", "Edit(./evals/**)"],
    "deny": ["Bash(rm:*)", "Bash(curl:*)", "Read(./.env)"]
  },
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "mcp__rhino__.*",
        "hooks": [
          { "type": "command", "command": "uv run --no-project python .claude/hooks/log_call.py" }
        ]
      }
    ]
  }
}
```

O hook chama `.claude/hooks/log_call.py`, que grava toda chamada ao MCP do Rhino (entrada e resultado chegam via stdin em JSON). Ele é em Python, e não em shell, para funcionar igual no Windows e no Mac. Esse log é a matéria-prima dos evals: você vai descobrir quais tools falham, quantas chamadas cada pedido consome e onde o Haiku se perde.

O script cria `logs/` sozinho; crie `output/` antes do primeiro uso.

## Camada 4: evals

Sem evals, não dá para saber se uma mudança na skill melhorou ou piorou o agente. Formato mínimo de `evals/cases.jsonl`:

```json
{"id": "balcao_01", "prompt": "balcão curvo 2400mm corda, 1100 alto, 600 profundo", "check": {"is_solid": true, "bbox_mm": [2400, 900, 1100], "tol": 0.01}, "tier": "medio"}
```

Rode cada caso em modo headless (`claude -p "<prompt>" --output-format json`), consulte a geometria resultante pelo MCP e compare com o `check`. Registre a taxa de aprovação por tier, o número médio de tool calls e o custo. Monte 30 casos antes de mexer na skill; depois disso, toda alteração na skill passa pelo eval.

## Camada 5: portabilidade (se um dia virar plataforma)

O escopo atual é o servidor MCP local: uma instância do Rhino com interface, um documento, um cliente. Se o projeto evoluir para multiusuário, o backend passa a ser o Rhino.Compute (que roda no Windows 11 para desenvolvimento e exige Windows Server em produção). Três hábitos de agora evitam retrabalho depois:

- Mantenha a lógica geométrica nos templates `.gh` de `gh-templates/`. Eles rodam tanto no Rhino desktop quanto no Compute (via Hops/`compute.rhino3d`).
- Faça o LLM produzir **parâmetros** (JSON validado por schema), e não código. Execução de Python arbitrário num servidor multiusuário equivale a um RCE.
- Os evals de hoje viram o teste de regressão da plataforma.
