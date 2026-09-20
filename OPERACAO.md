# OPERAÇÃO — como iniciar e como tocar o agente no dia-a-dia

Manual de bancada, para quem já sabe operar. **Se você está voltando ao projeto, comece por `ESTADO.md`; se está aprendendo, comece por `TUTORIAL.md`.** `HARNESS.md` explica *por que* o harness é assim; `NOTAS.md` registra *o que aconteceu* em cada rodada. Aqui está *o que você faz*, na ordem.

Dois modos de uso, mesma partida:

- **Modo produção** — você quer uma peça. Sessão interativa, você no loop.
- **Modo rodada** — você quer medir o agente. `claude -p`, protocolo fechado, veredito do `check.py`.

Nunca misture os dois na mesma sessão do Rhino: uma sessão de produção suja o log e deixa a próxima rodada não atribuível.

---

## 1. Partida (vale para os dois modos)

**1.1 Rhino.** Abra o Rhino 8 e crie um **documento NOVO**, em **milímetros**. Documento com geometria antiga é a causa mais barata de veredito errado — o `check.py` escolhe o Brep de maior bbox e pode medir a peça errada.

**1.2 Ponte MCP.** Na linha de comando do Rhino, rode:

```
mcpstart
```

Espere a confirmação no Rhino. Sem isso, o agente sobe, não acha o servidor e gasta dinheiro sem tocar em geometria.

**1.3 Terminal.** O agente roda com cwd em `rhino-agent/`:

```bash
cd C:\Users\eacosta\dev\rhino-agent
```

Isso não é detalhe: o `.mcp.json`, o `CLAUDE.md`, as permissões e o hook de log são todos resolvidos a partir daí.

**1.4 Modelo.** O `settings.json` do agente ainda aponta `claude-haiku-4-5-20251001`, e **nenhuma rodada de Haiku passou**. Até você decidir trocar isso no arquivo (o supervisor está bloqueado de editá-lo), passe o modelo na chamada:

```bash
claude --model sonnet
```

Referência de custo da rodada 4: 9 tool calls, 41,5 s, US$ 0,25 por peça aprovada — contra US$ 0,88 de uma rodada de Haiku que não entregou peça.

**1.5 Sanidade em 20 segundos** (só quando algo cheira errado):

```bash
claude -p "qual e o seu papel neste projeto?" --model sonnet
```

Resposta certa começa com *"Sou o agente NURBS deste projeto..."*. Se ele se apresentar como supervisor, **pare**: há um `CLAUDE.md` contaminando a árvore (ver §5).

---

## 2. Modo produção — pedir uma peça

```bash
cd C:\Users\eacosta\dev\rhino-agent
claude --model sonnet
```

### Como escrever o pedido

O agente segue a skill `rhino-nurbs` (interpretar → inspecionar → construir → verificar → reportar). Ele trabalha melhor com um pedido que já traga o que a skill vai cobrar de você:

- **Dimensões com unidade e eixo.** "2,4 m de corda, 1,1 m de altura, 60 cm de profundidade".
- **Tipo de geometria.** "sólido fechado" é diferente de "superfície". A skill trata sólido não fechado como tarefa não concluída.
- **Camada de destino.** Se você não disser, ele inventa — e nenhuma rodada de Haiku acertou a camada sozinha.
- **Salvar, explicitamente.** Escreva no pedido: *"salve como `./output/<nome>_v1.3dm`"*. Na rodada 4 o Sonnet entregou a peça correta e **não salvou** — "porque você não pediu". É a candidata nº 7 da fila de skill; até ela entrar, o pedido carrega essa responsabilidade.

Modelo de pedido que funciona:

```
cria um balcão de recepção curvo, sólido fechado, 2,4 m de corda,
1,1 m de altura, 60 cm de profundidade, na camada ESTANDE::Mobiliario.
Salve como ./output/balcao_recepcao_v5.3dm
```

### Como ler o que ele responde

**O relatório do agente é alegação, não evidência.** O padrão de falha documentado não é inventar número — é medir certo e **julgar errado**. Rodada 2: reportou 5100 mm (número correto) num pedido de 2400 e marcou "OK".

Confira sempre três coisas, nesta ordem:

