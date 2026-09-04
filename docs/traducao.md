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
| Itens (cliente) | `SystemEN/itemInfo_C.lua` | LATAM | ✅ 6.327 |
| Nomes de item (servidor) | `db/import/item_db.yml` | itemInfo_C, por ID | ✅ 4.305 |
| Nomes de mapa | `System/mapInfo_true.lub` | LATAM | ✅ 959 |
| Interface e login | `data/msgstringtable.csv` | LATAM `_ml`, coluna 7 | ✅ 4.207 |
| Interface (comandos) | `data/luafiles514/lua files/msgstring_kr.lub` | LATAM | ✅ 465 |
| Skills | `.../skillinfoz/skilldescript.lub`, `skillinfolist.lub` | LATAM | ✅ |
| Buffs / ícones de estado | `.../stateicon/stateiconinfo.lub` | LATAM | ✅ |
| Nome de classe | `.../datainfo/pcjobname.lub` | LATAM | ✅ 146 de 163 |
| Prefixo de carta | `data/cardprefixnametable.txt` | LATAM | ✅ 1.822 |
| **Ordem `prefixo + nome`** | compilada no exe | — | ❌ ver [pendências](#pendências) |
| Texturas de login e ESC | 110 BMP + 1 TGA | LATAM | ✅ 56 de 111 — o resto não tem par |
| **NPCs** | `npc/**` | brAthena | ⚠ ~16% viável |
| Nomes de mob (servidor) | `db/ragnabeat_mob_names.yml` | LATAM `i18n/sc/*.csv` | ✅ 561 de 1.004 |
| Quests, conquistas, `towninfo` | `System/*.lub` | LATAM (acessível) | ❌ sensível a episódio |

### A fonte que faltava para os mobs

Nome de item o cliente resolve; **nome de mob vem do servidor**, é o campo
`Name:` do `mob_db`. Por isso ficou em aberto tanto tempo — não há tabela de
mob no cliente para traduzir.

A fonte apareceu em `DEVTOOLS/PTBR/latam/i18n/sc/*.csv`: 1.494 planilhas do
cliente LATAM, uma linha por texto e uma coluna por idioma, tudo em base64
(coluna 2 inglês, coluna 7 português). São os nomes oficiais do bRO.

**Armadilha:** a base repete a mesma string em inglês com traduções diferentes
conforme o contexto, e pegar a primeira ocorrência trazia o ovo de pet como
nome de monstro — *Isis → "Ovo de Ísis"*, *Orc Warrior → "Ovo de Guerreiro
Orc"*. O [gerar-nomes-mob.py](gerar-nomes-mob.py) resolve por **voto da
maioria**; 2.840 casos precisaram do desempate.

---

## Busca por nome nos comandos

Já funciona, desde que se use o comando certo — e são dois:

| Comando | Procura em | Estado |
|---|---|---|
| `@ii` / `@iteminfo` | **itens** (`itemdb_searchname_array`) | 4.305 nomes PT-BR |
| `@mi` / `@mobinfo` | **monstros** (`mobdb_searchname_array`) | 561 nomes PT-BR |

`@ii Goblin Arqueiro` não acha nada porque Goblin Arqueiro é **monstro** — o
comando é `@mi Goblin Arqueiro`.

A comparação é `strcmpi` (`src/map/mob.cpp:271`), byte a byte sem locale, então
acento funciona: o cliente manda cp1252 e o db está em cp1252, os bytes batem.

Um detalhe do `mobdb_searchname_sub` (`mob.cpp:273`): monstro **sem exp e sem
spawn** é excluído da busca de propósito, por ser considerado slave. Se um mob
não aparecer no `@mi`, é essa a razão antes de suspeitar do nome.

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
| `grf_listar.py` | lê GRF v2 e v3, lista, **decifra** e extrai sem percorrer os 4 GB |
| `gen-texturas-ptbr.py` | texturas de login e ESC: extrai dos dois GRFs, tria e instala |
| `corrigir-aspas.py` | conserta descrição partida em aspa escapada, com a fonte do LATAM |
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

**O editor abriu um arquivo cp1252 como UTF-8 e destruiu os acentos ao gravar.**
Aconteceu em 03/set/2026 com cinco arquivos: `npc/custom/warper.txt` (326
acentos), `curandeira.txt` (55), `black_market.txt` (34), `jobmaster.txt` (13) e
`db/ragnabeat_items.yml` (6, em nome de item). No jogo o texto saiu assim:

```
esperado:  Bênção e Agilidade aplicadas.
saiu:      Bï¿½nï¿½ï¿½o e Agilidade aplicadas.
```

`ï¿½` é a assinatura do estrago, e ela diz exatamente o que houve. São os bytes
`EF BF BD` — o **U+FFFD REPLACEMENT CHARACTER** — lidos de novo como cp1252. Ou
seja: alguém leu o arquivo como UTF-8, cada byte de acento (`ç` = `0xE7`) é
inválido sozinho em UTF-8, virou U+FFFD, e o arquivo **foi gravado assim**.

> Não confunda com codepage errado. Codepage errado troca o caractere e dá para
> voltar (`é` vira `Ã©`, mas os bytes ainda estão lá). U+FFFD **apaga**: ele não
> guarda qual acento era. A volta foi palavra por palavra, no olho.

A forma de conferir se um reparo está certo é reaplicar o estrago:
`reparado.encode('cp1252').decode('utf-8', errors='replace').encode('utf-8')` tem
de devolver o arquivo corrompido byte a byte. Se devolver, cada U+FFFD virou um
byte alto na posição certa e nada mais mudou.

**Duas defesas ficaram no repo:**

- [`ragnabeat.code-workspace`](../ragnabeat.code-workspace) trava
  `files.autoGuessEncoding: false` e `windows1252` para `plaintext` e `yaml`.
  Adivinhar foi o que causou o estrago. O erro na outra direção (UTF-8 lido como
  cp1252) só dá `Ã©`, que é feio mas reversível — entre os dois, é o único que
  tem conserto.
- [`checar-encoding.py`](checar-encoding.py) varre o repo e sai com código 1 se
  achar dano, UTF-8 onde devia ser cp1252, ou BOM. Rode antes de commitar
  qualquer coisa com acento.


**Aspa escapada parte a string e derruba o cliente inteiro.** A descrição do
LATAM escreve aspas internas como `\"`, que é Lua válido. A regex ingênua
`"([^"]*)"` não conhece isso e corta ali: o texto **entre** as aspas some e
sobra uma linha que nunca fecha.

```
LATAM : "...admiradores de \"desenhos animados de Amatsu\" ou, como preferem..."
gerado: "...admiradores de \",          <- a barra escapa a aspa de fechar
        " ou, como preferem..."
```

O cliente não degrada: abre `CItemInfoMgr — unfinished string near` e **perde o
itemInfo inteiro**. Aconteceu em 12/ago/2026 com 10 dos 1.020 visuais.

Três coisas mudaram por causa disso:

- `add-item-ptbr.py` usa `"((?:[^"\\]|\\.)*)"`, que consome barra + o que vier depois
- `corrigir-aspas.py` conserta arquivo já gerado, buscando a linha certa no LATAM
- `build.py` bloqueia o release: contar aspas **não** pega o caso (o número é par),
  então a checagem varre a linha como o Lua faria

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

> **12/ago/2026 — EM ABERTO.** As mensagens que o cliente exibe ao entrar no
> jogo ("Alimentação automática de mascote desligada", "Não mostrar seus
> equipamentos ao público") aparecem **sem acento**. Foi descartado que seja
> falta de tradução: as chaves estão no nosso `msgstringtable.csv` **com**
> acento (`MSI_PET_AUTO_FEEDING_OFF`, `MSI_OPEN_EQUIPEDITEM_REFUSE`), e a
> versão de dentro do `data.grf` é coreana — ou seja, o cliente está lendo o
> nosso arquivo. Sobra a conversão.
>
> O arquivo está em UTF-8, mas o cliente converte texto com **cp1252** (6 das 7
> constantes trocadas, ver [cliente/acentuacao.md](cliente/acentuacao.md)) — e a
> tela de login, que funciona, pode usar outro caminho. Como o sintoma na tela
> não distingue "byte descartado" de "codepage errado", existe agora o
> [cliente/sonda-acento.py](cliente/sonda-acento.py): ele põe a mesma palavra
> nas três codificações numa única mensagem, e a que sair legível responde.
> **Rode, anote o resultado aqui, e tire a sonda.**

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

### 2. Texturas de login e menu ESC — feito o que dava

São 111 arquivos (110 BMP + 1 TGA, não "111 BMPs"): 33 `esc_*` mais 78 de
`login_interface\`, em `data\texture\<pasta de UI em cp949>\`. O texto é **pintado na
imagem**, não há string.

Metade estava encriptada nos dois GRFs, então o primeiro passo foi ensinar o
[`grf_listar.py`](cliente/grf_listar.py) a decifrar — porte de `src/common/des.cpp` e
`src/common/grfio.cpp` deste próprio repo. Ver [leia-me.md](cliente/leia-me.md).

O [`gen-texturas-ptbr.py`](cliente/gen-texturas-ptbr.py) extrai, tria e instala. Rodado
em 12/ago/2026 contra `C:\Gravity\Ragnarok\data.grf`:

| | | |
|---|---|---|
| **56 trocadas** | mesmas dimensões e bpp | as abas do ESC, os botões e as janelas de login |
| 25 iguais | LATAM nunca traduziu | setas de status, `win_make2`, `win_selectmap`, `name-edit` |
| 8 divergem | dimensão ou bpp diferente | `warning`/`warning2` (1920×1440 aqui, 640×480 lá), `esc_05*`, `chk_save*`, `win_service` |
| 22 sem par | só existem no kRO 2025 | `bt_start`, `bt_join`, `bt_otp*`, `bt_close*`, `btn_dropdown*`, `checkbox_*`, `bg_login.tga`, `bg_newotp1` |

Os 30 que sobraram (8 + 22) só saem redesenhando o texto por cima da arte kRO — não é
mais extração, é trabalho de imagem. A lista nominal fica em
`DEVTOOLS\PTBR\_extraido\texturas\TRIAGEM.txt`, regerada a cada execução.

A origem PT-BR é a **raiz** `data\texture\` do GRF do LATAM: `data\english\` e
`data\spanish\` é que são os overrides, e não existe `data\portuguese\`.

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
