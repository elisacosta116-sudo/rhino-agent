# ESTADO — onde paramos

> **Atualize este arquivo ao fim de toda sessão.** É o primeiro que se lê ao voltar.
> Formato fixo: não cresça o documento, substitua o conteúdo. Histórico fica em `NOTAS.md`.

**Última sessão:** 21/09/2026 — **o bloqueio arquitetural caiu**: o bake funciona pela rota IronPython. McNeel verificada e descartada por evidência; achada e corrigida a causa de o template não remontar (**correção ainda não provada no Rhino**); separação de séries corrigida; segundo leitor do tier borda escrito. Sondagens, nenhuma rodada.

---

## ✅ Bloqueio arquitetural RESOLVIDO — o bake existe, pela rota IronPython

Medido em 21/09, sondagem fora da série, US$ 0,44. **`clr.AddReference("Grasshopper")` funciona
dentro do `execute_rhinoscript_python_code`**, e o `BakeGeometry` entrega geometria ao documento do
Rhino. Confirmado por resposta do servidor lida do `logs/rhino_calls.jsonl`, não pelo relato do agente:

```
objetos bakeados: 18 · camada ESTANDE::Mobiliario (criada pelo script)
bbox [-1200, -529.41, 0] → [1200, 300, 1100]  =  2400 × 829,41 × 1100 mm
```

**A seção 5 do PRD fica de pé.** `LLM → parâmetros → template → Rhino → .3dm` fecha, e a última
seta é um **script versionado do harness** (`evals/bake_gh.py`), não autoria do modelo. Resolvido
sem trocar de servidor, sem perder a baseline e sem reescrever o PRD. O plano B (abandonar o `.gh`)
**não será executado**.

Por que a rota C# falhava e esta não: o assembly do Grasshopper está fora da compilação; IronPython
resolve em tempo de execução. Era só isso.

⚠️ **Três ressalvas, para não virar otimismo:** o script bakeou **tudo** que era bakeável (18
objetos, incluindo 5 pontos e 5 arcos de construção) e produção precisa de **seletor de
componente**; os 3 BREPs **não são sólido fechado**, porque o `Cap Holes` falhou na remontagem; e a
bbox bater com o alvo é encorajador mas **não é prova** — é a caixa dos 18 objetos juntos. Prova só
com `.3dm` pelo `check.py`.

## 🔧 Template não remontava: causa achada e corrigida — falta provar no Rhino

**Causa:** o conversor `evals/gh_canvas_para_template.py` gravava a origem de cada conexão e
**jogava fora de qual saída dela**. As duas linhas do perfil puxam de `End Points` — `lnS` da
saída `Start`, `lnE` da saída `End` — e sem essa informação as duas caíam na saída 0. O perfil não
fechava, o `Join Curves` saía com `data_count: 2` e o `Cap Holes` falhava, **cinco componentes
adiante da causa**.

Não era o `Flatten Tree`, que sempre esteve correto. A hipótese "o conversor perde informação"
estava certa; a informação existia no `param_name` do `gh_get_canvas_state` e nunca era lida.

**Corrigido**, com o campo que o contrato do `gh_build_graph` define (`$defs/connection`):

```json
{"source": "ends", "source_output_name": "Start", "target": "lnS", "target_input_index": 1}
{"source": "ends", "source_output_name": "End",   "target": "lnE", "target_input_index": 1}
```

O contrato marca o campo como **opcional**; na prática ele é obrigatório para qualquer origem com
mais de uma saída. O template regenerado tem `source_output_name` nas **26 conexões**.

Dois ganhos junto: o conversor passou a **avisar** quando uma conexão vem de origem com várias
saídas sem dizer qual (no formato antigo, o aviso pega 5 conexões deste template), e passou a
**preferir o alias do canvas** — `pA`, `lnS`, `ends`, `flatAll` em vez de `pt`, `pt_2`, `pt_3`.
O slider `profundidade` virou `prof`, que é o nome real do grafo; `README.md` atualizado.

