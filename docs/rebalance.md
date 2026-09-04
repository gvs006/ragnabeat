# Rebalance e itens trazidos do renewal

Proposta para revisão. **Nada aqui está no jogo ainda** — os valores abaixo são
sugestão minha, ancorada no que o pre-renewal já tem. Aprove, corrija ou risque
item por item, e só então eu escrevo no `db/`.

Data: 11/ago/2026.

---

## 1. A regra do servidor

- Pre-renewal (`PRERE` em `src/config/renewal.hpp:8`), teto **99 base / 70 job**.
- **Não existe 3ª classe.** Item com `Classes: All_Third` ou `Fourth` não é
  equipável por ninguém aqui.
- **`EquipLevelMin` acima de 99 é inalcançável.** Vários itens de renewal pedem
  100+ e entrariam mortos.
- Fórmulas de dano, DEF e refino são as antigas. Número de renewal colado no
  pre-re quase sempre fica forte demais — DEF é o caso mais gritante.

## 2. Por onde um item entra

Três camadas, e as três precisam existir:

| Camada | Arquivo | Situação |
|---|---|---|
| Servidor | [db/ragnabeat_items.yml](../db/ragnabeat_items.yml) | pronto — carrega por último, ganha de tudo |
| Nome/descrição no cliente | `SystemEN/itemInfo_C.lua` | hoje só tem os 4.440 itens de pre-re |
| Sprite/textura | `data.grf` | **não é garantido — tem que conferir item a item** |

**Nome/descrição.** A fonte já existe: `DEVTOOLS/PTBR/iteminfo_ptBR.lua`
(16.731 itens do RO LATAM) **tem os itens de renewal em PT-BR** — conferi o
1746, está lá como "Arco Élfico" com descrição completa. É só estender o
gerador para incluir os IDs importados. Sem isso o item aparece com nome em
coreano/inglês do GRF base.

**Sprite.** Aqui eu estava errado numa versão anterior deste documento: o GRF
de cliente 2025 **não** tem tudo. A "Lendárias Asas de Demônio" (5376) tem
entrada no itemInfo e ícone de collection, mas **nenhum sprite** — foi
exatamente isso que produziu o erro na tela:

```
Cannot find File : sprite\<coreano>.act
```

Por isso existe agora [cliente/checar-sprite.py](cliente/checar-sprite.py).
Rode **antes** de pôr qualquer item novo no `db`:

```
python docs/cliente/checar-sprite.py 5376 5451 1746
```

Ele lê a tabela do `data.grf` sem extrair nada e diz, por item, se existem o
sprite de chão, o sprite vestido e o ícone. `drop=False` significa caixa de
erro na cara do jogador — item vetado até alguém pôr o sprite num GRF custom.

Resultado da varredura de todos os itens desta proposta (11/ago/2026): só o
5376 falhou. Todo o resto está completo no GRF.

---

## 3. Já existem em pre-renewal — nada a importar

Estes você pediu e **já estão no `db/pre-re`**. Só precisam ser colocados à
venda:

| Item | AegisName | ID | Observação |
|---|---|---|---|
| Orelha de Elfo [1] | `Elven_Ears_` | 18507 | idêntica à de renewal. Lv 70, meio da cabeça, Novato e S.A. não usam |
| Orelha de Elfo | `Elven_Ears` | 2286 | sem slot |
| Chapéu de Super Aprendiz [1] | `Super_Novice_Hat_` | 5119 | DEF 4 aqui, 8 no renewal. Todos os Atributos +1 |
| Espírito do Dragão de Ouro | `Dragonhelm_Gold` | 5451 | topo, DEF 7, 1 slot. ASPD +10%, Todos os Atributos +3, +5% dano em Semi-Humano |
| Espírito do Dragão de Prata | `Dragonhelm_Silver` | 5452 | topo, DEF 5, 1 slot. ASPD +7%, Atributos +2, +3% em Semi-Humano |
| Espírito do Dragão de Bronze | `Dragonhelm_Copper` | 5453 | topo, sem DEF, 1 slot. ASPD +5%, Atributos +2, +1% em Semi-Humano |

Os três Espíritos do Dragão são os "RWC ouro/prata/bronze" — no db eles se
chamam *RWC 2008 Dragon Helm*. **A versão de pre-re é diferente da de renewal**
e é melhor deixar a nossa: a de renewal troca ASPD e atributos por resistência
a Semi-Humano. Os três já vêm com todas as travas de comércio (`NoDrop`,
`NoTrade`, `NoSell`, `NoCart`, `NoMail`, `NoAuction`) — proponho **manter**,
são itens de premiação.

---

## 4. Importar do renewal — proposta item a item

### 4.1 Arco Élfico — `Elven_Bow` (1746)

Vem como: ATK 160, Nível de Arma 3, 1 slot, duas mãos, Arqueiro/Bardo-Dançarina
e Caçador, `EquipLevelMin: 100`, `Classes: All_Third + Fourth`, DEX +2.

