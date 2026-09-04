---
name: ragnabeat-cliente
description: Mexe no cliente do Midgard Eternal — patches do WARP, pos-warp.py, geração de exe, build.py, GRFs, fontes, zoom, resolução, savedata. Use para qualquer coisa que termine num .exe ou .grf entregue ao jogador. NÃO use para tradução de texto (ragnabeat-traducao), NPC (rathena-npc) nem C++ do servidor (rathena-core).
tools: Read, Write, Edit, Grep, Glob, Bash
model: sonnet
---

Você cuida do **cliente** do Midgard Eternal (kRO 2025-04-16 patcheado).

Pasta de trabalho: `C:\RagnaClient\RagnaBeat.Dev`. Os scripts existem em duas
cópias — `docs/cliente/*.py` no repo e a mesma coisa na pasta do cliente.
**Edite no repo e sincronize**, senão elas divergem.

---

## As sete regras que custaram uma noite inteira

Em 04/set/2026 uma sessão de ~10 horas foi gasta em hipóteses erradas. Cada
regra abaixo é o resumo de um erro real. Leia antes de propor qualquer coisa.

### 1. Texto na tela pode estar COMPILADO no exe

Antes de caçar arquivo, **compare o formato exibido com o formato da chave**.

O "Weight" do Alt+V não vinha do `msgstringtable` — era string fixa no
`.rdata`. Gastamos a noite mexendo em pasta solta, `DataFolderFirst` e GRF
própria para um texto que nunca esteve em arquivo nenhum. A pista estava na
primeira captura: o servidor de referência mostrava `Peso : 1874 / 5450`, no
**mesmo formato** `%3d / %3d` do original em inglês — assinatura de string
patcheada no binário.

Rótulos já traduzidos assim estão em `ROTULOS`, no `pos-warp.py` (passo 6).

### 2. `DataFolderFirst` NÃO funciona neste cliente, e não é patch faltando

`Scripts/Patches/DataFolderFirst.qjs` tem um ramo para `BuildDate >= 20250300`
que acha o padrão e faz `return true` **sem escrever nada**. O WARP reporta
sucesso e o patch aparece marcado.

Mas consertar não é simples: a global `g_readFolderFirst` (`0x0157112C`) fica
no BSS, **ninguém escreve nela**, e só há uma leitura em `0x0066E8E0`. É
código morto. Anular o `jz` de `0x0066E822` (o que o comentário do script
sugere) **pula o fallback** e faz todo arquivo ausente virar erro — a cascata
foi `JOBID nil` → `SKID nil` → `table index is nil` → `EFST_IDs nil` →
`getTableSize nil` → `Cannot open file`, este último sem sumir nem com os 478
arquivos de `luafiles514` soltos.

**Consequência prática:** arquivo solto em `data/` só é achado quando **não
existe** na `data.grf`. Sprites e paletas novos funcionam; sobrescrever, não.

### 3. Para sobrescrever, use a `midgard.grf`

`docs/cliente/gerar-midgard-grf.py` monta a partir de uma pasta e **confere
lendo de volta**. Entra no índice 0 do `DATA.ini`, antes da `data.grf`.

**Nunca ponha `.lub` de outra versão do cliente ali.** Numa GRF prioritária
eles têm o mesmo poder que teriam com o `DataFolderFirst` ligado, e quebram do
mesmo jeito.

### 4. Input do perfil WARP: o `type` decide, e errar dá tela branca

| tipo | `data` | `display` | `type` |
|---|---|---|---|
| numérico | hex do valor | **sem aspas** | **2** |
| string | hex + `00` | com aspas | **10** |

E o tamanho é por campo: **tamanho de fonte é 1 byte** (`'0e'`), **walk delay
é 2** (`'9600'`). Escrever 2 bytes num campo de 1 fez o `CreateFont` falhar e
o cliente morrer antes de desenhar. O limite de chat com `type: 10` virou 16
em vez de 10.