⚠️ **Ainda não é evidência.** A correção foi testada de mesa (o instrumento pega o defeito que o
motivou e não acusa o template correto), mas **a remontagem no Rhino não rodou**: a conexão caiu
(`Could not connect to Rhino at 127.0.0.1:1999`). Enquanto o grafo não montar e rodar limpo, isto
é hipótese bem fundamentada, não fato medido.

### Caminhos, encerrados em 21/09

| Caminho | Situação |
|---|---|
| **Bake por script versionado (IronPython)** | ✅ **ESCOLHIDO E VERIFICADO.** Funciona. `evals/bake_gh.py` |
| **Trocar o servidor MCP** (`mcneel/RhinoAI`) | ❌ descartado por evidência: o oficial **não faz bake** (`BakeGeometry` com 0 ocorrências; 54 tools, nenhuma bakeia; `GH1_SolveTool.cs` opera sobre `IGH_PreviewObject`). Reavaliação **encerrada**, não adiada |
| **Abandonar `.gh`, manter o princípio** | ❌ não será executado — o plano B perdeu a razão de existir |
| **Bake humano** no Grasshopper | ❌ quebra a autonomia, que é o ponto do projeto |

⚠️ **Tensão a controlar, agora que a rota está aberta:** isso reabre `execute_rhinoscript_python_code`, a superfície de código arbitrário que o projeto fechou de propósito (61 de 208 chamadas em script; a API inventada da 3-bis). **A trava é de disciplina:** o bake nunca é autoria do modelo — script literal e versionado, executado por passo do runner. Se um dia o agente escrever o próprio bake, a garantia da seção 5 do PRD caiu sem ninguém notar.

## Próxima ação

**Provar a correção do template no Rhino** — exige Rhino aberto com `mcpstart` confirmado. Três passos numa sessão só, e fecham a cadeia inteira do PRD pela primeira vez:

1. `gh_create_document` (canvas limpo — não reaproveitar o velho), remontar de `balcao.json` **passando `source_output_name` verbatim**, e `gh_run_solution`. Sucesso = `error_count: 0` e `join` com `data_count: 1`.
2. Bakear com `evals/bake_gh.py` e salvar o `.3dm`.
3. Medir com o `check.py`, no alvo já verificado:
   `--bbox 2400 829 1100 --tol 0.01 --layer "ESTANDE::Mobiliario"`

Se o passo 3 der `PASSOU`, `LLM → parâmetros → template → Rhino → .3dm` fecha ponta a ponta pela primeira vez, e o primeiro caso de eval de template deixa de ter pré-requisito.

Depois disso, em ordem de valor:

1. **Seletor de componente no `evals/bake_gh.py`** — bakear a saída do alvo, não os 18 objetos do canvas inteiro. Trabalho de mesa.
2. **Passo de bake no `evals/rodada.py`** — bake + save do `.3dm` depois de o agente terminar, antes do `check.py`. O runner fala com o agente por `subprocess` do `claude` (`evals/rodada.py:127`) e não tem cliente MCP próprio; **preferir segunda invocação `claude -p`** com prompt literal, que não acrescenta dependência. Foi assim que a sondagem rodou.
3. **Primeiro caso de eval de template** — fecha `parâmetros → .gh → .3dm` ponta a ponta, medido pelo `check.py` como qualquer outro.

Trabalho pronto para seguir, em ordem de valor, **nenhum bloqueado**:

0. **Smoke test do Jev, antes de qualquer rodada.** Uma chamada Noul mínima, centavos de token. O contrato do SDK está lido dos docs e **nunca exercitado** — `TypeSafeClient()` como context manager, `response.nouls[k].noul`. Se estiver diferente do documentado, é melhor descobrir aqui do que com o Rhino aberto. ✅ **Desbloqueado:** a `TYPESAFE_API_KEY` já está visível no ambiente (verificado em 21/09, 108 chars) — o restart que faltava aconteceu.
1. **Rodar `impossivel_01`** — o instrumento de recusa foi escrito e testado em 5 ramificações, mas **nunca rodou numa rodada real**. Agora estreia com os **dois leitores** (mecânico + Jev aditivo), o que é melhor do que estrear e ter que re-medir depois. Barato, e é o primeiro dado do tier borda. Precisa do Rhino com documento novo e de `--with typesafe-sdk`.
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

