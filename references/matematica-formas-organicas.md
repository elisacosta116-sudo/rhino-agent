# Matemática das formas orgânicas

Referência para quem constrói os geradores paramétricos. O ponto não é teoria: é
que **forma orgânica tem dois números que decidem quase tudo**, e ignorá-los é o
que faz um estande bonito na tela virar impossível de fabricar.

## As duas curvaturas

Em cada ponto de uma superfície há duas curvaturas principais. Delas saem os dois
números que interessam:

| | Definição | O que significa na prática |
| --- | --- | --- |
| **K** — curvatura gaussiana | produto das curvaturas principais | `K = 0` → superfície **desenvolvível**: pode ser cortada em chapa plana e dobrada, sem esticar |
| **H** — curvatura média | média das curvaturas principais | `H = 0` → **superfície mínima**: menor área para um contorno dado, é a forma da película de sabão |

**Por que K importa para estande:** superfície desenvolvível é indistinguível do
plano do ponto de vista da geometria intrínseca — a transformação preserva
comprimentos e ângulos, então dá para cortar e dobrar, mas não esticar. É
exatamente a condição de fabricar em chapa, MDF curvado ou lona, sem deformação.
Superfície de dupla curvatura tem `K ≠ 0` e **não** desenvolve: ou vira painel
plano aproximado, ou exige conformação real do material.

O Rhino calcula isso: a análise de curvatura gaussiana verifica desenvolvibilidade
direto no modelo. É o teste de fabricabilidade mais barato que existe, e cabe na
fase 2 do PRD.

**Por que H importa:** a curvatura média é a variação da área em relação à
deformação, então superfície mínima é a que minimiza área e energia de dobra ao
mesmo tempo. Daí ela aparecer na natureza — e daí membranas tensionadas na
arquitetura serem baseadas em superfícies mínimas, tradição que vem de Frei Otto.
Para estande: mínimo de material para o mesmo vão.

## Form-finding — a forma não se desenha, se encontra

Forma de membrana não é desenhada ponto a ponto: ela é o resultado de um
equilíbrio. Historicamente por modelo físico — as películas de sabão do Frei Otto
— hoje por simulação.

Três caminhos, do mais prático ao mais teórico:

1. **Relaxação dinâmica** — é o que o Kangaroo 2 faz, por *goals*. O caminho
   prático no Grasshopper, ver `references/organico-gh.md`.
2. **Fluxo de curvatura média** (*mean curvature flow*) — parte de uma superfície
   qualquer e a evolui até o equilíbrio, com redistribuição tangencial dos nós
   para manter uniformidade. É uma EDP geométrica de segunda ordem.
3. **Geometria diferencial discreta** — teoria de curvatura para malhas, com
   malhas mínimas e de curvatura média constante discretas. É o que dá base
   matemática para painelar quad, pentagonal e hexagonal com viga bem definida.

Estruturas tensionadas evitam flexão e flambagem, então o projeto **começa** por
encontrar o estado de equilíbrio sob tensão e condições de contorno — não por
desenhar a forma e depois calcular.

## Continuidade: G0, G1, G2

A skill `rhino-nurbs` já usa esses termos. O que eles significam:

- **G0** — as superfícies se tocam. Há quina visível.
- **G1** — compartilham plano tangente no ponto de contato. Sem quina, mas o
  reflexo quebra.
- **G2** — a curvatura também coincide. Reflexo contínuo.

**G2 não é capricho de acabamento.** É condição para existirem **linhas de
curvatura bem definidas atravessando a superfície** — e malha por linha de
curvatura é a estratégia padrão de racionalizar pele de forma livre. Sem G2, a
painelização não tem em que se apoiar.

## O limite do NURBS por retalhos

Vale saber onde a ferramenta trava. NURBS é o modelo padrão para curva e
superfície livre, mas montar forma orgânica costurando retalhos tem dois
problemas conhecidos:

