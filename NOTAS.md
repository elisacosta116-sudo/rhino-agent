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

Ordem sugerida, da maior evidência para a menor:

7. **Obrigar o save antes de reportar.** O Sonnet entregou peça correta e **não salvou** — "porque você não pediu". Numa execução autônoma isso perde o trabalho. A skill já manda salvar; o texto não está pegando. Candidata de maior valor imediato, porque afeta o modelo que hoje passa. **Próxima da fila.**
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
