# ESTADO — onde paramos

> **Atualize este arquivo ao fim de toda sessão.** É o primeiro que se lê ao voltar.
> Formato fixo: não cresça o documento, substitua o conteúdo. Histórico fica em `NOTAS.md`.

**Última sessão:** 20/09/2026 — sessão longa, 6 rodadas + 2 sondagens + 1 template

---

## 🛑 Bloqueio arquitetural aberto: o Grasshopper não entrega geometria

O primeiro template foi construído (`gh-templates/balcao.json`, 21 componentes, 4 sliders) e **roda**: 0 erros, perfil fechado, `Cap Holes` produzindo sólido de 6 faces com as medidas certas. **Mas não há como trazer isso ao Rhino.**

As 27 tools `gh_*` montam, ligam, rodam e leem — e **nenhuma faz bake**. O `gh_get_parameter_value` devolve `{"type":"Brep","is_solid":true,"faces":6}`, descrição e não geometria. A rota C# não alcança (assembly do GH fora da compilação).

**A seção 5 do PRD desenha `LLM → parâmetros → template .gh → Rhino → .3dm`. A última seta não existe neste servidor.**

Três caminhos, nenhum decidido:

| Caminho | Custo | O que resolve |
|---|---|---|
| **Bake humano** no Grasshopper | zero técnico | quebra a autonomia, que é o ponto do projeto |
| **Trocar o servidor MCP** (`mcneel/RhinoAI`) | zera a baseline: 6 rodadas, 13 casos | pode ter bake — **não verificado** |
| **Abandonar `.gh`, manter o princípio** | reescrever a seção 5 do PRD | o objetivo real é "LLM emite parâmetros, não código". Um **script versionado e revisado** com schema de parâmetros dá a mesma garantia de governança, sem Grasshopper. E as sondagens mostraram que o agente executa script com confiabilidade. |

Minha leitura: o terceiro merece consideração séria, porque o Grasshopper era o *mecanismo* escolhido, não o *princípio*. Mas é decisão de produto, sua.

Isto é também o **gatilho para reavaliar o servidor MCP**, que estava condicionado a Rhino 9 / Grasshopper 2 / fila de skills esgotada. Há agora um quarto motivo, mais forte.

## Próxima ação

**Decidir o caminho do bloqueio arquitetural acima.** É decisão de produto, não técnica, e trava a frente de templates inteira. Enquanto não for decidida, as outras frentes seguem sem depender dela.

Trabalho pronto para seguir, em ordem de valor, **nenhum bloqueado**:

1. **Rodar `impossivel_01`** — o instrumento de recusa foi escrito e testado em 5 ramificações, mas **nunca rodou numa rodada real**. Barato, e é o primeiro dado do tier borda. Precisa do Rhino com documento novo.
2. **Rodar `esfera_01` ou `toro_01`** — fecha a calibração de facetamento. Curvatura dupla ainda está em 2% por precaução; curvatura simples mediu 0,055%. É a última incógnita do instrumento de medida.
3. **Rodar os outros 7 casos do tier fácil** — `caixa_01`, `placa_01`, `cunha_01`, `piramide_01`, `tubo_01`, `cone_01`, `calha_01`. Consolidam a linha de base e respondem se 25 tool calls é o orçamento certo, que é o que trava a candidata nº 12.
4. **Escrever os 12 casos do tier médio** — trabalho de mesa, sem Rhino.

⚠️ **A baseline anterior a 20/09 não é comparável.** As rodadas 1–4 rodaram sem percepção. Detalhe em `NOTAS.md`, seção "HARNESS v2".

## Placar da série harness v2

| Rodada | Caso | Variável testada | Veredito | Chamadas | Custo |
|---|---|---|---|---|---|
| v2r1 | `balcao_01` | percepção do servidor ligada | FALHOU — sem artefato (geometria passava) | 27 | US$ 0,53 |
| v2r2 | `balcao_01` | salvar vira passo 6 do fluxo | **PASSOU** | 36 | US$ 0,54 |
| v2r3 | `balcao_01` | prefixo de traço em `run_command` | **PASSOU** — sinal inconclusivo | 8 | US$ 0,22 |
| v2r4 | `prisma_hex_01` | estreia do tier fácil | **PASSOU** | 17 | US$ 0,27 |
| v2r5 | `cilindro_01` | calibra o facetamento da malha | **PASSOU** | 10 | US$ 0,17 |
| v2r6 | `caixa_furo_01` | boolean — a operação que derrubou a 3-bis | **PASSOU** | 15 | US$ 0,23 |

**5 de 6, em 4 casos de 13 escritos.** Ainda não é taxa de aprovação: 9 casos nunca rodaram.

**Padrão de custo que já dá para ver:**

| Tipo de caso | Chamadas | Custo |
|---|---|---|
| primitiva pura (`cilindro_01`) | 10 | US$ 0,17 |
| primitiva + boolean (`caixa_furo_01`) | 15 | US$ 0,23 |
| primitiva com orientação (`prisma_hex_01`) | 17 | US$ 0,27 |
| composição (`balcao_01`) | 8–36 | US$ 0,22–0,54 |

