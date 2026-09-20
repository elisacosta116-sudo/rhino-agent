# ESTADO — onde paramos

> **Atualize este arquivo ao fim de toda sessão.** É o primeiro que se lê ao voltar.
> Formato fixo: não cresça o documento, substitua o conteúdo. Histórico fica em `NOTAS.md`.

**Última sessão:** 20/09/2026

---

## Próxima ação

**Parar de mexer na skill e ampliar o dataset.** A fila de candidatas ficou sem item de evidência forte, e as três últimas rodadas mostram por quê: **o `balcao_01` já é resolvido, e um caso só não distingue regra de acaso.**

~~**1. Consertar o instrumento para o tier de borda.**~~ **Feito.** `espera_recusa` + `sinais_de_recusa` no caso, julgados por `julga_recusa()` em `evals/rodada.py`. Cinco ramificações testadas; desistir cai em `INCONCLUSIVO`, não em `PASSOU`. Primeiro caso escrito: `impossivel_01`, **ainda não rodado**.

**2. Escrever o tier fácil — 12 primitivas com volume analítico.** Caixa, cilindro, tubo, cunha, anel. É onde se descobre se o agente usa a superfície tipada sem cair em script, que é a aposta central da arquitetura do PRD. Rodar o lote responde também a pergunta que trava a candidata nº 12: se 25 tool calls é o número certo.

**3. Rodar `impossivel_01`** — exercita o instrumento novo numa rodada real e vale como primeiro dado do tier borda.

~~**Calibrar a tolerância dos casos curvos.**~~ **Feito na v2r5.** Facetamento de curvatura simples: 0,055%, contra os 2% que eu tinha arbitrado. Tolerância apertada para 0,5% em `cilindro_01`, `tubo_01`, `cone_01`, `calha_01` e `caixa_furo_01`. **`esfera_01` e `toro_01` ficam em 2%** — curvatura dupla faceta nas duas direções, ainda sem medição. Rodar um dos dois fecha a calibração.

⚠️ **A baseline anterior a 20/09 não é comparável.** As rodadas 1–4 rodaram sem percepção. Detalhe em `NOTAS.md`, seção "HARNESS v2".

## Placar da série harness v2

| Rodada | Caso | Variável testada | Veredito | Chamadas | Custo |
|---|---|---|---|---|---|
| v2r1 | `balcao_01` | percepção do servidor ligada | FALHOU — sem artefato (geometria passava) | 27 | US$ 0,53 |
| v2r2 | `balcao_01` | salvar vira passo 6 do fluxo | **PASSOU** | 36 | US$ 0,54 |
| v2r3 | `balcao_01` | prefixo de traço em `run_command` | **PASSOU** — sinal inconclusivo | 8 | US$ 0,22 |
| v2r4 | `prisma_hex_01` | estreia do tier fácil | **PASSOU** | 17 | US$ 0,27 |
| v2r5 | `cilindro_01` | calibra o facetamento da malha | **PASSOU** | 10 | US$ 0,17 |

**4 de 5, em 3 casos de 13 escritos.** Ainda não é taxa de aprovação: 10 casos nunca rodaram.

**Orçamento estourado em 3 de 5** (27/25, 36/25, 17/12). A v2r5 foi a primeira dentro do limite, e é também a mais barata — primitiva pura resolvida por tool tipada. O contraste com as 36 chamadas da v2r2 sugere que o custo alto vem da **composição** (arco + offset + join + extrusão), não da modelagem em si.

**Variância de rota, mesmo prompt e mesma skill:** v2r1 foi tipada, v2r2 misturou tudo, v2r3 fez um script só. Em nenhuma o agente seguiu a ordem de preferência declarada na skill.

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

- Nada. A skill está estável em `21a31ea` e as três últimas rodadas foram registradas.

## Fechado nesta sessão

- **`v2r3` PASSOU** com 8 tool calls, 44,9 s, US$ 0,2156 — a rodada mais barata e curta da série inteira. Mas o sinal da candidata nº 11 ficou **inconclusivo**: 1 de 1 com traço, amostra de uma chamada. O efeito observado foi o agente abandonar `run_command`, não usá-lo melhor.

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