**5 de 6, em 4 casos de 14 escritos.** Ainda não é taxa de aprovação: **10 casos nunca rodaram**.

A separação das séries agora é o campo **`serie`** de cada registro do `historico` (`pre-v2` | `v2`), não mais a caixa da palavra do veredito. A regra antiga não se sustentava: a `rodada 4` da série antiga está gravada como `PASSOU` maiúsculo e inflava a v2 em um PASSOU. Corrigido em 21/09.

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
| Segundo leitor (Jev) | **aditivo**, nunca decide. Lógica testada offline; chamada real **nunca feita** | `julga_recusa_jev()` |
| **Bake do Grasshopper** | ✅ **funciona** (IronPython, `clr.AddReference`). Verificado 21/09. Falta seletor de componente e o passo no runner | `evals/bake_gh.py` |
| Template Grasshopper | `balcao.json` **não remonta**: `Cap Holes` falha, `Join Curves` sai com 2 ramos. Bloqueio aberto | `gh-templates/` |
| `check.py` | lê Brep, Mesh e SubD; envelope min/max; `--solido`; histórico re-medido | `evals/check.py` |
| Skill | **`21a31ea`** — mudou 2× na série v2: `e404dd2` (candidata nº 7, salvar) e `21a31ea` (candidata nº 11, prefixo de traço) | `.claude/skills/rhino-nurbs/` |

**Marco do log:** `logs/rhino_calls.jsonl` tem **391 linhas** (385 + 6 da sondagem de bake). O runner faz essa conta sozinho.

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

- 🔴 **A correção do template nunca foi provada no Rhino.** Está commitada e testada de mesa, mas a remontagem não chegou a rodar: primeiro o Rhino caiu, depois um **incidente da Anthropic** derrubou o caminho `claude -p` (500 em qualquer prompt, inclusive `"diga apenas OK"`; status.claude.com confirmou *partial outage* de Claude Code e API em 21–22/09). **É a primeira coisa a fazer na próxima sessão** — o prompt já está desenhado, com parada condicional antes do bake.
- **Smoke test do Jev** — já desbloqueado (chave no ambiente), ainda não executado.
- A skill está estável em `21a31ea`, intocada. As rodadas estão registradas.
- **1 commit local não enviado**: `59ed854` (correção do conversor). Os anteriores foram para o GitHub em 21/09.
- O `supervisor` ganhou remoto **privado** (`elisacosta116-sudo/supervisor`, branch `master`), com os 4 commits enviados. Era o único trabalho sem cópia fora do disco.

## Fechado nesta sessão

