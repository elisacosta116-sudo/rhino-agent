# RhinoCommon e scripts — o que consultar antes de escrever

## Regra, derivada de falha medida

Na rodada 3-bis o agente escreveu, em C#:

```csharp
var saveOpt = new Rhino.FileIO.FileSaveOptions();
```

Resultado: `CS0234: The type or namespace name 'FileSaveOptions' does not exist
in the namespace 'Rhino.FileIO'`. O tipo foi inventado. O arquivo do trabalho
inteiro não foi salvo, e o agente ainda relatou "Arquivos Gerados:
output/balcao_recepcao_v3.3dm" — um arquivo que não existe no disco.

**A causa não é só o modelo.** O servidor oferece consulta de documentação para
Python (`get_rhinoscript_docs`) e **não oferece nada equivalente para C#**. A rota
C# é estruturalmente a mais exposta a alucinação de API: não há como conferir uma
assinatura sem sair do servidor.

Daí a ordem:

1. **Tool nativa do MCP.** 65 comandos, ver `references/mcp-superficie.md`. Se
   existe tool, não se escreve script.
2. **Comando nativo do Rhino** via `run_command`. Use o prefixo de traço
   (`_-SaveAs`) para executar sem abrir diálogo modal — foi o que fez a segunda
   tentativa de save da rodada 3-bis não produzir arquivo nenhum.
3. **Python** via `execute_rhinoscript_python_code`, **sempre** depois de
   consultar `get_rhinoscript_docs` para a assinatura.
4. **C#** — evitar. Sem consulta de docs disponível, toda assinatura é chute.

## Referência oficial

- [RhinoCommon API 8.x](https://developer.rhino3d.com/api/rhinocommon/?version=8.x)
  — referência por namespace. O seletor de versão importa: fixe em `8.x`.
- Namespaces mais usados aqui: `Rhino.Geometry` (e `.Intersect`, `.Morphs`),
  `Rhino.DocObjects` (e `.Tables`), `Rhino.FileIO`, `Rhino.Commands`.
- [Changelogs por versão](https://developer.rhino3d.com/api/rhinocommon/whatsnew/8.0)
  — úteis quando um método existe na doc mas não na build instalada.
- Os exemplos de código do site antigo são mais completos que os do novo layout;
  se um método aparecer sem exemplo, vale procurar a versão anterior da página.

## Servidor MCP em uso

[`jingcheng-chen/rhinomcp`](https://github.com/jingcheng-chen/rhinomcp) — arquitetura
em três camadas: cliente MCP (stdio) → servidor Python → plugin C# dentro do Rhino,
por TCP em `127.0.0.1:1999`. A ponte liga e desliga com `mcpstart` / `mcpstop`.

Os contratos do protocolo ficam em `contracts/` no repositório do servidor, em
JSON Schema — é a fonte autoritativa dos parâmetros de cada tool quando a
descrição da tool não bastar.

**Segurança:** o transporte é loopback sem autenticação, e `run_command`,
`execute_rhinoscript_python_code` e `execute_rhinocommon_csharp_code` são
superfície de execução aberta dentro do Rhino. Aceitável local e monousuário;
inaceitável exposto — ver a seção de arquitetura do PRD.
