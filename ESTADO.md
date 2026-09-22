# ESTADO — onde paramos

> **Atualize este arquivo ao fim de toda sessão.** É o primeiro que se lê ao voltar.
> Formato fixo: não cresça o documento, substitua o conteúdo. Histórico fica em `NOTAS.md`.

**Última sessão:** 22/09/2026 — **a cadeia fechou ponta a ponta, medida**: `LLM → parâmetros → template → Rhino → .3dm` deu `PASSOU` no `check.py`. Dois defeitos caíram no caminho, nenhum previsto: `component_name` não identifica componente, e bake sem malha entrega arquivo que o instrumento não lê. Achado de instrumento: o log não registrava chamada que falha — **conserto commitado no mesmo dia (`addda29`), falta uma linha de registro que é trava do operador**. Sondagens e trabalho de mesa, nenhuma rodada.

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

## 🔎 O log era cego a chamada que falha — consertado no código, **falta ligar**

O `gh_build_graph` que falhou **não estava** em `logs/rhino_calls.jsonl`; o que teve sucesso,
estava. O hook era só `PostToolUse`, que não dispara em erro de tool.

**A contagem de chamadas de toda rodada subestimava**, e o que ela escondia é justamente o modo
de falha mais interessante: tentar, errar e tentar de novo. Um agente que erra cinco vezes e
acerta na sexta registrava uma chamada.

**Conserto commitado em `addda29`**, e o que ele faz:

- `log_call.py` roda nos **dois** eventos. `PreToolUse` é a tentativa e dispara sempre; a dupla
  tentativa-sem-resultado de mesmo `tool_use_id` **é** a chamada que falhou.
- **Falha aberta, e não é negociável:** em `PreToolUse`, sair com código ≠ 0 *bloqueia* a chamada.
  Um logger que derruba a chamada que deveria medir inverte o instrumento — a rodada passaria a
  medir o hook, e falharia parecendo resultado do modelo. Tudo em `try/except`, sai `0` sempre,
  e nada vai para stdout/stderr (em `PreToolUse` isso entraria no contexto do agente).
- `conta_chamadas()` no runner: a contagem da rodada passa a ser **tentativas**, e o critério de
  `ANULADA` junto — rodada cujas chamadas *todas* falharam tocou no Rhino e é resultado legítimo,
  não problema de setup. Contar só o concluído a carimbaria de anulada, que é o erro mais caro
  possível para esta série: descartar dado bom como falha de ambiente.

⚠️ **Falta uma linha, e sem ela nada disso mede:** registrar `PreToolUse` em
`.claude/settings.json`, que é **trava do operador** — o supervisor entrega o diff, o usuário
aplica. Até lá o runner detecta o formato antigo e imprime `cego_a_falha` em vez de fingir
precisão. O diff é o bloco `PostToolUse` duplicado com a chave trocada; nada mais muda.

**Decisão tomada, que o documento pedia:** o histórico **é re-interpretável, não vira marco novo**.
Os 11 vereditos já gravados ficam, carimbados `log_cego_a_falha: true`, e **campo ausente
significa cego**, não limpo — ler ausência como "todas concluídas" carimbaria de exato justamente
o número que não é.

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

**Ligar o `PreToolUse`, e confirmar com uma chamada real — antes de qualquer rodada.** O código
está commitado e testado offline; o que falta é o registro no `.claude/settings.json` do agente,
que é trava do operador. Dois passos, nessa ordem:

1. **Aplicar o diff** — duplicar o bloco `PostToolUse` do `.claude/settings.json` com a chave
   trocada para `"PreToolUse"`, mesmo matcher e mesmo comando. **Pelas mãos do usuário.**
2. **Confirmar no Rhino, com uma chamada MCP qualquer:** têm de sair **duas** linhas no
   `logs/rhino_calls.jsonl`, não uma. O teste offline prova que o script funciona; **não** prova
   que o registro pegou, e essa é a diferença que decide se a próxima rodada mede ou só avisa.

Sem o passo 2 nenhuma rodada nova é comparável, porque não se sabe se o número é tentativa ou
resultado. Gastar uma rodada para descobrir isso é caro e evitável.

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
| Hook de log | código pronto para os dois eventos, falha aberta, testado offline — ⚠️ **`PreToolUse` ainda não registrado**, então na prática segue cego | `.claude/hooks/log_call.py` |
| `check.py` | lê Brep, Mesh e SubD; envelope min/max; `--solido`; histórico re-medido | `evals/check.py` |
| Skill | **`21a31ea`** — mudou 2× na série v2: `e404dd2` (candidata nº 7, salvar) e `21a31ea` (candidata nº 11, prefixo de traço) | `.claude/skills/rhino-nurbs/` |

**Marco do log:** `logs/rhino_calls.jsonl` tem **431 linhas** (391 + 1 de sessao perdida + 39 da sondagem de 22/09). O runner faz essa conta sozinho. ⚠️ **As 431 são chamadas bem-sucedidas apenas.** O conserto do log foi testado em cwd temporário justamente para não sujar este número: o marco é a base de contagem de toda rodada, e estragá-lo para testar o contador de rodadas seria arruinar o instrumento com o teste do instrumento. Depois de ligado o `PreToolUse`, a linha nova passa a ser ~2 por chamada — o marco absorve isso sozinho, porque a conta é por diferença.

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
- ~~3 commits locais não enviados~~ **Vencido: zero.** Os dois repositórios estão em dia com o `origin`, `rhino-agent` até `655a30c`.
- ⚠️ **O `PreToolUse` está commitado mas não registrado.** É a única peça deste conserto que o supervisor não pode aplicar, e é a que faz o resto valer. Enquanto não for, toda rodada nova sai marcada `cego_a_falha`.
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
- **Defeito de instrumento achado E consertado no código: o log era cego a chamada que falha.**
  `PostToolUse` não dispara em erro de tool. Commit `addda29`: hook nos dois eventos com falha
  aberta, `conta_chamadas()` pareando por `tool_use_id`, histórico carimbado. Testado offline em
  cwd temporário — o hook grava as duas fases e sai `0` com entrada inválida sem gravar; o
  contador nomeia a chamada que falhou, cai no formato antigo quando não há `PreToolUse`, e
  respeita o marco. **Falta ligar** — ver a próxima ação.
- **Erro corrigido na própria correção:** o docstring do `conta_chamadas()` chamava
  `45, 25, 68, 9, 27, 36` de "as seis rodadas da série v2". Não são — os quatro primeiros são
  `pre-v2`. É a mesma confusão de séries que custou a correção de 21/09, cometida de novo na
  linha que avisa sobre ela.
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
- **Orçamento de tool calls nunca pegou.** `pre-v2`: 45 → 25 → 68 → 9. `v2`: 27 → 36 → 8 → 17 → 10 → 15. A rodada aprovada da v2 gastou 36 contra um limite de 25 — não se sabe se a regra está sendo ignorada ou se o número está errado. **E nenhum desses números é valor:** todos contam só chamadas bem-sucedidas, então são **limite inferior**; o gasto real foi maior, e não se sabe quanto. O instrumento para saber existe desde `addda29`, mas **só mede depois de ligado** — até lá o risco segue igual, e as duas séries não se juntam numa lista só (foi o que o campo `serie` existe para impedir).

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