1. **O arquivo existe no disco?** Na rodada 3-bis o agente declarou ter gerado `v3.3dm`; não havia arquivo nenhum.
2. **As dimensões medidas batem com o pedido?** Ele deve reportar medidas, não o que você pediu. Compare os números.
3. **É sólido fechado, na camada certa?** `IsSolid` true, 0 arestas nuas.

Se a peça importa, meça com o instrumento (§4) em vez de acreditar.

Agora há uma ajuda que não depende de você olhar: com `RHINO_MCP_PERCEPTION=1` ligado no `.mcp.json`, **toda operação que modifica o documento volta com `_health`** (objetos que falham validade, com motivo) **e `_delta`** (ids criados e removidos). Se o agente declarar sucesso e o `_health` do mesmo retorno acusar problema, a contradição está no log, não na sua memória.

### Sinais de que a rodada está descarrilando

- Passou de **25 tool calls** sem parar para reportar. Hoje isso é só texto de skill — e texto de skill é a defesa mais fraca: as rodadas gastaram 45, 25 e 68.
- Foi direto para script sem tentar a rota tipada. Existe `create_object` com `type: "ARC"` e `offset_curve` tipado, ambos com sucesso registrado no log. O que **não** existe tipado é junção de curvas.
- Usou curva interpolada no lugar de arco de 3 pontos. A skill proíbe; o Haiku reincidiu duas vezes.
- `_delta` mostrando objetos criados que ninguém pediu: geometria de construção acumulando. Apareceu em três sessões, com 2 e 4 Breps sobrando no arquivo.

### Higiene do save

- Nome novo a cada peça. O agente reusa `_v1` e **sobrescreve a peça anterior** — foi assim que a rodada 1 sobrou só como `.3dmbak`.
- Salve pelo Rhino, nunca por Bash (`cp`/`mv` estão negados de propósito).
- **Não use "Save Small".** Sem malha de render no arquivo, o `check.py` não consegue medir bbox nem volume e devolve `INCONCLUSIVO`. Dê uma passada em vista sombreada antes de salvar para garantir malha.

---

## 3. Modo rodada — medir o agente

**O runner faz os seis passos do protocolo.** Escrevê-los à mão foi o que produziu três erros de procedimento: arquivo sobrescrito, rodada anulada lida como falha, artefato declarado e inexistente.

**Passo 0 — congele o estado.** Commite antes de começar. Rodada sobre árvore suja não é atribuível a diff nenhum.

**Passo 1 — Rhino limpo.** §1.1 e §1.2. Espere a confirmação do `mcpstart`.

**Passo 2 — rode.**

```bash
uv run --with rhino3dm python evals/rodada.py balcao_01 --model sonnet
```

Ele arquiva os `.3dm` atuais, anota o marco do log, escreve o orçamento para o hook de guarda, chama o agente com o prompt literal do caso, **valida se foi rodada** antes de ler qualquer resultado, acha o arquivo novo, mede com o `check.py`, registra no histórico do caso e imprime o bloco do `NOTAS.md`.

Opções: `--rodada <rótulo>` para nomear (default: próximo número), `--dry-run` para rodar e medir sem escrever no `cases.jsonl`, `--timeout <s>` (default 1800).

**Passo 3 — leia o veredito.** `PASSOU` / `FALHOU` / `INCONCLUSIVO`, mais os dois casos que o runner detecta antes de medir:

| Saída | Significa |
|---|---|
| `ANULADA` | 0 tool calls ou 1 turno — o agente não tocou no Rhino. **Não é falha do modelo.** |
| `FALHOU`, sem arquivo | rodada válida, nenhum `.3dm` novo. Sem artefato não há entrega. |
| `INCONCLUSIVO` | arquivo sem malha de render: a caixa medida é limite superior. **Não é aprovação.** |

**Passo 4 — registre.** Cole o bloco impresso no `NOTAS.md` e complete as duas linhas que ele deixa em branco: **relato do agente vs medido**, e hipótese de causa. Essa coluna de contraste é o produto da série inteira — foi o que separou "erro de medição" de "erro de julgamento".

**Passo 5 — atualize o `ESTADO.md`.** Fim de sessão sem isso é progresso perdido.

