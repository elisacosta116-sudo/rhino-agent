# Armadilhas medidas do servidor MCP

Comportamentos que **não estão na descrição das tools** e que já produziram falha
registrada. Todos medidos em `logs/rhino_calls.jsonl`, com a sessão citada.

Escrito à mão. Não confundir com `mcp-superficie.md`, que é gerado por script e
se reescreve inteiro a cada regeneração.

---

## `get_or_set_current_layer` falha em silêncio com caminho hierárquico

Aceita **só o nome da folha**. Com o caminho completo ela não define nada e
devolve uma string bem-formada que parece sucesso:

```
get_or_set_current_layer {"name": "ESTANDE::Totem"}  ->  "Current layer: Default"   <- NÃO definiu
get_or_set_current_layer {"name": "Totem"}           ->  "Current layer: Totem"     <- definiu
```

**Para pôr um objeto na camada certa, use `update_object_attributes`**, que aceita
o caminho completo e devolve o `full_path` do resultado:

```
update_object_attributes {"id": "...", "layer": "ESTANDE::Totem"}    <- funciona
```

**Por que isso importa mais do que parece.** O retorno `"Current layer: Default"`
é indistinguível de uma leitura bem-sucedida. Não há erro, não há flag. Quem não
comparar o retorno com o que pediu segue achando que a camada foi definida.

Medido nas sessões `04c4c2d1` (rodada 1, Haiku), `e5143ceb` (v2r1, Sonnet) e
`5f7984fe` (v2r4, Sonnet). **Pega os dois modelos.** A rodada 1 não conferiu o
retorno e entregou o objeto em `Default` — a falha de camada que ficou três
rodadas atribuída a desleixo do modelo. As outras conferiram e corrigiram.

> Regra geral que este caso ilustra: **compare o retorno de toda tool com o que
> você pediu.** Sucesso aparente não é sucesso.

---

## O envelope de percepção não chega em toda mutação

Com `RHINO_MCP_PERCEPTION=1`, o servidor põe `include_health` e `include_delta`
no envelope de **todas** as chamadas (`server.py:547`), mas o plugin dentro do
Rhino só honra em algumas.

Medido na v2r1 (`e5143ceb`): **2 de 27** respostas trouxeram o envelope —
`execute_rhinoscript_python_code` e `update_object_attributes`. Não trouxeram:
`create_object`, `offset_curve`, `extrude_curve`, `delete_object`,
`create_layer`, `modify_object`.

**Nenhuma tool de criação de geometria honra o envelope.** Não conte com ele
como rede de verificação; use `analyze_objects` explicitamente.

---

## `run_command` sem prefixo de traço abre a interface e trava a sessão

`_Arc` abre o comando interativo e fica esperando cliques no viewport; `_-Arc`
executa direto. O mesmo vale para `_-SaveAs`, `_-Layer`, `_-Properties`.

Quando um comando interativo fica pendurado, ele **engole as chamadas seguintes
e não pode ser cancelado pelo MCP** — exige `Esc` humano no Rhino.

Medido em `6fd25973` (v2r2): um `_Arc` sem traço travou a sessão e engoliu o
`_-SaveAs` seguinte; o agente só entregou porque detectou que o save não
acontecera e refez por outra rota. Em `dcf27bed` (3-bis) um `SaveAs` sem traço
não gerou arquivo nenhum e o agente declarou o arquivo como gerado.

Em 35 chamadas de `run_command` nas seis primeiras rodadas, **4 usaram o traço**.

---

## Em geometria curva, `analyze_objects` e o `check.py` medem objetos diferentes

`analyze_objects` devolve o volume do **Brep** — a superfície exata. O
`evals/check.py` mede pela **malha de render** — a aproximação facetada gravada
no arquivo. Em faces planas os dois coincidem; em superfície curva a malha fica
inscrita e mede **para menos**.

Medido em `21f5fb88` (v2r5), cilindro de R=300 e h=900:

```
analitico  pi.r2.h        254.469.004,9
Brep       analyze_objects 254.469.006,0    desvio 0,0000%
malha      check.py        254.328.522,9    desvio 0,055%
```

A bbox saiu exata: os vertices da malha caem sobre a superficie, e num cilindro
os extremos em 0, 90, 180 e 270 graus sao atingidos.

**O sinal do desvio depende de a curvatura ser aditiva ou subtrativa.** Num
cilindro solido a malha fica inscrita e mede **para menos**. Num furo cilindrico
a malha da parede tambem fica inscrita, o que deixa o furo **menor** do que e' —
e o solido sobra volume. Medido em `13a191fd` (v2r6), caixa 1000x800x400 com
furo de R=150:

```
analitico  caixa - furo    291.725.666,1
Brep                       291.725.666,0    desvio  0,0000%
malha      check.py        291.809.808,2    desvio +0,0288%   <- para MAIS
```

Nao suponha a direcao do erro pelo tipo de superficie. Compare sempre em modulo.

**Nao leia essa diferenca como relato infiel do agente.** Sao duas medicoes
legitimas de objetos diferentes. Curvatura dupla (esfera, toro) faceta nas duas
direcoes e o desvio e' maior — ainda nao medido.

### A caixa solta mente em geometria aparada

No mesmo arquivo da v2r6, `bbox_solta` deu **1000 x 800 x 420** contra 400 reais
em Z: 420 e' a altura do cilindro de corte antes de ser aparado, e a superficie
nao aparada sobrevive no Brep. A malha deu 400,0 exato.

E' a mesma armadilha do bug de bbox corrigido em 19/09. Se o `check.py` ainda
medisse pelo casco de controle, geometria perfeita reprovaria por 5% em Z.

---

## `analyze_objects` devolve só o nome da folha da camada

O campo `layer` traz `"Mobiliario"`, não `"ESTANDE::Mobiliario"`. Isso parece
camada errada e não é. Para o caminho completo, use `get_object_attributes`, que
devolve `layer.full_path`.

Medido em `e5143ceb` (v2r1): o relato do agente pareceu indicar camada plana, e
o `check.py` sobre o arquivo mostrou a hierárquica correta.