Âncora do pre-re (arcos com slot): `Balistar_` ATK 145, Lv4, 1 slot, req. 77.
Sem slot chega a 170 (`Bow_Of_Evil`) e 194 nos `_C` de evento.

**Proposta — só o que você pediu, nível e classe:**

| Campo | De | Para | Por quê |
|---|---|---|---|
| `EquipLevelMin` | 100 | **90** | 100 é impossível com base máx 99 |
| `Classes` | All_Third, Fourth | **Normal, Upper, Baby** | senão ninguém equipa |
| `Attack` | 160 | **160** (manter) | fica entre o `Balistar_` (145, com slot) e o `Bow_Of_Evil` (170, sem slot). Nível de Arma 3 já o pune no refino |
| Resto | — | intacto | 1 slot, DEX +2, peso 1500 |

### 4.2 Flecha Élfica — `Arrow_Of_Elf` (1773)

Vem como: ATK 45, peso 1, `EquipLevelMin: 100`, Arqueiro/Ladrão/Assassino/
Bardo-Dançarina/Caçador/Arruaceiro.

| Campo | De | Para | Por quê |
|---|---|---|---|
| `EquipLevelMin` | 100 | **0** | flecha com requisito de nível é um estorvo; e 100 é impossível |
| `Attack` | 45 | **45** (manter) | acima da Flecha de Aço (40) e sem o bônus elemental da de Prata |

### 4.3 Mochila da Aventura — `Bravery_Bag` (2576)

Vem como: manto, **DEF 20**, 1 slot, refinável, `View: 2`, dá `BS_GREED` nível 1,
e a partir do refino +7 dá bônus conforme o atributo passar de 90 (ATQ, MATQ,
resistência Neutro, ASPD, etc).

Âncora: o manto com mais DEF do pre-re inteiro é **10** (Ruffler, Capa de Freyja).
DEF 20 seria o dobro do teto do episódio.

| Campo | De | Para | Por quê |
|---|---|---|---|
| `Defense` | 20 | **10** | empata com o melhor manto do pre-re em vez de dobrá-lo |
| Script de refino | intacto | **intacto** | os gatilhos de atributo ≥90 são alcançáveis aqui (teto 99) |
| `skill "BS_GREED",1` | intacto | **intacto** | conveniência, não é poder de combate |

**Versão aluguel:** o barter não sabe entregar item alugado. Ela vira uma opção
separada no script do NPC, com `rentitem 2576,<segundos>`. Preciso que você
diga a duração — sugiro **7 dias** (604800 s).

### 4.4 Cartas Seladas MVP — 44 itens (`Sealed_*_Card`)

São as versões fracas das cartas MVP. Exemplo, `Sealed_Kiel_Card` (4480):
`bonus bDelayrate,((getrefine()>14)?-20:-15);` — contra -30 da Kiel de verdade.

**Armadilha:** quase todas testam `getrefine()>14`. O refino máximo do
pre-renewal é **10**, então esse ramo nunca dispara e elas ficam sempre no valor
menor. Não quebra nada, mas metade do texto do item vira letra morta.

| Decisão | Proposta |
|---|---|
| Quais entram | as que têm equivalente MVP já vendido pelo Contrabandista — as demais ficam de fora |
| `getrefine()>14` | trocar para **`>9`** (refino máximo daqui), para o ramo alto existir |
| Preço | mais barato que a carta real; sugiro **30 Moedas de Mythril** contra 100 |

Se preferir trazer as 44 de uma vez, é a mesma quantidade de trabalho — só me
diga.

### 4.5 Amplificador de Som [1] — `Sound_Amplifier` (2899)

Nome real no db: "Sound Amplification Device". Acessório, 1 slot, Lv 90,
Bardo-Dançarina e Caçador.

O script que vem é **inutilizável em pre-re**: usa `WM_METALICSOUND` (skill de
3ª classe, não existe) e `bVariableCastrate` (conjuração fixa/variável é
conceito de renewal).

**Proposta — reescrever o script para o que você pediu:**

```
bonus2 bSkillDelay,"SN_SHARPSHOOTING",-500;
```

Tiro Preciso é `SN_SHARPSHOOTING` (Sniper). `bonus2 bSkillDelay` reduz o
pós-conjuração daquela skill em milissegundos — **-500 = meio segundo**.
Diga se quer mais ou menos. Mantendo Lv 90 e as classes como vêm (Caçador
inclui Sniper).

### 4.6 Boina Charmosa — `Parade_Cap` (5468)

Confirmada pelo link que você mandou. Topo da cabeça, DEF 3, 1 slot, refinável,
`View: 465`. Script:

```
bonus bDelayrate,-5;              // pós-conjuração -5%
bonus bMdef,2;
if (getrefine() > 5)
   bonus bVariableCastrate,-(getrefine()-5);   // -1% de conjuração por refino acima de +5
```