O caro não é modelar, é **compor**. Isso apoia o *princípio* do PRD — tirar a composição do modelo e pôr num artefato parametrizado. Mas **não** apoia especificamente o `.gh`, que hoje não entrega geometria (ver bloqueio no topo). O argumento é a favor de "template", não de "Grasshopper".

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
| Runner de rodada | exercitado em 6 rodadas; 1 defeito achado e corrigido | `evals/rodada.py` |
| Instrumento de recusa | escrito e testado, **nunca rodou de verdade** | `julga_recusa()` |
| Template Grasshopper | `balcao.json` monta e roda — **não entrega** (sem bake) | `gh-templates/` |
| `check.py` | lê Brep, Mesh e SubD; envelope min/max; `--solido`; histórico re-medido | `evals/check.py` |
| Skill | `200f2e5`, intocada | `.claude/skills/rhino-nurbs/` |

**Marco do log:** `logs/rhino_calls.jsonl` tem **385 linhas**. O runner faz essa conta sozinho.

---

## Frente orgânica — duas sondagens em 20/09

**A capacidade existe.** A sondagem 2 pediu uma vela de dupla curvatura encontrada por relaxação. O agente implementou **densidades de força**, 985 iterações, resíduo 1e-4 mm, cabos de borda com densidade 6× — e entregou um paraboloide hiperbólico anticlástico correto, em **8 chamadas e US$ 0,19**. Verificado na captura: sela genuína, bordas côncavas.

Contraste com a sondagem 1 (coral): lá o orgânico estava na **silhueta** de uma chapa recortada; aqui está na **superfície**, encontrada por solver. E custou 3× menos.

**Consequência para o PRD.** A seção 5 justifica "o LLM emite parâmetros, nunca geometria" em parte pela dificuldade do modelo com topologia. Aqui ele acertou a topologia. A decisão continua de pé pelas razões de **governança** — código arbitrário é RCE em servidor multiusuário, script não é reproduzível como slider, eval de template é mais barato. Mas a justificativa precisa ser corrigida: a restrição é de governança, não de capacidade. Argumento apoiado em limitação de capacidade envelhece mal.

## Frente orgânica — o que as sondagens revelaram sobre o instrumento

Uma sondagem fora da série (sessão `25491602`, US$ 0,58) pediu uma divisória tipo coral. Entregou Brep sólido válido, ramificação convincente, envelope respeitado. Três consequências para o roteiro:

1. ~~**check por faixa**~~ **Feito.** `--bbox-max` / `--bbox-min` por eixo, `0` = sem limite. A peça do coral, que reprovava por 19,3%, agora passa; e reprova de verdade quando estoura um teto real.
2. ~~**ler Mesh e SubD**~~ **Feito.** Mesh medida de verdade (bbox e volume por divergência, sólido por `IsClosed`); SubD mede caixa de controle como limite superior e **não mede volume** — o `rhino3dm` não expõe a superfície limite, e fingir precisão aí repetiria o bug de 19/09. Histórico re-medido, nenhum veredito mudou.
3. ~~**A rota `gh_*` não aparece sozinha.**~~ **Resolvido, e revelou coisa pior.** O agente usou as tools `gh_*` assim que recebeu a tarefa de construir um template, e montou o grafo sem dificuldade. O que ele não consegue é **tirar a geometria de lá** — ver o bloqueio no topo.

4. ~~**exigência de sólido fechado**~~ **Feito.** O `check.py` reprovava `IsSolid = false` incondicionalmente, e uma vela é superfície aberta por definição — hypar perfeito dava `FALHOU`. Agora `--solido {fechado|aberto|qualquer}`, vindo de `check.is_solid` no caso.

**O padrão das quatro lacunas:** o instrumento foi escrito supondo que toda entrega é **sólido fechado, do tipo Brep, com dimensões exatas**. Forma orgânica quebra as três suposições de uma vez. Valeu mais achar isso por duas sondagens de US$ 0,77 do que por uma série de rodadas reprovadas.

**Ainda sem instrumento: curva.** Uma teia é rede de curvas, e o `check.py` não a enxerga. Curva não tem volume nem sólido; o check para ela (comprimento total, segmentos, conectividade) ainda não tem caso que o justifique.

**Achado de fundo:** a peça é orgânica **na silhueta**, não na superfície — chapa recortada e ondulada. As famílias de gerador do PRD (casca relaxada, malha inflada, dupla curvatura) são sobre a superfície. Resolve a divisória como produto e não exercita a arquitetura apostada.

**Custo:** US$ 0,58 contra ~US$ 0,17 de uma primitiva. O guardrail do PRD é US$ 0,15 por pedido.

## Em voo

- Nada. A skill está estável em `21a31ea` e as rodadas estão registradas.

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
