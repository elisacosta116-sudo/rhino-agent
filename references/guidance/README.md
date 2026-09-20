# Guias do servidor rhinomcp

O próprio servidor traz um guia de modelagem em 6 tópicos, acessível por
`get_modeling_guidance("<topico>")` ou pelo resource `rhinomcp://guidance/{topic}`.

| Tópico | Capturado aqui | Observação |
| --- | --- | --- |
| `overview` | sim — `overview.md` | único que aparece no log das rodadas |
| `transforms` | **não** | ancoragem de criação e pivô de rotação variam por tool |
| `planar_regions` | **não** | face planar com furos |
| `organization` | **não** | nomes e camadas hierárquicas |
| `verification` | **não** | **as checagens que a skill manda ler no passo 5** |
| `recovery` | **não** | o que fazer após falha ou interrupção |

## Por que faltam cinco

Só o `overview` foi capturado porque é o único que o agente chegou a chamar. Em
todas as rodadas registradas (208 chamadas MCP), `get_modeling_guidance` foi
chamado 4 vezes — **sempre com `overview`**. O tópico `verification` nunca foi
lido, apesar de a skill `rhino-nurbs` mandar lê-lo no passo 5 e de o próprio
`overview` repetir a instrução ("Retrieve verification for the checks to use").

Esse é um dos achados que explicam as rodadas 1 e 2: o agente declarou sucesso
sem nunca consultar as checagens que o servidor oferece.

## Como capturar os que faltam

Exige uma sessão com o Rhino aberto e `mcpstart` ativo. Para cada tópico:

```
get_modeling_guidance("transforms")
get_modeling_guidance("planar_regions")
get_modeling_guidance("organization")
get_modeling_guidance("verification")
get_modeling_guidance("recovery")
```

Grave cada resposta como `<topico>.md` nesta pasta, com o mesmo cabeçalho do
`overview.md`: conteúdo literal do servidor, sem paráfrase. **Não escreva de
memória o conteúdo desses tópicos** — o objetivo do corpus é justamente eliminar
invenção.
