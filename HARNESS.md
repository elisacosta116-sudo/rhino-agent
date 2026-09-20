# Harness do agente Rhino — guia de configuração

O harness é tudo o que envolve o modelo: instruções persistentes, ferramentas, permissões, hooks, logs e evals. O modelo (Haiku 4.5) é a peça trocável; o harness é o que torna o comportamento previsível.

## Estrutura do projeto

```
rhino-agent/
├── CLAUDE.md                 # contexto persistente do projeto
├── .mcp.json                 # servidores MCP do projeto (gerado pelo `claude mcp add --scope project`)
├── .claude/
│   ├── settings.json         # modelo, permissões, hooks
│   ├── hooks/log_call.py     # PostToolUse: registra toda chamada MCP
│   ├── hooks/guard_call.py   # PreToolUse — escrito, INERTE (não registrado; ver camada 5)
│   └── skills/
│       └── rhino-nurbs/SKILL.md
├── gh-templates/             # definições .gh parametrizadas (a rota preferida da skill)
├── references/               # superfície do MCP, guias do servidor, APIs, técnicas orgânicas
├── evals/
│   ├── cases.jsonl           # casos de teste, com o histórico medido de cada rodada
│   ├── check.py              # verificação do .3dm — fonte de verdade dos vereditos
│   ├── rodada.py             # runner: executa e mede uma rodada inteira
│   └── dump_capabilities.py  # regenera references/mcp-superficie.md
├── ESTADO.md                 # onde paramos — atualizado ao fim de toda sessão
├── TUTORIAL.md               # como operar, do zero
├── OPERACAO.md               # manual de bancada
├── NOTAS.md                  # histórico das rodadas
└── logs/
```

## CLAUDE.md (camada 1: contexto)

Seja curto: o Haiku segue instruções curtas e específicas melhor do que documentos longos. Um bom ponto de partida:

```markdown
# Projeto: agente NURBS
- Rhino 8 via MCP `rhino`. Unidade padrão: mm. Z vertical.
- Para qualquer geometria, siga a skill `rhino-nurbs` (inspecionar → construir → verificar → reportar).
- Rota preferida: templates em gh-templates/ > tools MCP > comandos Rhino > script curto.
- Nunca declare sucesso sem IsValid/IsSolid verificados.
- Arquivos de saída vão para ./output com sufixo _vN.
```

## settings.json (camadas 2 e 3: modelo e permissões)

```json
{
  "model": "claude-haiku-4-5-20251001",
  "permissions": {
    "allow": ["mcp__rhino", "Read", "Edit(./gh-templates/**)", "Edit(./evals/**)"],
    "deny": ["Bash(rm:*)", "Bash(curl:*)", "Read(./.env)"]
  },
  "hooks": {
    "PostToolUse": [
      { "matcher": "mcp__rhino__.*",
        "hooks": [ { "type": "command", "command": "uv run --no-project python .claude/hooks/log_call.py" } ] }
    ]
  }
}
```

O `model` aqui é o pin do arquivo. A decisão medida é outra: **Sonnet passa, Haiku não** — mesma skill, mesmo caso, três falhas contra uma aprovação. Enquanto o pin não muda, o modelo vai na chamada (`--model sonnet`).

O hook chama `.claude/hooks/log_call.py`, que grava toda chamada ao MCP do Rhino (entrada e resultado chegam via stdin em JSON). Ele é em Python, e não em shell, para funcionar igual no Windows e no Mac. Esse log é a matéria-prima dos evals: você vai descobrir quais tools falham, quantas chamadas cada pedido consome e onde o Haiku se perde.

O script cria `logs/` sozinho; crie `output/` antes do primeiro uso.

## Camada 4: evals

Sem evals, não dá para saber se uma mudança na skill melhorou ou piorou o agente. Formato mínimo de `evals/cases.jsonl`:

```json
{"id": "balcao_01", "prompt": "balcão curvo 2400mm corda, 1100 alto, 600 profundo", "check": {"is_solid": true, "bbox_mm": [2400, 900, 1100], "tol": 0.01}, "tier": "medio"}
```

Rode cada caso em modo headless (`claude -p "<prompt>" --output-format json`), consulte a geometria resultante pelo MCP e compare com o `check`. Registre a taxa de aprovação por tier, o número médio de tool calls e o custo. Monte 30 casos antes de mexer na skill; depois disso, toda alteração na skill passa pelo eval.

## Camada 5: defesas mecânicas

As quatro camadas acima assumem que o modelo coopera. A evidência diz que não dá para assumir isso: a skill manda ler `get_modeling_guidance("verification")` no passo 5 desde o primeiro commit e, em **217 chamadas registradas, esse tópico nunca foi lido**. A regra "tolerância é binária" está escrita e o Haiku marcou OK com desvio de 585%.

Daí a hierarquia que organiza o harness hoje:

