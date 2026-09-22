# NOTAS — rodadas do agente rhino-agent

> ## ⚠️ CORREÇÃO DE INSTRUMENTO — 19/09, após a rodada 4
>
> O `check.py` media a bbox errada e **reprovou geometria correta**. `rhino3dm` devolve, para um Brep, a caixa das superfícies **não aparadas** (casco dos pontos de controle), não a da geometria recortada. Numa tampa plana aparada isso superestima grosseiramente.
>
> A assinatura do bug: **2608,4 × 2333,8** aparecia idêntico em objetos completamente diferentes — é a caixa da superfície-base das tampas, não da peça.
>
> | Objeto | bbox solta (antiga) | bbox real (malha) |
> |---|---|---|
> | rodada 4, Sonnet | 2608,4 × 2333,8 | **2400,0 × 829,4 × 1100** — passa |
> | sessão 69f7b15a | 2608,4 × 2333,8 | 1619,4 × 2053,5 — falha |
> | rodada 2 (`balcao_v1`) | 6116,4 × 5682,3 | 5099,6 × 5099,7 — falha |
>
> **`check.py` corrigido**: mede pelas malhas de render, calcula volume, e quando não há malha no arquivo trata a caixa solta como **limite superior** — só reprova por falta (medido menor que o esperado); acima do esperado devolve `INCONCLUSIVO`, nunca reprovação. Veredito novo: `PASSOU` / `FALHOU` / `INCONCLUSIVO`.
>
> ### O que foi retratado
>
> - **Rodada 1, "agente inventou a corda 2400"** — **retirado**. Os 2835,1 eram caixa solta; a corda real pode muito bem ser 2400. Hoje esse eixo é `INCONCLUSIVO` (o arquivo não tem malha de render). Continuam de pé a falha em Y (580,6 vs 829 — como a caixa solta é limite superior, o valor real é ainda menor, então reprova com certeza) e a camada `Default`.
> - **Rodada 2, "agente relatou 5100, medido 6116"** — **retirado**. O número do agente estava **correto**: a peça mede 5099,6 × 5099,7. Eu é que media errado.
> - **"Três modos distintos de relato falso"** — **reformulado**. Não houve fabricação de número. O padrão real é outro, e mais útil: nas rodadas 1 e 2 o Haiku **mediu de forma aceitável e julgou errado** — declarou OK com desvio que ele mesmo tinha medido e citado. É a regra "tolerância é binária" não pegando, não alucinação de medida.
>
> As conclusões sobre camada, orçamento de chamadas, geometria órfã, rota de script e API inventada **não dependem da bbox** e seguem válidas.

Caso em teste: `balcao_01` (`evals/cases.jsonl`).
Esperado: sólido fechado, bbox **2400 × 829 × 1100 mm**, volume **~1,455e9 mm³**, camada **ESTANDE::Mobiliario**, tol 1%, orçamento 25 tool calls.

**Fonte de verdade = saída de `evals/check.py`.** A autoavaliação do agente não é evidência; é dado a ser comparado com a medição.

Comando de verificação usado em todas as rodadas:

```
uv run --with rhino3dm python evals/check.py <arquivo.3dm> \
  --bbox 2400 829 1100 --tol 0.01 --layer "ESTANDE::Mobiliario"
```

---

## Relato do agente vs medido

| Rodada | Modelo | Critério | Relato do agente | Medido (check.py) | Veredito |
|---|---|---|---|---|---|
Medições já corrigidas pelo `check.py` novo. Onde o arquivo não tem malha de render, a coluna traz a caixa solta, que é **limite superior** do valor real.

| Rodada | Modelo | Critério | Relato do agente | Medido | Veredito |
|---|---|---|---|---|---|
| 1 | Haiku 4.5 | bbox X (corda) | 2400 ✓ | ≤ 2835,1 (sem malha) | **inconclusivo** |
| 1 | Haiku 4.5 | bbox Y (profundidade) | 569 | ≤ 580,6 vs 829 esperado | FALHOU |
| 1 | Haiku 4.5 | camada | RECEPÇÃO::Balcão | **Default** | FALHOU |
| 1 | Haiku 4.5 | conclusão | "OK" | **FALHOU** | — |
| 2 | Haiku 4.5 | bbox X e Y | 5100 (anel 332°) | **5099,6 × 5099,7** | relato **correto** |
| 2 | Haiku 4.5 | bbox vs esperado | — | 5100 vs 2400 × 829 | FALHOU |
| 2 | Haiku 4.5 | camada | — | **Default** | FALHOU |
| 2 | Haiku 4.5 | nº de sólidos | 1 | **2 Breps no arquivo** | FALHOU |
| 2 | Haiku 4.5 | conclusão | "OK" | **FALHOU** | — |
| 3-bis | Haiku 4.5 | sólido | "NÃO CONCLUÍDO" | 0 Breps fechados | relato **correto** |
| 3-bis | Haiku 4.5 | arquivo gerado | `v3.3dm` | **não existe no disco** | FALHOU |
| 4 | **Sonnet 5** | bbox | 2400 × 829,41 × 1100 | **2400,0 × 829,4 × 1100** | ✓ |
| 4 | **Sonnet 5** | volume | 1,45517·10⁹ | **1,45495·10⁹** | ✓ (0,004%) |
| 4 | **Sonnet 5** | IsSolid / camada | true / ESTANDE::Mobiliario | true / ESTANDE::Mobiliario | ✓ |
| 4 | **Sonnet 5** | conclusão | "aprovado" | **PASSOU** | — |

**O padrão não é fabricação de número — é erro de julgamento.** Nas rodadas 1 e 2 o Haiku mediu de forma aceitável e concluiu errado: na rodada 2 ele reconheceu explicitamente um anel de 332°, reportou 5100 (número **correto**, confirmado na re-medição) e mesmo assim marcou OK. A regra "tolerância é binária" da skill não virou comportamento. Na rodada 4, o Sonnet relatou o que o servidor mediu, dígito por dígito, e a conclusão bateu com o `check.py`.

---

## Rodada 1

- **Modelo:** claude-haiku-4-5-20251001
- **Sessão MCP:** `04c4c2d1`, linhas 2–46 do `logs/rhino_calls.jsonl`
- **Tool calls:** 45 chamadas MCP registradas no log (o histórico antigo do caso dizia 65 — ver "Pendências")
- **Arquivo:** salvou `output/balcao_recepcao_v1.3dm`; esse conteúdo sobrevive hoje só como `output/balcao_recepcao_v1.3dmbak`, arquivado em `output/_rodadas/rodada1_balcao.3dm`
- **Veredito:** FALHOU
- **Falhas:** bbox X 2835,1 vs 2400 (18,1%); bbox Y 580,6 vs 829 (30,0%); camada Default vs ESTANDE::Mobiliario. `IsValid` e `IsSolid` = true, 1 Brep no arquivo.
- **Assinatura da geometria:** objetos `balcao_arco_interpolado` (curva interpolada, não arco), `balcao_offset_final`, `balcao_perfil_final` (**PolylineCurve** — o perfil curvo virou polilinha), `balcao_v1`.
- **Hipótese de causa:** o agente usou curva interpolada no lugar de arco e fechou o perfil com polilinha, exatamente os dois erros que a skill passou a proibir no commit `200f2e5`. O X de 2835 indica offset para fora (sentido errado), não para o centro. Como mediu as curvas em vez do sólido, a verificação do passo 5 não pegou nada.

## Rodada 2

- **Modelo:** claude-haiku-4-5-20251001
- **Sessão MCP:** `a5b23bb6`, linhas 116–140 do `logs/rhino_calls.jsonl`
- **Tool calls:** 25 chamadas MCP (no limite exato do orçamento de 25 da skill)
- **Arquivo:** sobrescreveu `output/balcao_recepcao_v1.3dm` (16:45), arquivado em `output/_rodadas/rodada2_balcao.3dm`
- **Veredito:** FALHOU
- **Falhas:** bbox X 6116,4 vs 2400 (154,8%); bbox Y 5682,3 vs 829 (585,4%); camada Default; **2 Breps** no arquivo (Extrusion 5996×5571×1100 + Brep 6116×5682×1100) — sobrou geometria de tentativa.
- **Assinatura da geometria:** `balcao_solido_v1`, 12 de 25 chamadas foram `execute_rhinoscript_python_code` mais uma `execute_rhinocommon_csharp_code` — o agente abandonou as tools nativas e foi para script.
- **Hipótese de causa:** erro de ângulo do arco (332° ≈ anel quase completo em vez do setor de 0,49 rad). Um anel de R=2550 dá bbox 5100×5100, e o offset para fora leva a 6116×5682. O agente **reconheceu** o anel de 332° e ainda assim marcou OK: aqui a fórmula da skill não foi aplicada e a regra "tolerância é binária" foi ignorada com o desvio já medido na frente.

## Rodada 3 — ANULADA (contaminação de contexto, não é resultado do modelo)

- **Modelo:** claude-haiku-4-5-20251001
- **Sessão:** `7bd9dc3f` — **nenhuma chamada MCP**. Log continuou em 140 linhas.
- **Tool calls:** 0. `num_turns` = 1, 11,1 s, US$ 0,058, 25.841 tokens de cache creation.
- **Veredito:** ANULADA. Nenhuma geometria foi criada; não há arquivo para o `check.py`.
- **O que o agente respondeu:** assumiu o papel de *supervisor* e pediu ao usuário que abrisse um documento novo no Rhino e rodasse `mcpstart` — recitando o protocolo de rodada ("vou anotar o estado inicial do log do agente"). O agente sob teste virou avaliador de si mesmo e ficou esperando confirmação.
- **Causa (confirmada por timestamp):** o `claude -p` roda com cwd `rhino-agent/`, e o Claude Code carrega os `CLAUDE.md` dos diretórios **pais**. O arquivo `C:\Users\eacosta\dev\CLAUDE.md` (papel de supervisor + protocolo de rodada) foi criado às **16:55**, entre a rodada 2 (16:45) e a rodada 3 (17:18). O agente recebeu as instruções do supervisor por cima do próprio `rhino-agent/CLAUDE.md` e obedeceu às do supervisor.
- **Consequência para as rodadas anteriores:** rodadas 1 (16:29) e 2 (16:45) são **anteriores** ao arquivo de 16:55 e portanto **não foram contaminadas**. Os vereditos delas continuam válidos.
- **A hipótese "limite do modelo vs problema de skill" segue sem teste.** A rodada 3 não mediu o Haiku; mediu um furo de isolamento do harness.

### Efeito colateral observado

`output/balcao_recepcao_v1.3dm` foi reescrito às 17:18 com a **mesma geometria da rodada 2** (6116,4 × 5682,3 × 1100) — provavelmente o Rhino salvando o documento antigo ao abrir o novo. Isso empurrou o conteúdo da rodada 2 para o `.3dmbak` e **destruiu o `.3dmbak` da rodada 1**. As cópias em `output/_rodadas/` eram a única outra via de recuperação.

### Correção necessária antes da rodada 3-bis

O `--bare` desliga a auto-descoberta de `CLAUDE.md`, **mas também desliga os hooks** — sem o hook não há log, e sem log não há contagem de tool calls. Não serve. A correção tem que ser tirar o `CLAUDE.md` do supervisor da árvore de pais de `rhino-agent/`.

**Correção aplicada (17:2x):** `C:\Users\eacosta\dev\CLAUDE.md` → `C:\Users\eacosta\dev\supervisor\CLAUDE.md`. Não resta nenhum `CLAUDE.md` em `dev/` nem acima; o único na árvore de `rhino-agent/` é o do próprio agente. O arquivo do supervisor ganhou uma seção "Isolamento" proibindo recriar `CLAUDE.md` em `dev/`.

**Isolamento verificado por sonda** (`claude -p "qual e o seu papel neste projeto?"`, 0 chamadas MCP, US$ 0,019): o agente respondeu *"Sou o agente NURBS deste projeto: inspecciono, construo e verifico geometria no Rhino 8 via MCP..."*. Antes da correção, a mesma árvore produzia um agente que se apresentava como supervisor.

## Rodada 3-bis — VÁLIDA, FALHOU (sem sólido e sem artefato salvo)

- **Modelo:** claude-haiku-4-5-20251001 · **Sessão:** `dcf27bed` · linhas 141–208 do log
- **Validade:** `num_turns` = 88, 68 chamadas MCP novas, 413,8 s, US$ 0,88. Rodada legítima (contraste com a rodada 3, que teve 0).
- **Tool calls: 68 — orçamento da skill é 25.** Estourou em 172% e não parou para reportar, como a skill manda.
- **Veredito: FALHOU.** Não há sólido fechado e **não há arquivo** para o `check.py`: as duas tentativas de salvar falharam (linhas 207 e 208).
- **Rota:** 22 de 68 chamadas foram `execute_rhinocommon_csharp_code` — de novo o agente abandonou as tools nativas e foi para script, a última opção da ordem de preferência da skill.

### O que mudou para melhor

**Pela primeira vez o agente não mentiu sobre o sólido.** Marcou explicitamente "⚠️ Sólido final: **NÃO CONCLUÍDO**" e descreveu a causa real (extrusão produziu "fatias", boolean difference falhou). Nas rodadas 1 e 2 ele marcou OK com desvios de 30% e 585%.

**A geometria de referência da skill foi aplicada certo.** Calculou antes de modelar: R = 2550, r = 1950, θ ≈ 0,49 rad, bbox esperada ~2400 × 831 × 1100. É o alvo correto — a seção "Geometria de referência" da skill funcionou.

### O que continua quebrado

