# ESTADO — onde paramos

> **Atualize este arquivo ao fim de toda sessão.** É o primeiro que se lê ao voltar.
> Formato fixo: não cresça o documento, substitua o conteúdo. Histórico fica em `NOTAS.md`.

**Última sessão:** 22/09/2026 — **a cadeia fechou ponta a ponta, medida**: `LLM → parâmetros → template → Rhino → .3dm` deu `PASSOU` no `check.py`. Dois defeitos caíram no caminho, nenhum previsto: `component_name` não identifica componente, e bake sem malha entrega arquivo que o instrumento não lê. Achado de instrumento: o log não registra chamada que falha. Sondagens, nenhuma rodada.

---

## ✅ A CADEIA FECHOU — `PASSOU` medido em 22/09

`LLM → parâmetros → template → Rhino → .3dm` fecha pela primeira vez. Saída do `check.py`, que é
a fonte de verdade:

```
veredito: PASSOU
bbox      2400,0 × 829,4 × 1100   fonte: malha
is_solid  true       volume 1,4543·10⁹ mm³
casco de controle (o que se mediria sem malha): 2608,4 × 2333,8
```

Arquivo: `output/balcao_template_v1.3dm`. Remontagem limpa confirmada **no log**, não no relato:
`error_count: 0`, `join` com `data_count: 1` e `is_closed: true`, `cap` com Brep `is_solid: true`
de 6 faces.

**Dois defeitos tiveram de cair, e nenhum era o previsto** (detalhe em `NOTAS.md`, 22/09):

1. **`component_name` não identifica componente.** O `gh_build_graph` criou, do mesmo JSON e em
   duas sessões, dois `Flatten Tree` diferentes — mesmo nome, mesmo nickname, mesma categoria,
   parâmetros distintos (`Data`→`Data` em 20/09; `Tree`,`Path`→`Tree` em 22/09). O dump do canvas
   **não expõe GUID de tipo**, só `instance_id` e `graph_id`. Corrigido com
   `source_output_index: 0` na conexão do `flatAll`, depois de levantar os 21 componentes num
   canvas limpo e comparar as 26 conexões campo a campo — só essa não casava.
2. **Bake sem malha de render entrega `.3dm` que o `check.py` não mede.** Deu `INCONCLUSIVO` com
   `2608,4 × 2333,8`, a assinatura do bug de 19/09. Sombrear o viewport não resolve. Corrigido em
   `evals/bake_gh.py`, com `CreateMeshes(MeshType.Render, …)` + `CommitChanges()` nos objetos
   bakeados.

⚠️ **Três ressalvas:** ainda sobram 14 objetos de construção no arquivo (o seletor de componente
continua não existindo, e o alvo certo foi achado por regra de desempate); `_SaveSmall=_No` **não
é opção de `_-SaveAs` neste build** — o arquivo tem malha porque ela foi comitada no objeto, não
porque a opção pegou, e se o padrão de SaveSmall mudar isto quebra em silêncio; e **nenhuma rodada
de modelo aconteceu** — o placar da série v2 não mudou.

## 🔎 Achado de instrumento: o log não registra chamada que falha

O `gh_build_graph` que falhou **não está** em `logs/rhino_calls.jsonl`; o que teve sucesso, está.
O hook é `PostToolUse` e não dispara em erro de tool.

**A contagem de chamadas de toda rodada subestima**, e o que ela esconde é justamente o modo de
falha mais interessante: tentar, errar e tentar de novo. Um agente que erra cinco vezes e acerta
na sexta registra uma chamada. O orçamento de tool calls é critério de caso, e o número comparado
com ele não é o número real — o que também envenena o risco "orçamento nunca pegou", mais abaixo.

## Histórico curto — como a cadeia chegou até aqui