- **Pontos extraordinários** — onde um número incomum de arestas converge.
  Formulações de retalho único têm graus de liberdade insuficientes ali, o que
  limita a continuidade de curvatura; assimetria aparece como distorção de
  curvatura perto desses pontos. Catmull-Clark e Loop são comprovadamente menos
  suaves nos pontos extraordinários que no resto da superfície.
- **Influência global** — mexer num ponto de controle propaga efeito além do
  desejado.

Foi por isso que SubD e T-splines ganharam espaço: crescem uma folha única
estanque, concentrando controle onde a curvatura torce ou converge. Para estande
orgânico, **modelar em SubD e converter** costuma ser mais produtivo que costurar
NURBS — é o caminho descrito em `references/organico-gh.md`.

O termo do ofício para o alvo de qualidade é *Class-A surfacing*: G2/G3 com fluxo
de curvatura estável e superfície estanque.

## Racionalização — onde forma vira peça

Ordem sugerida, da forma para a fabricação:

1. Encontrar a forma (relaxação).
2. Verificar `K` — o que é desenvolvível sai barato; o resto exige decisão.
3. Malhar seguindo linhas de curvatura (exige G2).
4. Painelar. Para malha triangular há a via do empacotamento de círculos, cujos
   incírculos formam um empacotamento sobre a superfície.
5. Verificar planaridade painel a painel. Painel não planar em dupla curvatura é
   o modo de falha número um.

## Livros e artigos

**Geometria diferencial, base:**
- do Carmo, *Differential Geometry of Curves and Surfaces*, Prentice-Hall, 1976 — o clássico.
- Abbena, Salamon & Gray, *Modern Differential Geometry of Curves and Surfaces with Mathematica*, CRC Press, 2017.

**NURBS e CAD:**
- Piegl & Tiller, *The NURBS Book* — a referência de NURBS.
- Pottmann & Wallner, *Computational Line Geometry*, Springer, 2001.

**Arquitetura e forma livre:**
- [Geometry of architectural freeform structures](https://www.researchgate.net/publication/221115565_Geometry_of_architectural_freeform_structures) — geometria diferencial discreta aplicada a malhas de arquitetura.
- [Minimal surfaces for architectural constructions](https://www.researchgate.net/publication/47393592_Minimal_surfaces_for_architectural_constructions) — superfícies mínimas em construção, a linhagem do Frei Otto.
- [Free-form Design of Discrete Architectural Surfaces by use of Circle Packing](https://arxiv.org/pdf/2103.07584) — racionalização por empacotamento de círculos.
- [Computer-Aided Design of Developable Surfaces](https://dcain.etsin.upm.es/~leonardo/papers/jc18.pdf) — desenvolvibilidade e curvatura gaussiana nula em CAD.
- [Computing minimal surfaces by mean curvature flow](https://www.researchgate.net/publication/324259049_Computing_minimal_surfaces_by_mean_curvature_flow_with_area-oriented_tangential_redistribution) — o método por fluxo de curvatura média.
- [NURBS continuity: applications in architecture, product and digital fabrication](https://eaapublishing.org/journals/index.php/technorev/article/view/683) — G1/G2 para segmentar e reagregar superfície complexa.
- [Why NURBS patchcraft gave way to subdivision and T-splines](https://novedge.com/blogs/design-news/design-software-history-continuity-in-freeform-cad-why-nurbs-patchcraft-gave-way-to-subdivision-and-t-splines) — o limite dos pontos extraordinários, em linguagem de projeto.
- Tang, Bo, Wallner & Pottmann, "Interactive design of developable surfaces", ACM TOG 35(2), 2016.

## Duas lacunas honestas desta referência

1. **Pottmann, Asperl, Hofer & Kilian, *Architectural Geometry*** é o livro
   canônico que cobre tudo acima de forma integrada. Ele **não apareceu** nas
   buscas que fiz, então está citado de memória e não verificado — confira antes
   de comprar.
2. **Superfícies implícitas e metaballs** — a via de forma fluida por campo
   escalar e blend, que seria natural para estande orgânico, não retornou nada
   nas buscas. É um buraco desta referência, não um tema inexistente.
