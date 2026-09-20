# Formas orgânicas em Rhino e Grasshopper

Referência para quem constrói os templates `.gh` do catálogo. A forma orgânica
mora no template — o LLM só preenche parâmetros.

## O ponto de partida: o MCP já fala Grasshopper

O `rhinomcp` expõe **27 comandos `gh_*`** (ver `references/mcp-superficie.md`):
criar documento, buscar componentes por nome ou categoria, adicionar, conectar,
ler e escrever valores de parâmetro, rodar a solução, capturar preview do canvas.
Em 208 chamadas registradas nas rodadas de avaliação, **nenhum foi usado**.

Isso importa para o catálogo: dá para construir e ajustar definições Grasshopper
programaticamente, não só carregar `.gh` prontos. `gh_build_graph` e
`gh_mutate_graph` aplicam várias operações de canvas numa chamada só.

## Kangaroo 2 — relaxação e form-finding

Vem **instalado** com o Rhino 6 e superior; não precisa baixar nada. É baseado em
dinâmica relaxada e organizado por *goals* (metas), diferente do Kangaroo 1, que
era baseado em forças — tutorial antigo de Kangaroo 1 não se aplica.

Padrão de montagem:

- Reconstrua o modelo como conjunto de goals e monte um "playground" onde a
  simulação roda, separado da geometria final.
- Organize os goals em árvore com `Entwine` na entrada do solver e `Unflatten Tree`
  na saída.
- Use o goal `Show` para passar geometria discreta (pontos, linhas, polilinhas,
  malhas) pelo solver e reconstituir a malha de saída.
- Selecione vértices de borda com o componente `Mesh Edges` por valência —
  valência 1 são as arestas nuas, que normalmente viram âncoras.
- Os arquivos de exemplo que acompanham o Kangaroo 2, mais o PDF de documentação,
  são o caminho mais rápido para o fluxo por goals.

Casos diretamente úteis para estande: superfície tensionada entre dois perfis,
malha inflada a partir de curvas de borda com curvas fixas, cobertura tipo vela
apoiada em quatro pontos.

## Remesh antes de relaxar

Sem remesh, a topologia original da malha permanece e a relaxação produz
distorção irregular. `MeshMachine` faz remesh triangular com adaptação a
features, gerando triângulos menores onde a curvatura pede.

Cuidado registrado pela comunidade: com `Pull` em 0 ele tende a colapsar a malha;
costuma-se rodar por pouco tempo — por exemplo, para relaxar a união booleana de
sólidos do Rhino numa forma curva contínua.

## SubD como origem da forma

O caminho usual é modelar a massa em SubD no Rhino, converter para malha quad ou
tri, remeshar e só então relaxar. SubD dá controle de forma com poucos pontos —
que é a mesma lógica da heurística NURBS da skill: menos pontos de controle,
superfície mais limpa.

## Mapear geometria sobre a forma relaxada

`MeshMap` (Kangaroo) funciona entre duas malhas de **mesma topologia**. Isso
permite desenhar o padrão numa malha UV plana (via `_ExtractUVMesh`) e mapear de
volta na superfície de dupla curvatura — o caminho natural para painelar um
estande orgânico sem desenhar cada painel.

Para a fase 2 (fabricação), é aqui que entra a verificação de planaridade por
painel: painel não planar em forma de dupla curvatura é o modo de falha mais
comum, e é o motivo de a fabricação ter go/no-go próprio no PRD.

## Fontes

- [Mesh relaxation in Kangaroo 2 — fórum Grasshopper](https://www.grasshopper3d.com/group/kangaroo/forum/topics/mesh-relaxation-in-kangaroo2)
- [Mesh Relaxation (+Kangaroo) — Food4Rhino](https://www.food4rhino.com/en/resource/mesh-relaxation-kangaroo)
- [Como relaxar uma forma com Kangaroo — fórum Grasshopper](https://www.grasshopper3d.com/forum/topics/how-to-relax-my-form-using-kangaroo)
- [Tensile Kangaroo — Parametric House](https://parametrichouse.com/parametric/tensile-kangaroo/)
- [Four-point sail — parametric by design](https://parametricbydesign.com/grasshopper/tutorials/four-point-sail/)