| Data | O que caiu | Detalhe |
|---|---|---|
| 21/09 | **O bake existe.** `clr.AddReference("Grasshopper")` funciona dentro do `execute_rhinoscript_python_code`; a rota C# falhava porque o assembly está fora da compilação e IronPython resolve em tempo de execução | `NOTAS.md` 21/09 |
| 21/09 | **Conversor jogava fora a saída de origem.** `End Points` tem `Start` e `End`; as duas linhas do perfil caíam na saída 0, e o `Cap Holes` falhava cinco componentes adiante. Corrigido com `source_output_name` nas 26 conexões | `NOTAS.md` 21/09 |
| 22/09 | **`component_name` é ambíguo** e **bake sem malha não é mensurável** — ver o topo | `NOTAS.md` 22/09 |

**Caminhos encerrados**, e não são para reabrir: trocar o servidor MCP pelo da McNeel (descartado
por evidência de código — `BakeGeometry` com 0 ocorrências, 54 tools, nenhuma bakeia); abandonar
o `.gh` (plano B, perdeu a razão de existir); bake humano (quebra a autonomia, que é o ponto).

⚠️ **Tensão a controlar:** a rota do bake reabre `execute_rhinoscript_python_code`, a superfície
de código arbitrário que o projeto fechou de propósito. **A trava é de disciplina:** o bake nunca
é autoria do modelo — script literal e versionado, enviado verbatim por passo do runner. Em 22/09
o script foi conferido no `tool_input` do log. Se um dia o agente escrever o próprio bake, a
garantia da seção 5 do PRD caiu sem ninguém notar.

## Próxima ação

**Consertar o log, antes de qualquer rodada.** O achado acima invalida a contagem de chamadas, que
é a métrica de toda rodada. Trabalho de mesa, e é pré-requisito de medir qualquer coisa:
registrar também as chamadas que falham. `PostToolUse` não basta — precisa de `PreToolUse`
(registra a tentativa) ou de um par tentativa/resultado. Ao mudar, decidir se o histórico de
391 linhas é re-interpretável ou se vira marco novo, e **dizer isso em `NOTAS.md`** — as contagens
das 6 rodadas da v2 passam a ser limite inferior, não valor.

Depois disso, em ordem de valor, **nenhum bloqueado**:

1. **Seletor de componente no `evals/bake_gh.py`** — bakear a saída do alvo, não os 16 objetos do
   canvas inteiro. Hoje o alvo certo é achado por regra de desempate do `check.py`, o que funciona
   por sorte de arranjo, não por construção. Trabalho de mesa.
2. **Regra de saída no conversor** — `source_output_name` só quando a origem tem mais de uma saída;
   saída única usa `source_output_index`. Junto: validação de ida e volta (montar → dump → comparar
   nomes de parâmetro), que é a única defesa contra `component_name` ambíguo. Trabalho de mesa.
3. **Passo de bake no `evals/rodada.py`** — bake + save do `.3dm` depois de o agente terminar, antes do `check.py`. O runner fala com o agente por `subprocess` do `claude` (`evals/rodada.py:127`) e não tem cliente MCP próprio; **preferir segunda invocação `claude -p`** com prompt literal, que não acrescenta dependência. Foi assim que a sondagem rodou. Inclua o `_-SaveAs` **sem** `_SaveSmall`, que este build recusa.
4. **Primeiro caso de eval de template** — deixou de ter pré-requisito: a cadeia está provada.

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
| Hook de guarda | escrito e testado, **inerte** — não registrado, por decisão | `.claude/hooks/guard_call.py` |
| Runner de rodada | exercitado em 6 rodadas; 1 defeito achado e corrigido | `evals/rodada.py` |
| Instrumento de recusa | escrito e testado, **nunca rodou de verdade** | `julga_recusa()` |
| Segundo leitor (Jev) | **aditivo**, nunca decide. Lógica testada offline; chamada real **nunca feita** | `julga_recusa_jev()` |
| **Bake do Grasshopper** | ✅ **funciona e entrega arquivo mensurável** (IronPython + malha de render comitada). Falta seletor de componente e o passo no runner | `evals/bake_gh.py` |
| Template Grasshopper | ✅ **`balcao.json` remonta, resolve limpo e mede `PASSOU`** (22/09). Saída única agora por índice | `gh-templates/` |
| Hook de log | ativo, mas **cego a chamada que falha** — `PostToolUse` não dispara em erro. Contagem subestima | `.claude/hooks/log_call.py` |
| `check.py` | lê Brep, Mesh e SubD; envelope min/max; `--solido`; histórico re-medido | `evals/check.py` |
| Skill | **`21a31ea`** — mudou 2× na série v2: `e404dd2` (candidata nº 7, salvar) e `21a31ea` (candidata nº 11, prefixo de traço) | `.claude/skills/rhino-nurbs/` |