| Regra da skill | O que o agente fez |
|---|---|
| "Crie o arco como arco (3 pontos), **nunca** como curva interpolada" | usou **curva interpolada** de novo (mesmo erro da rodada 1) |
| "Orçamento: se passar de 25 tool calls, pare e reporte" | 68 chamadas, sem parar |
| "Nunca invente o nome de um método RhinoCommon" | inventou `Rhino.FileIO.FileSaveOptions` — erro de compilação `CS0234`, o tipo não existe |
| "Salve pelo próprio Rhino, com caminho absoluto dentro de ./output" | os dois saves falharam e **mesmo assim** relatou "Arquivos Gerados: /output/balcao_recepcao_v3.3dm" |

**Relato do agente vs medido:** o único item falso que sobrou é o artefato — declarou um arquivo que não existe no disco. O restante do relato bate com a realidade.

### Medição descartada por decisão do usuário

A geometria da 3-bis ficou só no documento aberto do Rhino e **não foi salva manualmente**: optou-se por não intervir no resultado do agente. O veredito FALHOU se apoia no relatório do próprio agente (sem sólido fechado) e na ausência de artefato — **não** em saída do `check.py`. Não há medição pendente para esta rodada; a linha `medido` fica nula em definitivo.

### Falha de save (causa técnica)

1. Linha 207, C#: `new Rhino.FileIO.FileSaveOptions()` → `CS0234: The type or namespace name 'FileSaveOptions' does not exist in the namespace 'Rhino.FileIO'`. API inventada.
2. Linha 208, `run_command: SaveAs "...\balcao_recepcao_v3.3dm"` → sem prefixo de traço (`_-SaveAs`), o comando abre diálogo modal em vez de executar direto. Nenhum arquivo foi criado.

---

## Rodada 4 — Sonnet 5 — **PASSOU**

- **Modelo:** `claude-sonnet-5`, via `claude --model sonnet` na chamada. O `settings.json` do agente **não foi alterado** — as travas dele seguem intactas e o modelo foi a única variável.
- **Sessão:** `bd2747a2`, linhas 209–217 do log
- **Tool calls: 9** — contra 45, 25 e 68 das rodadas de Haiku. Orçamento da skill é 25.
- **14 turnos, 41,5 s, US$ 0,25.**
- **Veredito: PASSOU.** bbox 2400,0 × 829,4 × 1100 (desvio 0,048% em Y), volume 1,4549·10⁹ vs 1,455·10⁹ (0,004%), `IsSolid` true com 6 faces e 0 arestas nuas, camada `ESTANDE::Mobiliario`, 1 único Brep no arquivo — sem geometria de construção sobrando.
- **Fidelidade do relato:** o `analyze_objects` do servidor devolveu `bbox_dimensions: [2400, 829.4117647058824, 1100.0000000000002]` e volume `1455173258,697`. O agente relatou exatamente isso. **Não houve desvio entre o que mediu e o que reportou.**

### Primeiras vezes em 217 chamadas registradas

- **Chamou `get_modeling_guidance("verification")`.** As três rodadas de Haiku pararam no `overview`, apesar de o passo 5 da skill mandar ler `verification` desde sempre.
- **Criou a camada hierárquica corretamente** — `ESTANDE`, depois `Mobiliario` com parent. Nenhuma rodada de Haiku acertou a camada.
- **Usou arco de 3 pontos**, como a skill manda, em vez de curva interpolada.

### O que ainda desviou da skill

| Regra | O que fez |
|---|---|
| "Salve pelo próprio Rhino, dentro de `./output` com sufixo `_vN`" | **não salvou** — "não salvei o arquivo, porque você não pediu". Salvo depois pelo usuário como `v4` para permitir a medição |
| Ordem de rotas: template > tool nativa > comando > script | foi direto para **C#**, a última opção |
| Superfície disponível | não tocou em `gh_*`, `include_health` nem `dry_run` |

A justificativa que deu para o script é **parcialmente verdadeira**, e a parte falsa passou despercebida até 20/09: não existe template Grasshopper (`gh-templates/` está vazio) nem arco **por 3 pontos** — mas **existe `create_object` com `type: "ARC"`** (centro, raio, ângulo), que outras três sessões usaram com sucesso, e `offset_curve` tipado. Ver a correção na seção "Harness v2". A primeira tentativa em C# falhou por erro de compilação (`CS1061`, tratou `int` como objeto com `.Index`) e ele corrigiu na segunda — diferente da 3-bis, que inventou um tipo inexistente e não se recuperou.

---

## Conclusões até aqui

1. **A hipótese está resolvida do lado do modelo: Sonnet passa, Haiku não.** Mesma skill, mesmo prompt, mesmo caso, mesma superfície de tools. 9 chamadas contra 45/25/68, e a primeira aprovação da série.
2. **O modo de falha do Haiku é julgamento, não medição.** Ele mede de forma aceitável e conclui errado — a rodada 2 reportou 5100 (número correto) e marcou OK. A regra "tolerância é binária" está escrita e não vira comportamento. Isso é diferente de alucinar número, e muda o tipo de correção que faz sentido.
3. **Nenhuma rodada de Haiku acertou a camada.** O Sonnet acertou na primeira.
4. **A skill funciona — quando é lida.** A seção "Geometria de referência" produziu R=2550, r=1950 e θ correto no Haiku (3-bis) e no Sonnet. O que o Haiku não executa é a parte de verificação e de disciplina.
5. **O instrumento de medida era o elo fraco.** Um bug de bbox no `check.py` reprovou geometria correta e distorceu o registro de três rodadas. Corrigido; ver o aviso no topo.
6. **Custo:** Sonnet US$ 0,25 por peça aprovada contra US$ 0,88 do Haiku na 3-bis, que não entregou peça. O modelo mais caro saiu mais barato por resultado.

### Perguntas ainda abertas

- **Uma rodada não é série.** `balcao_01` é 1 caso de 30. O Sonnet passou uma vez; isso não é taxa de aprovação.
- **Haiku com a skill corrigida ainda não foi testado.** A fila de candidatas (`include_health`, `gh_*`, `dry_run`) existe justamente para atacar o modo de falha de julgamento. Pode ser que o Haiku passe com elas — o que muda a conta de custo do PRD.
- **O Sonnet não salvou o arquivo.** Numa execução autônoma isso significaria perder o trabalho. É candidata de skill, não de modelo.

---

## Pendências e riscos do harness

- **Sessão `69f7b15a` não atribuída a nenhuma rodada.** 69 chamadas MCP (linhas 47–115). É quase certo que produziu `output/balcao_recepcao_v2.3dm` (`balcao_final`, bbox real por malha **1619,4 × 2053,5 × 1100**, volume 9,695·10⁸ vs 1,455·10⁹ esperado, não é sólido fechado, camada RECEPÇÃO::Balcão, 4 Breps, veredito FALHOU): o nome `balcao_final` só aparece nessa sessão e o mtime do arquivo (16:38) cai na janela dela. Ressalva: **o save desse arquivo não aparece no log** — as duas sessões que salvam (`04c4c2d1` e `a5b23bb6`) gravam o path `balcao_recepcao_v1.3dm`, e nenhuma grava `_v2`. Ou o save saiu por um caminho não coberto pelo hook, ou o arquivo foi salvo à mão no Rhino. Arquivada em `output/_rodadas/sessao_69f7b15a_balcao.3dm`. O `tool_calls: 65` que constava no histórico do caso é próximo dessas 69 e provavelmente foi anotado dessa sessão, não da rodada 1.

- **Rodadas 1 e 2 gravaram o mesmo path.** Confirmado no log: `04c4c2d1` salvou `./output/balcao_recepcao_v1.3dm` e `a5b23bb6` salvou `C:\Users\eacosta\dev\rhino-agent\output\balcao_recepcao_v1.3dm` — o mesmo arquivo, o que explica a rodada 1 ter sobrado apenas como `.3dmbak`.
- **Rodadas sobrescrevem o arquivo umas das outras.** O agente salvou `_v1` duas vezes; a rodada 1 só sobreviveu como `.3dmbak` e teria sido perdida na próxima gravação. Mitigação aplicada: cópias em `output/_rodadas/`. A rodada 3 deve salvar em nome novo (`balcao_recepcao_v3.3dm`).
- ~~`check.py` não verifica volume~~ — **resolvido**. Mede volume pelas malhas de render (`--volume`). Na rodada 4 deu 0,004% de desvio.
- ~~`check.py` usava bbox de casco de controle~~ — **resolvido**, era o bug grave. Ver o aviso no topo.
- **`check.py` ainda escolhe o Brep de maior bbox.** Com sobra de geometria no arquivo (rodada 2 tinha 2, a sessão 69f7b15a tinha 4), pode avaliar o objeto errado — e o ranking mistura caixa justa com caixa solta quando parte dos objetos não tem malha. Na rodada 2 isso faz o alvo cair no Brep sem malha. O campo `breps_no_arquivo` é o sinal de alerta.
- **Arquivo sem malha de render não é mensurável.** Rodadas 1 e 2 não têm malha, então bbox e volume ficam `INCONCLUSIVO` para cima. Rodada futura deve garantir que o save preserve malha de render.

---

---

# HARNESS v2 — série nova a partir de 20/09

> ## ⚠️ A BASELINE ANTIGA NÃO É COMPARÁVEL
>
> As rodadas 1, 2, 3-bis e 4 foram medidas com `RHINO_MCP_PERCEPTION` **desligado**. A partir daqui ele está ligado, e o servidor anexa `_health` e `_delta` ao resultado de **toda** operação que modifica o documento. O modelo passa a ver, dentro do próprio retorno da operação, informação que nenhuma rodada anterior viu.
>
> Isso muda o contexto de entrada, não só a ferramenta. **Qualquer comparação direta de taxa de aprovação entre as duas séries é inválida.**
>
> A numeração recomeça: **harness v2, rodada 1** — não "rodada 5". Chamar de rodada 5 sugeria uma continuidade que não existe.
>
> O que **continua** comparável: o caso `balcao_01` não mudou (mesmo prompt, mesma bbox esperada, mesmo `check.py`), então "entregou a peça certa?" significa a mesma coisa nas duas séries. As 4 rodadas antigas seguem válidas como **baseline histórica**: 1 aprovação em 4, e o modo de falha documentado.

## A mudança, e só ela

Uma linha, em `.mcp.json`:

```json
"env": { "RHINO_MCP_PERCEPTION": "1" }
```

O servidor põe `include_delta` e `include_health` no envelope de toda mutação (`server.py:547`). O plugin devolve os ids criados e removidos, e os objetos que falham validade com o motivo. **O modelo não participa dessa decisão.**

É a candidata nº 1 da fila, que era a de maior evidência: nunca usada em 217 chamadas, e ataca direto o modo de falha central — declarar sucesso sem verificar. Como virou configuração de servidor, saiu da fila: não precisa de rodada para medir se o modelo obedece, porque ele não tem como não obedecer.

Nada mais mudou. A skill está em `200f2e5`, intocada.

## ✅ A CADEIA FECHOU PONTA A PONTA — `PASSOU` medido — 22/09

> Sondagem fora da série, sem veredito de modelo. Oito invocações `claude -p`, **US$ 1,69**.
> Log: 392 → 431 linhas (39 chamadas registradas; as que falharam não entraram — ver achado
> de instrumento abaixo). A variável não era o modelo; era o harness.

### O resultado

`LLM → parâmetros → template → Rhino → .3dm` fecha pela primeira vez, medido pelo `check.py`:

```
veredito: PASSOU
bbox      2400,0 × 829,4 × 1100   fonte: malha
is_solid  true       volume 1,4543·10⁹ mm³
casco de controle (o que se mediria sem malha): 2608,4 × 2333,8
```

Dois defeitos tiveram de cair no caminho, e nenhum dos dois era o previsto.

### Defeito 1 — `component_name` não identifica componente

A remontagem falhou **antes** de rodar, no `gh_build_graph`:
`Could not find output parameter on source component 'Flatten'.`

O template pedia a saída `Data` do `flatAll`. Confirmado no `_canvas_bruto.json`: a saída **é**
`Data` (nickname `D`, descrição *"Squished data"*). O conversor gravou certo. O servidor é que
criou outro componente:

| | inputs | output |
|---|---|---|
| canvas de 20/09 | `Data` | `Data` — *"Squished data"* |
| servidor em 22/09 | `Tree`, `Path` | `Tree` — *"Flattened data tree"* |

Mesmo `name` (`Flatten Tree`), mesmo `nickname` (`Flatten`), mesma `category/subcategory`
(`Sets/Tree`) — **componentes diferentes**. E os dois canvases foram montados pelo próprio
`gh_build_graph` (`graph_id: MCPGraph_*`), do mesmo JSON.

**A resolução por nome de exibição é ambígua e devolveu componentes diferentes em duas sessões,
sem o JSON mudar.** O `gh_get_canvas_state` não expõe GUID de *tipo* — só `instance_id` (por
instância) e `graph_id` (por montagem), nenhum dos dois estável entre documentos. **O template
não tem como dizer qual componente quer.**

Isso é a lição de 21/09 um nível abaixo. Lá, o conversor jogava fora informação que existia.
Aqui, **a informação não existe no dump** — e o `README` do `gh-templates/` promete
reprodutibilidade que o formato não pode sustentar sozinho.

**Correção aplicada, mínima:** `Flatten Tree` tem saída única nas duas variantes, então o índice
é estritamente mais robusto que o nome. Uma linha em `gh-templates/balcao.json`:

```diff
-      "source_output_name": "Data",
+      "source_output_index": 0,
```