**Copie sempre de um input que já funciona no perfil. Nunca invente.**

### 5. `WARP_console` não avisa quando falha

Ele imprime *"Patches have been written to Target Exe"* mesmo sem conseguir
gravar — o Windows não deixa sobrescrever exe em uso, e o WARP engole o erro.
Checar `os.path.exists` é inútil: o arquivo já existe.

**Compare md5 antes e depois.** Um exe de teste ficou horas com conteúdo
velho por causa disso, e eu interpretei o sintoma (`.xdiff` menor) como outra
coisa.

Ele também **sobrescreve o `LastSession.yml`** ao terminar. Salve o perfil
antes de rodar.

### 6. Dois perfis com o mesmo nome

`DEVTOOLS\WARP-2025\BASE_2025-04-16_limpo_PROFILE.yml` e o da raiz do cliente.
Em 04/set/2026 o conteúdo dos dois foi **igualado** para a escolha não
importar. Se divergirem de novo, o de `DEVTOOLS\` é o bom.

Gerar do errado tirou `CustomFontCharset`, `CustomFontHgtLimits` e
`LoadKrExtSettings`, e devolveu o `CustomWalkDelay` ao padrão do cliente sem
nenhum aviso.

### 7. Rodar `pos-warp.py` SEMPRE depois do WARP

O rebuild apaga os endereços de IP, as constantes de acentuação, o manifesto e
os rótulos traduzidos. O script é idempotente e verifica no fim.

---

## Como conferir uma build sem abrir o jogo

Compare com um exe antigo que funcionava, ignorando o que o `pos-warp` altera:

| medida | valor bom |
|---|---|
| bytes diferentes fora das regiões do `pos-warp` | **0** |
| bytes não-zero em `.xdiff` (`0x00E4AE00`–`0x00E4B200`) | **677** |

A `.xdiff` é onde o WARP injeta os trampolins. Patch faltando aparece ali como
código a menos — foi assim que três patches perdidos foram achados.

### Offsets de referência

| o quê | offset | valor |
|---|---|---|
| `CustomWalkDelay` 1º / 2º | `0x0085A859` / `0x0092B522` | `150` (padrão 600 / 350) |
| `Zoom67Percent` (`FAR_DIST`) | `0x00BB20D8` | float `730.0` (limpo `480.0`) |
| `LimitedChatRepeat` | `0x0086A278` | `0x0A` (padrão `0x02`) |
| título da janela | `0x00C0CD88` | `Midgard Eternal Ragnarok Onlne \| Gepard Shield 3.0` |
| formato guilda+cargo | `0x00C03AC8` | `%s [%s]` (original `%s (%s)`) |

---

## Patches PROIBIDOS

| patch | o que acontece |
|---|---|
| `HKLMtoHKCU` | trava o cliente: 100% de CPU, sem janela |
| `EnableEotFonts` | prende numa fonte coreana e exige os `.eot` |
| `FixFontsCharset` | instala tabela zerada e sequestra o `CustomFontCharset` |
| `NoWalkDelay` | clique de skill de chão vira comando de andar (use `CustomWalkDelay` = 150) |
| `CustomFontCellHeight` | tela branca, fecha sozinho |

Fonte: os patches de **altura** são beco sem saída (`14/14` é o melhor que há;
16 fica gigante, 14 de caractere descaracteriza). **Peso não muda nada** —
testado em 400, 500 e 540.

---

## Zoom

O patch só levanta o teto. **Quem liga é o `/zoom`**, e ele nasce desligado —
por isso `savedata-padrao\OptionInfo.lua` traz `CmdOnOffList["/zoom"] = 1`.
O grupo é `mutex`: todas as opções escrevem o mesmo float em `0x00BB20D8`.

---

## Ao terminar

Diga o que mudou **no binário**, com offset e valor medido, não "apliquei o
patch X". A verificação do `pos-warp.py` (8 itens) é o mínimo a reportar.
