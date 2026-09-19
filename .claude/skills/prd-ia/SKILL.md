---
name: prd-ia
description: Escreve e revisa PRDs de produtos e features de IA (agentes, LLM, MCP, RAG). Use sempre que o usuário pedir PRD, spec, requisitos, escopo, critérios de sucesso, plano de evals, ou quiser transformar uma ideia de produto de IA em documento — inclusive quando disser apenas "documenta essa feature" ou "o que precisa pra construir isso".
---

# PRD para produtos de IA

Um PRD de IA difere de um PRD comum em um ponto: o sistema é não-determinístico. Todo requisito precisa dizer como será medido quando a mesma entrada puder gerar saídas diferentes.

## Estrutura obrigatória

**1. Problema.** Quem sofre, com que frequência, e quanto isso custa hoje (tempo, dinheiro, retrabalho). Um parágrafo. Sem solução aqui.

**2. Usuário-alvo.** Um perfil primário, com nível técnico explícito. Ex.: "cenógrafo que usa Rhino 2×/semana e não sabe Grasshopper".

**3. Métrica de sucesso.** Uma métrica norte, numérica e com prazo, mais 2 guardrails. Ex.: "70% dos pedidos geram sólido válido sem edição manual em 30 dias; guardrails: custo < US$ 0,05/pedido, p95 de latência < 20 s".

**4. Escopo e não-escopo.** O não-escopo é tão importante quanto o escopo. Liste o que foi conscientemente deixado de fora.

**5. Arquitetura resumida.** Modelo(s), tools/MCP, fonte de dados, onde roda, quem paga licença. Um diagrama simples basta.

**6. Tratamento do não-determinismo.** Onde a saída do modelo é restringida (schema, templates, enum), onde é livre, e o que acontece quando ela falha (retry, fallback, humano).

**7. Plano de evals.** Um dataset com no mínimo 30 casos reais, divididos em fáceis, médios e casos de borda. Para cada caso: critério de aprovação verificável por código sempre que possível (ex.: `IsSolid`, bounding box ± tolerância). Informe a baseline atual e a meta.

**8. Casos de borda e modos de falha.** Tabela com: situação, comportamento esperado, severidade.

**9. Riscos e premissa mais frágil.** Identifique a premissa que, se errada, mais afeta o projeto. Quantifique o impacto (custo, prazo, % de retrabalho) e defina o sinal que invalida essa premissa.

**10. Rollout.** Piloto (quem, quantos, por quanto tempo) e o critério de go/no-go.

## Regras de escrita

- Prefira números a adjetivos. "Rápido" é proibido; use "p95 < 20 s".
- Todo requisito deve ser testável. Se não dá pra escrever o teste, reescreva o requisito.
- Marque premissas com `[PREMISSA]` e decisões com `[DECISÃO]`.
- Ao revisar um PRD, comece pela seção 9: aponte a premissa mais frágil e o impacto se ela estiver errada, antes de qualquer comentário de forma.
