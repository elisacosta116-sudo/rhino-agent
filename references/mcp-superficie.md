# Superficie do MCP `rhino` (rhinomcp 0.4.1.1)

> Gerado por `evals/dump_capabilities.py` a partir de `logs/rhino_calls.jsonl`.
> Nao edite a mao: rode o script de novo.

**65 comandos** — 38 do Rhino, 27 do Grasshopper.

Nunca invente nome de tool nem assinatura de metodo. Se nao esta nesta lista,
nao existe. Para scripts em Python, consulte `get_rhinoscript_docs` antes de
escrever. **Nao existe consulta equivalente para C#** — ver `references/rhinocommon.md`.

> **Esta lista diz o que existe, nao como cada tool se comporta.** Comportamentos
> que a descricao das tools nao conta e que ja produziram falha medida estao em
> `references/armadilhas-mcp.md` — entre eles uma tool de camada que falha em
> silencio. Leia antes de confiar no retorno de qualquer chamada.

## Verificacao embutida (envelope de percepcao)

Mutating commands accept opt-in envelope flags that attach extra feedback to the result. Set them per command on the envelope, or globally with the RHINO_MCP_PERCEPTION server setting.

- **`include_delta`** — anexa `_delta`. Attaches a change-delta (created/deleted ids and counts) to a mutating command's result.
- **`include_health`** — anexa `_health`. Attaches a geometry-health report (created/modified objects that fail validity checks, with reasons) to a mutating command's result.

Os tres booleanos aceitam `dry_run`: simule antes de aplicar.

## Rhino (38)

| Comando | Somente leitura | dry_run |
| --- | --- | --- |
| `analyze_objects` | sim | - |
| `boolean_difference` | - | sim |
| `boolean_intersection` | - | sim |
| `boolean_union` | - | sim |
| `capture_viewport` | sim | - |
| `create_layer` | - | - |
| `create_object` | - | - |
| `create_objects` | - | - |
| `create_planar_region` | - | - |
| `delete_layer` | - | - |
| `delete_object` | - | - |
| `describe_capabilities` | sim | - |
| `execute_rhinocommon_csharp_code` | - | - |
| `execute_rhinoscript_python_code` | - | - |
| `extrude_curve` | - | - |
| `get_commands` | sim | - |
| `get_document_summary` | sim | - |
| `get_object_attributes` | sim | - |
| `get_object_info` | sim | - |
| `get_objects` | sim | - |
| `get_or_set_current_layer` | - | - |
| `get_selected_objects_info` | sim | - |
| `intersect_curves` | - | - |
| `loft` | - | - |
| `measure_objects` | sim | - |
| `modify_object` | - | - |
| `modify_objects` | - | - |
| `offset_curve` | - | - |
| `pipe` | - | - |
| `project_curve` | - | - |
| `redo` | sim | - |
| `run_command` | - | - |
| `section_profile` | sim | - |
| `select_objects` | - | - |
| `split_curve` | - | - |
| `sweep1` | - | - |
| `undo` | sim | - |
| `update_object_attributes` | - | - |

## Grasshopper (27)

| Comando | Somente leitura | dry_run |
| --- | --- | --- |
| `gh_add_component` | - | - |
| `gh_batch_get_component_type_info` | sim | - |
| `gh_batch_search_components` | sim | - |
| `gh_build_graph` | - | - |
| `gh_capture_preview` | sim | - |
| `gh_clear_canvas` | - | - |
| `gh_clear_graph` | - | - |
| `gh_connect_components` | - | - |
| `gh_create_document` | - | - |
| `gh_delete_component` | - | - |
| `gh_disconnect_components` | - | - |
| `gh_expire_solution` | - | - |
| `gh_get_available_components` | sim | - |
| `gh_get_canvas_state` | sim | - |
| `gh_get_component_info` | sim | - |
| `gh_get_component_type_info` | sim | - |
| `gh_get_document_info` | sim | - |
| `gh_get_graph` | sim | - |
| `gh_get_parameter_value` | sim | - |
| `gh_layout_components` | - | - |
| `gh_list_component_categories` | sim | - |
| `gh_list_components` | sim | - |
| `gh_mutate_graph` | - | - |
| `gh_run_solution` | - | - |
| `gh_search_components` | sim | - |
| `gh_set_parameter_value` | - | - |
| `gh_update_component` | - | - |
