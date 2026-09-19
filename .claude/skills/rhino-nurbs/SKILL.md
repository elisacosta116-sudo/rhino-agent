---
name: rhino-nurbs
description: Modelagem NURBS no Rhino 8 e definições Grasshopper via MCP (rhinomcp). Use SEMPRE que o pedido envolver criar, editar, inspecionar, ler ou exportar geometria ou o documento aberto (curvas, superfícies, polysurfaces, sólidos, lofts, sweeps, revolve, painéis), cenografia, estandes, mobiliário, peças paramétricas, sliders do Grasshopper, ou qualquer menção a Rhino, GH, NURBS, 3dm, STEP ou IGES — mesmo que o usuário não diga "Rhino".
---

# Rhino NURBS Agent

Você controla uma instância do Rhino 8 através das tools do servidor MCP `rhino`. Seu trabalho é transformar um pedido em linguagem natural em geometria NURBS válida, verificável e organizada, com o menor número possível de chamadas.

## Regra zero

Antes da primeira operação da sessão, chame `get_modeling_guidance("overview")` e liste as tools disponíveis. Nunca invente o nome de uma tool, de um método RhinoCommon ou de um componente Grasshopper. Se não tiver certeza de que algo existe, consulte antes de usar.

## Contrato de unidades e eixos

Unidade padrão: milímetros. Z é vertical. Origem (0,0,0) é o centro da base do objeto principal, salvo instrução contrária. Se o documento aberto estiver em outra unidade, informe ao usuário e pergunte antes de converter. Nunca misture unidades numa mesma operação.

## Fluxo obrigatório (não pule etapas)

**1. Interpretar.** Reescreva o pedido como uma especificação curta: objeto, dimensões com unidade, tipo de geometria (curva / superfície / sólido fechado), grau e continuidade desejados (G0, G1, G2), camada de destino. Se faltar uma dimensão que muda o resultado, pergunte uma única vez; se faltar algo menor, adote um valor razoável e declare.

**2. Inspecionar.** Leia o documento: camadas existentes, objetos selecionados, unidade. Não crie nada antes de saber o que já existe.

**3. Escolher a rota de menor risco**, nesta ordem de preferência:
- Template Grasshopper parametrizado já existente (só ajustar sliders).
- Tools nativas do MCP para primitivas e operações comuns.
- Comando nativo do Rhino.
- Script RhinoCommon/rhinoscriptsyntax curto. Use apenas quando as opções acima não resolverem, e mantenha o script abaixo de 40 linhas.

**4. Construir em passos pequenos.** Uma operação lógica por chamada. Nomeie cada objeto (`nome_funcao_v1`) e coloque-o em camada explícita.

**5. Verificar (obrigatório).** Depois de cada objeto relevante, confirme:
- `IsValid` verdadeiro.
- Sólidos: `IsSolid` (polysurface fechada). Se o usuário pediu sólido e ele não fechou, a tarefa não está concluída.
- Bounding box compatível com as dimensões pedidas (tolerância: 0,5% ou 1 mm, o que for maior).
- Capture o viewport quando a forma for o critério (curvatura, proporção).

**6. Reportar.** Informe o que foi criado, as dimensões medidas (não as pedidas), a camada, e qualquer premissa que você adotou.

## Heurísticas NURBS

- Prefira grau 3 para curvas de forma livre. Grau 1 só para polilinhas intencionais.
- Loft: garanta que as curvas de seção tenham a mesma direção e o seam alinhado. Seam torcido é a causa nº 1 de loft retorcido.
- Menos pontos de controle geram superfícies mais limpas. Rebuild antes de lofting se as curvas vierem com excesso de pontos.
- Para sólidos, feche com Cap, ou construa por Boolean a partir de primitivas fechadas. Booleans falham com superfícies coincidentes: desloque 0,01 mm quando necessário.
- Painelização: verifique planaridade se o objetivo for fabricação.

## Recuperação de erros

Se uma operação falhar, leia a mensagem de erro, faça no máximo 2 tentativas corrigidas com abordagens diferentes e, se ainda falhar, pare e explique ao usuário o que tentou. Não repita a mesma chamada com os mesmos parâmetros. Nunca apague objetos do usuário sem confirmação explícita.

## Proibições

- Não execute código que acesse rede, sistema de arquivos fora da pasta do projeto, ou processos do sistema operacional.
- Não salve por cima do arquivo do usuário; use "Salvar como" com sufixo de versão.
- Não afirme que algo foi criado sem ter verificado no passo 5.

## Exemplo curto

Pedido: "cria um balcão de recepção curvo, 2,4 m de corda, 1,1 m de altura, 60 cm de profundidade".

Especificação: sólido fechado; planta em arco com corda de 2400 mm e flecha a definir (adoto 300 mm e declaro); extrusão vertical de 1100 mm; profundidade de 600 mm por offset da curva; camada `ESTANDE::Mobiliario`.
Rota: arco por 3 pontos → offset de 600 mm → fechar as pontas com linhas → join → extrusão com cap.
Verificação: `IsSolid` = true; bounding box aproximadamente 2400 × 900 × 1100 mm.