Levantamento completo antes de mexer: os 21 componentes foram criados num canvas limpo **sem
nenhuma conexão** e o `gh_get_canvas_state` comparado campo a campo com o template. Das 26
conexões, **só o `flatAll` não casava**. Os 5 sliders/Panel são `standalone_parameters`, não
têm lista `outputs`, e o servidor aceita o que o conversor põe ali.

**A regra que sai disto:** `source_output_name` só quando a origem tem **mais de uma** saída;
saída única usa `source_output_index: 0`. O nome serve para desambiguar, e desambiguar é a única
coisa que ele faz bem — identificar, não.

### Defeito 2 — bake sem malha entrega arquivo que o instrumento não lê

Remontado e resolvido limpo (`error_count: 0`, `join` com `data_count: 1` e `is_closed: true`,
`cap` com Brep `is_solid: true`, 6 faces — tudo lido do log, não do relato), o bake rodou e o
`.3dm` saiu **`INCONCLUSIVO`**, com `2608,4 × 2333,8`. É a assinatura literal do bug de
instrumento de 19/09: sem malha de render, o `rhino3dm` só entrega o casco dos pontos de
controle, que é limite superior.

Verificado no arquivo: **zero malhas**, em `Render`, `Analysis`, `Preview` e `Any`.

Sombrear o viewport (`_-SetDisplayMode _Mode=_Shaded`, `_-SelAll`, `_-Zoom`, `_-Save`) **não
resolveu** — segunda medição idêntica. A malha precisa existir *no objeto* e ser comitada.

**Correção aplicada em `evals/bake_gh.py`**, que é o lugar certo: quem bakeia é quem deve
entregar arquivo mensurável.

```python
mp = Rhino.Geometry.MeshingParameters.DocumentCurrentSetting(doc_rh)
for gid in ids:
    ro = doc_rh.Objects.FindId(gid)
    if ro and ro.CreateMeshes(Rhino.Geometry.MeshType.Render, mp, False) > 0:
        ro.CommitChanges()
```

Saiu `objetos com malha de render: 2` — os 2 Breps; pontos e curvas não têm malha, e não
precisam. A medição seguinte deu `PASSOU`.

### Achado de instrumento: o log não registra chamada que falha

O `gh_build_graph` do defeito 1 **não aparece** em `logs/rhino_calls.jsonl`. O que teve sucesso,
aparece. O hook é `PostToolUse` e não dispara em erro de tool.

**Consequência, e não é pequena:** a contagem de chamadas de toda rodada **subestima**, e o modo
de falha mais interessante — o agente tentar, errar e tentar de novo — é justamente o invisível.
Um agente que erra cinco vezes e acerta na sexta registra uma chamada. Some-se a isso que o
orçamento de tool calls é critério de caso, e o número que se compara com ele não é o número real.

### Ressalvas, para não virar otimismo

1. **Ainda sobra geometria de construção.** 16 objetos bakeados, 2 mensuráveis; o `check.py`
   avisa *"sobrou geometria de construcao"*. O seletor de componente continua não existindo.
   O alvo foi escolhido certo (`malha > sólido fechado > maior caixa` pegou o Brep do `cap`),
   mas por regra de desempate, não porque o bake entregou só o que importa.
2. **`_SaveSmall=_No` não é opção de `_-SaveAs` neste build.** O Rhino salvou e depois reclamou
   `Unknown command: _SaveSmall=_No`. O arquivo tem as malhas porque elas foram comitadas no
   objeto, não porque a opção pegou. Se algum dia o padrão de SaveSmall virar `Yes`, isto
   quebra silenciosamente e volta o `INCONCLUSIVO`.
3. **Nenhuma rodada de modelo aconteceu.** Isto é harness. O placar da série v2 não mudou.

### O que o agente fez bem, e vale registrar

Parou **quatro vezes** em vez de improvisar: no `gh_build_graph` que falhou, no
`gh_create_document` que devolveu `created: false` com 21 objetos de sondagem anterior, e no
`_SaveSmall` recusado — neste último recusando-se inclusive a relatar o `object_count`, com o
argumento de que relatar implicaria que o save era confiável. Prompt com parada condicional
explícita produziu relato fiel de máquina, que foi o que permitiu diagnosticar. Nos três casos
o relato do agente bateu com o log.

## POR QUE O TEMPLATE NÃO REMONTAVA: a saída de origem, jogada fora — 21/09

> Trabalho de mesa. A remontagem no Rhino **não chegou a rodar** — a conexão caiu
> (`Could not connect to Rhino at 127.0.0.1:1999`). Causa identificada e corrigida; falta a prova.

### A causa

O conversor `evals/gh_canvas_para_template.py` gravava, de cada conexão, a **origem** e o índice de
entrada do destino — e **jogava fora de qual saída da origem** o fio saía:

```python
saida.append({"source": mapa[oid], "target": destino,
              "target_input_index": entrada["index"]})
```

O `End Points` tem duas saídas, `(0, 'Start')` e `(1, 'End')`. As duas linhas do perfil puxam dele:

```
lnS.in[1] <- ends . param_name='Start'
lnE.in[1] <- ends . param_name='End'
```

No template convertido, as duas viraram a mesma coisa:

```json
{"source": "end", "target": "ln",   "target_input_index": 1}
{"source": "end", "target": "ln_2", "target_input_index": 1}
```

Sem o nome da saída, o `gh_build_graph` cai na **saída 0** nas duas. As duas linhas passam a sair do
mesmo ponto, o perfil não fecha, o `Join Curves` devolve 2 ramos e o `Cap Holes` falha — **cinco
componentes adiante da causa**. Foi por isso que o diagnóstico apontou para o `Flatten Tree`, que
sempre esteve correto.

**A informação nunca faltou:** o `param_name` do `gh_get_canvas_state` é exatamente o nome da saída.
O conversor lia `component_id` e descartava o resto do dicionário.

### A correção, com o campo que o contrato define

O contrato do servidor (`contracts/commands/gh_build_graph.json`, `$defs/connection`) declara
`source_output_index` e `source_output_name` — este último descrito como *"Output parameter name or
nickname on source"*. Não foi preciso inventar nada:

```json
{"source": "ends", "source_output_name": "Start", "target": "lnS", "target_input_index": 1}
{"source": "ends", "source_output_name": "End",   "target": "lnE", "target_input_index": 1}
```

**O contrato marca o campo como opcional, e na prática ele é obrigatório** para qualquer origem com
mais de uma saída. Template regenerado: `source_output_name` nas 26 conexões.

### Rede de segurança, e o teste que tenta enganá-la