```
configuração do servidor  >  regra de permissão  >  hook  >  texto de skill
        (inescapável)         (bloqueia a tool)   (condiciona)  (pede por favor)
```

**Uma regra que vira mecanismo sai da fila de candidatas de skill.** Foi o que aconteceu com três das oito: a nº 1 virou variável de ambiente, a nº 3 e a nº 4 viraram hook e permissão.

### Configuração do servidor

O `rhinomcp` expõe controles por variável de ambiente, declaradas no `.mcp.json`:

```json
"env": { "RHINO_MCP_PERCEPTION": "1" }
```

`RHINO_MCP_PERCEPTION=1` faz o servidor pôr `include_delta` **e** `include_health` no envelope de toda operação que modifica o documento (`server.py:547`). O plugin anexa ao resultado um `_delta` com os ids criados e removidos, e um `_health` com os objetos que falham validade e o motivo. **O modelo não participa dessa decisão** — a validação vem junto com o retorno da operação, obedeça ele ou não. É o antídoto direto ao modo de falha central do projeto, declarar sucesso sem verificar.

Outros controles do servidor existem e **não estão ligados**: `RHINO_MCP_VALIDATE` (modos `off`/`warn`/`strict`, default `warn`) e `RHINO_MCP_TIMEOUT` (15 s). Ligar qualquer um é mudança de harness e abre série nova.

### Regra de permissão e hook: propostos e não adotados

A hierarquia acima é atraente, e por isso perigosa: ela convida a mecanizar tudo que dá, antes de saber se a coisa mecanizada é a certa.

Em 20/09 foram propostos um `deny` de `execute_rhinocommon_csharp_code` e um hook `PreToolUse` com três regras. **A investigação do log reprovou os dois.** O resumo está em `NOTAS.md`, seção "O que foi proposto, analisado e REJEITADO"; o essencial:

- A única rodada aprovada construiu 100% da geometria em C#, e o erro de C# dela foi de compilação (`CS1061`), não API inventada. A rota Python tem 0 aprovações em 2 sessões. Fechar C# trocaria a única rota com sucesso por uma sem.
- A regra "Python só depois de `get_rhinoscript_docs`" negaria a primeira tentativa com certeza: o agente chamou essa tool **zero** vezes em 4 rodadas.

`.claude/hooks/guard_call.py` está escrito e testado, e **inerte** — não registrado no `settings.json`. Dois defeitos a corrigir antes de qualquer reconsideração: falha fechada se `logs/` ficar sem escrita (lista vazia ⇒ nega tudo), e lê o log inteiro a cada chamada MCP (1,37 MB hoje, por causa dos PNG em base64 do `capture_viewport`).

**A lição é de método, não de ferramenta.** Mecanismo é mais forte que texto, mas só depois de a regra estar certa. Mecanizar uma regra errada a torna mais difícil de derrubar, não menos.

## Camada 6: corpus de referência

O agente precisa de conhecimento que não cabe na skill e que ele não pode inventar: nomes de tool, assinaturas de API, guias do servidor, matemática de forma. Isso vive em `references/` e é recuperado **por caminho**, não por busca.

A skill traz uma tabela de roteamento — "para esta dúvida, leia este arquivo" — e o Claude Code carrega o arquivo quando a skill o nomeia. É recuperação determinística: não erra, não classifica errado, não precisa de índice.

**Por que não há índice vetorial.** O corpus tem 6 documentos e cabe inteiro em contexto. Um índice de embeddings aqui trocaria recuperação determinística por probabilística, acrescentaria uma dependência e um pipeline de reindexação, e resolveria um problema de escala que não existe. O que falta ao corpus hoje não é busca — é **cobertura**: 5 dos 6 tópicos de `get_modeling_guidance` nunca foram capturados, e o mais importante deles (`verification`) é justamente o que a skill manda ler.

**Gatilho para reavaliar:** quando o catálogo de geradores `.gh` passar de ~20 e a pergunta virar *"qual gerador chega mais perto deste briefing?"*. Aí a consulta é semântica sobre descrições de forma, não uma busca por nome exato, e o índice se justifica. É seleção de template, não geometria — e por isso não bloqueia nada do que está em curso.

## Camada 7: portabilidade (se um dia virar plataforma)

O escopo atual é o servidor MCP local: uma instância do Rhino com interface, um documento, um cliente. Se o projeto evoluir para multiusuário, o backend passa a ser o Rhino.Compute (que roda no Windows 11 para desenvolvimento e exige Windows Server em produção). Três hábitos de agora evitam retrabalho depois:

- Mantenha a lógica geométrica nos templates `.gh` de `gh-templates/`. Eles rodam tanto no Rhino desktop quanto no Compute (via Hops/`compute.rhino3d`).
- Faça o LLM produzir **parâmetros** (JSON validado por schema), e não código. Execução de Python arbitrário num servidor multiusuário equivale a um RCE.
- Os evals de hoje viram o teste de regressão da plataforma.