**Mudança de skill: uma por rodada, com diff e aprovação sua antes de editar.** A fila está no fim do `NOTAS.md`.

### Medir um arquivo avulso, fora de rodada

```bash
uv run --with rhino3dm python evals/check.py output/<arquivo>.3dm \
  --bbox 2400 829 1100 --tol 0.01 --layer "ESTANDE::Mobiliario"
```

---

## 4. Caixa de ferramentas do dia-a-dia

```bash
# medir uma peça qualquer contra o caso balcao_01
uv run --with rhino3dm python evals/check.py output/X.3dm --bbox 2400 829 1100 --tol 0.01 --layer "ESTANDE::Mobiliario"

# quantas chamadas MCP até agora
wc -l logs/rhino_calls.jsonl

# o que o agente fez nas últimas chamadas (sessão, tool, argumentos)
tail -5 logs/rhino_calls.jsonl

# regenerar o mapa de superfície do servidor MCP a partir do log
uv run --no-project python evals/dump_capabilities.py

# quais tools foram usadas, e quantas vezes cada uma
uv run --no-project python -c "import json,collections;c=collections.Counter(json.loads(l)['tool_name'] for l in open('logs/rhino_calls.jsonl',encoding='utf-8') if l.strip());[print(f'{v:>4}  {k}') for k,v in c.most_common()]"
```

Onde olhar quando travar:

| Dúvida | Arquivo |
|---|---|
| onde paramos, próxima ação | `ESTADO.md` |
| como operar do zero, e as defesas do harness | `TUTORIAL.md` |
| que tools o servidor expõe, com `read_only`/`dry_run` | `references/mcp-superficie.md` |
| ordem de rotas e a regra do prefixo `_-` em `run_command` | `references/rhinocommon.md` |
| o que já falhou e por quê | `NOTAS.md` |
| forma orgânica, Kangaroo, SubD | `references/organico-gh.md` |

---

## 5. As seis armadilhas já pagas

1. **`CLAUDE.md` em `dev/` ou acima contamina o agente.** O Claude Code carrega os `CLAUDE.md` dos diretórios pais. Um arquivo de supervisor em `dev/` fez o agente sob teste virar avaliador de si mesmo — rodada 3 anulada, 0 tool calls. O `CLAUDE.md` do supervisor mora em `dev/supervisor/` exatamente por isso. **Nunca crie `CLAUDE.md` em `dev/`.**

2. **`--bare` não é a saída para isolar.** Ele desliga a auto-descoberta de `CLAUDE.md`, mas **também desliga os hooks** — sem hook não há log, sem log não há contagem de tool calls. Para trabalhar no agente a partir do supervisor, use `--add-dir`.

3. **Toda skill em `rhino-agent/.claude/skills/` entra no contexto de toda rodada e vira variável do eval.** Foi o que a `prd-ia` fazia antes de ser removida. Skill de supervisor vai em `dev/supervisor/.claude/skills/`.

4. **O agente sobrescreve a própria evidência.** Nome novo por rodada, cópia em `output/_rodadas/` antes de rodar.

5. **O instrumento também erra.** O `check.py` tinha bug de bbox (media casco de controle em vez de malha) e **reprovou geometria correta** em três rodadas. Corrigido em 19/09. Quando um veredito surpreender, desconfie do instrumento antes de escrever conclusão sobre o modelo.

6. **Texto de skill não vira comportamento sozinho.** A skill manda ler `get_modeling_guidance("verification")` desde o primeiro commit; em 217 chamadas o tópico nunca foi lido. Por isso o que dá para mecanizar está em configuração do servidor, permissão e hook — não em prosa. A hierarquia está em `TUTORIAL.md` §4.3.

---

## 6. Estado atual

Vive em **`ESTADO.md`**, atualizado ao fim de toda sessão. Este manual não repete estado de propósito: informação duplicada é informação que envelhece em um dos dois lugares.

Dois fatos que são de operação, não de estado, e ficam aqui:

- **`settings.json` está pinado em Haiku, e nenhuma rodada de Haiku passou.** Use `--model sonnet` na chamada até o pin mudar.
- **O agente não salva se você não mandar.** Peça o save no prompt, com caminho, até a candidata nº 7 entrar na skill.
