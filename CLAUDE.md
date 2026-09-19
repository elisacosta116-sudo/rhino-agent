# Projeto: agente NURBS
- Rhino 8 via MCP `rhino`. Unidade padrão: mm. Z vertical.
- Para qualquer geometria, siga a skill `rhino-nurbs` (inspecionar → construir → verificar → reportar).
- Rota preferida: templates em gh-templates/ > tools MCP > comandos Rhino > script curto.
- Nunca declare sucesso sem IsValid/IsSolid verificados.
- Arquivos de saída vão para ./output com sufixo _vN.
- OBRIGATÓRIO: antes da PRIMEIRA chamada a qualquer tool do MCP `rhino` na sessão, leia a skill `rhino-nurbs` e chame `get_modeling_guidance('overview')`. Vale também para pedidos só de leitura.