**Marco do log:** `logs/rhino_calls.jsonl` tem **431 linhas** (391 + 1 de sessao perdida + 39 da sondagem de 22/09). O runner faz essa conta sozinho. ⚠️ **O marco conta chamadas bem-sucedidas apenas** — ver o achado de instrumento acima.

---

## Frente orgânica — duas sondagens em 20/09

**A capacidade existe.** A sondagem 2 pediu uma vela de dupla curvatura encontrada por relaxação. O agente implementou **densidades de força**, 985 iterações, resíduo 1e-4 mm, cabos de borda com densidade 6× — e entregou um paraboloide hiperbólico anticlástico correto, em **8 chamadas e US$ 0,19**. Verificado na captura: sela genuína, bordas côncavas.

Contraste com a sondagem 1 (coral): lá o orgânico estava na **silhueta** de uma chapa recortada; aqui está na **superfície**, encontrada por solver. E custou 3× menos.

**Consequência para o PRD.** A seção 5 justifica "o LLM emite parâmetros, nunca geometria" em parte pela dificuldade do modelo com topologia. Aqui ele acertou a topologia. A decisão continua de pé pelas razões de **governança** — código arbitrário é RCE em servidor multiusuário, script não é reproduzível como slider, eval de template é mais barato. Mas a justificativa precisa ser corrigida: a restrição é de governança, não de capacidade. Argumento apoiado em limitação de capacidade envelhece mal.

## Frente orgânica — o que as sondagens revelaram sobre o instrumento

Uma sondagem fora da série (sessão `25491602`, US$ 0,58) pediu uma divisória tipo coral. Entregou Brep sólido válido, ramificação convincente, envelope respeitado. Três consequências para o roteiro:

1. ~~**check por faixa**~~ **Feito.** `--bbox-max` / `--bbox-min` por eixo, `0` = sem limite. A peça do coral, que reprovava por 19,3%, agora passa; e reprova de verdade quando estoura um teto real.
2. ~~**ler Mesh e SubD**~~ **Feito.** Mesh medida de verdade (bbox e volume por divergência, sólido por `IsClosed`); SubD mede caixa de controle como limite superior e **não mede volume** — o `rhino3dm` não expõe a superfície limite, e fingir precisão aí repetiria o bug de 19/09. Histórico re-medido, nenhum veredito mudou.
3. ~~**A rota `gh_*` não aparece sozinha.**~~ **Resolvido, e revelou coisa pior.** O agente usou as tools `gh_*` assim que recebeu a tarefa de construir um template, e montou o grafo sem dificuldade. O que ele não conseguia era **tirar a geometria de lá**; resolvido em 21–22/09.

4. ~~**exigência de sólido fechado**~~ **Feito.** O `check.py` reprovava `IsSolid = false` incondicionalmente, e uma vela é superfície aberta por definição — hypar perfeito dava `FALHOU`. Agora `--solido {fechado|aberto|qualquer}`, vindo de `check.is_solid` no caso.

**O padrão das quatro lacunas:** o instrumento foi escrito supondo que toda entrega é **sólido fechado, do tipo Brep, com dimensões exatas**. Forma orgânica quebra as três suposições de uma vez. Valeu mais achar isso por duas sondagens de US$ 0,77 do que por uma série de rodadas reprovadas.

**Ainda sem instrumento: curva.** Uma teia é rede de curvas, e o `check.py` não a enxerga. Curva não tem volume nem sólido; o check para ela (comprimento total, segmentos, conectividade) ainda não tem caso que o justifique.

