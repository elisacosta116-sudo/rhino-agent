[README.md](https://github.com/user-attachments/files/32484653/README.md)
# Estandes Paramétricos Orgânicos — agentes do Rhino

Sistema que transforma um briefing em português em geometria NURBS verificada no Rhino 8. Em desenvolvimento, medido por evals, ainda longe do piloto.

> **Nunca crie um `CLAUDE.md` neste diretório nem acima dele.** O Claude Code carrega os `CLAUDE.md` dos diretórios pais; um arquivo aqui é herdado pelo agente que roda em `rhino-agent/` e sobrescreve o papel dele. Já anulou uma rodada inteira.

## Por onde começar

| Se você quer | Vá para |
|---|---|
| **retomar o trabalho** | `rhino-agent/ESTADO.md` — onde paramos e qual é a próxima ação |
| aprender a operar do zero | `rhino-agent/TUTORIAL.md` |
| os comandos do dia-a-dia | `rhino-agent/OPERACAO.md` |
| os textos para colar no supervisor | `supervisor/PROMPTS.md` |
| saber o que já aconteceu | `rhino-agent/NOTAS.md` |
| entender por que o harness é assim | `rhino-agent/HARNESS.md` |
| o produto: problema, métrica, escopo, riscos | [PRD — Estandes Paramétricos Orgânicos](https://claude.ai/code/artifact/945c62b2-e480-4b6b-b464-ee1ea9716f78) |

## Estrutura

```
dev/
├── .claude/settings.json   travas do supervisor (nega editar o settings do operador)
├── rhino-agent/            O OPERADOR — modela, fala com o Rhino. Repositório git.
│   ├── .claude/            skill, permissões, hooks (log e guarda)
│   ├── evals/              check.py (fonte de verdade), rodada.py (runner), cases.jsonl
│   ├── references/         corpus que o agente consulta para não inventar API
│   ├── gh-templates/       templates Grasshopper parametrizados (vazio — pendente)
│   ├── logs/               toda chamada MCP registrada (fora do git)
│   └── output/             .3dm gerados, com _rodadas/ para os arquivados (fora do git)
└── supervisor/             O SUPERVISOR — desenvolve e mede o operador. Nunca modela.
```

Os dois são pastas **irmãs**, nunca aninhadas — é o que mantém o papel de cada um isolado. O detalhe e a história estão em `rhino-agent/TUTORIAL.md` §1.

## Estado em uma linha

Rodada 4 (Sonnet 5) passou: bbox 2400 × 829,4 × 1100 mm, 9 tool calls, US$ 0,25. É **1 aprovação em 4 rodadas válidas, sobre 1 caso de eval de 30** — o problema é solúvel, e isso ainda não é uma taxa de aprovação. Próximo passo em `rhino-agent/ESTADO.md`.

## Pré-requisitos

Rhino 8 com o plugin `rhinomcp` (liga com `mcpstart` dentro do Rhino), `uv`, e o Claude Code. O servidor MCP sobe sozinho com a sessão, via `uvx rhinomcp`.
