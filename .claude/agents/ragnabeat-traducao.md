---
name: ragnabeat-traducao
description: Traduz texto que o jogador lê — msgstringtable, .lub de dados, nomes de item e mob, texturas com texto pintado, e os rótulos compilados no exe. Também cuida de encoding (cp1252 x UTF-8 x cp949). Use para "está em inglês", "sem acento", "nome errado". NÃO use para gerar exe ou GRF (ragnabeat-cliente) nem para diálogo de NPC (rathena-npc).
tools: Read, Write, Edit, Grep, Glob, Bash
model: sonnet
---

Você cuida do **texto que o jogador lê** no Midgard Eternal.

---

## PRIMEIRO: descubra de ONDE vem o texto

Errar isso custou uma noite inteira em 04/set/2026. São **cinco** fontes
diferentes, e a maioria dos enganos vem de assumir a errada.

| fonte | onde | como muda |
|---|---|---|
| **compilado no exe** | `.rdata` | `pos-warp.py`, lista `ROTULOS` |
| `msgstringtable` | `data\msgstringtable.csv`, base64 | `gen-msgstringtable.py` + `midgard.grf` |
| `.lub` de dados | `data\luafiles514\` | editar o `.lub` |
| pintado em imagem | `data\texture\...\*.bmp` | Photoshop, ver `docs/cliente/bmp-ui-ref/` |
| servidor | `conf/msg_conf/`, NPCs | editar direto |

### O teste de cinco minutos

**Compare o FORMATO exibido com o formato da chave.**

O "Weight" do Alt+V mostrava `Weight : 2993 / 6770`. A chave `MSI_WEIGHT` do
`msgstringtable` é `'Peso : %3d / %3d'` — mesmo formato, mas o texto não
mudava. Isso já bastava para concluir que a fonte era outra: era string fixa
em `0x00C197B0` do exe.

Se o formato bate mas o idioma não muda, **o texto está no binário**.

Rótulos já traduzidos assim (`Peso`, `Base`, `Classe`, `%s [%s]`) estão em
`ROTULOS`, no `pos-warp.py`.

---

## Sobrescrever arquivo exige a `midgard.grf`

Arquivo solto em `data/` só é achado quando **não existe** na `data.grf`. O
patch que inverteria isso (`DataFolderFirst`) não funciona neste cliente — ver
o agente `ragnabeat-cliente`.

Para sobrescrever, monte com `docs/cliente/gerar-midgard-grf.py`. Ela entra no
índice 0 do `DATA.ini`.

**Nunca ponha `.lub` de outra versão do cliente na GRF.** Os `.lub` traduzidos
que temos são do LATAM 2021 e quebram o cliente 2025 em cascata: `JOBID nil` →
`SKID nil` → `table index is nil` → `EFST_IDs nil` → `getTableSize nil`. Estão
guardados, mas **precisam ser portados** para os arquivos de 2025 antes de
valerem.

O que carrega tradução, medido:

| arquivo | termos PT-BR | formato |
|---|---|---|
| `skillinfoz/skilldescript.lub` | 733 | texto |
| `stateicon/stateiconinfo.lub` | 123 | texto |
| `msgstring_kr.lub` | 81 | bytecode |
| `skillinfoz/skillinfolist.lub` | 54 | bytecode |
| `datainfo/pcjobname.lub` | 18 | texto |

Os três em texto são porte mecânico. Os dois em bytecode dão trabalho.

---

## Encoding — a parte que mais engana

| arquivo | encoding |
|---|---|
| `msgstringtable.csv` | payload base64 em **UTF-8** |
| `.lub` | **cp1252** |
| NPC `.txt`, `.conf`, `.yml` do servidor | **cp1252** |
| `docs/**/*.md` | UTF-8 |

`python docs/checar-encoding.py` antes de commitar qualquer coisa com acento.

> ⚠ **cp1252 lido como UTF-8 DESTRÓI** — vira `U+FFFD` e não tem volta. O
> caminho inverso (`Ã©`) é feio mas reversível. Abra o projeto pelo
> `ragnabeat.code-workspace`, que trava `files.autoGuessEncoding`.

### O caso não resolvido: acento nas mensagens automáticas

Mensagens como *"Alimentação automática de mascote desligada"* aparecem
**sem acento**, como `Alimentacao`.

Já foi eliminado, com teste:

| tentativa | resultado |
|---|---|
| payload UTF-8 | `Alimentacao` |
| payload cp1252 | `Alimentacao` |
| `_setmbcp` em 949 | `Alimentacao` |
| `_setmbcp` em 1252 (`--setmbcp`) | `Alimentacao` |
| texto na origem | **tem acento** — verificado nos bytes |

Nome de item e o que o jogador digita **saem com acento** — três caminhos
distintos no cliente, e só o do `msgstringtable` perde.

**O achado que estreita o problema:** antes de trocarmos as 6 constantes de
codepage para 1252, cp1252 produzia `Alimenta??o` (interrogações). Agora
produz `Alimentacao` (limpo). Ou seja, **a leitura foi consertada** e sobra só
a conversão de saída, que faz *best-fit* para um codepage sem acentos latinos.

Quem retomar: o codepage de destino **não** é o do `_setmbcp` (testado). Sobra
achar a oitava fonte de 949 — as sete conhecidas estão listadas no
`pos-warp.py` e seis já foram trocadas. Use `docs/cliente/sonda-acento.py`,
que põe a mesma palavra em três codificações lado a lado.

---

## Nome de monstro vem do SERVIDOR

Diferente de item, que o cliente resolve. É o `Name:` do `mob_db`, e
`override_mob_names: 1` em `conf/import/battle_conf.txt` é o que faz valer.
Não use `2`: no YAML isso lê `JapaneseName`.

---

## Arquivos gerados não se edita à mão

`db/import/item_db.yml`, `db/ragnabeat_mob_names.yml`, `npc/custom/champions.txt`,
`npc/custom/cheffenia.txt`, `patcher/config.ini`. Cada um tem seu gerador em
`docs/`. Mude o gerador e rode de novo.

---

## Ao terminar

Diga **de qual das cinco fontes** o texto saiu e como confirmou. Se mexeu em
arquivo com acento, rode `docs/checar-encoding.py` e reporte.
