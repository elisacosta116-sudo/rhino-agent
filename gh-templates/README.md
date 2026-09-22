# Templates Grasshopper

## ✅ O elo que faltava existe: bake por IronPython

**Resolvido em 21/09.** O `rhinomcp` 0.4.1.1 expõe 27 tools `gh_*` que constroem e calculam um
grafo, e **nenhuma delas bakeia** — mas o bake não precisa ser tool do MCP. Ele é feito por
`evals/bake_gh.py`, um **script versionado** enviado verbatim para `execute_rhinoscript_python_code`:

```python
import clr
clr.AddReference("Grasshopper")
import Grasshopper as gh
doc_gh = gh.Instances.ActiveCanvas.Document
```

| Capacidade | Existe? |
| --- | --- |
| criar documento, buscar componentes, montar e ligar grafo | sim (`gh_build_graph`, `gh_mutate_graph`) |
| rodar a solução e ler mensagens de erro | sim (`gh_run_solution`) |
| ler o que um parâmetro produziu | só metadado (`{"type":"Brep","is_solid":true,"faces":6}`) |
| **bake para o documento do Rhino** | **sim, por `evals/bake_gh.py`** |
| salvar o `.gh` | não existe |

**Por que a rota C# falhava e esta não.** O `execute_rhinocommon_csharp_code` não alcança o
Grasshopper porque o assembly está fora da compilação (por reflexão, `NullReferenceException`). O
plugin executa scripts com `PythonScript.Create()` — IronPython 2.7, em processo — e IronPython
resolve assembly em **tempo de execução**. Era só isso.

**Medido:** 18 objetos bakeados, camada `ESTANDE::Mobiliario` criada pelo script, bbox
2400 × 829,41 × 1100 mm. Confirmado pela resposta do servidor no `logs/rhino_calls.jsonl`.

### Consequência para a arquitetura

A seção 5 do PRD (`LLM → parâmetros → template → Rhino → .3dm`) **fica de pé**, e a última seta é
infraestrutura do harness, como o `check.py`.

⚠️ **A garantia é de disciplina, não de trava.** O bake usa a superfície de código arbitrário que o
projeto fechou de propósito. O script é **literal, versionado e revisado**, e o modelo **nunca o
escreve** — é isso que mantém de pé o "o LLM emite parâmetros, não código". Se um dia o agente
escrever o próprio bake, a garantia caiu sem ninguém notar.

**Falta:** seletor de componente (hoje bakeia os 18 objetos do canvas, geometria de construção
incluída) e o passo de bake no `evals/rodada.py`.

## 🛑 Aberto: este template não remonta a partir do JSON

Na remontagem de 21/09 via `gh_build_graph`, os 21 componentes e 26 conexões entraram sem erro, mas
a solução **não rodou limpa**: `Cap Holes` deu `Capping algorithm failed to return a result.`, porque
o `Join Curves` saiu com `data_count: 2` — o perfil não fechou numa curva única.

**É a armadilha declarada resolvida mais abaixo neste mesmo arquivo.** O `Flatten Tree` está no
template e a fiação está correta (`arc`, `offset`, `ln`, `ln_2` → `flatten` → `join`).

**Isto ataca a aposta do formato versionado**, não só este template: o JSON deveria ser reprodutível,
e a reprodutibilidade falhou na primeira tentativa de exercê-la. Duas hipóteses, nenhuma
investigada — o conversor `evals/gh_canvas_para_template.py` perde informação, ou o `gh_build_graph`
liga diferente do canvas original. O `_canvas_bruto.json` existe exatamente para esta auditoria.

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

### ⚠️ Toda conexão precisa de `source_output_name`

O contrato do `gh_build_graph` marca o campo como opcional. **Na prática ele é obrigatório:** uma
origem com mais de uma saída fica ambígua sem ele, e o build cai silenciosamente na saída 0.

Foi o que quebrou este template. As duas linhas do perfil puxam de `End Points` — `lnS` da saída
`Start`, `lnE` da saída `End` — e sem o nome as duas viraram `Start`. O perfil não fechava, o
`Join Curves` saía com `data_count: 2` e o `Cap Holes` falhava, **cinco componentes adiante da
causa**. É o tipo de perda que não aparece na conversão, só na remontagem.

O conversor agora emite o campo a partir do `param_name` do `gh_get_canvas_state`, e **avisa**
quando uma conexão vem de origem com várias saídas sem dizer qual. No formato antigo, o aviso
pegava 5 conexões deste template.

### Os aliases vêm do canvas, quando existem

O conversor prefere o `alias` que o próprio canvas carrega — `pA`, `lnS`, `ends`, `flatAll` — em vez
de derivar do nickname. Três `Construct Point` têm o mesmo nickname `Pt` e virariam `pt`, `pt_2`,
`pt_3`, numerados por ordem de iteração: o template deixaria de ser legível, que é metade da razão
deste formato existir. Só cai na derivação quando o canvas não traz alias válido.

## `balcao.json`

Primeiro template do catálogo. 21 componentes, 26 conexões.

**Parâmetros:**

| Slider | Valor | Faixa |
| --- | --- | --- |
| `corda` | 2400 | 500 – 6000 |
| `flecha` | 300 | 10 – 1500 |
| `prof` | 600 | 50 – 1500 |
| `altura` | 1100 | 100 – 3000 |

Os aliases são a **interface pública** do template — é neles que o PRD encosta o "LLM preenche
parâmetros de algo já declarado". `prof` era `profundidade` até 21/09, quando o conversor passou a
respeitar o alias do canvas; o nome real do grafo sempre foi `prof`.

**Cadeia:** `corda` ÷ 2 → pontos A, B, C → `Arc 3Pt` → `Offset Curve` (distância negativa, para o centro) → `End Points` + 2 `Line` → `Flatten Tree` → `Join Curves` → `Extrude` (vetor Z = `altura`) → `Cap Holes`.

**Estado: entrega, mas não remonta.** Na sessão original de 20/09 o grafo produziu perfil fechado de 5609,6 mm e um Brep sólido de 6 faces — consistente com R = 2550, r = 1950 e bbox ≈ 2400 × 829 × 1100. **Isso nunca foi verificado pelo `check.py`**: era leitura dos componentes do GH, não medição do artefato.

Agora há bake, então a medição é possível — mas **a remontagem a partir deste JSON falha no `Cap Holes`** (ver bloqueio no topo). Enquanto isso não for resolvido, o número acima continua sendo alegação de 20/09, não evidência.

Duas armadilhas encontradas ao montar, que valem para os próximos templates:

- **Offset com distância positiva vai para fora.** O perfil saiu com 3086 mm em vez de 1910. Precisa de `Negative` na profundidade.
- **`Join Curves` gera ramos separados** quando as linhas vêm de uma árvore mais profunda que o arco. Precisa de `Flatten Tree` antes.

## `_canvas_bruto.json`

Resposta literal de `gh_get_canvas_state` da sessão `ec9b77a3`. Guardado como origem da conversão, para a tradução poder ser auditada. Não é o template.
