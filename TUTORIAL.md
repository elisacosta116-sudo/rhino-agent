# TUTORIAL — operar os agentes do Rhino, do zero

Este documento ensina a operar o sistema do começo: quais programas abrir, em que ordem, o que digitar, o que esperar de volta e o que fazer quando não vem o esperado. É escrito para ser seguido depois de semanas sem tocar no projeto.

Os outros documentos, e quando ir a cada um:

| Documento | Responde |
|---|---|
| **`ESTADO.md`** | onde paramos e qual é a próxima ação — **leia primeiro, sempre** |
| `TUTORIAL.md` (este) | como operar, do zero |
| `OPERACAO.md` | manual de bancada: comandos do dia-a-dia, armadilhas |
| `NOTAS.md` | o que já aconteceu em cada rodada, e por quê |
| `HARNESS.md` | por que o harness é construído assim |
| `../supervisor/PROMPTS.md` | os textos prontos para colar no supervisor |
| `references/` | o que o agente consulta para não inventar API |

---

## 1. Quem é quem

Existem **dois** agentes, e confundi-los já custou uma rodada inteira.

```
C:\Users\eacosta\dev\
├── rhino-agent\        ← O OPERADOR. Modela. Fala com o Rhino.
└── supervisor\         ← O SUPERVISOR. Desenvolve e mede o operador. Nunca modela.
```

**O operador** (`rhino-agent/`) recebe um pedido em português e produz geometria NURBS no Rhino, através do servidor MCP `rhino`. Ele roda sob travas: uma skill que define o fluxo obrigatório, uma lista de permissões, hooks que registram e bloqueiam chamadas, e um orçamento de tool calls. Ele não sabe que está sendo avaliado.

**O supervisor** (`supervisor/`) é onde você trabalha. Ele lê os resultados, propõe mudanças na skill, roda as rodadas de avaliação e mantém o registro. Ele **não modela** e **não altera as travas do operador** — `dev/.claude/settings.json` nega a ele a edição do `settings.json` do agente, de propósito.

### Por que pastas irmãs e não aninhadas

O Claude Code carrega os arquivos `CLAUDE.md` do diretório atual **e de todos os diretórios pais**. Em 19/09 existiu um `CLAUDE.md` de supervisor em `dev/`. Na rodada seguinte, o operador — rodando com cwd em `dev/rhino-agent/` — herdou aquele arquivo, **assumiu o papel de supervisor** e passou a pedir que o usuário abrisse um documento novo no Rhino. Zero geometria, zero tool calls, US$ 0,058 queimados. A rodada foi anulada, não reprovada: não mediu o modelo, mediu um furo de isolamento.

Daí a regra, que vale mais que qualquer outra neste projeto:

> **Nunca crie um `CLAUDE.md` em `dev/` nem acima.** O único `CLAUDE.md` na árvore de pais do operador é o dele mesmo.

E o corolário: para trabalhar nos arquivos do operador a partir do supervisor, use `--add-dir`, **nunca `--bare`**. O `--bare` desliga a herança de `CLAUDE.md`, mas desliga os hooks junto — e sem hook não há log, sem log não há contagem de tool calls, e sem contagem não há rodada mensurável.

---

## 2. Abrir, em ordem

Quatro passos. A ordem importa: cada um depende do anterior estar de pé.

### 2.1 Rhino 8 — documento NOVO

Abra o Rhino 8 e crie um **documento novo**, em **milímetros**, vazio.

*Por quê:* o `check.py` escolhe o Brep alvo do arquivo por um ranking. Com geometria antiga no documento, ele pode medir a peça errada e devolver um veredito que não é sobre a rodada. A rodada 2 deixou 2 Breps no arquivo; uma sessão anterior deixou 4.

*Sintoma de quem pula:* veredito estranho, com `breps_no_arquivo` maior que 1 nos avisos do `check.py`.

### 2.2 `mcpstart` — a ponte

Na **linha de comando do Rhino** (dentro do Rhino, não no terminal), digite:

```
mcpstart
```

Espere a confirmação aparecer no Rhino. Isso liga o plugin que escuta em `127.0.0.1:1999` e é por onde o servidor MCP fala com o Rhino. Para desligar: `mcpstop`.

*Sintoma de quem pula:* o agente sobe, responde em texto, gasta dinheiro e **não toca em geometria nenhuma**. O runner detecta isso e marca a rodada como `ANULADA`.