**Achado de fundo:** a peça é orgânica **na silhueta**, não na superfície — chapa recortada e ondulada. As famílias de gerador do PRD (casca relaxada, malha inflada, dupla curvatura) são sobre a superfície. Resolve a divisória como produto e não exercita a arquitetura apostada.

**Custo:** US$ 0,58 contra ~US$ 0,17 de uma primitiva. O guardrail do PRD é US$ 0,15 por pedido.

## Em voo

- ✅ ~~A correção do template nunca foi provada no Rhino.~~ **Provada em 22/09**, e revelou dois defeitos novos — ver o topo deste documento.
- **Smoke test do Jev** — já desbloqueado (chave no ambiente), ainda não executado.
- A skill está estável em `21a31ea`, intocada. As rodadas estão registradas.
- **3 commits locais não enviados**: `59ed854`, `7a8d407` e o de 22/09. Os anteriores foram para o GitHub em 21/09.
- **Os prompts das sondagens não estão versionados.** O de 21/09 ("já desenhado") morreu com o contexto da sessão e teve de ser reescrito. Prompt de sondagem é instrumento: ou vai para `PROMPTS.md`, ou se perde.
- O `supervisor` ganhou remoto **privado** (`elisacosta116-sudo/supervisor`, branch `master`), com os 4 commits enviados. Era o único trabalho sem cópia fora do disco.

## Fechado nesta sessão — 22/09

- ✅ **A cadeia fechou ponta a ponta, medida.** `PASSOU` no `check.py`, bbox pela malha,
  sólido fechado. Ver o topo.
- **Defeito de formato achado: `component_name` não identifica componente.** Dois `Flatten Tree`
  distintos do mesmo JSON, em duas sessões, sem GUID de tipo no dump para desempatar. Corrigido
  pontualmente com `source_output_index: 0`; a regra geral (índice para saída única, nome só para
  desambiguar) ainda **não está no conversor**.
- **Defeito de instrumento achado: bake sem malha de render entrega `.3dm` que o `check.py` não
  mede.** Corrigido em `evals/bake_gh.py`. Sombrear o viewport não resolve — testado.
- **Defeito de instrumento achado, ainda ABERTO: o log é cego a chamada que falha.** `PostToolUse`
  não dispara em erro de tool. É a próxima ação.
- **Método que funcionou, e vale repetir:** prompt de sondagem com **parada condicional explícita**
  (*"se falhar, relate e pare; diagnosticar é trabalho do supervisor"*). O agente parou quatro
  vezes em vez de improvisar — inclusive recusando-se a relatar um `object_count` porque isso
  implicaria que um save duvidoso era confiável. Nos três casos o relato bateu com o log.
- **Levantamento antes de mexer:** os 21 componentes foram criados num canvas limpo **sem conexão
  nenhuma** e comparados campo a campo com o template, para saber se o `flatAll` era exceção ou
  regra. Era exceção — 1 de 26. Sem isso, a correção teria sido chute.
- Custo da sessão: **US$ 1,69**, 8 invocações `claude -p`, nenhuma rodada de modelo.

## Roteiro, em ordem

1. ~~**harness v2, rodada 1**~~ — **feito**, e já foram seis rodadas. A próxima ação está no topo deste documento.
2. **Rodada tipada** — uma rodada que tente a rota tipada até o fim (`create_object type=ARC` → `offset_curve` → fechar o perfil), para descobrir se `create_planar_region` dispensa o join que não existe tipado. É o que decide se a rota C# é necessária ou apenas conveniente.
3. **Capturar os 5 tópicos de guidance que faltam** (`transforms`, `planar_regions`, `organization`, `verification`, `recovery`). Exige Rhino aberto; procedimento em `references/guidance/README.md`. O `verification` nunca foi lido em 217 chamadas.
4. **Candidata nº 7** — obrigar o save.
5. **Fechar a lacuna que sobrou do `check.py`** — escolha do Brep alvo. A outra (*arquivo sem malha de render*) foi atacada pelo lado do bake em 22/09, não pelo lado do check: o `check.py` continua sem saber medir Brep aparado sem malha, e **só não dói porque o bake agora sempre gera malha**. Arquivo vindo de outra fonte ainda cai no casco de controle. Ao mudar o instrumento, re-medir o histórico inteiro.
6. **Escrever os casos de eval restantes** — 14 de ~30 escritos. Pré-requisito do piloto.
7. **Construir os 4 primeiros templates** — balcão, arco, painel, totem. **Formato decidido:** `.gh` via JSON versionado; a rota IronPython alcançou e o balcão mediu `PASSOU`. Cada template novo só conta como versionado depois de **remontado, resolvido e medido** — converter sem erro não prova nada, e `component_name` ambíguo garante que aí haverá surpresa.
8. **Medir os dois números da seção 1 do PRD** — tempo por proposta e variações por cliente.

