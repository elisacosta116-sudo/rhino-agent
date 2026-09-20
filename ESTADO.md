# ESTADO — onde paramos

> **Atualize este arquivo ao fim de toda sessão.** É o primeiro que se lê ao voltar.
> Formato fixo: não cresça o documento, substitua o conteúdo. Histórico fica em `NOTAS.md`.

**Última sessão:** 20/09/2026

---

## Próxima ação

**Rodar a `harness v2, rodada 1`** — o caso `balcao_01` com Sonnet, com a percepção do servidor ligada.

```
cd C:\Users\eacosta\dev\rhino-agent
uv run --with rhino3dm python evals/rodada.py balcao_01 --model sonnet --rodada "v2r1"
```

Antes: Rhino 8 aberto, documento **NOVO** em mm, `mcpstart` confirmado.

**Uma variável só.** A única mudança em relação ao último commit é `RHINO_MCP_PERCEPTION=1` no `.mcp.json`. A skill está intocada em `200f2e5`; o `settings.json` do operador não foi alterado.

⚠️ **A baseline antiga não é comparável.** As rodadas 1–4 rodaram sem percepção; agora o modelo vê `_health` e `_delta` no retorno de toda mutação. Taxa de aprovação entre as séries não se compara. O que se compara é o veredito do caso, que não mudou. Detalhe em `NOTAS.md`, seção "Harness v2".

---

## Estado do harness

| Peça | Estado | Onde |
|---|---|---|
| Modelo do agente | `claude-haiku-4-5-20251001` no arquivo — **use `--model sonnet` na chamada** | `.claude/settings.json` |
| Percepção do servidor | **ligada** — `_health` e `_delta` em toda mutação | `.mcp.json` |
| Rota C# | **aberta** — proposta de fechar foi analisada e **rejeitada** | — |
| Hook de log | ativo | `.claude/hooks/log_call.py` |
| Hook de guarda | escrito e testado, **inerte** — não registrado, por decisão | `.claude/hooks/guard_call.py` |
| Runner de rodada | pronto, não exercitado ponta a ponta | `evals/rodada.py` |
| `check.py` | corrigido em 19/09; 2 lacunas abertas | `evals/check.py` |
| Skill | `200f2e5`, intocada | `.claude/skills/rhino-nurbs/` |

**Marco do log:** `logs/rhino_calls.jsonl` tem **217 linhas**. O runner faz essa conta sozinho.

---

## Em voo

- **harness v2, rodada 1** — preparada, não executada. Precisa do Rhino aberto e de você presente.

## Fechado nesta sessão

- Documentação operacional: `TUTORIAL.md`, `ESTADO.md`, `OPERACAO.md`, `../README.md`, `../supervisor/PROMPTS.md`; `HARNESS.md` com as camadas de defesa e corpus.
- `supervisor/` virou repositório git, com cópia rastreada das travas de `dev/.claude/settings.json`.
- Runner `evals/rodada.py` e hook `guard_call.py` (este último inerte).
- **Análise que reprovou o bloqueio do C#** e corrigiu o registro sobre a tool tipada de arco — em `NOTAS.md`.

---

## Roteiro, em ordem

1. **harness v2, rodada 1** — percepção ligada, uma variável. *(próxima ação)*
2. **Rodada tipada** — uma rodada que tente a rota tipada até o fim (`create_object type=ARC` → `offset_curve` → fechar o perfil), para descobrir se `create_planar_region` dispensa o join que não existe tipado. É o que decide se a rota C# é necessária ou apenas conveniente.
3. **Capturar os 5 tópicos de guidance que faltam** (`transforms`, `planar_regions`, `organization`, `verification`, `recovery`). Exige Rhino aberto; procedimento em `references/guidance/README.md`. O `verification` nunca foi lido em 217 chamadas.
4. **Candidata nº 7** — obrigar o save.
5. **Fechar as 2 lacunas do `check.py`** — escolha do Brep alvo e arquivo sem malha de render. Trabalho de mesa. Ao mudar o instrumento, re-medir o histórico inteiro.
6. **Escrever os 29 casos de eval restantes** — pré-requisito do piloto.
7. **Construir os 4 primeiros templates `.gh`** — balcão, arco, painel, totem.
8. **Medir os dois números da seção 1 do PRD** — tempo por proposta e variações por cliente.

## Riscos abertos

- **`dev/.claude/settings.json` não está sob controle de versão.** É o que impede o supervisor de mexer nas travas do operador. Há cópia rastreada em `supervisor/travas-do-supervisor.json`; re-copie ao mudar.
- **O `guard_call.py` tem dois defeitos conhecidos** antes de qualquer reconsideração: falha fechada se o log ficar sem escrita, e lê o log inteiro a cada chamada (1,37 MB hoje, por causa dos PNG em base64 do `capture_viewport`).
- **1 caso de eval de 30.** Uma aprovação não é taxa de aprovação — e agora a série recomeçou do zero.
- **O runner nunca rodou ponta a ponta.** A primeira execução é também o teste dele; se algo quebrar, pode ser o runner e não o agente.
