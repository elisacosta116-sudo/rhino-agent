# Templates Grasshopper

## ⚠️ O elo que falta: não há bake pelo MCP

O `rhinomcp` 0.4.1.1 expõe 27 tools `gh_*` que **constroem e calculam** um grafo, e **nenhuma que entregue a geometria ao documento do Rhino**. Medido em 20/09, sessão `ec9b77a3`:

| Capacidade | Existe? |
| --- | --- |
| criar documento, buscar componentes, montar e ligar grafo | sim (`gh_build_graph`, `gh_mutate_graph`) |
| rodar a solução e ler mensagens de erro | sim (`gh_run_solution`) |
| ler o que um parâmetro produziu | **só metadado** |
| **bake para o documento do Rhino** | **não existe** |
| salvar o `.gh` | não existe |

O `gh_get_parameter_value` devolve descrição, não geometria:

```json
{"type":"Brep","is_solid":true,"faces":6}
```

Sem vértices, sem pontos de controle, sem serialização. **A geometria não sai do Grasshopper por este servidor.**

A rota C# de dentro do Rhino também não alcança: o assembly do Grasshopper não é referenciado na compilação, e por reflexão deu `NullReferenceException`.

### Consequência para a arquitetura

A seção 5 do PRD desenha `LLM → parâmetros → template .gh → Rhino → .3dm`. A última seta **não existe** neste servidor. O agente monta o template, roda, confirma que o sólido fechou com 6 faces — e não consegue entregar nada.

Isso não é falha do agente nem do template. É limite da ponte.

**Este é o gatilho para reavaliar o servidor MCP**, que o `NOTAS.md` tinha deixado condicionado a "necessidade de Rhino 9, necessidade de Grasshopper 2, ou fila de skills esgotada". Há agora um quarto motivo, mais forte que os três.

## O formato versionado é JSON, não `.gh`

Como não há `gh_save`, o grafo vive só na sessão aberta do Grasshopper. O template versionado deste repositório é o **JSON no formato de entrada do `gh_build_graph`**, e não o binário.

Isso é melhor, não pior:

- é diffável no git — dá para revisar a mudança de um template como se revisa código;
- é exatamente o que `gh_build_graph` consome, sem conversão;
- casa com a arquitetura do PRD, em que o LLM preenche parâmetros de algo já declarado.

Para regenerar um template a partir de um canvas montado à mão:

```bash
uv run --no-project python evals/gh_canvas_para_template.py <canvas.json> gh-templates/<nome>.json
```

O `<canvas.json>` é a resposta de `gh_get_canvas_state`.

## `balcao.json`

Primeiro template do catálogo. 21 componentes, 26 conexões.

**Parâmetros:**

| Slider | Valor | Faixa |
| --- | --- | --- |
| `corda` | 2400 | 500 – 6000 |
| `flecha` | 300 | 10 – 1500 |
| `profundidade` | 600 | 50 – 1500 |
| `altura` | 1100 | 100 – 3000 |

**Cadeia:** `corda` ÷ 2 → pontos A, B, C → `Arc 3Pt` → `Offset Curve` (distância negativa, para o centro) → `End Points` + 2 `Line` → `Flatten Tree` → `Join Curves` → `Extrude` (vetor Z = `altura`) → `Cap Holes`.

**Estado: monta e calcula, não entrega.** Com os valores acima, o grafo produz perfil fechado de 5609,6 mm e um Brep sólido de 6 faces — consistente com R = 2550, r = 1950 e bbox ≈ 2400 × 829 × 1100. **Isso não foi verificado pelo `check.py`**, porque não há como trazer o sólido ao Rhino. É leitura dos componentes do GH, não medição do artefato.

Duas armadilhas encontradas ao montar, que valem para os próximos templates:

- **Offset com distância positiva vai para fora.** O perfil saiu com 3086 mm em vez de 1910. Precisa de `Negative` na profundidade.
- **`Join Curves` gera ramos separados** quando as linhas vêm de uma árvore mais profunda que o arco. Precisa de `Flatten Tree` antes.

## `_canvas_bruto.json`

Resposta literal de `gh_get_canvas_state` da sessão `ec9b77a3`. Guardado como origem da conversão, para a tradução poder ser auditada. Não é o template.