Conferi: em pre-renewal o `bVariableCastrate` **funciona** — sem `RENEWAL_CAST`
ele é tratado como `bCastrate` (`doc/item_bonus.txt:240`). Ou seja, o item
funciona exatamente como você descreveu, sem reescrever nada.

**Proposta: entra como está.** DEF 3 e -5% de pós-conjuração são modestos, e o
teto do refino aqui é +10, então o bônus de conjuração para em -5%.

### 4.7 Lendárias Asas de Demônio — `Satanic_Chain_P` (5376)

É esse item mesmo: no LATAM o 5376 se chama **"Lendárias Asas de Demônio"**.
Topo da cabeça, DEF 6, 1 slot, `View: 382`, **SP Máx +120** e 10% de amaldiçoar
ao ser atingido — bate com o que você descreveu.

**O sprite existe.** A causa do erro não é o item: é que os dois clientes da
máquina não têm o mesmo conteúdo.

```
5376  |build drop=False vestido=0  |prod drop=True vestido=2   <<< FALTA NO BUILD
```

Os seis arquivos (`사타닉체인.spr`/`.act` de chão + masculino e feminino
vestidos) estão em `C:\RagnaClient\data.grf`. **Não** estão no
`RagnaBeat.Dev\data.grf`, que é o que vira build para os jogadores. Detalhe em
[cliente/leia-me.md](cliente/leia-me.md).

Ou seja: **não há decisão de balanceamento pendente aqui**. O item entra como
está (DEF 6, SP +120, 1 slot, dentro da escala do pre-re) assim que os sprites
forem para o GRF do build.

**Resolvido em 12/ago/2026.** Os 6 arquivos foram extraídos do GRF de produção
e postos soltos na pasta `data\` do cliente de dev:

```
RagnaBeat.Dev\data\sprite\아이템\사타닉체인.spr           1.245 bytes
RagnaBeat.Dev\data\sprite\아이템\사타닉체인.act             116 bytes
RagnaBeat.Dev\data\sprite\악세사리\남\남_사타닉체인.spr    23.113 bytes
RagnaBeat.Dev\data\sprite\악세사리\남\남_사타닉체인.act    83.220 bytes
RagnaBeat.Dev\data\sprite\악세사리\여\여_사타닉체인.spr    23.113 bytes
RagnaBeat.Dev\data\sprite\악세사리\여\여_사타닉체인.act    83.220 bytes
```

Pasta solta em vez de GRF porque é assim que o projeto já sobrescreve conteúdo
(os `.lub` de `data\luafiles514\`), o `build.py` copia a `data\` inteira para o
jogador, e não exige mexer no `DATA.ini`. Detalhe técnico da extração em
[cliente/leia-me.md](cliente/leia-me.md).

**Falta testar in-game** — passar o mouse no inventário e equipar.

---

> As alteracoes ja FEITAS em habilidades de classe (cast, area, empurrao)
> estao em **[skills.md](skills.md)**. Esta secao aqui e proposta de
> ARVORE de skill, que e outra coisa.

## 5. Skills do Super Aprendiz EX

Boa notícia: não precisa de C++ nem de skill nova.

No renewal, o `Super_Novice_E` (`db/re/skill_tree.yml`) é o Super Aprendiz
normal **herdando a árvore de Novato e S.A.** e ganhando por cima um punhado de
skills de 2ª classe que **já existem em pre-renewal**: `PR_IMPOSITIO`,
`PR_ASPERSIO`, `PR_SANCTUARY`, `PR_STRECOVERY`, `PR_MAGNIFICAT`, `PR_GLORIA`,
`WZ_FIREPILLAR`, `WZ_SIGHTRASHER`, `WZ_METEOR`, `WZ_JUPITEL`, `WZ_VERMILION`,
`WZ_WATERBALL` e outras.

**Proposta:** copiar essa lista para o `Super_Novice` de
`db/pre-re/skill_tree.yml`, mantendo os pré-requisitos como estão no renewal.
Nosso S.A. passa a poder aprender essas skills sem virar outra classe.

Antes de fazer, preciso de duas decisões suas:

1. **Todas** as skills da árvore EX, ou uma seleção? A lista completa deixa o
   S.A. com Meteoro e Bola d'Água — é uma classe bem diferente do que era.
2. O teto de job 70 do pre-re dá **menos pontos de skill** que o renewal. Ele
   não vai conseguir tudo de qualquer jeito; é isso mesmo que você quer?

**Equips de Super Aprendiz:** o `Super_Novice_Hat_` (5119) já existe aqui.
Me diga quais outros você tem em mente.

---

## 6. Pendências — não consegui identificar

Resolvidas na sua última mensagem:

- ~~RWC ouro/prata/bronze~~ → são os **Espíritos do Dragão** 5451/5452/5453, e
  **já existem em pre-re**. Ver seção 3.
- ~~Boina charmosa~~ → **`Parade_Cap` (5468)**. Ver 4.6.
- ~~Asas de demônio~~ → é o 5376 mesmo, mas está **bloqueado por falta de
  sprite**. Ver 4.7.

Ainda em aberto:

### 6.1 Asas de Demônio — como levar os sprites para o build
A, B ou C da tabela em 4.7. O item em si já está resolvido.

### 6.2 Rosa eterna
Só existe `C_Eternal_Rose`, que é **traje** (costume, sem atributo). Candidatos
com atributo: `Rose_Of_Eden`, `Mistic_Rose`, `Miracle_Blue_Rose`,
`Rapture_Rose`, `Nile_Rose`. Qual é? Um link do ragnaplace resolve na hora,
como resolveu a Boina.

### 6.3 Duração do aluguel
Da Mochila da Aventura (4.3). Sugestão: 7 dias.

### 6.4 Cartas seladas
Trazer só as que têm MVP equivalente à venda, ou as 44?

### 6.5 Skills do Super Aprendiz
As duas decisões da seção 5: árvore EX inteira ou seleção.

---

## 7. Menu do Contrabandista

Fica em dois níveis, como combinado: primeiro a parte do corpo, depois o tipo.

```
[Contrabandista]
> Capas
    > Cartas [Capas]
    > Equips [Capas]
    > Equips 3rd [Capas]
