# Tradução PT-BR — roadmap

Documento único da tradução. Estado, fontes, ferramentas, armadilhas e o que falta.
Atualizado em 11/ago/2026.

> **Pré-requisito de tudo:** o cliente só renderiza acento depois da correção das
> constantes cp949 — ver [cliente/acentuacao.md](cliente/acentuacao.md). Antes disso,
> traduzir qualquer coisa era inútil.

---

## Estado por camada

| Camada | Onde vive | Fonte | Estado |
|---|---|---|---|
| Mensagens do servidor | `conf/msg_conf/import/map_msg_eng_conf.txt` | rAthena (mkbu95/Mahiro) | ✅ 1.276 |
| Itens (cliente) | `SystemEN/itemInfo_C.lua` | LATAM | ✅ 5.296 |
| Nomes de item (servidor) | `db/import/item_db.yml` | itemInfo_C, por ID | ✅ 4.305 |
| Nomes de mapa | `System/mapInfo_true.lub` | LATAM | ✅ 959 |
| Interface e login | `data/msgstringtable.csv` | LATAM `_ml`, coluna 7 | ✅ 4.207 |
| Interface (comandos) | `data/luafiles514/lua files/msgstring_kr.lub` | LATAM | ✅ 465 |
| Skills | `.../skillinfoz/skilldescript.lub`, `skillinfolist.lub` | LATAM | ✅ |
| Buffs / ícones de estado | `.../stateicon/stateiconinfo.lub` | LATAM | ✅ |
| Nome de classe | `.../datainfo/pcjobname.lub` | LATAM | ✅ 146 de 163 |
| Prefixo de carta | `data/cardprefixnametable.txt` | LATAM | ✅ 1.822 |
| **Ordem `prefixo + nome`** | compilada no exe | — | ❌ ver [pendências](#pendências) |
| **Texturas de login e ESC** | 111 BMPs | LATAM | ❌ texto pintado na imagem |
| **NPCs** | `npc/**` | brAthena | ⚠ ~16% viável |
| **Nomes de mob (servidor)** | `db/pre-re/mob_db.yml` | sem fonte definida | ❌ |
| Quests, conquistas, `towninfo` | `System/*.lub` | LATAM (acessível) | ❌ sensível a episódio |

---

## A regra que decide tudo: qual arquivo o exe abre

Traduzir o arquivo errado não dá erro — **não acontece nada**. Aconteceu duas vezes:
o `mapnametable.txt` do `en.grf` (o cliente 2025 nunca o lê) e quase com o
`pcjobnamegender` (nome de tabela diferente do nosso).

Antes de traduzir camada nova, confirme o caminho no binário:

```python
import re
d = open('RagnaBeat.exe','rb').read()
for m in re.findall(rb'[ -~]{0,34}CHAVE[ -~]{0,18}', d):
    s = m.decode('latin-1')
    if chr(92) in s or '.lu' in s: print(s)
```

Caminhos confirmados:

| Camada | O exe abre |
|---|---|
| Itens | `SystemEN\itemInfo.lua` (via patch `CustomItemInfoLub`) |
| Skills | `Lua Files\SkillInfoz\SkillDescript`, `...\SkillInfoList`, `...\SkillID` |
| Buffs | `Lua Files\StateIcon\StateIconInfo`, `...\EFSTIDs` |
| Classe | `Lua Files\DataInfo\PCJobName` |
| Mapas | `system\mapInfo_true.lub` |
| Interface | `Lua Files\MsgString_KR` **e** `data\msgstringtable.csv` |
| Prefixo de carta | `CardPrefixNameTable.txt` |

---

## Encoding — por arquivo, sempre medido

**Não existe regra única.** Nem o LATAM nem o nosso cliente são uniformes. Medir o
arquivo que se vai instalar é obrigatório; assumir já custou duas quebras.

| Arquivo | Encoding |
|---|---|
| `.lub` (skills, buffs, classes, mapas) | cp1252 |
| `.txt` (cardprefix, scripts de NPC) | cp1252 |
| **`msgstringtable.csv`** | **UTF-8** |
| `db/*.yml` (servidor) | cp1252 — o rapidyaml passa os bytes intactos |
| `resourceName` de item | **cp949**, copiar byte a byte, nunca reencodar |

Como medir, e a armadilha de cada caso, em [encoding.md](encoding.md).

> Nos `.lub` gerados, acento vai como **escape Lua** (`Novi\231o`), não byte cru. Um
> arquivo com zero bytes altos pode estar correto — não confunda com falta de tradução.

---

## Fontes

**RO LATAM** — a fonte de quase tudo. Instalação em `C:\Gravity\Ragnarok`.

- `System\` — pasta real, sempre foi acessível: `mapInfo.lub`, `towninfo`,
  `achievement_list`, `ongoingquestinfolist`, `tipbox_ptBR`, `iteminfo_new`
- `data.grf` — **GRF v0x300, magic `Event Horizon`**. Não é encriptado: o layout é o
  mesmo do v0x200, com o cabeçalho da tabela em 12 bytes (não 8) e cada entrada em 21
  (não 17). O [grf_listar.py](cliente/grf_listar.py) lê os 269.030 arquivos
- Cópia dos `.lub` e texto em `DEVTOOLS/PTBR/latam/` (153 MB). O resto foi apagado —
  é recuperável do GRF deles

**brAthena** — `github.com/brAthena/brAthena20180924`, base Hercules, `npc/` toda em
português com diálogos oficiais do bRO. Sintaxe ~90% compatível.

---

## Ferramentas

Todas versionadas em [docs/cliente/](cliente/), com cópia de trabalho em
`DEVTOOLS/PTBR/`.

| Ferramenta | O que faz |
|---|---|
| `grf_listar.py` | lê GRF v2 e v3, lista e extrai sem percorrer os 4 GB |
| `gen-nomes-servidor.py` | `db/import/item_db.yml` a partir do `itemInfo_C.lua` |
| `gen-msgstringtable.py` | `msgstringtable.csv` da coluna 7 do `_ml` do LATAM |
| `gen-nomes-classe.py` | `pcjobname.lub` no nosso formato com o texto deles |
| `instalar_stateicon.py` | buffs, com os 15 EFST que faltam |
| `editar-skills-prere.py` | reescreve descrição de skill para pre-renewal |
| `utf8_para_cp1252.py` | converte escapes `\ddd` num fonte decompilado |
| `ver-skill.py`, `ver_perdidos.py` | inspeção |
| `unluac.jar` | decompila `.lub` (Lua 5.1) |

Fluxo para editar um `.lub`: **decompilar → editar texto → gravar como texto**. O
cliente aceita fonte e bytecode, então não é preciso recompilar.

---

## Armadilhas já pagas

Cada uma custou uma quebra do cliente. Estão aqui para não se repetirem.

**Ler o arquivo inteiro antes de substituir.** Gerar só a tabela que interessa deixa de
fora o resto. O `pcjobname.lub` também define `ReqPCJobName`; sem ela o cliente entra em
laço com *attempt to call a nil value*.

**Metatable guardando a tabela.** O `EFST_IDs` termina com
`__newindex = function() error("unknown state") end`. Acrescentar chave **depois** da
construção derruba a tabela inteira — e aí todas as constantes ficam nil, e o próximo
arquivo estoura em cascata. As entradas novas vão **dentro** do literal.

**Constantes que a nossa versão não define.** Os arquivos do LATAM indexam por
`SKID.X` / `EFST_IDs.X`. Onde falta, `tabela[nil]` é erro em Lua. Confira sempre:
extraia as referências do arquivo deles, cruze com as definidas no nosso, e a diferença
tem que ser vazia. Foram 3 nas skills (duas eram digitação corrigida entre versões) e 15
nos buffs (efeitos regionais).

**Substituir o arquivo de constantes inteiro não serve.** O do LATAM tem *menos*
constantes que o nosso; trocar perde as que outros arquivos usam. A saída é manter o
nosso e acrescentar só o que falta.

**`unidentifiedDisplayName` contém `identifiedDisplayName`.** Sem `(?<!un)` no regex
você lê o nome do item não-identificado, vazio em 856 itens, e perde tudo em silêncio.

**Encoding, de novo.** Ver a tabela acima. O `msgstringtable` em cp1252 fez todo acento
virar `?` na tela de login.

**O LATAM erra.** `MSI_DO_YOU_AGREE` tem português falando de Replay. Há uma tabela
`CORRIGIR` no `gen-msgstringtable.py` para esses casos.

---

## Pendências

### 1. Ordem `prefixo + nome` no equipamento

Hoje sai `+10 Trip Rebelde Frigideira Lunar`; o desejado é o nome antes do prefixo. A
montagem está **compilada no exe** (`%s %s`, 18 ocorrências) e não há patch no WARP.

Inverter exige achar o ponto exato e trocar a ordem dos argumentos — mudança de risco
alto. **Antes de tentar:** verificar se o cliente do LATAM ou o do ThanatosRO mostra o
prefixo depois. Se mostrar, existe mecanismo pronto e é melhor achá-lo que patchar.

Alternativa barata: ajustar o texto dos prefixos no `cardprefixnametable.txt`, que já é
nosso, para soarem melhor na posição em que aparecem.

### 2. Texturas de login e menu ESC

111 BMPs — 33 `esc_*` mais `login_interface\`. O texto é **pintado na imagem**, não há
string. Agora que o GRF deles abre, as PT-BR são extraíveis. É substituir imagem por
imagem.

### 3. NPCs — precisa de outra abordagem

`traduzir_npc.py` casa NPC por **coordenada** (`mapa,x,y`), que não muda entre forks, e
substitui só as linhas `mes`. Piloto em `cities/prontera.txt`: 19 NPCs casados, **3
traduzidos** — nos outros a contagem de falas difere e o script pula, para não desalinhar
o diálogo. Rendimento seguro: **~16%**.

O brAthena é de 2018 e o rAthena de 2026; os scripts divergiram. **O caminho para
escalar** é memória de tradução: construir um dicionário `frase EN → frase PT` a partir
de todos os pares onde a contagem bate, e aplicar linha a linha nos 383 scripts.
Casamento por texto exato escala muito melhor que posicional.

> Nome de NPC em português é mais longo e há limite de bytes no cliente. Alguns podem
> precisar de encurtamento.

### 4. Itens sem tradução

**1.729 dos 6.169** do servidor ficam em inglês — não existem no cliente LATAM (itens
antigos de pre-renewal). Traduzir à mão ou buscar no brAthena.

### 4b. Cuidado: o `db/import/item_db.yml` é gerado

O `gen-nomes-servidor.py` **reescreve o arquivo inteiro**. Se você acrescentar algo
à mão ali, some na próxima regeneração.

A única exceção tratada é o `Footer:` — um `Imports:` escrito à mão é preservado.
Foi o caso do `db/ragnabeat_items.yml`. Qualquer outra edição manual, não.

Regra: conteúdo próprio vai em **outro** `.yml`, importado pelo `Footer`.

### 5. Nomes de mob no servidor

Para `@mi Guardião` funcionar. O `itemInfo` só cobre itens; falta definir a fonte.

### 6. Os 856 itens sem nome no `itemInfo_C.lua`

Entradas-tronco do gerador antigo, com `identifiedDisplayName = ""`. Pelo
`F_itemInfoMerge` com `state = false` elas não deveriam apagar o nome inglês — mas essa
leitura também diria que os nossos 4.440 nomes seriam ignorados, e eles aparecem. As
duas coisas não podem ser verdade. **Investigar antes de regenerar o `itemInfo_C.lua`.**

### 7. Descrições de skill ainda em renewal

O arquivo inteiro descreve renewal. Duas já corrigidas —
[cliente/skills-prerenewal.md](cliente/skills-prerenewal.md). Suspeitas: Bênção,
Aumentar DEX/AGI, as de Mercador e as linhas de dano dos 2ª classe.
