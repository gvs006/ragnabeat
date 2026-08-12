# Encoding — a regra única do projeto

> **Tudo que o jogador vê tem que estar em cp1252 (ANSI ocidental).**
> UTF-8 vira mojibake na tela.

O cliente foi patchado para decodificar cp1252 ([cliente/acentuacao.md](cliente/acentuacao.md)).
Ele não converte nada: os bytes que chegam são os bytes que ele desenha. Então **qualquer**
arquivo cujo texto termina na tela precisa estar em cp1252 — do script de NPC ao nome de
item no banco.

## Como reconhecer o erro

| Na tela | Nos bytes | Significa |
|---|---|---|
| `bÃªnÃ§Ãos` | `c3 aa`, `c3 a7` | **UTF-8 lido como cp1252** — o arquivo está no encoding errado |
| `b?n??os` | `ea`, `e7` isolados | cp1252 correto, mas o cliente ainda em cp949 (não é mais o nosso caso) |

O primeiro é o comum. `Ã` é a assinatura: em UTF-8 todo acento latino começa com `0xC3`,
que em cp1252 é `Ã`.

## Onde vale, e o estado

| Camada | Arquivo | Encoding |
|---|---|---|
| Scripts de NPC | `npc/custom/*.txt` | **cp1252** — convertidos em 11/ago/2026 |
| Mensagens do servidor | `conf/msg_conf/import/map_msg_eng_conf.txt` | cp1252 (já vinha) |
| Nome de item/mob | `db/import/*.yml` | **cp1252** — ver abaixo |
| Itens (cliente) | `SystemEN/itemInfo_C.lua` | cp1252 |
| Interface, skills, mapas | `data\...\*.lub` | cp1252 (o LATAM já entrega assim) |

## Verificação

Um arquivo em cp1252 **não** decodifica como UTF-8. É o teste:

```python
try:
    open(p, 'rb').read().decode('utf-8')
    print('UTF-8 - ERRADO, converter')
except UnicodeDecodeError:
    print('cp1252 - certo')
```

Varredura da árvore de NPC:

```python
import os
for base, _, arqs in os.walk('npc'):
    for a in arqs:
        if not a.endswith('.txt'): continue
        p = os.path.join(base, a); d = open(p, 'rb').read()
        if not any(b >= 0x80 for b in d): continue
        try:
            d.decode('utf-8'); print('UTF-8:', p)
        except UnicodeDecodeError:
            pass
```

> Ignore os arquivos de `npc/re/` e `npc/custom/official/` — são do upstream, contêm
> renewal que não carregamos, e converter cria conflito de merge. Um caso especial é
> `npc/quests/skills/assassin_skills.txt`, que usa `■` no **nome interno** de um NPC
> oculto: não é texto exibido, deixe como está.

## Nome de item e mob no servidor

Para o jogador digitar `@ii Espírito do Dragão` ou `@mi Guardião`, o nome precisa estar
acentuado **no banco do servidor**, não só no cliente — o `@ii` compara com
`db/*/item_db*.yml`.

**Isso funciona, e foi medido.** O rAthena lê os `.yml` com **rapidyaml**
([src/common/database.hpp:10](../src/common/database.hpp#L10)), um parser zero-copy que
opera sobre o buffer bruto: bytes cp1252 atravessam intactos, sem validação de UTF-8 e
sem conversão.

Prova de conceito em 11/ago/2026 — `db/import/item_db.yml` com um item e o byte `\xe3`:

```
Done reading '1' entries in 'db/import/item_db.yml'
```

Sem erro de parse. O arquivo continua com `Camisa de Algod\xe3o` em disco.

> ⚠ **Não confundir com o yaml-cpp**, que também está no `3rdparty/`. Ele existe no
> projeto mas **não** é quem lê o `item_db`. A conclusão acima vale para o rapidyaml.

> ⚠ **Sem BOM.** Um BOM de UTF-8 no início faria o parser tratar o arquivo como UTF-8.
> Grave com `encode('cp1252')` puro, e cuidado com editores que "corrigem" o encoding
> sozinhos — o VS Code faz isso ao salvar se estiver configurado para UTF-8.

## A armadilha do editor

Foi assim que os 5 scripts de NPC nasceram errados: escritos num editor em UTF-8, sem
ninguém perceber, porque o texto **parece certo no editor**. Só aparece no jogo.

Ao criar arquivo novo com acento, confirme o encoding antes de commitar. O teste do
`decode('utf-8')` acima leva um segundo.

## A exceção: `msgstringtable.csv` é UTF-8

A regra do cp1252 vale para tudo **menos** este arquivo. O payload base64 do
`data\msgstringtable.csv` é **UTF-8** — conferido no próprio arquivo do nosso GRF,
cujo texto coreano decodifica como UTF-8 e falha em cp949 e cp1252:

```
eb 8f 99 ec 9d 98  ->  UTF-8: 동의
```

Gerei a primeira versão convertendo para cp1252 e **todo acento virou `?`** na tela de
login e na janela de configurações. O cliente decodifica como UTF-8, e byte cp1252
isolado não é UTF-8 válido.

Como o LATAM também usa UTF-8 nesse arquivo, o gerador copia o base64 **como está**, sem
reconverter — menos conversão, menos chance de erro.

| Arquivo | Encoding |
|---|---|
| `.lub` (skills, buffs, classes, mapas) | cp1252 |
| `.txt` (cardprefix, NPC) | cp1252 |
| **`msgstringtable.csv`** | **UTF-8** |

## Nomes de item traduzidos no servidor

Gerados por [cliente/gen-nomes-servidor.py](cliente/gen-nomes-servidor.py) para
`db/import/item_db.yml`. **Não edite à mão — regenere.**

| | |
|---|---|
| Itens no servidor (pre-re) | 6.169 |
| Com nome PT-BR no cliente | 4.440 |
| Já idênticos (sem override) | 135 |
| **Gravados** | **4.305** |
| Sem tradução, ficam em inglês | 1.729 |

A fonte é o `SystemEN/itemInfo_C.lua` do cliente, casado por **ID do item** — o mesmo
critério que funcionou nas outras camadas.

### Duas armadilhas do gerador

**`unidentifiedDisplayName` contém `identifiedDisplayName` como substring.** Sem
`(?<!un)` no regex, você lê o nome do item *não-identificado*, que em 856 itens é string
vazia — e perde esses itens em silêncio. Foi o primeiro resultado, 4.437 em vez de 4.440,
e os nomes estavam errados.

**`ITEM_NAME_LENGTH` é 50** ([mmo.hpp:161](../src/common/mmo.hpp#L161)), então o limite
útil é 49. O gerador pula o que passar disso em vez de truncar — hoje nenhum passa, mas a
checagem fica.

### Observação separada: 856 itens sem nome no `itemInfo_C.lua`

O gerador antigo do cliente emitiu entradas-tronco com `identifiedDisplayName = ""` e
descrição vazia, preservando só o `resourceName`. O item 556 (`Rice Cake Stick`) é um
exemplo.

Pelo `F_itemInfoMerge` com `state = false`, entrada custom só entra se o ID **ainda não
existir** na tabela base — então esses vazios não deveriam apagar o nome inglês. Mas o
comportamento observado in-game não bate com essa leitura, e o ponto merece ser
investigado antes de regenerar o `itemInfo_C.lua`.