- **Causa de o template não remontar, achada e corrigida:** o conversor descartava a saída de origem das conexões (`End Points` tem `Start` e `End`; as duas linhas do perfil caíam na saída 0). Agora usa `source_output_name`, campo que o contrato do `gh_build_graph` já define, nas 26 conexões — mais rede de segurança contra conexão ambígua e aliases legíveis de volta. **Não provado no Rhino**, ver "Em voo".
- ✅ **O bloqueio arquitetural de 20/09 caiu.** O bake funciona pela rota IronPython: 18 objetos entregues ao documento do Rhino, bbox 2400 × 829,41 × 1100, confirmado pela resposta do servidor no log — não pelo relato do agente. Custo total da sondagem: **US$ 0,44**, 6 chamadas MCP. A seção 5 do PRD fica de pé e o plano B foi arquivado.
- 🛑 **Bloqueio novo, e ataca a aposta do PRD:** o `balcao.json` **não remonta** — `Cap Holes` falha porque o `Join Curves` sai com 2 ramos, apesar de o `Flatten Tree` estar presente e bem ligado. O JSON versionado não reproduz o grafo que funcionou. É a próxima ação.
- **`evals/bake_gh.py`** — script de bake versionado, camada por parâmetro. Enviado verbatim pelo agente (conferido no `tool_input.code` do log).
- **Servidor da McNeel verificado e descartado por evidência de código.** `BakeGeometry`: 0 ocorrências; 54 tools inventariadas, nenhuma bakeia; `GH1_SolveTool.cs` opera sobre pré-visualização. A reavaliação do servidor MCP está **encerrada, não adiada**. Detalhe em `NOTAS.md`, 21/09.
- **Caminho novo descoberto:** bake é capacidade do plugin, não do protocolo. A rota `execute_rhinoscript_python_code` (IronPython 2.7, em processo, `clr.AddReference` em tempo de execução) nunca foi tentada, e contorna exatamente o motivo da falha do C#. Sondagem pendente.
- **Terceiro defeito de instrumento corrigido:** o `cases.jsonl` separava séries pela caixa da palavra do veredito, e a `rodada 4` antiga está em maiúscula — inflava a v2 em um PASSOU. Agora há campo `serie` explícito em todo registro de `historico`; nenhum outro campo tocado (verificado por diff registro a registro). A skill de onboarding foi corrigida junto.
- **Divergências documento × disco corrigidas** neste arquivo: 14 casos escritos (não 13), 10 nunca rodados (não 9), hash da skill `21a31ea` (não `200f2e5`), plugin `typesafe` desabilitado, item 1 do roteiro vencido, dois riscos obsoletos.
- **Achado: o instrumento de recusa tinha viés para falso `PASSOU`.** `julga_recusa()` casa substring, e **substring não lê negação** — `"nao e impossivel, entao fiz uma aproximacao"` casa com o sinal `impossivel` e aprova uma rodada que fez exatamente o que o caso proíbe. Como o `impossivel_01` declara 8 sinais, vários genéricos, o risco de aprovação perdida é baixo e o risco concentrado é o falso positivo. **Direção oposta ao viés de 19/09**, quando o instrumento reprovava geometria correta. A lição: todo instrumento novo precisa de um caso de teste que tente enganá-lo.
- **Segundo leitor escrito, aditivo por construção:** `julga_recusa_jev()` + `compara_com_jev()` em `evals/rodada.py`. Três Nouls numa requisição (`recusou_a_tarefa`, `motivo_geometrico_correto`, `parou_por_obstaculo_tecnico`). Roda depois do veredito mecânico, não altera veredito, não derruba rodada, e `FALHOU` por artefato nunca passa por modelo. A terceira pergunta nomeia a dúvida que o `INCONCLUSIVO` só descrevia em prosa.
- **Lógica testada offline em 5 caminhos**, incluindo o falso positivo acima, que sai como `DIVERGENCIA FORTE`. O caminho feliz não foi testado: não havia chave.
- **Decisão registrada:** o Jev resolve o problema de *interface* (resposta tipada em vez de texto para parsear), não o de verdade — os docs da TypeSafe dizem *"typed output guarantees the interface, not truth"*. Por isso não vira veredito. O `check.py` com `rhino3dm` continua sendo a fonte de verdade da geometria, e **pôr modelo ali seria rebaixar o instrumento**.
- Documentação: `NOTAS.md` (seção de 21/09), `OPERACAO.md` (§3 passo 2-bis, chave e comando), `HARNESS.md` (camada 4, os dois instrumentos).
- Segurança: o repositório é **público**; `.env` e `.env.*` no `.gitignore`, varredura do histórico sem nenhuma ocorrência de chave, chave em variável de ambiente de usuário via `setx`.
- Plugin `typesafe@typesafe-ai` instalado no escopo de usuário (1 skill, 0 hooks, 0 MCP servers). **Está desabilitado** (`claude plugin list` → `✘ disabled`, verificado 21/09), então não há os ~207 tok sempre-presentes no contexto do agente — a variável de eval não existe hoje. **Não é dependência do harness**: o runner usa o SDK Python direto.
- Os 16 commits pendentes de 20/09 foram enviados ao GitHub (`200f2e5..df0d2bf`).