## Riscos abertos

- **Comando interativo do Rhino trava a sessão e o MCP não cancela.** Na v2r2 um `_Arc` sem prefixo de traço ficou pendurado com linha elástica no viewport, bloqueou o `run_command` seguinte e só saiu com `Esc` humano. **Numa rodada autônoma isso trava tudo a partir dali.** Candidata nº 11 ataca a causa; não há mitigação para o caso de acontecer mesmo assim.
- **Orçamento de tool calls nunca pegou:** 45 → 25 → 68 → 9 → 27 → 36. E a rodada aprovada gastou 36 contra um limite de 25 — não se sabe se a regra está sendo ignorada ou se o número está errado. **Pior desde 22/09:** esses seis números contam só chamadas bem-sucedidas, então são **limite inferior**. O gasto real foi maior, e não se sabe quanto.

- **O template versionado não é reprodutível por construção — só por verificação.** `component_name`
  é ambíguo e o dump do canvas não traz GUID de tipo, então o mesmo JSON pode montar grafos
  diferentes em sessões diferentes (provado em 22/09 com o `Flatten Tree`). O PRD encosta a aposta
  em *"é diffável no git, é exatamente o que `gh_build_graph` consome"* — verdadeiro sobre o
  formato, **frágil sobre o conteúdo**. Mitigação hoje: nenhuma automática; só a disciplina de
  remontar-e-medir todo template antes de confiar nele. Mitigação real exigiria o servidor expor
  GUID de tipo, que é pedido a montante.
- **`dev/.claude/settings.json` não está sob controle de versão.** É o que impede o supervisor de mexer nas travas do operador. Há cópia rastreada em `supervisor/travas-do-supervisor.json`; re-copie ao mudar.
- **O `guard_call.py` tem dois defeitos conhecidos** antes de qualquer reconsideração: falha fechada se o log ficar sem escrita, e lê o log inteiro a cada chamada (1,37 MB hoje, por causa dos PNG em base64 do `capture_viewport`).
- **4 casos rodados de 14 escritos**, para um alvo de ~30. Cinco aprovações não são taxa de aprovação: 10 casos nunca rodaram, e 12 dos 14 escritos são do tier fácil.
- ~~**O runner nunca rodou ponta a ponta.**~~ **Vencido:** exercitado em 6 rodadas, 1 defeito achado e corrigido. O que ainda nunca rodou de verdade é o **instrumento de recusa** (`julga_recusa()`) e o **segundo leitor** (`julga_recusa_jev()`) — ambos estreiam em `impossivel_01`.
- **O contrato do SDK do Jev está lido dos docs, não verificado.** `TypeSafeClient()` como context manager e `response.nouls[k].noul` vêm da página do SDK Python. Se divergirem, o leitor cai no caminho de indisponível e a rodada segue — o risco é de perder o dado do segundo leitor, não de perder a rodada. Mitigação: o smoke test do item 0.
- **Um segundo leitor é um segundo instrumento, e instrumento tem viés.** Hoje ele não decide nada, então o viés é inofensivo. Ele deixa de ser inofensivo no dia em que alguém olhar a probabilidade e ajustar o veredito à mão. Se isso virar prática, precisa de re-medição do histórico, como em 19/09.