A perda era **silenciosa** — o conversor rodava sem erro e só quebrava na remontagem, longe da
causa. O conversor agora avisa quando uma conexão vem de origem com mais de uma saída sem dizer
qual. Aplicando a lição de 21/09 (*"todo instrumento novo precisa de um caso de teste que tente
enganá-lo"*), foi verificado nos dois sentidos:

| Entrada | Resultado |
|---|---|
| template corrigido | 0 ambíguas — sem falso positivo |
| formato antigo (nomes removidos) | **5 ambíguas**, incluindo `ends → lnS` e `ends → lnE` |

Cinco, não duas: `arco → off`, `vec → extr` e `arco → flatAll` também eram ambíguas. Só as duas do
`ends` mudavam o resultado de forma visível; as outras três calhavam de querer a saída 0 mesmo.
**O template estava mais quebrado do que o sintoma mostrava.**

### Ganho colateral: os aliases voltaram a ser legíveis

O conversor derivava alias do *nickname*, e três `Construct Point` com nickname `Pt` viravam `pt`,
`pt_2`, `pt_3`, numerados por ordem de iteração. O canvas já trazia `alias` próprio — `pA`, `pB`,
`pC`, `arco`, `off`, `ends`, `lnS`, `lnE`, `flatAll` — posto lá pelo `gh_build_graph` original.
Agora o conversor prefere esse, e só deriva quando não há alias válido.

Consequência de interface: o slider `profundidade` virou **`prof`**, que sempre foi o nome real do
grafo. Os aliases são a interface pública do template — é neles que o PRD encosta o "o LLM preenche
parâmetros de algo já declarado" — então o `README.md` foi corrigido junto.

### O que isto diz sobre a aposta do formato versionado

O JSON **não era** reprodutível, e ninguém saberia até tentar. A promessa do `README` (*"é diffável
no git, é exatamente o que `gh_build_graph` consome"*) era verdadeira sobre o formato e falsa sobre
o conteúdo: faltava um campo que o contrato não exige e o servidor precisa.

Isso não derruba a aposta — corrige uma implementação dela. Mas estabelece que **todo template novo
precisa ser remontado e rodado antes de ser considerado versionado.** Converter sem erro não prova
nada.

## ✅ O BAKE FUNCIONA — a rota IronPython alcança o Grasshopper — 21/09

> Sondagem fora da série, sem veredito. Duas invocações, 6 chamadas MCP, **US$ 0,44** no total.
> Sessões `03b4d3a6` (passo 1) e `4f90861f` (passo 2). Log: 385 → 391 linhas.

### O resultado

**`clr.AddReference("Grasshopper")` funciona dentro do `execute_rhinoscript_python_code`.**
Sem exceção. `gh.Instances.ActiveCanvas.Document` devolveu o documento. O `BakeGeometry` entregou
geometria ao documento do Rhino.

Saída literal do script (`evals/bake_gh.py`, enviado verbatim):

```
componentes bakeaveis: 12
objetos bakeados: 18
camada: ESTANDE::Mobiliario (indice 2)
```

**Confirmado por evidência independente do relato do agente** — resposta do servidor a
`get_document_summary`, lida do `logs/rhino_calls.jsonl`, não da narração:

```json
"object_count": 18,
"objects_by_type": {"ARC": 5, "POINT": 5, "LINE": 4, "BREP": 3, "CURVE": 1},
"objects_by_layer": {"Mobiliario": 18},
"model_bounding_box": [[-1200.0, -529.4117647058824, 0.0], [1200.0000000000005, 300.0, 1100.0]]
```

Isso é **2400 × 829,41 × 1100 mm** — o alvo verificado do `balcao_01`. O documento tinha 0 objetos
antes; a camada `ESTANDE::Mobiliario` foi criada pelo script, com o pai já existente.

**A hipótese estava certa, e pelo motivo previsto.** A rota C# falhou porque o assembly do
Grasshopper está fora da compilação; IronPython resolve em tempo de execução. Era a diferença.

### O que isto decide

**A seção 5 do PRD fica de pé.** `LLM → parâmetros → template → Rhino → .3dm` fecha: a última seta
existe, e é um script versionado do harness, não autoria do modelo. O plano B — abandonar o `.gh`
e migrar para script com schema — **não será executado**.

O bloqueio arquitetural de 20/09 está **resolvido**, e resolvido sem trocar de servidor, sem
perder a baseline e sem reescrever o PRD.

### Três ressalvas, antes que isto vire otimismo

1. **O script bakeou tudo que era bakeável: 18 objetos**, incluindo geometria de construção
   (5 pontos, 5 arcos, 4 linhas). Produção precisa de **seletor de componente** — bakear a saída
   do alvo, não o canvas inteiro. Está previsto, mas não está feito.
2. **Os 3 BREPs não são sólido fechado.** O `Cap Holes` falhou nesta remontagem (ver seção
   seguinte), então são extrusões sem tampa. O bake entregou o que havia; não havia sólido.
3. **A bbox bater com o alvo é encorajador, não é prova.** É a caixa dos 18 objetos juntos,
   curvas de construção incluídas. Coincide com o alvo; não demonstra que o sólido está certo.
   Prova mesmo só sai com `.3dm` salvo e passado pelo `check.py`.

### 🛑 Achado colateral, e é sério: o template versionado não remonta

O `gh_build_graph` montou os 21 componentes e as 26 conexões do `gh-templates/balcao.json` sem
erro, mas a solução **não rodou limpa**: `Cap Holes` deu
`Capping algorithm failed to return a result.`

Diagnóstico do agente: o `Join Curves` saiu com `data_count: 2` — o perfil não fechou numa curva
única — e `Extrude` e `Cap Holes` herdaram os dois ramos.

**É a armadilha que o `gh-templates/README.md` declara resolvida.** O `Flatten Tree` está no
template (componente `flatten`) e a fiação está correta: `arc`, `offset`, `ln`, `ln_2` entram todos
no `flatten` (input 0), que alimenta o `join`. Ainda assim o join não fechou.

**Consequência para a arquitetura, não só para este template:** o JSON versionado é o artefato que
o PRD aposta como reprodutível — *"é diffável no git, é exatamente o que `gh_build_graph` consome"*.
**Essa reprodutibilidade acabou de falhar na primeira tentativa de exercê-la.** O grafo que
funcionou em 20/09 e o grafo remontado a partir do JSON não são o mesmo grafo.

Duas hipóteses, nenhuma investigada: o conversor `evals/gh_canvas_para_template.py` perde
informação (ordem de entrada? enxerto de árvore?), ou o `gh_build_graph` liga de um jeito que o
canvas original não tinha. **Isto precisa ser resolvido antes de qualquer caso de eval de
template** — senão o template não é artefato versionado, é rascunho.

## SERVIDOR DA McNEEL: VERIFICADO E DESCARTADO — e a rota que sobrou — 21/09

> Trabalho de mesa, sem Rhino e sem rodada. Levantamento de código-fonte via `gh`, não de documentação.

### A pergunta, e a resposta

O bloqueio de 20/09 (o Grasshopper não entrega geometria) tinha três saídas, e a preferida era
**trocar pelo servidor oficial da McNeel**, condicionada a uma incógnita: *ele faz bake?*

**Não faz.** Inventário completo das tools do `mcneel/RhinoAI`, tirado dos arquivos-fonte:

| Família | Tools | Bake? |
|---|---|---|
| Documento/cena | 27 (`CreateTool`, `SaveDocTool`, `ListObjectsTool`, `RunPythonTool`, `RunCSharpTool`, `RunCommandTool`…) | não |
| Grasshopper 1 | 13 (`Start`, `ClearCanvas`, `SearchComponents`, `DescribeComponent`, `PlaceComponent`, `PlaceSlider`, `Connect`, `ConnectMany`, `Delete`, `ApplyGraph`, `GetCanvasGraph`, `Solve`) | **não** |
| Grasshopper 2 | 14, espelhando GH1 | **não** |

Três provas independentes:

1. **`BakeGeometry`** — a chamada do RhinoCommon que comete geometria no documento — tem
   **0 ocorrências** no repositório inteiro.
2. "Bake" aparece **2 vezes** em todo o repo: num gerador de IDs aleatórios (coincidência) e numa
   página de documentação que **alerta contra** bakear — *"the cheapest way to 'match' your
   geometry is to bake your existing Rhino objects into the GH output. That's not parametric."*
3. `rhino/plugin/Tools/GH1/GH1_SolveTool.cs` prova a arquitetura: opera sobre
   `IGH_PreviewObject`, calcula `GetPreviewBoundingBox` e dá zoom na **pré-visualização**. É a
   mesma lacuna que temos.

Não é repositório abandonado: push em 21/09/2026, 316 estrelas, MIT, releases em julho e setembro.
**É ausência da capacidade, não falta de manutenção.**

**Decisão: não trocar. Fechada por evidência, não por preferência.** Trocar zeraria 6 rodadas e
14 casos **e não resolveria o problema que motivou a troca**. A terceira razão de 19/09 ("trocar
zera a baseline") não só continua válida como agora é a única que importa — as outras duas viraram
irrelevantes, porque o benefício que as compensaria não existe.

**Confirmação lateral do nosso próprio bloqueio:** o código do servidor atual diz de si mesmo
*"Grasshopper preview is live but not baked"* (`plugin/Functions/GrasshopperHelpers.cs:169`) e
reporta `has_baked_rhino_objects`. E a `0.4.1.1` instalada **já é a última tag** — não há upgrade
esperando. O bloqueio registrado no `ESTADO.md` está correto.

### O achado que reabre o `.gh`: bake é do plugin, não do protocolo

O único servidor com bake (`EaseHee/rhino-mcp` — imaturo: 8 estrelas, 1 fork, parado desde maio)
delega a um bridge C# que roda **em processo com o Grasshopper**:

```python
def gh_bake_to_rhino(args: _BakeIn) -> dict[str, Any]:
    """Bake the output of one or more components into the active Rhino document."""
    return runtime().require_bridge().call("gh.canvas.bake", args.model_dump())
```

Ou seja: **bake não é capacidade do MCP, é de quem está dentro do processo.** E nós já temos duas
portas para esse mesmo processo — só uma foi testada.

| Rota | Estado | Por quê |
|---|---|---|
| `execute_rhinocommon_csharp_code` | **falhou** | assembly do GH fora da compilação; por reflexão, `NullReferenceException` |
| `execute_rhinoscript_python_code` | **nunca tentada para bake** | — |

**O motivo da falha do C# é exatamente o que a rota Python contorna.** O plugin executa scripts com
`PythonScript.Create()` (`plugin/Functions/ExecuteRhinoscript.cs:23`), que no Rhino 8 é
**IronPython 2.7, em processo**. IronPython resolve assembly em **tempo de execução** via
`clr.AddReference("Grasshopper")` — a peça que faltava na compilação C#.

Se alcançar, o bake vira **script fixo, versionado e revisado**: infraestrutura do harness, como o
`check.py`. O princípio da seção 5 do PRD fica intacto — o LLM continua emitindo só parâmetros;
quem bakeia é o harness.

**Tensão a controlar, dita aqui para não ser esquecida depois:** `execute_rhinoscript_python_code`
é a superfície de código arbitrário que o projeto fechou de propósito (61 de 208 chamadas em
script; a API inventada da 3-bis). A mitigação é o bake **nunca ser autoria do modelo** — script
literal, versionado, executado por passo do runner. Isso é disciplina, não trava.

**Pendente: a sondagem que responde.** Fora da série, sem veredito, US$ 0,05–0,20, exige Rhino
aberto com o template no canvas. É o próximo passo do projeto.

### Correção de instrumento: as séries não se separavam sozinhas

O `cases.jsonl` não tinha como distinguir as séries a não ser pela **caixa da palavra** do veredito
(`PASSOU` vs `falhou`) — convenção adotada em 20/09 e escrita na skill de onboarding. **Ela não se
sustenta:** a `rodada 4` da série antiga está gravada como `PASSOU` **maiúsculo**. Toda contagem
automática somava um veredito pré-v2 à série v2, inflando o placar em um PASSOU (dava 6 PASSOU
onde a v2 tem 5).

Achado pela própria skill de onboarding, que leu o número inflado na primeira execução.

**Corrigido:** todo registro de `historico` agora tem campo **`serie`** explícito (`pre-v2` | `v2`);
a nota descritiva que vivia no campo `serie` da `v2r1` virou `nota_serie`. Nenhum outro campo foi
tocado — verificado por diff registro a registro contra backup. O placar por série passa a ser:

| Série | Vereditos |
|---|---|
| `pre-v2` | falhou 3 · anulada 1 · **PASSOU 1** ← o que contaminava |
| `v2` | **PASSOU 5** · FALHOU 1 |

A skill de onboarding foi corrigida junto: conta pelo campo, e avisa se algum registro aparecer
com `serie SEM CAMPO`.

**O padrão, de novo:** é o terceiro defeito de instrumento do projeto (bbox solta em 19/09, falso
`PASSOU` do `julga_recusa` em 21/09, e agora a separação de séries). Os três eram invisíveis até
alguém medir contra o disco em vez de ler o documento.

## SEGUNDO LEITOR DE RECUSA — Jev/TypeSafe, aditivo — 21/09

> Trabalho de mesa, sem Rhino e sem rodada. Nenhuma chamada ao Jev foi feita ainda.

### O viés que estava no instrumento, e a direção dele

O `julga_recusa()` aprova quando um dos `sinais_de_recusa` do caso aparece no relato, por substring sem acento. **Substring não lê negação.** Este relato aprova hoje:

```
"Nao e impossivel construir essa peca, entao fiz uma aproximacao
 com profundidade de 2000 mm."
```

Casa com o sinal `impossivel` → `PASSOU`. É um falso positivo, e o pior tipo: aprova uma rodada em que o agente fez exatamente o que o caso proíbe (improvisar peça aproximada).

**A direção do viés importa mais que a existência dele.** O `impossivel_01` declara 8 sinais, vários genéricos (`impossivel`, `excede`, `negativo`, `inconsistente`). Lista larga pega quase qualquer recusa genuína, então o risco de *aprovação perdida* é baixo; o risco concentrado é **falso `PASSOU`**. Isso é o oposto do viés de 19/09, em que o instrumento reprovava geometria correta. O instrumento errou nas duas direções em dois lugares diferentes — a lição não é "o check.py era frouxo", é que **todo instrumento novo precisa de um caso de teste que tente enganá-lo**.

### Por que um modelo, e por que não como veredito

Recusa correta é julgamento semântico: texto não se verifica por código com o rigor de uma bbox. O Jev (TypeSafe System One) devolve resposta tipada com probabilidade em vez de texto para parsear — resolve o problema de **interface**, que é o que substring faz mal. Não resolve o de verdade, e os docs da própria TypeSafe são explícitos: *"typed output guarantees the interface, not truth."*

Então ele entra **aditivo**, nunca como veredito. Trocar o instrumento agora repetiria o erro de 19/09: instrumento novo sem histórico re-medido. O plano é acumular N rodadas com os dois leitores lado a lado e só então decidir.

Garantias por construção, em `evals/rodada.py`:

| Garantia | Como |
|---|---|
| não influencia o veredito | roda **depois** de `julga_recusa()`, nem por ordem de execução |
| `FALHOU` por artefato nunca vai a modelo | continua mecânico e primeiro |
| não derruba rodada | sem pacote, sem chave ou rede fora → `{"indisponivel": motivo}`; todo `Exception` capturado |
| `sys.exit()` | continua vindo só do veredito mecânico |

Minutos de Rhino aberto não podem morrer por causa de um leitor opcional.

### As três perguntas

Independentes sobre o mesmo estado, então vão numa requisição só e rodam em paralelo — nenhuma vê a resposta da outra:

| Pergunta (Noul) | O que resolve |
|---|---|
| `recusou_a_tarefa` | recusou, ou entregou aproximação? |
| `motivo_geometrico_correto` | acertou a causa que o caso declara em `por_que_e_impossivel`? |
| `parou_por_obstaculo_tecnico` | desistiu por erro de ferramenta, não por juízo? |

A terceira é a que justifica o esforço: ela nomeia a dúvida que o `INCONCLUSIVO` já descrevia em prosa — *"pode ter desistido em vez de recusar"*. E **não** é a negação da primeira: o agente pode recusar com critério E ter batido num erro de ferramenta.

Contrato lido dos docs: campo de probabilidade `noul`, faixa 0–1; **Noul não tem `confidence` separado** (*"There is no separate `confidence` value for a Noul"*). Limiares `JEV_ALTO = 0.85` / `JEV_BAIXO = 0.15`, assimétricos porque o falso `PASSOU` é o erro caro. Sobrescreve por caso em `check.limiar_jev`.

### Testado offline, 5 caminhos

Os cinco se comportam: falso positivo detectado com `DIVERGENCIA FORTE`, corroboração, obstáculo técnico sinalizado, artefato vencendo tudo mecanicamente, degradação sem chave. **O caminho feliz nunca rodou** — não há chave no ambiente, então o contrato do SDK (`TypeSafeClient()` como context manager, `response.nouls[k].noul`) está lido dos docs, não verificado. Pendente: smoke test antes da primeira rodada.

### Segurança

O repositório é **público**. `.env` e `.env.*` entraram no `.gitignore`; varredura do histórico com `git rev-list --all` não achou nenhuma ocorrência de chave. A chave mora em variável de ambiente do usuário (`setx`), nunca em `.claude/settings.json` — esse arquivo é rastreado.

## PRIMEIRO TEMPLATE GRASSHOPPER — e o elo que falta na arquitetura — 20/09

> Sessão `ec9b77a3`, linhas 359–385. 34 turnos, 27 chamadas MCP, 163,3 s, **US$ 0,7542** — a mais cara do projeto.
> **Primeiro uso de tools `gh_*` em 385 chamadas registradas.**

### O que funcionou

O agente descobriu a superfície com `gh_batch_search_components`, montou o grafo com `gh_build_graph` numa chamada, e iterou com `gh_mutate_graph`. **21 componentes, 26 conexões, 4 sliders nomeados** (`corda`, `flecha`, `profundidade`, `altura`).

A solução roda com 0 erros e 0 warnings. Perfil fechado de 5609,6 mm = arco externo 2498,8 + arco interno 1910,8 + 2 linhas de 600. `Cap Holes` produz Brep **sólido de 6 faces**. R = 2550, pontas do arco interno em Y = −529,4 → 829,4 mm de profundidade. Consistente com o alvo verificado.

Duas armadilhas de montagem, que valem para os próximos templates:

- **Offset com distância positiva vai para fora** — perfil saiu com 3086 mm em vez de 1910. Precisa de `Negative`.
- **`Join Curves` gera ramos separados** quando as linhas vêm de árvore mais profunda que o arco. Precisa de `Flatten Tree` antes.

### 🛑 O que não existe: bake

**As 27 tools `gh_*` constroem e calculam, e nenhuma entrega geometria ao documento do Rhino.** Verificado no código do servidor e no log.

| Capacidade | Existe? |
| --- | --- |
| montar, ligar, rodar, ler erros | sim |
| ler o que um parâmetro produziu | **só metadado** |
| **bake para o Rhino** | **não existe** |
| salvar o `.gh` | não existe |

O `gh_get_parameter_value` devolve `{"type":"Brep","is_solid":true,"faces":6}` — descrição, não geometria. Sem vértices, sem serialização. A rota C# de dentro do Rhino também não alcança: o assembly do Grasshopper não é referenciado na compilação, e por reflexão deu `NullReferenceException`.

**A seção 5 do PRD desenha `LLM → parâmetros → template .gh → Rhino → .3dm`. A última seta não existe neste servidor.**

### Comportamento do agente: exemplar

Marcou **NÃO CONCLUÍDO**, disse que o alvo não foi verificado, e explicitou que o que tinha era leitura dos componentes do GH e **não** medição no Rhino — *"não é a verificação que você pediu"*. Declarou o efeito colateral (duas camadas vazias criadas) e **recusou-se a salvar** um `.3dm` só com camadas, porque seria enganoso. Parou nas 2 tentativas que a skill permite.

É o oposto exato da rodada 3-bis, que declarou um arquivo inexistente. Nona saída seguida de relato fiel.

### O que ficou versionado

- `gh-templates/balcao.json` — o grafo no formato de entrada do `gh_build_graph`, com os domínios dos sliders. **Formato versionado é JSON, não `.gh`**: não há `gh_save`, e o JSON é diffável e consumível direto.
- `gh-templates/_canvas_bruto.json` — resposta literal de `gh_get_canvas_state`, para a conversão poder ser auditada.
- `evals/gh_canvas_para_template.py` — o conversor. Existe porque sem ele o grafo morre ao fechar o Rhino, e refazê-lo custa US$ 0,75.

### ⚠️ Isto é o gatilho para reavaliar o servidor MCP

A seção "Adiado" condicionava a troca a *"necessidade de Rhino 9, necessidade de Grasshopper 2, ou fila de candidatas de skill esgotada"*. **Há agora um quarto motivo, mais forte que os três: o servidor atual não consegue entregar a geometria do Grasshopper.**

Isso reabre a comparação com o `mcneel/RhinoAI`, que foi rejeitado em 19/09 com três razões. Duas delas precisam ser relidas à luz disto:

1. *"o oficial lidera com scripting, que é a rota das nossas falhas"* — enfraquecida. As sondagens de 20/09 mostram o agente usando script com sucesso e consultando docs por conta própria, e a rota C# foi reabilitada por evidência.
2. *"não se sabe se o oficial tem equivalente ao `include_health`"* — enfraquecida. Medimos que o `include_health` cobre 2 de 27 respostas e nenhuma tool de criação de geometria. Vale menos do que se supunha.
3. *"trocar zera a baseline de evals"* — **continua válida**, e agora custa mais: são 6 rodadas e 13 casos.

**Não decidido.** Fica registrado como a questão aberta mais importante do projeto.

---

## SONDAGEM 2 — form-finding (fora da série, sem veredito) — 20/09

> Desenhada para forçar a rota de **superfície**, depois de a sondagem 1 entregar
> orgânico só na silhueta. Sessão `c129745a`, linhas 351–358 do log.

**Briefing:** *"cobertura tipo vela: superfície de dupla curvatura, vão 4000 × 3000, ancorada em 4 pontos, altura máxima 2800. A forma tem que ser ENCONTRADA por relaxação (form-finding), como uma membrana tensionada — não desenhada. Nada de chapa recortada, extrusão de perfil ou loft."*

**14 turnos, 8 chamadas MCP, 55,0 s, US$ 0,1921.**

### Entregou form-finding de verdade

> **Método:** densidades de força, resolvido por relaxação iterativa numa malha de 21 × 16 nós (passo 200 mm). **985 iterações**, resíduo final 1e-4 mm. Bordas como cabos, densidade 6 contra 1 da malha — por isso caem em curva côncava.

Verificado na captura de viewport: **paraboloide hiperbólico anticlástico**, cabos de borda côncavos, sela genuína. É a forma de livro de uma membrana tensionada em quatro pontos — a mesma que o `references/organico-gh.md` cita como caso útil ("cobertura tipo vela apoiada em quatro pontos").

bbox 4000 × 3000 × 2000, Z de 800 a 2800 — vão e altura máxima batendo exatamente. Superfície aberta, 4 arestas nuas, que são as bordas.

**Contraste com a sondagem 1:** lá o orgânico estava na silhueta de uma chapa; aqui está na **superfície**, encontrada por um solver. E saiu **3× mais barata**: US$ 0,19 contra US$ 0,58, em 8 chamadas contra 20.

### ⚠️ Isso mexe com o raciocínio da seção 5 do PRD

A decisão registrada é: *"O LLM emite parâmetros, nunca geometria. A forma orgânica mora no template Grasshopper."* O motivo dado inclui que o modelo erra a topologia.

**Aqui o modelo implementou densidades de força corretamente, num único script, e acertou a topologia.** Isso não derruba a decisão — as razões de **governança** seguem inteiras: execução de código arbitrário é RCE em servidor multiusuário, script não é reproduzível como slider de template, e o eval de um template é mais barato que o de um gerador de código.

Mas muda a **justificativa**: a restrição é de governança e reprodutibilidade, não de capacidade. Convém corrigir isso no PRD, porque um argumento que se apoia em limitação de capacidade envelhece mal.

### Terceira parede segue de pé, e agora com 358 chamadas

**Zero `gh_*` de novo.** O agente cita o motivo no próprio relato:

> "Não usei nenhum template, porque não existe nenhum em `gh-templates/`."

Ele não está ignorando a rota nº 1 da skill — está constatando que ela não existe. **A rota Grasshopper não vai aparecer por instrução; precisa de template construído.**

### Lacuna nº 3 do instrumento, encontrada aqui

O `check.py` reprovava `IsSolid = false` **incondicionalmente**. Uma vela é superfície aberta por definição, e o agente justificou corretamente as 4 arestas nuas. **Hypar perfeito, veredito `FALHOU`.**

Corrigido com `--solido {fechado|aberto|qualquer}`, default `fechado` para preservar o comportamento. No caso, vem de `check.is_solid`: ausente = não verifica. Testado nos dois sentidos — a vela passa como `aberto`, e um cilindro fechado reprova num caso que pede `aberto`. Regressão dos 5 arquivos intacta.

É a terceira lacuna do mesmo tipo em um dia: **o instrumento foi escrito supondo que toda entrega é um sólido fechado de dimensões exatas.** Forma orgânica quebra as três suposições — dimensão exata, tipo Brep, e fechamento.

---

## Instrumento: Mesh, SubD e envelope — 20/09

Duas das três paredes levantadas pela sondagem orgânica foram derrubadas. Mudança no `check.py`, que é a fonte de verdade — **histórico inteiro re-medido, nenhum veredito mudou.**

### 1. Envelope em vez de igualdade

`--bbox-max` e `--bbox-min` por eixo, com `0` significando "sem limite neste eixo". Motivo medido: a sondagem pediu *"400 mm de profundidade máxima"*, a peça deu 322,8 — **satisfazia** — e o `check.py` devolvia `FALHOU` por 19,3%, porque comparava igualdade.

A mesma peça, agora:

| Comando | Veredito |
| --- | --- |
| `--bbox 2400 400 2200` (igualdade) | `FALHOU` — bbox Y 322,8 vs 400 |
| `--bbox-max 0 400 0 --bbox-min 2300 0 2150` | **`PASSOU`** |
| `--bbox-max 0 300 0` (teto que ela de fato estoura) | `FALHOU` — excede o teto |

Assimetria deliberada, na mesma lógica da caixa solta: medida **acima** do teto com caixa solta vira `INCONCLUSIVO` (a caixa solta superestima, a real pode não estourar); medida **abaixo** do piso reprova sempre (se até o limite superior ficou abaixo, a real ficou também).

### 2. O instrumento enxerga Mesh e SubD

Antes lia só Brep — `if not isinstance(g, r.Brep): continue`. Malha, SubD e curva eram **puladas**, e o veredito saía "nenhum Brep no arquivo". Para a frente orgânica isso era uma bomba: **Kangaroo relaxa malha.**

| Tipo | bbox | volume | sólido |
| --- | --- | --- | --- |
| Brep / Extrusion | malhas de render | divergência | `IsSolid` |
| **Mesh** | vértices | divergência, só se fechada | `IsClosed` |
| **SubD** | caixa de controle, **limite superior** | **não medido** | `IsSolid` |

**SubD fica incompleto, e declarado como tal.** O `rhino3dm` 8.35 não expõe a superfície limite — só `Mesh.CreateFromSubDControlNet`, que devolve a rede de controle, a mesma classe de aproximação que causou o bug de bbox de 19/09. Fingir precisão aí seria repetir o erro. Verificado por arquivo sintético: malha fechada de 300 × 200 × 100 mede volume 6.000.000 exato.

### 3. Defeito encontrado no caminho: eixo esperado zero

`--bbox` com `0` num eixo levantava `ZeroDivisionError`. Geometria plana — região planar, malha aberta, chapa sem espessura — tem eixo zero legitimamente, e o instrumento **quebrava**. Agora eixo zero vira comparação absoluta contra uma fração do maior eixo do caso.

O bug é anterior a esta mudança; só não tinha aparecido porque nenhum caso até aqui tinha eixo nulo.

### Verificações feitas

- **Regressão:** os 5 arquivos com veredito registrado seguem `PASSOU`.
- **Arquivo sem malha** (rodada 1): segue `FALHOU` em Y e `INCONCLUSIVO` em X, idêntico ao registrado.
- **Malha fechada sintética:** bbox e volume exatos.
- **Malha aberta:** bbox correta com Z = 0, `is_solid` false, volume `INCONCLUSIVO` com a causa certa ("malha aberta"), não com a mensagem genérica de malha ausente.

**Ainda de pé:** curva. Uma teia é rede de curvas e o `check.py` continua sem enxergá-la. Não foi feito porque curva não tem volume nem sólido, e o tipo de check para ela (comprimento total, número de segmentos, conectividade) ainda não tem caso que o justifique.

---

## SONDAGEM — forma orgânica (fora da série, sem veredito) — 20/09

> **Não é rodada de eval.** Sem caso, sem veredito, não entra no placar. Feita para
> descobrir onde a forma orgânica quebra, antes de investir código em qualquer
> uma das três paredes previstas. Sessão `25491602`, linhas 331–350 do log.

**Briefing:** *"divisória orgânica para estande, inspirada em coral: 2400 × 2200 mm, 400 mm de profundidade máxima, com ramificação e vazados. Superfície contínua, não uma treliça de tubos. Camada `ESTANDE::Divisoria`."*

**26 turnos, 20 chamadas MCP, 277,4 s, US$ 0,5843** — a mais cara de todas, ~3,4× uma primitiva.

**Entregue:** `output/divisoria_coral_v1.3dm`, um Brep sólido fechado, 166 faces, 0 arestas nuas, camada certa, arquivo limpo. bbox medida 2409,2 × 322,8 × 2200,0.

### Rota: C#, seis vezes

| Tool | Chamadas |
| --- | --- |
| `execute_rhinocommon_csharp_code` | **6** |
| `capture_viewport` | 4 |
| `get_modeling_guidance` | 3 |
| `create_layer` | 3 |
| outras | 4 |

**Zero tools `gh_*`.** O contador chega a **350 chamadas registradas sem uma única chamada de Grasshopper.**

Para geração de forma, o agente vai para código — e é razoável: não existe tool tipada para silhueta ramificada, e a ordem de preferência da skill começa por "template já existente", que não existe. **É a evidência mais forte até aqui contra a proposta de fechar a rota C#**, que já tinha sido reprovada na análise de 20/09. Tivesse sido aplicada, esta sondagem não teria saído do lugar.

### Parede 1 (instrumento só vê Brep) — não se aplicou aqui, mas segue de pé

A saída foi **Brep**, e o `check.py` a enxergou normalmente. A previsão de que forma orgânica sairia como malha estava errada **para esta rota**: o agente fez chapa recortada e extrudada, que é NURBS.

A parede continua válida para a rota que o PRD aposta — Kangaroo relaxa **malha**, e malha o `check.py` ignora. Só não foi essa a rota tomada.

### Parede 2 (igualdade vs restrição) — confirmada, com demonstração

O briefing pediu **"400 mm de profundidade máxima"**. A peça deu 322,8 mm, o que **satisfaz o pedido**. Rodando o `check.py` com 400 como esperado:

```
veredito: FALHOU
falhas: ["bbox Y: medido 322.8 vs esperado 400.0 (19.3%)"]
```

**Geometria correta, reprovada pelo instrumento.** Não é bug: o `check.py` compara igualdade, e o briefing declarou um teto. Caso orgânico precisa de um tipo de check novo — faixa (`min`/`max`) por eixo em vez de valor com tolerância. É pré-requisito de qualquer caso de tier orgânico.

### O que a peça é, de fato

Vista pela captura de perspectiva: ramificação convincente — troncos, bifurcações, pontas afinando, ondulação em Y dando profundidade. Lê mais como galho seco ou gorgônia do que como coral de recife, exatamente como o agente disse de si mesmo.

**Mas o orgânico está na silhueta, não na superfície.** É uma chapa de 40 mm recortada com contorno ramificado e ondulada num eixo. As famílias de gerador da seção 4 do PRD — casca relaxada com âncoras, malha inflada, dupla curvatura — são sobre a **superfície** ser orgânica. Isto é gráfico orgânico extrudado: resolve a divisória como produto, e **não exercita a arquitetura que o PRD aposta**.

### Autoavaliação do agente: acurada, inclusive no estético

> "A silhueta ainda lê mais como árvore ramificada do que como coral. (…) não é um coral convincente. Vi só a vista frontal da silhueta e uma perspectiva com auto-zoom, então a impressão visual é subjetiva."

Declarou o que não verificou (posição dos vazados, se a chapa fica de pé), a fragilidade estrutural da base (barra de ~130 mm), as premissas que adotou (espessura 40 mm, origem) e que usou **semente fixa, logo reproduzível**. Oitava saída seguida de relato fiel — e a primeira em que ele julga a própria forma como insuficiente tendo cumprido todas as medidas.

### Consequências

1. **Tipo de check por faixa** (`min`/`max` por eixo) é pré-requisito para tier orgânico. Sem ele, envelope máximo vira reprovação.
2. **`check.py` precisa ler Mesh e SubD** antes de qualquer rodada com Kangaroo.
3. **A rota `gh_*` não vai aparecer sozinha.** 350 chamadas, zero uso. Se a arquitetura do PRD depende dela, precisa de template no `gh-templates/` e de menção explícita na skill — hoje a skill manda usar "template já existente", e não existe nenhum.
4. **Custo de forma orgânica: ~US$ 0,58** contra ~US$ 0,17 de uma primitiva. Relevante para o guardrail de US$ 0,15 por pedido do PRD, que já estava apertado.

---

## harness v2, rodada 6 — **PASSOU** · o boolean que derrubou a 3-bis

- **Caso:** `caixa_furo_01` (tier fácil, único com boolean) · **Sessão:** `13a191fd` · linhas 316–330
- **21 turnos, 15 tool calls** (orçamento 15, **exatamente no limite**), **40,2 s**, **US$ 0,2338**
- **Veredito: PASSOU.** `output/caixa_furo_v1.3dm`, 1 Brep, arquivo limpo.

```
bbox      1000,0 × 800,0 × 400,0     volume 291.809.808
camada    ESTANDE::Mobiliario        7 faces · 0 arestas nuas
```

**O boolean é a operação que falhou na 3-bis** ("extrusão produziu fatias, boolean difference falhou"). Aqui passou na primeira, e o agente fez o que a skill manda para booleans: cilindro de corte com **420 mm**, 10 mm sobrando de cada lado, para evitar faces coincidentes. Apagou o cortador depois.

### O facetamento troca de sinal em feature subtrativa

| Medida | Valor | Desvio |
| --- | --- | --- |
| Analítico (caixa − furo) | 291.725.666,1 | — |
| Malha (`check.py`) | 291.809.808,2 | **+0,0288%** |
| Brep (`analyze_objects`) | 291.725.666,0 | 0,0000% |

**O desvio é positivo.** Na v2r5 a malha media *para menos*; aqui mede *para mais*. A causa é a mesma e o sinal inverte: a malha da parede do furo é **inscrita** no cilindro, então o furo fica menor do que é e sobra volume no sólido.

Consequência prática: tolerância de caso curvo precisa ser **bilateral**, e não dá para supor a direção do erro pelo tipo de superfície — depende de a curvatura ser aditiva ou subtrativa. O `check.py` já compara em módulo, então nada a mudar; mas a nota em `references/armadilhas-mcp.md` estava simplificada e foi corrigida.

### Validação incidental da correção do `check.py`

O `bbox_solta` deste caso é **1000 × 800 × 420** — a caixa de controle acusa Z = 420, que é a altura do cilindro de corte antes de aparado. A malha deu **400,0 exato**.

É exatamente a classe de erro do bug de 19/09 (casco de controle em vez de malha), reaparecendo num caso novo. **Se o `check.py` não tivesse sido corrigido, esta rodada reprovaria por 5% em Z** com geometria perfeita. Segunda vez que o bug teria distorcido um veredito.

### Relato do agente vs medido

Fiel. O volume do Brep bate com o analítico até o inteiro; a diferença para o `check.py` é a nuance de malha já registrada na v2r5. Declarou as premissas (raio e não diâmetro; origem no centro da base), o sobre-comprimento do cortador e o fato de não ter olhado o viewport.

**E reportou a armadilha de camada por conta própria**, sem ser perguntado:

> `get_or_set_current_layer` com `ESTANDE::Mobiliario` não trocou a camada atual, que continua `Default`. (…) Objetos novos criados depois sem esse passo vão para `Default`.

Terceira sessão em que a armadilha aparece, segunda em que o agente a detecta e contorna. Sétima rodada seguida de relato fiel.

**Hipótese de causa:** o caso foi resolvido pela rota tipada com boolean nativo, dentro do orçamento. Reforça o padrão da v2r5 — primitiva e operação tipada saem baratas; o custo alto da série veio da composição do `balcao_01`.

---

## harness v2, rodada 5 — **PASSOU** · calibra o facetamento da malha

- **Caso:** `cilindro_01` (tier fácil, primeiro curvo) · **Sessão:** `21f5fb88` · linhas 306–315
- **16 turnos, 10 tool calls** — **primeira rodada da série dentro do orçamento** (10 de 10)
- **26,9 s**, **US$ 0,1722** — a mais barata e a mais rápida até aqui
- **Veredito: PASSOU.** `output/cilindro_estrutura_v1.3dm`, 1 Brep, arquivo limpo.

```
bbox      600,0 × 600,0 × 900,0      exato
volume    254.328.523                camada ESTANDE::Estrutura
```

### A calibração: o facetamento é 36× menor do que eu arbitrei

| Medida | Valor | Desvio do analítico |
| --- | --- | --- |
| Analítico (π·300²·900) | 254.469.004,9 | — |
| **Malha de render** (o que o `check.py` mede) | 254.328.522,9 | **0,055%** |
| **Brep** (o que o `analyze_objects` devolve) | 254.469.006,0 | 0,0000% |

A bbox saiu **exata**: os vértices da malha caem sobre a superfície, e num cilindro os extremos em 0°, 90°, 180° e 270° são atingidos.

**Tolerância dos curvos apertada de 2% para 0,5%**, nos casos de curvatura simples (`cilindro_01`, `tubo_01`, `cone_01`, `calha_01`, `caixa_furo_01`) — 0,055% medido deixa 9× de folga. `esfera_01` e `toro_01` **ficam em 2%**: curvatura dupla faceta nas duas direções e o erro é maior, ainda sem medição.

Regra do projeto cumprida: mudou o instrumento, re-mediu o histórico. `cilindro_01` é o único caso com rodada registrada afetado pelo aperto, e o veredito continua `PASSOU` sob 0,5%.

### ⚠️ Em caso curvo, agente e `check.py` medem coisas diferentes — e os dois estão certos

O agente relatou 254.469.006 e o `check.py` mediu 254.328.523. **Não é divergência de fidelidade.** O `analyze_objects` devolve o volume do **Brep** (a superfície exata); o `check.py` mede pela **malha de render** (a aproximação facetada).

Isso vale para toda geometria curva daqui em diante: o número do agente vai bater com o analítico e o do instrumento vai ficar ligeiramente abaixo. **Não leia essa diferença como relato infiel** — é a assinatura de duas medições legítimas de objetos diferentes. Em caso planar os dois coincidem.

### Relato do agente vs medido

Fiel, com a ressalva acima. Declarou a premissa de posição (base na origem), informou que criou as duas camadas e que não tocou nas existentes, e confirmou o save com o tamanho em bytes. Sexta rodada seguida de relato fiel.

**Hipótese de causa do sucesso e do baixo custo:** caso de primitiva pura, com a tool tipada resolvendo em uma chamada. É o comportamento que a arquitetura do PRD aposta — e o contraste com as 36 chamadas da v2r2 sugere que o custo alto vem da composição (arco + offset + join + extrusão), não da modelagem em si.

---

## harness v2, rodada 4 — **PASSOU** · primeiro caso do tier fácil

- **Caso:** `prisma_hex_01` (tier fácil, estreia do dataset ampliado) · **Sessão:** `5f7984fe` · linhas 289–305
- **24 turnos, 17 tool calls** (orçamento 12, estouro de 42%), **44,7 s**, **US$ 0,2692**
- **Veredito: PASSOU.** `output/totem_prisma_hex_v1.3dm`, salvo pelo agente, 1 Brep, arquivo limpo.

```
bbox      800,0 × 692,8 × 700,0      exatamente o esperado
volume    290.984.531                desvio 0,00016% do analítico
camada    ESTANDE::Totem             is_solid · 8 faces · 0 arestas nuas
```

A orientação declarada no pedido ("dois vértices sobre o eixo X") foi respeitada — vértices em 0°, 60°, … 300°. Sem essa frase no caso, a bbox alternaria entre 800 × 692,8 e 692,8 × 800.

**Calibração do instrumento:** este é caso planar, e a malha de render bateu com o analítico em 0,00016%. Confirma que a tolerância de 0,5% para planares é folgada com sobra. A dos curvos (2%) continua sem calibração — precisa de uma rodada de cilindro ou esfera.

### 🔎 Armadilha de API encontrada: `get_or_set_current_layer` falha em silêncio

| Chamada | Entrada | Retorno |
| --- | --- | --- |
| 5 | `get_or_set_current_layer {"name": "ESTANDE::Totem"}` | `"Current layer: Default"` — **sem erro** |
| 7 | `get_or_set_current_layer {"name": "Totem"}` | `"Current layer: Totem"` — funciona com o **nome da folha** |
| 13 | `update_object_attributes {"layer": "ESTANDE::Totem"}` | funciona com o **caminho completo** |

A tool aceita só o nome da folha para definir a camada atual. Com caminho hierárquico ela **não define nada e devolve uma string que parece sucesso** — `"Current layer: Default"` é uma resposta bem-formada, indistinguível de uma leitura. Quem não comparar o retorno com o que pediu segue achando que funcionou.

### ⚠️ Isso corrige a leitura das rodadas de Haiku

Estava registrado: *"Nenhuma rodada de Haiku acertou a camada. O Sonnet acertou na primeira."* **Verdadeiro e incompleto.**

O log mostra que a **rodada 1** chamou `get_or_set_current_layer` com `RECEPÇÃO::Balcão` duas vezes, recebeu `"Current layer: Default"` nas duas, e nunca usou `update_object_attributes`. E mostra que **o Sonnet caiu na mesma armadilha em v2r1 e v2r4** — a primeira chamada devolveu `Default` igualmente.

**A armadilha pega os dois modelos.** O que separa não é conhecer camadas hierárquicas: é conferir o retorno contra o que se pediu. Reforça a conclusão já registrada de que o modo de falha do Haiku é de **verificação/julgamento**, e enfraquece a leitura de que ele "não sabia criar camada".

**Ressalva:** no log da rodada 1 o nome aparece como `RECEPÃ‡ÃƒO::BalcÃ£o` — mojibake de UTF-8 lido como latin-1. O hook só ganhou tratamento utf-8 no commit `200f2e5`, depois daquela rodada, então é **provável** que seja artefato de log e não do que foi enviado. Não dá para afirmar com o registro disponível.

### Relato do agente vs medido

Bate item a item, incluindo o volume com 8 dígitos. Declarou as premissas (altura em +Z a partir de Z=0; "raio circunscrito" como distância do centro ao vértice), **declarou a própria falha de camada e o contorno**, e confirmou o arquivo em disco com tamanho. Quinta rodada seguida de relato fiel.

**Hipótese de causa do estouro de orçamento (17 contra 12):** três das chamadas extras vêm do contorno da armadilha de camada (5, 6, 7 mais a 12 e 13 de conferência e correção). O orçamento de 12 foi estimado sem saber disso. É dado para a candidata nº 12: parte do estouro é custo de contornar a superfície, não desperdício do modelo.

---

## Instrumento: casos de recusa (tier borda) — 20/09

O PRD pede 6 casos de tier borda com "recusa correta em 100%". **O `check.py` não podia julgá-los**: ele mede `.3dm`, e recusa correta não produz arquivo. O runner classificava isso como `FALHOU — nenhum .3dm novo`, indistinguível de um fracasso real.

Agora o caso pode declarar `espera_recusa: true` e uma lista `sinais_de_recusa`. O veredito sai de `julga_recusa()` em `evals/rodada.py`:

| Saída | Quando | Confiança |
| --- | --- | --- |
| `FALHOU` | produziu `.3dm` num caso que pede recusa | mecânica, certa |
| `PASSOU` | sem artefato **e** o relato traz um sinal declarado no caso | mecânica, mas sobre texto |
| `INCONCLUSIVO` | sem artefato e sem sinal | **exige leitura humana** |

**Limitação declarada, não contornada.** Um `.3dm` se mede; uma recusa correta é texto, e texto não se verifica por código com o mesmo rigor. A regra adotada é a mesma que o `check.py` passou a usar depois do bug de bbox: **só aprova o que dá para checar; o resto vira `INCONCLUSIVO`, nunca aprovação.** Um agente que simplesmente desiste ("tentei várias abordagens e não consegui") cai em `INCONCLUSIVO`, não em `PASSOU` — testado.

Os sinais vêm do caso, não de uma lista global: o que conta como recusa correta muda conforme o caso seja dimensão impossível, pedido ambíguo ou topologia fora do catálogo. Comparação sem acento e sem caixa.

**Alternativa rejeitada:** LLM como juiz do relato. Acrescentaria não-determinismo ao instrumento, que é a única peça do sistema que precisa ser confiável. O projeto já teve um instrumento com viés reprovando geometria correta por três rodadas; a lição foi não repetir.

**Primeiro caso escrito:** `impossivel_01` — balcão de corda 2400, flecha 300 (R = 2550) e profundidade radial de 3000 mm. O offset daria raio interno de −450 mm; não existe sólido. O acerto é reconhecer isso **pela fórmula que a skill já traz**, antes de modelar. Ainda não rodado.

---

## harness v2, rodada 3 — **PASSOU**, mas o sinal é inconclusivo

- **Modelo:** `claude-sonnet-5` · **Sessão:** `4f1e0fa3` · linhas 281–288 do log
- **Variável testada:** candidata nº 11 — prefixo de traço em `run_command` entrou no fluxo obrigatório (commit `21a31ea`).
- **16 turnos, 8 tool calls** (orçamento 25), **44,9 s**, **US$ 0,2156**
- **Veredito: PASSOU.** `output/balcao_recepcao_v7.3dm`, salvo pelo agente, 1 Brep, arquivo limpo.

```
bbox      2400,0 × 829,4 × 1100        volume 1,454945589e9 (0,0035%)
camada    ESTANDE::Mobiliario          is_valid · is_solid · 0 arestas nuas
```

### ⚠️ O sinal previsto não foi medido de verdade

Antes de rodar ficou escrito: *"fração de `run_command` com traço deve ir de 11% para perto de 100%"*. Resultado: **1 de 1 com traço.**

**Isso não confirma a regra.** A rodada fez uma única chamada de `run_command` — o `_-SaveAs` final. A amostra é 1. O que se pode dizer é que a regra foi seguida na única vez em que se aplicou, e nada além disso.

### O que mudou de verdade foi a rota

| Rodada | Rota | Chamadas |
| --- | --- | --- |
| v2r1 | tipada: `create_object` + `offset_curve` ×2 + `extrude_curve`, Python só p/ join | 27 |
| v2r2 | tipada + `run_command` + Python, com comando interativo travado no meio | 36 |
| v2r3 | `get_rhinoscript_docs` → **um único script Python faz tudo** | 8 |

A queda de 36 para 8 chamadas **não é atribuível ao prefixo de traço**. É atribuível a o agente ter praticamente abandonado `run_command`. Duas leituras possíveis, e uma rodada não separa:

1. **Efeito colateral do texto.** A regra nova descreve `run_command` como rota que trava a sessão e não pode ser cancelada. Pode ter empurrado o agente para longe da rota inteira, não só para o traço.
2. **Variância.** Três rodadas, três rotas diferentes, mesmo prompt e mesma skill (fora a linha mudada).

A leitura 1, se verdadeira, é resultado bom por caminho errado: o objetivo era usar `run_command` corretamente, não evitá-lo. E contradiz a ordem de preferência da própria skill, que põe comando nativo **acima** de script.

### Variância de rota é achado próprio

Três rodadas seguidas, mesmo caso, mesmo modelo, rotas completamente diferentes. **A ordem de preferência da skill não está produzindo comportamento consistente** — em nenhuma das três o agente seguiu a ordem declarada (template → tool tipada → comando → script). Na v2r3 foi direto para a última opção.

Isso não apareceu antes porque as rodadas anteriores falhavam por outros motivos. Agora que três passam, a inconsistência fica visível. Candidata nova, nº 13.

### Terceira vez: consultou docs sem hook

Chamada 3, `get_rhinoscript_docs`, antes do script da chamada 5. Terceira rodada seguida em que o agente consulta a documentação por conta própria. **A regra do hook reprovado segue desnecessária.**

### Relato do agente vs medido

Bate item a item: bbox 2400,0 × 829,4 × 1100, volume 1,4552e9 contra 1,454945589e9 medido, sólido, camada certa, arquivo confirmado. Declarou a premissa da flecha (300 mm) e ofereceu refazer com outra.

**Declarou também uma omissão sua:** *"Não capturei o viewport, então a curvatura foi verificada só pelos números."* A skill manda capturar quando a forma é o critério. Ele não capturou e **disse que não capturou** — o oposto do modo de falha do Haiku.

**Hipótese de causa:** provável efeito colateral da redação, não adesão à regra. A rodada que viria a seguir deveria forçar uso de `run_command` para medir o traço com amostra real — ou a regra fica sem confirmação.

---

## harness v2, rodada 2 — **PASSOU** (a candidata nº 7 funcionou)

- **Modelo:** `claude-sonnet-5` · **Sessão:** `6fd25973` · linhas 245–280 do log
- **Variável testada:** candidata nº 7 — salvar virou o passo 6 do fluxo obrigatório (commit `e404dd2`). Nada mais mudou.
- **47 turnos, 36 tool calls** (orçamento 25, estouro de 44%), **162,9 s**, **US$ 0,5361**
- **Veredito: PASSOU.** `output/balcao_recepcao_v6.3dm`, salvo **pelo próprio agente** — primeira vez em 6 rodadas.

```
bbox      2400,0 × 829,4 × 1100        (fonte: malha)
volume    1,454944739e9                desvio 0,0035%
camada    ESTANDE::Mobiliario
is_valid true · is_solid true · 1 Brep · arquivo limpo
```

### A mudança de texto pegou — e o sinal previsto apareceu

Antes de rodar ficou escrito que o sinal seria "uma chamada de save entre `analyze_objects` e o fim". Chamada 30: `run_command _-SaveAs "C:\...\output\balcao_recepcao_v6.3dm"`, com o prefixo de traço que a skill passou a exigir.

**O diagnóstico estava certo.** O agente nunca desobedeceu: o fluxo obrigatório não passava por salvar, e a seção "## Salvar" ensinava onde salvar sem dizer que salvar é concluir. Movido para dentro do fluxo, o comportamento mudou na primeira tentativa.

### O mais valioso da rodada: ele detectou o próprio save falhando

O `_-SaveAs` da chamada 30 **não gravou**. Relato do agente:

> Salvei pela API do documento (`WriteFile`), não pelo `_-SaveAs`. O `_-SaveAs` foi engolido por um comando `_Arc` que travou no Rhino depois de um timeout meu. Reabri o arquivo e conferi o conteúdo.

As 6 chamadas depois do save (31–36) são isso: ele verificou, viu que não tinha arquivo, e refez por Python com `WriteFile`. A frase nova da skill — *"Confirme que o save retornou sucesso"* — funcionou num caso que ela não previa. É o oposto da 3-bis, que declarou um `v3.3dm` inexistente.

### Achado de harness: comando interativo trava a sessão e o MCP não cancela

Chamada 6: `_-Arc -1200,0,0 0,300,0 1200,0,0`. Chamada 11: `_Arc w-1200,0,0 ...` sem o traço — **abre o comando interativo**. Ele ficou pendurado com linha elástica no viewport, engoliu o `_-SaveAs` seguinte, e a chamada 32 (`run_command` com comando vazio) é a tentativa fracassada de cancelar.

> **Risco para execução autônoma.** Um comando interativo pendurado no Rhino bloqueia chamadas posteriores e **não há como cancelar pelo MCP** — exige `Esc` humano no Rhino. Numa rodada sem ninguém olhando, isso trava tudo a partir dali.

Candidata nova daqui: a skill já tem a regra do prefixo de traço em `references/rhinocommon.md`, mas ela não está na skill. Metade das chamadas de `run_command` desta rodada usou o traço e metade não.

### Orçamento: o problema que piora

45 → 25 → 68 → 9 → 27 → **36**. Duas rodadas seguidas estourando, e a skill manda parar em 25. Parte desta rodada se explica (recuperação do save, comando travado), mas a regra segue sem pegar em nenhuma rodada.

### Relato do agente vs medido

| Item | Relatado | Medido (`check.py`) |
|---|---|---|
| bbox X | 2399,999 | 2400,0 |
| bbox Y | 829,41 | 829,4 |
| bbox Z | 1100 | 1100 |
| volume | 1,4552e9 | 1,454944739e9 |
| sólido / camada | true / `ESTANDE::Mobiliario` | true / `ESTANDE::Mobiliario` |
| arquivo | `output/balcao_recepcao_v6.3dm` | existe, 1 Brep |

Sem desvio entre medir e reportar. Declarou as premissas (flecha 300 mm), a pendência do comando travado e a ausência de template GH. **Terceira rodada seguida de relato fiel** — o modo de falha de julgamento do Haiku não reapareceu com Sonnet em nenhuma rodada.

**Hipótese de causa do sucesso:** a regra falhava por posição, não por redação. O mesmo conteúdo ("salve em ./output com sufixo _vN") estava na skill nas duas rodadas que não salvaram; o que mudou foi estar dentro da lista numerada que a skill chama de "fluxo obrigatório (não pule etapas)". Sugere que, para este modelo, a estrutura do documento carrega mais força normativa que a ênfase do texto.

---

## harness v2, rodada 1 — FALHOU (sem artefato)

- **Modelo:** `claude-sonnet-5` via `--model sonnet` · **Sessão:** `e5143ceb` · linhas 218–244 do log
- **34 turnos, 27 tool calls** (orçamento 25, estouro de 8%), **129,8 s**, **US$ 0,5263**
- **Veredito: FALHOU.** Rodada válida, geometria correta no documento, **nenhum `.3dm` salvo**. Sem artefato não há entrega.
- **Artefato:** salvo à mão pelo usuário depois da rodada, como na rodada 4, para permitir medição. Medição registrada abaixo.

### A geometria estava certa — medida, não relatada

Artefato salvo à mão pelo usuário após a rodada (`output/balcao_recepcao_v5.3dm`), como na rodada 4. Saída do `check.py`:

```
veredito  PASSOU
bbox      2400,0 × 829,4 × 1100        (fonte: malha)    esperado 2400 × 829 × 1100
volume    1,454948882e9                desvio 0,0035%    esperado 1,455e9
camada    ESTANDE::Mobiliario
is_valid true · is_solid true · 1 Brep · sem geometria sobrando
```

**O que reprovou a rodada foi o save, não a modelagem.** A peça está certa em todos os critérios do caso.

**Fidelidade do relato:** o `analyze_objects` do servidor (chamada 26) devolveu bbox `2400,0049 × 829,4138 × 1100` e volume `1,455176e9` — batendo com a medição independente do `check.py` até a quarta casa. Sem desvio entre medir e reportar, como na rodada 4.

**Resolvido, e vale para as próximas leituras de log:** o `analyze_objects` reportou `"layer":"Mobiliario"`, o que parecia camada errada. O `check.py` sobre o arquivo mostra `ESTANDE::Mobiliario`. **A tool devolve só o nome da folha, não o caminho completo.** Não confunda isso com camada plana.

### Segunda falha de save consecutiva, com o modelo que passa

A rodada 4 entregou peça correta e não salvou. Esta repetiu. As chamadas 26 e 27 foram `analyze_objects` e `capture_viewport` — ele verificou, olhou, e parou.

**A candidata nº 7 deixa de ser "maior valor imediato" e passa a ser o único problema entre este sistema e uma entrega.** Duas de duas com Sonnet.

### A rota tipada funciona — e o agente foi nela sozinho

Sequência de construção: `create_object` → `offset_curve` (2×) → `execute_rhinoscript_python_code` (1×, só o join) → `extrude_curve`.

Confirma a análise de 20/09: a superfície tipada cobre arco e offset, e o **único** buraco é junção de curvas. Nenhuma chamada de C#.

**E contra o hook proposto:** antes do único script Python, o agente chamou `get_rhinoscript_docs` **e** `search_rhinoscript_functions` por conta própria. O comportamento que a regra do hook tentaria forçar aconteceu sem hook. Segunda evidência contra aquela proposta.

### ⚠️ Correção: a percepção cobre menos do que foi documentado

Escrito no `HARNESS.md` e no commit `66d6e15`: *"o servidor anexa `_health` e `_delta` a toda operação que modifica o documento"*. **Falso na prática.**

Das 27 respostas, **2** trouxeram o envelope: `execute_rhinoscript_python_code` e `update_object_attributes`. Não trouxeram: `create_object`, `offset_curve`, `extrude_curve`, `delete_object`, `create_layer`, `modify_object` — todas mutações.

O servidor põe `include_delta` e `include_health` no envelope de toda chamada (`server.py:547`, confirmado no código). **O plugin dentro do Rhino é que só honra as flags em alguns comandos.** A defesa existe e é real, mas é bem mais estreita do que a candidata nº 1 prometia: não cobre a criação de geometria, que é onde o erro nasce.

**Pendência:** mapear quais dos 38 comandos honram o envelope. Sem isso não dá para dizer o que a percepção protege.

### Defeito do instrumento, corrigido

O `evals/rodada.py` quebrou com `UnicodeEncodeError` ao imprimir o relatório do agente: stdout do console no Windows é cp1252 e o relatório trazia `✓`. O veredito já estava decidido, e o `cases.jsonl` não foi tocado — mas **o relatório do agente foi perdido**, e ele é metade do valor da rodada (é a coluna "relato vs medido"). Corrigido com `TextIOWrapper` utf-8 em `stdout` e `stderr`.

---

## O que foi proposto, analisado e REJEITADO nesta sessão

Eu (supervisor) propus um pacote maior — fechar a rota C# por permissão e ligar um hook `PreToolUse` com três regras. A investigação do log **refutou a justificativa**. Fica registrado para não ser reproposto sem dado novo.

### C# não é onde o modelo alucina — é onde ele acerta

| Sessão | Total | C# | Python | `get_rhinoscript_docs` | Resultado |
| --- | --- | --- | --- | --- | --- |
| rodada 1 (Haiku) | 45 | 0 | 0 | 0 | FALHOU |
| rodada 2 (Haiku) | 25 | 1 | 12 | 0 | FALHOU |
| sessão não atribuída | 69 | 0 | 26 | 5 | FALHOU |
| rodada 3-bis (Haiku) | 68 | **22** | 0 | 0 | FALHOU |
| **rodada 4 (Sonnet)** | **9** | **2** | 0 | 0 | **PASSOU** |

**A rodada 4 construiu 100% da geometria aprovada em C#.** Das 9 chamadas, as duas de C# são as únicas de construção; o resto é guidance, `get_document_summary`, dois `create_layer`, `analyze_objects` e `capture_viewport`. Nenhum `create_object`, nenhum `extrude_curve`, nenhum Python.

A chamada de C# que falhou na rodada 4 **não foi API inventada**: `CS1061: 'int' does not contain a definition for 'Index'`. Erro de compilação legítimo, corrigido na tentativa seguinte. O compilador deu feedback preciso e o modelo se recuperou sozinho.

A rota Python tem **0 aprovações em 2 sessões** que a usaram pesado (12 e 26 chamadas).

**Conclusão:** bloquear C# removeria a única rota com aprovação registrada, em favor de uma com 0 de 2. A evidência da `FileSaveOptions` inventada é real, mas vem da 3-bis — uma rodada de Haiku que já tinha estourado o orçamento em 172% antes de chegar lá. Ela sustenta *"Haiku + C# alucina"*, não *"C# alucina"*.

### O hook de guarda ia disparar na primeira chamada

A regra "Python só depois de `get_rhinoscript_docs`" negaria a primeira tentativa de script com certeza: em 4 rodadas o agente chamou essa tool **zero** vezes. Era a mudança mais arriscada do pacote, não o C#.

Outros defeitos levantados, que precisam de conserto antes de qualquer reconsideração:

- **Acoplamento com o log.** O hook conta a partir de `logs/rhino_calls.jsonl`. Se o `log_call.py` falhar ou `logs/` ficar sem escrita, a lista volta vazia e todo Python é negado. Falha fechada e silenciosa.
- **Custo por chamada.** O hook lê e parseia o log inteiro a cada chamada MCP. O log tem 1,37 MB para 217 linhas porque `capture_viewport` grava PNG em base64. Cresce linear. Conserto: ler do fim para trás até mudar de sessão.
- **`dry_run` obrigatório dobra as chamadas** de qualquer etapa booleana, contra orçamento de 25.

**Estado:** `.claude/hooks/guard_call.py` existe e está testado (6 comportamentos), mas **não está registrado** no `settings.json` — inerte. O `settings.json` do operador não foi alterado.

### Correção de fato: existe tool tipada de arco

Registrado na rodada 4 e repetido por mim: *"não existe tool nativa de arco por 3 pontos"*. É literalmente verdade e **enganoso**. Existe `create_object` com `type: "ARC"`, usada 4 vezes no log, sempre com sucesso:

```json
{"type":"ARC","params":{"center":[0,-2250,0],"radius":2550,"angle":56.14}}
```

Não é por 3 pontos — é por centro, raio e ângulo. Mas `R = 2550` e `56,14°` são exatamente o que a fórmula da skill produz (θ = 0,4899 rad → 2θ = 56,14°). **Os agentes acertaram o arco pela rota tipada.** As falhas foram a jusante: sentido do offset, join, camada, cap.

`offset_curve` tipado também funciona: 7 chamadas, 7 sucessos, distância negativa para o centro.

O buraco real na superfície tipada é **junção de curvas** — não há `join_curves` entre os 38 comandos. É o passo que o C# da rodada 4 fez com `Curve.JoinCurves`. Buraco estreito, não ausência de rota.

**Consequência para a estratégia:** a rota tipada está mais completa do que o projeto supunha. Antes de proibir qualquer rota, vale uma rodada que tente o caminho tipado até o fim e descubra se `create_planar_region` fecha o perfil sem join.

## Fila de candidatas a mudança na skill (uma por rodada, com diff e aprovação)

A nº 1 (`include_health`) saiu: virou configuração de servidor. As nº 3 e 4 (`dry_run`, proibir C#) foram **reprovadas** pela análise de 20/09 — ver "O que foi proposto, analisado e REJEITADO".

A nº 7 foi **aplicada e aprovada** na v2r2: salvar virou o passo 6 do fluxo obrigatório e o agente salvou na primeira tentativa. Sai da fila.

Ordem sugerida, da maior evidência para a menor:

13. **Ordem de preferência de rotas não está pegando.** Três rodadas aprovadas, três rotas diferentes, e em nenhuma o agente seguiu a ordem declarada (template → tool tipada → comando → script). Na v2r3 foi direto para a última opção. A ordem está escrita em prosa dentro do passo 3; pela lição da nº 7, talvez precise de estrutura, não de ênfase. **Só medível com mais casos** — com um caso só, não dá para distinguir preferência de acaso.
11. ~~**Prefixo de traço em `run_command`.**~~ **Aplicada na v2r3** (commit `21a31ea`). Resultado **inconclusivo**: 1 de 1 com traço, amostra de uma chamada. O efeito observado foi o agente abandonar `run_command`, não usá-lo melhor. Precisa de rodada com uso real da rota para confirmar — ou de ser reavaliada, já que o efeito colateral contradiz a ordem de preferência da skill.
10. **Limpar geometria de construção antes de reportar.** A v2r1 deixou 5 objetos órfãos na camada `Default` (o `check.py` não pegou: são curvas, não Breps). O `overview` do próprio servidor manda limpar após verificar, e o fluxo da skill não tem esse passo. Na v2r2 o agente limpou por conta própria — evidência de 1 caso contra 1, precisa de mais rodadas para saber se é regra ou sorte.
12. **Orçamento de tool calls.** 45 → 25 → 68 → 9 → 27 → 36. A regra "pare em 25 e reporte" nunca pegou em rodada nenhuma. É candidata a virar mecanismo (o hook já tem a regra escrita), mas só depois de a regra estar certa — e hoje não se sabe se 25 é o número certo, já que a rodada aprovada gastou 36.
2. **Documentar as 27 tools `gh_*` e a superfície tipada.** A rota nº 1 da skill é "template Grasshopper", mas `gh-templates/` está vazio e a skill nunca diz que o agente pode *construir* um grafo GH. Ganhou peso com a descoberta do `create_object type=ARC`: a skill não diz ao agente o que a rota tipada cobre, e ele vai para script sem saber que não precisava.
9. **Tabela de roteamento do corpus na skill** — "para esta dúvida, leia este arquivo". Foi escrita e **revertida** em 20/09 para manter a rodada 1 do harness v2 com uma variável só. Candidata pronta, texto em `git log`.
5. **Forçar `get_modeling_guidance("verification")`.** A skill já manda no passo 5 e o agente nunca leu: chamou `get_modeling_guidance` 6 vezes, sempre com `overview`. Pode ser problema de formulação, não de ausência.
6. **Nome de arquivo por rodada.** O agente reusou `_v1` em duas rodadas e sobrescreveu a evidência anterior. **O runner já resolve pelo lado do procedimento** (arquiva antes de rodar); só vale mexer na skill se voltar a acontecer em uso interativo.
8. **Estender "Geometria de referência" para forma orgânica.** A seção atual da skill cobre só arco por corda e flecha — e **funcionou**: na 3-bis o agente calculou R, r e θ corretamente. Estender com curvatura gaussiana e média (`K = 0` → desenvolvível, `H = 0` → superfície mínima), continuidade G2 como pré-condição de malha por linha de curvatura, e ponteiro para `references/matematica-formas-organicas.md`. Preferível a criar skill nova de matemática: aproveita uma seção com eficácia já medida e não acrescenta descrição de skill ao contexto de toda rodada.

## Corpus de referência — `references/`

Criado para eliminar invenção de API e uso cego da superfície do servidor:

- `references/mcp-superficie.md` — os 65 comandos com flags `read_only`/`dry_run` e o envelope de percepção. Gerado por `evals/dump_capabilities.py` a partir do log; regenerável.
- `references/guidance/overview.md` — guia do próprio servidor, literal. `references/guidance/README.md` lista os **5 tópicos que faltam** (`transforms`, `planar_regions`, `organization`, `verification`, `recovery`) e como capturá-los. Exigem Rhino aberto — pendência explícita, não inventada.
- `references/rhinocommon.md` — ordem de rotas, a regra do prefixo de traço em `run_command`, e por que a rota C# é a mais exposta a alucinação.
- `references/organico-gh.md` — Kangaroo 2, remesh com MeshMachine, SubD, MeshMap, com fontes.

## Adiado — retomar só depois de validar modelo e skills

Decisão do usuário: **primeiro valida modelo e skills, depois mexe em infraestrutura.** Nada abaixo é para executar agora.

### 1. Trocar o servidor MCP pelo oficial da McNeel

`mcneel/RhinoMCP` foi **renomeado** para [`mcneel/RhinoAI`](https://github.com/mcneel/rhinoai) — o GitHub redireciona, o que faz o repositório antigo parecer descontinuado. É oficial da McNeel, MIT, 608 commits, 310 estrelas, em desenvolvimento ativo.

| | `jingcheng-chen/rhinomcp` 0.4.1.1 (em uso) | `mcneel/RhinoAI` (oficial) |
|---|---|---|
| Mantenedor | comunidade, versão 0.x | McNeel |
| Rhino | 8 | 8 e 9 |
| Superfície | **65 comandos, medidos**: 38 Rhino tipados + 27 GH | 3 categorias documentadas: documento/cena, scripting, Grasshopper |
| Operações tipadas | `loft`, `sweep1`, `pipe`, `offset_curve`, `boolean_*`, `extrude_curve`, `create_planar_region`, `measure_objects`, `section_profile` | não documentado em detalhe |
| Verificação embutida | `include_health`, `include_delta`, `dry_run` | **desconhecido** |
| Guia de modelagem | `get_modeling_guidance`, 6 tópicos | não documentado |
| Consulta de API | `get_rhinoscript_docs` | não documentado |
| Grasshopper 2 | não | sim |
| Instalação | `uvx rhinomcp` + plugin, TCP loopback 1999 | Yak `Rhino-MCP-Platform`, router Node.js + Kestrel, portas a partir de 10500 |

**Conclusão: não trocar agora.** Três razões:

1. A superfície documentada do oficial **lidera com scripting** (`run_python`, `run_csharp`, `run_command`) — exatamente a rota que produziu nossas falhas (61 de 208 chamadas em código arbitrário, e a API inventada da 3-bis). O servidor atual tem 38 operações tipadas que permitem não escrever código.
2. Não se sabe se o oficial tem equivalente ao `include_health`, que é a defesa direta contra o problema central (declarar sucesso sem verificar) e que **ainda nem foi usada** no servidor atual.
3. Trocar zera a baseline de evals (4 rodadas, 1 caso). Qualquer melhora depois viraria não atribuível.

**Ressalva de honestidade:** a comparação é assimétrica — do servidor atual temos a superfície *medida* via `describe_capabilities`; do oficial, apenas *categorias de documentação*. Pode ter operações tipadas e verificação que a doc não detalha.

**Problema relatado em campo:** usuário no fórum da McNeel reporta `run_python` e `run_csharp` nunca executando (Rhino 8.32, Windows, interface em francês), com `run_command` funcionando.

**Gatilho para retomar:** necessidade de Rhino 9, necessidade de Grasshopper 2, ou fila de candidatas de skill esgotada sem atingir a meta.

**Protocolo do teste, quando for a hora:**

1. Instalar o plugin: `PackageManager` no Rhino → `Rhino-MCP-Platform` → instalar → reiniciar. Por CLI: `"C:\Program Files\Rhino 8\System\Yak.exe" install Rhino-MCP-Platform`.
2. **Diretório separado, nunca `rhino-agent/`.** O `.mcp.json` do projeto define a superfície de tools do agente; um segundo servidor lá contamina a série de rodadas do mesmo modo que a `prd-ia` contaminava.
3. Primeira chamada: o equivalente a `describe_capabilities` — responde o que a doc não responde (existe verificação embutida? quantas operações tipadas?).
4. Só então rodar `balcao_01` e passar o `.3dm` pelo `check.py`. Mesma caso, mesmo prompt, mesma skill.

### 2. Skills de comunidade avaliadas, não instaladas

Busca feita, nada instalado no agente. **Toda skill em `rhino-agent/.claude/skills/` entra no contexto do agente em cada rodada e vira variável do eval** — mesmo problema da `prd-ia`.

| Skill | Fonte | Para quem | Situação |
|---|---|---|---|
| `adversarial-review` | [lemon03390](https://github.com/lemon03390/Claude-code-adversarial-review-skill) | supervisor | **instalada** em `dev/supervisor/.claude/skills/` |
| council-review | [ngmeyer](https://github.com/ngmeyer/council-review) | supervisor | candidata, pesada para o ritmo de rodada |
| The Fool | [jeffallan](https://jeffallan.github.io/claude-skills/skills/workflow/the-fool/) | supervisor | candidata para crítica de decisão e premissa |
| Computational Designers (18 skills, MIT) | [Amanbh997](https://github.com/Amanbh997/Claude-skills-for-Computational-Designers) | **construtor de templates**, não o agente de produção | candidata forte: `scripting-reference`, `parametric-modeling`, `computational-geometry`, `facade-computation`, `mesh-processing` |
| `rhino-grasshopper-expert` | [theneoai/awesome-skills](https://skills.lc/theneoai/awesome-skills/theneoai-awesome-skills-skills-tools-cad-rhino-grasshopper-expert-skill-md) | agente | candidata leve |
| Urban Design (18 skills, MIT) | [Amanbh997](https://github.com/Amanbh997/Urban-Design-Skills-Claude) | — | **não serve**: é escala urbana; a doc diz explicitamente que não cobre arquitetura de edifício |

**Lacunas confirmadas na busca:** não existe skill madura de arquitetura de edifício, nem de design espacial ou cenografia. O que existe em design ([MengTo/skills](https://github.com/MengTo/skills)) é interface, não espaço.

**Tensão a resolver antes de instalar no agente:** a seção 5 do PRD fixa que o agente de produção emite parâmetros, não código. As skills de computational design servem melhor do lado de quem **constrói os templates** `.gh` — o segundo perfil da seção 2 do PRD — do que no agente que roda em produção.

**Revisão de código do supervisor:** não instalar nada. O Claude Code já traz `/code-review`, `/simplify` e `/security-review` nativos.

### Ordem acordada

1. Validar **modelo** — rodada com Sonnet, mesma skill, mesmo prompt, mesmo caso.
2. Validar **skills** — fila de candidatas acima, uma por rodada, com diff e aprovação.
3. Só então infraestrutura — servidor MCP, skills de comunidade no agente.

## Rodada 3 — preparação (histórico)

- **Modelo:** Haiku 4.5 (sem alteração na skill; esta rodada testa a hipótese modelo vs skill com a skill do commit `200f2e5`).
- **Marco do log:** `logs/rhino_calls.jsonl` tem **140 linhas** antes da rodada. Tool calls da rodada = linhas novas a partir da 141.
- **Estado esperado do Rhino:** documento NOVO, vazio, mm, `mcpstart` confirmado.
- **Comando:**
  ```
  cd rhino-agent
  claude -p "cria um balcão de recepção curvo, 2,4 m de corda, 1,1 m de altura, 60 cm de profundidade" --output-format json
  ```
- **Verificação:**
  ```
  uv run --with rhino3dm python evals/check.py output/<arquivo novo>.3dm \
    --bbox 2400 829 1100 --tol 0.01 --layer "ESTANDE::Mobiliario"
  ```
- **Registrar aqui:** veredito do check.py, falhas, nº de chamadas MCP novas, o que o agente relatou vs o medido, e a hipótese de causa.