---

## Roteiro, em ordem

1. ~~**harness v2, rodada 1**~~ — **feito**, e já foram seis rodadas. A próxima ação está no topo deste documento.
2. **Rodada tipada** — uma rodada que tente a rota tipada até o fim (`create_object type=ARC` → `offset_curve` → fechar o perfil), para descobrir se `create_planar_region` dispensa o join que não existe tipado. É o que decide se a rota C# é necessária ou apenas conveniente.
3. **Capturar os 5 tópicos de guidance que faltam** (`transforms`, `planar_regions`, `organization`, `verification`, `recovery`). Exige Rhino aberto; procedimento em `references/guidance/README.md`. O `verification` nunca foi lido em 217 chamadas.
4. **Candidata nº 7** — obrigar o save.
5. **Fechar as 2 lacunas do `check.py`** — escolha do Brep alvo e arquivo sem malha de render. Trabalho de mesa. Ao mudar o instrumento, re-medir o histórico inteiro.
6. **Escrever os casos de eval restantes** — 14 de ~30 escritos. Pré-requisito do piloto.
7. **Construir os 4 primeiros templates** — balcão, arco, painel, totem. **O formato depende da sondagem do bake**: `.gh` se a rota IronPython alcançar, script versionado com schema se não.
8. **Medir os dois números da seção 1 do PRD** — tempo por proposta e variações por cliente.

## Riscos abertos

- **Comando interativo do Rhino trava a sessão e o MCP não cancela.** Na v2r2 um `_Arc` sem prefixo de traço ficou pendurado com linha elástica no viewport, bloqueou o `run_command` seguinte e só saiu com `Esc` humano. **Numa rodada autônoma isso trava tudo a partir dali.** Candidata nº 11 ataca a causa; não há mitigação para o caso de acontecer mesmo assim.
- **Orçamento de tool calls nunca pegou:** 45 → 25 → 68 → 9 → 27 → 36. E a rodada aprovada gastou 36 contra um limite de 25 — não se sabe se a regra está sendo ignorada ou se o número está errado.

- **`dev/.claude/settings.json` não está sob controle de versão.** É o que impede o supervisor de mexer nas travas do operador. Há cópia rastreada em `supervisor/travas-do-supervisor.json`; re-copie ao mudar.
- **O `guard_call.py` tem dois defeitos conhecidos** antes de qualquer reconsideração: falha fechada se o log ficar sem escrita, e lê o log inteiro a cada chamada (1,37 MB hoje, por causa dos PNG em base64 do `capture_viewport`).
- **4 casos rodados de 14 escritos**, para um alvo de ~30. Cinco aprovações não são taxa de aprovação: 10 casos nunca rodaram, e 12 dos 14 escritos são do tier fácil.
- ~~**O runner nunca rodou ponta a ponta.**~~ **Vencido:** exercitado em 6 rodadas, 1 defeito achado e corrigido. O que ainda nunca rodou de verdade é o **instrumento de recusa** (`julga_recusa()`) e o **segundo leitor** (`julga_recusa_jev()`) — ambos estreiam em `impossivel_01`.
- **O contrato do SDK do Jev está lido dos docs, não verificado.** `TypeSafeClient()` como context manager e `response.nouls[k].noul` vêm da página do SDK Python. Se divergirem, o leitor cai no caminho de indisponível e a rodada segue — o risco é de perder o dado do segundo leitor, não de perder a rodada. Mitigação: o smoke test do item 0.
- **Um segundo leitor é um segundo instrumento, e instrumento tem viés.** Hoje ele não decide nada, então o viés é inofensivo. Ele deixa de ser inofensivo no dia em que alguém olhar a probabilidade e ajustar o veredito à mão. Se isso virar prática, precisa de re-medição do histórico, como em 19/09.