### 2.3 Terminal A — o supervisor

```bash
cd C:\Users\eacosta\dev\supervisor
claude --add-dir ../rhino-agent
```

É a sua sessão de trabalho. O `--add-dir` dá ao supervisor acesso aos arquivos do operador sem mudar o diretório de trabalho — o que manteria o isolamento de qualquer jeito, mas deixa explícito de onde ele está operando.

Primeiro input, sempre o mesmo (está em `../supervisor/PROMPTS.md`):

```
Leia rhino-agent/ESTADO.md e rhino-agent/NOTAS.md. Confirme o estado do harness
contra os arquivos (não contra o que está escrito) e me diga a próxima ação.
Não rode nada antes de eu confirmar.
```

### 2.4 Terminal B — o operador

**Só abra quando for rodar o operador em modo interativo.** Para rodadas de avaliação você não precisa dele: o runner chama o operador sozinho, em modo headless.

```bash
cd C:\Users\eacosta\dev\rhino-agent
claude --model sonnet
```

*Por que `--model sonnet`:* o `settings.json` do operador ainda aponta `claude-haiku-4-5-20251001`, e **nenhuma rodada de Haiku passou** — três falhas em três. O Sonnet passou na primeira, com 9 chamadas contra 45/25/68 e um terço do custo. Até você trocar o pin no arquivo, o modelo vai na chamada.

---

## 3. Uma rodada inteira, narrada

Uma "rodada" é uma execução medida do operador contra um caso de eval. É assim que o projeto sabe se uma mudança melhorou ou piorou alguma coisa.

### 3.1 Antes: commite

```bash
cd C:\Users\eacosta\dev\rhino-agent
git status --short
```

Se houver mudança não commitada, **commite antes**. Uma rodada sobre árvore suja não é atribuível a diff nenhum — você saberá o resultado, mas não de qual mudança ele veio.

### 3.2 Rodar

Um comando faz os seis passos do protocolo:

```bash
uv run --with rhino3dm python evals/rodada.py balcao_01 --model sonnet
```

O que ele faz, em ordem, e por que cada passo existe:

| Passo | O que faz | Erro que evita |
|---|---|---|
| 1 | copia os `.3dm` atuais para `output/_rodadas/` | a rodada 2 sobrescreveu o arquivo da rodada 1, que sobrou só como `.3dmbak` |
| 2 | anota o número de linhas do log | tool calls da rodada = linhas novas |
| 3 | escreve `logs/_rodada_atual.json` com o orçamento | é o que liga a regra de orçamento no hook de guarda |
| 4 | roda `claude -p "<prompt do caso>" --output-format json` | prompt vem do caso, literal, sem adaptar |
| 5 | **valida se foi rodada** antes de ler qualquer resultado | a rodada 3 teve 0 tool calls e quase foi lida como falha do modelo |
| 6 | acha o `.3dm` novo, e para se não houver | a 3-bis declarou um `v3.3dm` que não existia; a rodada 4 nem salvou |
| 7 | mede com `check.py` | a fonte de verdade é o arquivo, não o relato |
| 8 | registra no `historico` do caso e imprime bloco para o `NOTAS.md` | registro escrito à mão é registro que se perde |

### 3.3 Casos de recusa (tier borda)

Alguns casos são feitos para o agente **não** entregar geometria: dimensão impossível, pedido ambíguo, topologia fora do catálogo. Eles trazem `espera_recusa: true` e uma lista `sinais_de_recusa` no `cases.jsonl`, e o runner julga por outro caminho — sem `.3dm`, sem `check.py`.

Nesses casos, **produzir arquivo é a falha**. E há uma diferença que o instrumento sozinho não resolve: recusar com critério não é a mesma coisa que desistir. Por isso "parou sem dizer por quê" vira `INCONCLUSIVO`, e `INCONCLUSIVO` **nunca conta como aprovação** — o runner imprime o relato e a decisão é sua.

### 3.4 As três saídas possíveis

**`ANULADA`** — o agente não tocou no Rhino. Não é falha do modelo. O runner imprime as três causas conhecidas em ordem de frequência: Rhino fechado ou `mcpstart` não confirmado; `CLAUDE.md` contaminando o papel do agente; o agente parou para perguntar algo. Corrija e rode de novo — não registre como falha.

**`FALHOU` sem arquivo** — rodada válida, mas nenhum `.3dm` novo. Sem artefato não há entrega, independente do que o agente relatou. Dois precedentes exatos.