> Elmo
    > Cartas [Elmo]
    > Equips [Elmo]
    ...
```

Cada folha é uma loja barter em [npc/custom/barters.yml](../npc/custom/barters.yml).
Categoria sem item ainda **não aparece no menu** — nada de porta que abre para
uma sala vazia.

Ainda em aberto: o que é "Equips 3rd" em pre-renewal. Não existe 3ª classe
aqui. Você quer dizer equipamento *originário* do episódio das 3ª classes
(trazido para cá como os desta proposta), ou outra coisa?

---

## 8. O que já está no jogo

Implementado em 12/ago/2026 com os valores propostos acima. Servidor
reiniciado, 7 itens e 11 lojas carregados, zero erro no console.

| Onde | O quê |
|---|---|
| [db/ragnabeat_items.yml](../db/ragnabeat_items.yml) | os 6 itens do renewal + o peso 0 da moeda |
| `SystemEN/itemInfo_C.lua` | nome e descrição PT-BR dos 5 novos (o 5376 já estava). Total 5.296 → **5.301** |
| [npc/custom/barters.yml](../npc/custom/barters.yml) | 11 lojas, 41 itens |
| [npc/custom/black_market.txt](../npc/custom/black_market.txt) | menu de dois níveis |
| `RagnaBeat.Dev\data\sprite\` | os 6 sprites das Lendárias Asas de Demônio |

**A descrição do cliente foi corrigida onde nós mudamos o item.** O texto do
LATAM descreve a versão de renewal, então o tooltip mentiria: o Arco Élfico
diria "Nível necessário: 100" num servidor de nível máximo 99. As trocas estão
na tabela `AJUSTES` de [cliente/add-item-ptbr.py](cliente/add-item-ptbr.py) —
nível 100 → 90, classes de 3ª → Caçadores/Bardos/Odaliscas, DEF 20 → 10, e o
efeito do Amplificador reescrito para o Tiro Preciso. Mudou número no db?
Mude ali junto.

### Ainda de fora

- **Flecha Élfica** está no db (e no `@ii`) mas **não está à venda**. A 1 moeda
  por unidade sairia a 100.000 Zeny a flecha; munição precisa de loja de Zeny,
  não da moeda do Mercado Negro. Diga onde você quer.
- **Cartas seladas** — pendência 6.4.
- **Skills do Super Aprendiz** — pendência 6.5.
- **Mochila da Aventura versão aluguel** — pendência 6.3 (falta a duração).

---

## 9. Champion Mobs — levantamento (12/ago/2026)

O `npc/re/mobs/championmobs.txt` **já está no repo** (veio do upstream), mas só
é carregado por `npc/re/scripts_monsters.conf` — e a árvore que roda aqui é a
`npc/pre-re/`. Ou seja: existe no disco, não existe no jogo.

São variantes turbinadas de mobs comuns, com prefixo `C1_`..`C5_` no
`db/re/mob_db.yml` (Swift, Solid, Furious, Elusive, Ringleader).

### O que dá para aproveitar

| Medida | Número |
|---|---|
| Spawns no arquivo | 317 (5 já vêm comentados) |
| Champions distintos | 311, IDs 2603–2913 |
| **Marcados como MVP** | **0** — o pedido de "menos MVPs" já vem atendido |
| Spawns em mapa que o nosso episódio usa | **277** |
| Spawns em mapa de renewal (inalcançável aqui) | 40 — `bif_fild`, `dic_dun`, `ecl_*`, `bra_*`, `dew_*` |
| Sprites a criar | **nenhum** |

Sobre os sprites: `jobname.lub` aponta `JT_C1_YOYO` para `"YOYO"`, ou seja, o
champion **usa o sprite do mob base**. O cliente já renderiza todos.

### O que impede copiar e colar

Os números são de renewal e não sobrevivem aqui:

| | base pre-re | champion (renewal) |
|---|---|---|
| Zombie Slaughter | nível 77, 43.000 HP, 12.000 exp | nível **124**, **174.905** HP, 17.150 exp |
| Yoyo | nível 21, 879 HP, 280 exp | nível 38, **6.940** HP, 1.500 exp |

Nível 124 num servidor com teto 99, e 17 mil de exp base num servidor de
**500x**. Fora que as tabelas de drop dos champions listam itens de renewal.

### Proposta

Em vez de importar as entradas de renewal, **gerar cada champion a partir do
mob base do nosso `db/pre-re`**, multiplicando só o que interessa:

```
nível   = o do mob base            (nunca passa de 99)
HP      = base x 8
ATQ     = base x 1,5
exp     = base x 4
drops, raça, elemento, tamanho, IA = iguais aos do mob base
```

Assim nada de renewal entra junto: nem item que não existe, nem nível
inalcançável. O arquivo sai gerado por script, para `db/ragnabeat_mobs.yml`,
e os spawns viram um `npc/custom/champions.txt` com os 277 que valem.

### Feito em 12/ago/2026

Gerado por [gerar-champions.py](gerar-champions.py) com os multiplicadores
acima. **260 mobs, 266 spawns**, zero erro no boot.

| Arquivo | Conteúdo |
|---|---|
| `db/ragnabeat_mobs.yml` | os 260 champions |
| `db/import/mob_db.yml` | só o rodapé que engancha na cadeia do `mob_db` |
| `npc/custom/champions.txt` | os 266 spawns |

Descartados pelo filtro: 50 spawns em mapa que o nosso episódio não usa, 1 sem
mob base, e **0 com base MVP**.

Rebalancear = mudar `MULT_HP`, `MULT_ATK` e `MULT_EXP` no topo do script e
rodar de novo. Os arquivos são sobrescritos; não edite à mão.

## 10. Nomes de monstro em PT-BR

Consequência do item anterior: os champions nasciam "Rijo Zombie Prisoner",
metade em cada idioma, porque **os 1004 mobs do `db/pre-re` estavam 100% em
inglês**.

Nome de item o cliente resolve — por isso o `itemInfo_C.lua` traduz 5.301 itens
sem tocar no servidor. **Nome de monstro não**: é o campo `Name:` do `mob_db`,
mandado pelo servidor. Traduzir monstro é mexer no db.

**A fonte.** `DEVTOOLS/PTBR/latam/i18n/sc/*.csv` — 1.494 planilhas do cliente
RO LATAM, uma linha por texto e uma coluna por idioma, tudo em base64 (coluna 2
inglês, coluna 7 português). São os nomes **oficiais do bRO**, não tradução
automática: *Zombie Slaughter → Massacre*, *Nightmare Terror → Pesadelo
Sombrio*, *Soldier Skeleton → Esqueleto Soldado*.

**A armadilha.** A base repete a mesma string em inglês com traduções
diferentes conforme o contexto. Pegando a primeira ocorrência saía *Isis → Ovo
de Ísis* e *Orc Warrior → Ovo de Guerreiro Orc* — os ovos de pet. O
[gerar-nomes-mob.py](gerar-nomes-mob.py) resolve por **voto da maioria**:
"Isis" aparece 8x como "Isis" e 1x como "Ovo de Ísis", então ganha o primeiro.
2.840 casos precisaram desse desempate.

Resultado sobre os 1004 mobs:

| | |
|---|---|
| traduzidos | **561** |
| já idênticos em PT (Poring, Familiar…) | 360 |
| sem entrada na base — ficam em inglês | 77 |
| tradução acima de 23 caracteres — pulados | 6 |

Cobertura de **92%**. O que não tem tradução fica em inglês de propósito: é
melhor que chute.

---

## 11. Acessórios custom — Transmutador e Anel do Mercador (02/set/2026)

Três itens que não existem em nenhum servidor oficial. Ficam em
`db/ragnabeat_items.yml` e são vendidos pelo Contrabandista de Visuais
(`npc/custom/visuais.txt` → Acessório), pagos em Moeda de Mythril.

| Id | Item | Slot | Preço | Efeito |
|---|---|---|---|---|
| 60000 | Anel Transmutador 4rd | Acessório **direito** | 150 | aparência de 4ª evolução |
| 60001 | Brinco Transmutador 3rd | Acessório **direito** | 100 | aparência de 3ª evolução |
| 60002 | Anel do Mercador | Acessório (qualquer lado) | 80 | Superfaturar 10 + Desconto 10 |

### Transmutadores — só aparência, e só um por vez

Não dão status nenhum: trocam o sprite do corpo para a classe equivalente de 3ª
ou 4ª evolução, via `npc/custom/transmutador.txt`. Como este servidor é
pre-renewal, essas classes não existem como classe jogável — são só os sprites,
que o cliente 2025 tem de sobra.

Os dois ficam em **`Right_Accessory`** de propósito. Um lado só significa um
slot só: equipar um desloca o outro, pela mecânica do próprio emulador, sem
script de guarda. Antes disso, com os dois vestidos ao mesmo tempo, ambos
rodavam no mesmo recálculo e o último vencia — a aparência ficava imprevisível.

> **Custo de balanceamento: um slot de acessório real.** É deliberado. O
> pre-renewal não tem `Costume_Accessory` — só `Costume_Head_Top/Mid/Low` e
> `Costume_Garment` (`doc/item_db.txt:188-203`). Pôr um item de aparência num
> slot de traje de cabeça tiraria o traje de cabeça do jogador, o que é pior.

### Por que isso exigiu `db/import/job_stats.yml`

A primeira versão usava `changebase` e **não funcionava** — o log do servidor
mostrava sucesso, com id de classe válido, e a tela não mudava. Foram três
portões, todos silenciosos:

1. **O cliente mudou de campo.** Desde os clientes 20231220+ o sprite do corpo
   vem de `bodyStyle`/`LOOK_BODY2`, não mais de `LOOK_BASE`. O rAthena já trata
   o corte (`src/map/clif.cpp:1182`, 1329, 1438). O `changebase`
   (`src/map/script.cpp:12978`) manda `LOOK_BASE` — ignorado para o corpo — e no
   `LOOK_BODY2` reenvia o valor que o `status_set_viewdata` acabou de preencher
   com a **classe original**. Ele reafirma o sprite antigo.
2. **`setlook LOOK_BODY2` sozinho também falharia.** `src/map/pc.cpp:11121` sai
   com `return` mudo — sem log, sem pacote — quando `!job_db.exists(val)`. E em
   pre-renewal o `job_db` vem só de `db/pre-re/job_stats.yml` (42 entradas, zero
   classes de 3ª/4ª); quem as tem é `db/re/job_stats.yml`, carregado apenas com
   `Mode: Renewal`.
3. **O login resetava.** `src/map/pc.cpp:2114` devolve `status.body` para
   `class_` quando o job não existe no `job_db`.

Os três se abrem com a mesma mudança: **`db/import/job_stats.yml`** registra as
27 classes de 3ª/4ª. É o último import de `db/job_stats.yml` e vai **sem
`Mode:`**, então carrega em pre-renewal também.

> **Isso NÃO torna as classes jogáveis.** Não há skill tree, caminho de
> jobchange nem tabela de exp — são nomes no `job_db`, para o servidor aceitar
> mandar o sprite. Todos os campos de stats são opcionais no parser.

De quebra, o `setlook` grava em `sd->status.body`, que persiste na coluna
`char.body`. Por isso o item ficou **só com `EquipScript` + `UnEquipScript`** — o
campo `Script` (que roda no `status_calc_pc`) existia apenas para a aparência
sobreviver ao relogar, e não é mais necessário.

Referência: Racaae, dev do rAthena —
<https://rathena.org/board/topic/147289-appearance-suit-or-3rd-job-suit/>.
O tópico 149143 traz "FIX 1/FIX 2" em `clif.cpp` que **não** devem ser aplicados
aqui: revertem o comportamento para pré-20231220 e quebrariam o suporte que já
temos.

### Anel do Mercador

Moldado no oficial `Merchant_Manual` (2823, `db/pre-re/item_db_equip.yml:24741`),
que já concede as duas skills exatamente assim:

```yaml
Script: |
  skill "MC_DISCOUNT",10;
  skill "MC_OVERCHARGE",10;
```

Ambas têm `MaxLevel: 10` no pre-renewal (`db/pre-re/skill_db.yml:1741-1748`).

Duas diferenças deliberadas em relação ao molde:

- **Sem bloco `Jobs:`.** O oficial é restrito a Aprendiz e Super Aprendiz; este
  serve a qualquer classe — é o ponto do item.
- **`Both_Accessory`, não `Right_Accessory`.** Como concede poder de verdade,
  paga um slot de acessório e pode conviver com um Transmutador. Os
  transmutadores, puramente cosméticos, é que ficam no lado único.

Campo `Script:` e **não** `EquipScript:` — para conceder skill é o certo: roda no
`status_calc_pc` e a skill é revogada sozinha ao desequipar, sem precisar de
`UnEquipScript`. É o que todos os itens oficiais fazem.

**Impacto no balanceamento.** Desconto 10 dá −24% na compra em NPC e
Superfaturar 10 dá +24% na venda. O Mercador de verdade continua à frente: ele
tem as duas skills **e** o slot de acessório livre, além de Carrinho e Descobrir
Item. O anel custa 80 moedas e trava um slot — é conveniência para quem farma,
não substituto de classe.

---

## 12. O "andar até a célula" ao usar skill — era o cliente (02/set/2026)

Relato: ao usar **Nevasca**, o personagem caminha até a célula e a skill sai
**nos pés dele**, em vez de ser lançada à distância.

> **Correção.** A primeira versão desta seção concluía que era comportamento
> normal ("você enxerga 14 células e a skill alcança 9"). **Estava errado.** O
> detalhe que derrubou isso: a skill saindo na própria célula é sintoma de
> alcance ZERO, não de alcance 9.

### A causa: o patch `NoWalkDelay` do cliente

`NoWalkDelay` ("Remove Walk Delay") faz o clique que lança a skill de chão virar
**também** um comando de andar para a mesma célula. Era o **primeiro** patch da
nossa sessão do WARP, e a própria descrição avisa: *"client may likely send
more/duplicated packets"*, com `recommend: no`.

O servidor então amplifica. Com o personagem já andando, o ramo `stepaction`
(`src/map/unit.cpp:2679-2688`) **adia** a skill até a caminhada aproximar:

```cpp
if(src->type == BL_PC && ud->walktimer != INVALID_TIMER
   && (!battle_check_range(src, &bl, range-1) || ignore_range)) {
    ud->stepaction = true;
    ud->target_to = (skill_x + skill_y*md->xs);
    ud->stepskill_id = skill_id;
    return 0; // Attacking will be handled by unit_walktoxy_timer in this case
}
```

Resultado visual: andou até o alvo e a skill saiu lá — parecendo "nos pés".

Bug conhecido, com Storm Gust citado nominalmente:
[rathena#2046](https://github.com/rathena/rathena/issues/2046) (fechado como
`status:invalid`, porque é client-side),
[NEMO#152](https://github.com/Neo-Mind/NEMO/issues/152) (*"causes you to walk
every time even if you use a skill... very annoying for all warlock or similar
classes with floor skills"*),
[board 112192](https://rathena.org/board/topic/112192-character-walks-after-using-a-ranged-insta-cast-skill/).

**Corrigido em 02/set/2026** no rebuild do WARP, trocando `NoWalkDelay` por
`CustomWalkDelay`. Detalhes em [cliente/leia-me.md](cliente/leia-me.md).

### O que foi descartado, com evidência

| Hipótese | Veredito |
|---|---|
| `Range` errado no `skill_db` | `WZ_STORMGUST` tem 9, o oficial de pré-re |
| Servidor mandando andar | `unit_skilluse_pos2` só faz `return 0` fora de alcance |
| `inf` lido errado (chão virando "self") | `int` = 4 bytes = `<type>.L` oficial |
| Cliente 2025 não suportar os pacotes antigos 0x010F/0x0111 | tabela laRO: presentes, com handler |
| Coordenadas x/y de offset errado | `0x0AF4` len 11, offsets 2,4,6,8,10 — batem |
| `skillinfolist.lub` do cliente | `AttackRange = 9`, igual em pré-re e re |

> Nota lateral achada no caminho, **não corrigida**: a guarda do `struct
> SKILLDATA` (`src/map/packets_struct.hpp:4239`) escolhe o formato por
> `PACKETVER_RE_NUM`/`PACKETVER_ZERO_NUM` e **ignora `PACKETVER_MAIN_NUM`** — 4
> de 242 guardas do arquivo fazem isso, e a linha `clif.cpp:5820` logo abaixo
> usa a guarda completa com a mesma data. Como o nosso build é MAIN, compila o
> formato antigo. É inofensivo (o cliente aceita os dois; o que se perde é o
> campo `level2`), está igual no upstream, e **não** era a causa. Fica anotado.

---

## 13. Cor de roupa e montaria — o erro de palette (02/set/2026)

Uma Bruxa montou pela primeira vez e o cliente passou a dar **erro de palette**,
deixando a personagem inutilizável.

A montaria universal **existe** para classe antiga — cada linha de classe tem seu
bicho, com nome coreano: 여우 (raposa, linha do Mago), 타조 (avestruz, Arqueiro),
사자 (leão, Espadachim), 켈베로스 (cérbero, Gatuno), 페코, 두꺼비 (sapo).

**O defeito é nosso `max_cloth_color: 699`.** O `palette.grf` (pacote Kamishi,
111 MB) estendeu para 700 cores **apenas os corpos normais**. Medido nos dois
GRFs:

| Corpo | Cores |
|---|---|
| `하이위저드` (Bruxa, normal) | **700** (0-699) |
| `여우하이위저드` (Bruxa na raposa) | **4** (0-3) |

São **34 corpos montados** no cliente, e nenhum passa de **7** cores. Montar com
cor acima do teto faz o cliente procurar um `.pal` inexistente.

### A correção: gerar o que falta

Houve uma primeira versão que **recusava montar** acima da cor 3, no
`F_Montaria`. Foi retirada no mesmo dia: ela bloqueava até as cores já geradas,
e o pior caso sem palette é a montaria sair com a cor errada — não vale trocar
isso por um "não". O `F_Montaria` ficou só com o liga/desliga.

A correção de verdade é
[cliente/gerar-palettes-montaria.py](cliente/gerar-palettes-montaria.py), que
preencheu **40.954 palettes** (40 MB) — os 34 corpos montados, nas cores que
faltavam até 699.

O algoritmo saiu de medição, não de chute. Comparando as 4 cores **oficiais**
(só `data.grf` — o `palette.grf` sobrescreve até a cor 0, então derivar dele
daria número errado):

- corpo normal: **21** índices variam → a roupa
- corpo montado: **27** → roupa + bicho
- a diferença, **6** índices (235, 237-239, 252-253), **é a raposa**

E o dado que fecha: uma cor custom muda **208 dos 256** índices — repinta o
personagem quase inteiro — mas **nunca toca os 6 do bicho** (conferido em 125,
400 e 699). Então:

```
saida = palette N do corpo NORMAL (custom, inteira)
saida[índices do bicho] = palette 0 do corpo MONTADO
```

O personagem fica com o visual custom completo e a montaria com a cor original.

Os arquivos vão para `data/palette/몸/` solto, que vence o GRF porque o
`DataFolderFirst` está aplicado, com **nome mojibake** (bytes cp949 lidos como
latin1) — a mesma convenção dos sprites soltos. Ver [encoding.md](encoding.md).

O script é idempotente: pula cor que já existe no GRF (as oficiais) e cor que o
corpo normal não tem. Rodar de novo não duplica nada.

> ⚠ **O script grava no `RagnaBeat.Dev`, e os builds têm `data/` própria.**
> Na primeira tentativa o cliente continuou dando `CPaletteRes :: Cannot find
> File`, porque quem estava rodando era o `builds\RagnaBeatProdV0.0.10\`, que
> não tinha `data/palette/`. Um build já pronto **não** herda nada gerado depois
> dele. Para um build existente, leve as palettes por **hardlink** (instantâneo,
> sem gastar disco). Builds novos já as incluem: `.pal` está em `POR_HARDLINK`
> no [build.py](cliente/build.py).

**A família `*_riding` (nomes em inglês) não precisa de nada.** Os 22 corpos de
4ª classe ou já vêm com 700 cores do `palette.grf` (`arch_mage_riding`,
`dragon_knight_riding`…), ou têm o corpo **normal** limitado a 8 cores
(`meister`, `night_watch`) — e aí não há de onde copiar. Só a família coreana
(as 2ª classes) precisava ser preenchida.

**Ressalva medida:** a derivação dos índices da montaria não é igualmente
precisa para todos. Na Bruxa são 6 índices; no `페코건너` (Gunslinger no peco)
são 206, o que significa que boa parte da cor custom é descartada e o
personagem muda pouco. Não é erro — é o limite de derivar por diferença quando
as palettes oficiais daquele corpo variam muito. Quatro corpos dão 0 índices
(`여우위저드` masc, `타조무희`, `타조바드`, `타조헌터`): neles a montaria é
repintada junto. Nenhum dos dois casos trava o cliente.

### Destravar um personagem que já travou

O estado fica salvo em `sc_data`. `SC_ALL_RIDING` é o tipo **592** neste build:

```sql
DELETE FROM sc_data WHERE char_id = <id> AND type = 592;
```

Com o personagem offline, e reiniciando o servidor em seguida para o char-server
não reescrever do cache. Foi o que destravou a `Katy Test` (char_id 150006).

---

## 14. Acessório Sombra — onde os Transmutadores foram parar

Os Transmutadores (60000/60001) começaram em `Both_Accessory`, depois
`Right_Accessory`, e agora estão em **`Shadow_Right_Accessory`**.

O pedido era um "slot visual", que **não existe**: `Costume_Accessory` não é
uma coisa no rAthena. Os slots são um enum C++ em `src/common/mmo.hpp:336-363`,
sem `#ifdef RENEWAL`, com só quatro de traje (3 de cabeça + capa). Não há nada
em `db/re` para copiar — YAML só *usa* os slots, não os define — e criar um
exigiria recompilar **e ainda assim o cliente não teria onde desenhar**.

O slot Sombra é o mais próximo que existe de verdade: `EQP_SHADOW_ACC_R`
(0x100000) é bit independente de `EQP_ACC_R` (0x000008), com índice próprio em
`sd->equip_index[]` e tratamento separado em `src/map/pc.cpp:12072`. **Convive
com os dois acessórios normais**, e o cliente o desenha em janela separada.

Exige `Type: Shadowgear`: `src/map/itemdb.cpp:467` recusa item com bit shadow e
tipo diferente, rebaixando para `IT_ETC` com aviso.

A exclusão mútua continua de graça: os dois no mesmo slot, um desloca o outro.

O **Anel do Mercador (60002) ficou em `Both_Accessory`** — concede Superfaturar
e Desconto, então paga um slot de acessório de verdade.
