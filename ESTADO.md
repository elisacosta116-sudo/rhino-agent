# ESTADO — onde paramos

> **Atualize este arquivo ao fim de toda sessão.** É o primeiro que se lê ao voltar.
> Formato fixo: não cresça o documento, substitua o conteúdo. Histórico fica em `NOTAS.md`.

**Última sessão:** 20/09/2026

---

## Próxima ação

**`v2r3` — candidata nº 11: a regra do prefixo de traço em `run_command`.** Diff da skill mostrado e aprovado antes de editar; uma variável só.

É a de maior evidência da fila e a única com risco de travar execução autônoma: na v2r2 um `_Arc` sem traço abriu comando interativo no Rhino, ficou pendurado, engoliu o `_-SaveAs` seguinte e **não pôde ser cancelado pelo MCP** — exigiu `Esc` humano. A regra existe em `references/rhinocommon.md` e nunca entrou na skill.

```
cd C:\Users\eacosta\dev\rhino-agent
uv run --with rhino3dm python evals/rodada.py balcao_01 --model sonnet --rodada "v2r3"
```

Antes: Rhino 8 aberto, documento **NOVO** em mm, `mcpstart` confirmado.

⚠️ **A baseline anterior a 20/09 não é comparável.** As rodadas 1–4 rodaram sem percepção. Detalhe em `NOTAS.md`, seção "HARNESS v2".

## Placar da série harness v2

| Rodada | Variável testada | Veredito |
|---|---|---|
| v2r1 | percepção do servidor ligada | FALHOU — sem artefato (geometria passava) |
| v2r2 | salvar vira passo 6 do fluxo | **PASSOU** |

**1 de 2.** Continua sendo 1 caso de eval de 30 — não é taxa de aprovação.

---

## Estado do harness

| Peça | Estado | Onde |
|---|---|---|
| Modelo do agente | `claude-haiku-4-5-20251001` no arquivo — **use `--model sonnet` na chamada** | `.claude/settings.json` |
| Percepção do servidor | **ligada**, mas cobertura estreita: 2 de 27 respostas na v2r1, nenhuma das tools de criação | `.mcp.json` |
| Rota C# | **aberta** — proposta de fechar foi analisada e **rejeitada** | — |
| Hook de log | ativo | `.claude/hooks/log_call.py` |
| Hook de guarda | escrito e testado, **inerte** — não registrado, por decisão | `.claude/hooks/guard_call.py` |
| Runner de rodada | pronto, não exercitado ponta a ponta | `evals/rodada.py` |
| `check.py` | corrigido em 19/09; 2 lacunas abertas | `evals/check.py` |
| Skill | `200f2e5`, intocada | `.claude/skills/rhino-nurbs/` |

**Marco do log:** `logs/rhino_calls.jsonl` tem **217 linhas**. O runner faz essa conta sozinho.

---

## Em voo

- **`v2r3`, candidata nº 11** — diff da skill ainda não escrito. Precisa da sua aprovação antes de editar.

## Fechado nesta sessão

- **`v2r2` PASSOU.** Primeira aprovação da série e **primeira vez que o agente salvou sozinho**, em 6 rodadas. `output/balcao_recepcao_v6.3dm`, 1 Brep, arquivo limpo. 36 tool calls, 162,9 s, US$ 0,5361.
- **A candidata nº 7 funcionou, e a causa foi posicional.** O mesmo texto ("salve em `./output` com sufixo `_vN`") estava na skill nas duas rodadas que não salvaram — o que mudou foi entrar na lista numerada do "fluxo obrigatório". Para este modelo, estrutura pesa mais que ênfase.
- **`harness v2, rodada 1` executada.** FALHOU por ausência de artefato; geometria medida `PASSOU` (bbox 2400,0 × 829,4 × 1100, volume 0,0035% de desvio, camada certa, 1 Brep). 27 tool calls, 129,8 s, US$ 0,5263.
- Três afirmações minhas corrigidas por medição: cobertura da percepção, existência de tool tipada de arco, e a necessidade de hook para forçar consulta de docs — o agente consultou sozinho.
- Defeito do runner corrigido: `UnicodeEncodeError` em stdout cp1252 engolia o relatório do agente.
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

- **Comando interativo do Rhino trava a sessão e o MCP não cancela.** Na v2r2 um `_Arc` sem prefixo de traço ficou pendurado com linha elástica no viewport, bloqueou o `run_command` seguinte e só saiu com `Esc` humano. **Numa rodada autônoma isso trava tudo a partir dali.** Candidata nº 11 ataca a causa; não há mitigação para o caso de acontecer mesmo assim.
- **Orçamento de tool calls nunca pegou:** 45 → 25 → 68 → 9 → 27 → 36. E a rodada aprovada gastou 36 contra um limite de 25 — não se sabe se a regra está sendo ignorada ou se o número está errado.

- **`dev/.claude/settings.json` não está sob controle de versão.** É o que impede o supervisor de mexer nas travas do operador. Há cópia rastreada em `supervisor/travas-do-supervisor.json`; re-copie ao mudar.
- **O `guard_call.py` tem dois defeitos conhecidos** antes de qualquer reconsideração: falha fechada se o log ficar sem escrita, e lê o log inteiro a cada chamada (1,37 MB hoje, por causa dos PNG em base64 do `capture_viewport`).
- **1 caso de eval de 30.** Uma aprovação não é taxa de aprovação — e agora a série recomeçou do zero.
- **O runner nunca rodou ponta a ponta.** A primeira execução é também o teste dele; se algo quebrar, pode ser o runner e não o agente.