**Veredito do `check.py`** — `PASSOU`, `FALHOU` ou `INCONCLUSIVO`. O `INCONCLUSIVO` aparece quando o arquivo não tem malha de render: aí a caixa medida é só um **limite superior**, e dá para reprovar por falta, nunca por excesso. `INCONCLUSIVO` não é aprovação.

### 3.5 Depois: registrar

O runner imprime um bloco markdown pronto. Cole no `NOTAS.md` e complete **as duas linhas que ele deixa em branco de propósito**:

- **Relato do agente vs medido** — o contraste entre o que o agente disse e o que o arquivo mede. É o produto mais valioso da série inteira: foi o que separou "erro de medição" de "erro de julgamento". O Haiku mede certo e conclui errado; isso muda o tipo de correção que faz sentido.
- **Hipótese de causa** — o que você acha que produziu o resultado.

Depois, atualize o `ESTADO.md`. **Fim de sessão sem `ESTADO.md` atualizado é progresso perdido.**

---

## 4. Manter os agentes

### 4.1 O que pode mudar e o que não pode

A distinção que importa: **o que entra no contexto ou no comportamento do operador é variável de eval.** Mudar duas ao mesmo tempo torna a rodada seguinte não atribuível.

| Peça | Vira variável de eval? |
|---|---|
| `.claude/skills/rhino-nurbs/SKILL.md` | **sim** — entra no contexto de toda rodada |
| qualquer skill nova em `rhino-agent/.claude/skills/` | **sim** — foi por isso que a `prd-ia` saiu de lá |
| `.claude/settings.json` (modelo, permissões, hooks) | **sim** |
| `.mcp.json` (superfície e configuração do servidor) | **sim** |
| `CLAUDE.md` do operador | **sim** |
| `references/**` | só se a skill apontar para o arquivo |
| `evals/check.py` | **não muda o agente, mas muda o veredito** — ao mexer, re-meça o histórico inteiro |
| `evals/rodada.py`, `NOTAS.md`, `ESTADO.md`, `TUTORIAL.md`, `OPERACAO.md` | não |

**Regra:** uma variável por rodada, com diff mostrado e aprovado antes de editar.

### 4.2 O `settings.json` que só você pode editar

O supervisor é impedido de editar `rhino-agent/.claude/settings.json` — é a trava que garante que quem avalia não afrouxa o que está sendo avaliado. Quando uma mudança ali for necessária, o supervisor entrega o diff e **você** aplica, lendo antes. Hoje não há nenhuma pendente.

### 4.3 As defesas, da mais forte para a mais fraca

```
configuração do servidor  >  regra de permissão  >  hook  >  texto de skill
        (inescapável)         (bloqueia a tool)   (condiciona)  (pede por favor)
```

O texto é o mais fraco dos quatro. Evidência: a skill manda ler `get_modeling_guidance("verification")` no passo 5 desde sempre; em **217 chamadas**, `get_modeling_guidance` foi chamado 6 vezes e o tópico `verification` **nunca**. A regra "tolerância é binária" está escrita e o Haiku marcou OK com desvio de 585% duas vezes.

**E é aqui que mora a armadilha.** A hierarquia convida a mecanizar tudo que der, e mecanizar a regra errada a torna mais difícil de derrubar depois, não menos. Em 20/09 foram propostas duas mecanizações — fechar a rota C# por permissão, e um hook exigindo consulta de docs antes de Python. O log reprovou as duas: a única rodada aprovada construiu tudo em C#, e o agente nunca chamou `get_rhinoscript_docs` em rodada nenhuma. A análise está em `NOTAS.md`.

**A ordem certa é: regra certa primeiro, mecanismo depois.**

Defesas ativas hoje:

| Defesa | Onde | Depende do modelo? |
|---|---|---|
| `_health` e `_delta` em toda mutação | `.mcp.json`, `RHINO_MCP_PERCEPTION=1` | **não** |
| salvar antes de reportar | skill | sim |
| ordem de preferência de rotas | skill | sim |
| tolerância é binária | skill | sim |
| orçamento de 25 tool calls | skill | sim |

Escrito e **inerte**, por decisão: `guard_call.py` (3 regras, testado, não registrado). Disponível e **não ligado**: `RHINO_MCP_VALIDATE=strict`.

### 4.4 Manutenção de rotina

**Quando o servidor MCP for atualizado**, a superfície de tools pode mudar. Regenere a referência:

```bash
uv run --no-project python evals/dump_capabilities.py
```

Ele lê a última resposta de `describe_capabilities` no log e reescreve `references/mcp-superficie.md`. Basta que uma rodada qualquer tenha chamado `describe_capabilities`.

**Quando o `output/` encher** — os `.3dm` de rodadas antigas ficam em `output/_rodadas/`, e `output/` está no `.gitignore`. Nada ali é recuperável pelo git: arquivar é a única via.

---

## 5. Melhorar a efetividade

### 5.1 A ordem acordada

1. ~~**Modelo**~~ — resolvido. Sonnet passa, Haiku não. Mesma skill, mesmo prompt, mesmo caso.
2. **Skills** — em andamento. Fila de candidatas no fim do `NOTAS.md`, uma por rodada, com diff e aprovação.
3. **Infraestrutura** — só depois. Inclui trocar o servidor MCP pelo oficial da McNeel (conclusão atual: **não trocar agora**, razões no `NOTAS.md`) e instalar skills de comunidade no operador.

### 5.2 A fila de candidatas, encolhida

Ela tinha 8 itens. Três viraram mecanismo e saíram do texto: a nº 1 (`include_health`) virou variável de ambiente, a nº 3 (`dry_run`) e a nº 4 (proibir C#) viraram hook e permissão. **Uma regra que vira mecanismo sai da fila** — é o padrão a perseguir com as demais.

Sobram as que dependem de julgamento e não dá para mecanizar:

| # | Candidata | Por que ainda é texto |
|---|---|---|
| 7 | obrigar o save antes de reportar | maior valor imediato: o Sonnet entregou peça correta e não salvou, "porque você não pediu" |
| 2 | documentar as 27 tools `gh_*` | a rota nº 1 da skill é "template Grasshopper" e `gh-templates/` está vazio |
| 5 | forçar `get_modeling_guidance("verification")` | pode ser problema de formulação, não de ausência |
| 6 | nome de arquivo por rodada | o runner já resolve pelo lado do procedimento |
| 8 | estender "Geometria de referência" para forma orgânica | a seção atual tem eficácia medida: produziu R, r e θ corretos no Haiku e no Sonnet |

### 5.3 Como se decide se uma mudança ajudou

Não por opinião, e não por uma rodada. Uma aprovação não é taxa de aprovação — `balcao_01` é 1 caso de 30. O que torna qualquer conclusão possível é o dataset de evals, e ele é o gargalo real do projeto hoje.

O sinal de que o corpus de referência está funcionando é mensurável no log: quais tools o agente chama. Hoje, **63 das 217 chamadas (29%) foram execução de código arbitrário** — 38 em Python e 25 em C#, a última opção da ordem de preferência da própria skill — mais 29 de `run_command`. Se as defesas e o corpus funcionarem, essa fração cai e as tools tipadas sobem.

---

## 6. Quando algo dá errado

| Sintoma | Causa provável | O que fazer |
|---|---|---|
| Agente responde em texto, log não cresce | Rhino fechado, ou `mcpstart` não confirmado | §2.1 e §2.2; rodada é **anulada**, não falha |
| Agente se apresenta como supervisor | `CLAUDE.md` em diretório pai | procure `CLAUDE.md` em `dev/` e acima; sonda em `OPERACAO.md` §1.5 |
| `num_turns` = 1 e 0 tool calls | contaminação de contexto, ou o agente parou para perguntar | leia a resposta dele; rodada anulada |
| `check.py` diz `INCONCLUSIVO` | arquivo sem malha de render | salve do Rhino **sem** "Save Small"; passe em vista sombreada antes de salvar |
| `breps_no_arquivo` > 1 nos avisos | geometria de construção sobrando, ou documento não estava vazio | §2.1; o alvo medido pode ser o objeto errado |
| Veredito surpreendente | **desconfie do instrumento antes do modelo** | o `check.py` já reprovou geometria correta por um bug de bbox e distorceu três rodadas |
| Agente estoura o orçamento | orçamento é texto de skill para o modelo, e regra de hook no runner | fora do runner a regra fica desligada; use o runner para rodadas |
| Peça correta e nenhum arquivo | o agente não salva se não for mandado | peça o save no prompt, com caminho; candidata nº 7 |
| Dois vereditos diferentes para o mesmo arquivo | versões diferentes do `check.py` | ao mudar o instrumento, re-meça o histórico e registre a retratação |
